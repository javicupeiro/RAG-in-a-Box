"""
Script de prueba para el PdfParser usando Docling.

Este script toma el nombre de un fichero PDF de la carpeta 'data/pdf/', lo procesa
para extraer chunks de texto, tablas e imágenes, y guarda los resultados en la
carpeta 'output/'.

Uso:
    Desde la raíz del proyecto (la carpeta 'mi_proyecto_rag'), ejecuta:
    python scripts/docling_pdf_parser.py <nombre_del_fichero.pdf>

Ejemplo:
    python scripts/docling_pdf_parser.py attention_is_all_you_need.pdf
"""
import sys
import argparse
import logging
from pathlib import Path

# Añadimos la raíz del proyecto al path de Python para poder importar desde 'src'
# Esto hace que el script sea ejecutable desde la carpeta raíz del proyecto.
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.processing.parsers.pdf_parser import PdfParser

# Definimos las rutas relativas a la raíz del proyecto
DATA_DIR = project_root / "data" / "pdf"
OUTPUT_DIR = project_root / "output"

def main():
    """Función principal del script."""
    
    # --- Configuración de Logging ---
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)

    # --- Configuración de Argumentos de Línea de Comandos ---
    parser = argparse.ArgumentParser(description="Procesa un fichero PDF con PdfParser.")
    parser.add_argument(
        "pdf_filename", 
        type=str, 
        help="Nombre del fichero PDF a procesar (debe estar en la carpeta 'data/pdf/')."
    )
    args = parser.parse_args()
    
    input_pdf_path = DATA_DIR / args.pdf_filename
    if not input_pdf_path.exists():
        logger.error(f"Error: El fichero '{input_pdf_path}' no existe.")
        sys.exit(1)

    # --- Lógica del Script ---
    logger.info("=" * 50)
    logger.info(f"Iniciando el procesamiento para: {args.pdf_filename}")
    logger.info("=" * 50)

    # 1. Crear el directorio de salida si no existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Los resultados se guardarán en: {OUTPUT_DIR}")

    # 2. Instanciar el parser
    pdf_parser = PdfParser()
    
    # 3. Extraer todos los chunks (texto, tablas, imágenes)
    pdf_parser.parse(input_pdf_path)

    # 4. Guardar imágenes de las tablas
    logger.info("Guardando tablas como imágenes...")
    pdf_parser.save_tables_as_images(input_pdf_path, OUTPUT_DIR)
    
    # 5. Guardar imágenes de las figuras
    logger.info("Guardando figuras como imágenes...")
    pdf_parser.save_pictures_as_images(input_pdf_path, OUTPUT_DIR)
    
    # 6. Reconstruir y guardar el PDF como Markdown
    logger.info("Reconstruyendo el documento a formato Markdown...")
    markdown_content = pdf_parser.reconstruct_to_markdown(input_pdf_path)
    
    markdown_filename = f"{input_pdf_path.stem}.md"
    markdown_output_path = OUTPUT_DIR / markdown_filename
    
    with open(markdown_output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    logger.info(f"Documento Markdown guardado en: {markdown_output_path}")
    
    logger.info("-" * 50)
    logger.info("Procesamiento completado con éxito.")
    logger.info("-" * 50)


if __name__ == "__main__":
    main()