# src/summarization/multimodal_summarizer.py

import logging
from pathlib import Path
from typing import Dict

from src.llm.ollama_client import OllamaClient
from src.processing.parsers.base_parser import DocumentChunk

logger = logging.getLogger(__name__)

class MultimodalSummarizer:
    """
    Generates summaries of DocumentChunks using an LLM client and external prompt templates.
    """
    def __init__(self, llm_client: OllamaClient, prompt_templates: Dict[str, Path]):
        """
        Initializes the summarizer.

        Args:
            llm_client (OllamaClient): The LLM client that will be used to generate the summaries.
            prompt_templates (Dict[str, Path]): A dictionary mapping the type of prompt 
                                                (e.g., 'text', 'image') to the path of its file.
        """
        self.llm_client = llm_client
        self.prompt_templates = prompt_templates
        self.loaded_prompts = {} # Cache to avoid reading the same file multiple times
        logger.info("Multimodal Summarizer initialized with external prompt templates.")

    def _load_prompt(self, prompt_type: str) -> str:
        """
        Loads a prompt template from a file, using a simple cache.

        Args:
            prompt_type (str): The type of prompt to load ('text', 'image', 'table').

        Returns:
            str: The content of the prompt template.
        """
        if prompt_type in self.loaded_prompts:
            return self.loaded_prompts[prompt_type]

        prompt_path = self.prompt_templates.get(prompt_type)
        if not prompt_path or not prompt_path.exists():
            logger.error(f"Prompt template not found for type '{prompt_type}' at path: {prompt_path}")
            # Return a generic prompt as fallback
            return "Summarize the following content as best as possible:"

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            self.loaded_prompts[prompt_type] = prompt_content
            logger.debug(f"Prompt template for '{prompt_type}' loaded from {prompt_path}")
            return prompt_content
        except Exception as e:
            logger.error(f"Error reading prompt file {prompt_path}: {e}")
            return "Summarize the following content:"

    def summarize_chunk(self, chunk: DocumentChunk) -> str:
        """
        Takes a DocumentChunk, generates a prompt from a template, and obtains a summary.

        Args:
            chunk (DocumentChunk): The document chunk to be summarized.

        Returns:
            str: The generated summary.
        """
        logger.debug(f"Generating summary for chunk of type '{chunk.type}' on page {chunk.source_page}.")
        
        prompt_template = self._load_prompt(chunk.type)
        
        # The content of 'image' and 'table' chunks is the image in base64.
        # In your pdf_parser.py, you had also converted tables into images.
        images_b64 = [chunk.content] if chunk.type in ('image', 'table') else None

        if chunk.type == 'text':
            prompt = prompt_template.format(text_content=chunk.content)
        else: # For 'image' and 'table'
            prompt = prompt_template
            # Optionally, add caption context if it exists
            if caption := chunk.metadata.get("caption"):
                prompt += f"\nAdditional caption context: '{caption}'"

        summary = self.llm_client.generate_response(prompt, images_base64=images_b64)
        
        logger.info(f"Summary generated for chunk of type '{chunk.type}': '{summary[:100]}...'")
        return summary
