import base64
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from _core.utils import encode_image_to_base64, detect_image_mime_type, clean_alt_text


class TestEncodeImageToBase64:
    """Test cases for the encode_image_to_base64 function."""

    def test_encode_empty_bytes(self):
        """Test encoding empty bytes."""
        result = encode_image_to_base64(b'')
        expected = base64.b64encode(b'').decode('utf-8')
        assert result == expected

    def test_encode_sample_bytes(self):
        """Test encoding sample bytes."""
        test_bytes = b'Hello, World!'
        result = encode_image_to_base64(test_bytes)
        expected = base64.b64encode(test_bytes).decode('utf-8')
        assert result == expected
        assert result == 'SGVsbG8sIFdvcmxkIQ=='

    def test_encode_binary_data(self):
        """Test encoding binary data like image bytes."""
        # Simulate JPEG header bytes
        jpeg_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        result = encode_image_to_base64(jpeg_bytes)
        expected = base64.b64encode(jpeg_bytes).decode('utf-8')
        assert result == expected

    def test_encode_large_data(self):
        """Test encoding larger binary data."""
        large_data = b'x' * 1000
        result = encode_image_to_base64(large_data)
        expected = base64.b64encode(large_data).decode('utf-8')
        assert result == expected

    def test_return_type_is_string(self):
        """Test that function returns a string."""
        result = encode_image_to_base64(b'test')
        assert isinstance(result, str)


