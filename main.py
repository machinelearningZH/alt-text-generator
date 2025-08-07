import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from _core.logger import get_logger
from _core.web_scraper import WebScraper
from _core.llm_processing import AltTextGenerator
from _core.exporter import ExcelExporter
from _core.config import config
from _core.sample_urls import SAMPLE_URLS
from _core.app_info import APP_INFO
from _core.models import ImageInfo
import re
import tempfile
import os

st.set_page_config(
    page_title=config["app_name"],
    layout="wide",
    initial_sidebar_state="expanded",
)

logger = get_logger(__name__)


# Initialize session state
if "images" not in st.session_state:
    st.session_state.images = []
if "processed_url" not in st.session_state:
    st.session_state.processed_url = ""

# TODO: Find better name for this state variable
if "ai_generator" not in st.session_state:
    try:
        st.session_state.ai_generator = AltTextGenerator()
    except ValueError as e:
        st.error(f"❌ API-Konfigurationsfehler: {str(e)}")
        st.stop()


def display_image_safely(image_url: str):
    """Try to display an image, if it fails, show the URL."""
    try:
        st.image(image_url, width=config["ui"]["image_display_width"])
    except Exception as e:
        logger.warning(f"Could not display image {image_url}: {e}")
        # If image loading fails, show URL as a fallback
        st.markdown(f"🖼️ **Bild-URL (konnte nicht geladen werden):** {image_url}")


def regenerate_alt_text(image_index: int):
    """Regenerate alt text for a specific image."""
    if 0 <= image_index < len(st.session_state.images):
        image = st.session_state.images[image_index]

        with st.spinner(f"Erstelle neuen Alt-Text für Bild {image_index + 1}..."):
            logger.info(f"Regenerating alt text for image: {image.url}")
            new_alt_text = st.session_state.ai_generator.generate_alt_text(image)

            if new_alt_text:
                st.session_state.images[image_index].suggested_alt_text = new_alt_text
                st.success(f"✅ Neuer Alt-Text für Bild {image_index + 1} erstellt!")
                st.rerun()
            else:
                st.error(
                    f"❌ Fehler beim Erstellen des Alt-Texts für Bild {image_index + 1}"
                )


def process_uploaded_image(uploaded_file, context_text: str = ""):
    """Process an uploaded image and generate alt text."""
    try:
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}"
        ) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        # Create file:// URL for the temporary file
        file_url = f"file://{temp_file_path}"

        # Create ImageInfo object
        image_info = ImageInfo(
            url=file_url,
            alt_text="",  # No existing alt text for uploaded images
            context=context_text,
        )

        # Generate alt text
        with st.spinner("Erstelle Alt-Text für das hochgeladene Bild..."):
            logger.info(f"Generating alt text for uploaded image: {uploaded_file.name}")
            alt_text = st.session_state.ai_generator.generate_alt_text(image_info)

        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")

        return alt_text

    except Exception as e:
        logger.error(f"Error processing uploaded image {uploaded_file.name}: {str(e)}")
        return None


def process_url(url: str):
    """Process the URL and extract images."""
    # Clear previous results
    st.session_state.images = []
    st.session_state.processed_url = ""

    # Initialize scraper
    scraper = WebScraper()

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Validate URL
        status_text.text("🔍 Überprüfe URL...")
        progress_bar.progress(10)

        if not scraper.validate_url(url):
            st.error(
                "❌ URL ist nicht gültig, erreichbar oder gibt keinen HTML-Inhalt zurück."
            )
            return

        # Step 2: Scrape images
        status_text.text("📄 Analysiere Webseite...")
        progress_bar.progress(30)

        images = scraper.scrape_page(url)
        if not images:
            st.warning("⚠️ Keine unterstützten Bilder auf der Webseite gefunden.")
            return

        # Step 3: Generate alt texts
        status_text.text("Erstelle Alt-Texte...")

        total_images = len(images)
        completed_count = 0

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=config["llm"]["max_workers"]) as executor:
            # Submit all tasks
            future_to_image = {
                executor.submit(
                    st.session_state.ai_generator.generate_alt_text, image
                ): (i, image)
                for i, image in enumerate(images)
            }

            # Process completed tasks
            for future in as_completed(future_to_image):
                i, image = future_to_image[future]
                completed_count += 1

                progress = 30 + (60 * completed_count / total_images)
                progress_bar.progress(int(progress))
                status_text.text(
                    f"Erstelle Alt-Text für Bild {completed_count}/{total_images}..."
                )

                try:
                    alt_text = future.result()
                    if alt_text:
                        image.suggested_alt_text = alt_text
                except Exception as e:
                    logger.error(f"Error generating alt text for image {i}: {str(e)}")

        # Step 4: Complete
        progress_bar.progress(100)
        status_text.text("✅ Fertig!")

        # Save results
        st.session_state.images = images
        st.session_state.processed_url = url

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        st.success(f"🎉 {len(images)} Bilder erfolgreich analysiert!")

    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der URL: {str(e)}")
        logger.error(f"Error processing URL {url}: {str(e)}")


