import pandas as pd
from datetime import datetime
from typing import List
from io import BytesIO
from abc import ABC, abstractmethod
from .logger import get_logger
from .config import config
from .models import ImageInfo

logger = get_logger(__name__)


class BaseExporter(ABC):
    """Abstract base class for data exporters."""

    @abstractmethod
    def prepare_data(self, images: List[ImageInfo]) -> List[dict]:
        """Prepare image data for export.

        Args:
            images: List of ImageInfo objects to prepare for export

        Returns:
            List of dictionaries containing prepared data
        """
        pass

    @abstractmethod
    def create_file(self, images: List[ImageInfo]) -> BytesIO:
        """Create a file from image data and return as BytesIO.

        Args:
            images: List of ImageInfo objects to export

        Returns:
            BytesIO buffer containing the exported file
        """
        pass

    @abstractmethod
    def get_filename(self) -> str:
        """Generate a filename for the export.

        Returns:
            String containing the filename
        """
        pass


class ExcelExporter(BaseExporter):
    """Utility class for exporting results to Excel format."""

    def __init__(self):
        # Generate columns list from config keys
        self.columns = [
            config["excel"]["image_url"],
            config["excel"]["alt_text_bisher"],
            config["excel"]["vorgeschlagener_alt_text"],
        ]

    def prepare_data(self, images: List[ImageInfo]) -> List[dict]:
        """Prepare image data for Excel export."""
        data = []
        for img in images:
            row = {
                config["excel"]["image_url"]: img.url,
                config["excel"]["alt_text_bisher"]: img.alt_text or "",
                config["excel"]["vorgeschlagener_alt_text"]: img.suggested_alt_text
                or "",
            }
            data.append(row)
        return data

    def create_file(self, images: List[ImageInfo]) -> BytesIO:
        """Create an Excel file from image data and return as BytesIO."""
        try:
            # Prepare data
            data = self.prepare_data(images)

            # Create DataFrame
            df = pd.DataFrame(data, columns=self.columns)

            # Create BytesIO buffer
            excel_buffer = BytesIO()

            # Write to Excel
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(
                    writer, sheet_name="Alt Text Results", index=False, header=True
                )

                # Get the worksheet
                worksheet = writer.sheets["Alt Text Results"]

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass

                    # Set column width (with some padding)
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            # Reset buffer position
            excel_buffer.seek(0)

            return excel_buffer

        except Exception as e:
            logger.error(f"Error creating Excel file: {str(e)}")
            raise

    def get_filename(self) -> str:
        """Generate a filename for the Excel export."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"alt_text_results_{timestamp}.xlsx"