class TestDetectImageMimeType:
    """Test cases for the detect_image_mime_type function."""

    @patch('mimetypes.guess_type')
    def test_detect_from_url_extension_jpg(self, mock_guess_type):
        """Test MIME type detection from URL extension - JPEG."""
        mock_guess_type.return_value = ('image/jpeg', None)
        
        result = detect_image_mime_type('https://example.com/image.jpg', b'dummy')
        assert result == 'image/jpeg'
        mock_guess_type.assert_called_once_with('https://example.com/image.jpg')

    @patch('mimetypes.guess_type')
    def test_detect_from_url_extension_png(self, mock_guess_type):
        """Test MIME type detection from URL extension - PNG."""
        mock_guess_type.return_value = ('image/png', None)
        
        result = detect_image_mime_type('https://example.com/image.png', b'dummy')
        assert result == 'image/png'

    @patch('mimetypes.guess_type')
    def test_detect_from_url_extension_webp(self, mock_guess_type):
        """Test MIME type detection from URL extension - WebP."""
        mock_guess_type.return_value = ('image/webp', None)
        
        result = detect_image_mime_type('https://example.com/image.webp', b'dummy')
        assert result == 'image/webp'

    @patch('mimetypes.guess_type')
    def test_url_non_image_mime_type_fallback_to_magic_bytes(self, mock_guess_type):
        """Test fallback to magic bytes when URL doesn't indicate image."""
        mock_guess_type.return_value = ('text/plain', None)
        
        # JPEG magic bytes
        jpeg_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        result = detect_image_mime_type('https://example.com/file.txt', jpeg_bytes)
        assert result == 'image/jpeg'

    @patch('mimetypes.guess_type')
    def test_url_no_mime_type_fallback_to_magic_bytes(self, mock_guess_type):
        """Test fallback to magic bytes when URL has no MIME type."""
        mock_guess_type.return_value = (None, None)
        
        # PNG magic bytes
        png_bytes = b'\x89PNG\r\n\x1a\n'
        result = detect_image_mime_type('https://example.com/unknown', png_bytes)
        assert result == 'image/png'

    @patch('mimetypes.guess_type')
    def test_detect_jpeg_from_magic_bytes(self, mock_guess_type):
        """Test JPEG detection from magic bytes."""
        mock_guess_type.return_value = (None, None)
        
        jpeg_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        result = detect_image_mime_type('https://example.com/unknown', jpeg_bytes)
        assert result == 'image/jpeg'

    @patch('mimetypes.guess_type')
    def test_detect_png_from_magic_bytes(self, mock_guess_type):
        """Test PNG detection from magic bytes."""
        mock_guess_type.return_value = (None, None)
        
        png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR'
        result = detect_image_mime_type('https://example.com/unknown', png_bytes)
        assert result == 'image/png'

    @patch('mimetypes.guess_type')
    def test_detect_webp_from_magic_bytes(self, mock_guess_type):
        """Test WebP detection from magic bytes."""
        mock_guess_type.return_value = (None, None)
        
        webp_bytes = b'RIFF\x00\x00\x00\x00WEBP'
        result = detect_image_mime_type('https://example.com/unknown', webp_bytes)
        assert result == 'image/webp'

    @patch('mimetypes.guess_type')
    def test_detect_gif87a_from_magic_bytes(self, mock_guess_type):
        """Test GIF87a detection from magic bytes."""
        mock_guess_type.return_value = (None, None)
        
        gif_bytes = b'GIF87a\x00\x00\x00\x00'
        result = detect_image_mime_type('https://example.com/unknown', gif_bytes)
        assert result == 'image/gif'

    @patch('mimetypes.guess_type')
    def test_detect_gif89a_from_magic_bytes(self, mock_guess_type):
        """Test GIF89a detection from magic bytes."""
        mock_guess_type.return_value = (None, None)
        
        gif_bytes = b'GIF89a\x00\x00\x00\x00'
        result = detect_image_mime_type('https://example.com/unknown', gif_bytes)
        assert result == 'image/gif'

    @patch('mimetypes.guess_type')
    def test_unknown_format_defaults_to_jpeg(self, mock_guess_type):
        """Test that unknown format defaults to JPEG."""
        mock_guess_type.return_value = (None, None)
        
        unknown_bytes = b'UNKNOWN_FORMAT\x00\x00\x00\x00'
        result = detect_image_mime_type('https://example.com/unknown', unknown_bytes)
        assert result == 'image/jpeg'

    @patch('mimetypes.guess_type')
    def test_empty_bytes_defaults_to_jpeg(self, mock_guess_type):
        """Test that empty bytes default to JPEG."""
        mock_guess_type.return_value = (None, None)
        
        result = detect_image_mime_type('https://example.com/unknown', b'')
        assert result == 'image/jpeg'

    @patch('mimetypes.guess_type')
    def test_partial_magic_bytes_defaults_to_jpeg(self, mock_guess_type):
        """Test that partial magic bytes default to JPEG."""
        mock_guess_type.return_value = (None, None)
        
        # Only first byte of JPEG magic
        partial_bytes = b'\xff'
        result = detect_image_mime_type('https://example.com/unknown', partial_bytes)
        assert result == 'image/jpeg'

    def test_webp_magic_bytes_boundary_case(self):
        """Test WebP detection with WEBP at position 8."""
        # RIFF header + 4 bytes size + WEBP
        webp_bytes = b'RIFF\x12\x34\x56\x78WEBP'
        result = detect_image_mime_type('https://example.com/unknown', webp_bytes)
        assert result == 'image/webp'

    def test_webp_magic_bytes_not_found_in_range(self):
        """Test that WEBP not found outside first 12 bytes."""
        # WEBP appears after position 12, should not be detected
        not_webp_bytes = b'RIFF\x12\x34\x56\x78XXXX\x00\x00WEBP'
        result = detect_image_mime_type('https://example.com/unknown', not_webp_bytes)
        assert result == 'image/jpeg'  # Should fall back to default


