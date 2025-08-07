"""
CLI tool for generating alt texts for images.

This command-line interface allows you to generate alt texts for:
- Single images (local files or URLs)
- Multiple images from URLs in a text file
- Images from a webpage
- Multiple websites from a list of URLs
- Batch processing with parallel execution
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import _core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from _core.config import config
from _core.logger import get_logger
from _core.cli_processor import BatchProcessor
from _core.models import ImageInfo

logger = get_logger(__name__)


class ProgressDisplay:
    """Handles progress display for different operations."""
    
    @staticmethod
    def single_image_progress(image_path_or_url: str) -> None:
        """Display progress for single image processing."""
        print(f"🖼️  Processing image: {image_path_or_url}")
        print("🤖 Generating alt text...")
    
    @staticmethod
    def batch_progress(url: str, success: bool, alt_text: Optional[str]) -> None:
        """Display progress for batch processing."""
        status = "✅" if success else "❌"
        print(f"{status} {url}")
        if success and alt_text:
            print(f"   Alt text: {alt_text}")
    
    @staticmethod
    def scrape_progress(image_info: ImageInfo, success: bool, alt_text: Optional[str]) -> None:
        """Display progress for web scraping."""
        status = "✅" if success else "❌"
        print(f"{status} {image_info.url}")
        if success and alt_text:
            print(f"   Generated: {alt_text}")
            if image_info.alt_text:
                print(f"   Original:  {image_info.alt_text}")


class AltTextCLI:
    """Command-line interface for alt text generation."""

    def __init__(self):
        """Initialize the CLI with the batch processor."""
        try:
            self.processor = BatchProcessor()
            self.default_max_workers = config["llm"]["max_workers"]
        except ValueError as e:
            print(f"❌ API Configuration Error: {str(e)}")
            print("Please ensure OPENROUTER_API_KEY is set in your environment.")
            sys.exit(1)

    def generate_single_image(
        self, image_path_or_url: str, context: str = "", alt_text: str = ""
    ) -> Optional[str]:
        """Generate alt text for a single image."""
        ProgressDisplay.single_image_progress(image_path_or_url)
        
        result = self.processor.process_single_image(image_path_or_url, context, alt_text)
        
        if result["success"]:
            print(f"✅ Generated alt text: {result['generated_alt_text']}")
            return result["generated_alt_text"]
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Failed to generate alt text: {error_msg}")
            return None

    def process_and_export(
        self, 
        source: str, 
        output_file: Optional[str] = None,
        format_type: str = "json",
        context: str = "", 
        max_workers: Optional[int] = None,
        is_webpage: bool = False
    ) -> bool:
        """Process images and optionally export results."""
        if max_workers is None:
            max_workers = self.default_max_workers
            
        # Determine processing type and execute
        if is_webpage:
            print(f"🕷️  Scraping images from: {source}")
            results = self.processor.scrape_and_process_webpage(
                source, max_workers, ProgressDisplay.scrape_progress
            )
        else:
            print(f"📋 Processing images from: {source}")
            results = self.processor.process_urls_from_file(
                source, context, max_workers, ProgressDisplay.batch_progress
            )
        
        if not results:
            error_msg = "No images found on the webpage" if is_webpage else f"No valid URLs found in {source}"
            print(f"❌ {error_msg}")
            return False

        successful = sum(1 for r in results if r["success"])
        print(f"\n📊 Processed {len(results)} images, {successful} successful")
        
        # Export results if output file is specified
        if output_file:
            export_success = self.processor.export_results(results, output_file, format_type)
            if export_success:
                print(f"📄 Results exported to {output_file}")
            else:
                print("❌ Failed to export results")
                return False
        
        return successful > 0

    def process_websites_and_export(
        self, 
        source: str, 
        output_file: Optional[str] = None,
        format_type: str = "json",
        max_workers: Optional[int] = None
    ) -> bool:
        """Process multiple websites and optionally export results."""
        if max_workers is None:
            max_workers = self.default_max_workers
            
        print(f"🌐 Processing websites from: {source}")
        
        def website_progress(url: str, current: int, total: int) -> None:
            """Display progress for website processing."""
            print(f"🕷️  Processing website {current}/{total}: {url}")
        
        results = self.processor.process_websites_from_file(
            source, max_workers, website_progress
        )
        
        if not results:
            print(f"❌ No images found from websites in {source}")
            return False

        successful = sum(1 for r in results if r["success"])
        total_websites = len(set(r.get("source_website", "") for r in results if r.get("source_website")))
        
        print(f"\n📊 Processed {total_websites} websites, found {len(results)} images, {successful} successful")
        
        # Export results if output file is specified
        if output_file:
            export_success = self.processor.export_results(results, output_file, format_type)
            if export_success:
                print(f"📄 Results exported to {output_file}")
            else:
                print("❌ Failed to export results")
                return False
        
        return successful > 0


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate alt texts for images using AI",
        epilog=f"""
