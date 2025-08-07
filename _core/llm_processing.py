import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional
from .logger import get_logger
from .models import ImageInfo
from .utils import encode_image_to_base64, detect_image_mime_type, clean_alt_text
from .config import config
from .prompts import ALT_TEXT_PROMPT
from .http_client import get_http_client

logger = get_logger(__name__)


class AltTextGenerator:
    """AI service for generating German alt text for images."""

    def __init__(self):
        self._load_environment()

        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required but not found in environment variables"
            )

        self.client = OpenAI(
            base_url=config["api"]["openrouter_base_url"],
            api_key=self.openrouter_api_key,
        )
        self.model = config["llm"]["default_model"]

    def _load_environment(self):
        """Load environment variables from .env files."""
        env_path = Path(config["env_file"])
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Fallback to local .env if the main one doesn't exist
            load_dotenv()

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL or read from local file and return as bytes."""
        try:
            # Handle local file:// URLs
            if image_url.startswith('file://'):
                from urllib.parse import urlparse
                from urllib.request import url2pathname
                
                parsed = urlparse(image_url)
                file_path = url2pathname(parsed.path)
                
                if Path(file_path).exists():
                    return Path(file_path).read_bytes()
                else:
                    logger.error(f"Local file not found: {file_path}")
                    return None
            
            # Handle HTTP/HTTPS URLs
            http_client = get_http_client()
            response = http_client.get(image_url)
            response.raise_for_status()

            # Check if it's actually an image
            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                logger.warning(f"URL does not return image content: {image_url}")
                return None
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image {image_url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading image {image_url}: {str(e)}")
            return None

    def create_prompt(self, context: str, current_alt: str) -> str:
        """Create the prompt for alt text generation."""
        return ALT_TEXT_PROMPT.format(
            context=context or "Kein Kontext verfügbar",
            current_alt=current_alt or "Kein Alt-Text vorhanden",
        )

    def generate_alt_text(self, image_info: ImageInfo) -> Optional[str]:
        """Generate German alt text for an image using AI."""
        try:
            # Download the image
            image_bytes = self.download_image(image_info.url)
            if not image_bytes:
                logger.error(f"Could not download image: {image_info.url}")
                return None

            # Encode image to base64
            base64_image = encode_image_to_base64(image_bytes)

            # Detect proper MIME type
            mime_type = detect_image_mime_type(image_info.url, image_bytes)

            # Create the prompt
            prompt = self.create_prompt(image_info.context, image_info.alt_text)

            # Prepare the message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

            # Call the API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                max_tokens=config["llm"]["max_tokens"],
                # temperature=config["llm"]["temperature"],
            )

            # Extract the generated alt text
            content = response.choices[0].message.content
            if not content:
                logger.error(f"No content in response for image: {image_info.url}")
                return None

            # Clean up the response
            alt_text = clean_alt_text(content)
            return alt_text

        except Exception as e:
            logger.error(f"Error generating alt text for {image_info.url}: {str(e)}")
            return None