def main():
    """Main application function."""

    with st.sidebar:
        st.header(f"✍️ {config['app_name']}")
        st.markdown(APP_INFO)

    # Create tabs
    tab1, tab2 = st.tabs(["🌐 Website analysieren", "📁 Bild hochladen"])

    with tab1:
        st.markdown("### Website-Analyse")

        selected_sample = st.selectbox(
            "🔗 Beispiel-URL auswählen...",
            SAMPLE_URLS,
            help="Wähle eine vordefinierte URL zum Testen",
        )

        # Set default value based on sample selection
        default_url = "" if selected_sample == SAMPLE_URLS[0] else selected_sample

        url = st.text_input(
            "➡️ oder hier eine eigene URL eingeben...",
            value=default_url,
            placeholder="https://zh.ch",
            help="Gib die vollständige URL einer öffentlichen Webseite ein",
        )

        # Process button
        if st.button("🔍 Webseite analysieren", type="primary"):
            if url:
                process_url(url)
            else:
                st.error("Bitte gib eine URL ein.")

        # Display results for website analysis
        if st.session_state.images:
            st.markdown(f"**Analysierte URL:** {st.session_state.processed_url}")
            st.markdown(f"**Gefundene Bilder:** {len(st.session_state.images)}")

            # Export button
            exporter = ExcelExporter()
            excel_data = exporter.create_file(st.session_state.images)
            filename = exporter.get_filename()

            st.download_button(
                label="📊 Als Excel exportieren",
                data=excel_data.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.divider()

            # Display each image
            for i, image in enumerate(st.session_state.images):
                with st.container():
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.markdown(f"### Bild {i + 1}")
                        display_image_safely(image.url)

                        # Regenerate button
                        if st.button("🔄 Neu erstellen", key=f"regen_{i}"):
                            regenerate_alt_text(i)

                    with col2:
                        
                        # Create a link to the CMS URL if applicable
                        # Uncomment the following lines if you have a CMS link prefix configured
                        # config["cms"]["link_prefix"] should be defined in your config
                        # cms_url = image.url.replace(
                        #     "https://www.zh.ch", config["cms"]["link_prefix"]
                        # )
                        # # Find and split on image file extensions
                        # match = re.search(
                        #     r"\.(jpg|jpeg|png|webp)", cms_url, re.IGNORECASE
                        # )
                        # if match:
                        #     extension = match.group(0)
                        #     cms_url = cms_url.split(extension)[0] + extension
                        # st.markdown(f"[**Bild-URL im CMS**]({cms_url})")

                        st.markdown(f"[**Bild-URL auf Webseite**]({image.url})")

                        st.markdown("**Aktueller Alt-Text:**")
                        if image.alt_text:
                            st.info(image.alt_text)
                        else:
                            st.warning("Kein Alt-Text vorhanden")

                        st.markdown("**KI-generierter Alt-Text (Deutsch):**")
                        if image.suggested_alt_text:
                            st.success(image.suggested_alt_text)
                        else:
                            st.error("Fehler beim Erstellen des Alt-Texts")

                        if image.context:
                            with st.expander("📝 Kontext der Webseite"):
                                st.text(
                                    image.context[: config["ui"]["max_context_display"]]
                                    + "..."
                                    if len(image.context)
                                    > config["ui"]["max_context_display"]
                                    else image.context
                                )

                    st.divider()

    with tab2:
        st.markdown("### Einzelnes Bild hochladen")

        # File upload
        uploaded_file = st.file_uploader(
            "📁 Bild auswählen",
            type=["png", "jpg", "jpeg", "webp"],
            help="Unterstützte Formate: PNG, JPG, JPEG, WebP",
        )

        # Optional context input
        context_text = st.text_area(
            "📝 Kontext (optional)",
            placeholder="Beschreibe den Kontext des Bildes, z.B. wo es verwendet wird oder was es zeigt...",
            help="Zusätzlicher Kontext hilft bei der Erstellung besserer Alt-Texte",
            height=100,
        )

        # Process uploaded image
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("### Hochgeladenes Bild")
                st.image(uploaded_file, width=config["ui"]["image_display_width"])

                # Generate button
                if st.button(
                    "🤖 Alt-Text erstellen", type="primary", key="generate_upload"
                ):
                    alt_text = process_uploaded_image(uploaded_file, context_text)

                    if alt_text:
                        st.session_state.uploaded_alt_text = alt_text
                        st.success("✅ Alt-Text erfolgreich erstellt!")
                        st.rerun()
                    else:
                        st.error("❌ Fehler beim Erstellen des Alt-Texts")

            with col2:
                st.markdown("### Ergebnis")

                if hasattr(st.session_state, "uploaded_alt_text"):
                    st.markdown("**KI-generierter Alt-Text (Deutsch):**")
                    st.success(st.session_state.uploaded_alt_text)

                    # Option to regenerate
                    if st.button("🔄 Neu erstellen", key="regen_upload"):
                        alt_text = process_uploaded_image(uploaded_file, context_text)

                        if alt_text:
                            st.session_state.uploaded_alt_text = alt_text
                            st.success("✅ Neuer Alt-Text erstellt!")
                            st.rerun()
                        else:
                            st.error("❌ Fehler beim Erstellen des Alt-Texts")

                if context_text:
                    with st.expander("📝 Verwendeter Kontext"):
                        st.text(context_text)


if __name__ == "__main__":
    main()
