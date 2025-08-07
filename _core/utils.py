import base64
import mimetypes


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')


def detect_image_mime_type(image_url: str, image_bytes: bytes) -> str:
    """Detect the MIME type of an image from URL or content."""
    # Try to get MIME type from URL extension first
    mime_type, _ = mimetypes.guess_type(image_url)
    if mime_type and mime_type.startswith('image/'):
        return mime_type
    
    # Fallback: detect from magic bytes
    if image_bytes.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:12]:
        return 'image/webp'
    elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
        return 'image/gif'
    
    # Default fallback
    return 'image/jpeg'


def clean_alt_text(alt_text: str) -> str:
    """Clean and validate alt text."""
    alt_text = alt_text.strip().replace("ß", "ss")
    if not alt_text:
        return ""
    
    # Remove surrounding quotes
    text = alt_text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    
    return text.strip()
