import re
import requests
from bs4 import BeautifulSoup, Tag
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from .logger import get_logger
from .models import ImageInfo
from .config import config
from .http_client import get_http_client

logger = get_logger(__name__)


# Remove tags and texts that are not useful for alt text generation.
# This is specific to pages from the Canton of Zurich.
# Adjust as needed based on the actual content structure.
TEXTS_TO_REMOVE = [
    "Bild im Vollbildmodus anzeigen",
    "Mehr erfahren",
    "Schliessen",
    "Auf dieser Seite",
    "Sie sind hier:",
    "Logo des Kantons Zürich",
    "Vorheriges Bild",
    "Nächstes Bild",
    "Ausgeblendete Navigationsebenen",
]


class WebScraper:
    """Web scraper for extracting images and context from web pages."""

    def __init__(self):
        self.http_client = get_http_client()

    def validate_url(self, url: str) -> bool:
        """Validate if the URL is accessible and returns HTML content."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.error(f"Invalid URL format: {url}")
                return False

            response = self.http_client.head(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logger.error(f"URL does not return HTML content: {url}")
                return False
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False

    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML content from the given URL."""
        try:
            response = self.http_client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            return soup

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HTML from {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing HTML from {url}: {str(e)}")
            return None

    def is_supported_image(self, img_url: str) -> bool:
        """Check if the image URL has a supported extension."""
        img_url_lower = img_url.lower()
        return any(
            img_url_lower.endswith(ext)
            for ext in config["images"]["supported_extensions"]
        )

    def extract_text_content(self, element) -> str:
        """Extract clean text content from an HTML element."""
        if not element:
            return ""
        # Get text and clean it up
        text = element.get_text(separator=" ", strip=True)
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def extract_context_from_element(self, element, processed_elements):
        """Helper function to extract context from a given element."""
        if not element or id(element) in processed_elements:
            return []

        processed_elements.add(id(element))
        context_texts = []
        min_length = config["html_parsing"]["minimal_text_length"]

        # Define element selectors in priority order
        selectors = [
            ["h1", "h2", "h3", "h4", "h5", "h6"],  # Headings (high priority)
            ["figcaption", "caption"],             # Image/table captions (high priority)
            ["p", "div", "span"]                   # Text content (lower priority)
        ]

        # Extract text from elements in priority order
        for selector_group in selectors:
            for elem in element.find_all(selector_group):
                text = self.extract_text_content(elem)
                if text and len(text) > min_length:
                    context_texts.append(text)

        return context_texts

    def find_context_elements(self, img_element) -> List[str]:
        """Find surrounding context elements for an image by traversing both upwards and downwards."""
        context_texts = []
        processed_elements = set()
        max_elements = config["html_parsing"]["max_context_elements"]

        # Collect context from different sources
        self._collect_upward_context(
            img_element, context_texts, processed_elements, max_elements
        )
        self._collect_sibling_context(
            img_element, context_texts, processed_elements, max_elements
        )
        self._collect_descendant_context(
            img_element, context_texts, processed_elements, max_elements
        )

        # Clean and deduplicate the collected context
        return self._clean_context_texts(context_texts[:max_elements])

    def _collect_upward_context(
        self, img_element, context_texts, processed_elements, max_elements
    ):
        """Collect context by traversing upwards from the image element."""
        current = img_element.parent
        depth = 0

        while (
            current
            and depth < config["html_parsing"]["context_search_depth"]
            and len(context_texts) < max_elements
        ):
            upward_context = self.extract_context_from_element(
                current, processed_elements
            )
            context_texts.extend(upward_context)
            current = current.parent
            depth += 1

    def _collect_sibling_context(
        self, img_element, context_texts, processed_elements, max_elements
    ):
        """Collect context from siblings of the image element."""
        if not img_element.parent or len(context_texts) >= max_elements:
            return

        for sibling in img_element.parent.children:
            if (
                len(context_texts) >= max_elements
                or sibling == img_element
                or not hasattr(sibling, "find_all")
            ):
                continue

            sibling_context = self.extract_context_from_element(
                sibling, processed_elements
            )
            context_texts.extend(sibling_context)

    def _collect_descendant_context(
        self, img_element, context_texts, processed_elements, max_elements
    ):
        """Collect additional context from descendants if needed."""
        if not img_element.parent or len(context_texts) >= max_elements:
            return

        # Limit descendant search to immediate children to avoid performance issues
        for child in img_element.parent.find_all(recursive=False):
            if len(context_texts) >= max_elements:
                break

            if id(child) not in processed_elements:
                child_context = self.extract_context_from_element(
                    child, processed_elements
                )
                # Add only the first context item to prevent noise
                if child_context:
                    context_texts.append(child_context[0])

    def _clean_context_texts(self, context_texts):
        """Clean and deduplicate context texts."""
        # Remove unwanted texts
        cleaned_texts = []
        for text in context_texts:
            for tag in TEXTS_TO_REMOVE:
                text = text.replace(tag, "")
            # Remove source attribution "Quelle: ..."
            text = text.split("Quelle:")[0].strip()
            if text:
                cleaned_texts.append(text)

        # Remove duplicates while preserving order
        seen = set()
        return [text for text in cleaned_texts if not (text in seen or seen.add(text))]

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[ImageInfo]:
        """Extract all supported images from the HTML with their context."""
        images = []

        img_tags = soup.find_all("img")
        for img in img_tags:
            # Only process Tag elements (not NavigableStrings)
            if not isinstance(img, Tag):
                continue

            # Images in carousels or lazy-loaded images may have different attributes.
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            # Ensure src is a string
            if isinstance(src, list):
                src = src[0] if src else None
            if not src or not isinstance(src, str):
                continue

            # Convert relative URLs to absolute
            img_url = urljoin(base_url, src)

            # Check if it's a supported image format
            if not self.is_supported_image(img_url):
                continue

            # Get current alt text
            alt_attr = img.get("alt", "")
            if isinstance(alt_attr, list):
                alt_text = alt_attr[0] if alt_attr else ""
            else:
                alt_text = alt_attr or ""

            alt_text = str(alt_text).strip()

            # Find surrounding context
            context_elements = self.find_context_elements(img)
            context = "\n".join(context_elements)

            image_info = ImageInfo(url=img_url, alt_text=alt_text, context=context)

            images.append(image_info)

        return images

    def scrape_page(self, url: str) -> Optional[List[ImageInfo]]:
        """Main method to scrape a page and extract images with context."""
        try:
            # Fetch HTML
            soup = self.fetch_html(url)
            if not soup:
                return None

            # Extract images
            images = self.extract_images(soup, url)
            return images

        except Exception as e:
            logger.error(f"Error scraping page {url}: {str(e)}")
            return None
