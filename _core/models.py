from dataclasses import dataclass


@dataclass
class ImageInfo:
    """Data class to store image information."""
    url: str
    alt_text: str = ""
    context: str = ""
    suggested_alt_text: str = ""
    
    def __post_init__(self):
        """Validate and clean data after initialization."""
        self.url = self.url.strip()
        self.alt_text = self.alt_text.strip()
        self.context = self.context.strip()
        self.suggested_alt_text = self.suggested_alt_text.strip()
