
import base64
import io
import logging
from pathlib import Path
from typing import List, Optional
import tempfile 

from PIL.Image import Image
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import DocItem, PictureItem, TableItem, TextItem, TitleItem

from .base_parser import BaseParser, DocumentChunk

# Configure a logger for this module
logger = logging.getLogger(__name__)

class PdfParser(BaseParser):
    """
    A specific parser for PDF documents that uses the Docling library.
    Extracts text, tables, and images in an order organized by page.
    """

    def __init__(self, image_resolution_scale: float = 2.0):
        """
        Initializes the Docling converter and the parser's state.
        """
        logger.info(f"Initializing PdfParser with image scale: {image_resolution_scale}")
        pipeline_options = PdfPipelineOptions(
            images_scale=image_resolution_scale,
            generate_page_images=True,
            generate_picture_images=True
        )
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        
        # State variables for the last parsed document
        self.chunks: List[DocumentChunk] = []
        self._doc: Optional[DocItem] = None
        self._doc_path: Optional[Path] = None

    def _image_to_base64(self, image: Image) -> str:
        """Converts a PIL image object to a base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _load_and_get_doc(self, file_path: Path) -> DocItem:
        """Helper to load document with Docling if not already loaded."""
        if self._doc is None or self._doc_path != file_path:
            logger.info(f"Loading document from: {file_path.name}")
            conv_res = self.converter.convert(str(file_path))
            self._doc = conv_res.document
            self._doc_path = file_path
        return self._doc

    def parse(self, file_path: str | Path) -> List[DocumentChunk]:
        """
        Processes a PDF file and extracts its content into a structured list of chunks.
        This method updates the internal state of the parser (chunks and counts).
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        logger.info(f"Starting to parse PDF: {file_path.name}")
        
        doc = self._load_and_get_doc(file_path)
        
        # Reset state for the new document
        self.chunks = []
        text_count, table_count, image_count = 0, 0, 0

        # Iterate through each page to get the content in order and the page number.
        for element, _level in doc.iterate_items():
            prov_list = getattr(element, "prov", [])
            logger.info(f"***************")
            logger.info(f"element: {element}")
            logger.info(f"_level: {_level}")
            logger.info(f"prov_list: {prov_list}")
            
            page_num = prov_list[0].page_no if prov_list and hasattr(prov_list[0], "page_no") else 0
            logger.info(f"page_num: {page_num}")
            logger.info(f"***************")
            chunk = None
            if isinstance(element, (TextItem, TitleItem)):
                if element.text.strip():  # Only add if not empty
                    chunk = DocumentChunk(
                        content=element.text, type="text", source_page=page_num,
                        metadata={"type": type(element).__name__}
                    )
                    text_count += 1
            elif isinstance(element, TableItem):
                # Save table as image
                image = element.get_image(doc=doc)
                image_b64 = self._image_to_base64(image)
                caption = element.caption_text(doc=doc)
                chunk = DocumentChunk(
                    content=image_b64, type="table", source_page=page_num,
                    metadata={"caption": caption if caption else ""}
                )
                table_count += 1
            elif isinstance(element, PictureItem):
                image = element.get_image(doc=doc)
                image_b64 = self._image_to_base64(image)
                caption = element.caption_text(doc=doc)
                chunk = DocumentChunk(
                    content=image_b64, type="image", source_page=page_num,
                    metadata={"caption": caption if caption else ""}
                )
                image_count += 1  
            # Add chunk to list              
            if chunk:
                self.chunks.append(chunk)

        logger.info(f"Parsing complete. Extracted {len(self.chunks)} total chunks.")
        logger.info(f"Summary: {text_count} text chunks, {table_count} table chunks, {image_count} image chunks.")
        return self.chunks

    # --- GETTER METHODS ---
    def get_text_chunks(self) -> List[DocumentChunk]:
        """Returns only the text chunks from the last parsed document."""
        return [chunk for chunk in self.chunks if chunk.type == 'text']

    def get_table_chunks(self) -> List[DocumentChunk]:
        """Returns only the table chunks from the last parsed document."""
        return [chunk for chunk in self.chunks if chunk.type == 'table']

    def get_image_chunks(self) -> List[DocumentChunk]:
        """Returns only the image chunks from the last parsed document."""
        return [chunk for chunk in self.chunks if chunk.type == 'image']

    # --- SAVER METHODS ---
    def save_tables_as_images(self, file_path: str | Path, output_dir: str | Path):
        """Finds all tables in the document and saves them as PNG images."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
            
        output_dir.mkdir(parents=True, exist_ok=True)
        doc = self._load_and_get_doc(file_path)
        doc_filename = file_path.stem
        
        table_counter = 0
        for element, _ in doc.iterate_items():
            if isinstance(element, TableItem):
                table_counter += 1
                image = element.get_image(doc)
                save_path = output_dir / f"{doc_filename}-table-{table_counter}.png"
                image.save(save_path, "PNG")
                logger.debug(f"Saved table image to {save_path}")
        logger.info(f"Saved {table_counter} tables as images to '{output_dir}'.")

    def save_pictures_as_images(self, file_path: str | Path, output_dir: str | Path):
        """Finds all pictures in the document and saves them as PNG images."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
            
        output_dir.mkdir(parents=True, exist_ok=True)
        doc = self._load_and_get_doc(file_path)
        doc_filename = file_path.stem
        
        picture_counter = 0
        for element, _ in doc.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                image = element.get_image(doc)
                save_path = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
                image.save(save_path, "PNG")
                logger.debug(f"Saved picture image to {save_path}")
        logger.info(f"Saved {picture_counter} pictures as images to '{output_dir}'.")

    def reconstruct_to_markdown(self, file_path: str | Path) -> str:
        """
        Reconstructs the PDF into a single Markdown file, with images embedded as base64.
        This method uses a temporary file because the underlying library function
        requires writing to a disk path.
        """
        from docling_core.types.doc import ImageRefMode
        if isinstance(file_path, str):
            file_path = Path(file_path)

        doc = self._load_and_get_doc(file_path)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=True, encoding='utf-8') as temp_md_file:
                temp_path = temp_md_file.name
                logger.info(f"Usando fichero temporal para la reconstrucción de Markdown: {temp_path}")
                
                doc.save_as_markdown(temp_path, image_mode=ImageRefMode.EMBEDDED)
                
                temp_md_file.seek(0)
                markdown_content = temp_md_file.read()

            logger.info(f"Reconstrucción a Markdown completada y leída desde el fichero temporal.")
            return markdown_content

        except Exception as e:
            logger.error(f"Ocurrió un error durante la reconstrucción a Markdown: {e}")
            raise