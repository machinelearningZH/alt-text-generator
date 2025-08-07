import json
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import config
from .logger import get_logger
from .models import ImageInfo
from .llm_processing import AltTextGenerator
from .web_scraper import WebScraper
from .exporter import ExcelExporter

logger = get_logger(__name__)


class BatchProcessor:
    """Handles batch processing of images for alt text generation."""

    def __init__(self):
        """Initialize the batch processor."""
        self.generator = AltTextGenerator()
        self.max_workers = config["llm"]["max_workers"]

    def _create_result_dict(
        self, 
        url: str, 
        context: str = "", 
        original_alt_text: str = "", 
        generated_alt_text: Optional[str] = None, 
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized result dictionary."""
        return {
            "url": url,
            "context": context,
            "original_alt_text": original_alt_text,
            "generated_alt_text": generated_alt_text,
            "success": generated_alt_text is not None,
            **({"error": error} if error else {})
        }

    def _process_parallel(
        self,
        items: List[Any],
        processor_func: Callable,
        progress_callback: Optional[Callable] = None,
        max_workers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generic parallel processing function."""
        if not items:
            return []

        # Use configured max_workers if not specified
        if max_workers is None:
            max_workers = self.max_workers

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(processor_func, item): item for item in items
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if progress_callback:
                        if isinstance(item, str):
                            # URL processing
                            progress_callback(
                                item, 
                                result["success"], 
                                result["generated_alt_text"]
                            )
                        else:
                            # ImageInfo processing
                            progress_callback(
                                item, 
                                result["success"], 
                                result["generated_alt_text"]
                            )
                        
                except Exception as e:
                    # Create error result based on item type
                    if isinstance(item, str):
                        error_result = self._create_result_dict(
                            url=item, 
                            error=str(e)
                        )
                    else:
                        error_result = self._create_result_dict(
                            url=item.url,
                            context=item.context,
                            original_alt_text=item.alt_text,
                            error=str(e)
                        )
                    
                    results.append(error_result)
                    
                    if progress_callback:
                        progress_callback(item, False, None)

        return results

    def process_single_image(
        self, image_path_or_url: str, context: str = "", alt_text: str = ""
    ) -> Dict[str, Any]:
        """Process a single image and return result."""
        # Handle local file paths
        if Path(image_path_or_url).exists():
            # Convert local file to absolute path, then to file:// URL for consistency
            absolute_path = Path(image_path_or_url).resolve()
            image_path_or_url = absolute_path.as_uri()

        image_info = ImageInfo(
            url=image_path_or_url, context=context, alt_text=alt_text
        )

        try:
            result = self.generator.generate_alt_text(image_info)
            return self._create_result_dict(
                url=image_path_or_url,
                context=context,
                original_alt_text=alt_text,
                generated_alt_text=result
            )
        except Exception as e:
            return self._create_result_dict(
                url=image_path_or_url,
                context=context,
                original_alt_text=alt_text,
                error=str(e)
            )

    def process_url_list(
        self, 
        urls: List[str], 
        context: str = "", 
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[str, bool, Optional[str]], None]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple image URLs in parallel."""
        
        def process_single_url(url: str) -> Dict[str, Any]:
            """Process a single URL and return result."""
            image_info = ImageInfo(url=url, context=context)
            alt_text = self.generator.generate_alt_text(image_info)
            return self._create_result_dict(
                url=url,
                context=context,
                generated_alt_text=alt_text
            )

        return self._process_parallel(
            items=urls,
            processor_func=process_single_url,
            progress_callback=progress_callback,
            max_workers=max_workers
        )

    def process_urls_from_file(
        self, 
        file_path: str, 
        context: str = "", 
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[str, bool, Optional[str]], None]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple image URLs from a text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []

        return self.process_url_list(urls, context, max_workers, progress_callback)

    def scrape_and_process_webpage(
        self, 
        url: str, 
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[ImageInfo, bool, Optional[str]], None]] = None
    ) -> List[Dict[str, Any]]:
        """Scrape images from a webpage and generate alt texts."""
        try:
            scraper = WebScraper()
            images = scraper.scrape_page(url)
        except Exception as e:
            logger.error(f"Failed to scrape webpage {url}: {str(e)}")
            return []

        if not images:
            logger.warning(f"No images found on webpage: {url}")
            return []

        def process_image_info(image_info: ImageInfo) -> Dict[str, Any]:
            """Process an ImageInfo object and return result."""
            alt_text = self.generator.generate_alt_text(image_info)
            return self._create_result_dict(
                url=image_info.url,
                context=image_info.context,
                original_alt_text=image_info.alt_text,
                generated_alt_text=alt_text
            )

        return self._process_parallel(
            items=images,
            processor_func=process_image_info,
            progress_callback=progress_callback,
            max_workers=max_workers
        )

    def process_websites_from_file(
        self, 
        file_path: str, 
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple websites from a text file and scrape images from each."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []

        if not urls:
            logger.warning(f"No valid URLs found in {file_path}")
            return []

        all_results = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls, 1):
            if progress_callback:
                progress_callback(url, i, total_urls)
            
            try:
                # Scrape and process each website
                website_results = self.scrape_and_process_webpage(url, max_workers)
                
                # Add website metadata to each result
                for result in website_results:
                    result["source_website"] = url
                    result["website_order"] = i
                
                all_results.extend(website_results)
                
                logger.info(f"Processed website {i}/{total_urls}: {url} - found {len(website_results)} images")
                
            except Exception as e:
                logger.error(f"Failed to process website {url}: {str(e)}")
                # Add an error result for this website
                error_result = self._create_result_dict(
                    url=url,
                    error=f"Failed to process website: {str(e)}"
                )
                error_result["source_website"] = url
                error_result["website_order"] = i
                all_results.append(error_result)

        return all_results

    def export_results(
        self, 
        results: List[Dict[str, Any]], 
        output_file: str, 
        format_type: str = "json"
    ) -> bool:
        """Export results to a file."""
        try:
            output_path = Path(output_file)

            if format_type.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                logger.info(f"Results exported to {output_path}")
                return True

            elif format_type.lower() == "excel":
                # For websites processing, we need to handle additional metadata
                has_website_data = any(result.get("source_website") for result in results)
                
                if has_website_data:
                    # Create a DataFrame directly for websites processing
                    import pandas as pd
                    
                    data = []
                    for result in results:
                        if result["success"]:
                            row = {
                                "source_website": result.get("source_website", ""),
                                "image_url": result["url"],
                                "original_alt_text": result.get("original_alt_text", ""),
                                "generated_alt_text": result.get("generated_alt_text", ""),
                                "context": result.get("context", ""),
                                "website_order": result.get("website_order", "")
                            }
                            data.append(row)
                    
                    if data:
                        df = pd.DataFrame(data)
                        
                        # Create and write Excel file
                        from io import BytesIO
                        excel_buffer = BytesIO()
                        
                        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                            df.to_excel(
                                writer, sheet_name="Website Alt Text Results", index=False, header=True
                            )
                            
                            # Auto-adjust column widths
                            worksheet = writer.sheets["Website Alt Text Results"]
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
                                adjusted_width = min(max_length + 2, 50)
                                worksheet.column_dimensions[column_letter].width = adjusted_width

                        # Write the buffer to file
                        with open(output_path, "wb") as f:
                            f.write(excel_buffer.getvalue())

                        logger.info(f"Results exported to {output_path}")
                        return True
                    else:
                        logger.warning("No successful results to export")
                        return False
                else:
                    # Use existing ImageInfo-based export for single webpage/batch processing
                    images = []
                    for result in results:
                        if result["success"]:
                            img = ImageInfo(
                                url=result["url"],
                                alt_text=result.get("original_alt_text", ""),
                                context=result.get("context", ""),
                                suggested_alt_text=result.get("generated_alt_text", ""),
                            )
                            images.append(img)

                    if images:
                        exporter = ExcelExporter()
                        excel_buffer = exporter.create_file(images)

                        # Write the buffer to file
                        with open(output_path, "wb") as f:
                            f.write(excel_buffer.getvalue())

                        logger.info(f"Results exported to {output_path}")
                        return True
                    else:
                        logger.warning("No successful results to export")
                        return False

            else:
                logger.error(f"Unsupported export format: {format_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to export results: {str(e)}")
            return False