Examples:
  %(prog)s single image.jpg --context "Product photo"
  %(prog)s single https://example.com/image.png
  %(prog)s batch urls.txt --output results.json
  %(prog)s scrape https://example.com --output webpage_images.xlsx --format excel
  %(prog)s websites website_urls.txt --output all_websites.xlsx --format excel
  %(prog)s batch urls.txt --workers {config['llm']['max_workers']} --context "Marketing images"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Single image command
    single_parser = subparsers.add_parser(
        "single", help="Generate alt text for a single image"
    )
    single_parser.add_argument("image", help="Path to local image file or URL")
    single_parser.add_argument(
        "--context", "-c", default="", help="Additional context for the image"
    )
    single_parser.add_argument(
        "--alt-text", "-a", default="", help="Existing alt text (for improvement)"
    )

    # Batch processing command
    batch_parser = subparsers.add_parser(
        "batch", help="Process multiple images from a URL list file"
    )
    batch_parser.add_argument(
        "file", help="Text file containing image URLs (one per line)"
    )
    batch_parser.add_argument(
        "--context", "-c", default="", help="Additional context for all images"
    )
    batch_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {config['llm']['max_workers']})",
    )
    batch_parser.add_argument("--output", "-o", help="Output file for results")
    batch_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "excel"],
        default="json",
        help="Output format (default: json)",
    )

    # Web scraping command
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape images from a webpage and generate alt texts"
    )
    scrape_parser.add_argument("url", help="URL of the webpage to scrape")
    scrape_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {config['llm']['max_workers']})",
    )
    scrape_parser.add_argument("--output", "-o", help="Output file for results")
    scrape_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "excel"],
        default="json",
        help="Output format (default: json)",
    )

    # Website batch processing command
    websites_parser = subparsers.add_parser(
        "websites", help="Process multiple websites from a URL list file"
    )
    websites_parser.add_argument(
        "file", help="Text file containing website URLs (one per line)"
    )
    websites_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {config['llm']['max_workers']})",
    )
    websites_parser.add_argument("--output", "-o", help="Output file for results")
    websites_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "excel"],
        default="json",
        help="Output format (default: json)",
    )

    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize the CLI
    cli = AltTextCLI()

    try:
        if args.command == "single":
            # Fix for the alt-text argument conversion
            alt_text = getattr(args, "alt_text", "")
            result = cli.generate_single_image(
                args.image, context=args.context, alt_text=alt_text
            )
            if not result:
                sys.exit(1)

        elif args.command == "batch":
            success = cli.process_and_export(
                source=args.file,
                output_file=args.output,
                format_type=args.format,
                context=args.context,
                max_workers=args.workers,
                is_webpage=False
            )
            if not success:
                sys.exit(1)

        elif args.command == "scrape":
            success = cli.process_and_export(
                source=args.url,
                output_file=args.output,
                format_type=args.format,
                max_workers=args.workers,
                is_webpage=True
            )
            if not success:
                sys.exit(1)

        elif args.command == "websites":
            success = cli.process_websites_and_export(
                source=args.file,
                output_file=args.output,
                format_type=args.format,
                max_workers=args.workers
            )
            if not success:
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        logger.exception("Unexpected error in CLI")
        sys.exit(1)


if __name__ == "__main__":
    main()
