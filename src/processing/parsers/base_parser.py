from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Any, Dict, Optional
from pathlib import Path

# We define the chunk type to have strict control over the possible values.
ChunkType = Literal["text", "table", "image"]

@dataclass
class DocumentChunk:
    """
    Represents a unit of information extracted from a document.
    This is the standard format that all parsers must return.
    """
    content: str  # Main content: text, table as markdown, or image as base64.
    type: ChunkType # texts, tables, images
    source_page: int
    metadata: Dict[str, Any]  # Additional metadata (e.g., image caption).

class BaseParser(ABC):
    """
    Abstract base class for all document parsers.
    Defines the contract that any parser must follow.
    """

    @abstractmethod
    def parse(self, file_path: str | Path) -> List[DocumentChunk]:
        """
        Takes the path to a file and processes it, returning a list of chunks.
        
        Args:
            file_path (str | Path): The path to the document to be processed.

        Returns:
            List[DocumentChunk]: An ordered list of the chunks extracted from the document.
        """
        pass

    def reconstruct_to_markdown(self, file_path: str | Path) -> Optional[str]:
        """
        (Optional) Reconstructs the original document into Markdown format.
        Not all parsers need to support this functionality.
        
        Args:
            file_path (str | Path): The path to the document to be processed.

        Returns:
            Optional[str]: A string with the content in Markdown, or None if not supported.
        """
        # By default, this functionality is not implemented.
        # Specific parsers may override this method.
        print(f"Markdown reconstruction is not implemented for {self.__class__.__name__}")
        return None
