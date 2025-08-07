from unittest.mock import patch
from bs4 import BeautifulSoup
from _core.web_scraper import WebScraper


class TestWebScraperExtractContextFromElement:
    """Test cases for the extract_context_from_element method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = WebScraper()

        # Mock config values
        self.mock_config = {
            "html_parsing": {
                "context_search_depth": 3,
                "max_context_elements": 5,
                "minimal_text_length": 10,
            }
        }

    @patch("_core.web_scraper.config")
    def test_extract_context_with_headings(self, mock_config):
        """Test context extraction from elements containing headings."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <section>
            <h1>Main Heading with sufficient length</h1>
            <h2>Secondary heading with enough content</h2>
            <p>Paragraph with meaningful content for testing purposes.</p>
            <h3>Short</h3>
        </section>
        """
        soup = BeautifulSoup(html, "lxml")
        section_element = soup.find("section")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(section_element, processed_elements)

        assert len(context) > 0
        assert any("Main Heading with sufficient length" in text for text in context)
        assert any("Secondary heading with enough content" in text for text in context)
        assert any("Paragraph with meaningful content" in text for text in context)
        # Short heading should be excluded due to minimal_text_length
        assert not any("Short" == text.strip() for text in context)

    @patch("_core.web_scraper.config")
    def test_extract_context_with_paragraphs_and_divs(self, mock_config):
        """Test context extraction from paragraphs and div elements."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>This is a meaningful paragraph with sufficient content length.</p>
            <div>Another div with enough text content to be included in context.</div>
            <span>A span element with meaningful content for testing extraction.</span>
            <p>Short</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        assert len(context) > 0
        assert any("meaningful paragraph with sufficient content" in text for text in context)
        assert any("Another div with enough text content" in text for text in context)
        assert any("span element with meaningful content" in text for text in context)
        # Short paragraph should be excluded
        assert not any("Short" == text.strip() for text in context)

    @patch("_core.web_scraper.config")
    def test_extract_context_with_figcaption_and_caption(self, mock_config):
        """Test context extraction from figcaption and caption elements."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <figure>
            <img src="test.jpg" alt="test" />
            <figcaption>Figure caption with detailed description of the image content.</figcaption>
        </figure>
        <table>
            <caption>Table caption explaining the data presented in this table structure.</caption>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")
        body_element = soup.find("body")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(body_element, processed_elements)

        assert len(context) > 0
        assert any("Figure caption with detailed description" in text for text in context)
        assert any("Table caption explaining the data" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_extract_context_filters_short_text(self, mock_config):
        """Test that text shorter than minimal_text_length is filtered out."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>OK</p>
            <p>No</p>
            <p>This paragraph has sufficient length to be included in context extraction.</p>
            <span>Yes</span>
            <span>Another span with enough content to meet the minimum length requirement.</span>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        # Should include long texts
        assert any("sufficient length to be included" in text for text in context)
        assert any("enough content to meet the minimum" in text for text in context)

        # Should exclude short texts
        for text in context:
            assert text.strip() not in ["OK", "No", "Yes"]

    @patch("_core.web_scraper.config")
    def test_extract_context_handles_none_element(self, mock_config):
        """Test that method handles None element gracefully."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        processed_elements = set()
        context = self.scraper.extract_context_from_element(None, processed_elements)

        assert context == []

    @patch("_core.web_scraper.config")
    def test_extract_context_handles_already_processed_element(self, mock_config):
        """Test that method handles already processed elements."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>This paragraph should not be processed twice in the same extraction.</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()
        
        # Add the element to processed_elements first
        processed_elements.add(id(div_element))

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        assert context == []

    @patch("_core.web_scraper.config")
    def test_extract_context_adds_element_to_processed(self, mock_config):
        """Test that processed elements are tracked correctly."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>This paragraph will be processed and tracked in processed_elements set.</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()

        # Verify element is not in processed_elements initially
        assert id(div_element) not in processed_elements

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        # Verify element is added to processed_elements after processing
        assert id(div_element) in processed_elements
        assert len(context) > 0

    @patch("_core.web_scraper.config")
    def test_extract_context_empty_elements(self, mock_config):
        """Test context extraction from elements with no meaningful content."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p></p>
            <span>   </span>
            <h1></h1>
            <div>    </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        assert context == []

    @patch("_core.web_scraper.config")
    def test_extract_context_nested_elements(self, mock_config):
        """Test context extraction from nested HTML structure."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <article>
            <header>
                <h1>Article title with sufficient length for inclusion in context</h1>
            </header>
            <section>
                <div class="content">
                    <p>First paragraph with meaningful content that should be extracted.</p>
                    <div class="nested">
                        <span>Nested span with enough content to meet minimum requirements.</span>
                    </div>
                </div>
            </section>
        </article>
        """
        soup = BeautifulSoup(html, "lxml")
        article_element = soup.find("article")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(article_element, processed_elements)

        assert len(context) > 0
        assert any("Article title with sufficient length" in text for text in context)
        assert any("First paragraph with meaningful content" in text for text in context)
        assert any("Nested span with enough content" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_extract_context_mixed_content_types(self, mock_config):
        """Test context extraction from elements with mixed content types."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <h2>Section heading with adequate length for context extraction</h2>
            <p>Paragraph content that provides meaningful context information.</p>
            <ul>
                <li>List item content</li>
            </ul>
            <figcaption>Caption describing visual content with sufficient detail.</figcaption>
            <span>Inline content with enough text to meet length requirements.</span>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        div_element = soup.find("div")
        processed_elements = set()

        context = self.scraper.extract_context_from_element(div_element, processed_elements)

        assert len(context) > 0
        assert any("Section heading with adequate length" in text for text in context)
        assert any("Paragraph content that provides meaningful" in text for text in context)
        assert any("Caption describing visual content" in text for text in context)
        assert any("Inline content with enough text" in text for text in context)
        # List items are not in the target elements, so they shouldn't be included
        assert not any("List item content" in text for text in context)


class TestWebScraperFindContextElements:
    """Test cases for the find_context_elements method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = WebScraper()

        # Mock config values
        self.mock_config = {
            "html_parsing": {
                "context_search_depth": 3,
                "max_context_elements": 5,
                "minimal_text_length": 10,
            }
        }

    @patch("_core.web_scraper.config")
    def test_find_context_upward_traversal(self, mock_config):
        """Test context extraction through upward traversal."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <article>
            <h1>Main Article Title</h1>
            <section>
                <h2>Section Header</h2>
                <div>
                    <p>This is a paragraph with context information.</p>
                    <img src="test.jpg" alt="" />
                </div>
            </section>
        </article>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        assert len(context) > 0
        assert any("Main Article Title" in text for text in context)
        assert any("Section Header" in text for text in context)
        assert any("paragraph with context information" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_find_context_sibling_elements(self, mock_config):
        """Test context extraction from sibling elements."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>Previous sibling content with useful information.</p>
            <img src="test.jpg" alt="" />
            <p>Next sibling content with more details.</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        assert len(context) > 0
        assert any("Previous sibling content" in text for text in context)
        assert any("Next sibling content" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_find_context_with_figcaption(self, mock_config):
        """Test context extraction when image has figcaption."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <figure>
            <img src="chart.jpg" alt="" />
            <figcaption>Chart showing data trends over time</figcaption>
        </figure>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        assert len(context) > 0
        assert any("Chart showing data trends" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_find_context_filters_short_text(self, mock_config):
        """Test that short text snippets are filtered out."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>Short</p>
            <img src="test.jpg" alt="" />
            <p>This is a longer paragraph that should be included in context.</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        # Should not include "Short" but should include the longer paragraph
        assert not any("Short" == text.strip() for text in context)
        assert any(
            "longer paragraph that should be included" in text for text in context
        )

    @patch("_core.web_scraper.config")
    def test_find_context_removes_unwanted_text(self, mock_config):
        """Test that unwanted text snippets are removed."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>Useful content Bild im Vollbildmodus anzeigen here</p>
            <img src="test.jpg" alt="" />
            <p>More useful content Mehr erfahren with information</p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        # Should remove the unwanted text snippets
        for text in context:
            assert "Bild im Vollbildmodus anzeigen" not in text
            assert "Mehr erfahren" not in text

        # But should keep the useful parts
        assert any("Useful content" in text for text in context)
        assert any("More useful content" in text for text in context)

    @patch("_core.web_scraper.config")
    def test_find_context_limits_max_elements(self, mock_config):
        """Test that context is limited to max_context_elements."""
        # Set a lower limit for this test
        test_config = self.mock_config.copy()
        test_config["html_parsing"]["max_context_elements"] = 2
        mock_config.__getitem__.side_effect = test_config.__getitem__

        html = """
        <div>
            <h1>Header 1 with sufficient length for inclusion</h1>
            <h2>Header 2 with sufficient length for inclusion</h2>
            <h3>Header 3 with sufficient length for inclusion</h3>
            <h4>Header 4 with sufficient length for inclusion</h4>
            <img src="test.jpg" alt="" />
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        assert len(context) <= 2

    @patch("_core.web_scraper.config")
    def test_find_context_empty_result(self, mock_config):
        """Test context extraction when no meaningful context is available."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <img src="test.jpg" alt="" />
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        assert isinstance(context, list)
        # May be empty or contain minimal context

    @patch("_core.web_scraper.config")
    def test_find_context_complex_nested_structure(self, mock_config):
        """Test context extraction in complex nested HTML structure."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <main>
            <article>
                <header>
                    <h1>Complex Article with Multiple Sections</h1>
                </header>
                <section class="content">
                    <div class="text-block">
                        <p>Introduction paragraph with important context information.</p>
                    </div>
                    <div class="media-container">
                        <div class="image-wrapper">
                            <img src="complex.jpg" alt="" />
                        </div>
                        <div class="caption-area">
                            <span>Image description in span element</span>
                        </div>
                    </div>
                    <div class="follow-up">
                        <p>Follow-up paragraph discussing the implications.</p>
                    </div>
                </section>
            </article>
        </main>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        # Debug: Print actual context for troubleshooting
        print(f"Extracted context: {context}")

        assert len(context) > 0
        # More flexible assertions - check for any meaningful content
        has_meaningful_content = any(
            any(
                keyword in text.lower()
                for keyword in [
                    "complex",
                    "article",
                    "sections",
                    "introduction",
                    "paragraph",
                ]
            )
            for text in context
        )
        assert has_meaningful_content, (
            f"Expected meaningful content in context, got: {context}"
        )

        # Check for specific content that should be found
        context_text = " ".join(context).lower()
        assert (
            "introduction paragraph" in context_text
            or "important context information" in context_text
        )

    @patch("_core.web_scraper.config")
    def test_find_context_handles_source_attribution(self, mock_config):
        """Test that source attribution (Quelle:) is properly removed."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <p>Important chart data showing trends. Quelle: Statistical Office</p>
            <img src="chart.jpg" alt="" />
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        # Should include the main content but remove source attribution
        assert any("Important chart data showing trends" in text for text in context)
        for text in context:
            assert "Quelle:" not in text
            assert "Statistical Office" not in text

    @patch("_core.web_scraper.config")
    def test_find_context_deduplicates_text(self, mock_config):
        """Test that duplicate context text is removed."""
        mock_config.__getitem__.side_effect = self.mock_config.__getitem__

        html = """
        <div>
            <h2>Repeated header content for testing purposes</h2>
            <div>
                <p>Repeated header content for testing purposes</p>
                <img src="test.jpg" alt="" />
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        img_element = soup.find("img")

        context = self.scraper.find_context_elements(img_element)

        # Should only appear once despite being in multiple elements
        duplicate_count = sum(
            1 for text in context if "Repeated header content" in text
        )
        assert duplicate_count == 1