class TestCleanAltText:
    """Test cases for the clean_alt_text function."""

    def test_clean_empty_string(self):
        """Test cleaning empty string."""
        result = clean_alt_text("")
        assert result == ""

    # Note: The function signature expects str, so None is not a valid input
    # according to the type hints, even though the function handles falsy values

    def test_clean_whitespace_only(self):
        """Test cleaning whitespace-only string."""
        result = clean_alt_text("   \t\n  ")
        assert result == ""

    def test_clean_normal_text(self):
        """Test cleaning normal text without quotes."""
        text = "A beautiful sunset over the mountains"
        result = clean_alt_text(text)
        assert result == text

    def test_clean_text_with_leading_trailing_spaces(self):
        """Test cleaning text with leading and trailing spaces."""
        result = clean_alt_text("  A beautiful sunset  ")
        assert result == "A beautiful sunset"

    def test_clean_double_quoted_text(self):
        """Test cleaning text wrapped in double quotes."""
        result = clean_alt_text('"A beautiful sunset over the mountains"')
        assert result == "A beautiful sunset over the mountains"

    def test_clean_single_quoted_text(self):
        """Test cleaning text wrapped in single quotes."""
        result = clean_alt_text("'A beautiful sunset over the mountains'")
        assert result == "A beautiful sunset over the mountains"

    def test_clean_double_quoted_with_spaces(self):
        """Test cleaning double-quoted text with surrounding spaces."""
        result = clean_alt_text('  "A beautiful sunset"  ')
        assert result == "A beautiful sunset"

    def test_clean_single_quoted_with_spaces(self):
        """Test cleaning single-quoted text with surrounding spaces."""
        result = clean_alt_text("  'A beautiful sunset'  ")
        assert result == "A beautiful sunset"

    def test_clean_mismatched_quotes_double_single(self):
        """Test that mismatched quotes are not removed - double then single."""
        text = '"A beautiful sunset\''
        result = clean_alt_text(text)
        assert result == text

    def test_clean_mismatched_quotes_single_double(self):
        """Test that mismatched quotes are not removed - single then double."""
        text = '\'A beautiful sunset"'
        result = clean_alt_text(text)
        assert result == text

    def test_clean_only_opening_quote(self):
        """Test text with only opening quote."""
        text = '"A beautiful sunset'
        result = clean_alt_text(text)
        assert result == text

    def test_clean_only_closing_quote(self):
        """Test text with only closing quote."""
        text = 'A beautiful sunset"'
        result = clean_alt_text(text)
        assert result == text

    def test_clean_empty_quotes_double(self):
        """Test cleaning empty double quotes."""
        result = clean_alt_text('""')
        assert result == ""

    def test_clean_empty_quotes_single(self):
        """Test cleaning empty single quotes."""
        result = clean_alt_text("''")
        assert result == ""

    def test_clean_quotes_with_only_spaces_double(self):
        """Test cleaning double quotes containing only spaces."""
        result = clean_alt_text('"   "')
        assert result == ""

    def test_clean_quotes_with_only_spaces_single(self):
        """Test cleaning single quotes containing only spaces."""
        result = clean_alt_text("'   '")
        assert result == ""

    def test_clean_nested_quotes(self):
        """Test cleaning text with nested quotes - outer quotes removed."""
        result = clean_alt_text('"She said \'Hello\' to me"')
        assert result == "She said 'Hello' to me"

    def test_clean_text_with_internal_quotes(self):
        """Test cleaning text with quotes in the middle (not wrapping)."""
        text = 'The word "beautiful" describes it'
        result = clean_alt_text(text)
        assert result == text

    def test_clean_text_with_newlines_and_tabs(self):
        """Test cleaning text with newlines and tabs inside quotes."""
        result = clean_alt_text('"A beautiful\n\tsunset"')
        assert result == "A beautiful\n\tsunset"

    def test_clean_unicode_text(self):
        """Test cleaning Unicode text."""
        result = clean_alt_text('"A beautiful sunset 🌅 über den Bergen"')
        assert result == "A beautiful sunset 🌅 über den Bergen"

    def test_clean_very_long_text(self):
        """Test cleaning very long text."""
        long_text = "A " + "very " * 100 + "long description"
        quoted_text = f'"{long_text}"'
        result = clean_alt_text(quoted_text)
        assert result == long_text

    def test_return_type_is_string(self):
        """Test that function always returns a string."""
        test_cases = [
            "",
            "normal text",
            '"quoted text"',
            "'quoted text'",
            "   whitespace   "
        ]
        
        for case in test_cases:
            result = clean_alt_text(case)
            assert isinstance(result, str)
