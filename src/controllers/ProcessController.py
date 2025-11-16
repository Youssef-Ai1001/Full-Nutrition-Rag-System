from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessingEnum
from typing import List
from dataclasses import dataclass


@dataclass
class Document:
    page_content: str
    metadata: dict


class ProcessController(BaseController):
    """
    This class handles all the file processing and chunking operations.
    """

    def __init__(self, project_id: str):
        """
        Initializes the ProcessController.

        Args:
            project_id (str): The ID of the project.
        """
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        """
        Gets the extension of a file.

        Args:
            file_id (str): The ID of the file.

        Returns:
            str: The extension of the file.
        """
        return os.path.splitext(file_id)[-1].lower()

    def get_file_loader(self, file_id: str):
        """
        Gets the appropriate file loader for a given file.

        Args:
            file_id (str): The ID of the file.

        Returns:
            A file loader instance, or None if the file type is not supported.
        """

        file_ext = self.get_file_extension(file_id=file_id)

        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        # Return the appropriate loader based on the file extension
        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)

        return None

    def get_file_content(self, file_id: str):
        """
        Gets the content of a file.

        Args:
            file_id (str): The ID of the file.

        Returns:
            The content of the file, or None if the file cannot be loaded.
        """

        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load()

        return None

    def process_file_content(
        self,
        file_content: list,
        file_id: str,
        chunk_size: int = 100,
        overlap_size: int = 20,
    ):
        """
        Processes the content of a file into chunks.

        Args:
            file_content (list): The content of the file.
            file_id (str): The ID of the file.
            chunk_size (int, optional): The size of each chunk. Defaults to 100.
            overlap_size (int, optional): The size of the overlap between chunks. Defaults to 20.

        Returns:
            A list of chunks.
        """

        file_content_texts = [rec.page_content for rec in file_content]

        file_content_metadata = [rec.metadata for rec in file_content]

        chunks = self.process_simpler_splitter(
            texts=file_content_texts,
            metadatas=file_content_metadata,
            chunk_size=chunk_size,
            splitter_tag="\n",
        )

        return chunks

    def process_simpler_splitter(
        self,
        texts: List[str],
        metadatas: List[dict],
        chunk_size: int,
        splitter_tag: str = "\n",
    ) -> List[str]:
        """
        Processes texts into chunks using a simpler splitter based on a specified tag.

        Args:
            texts (List[str]): The list of texts to be chunked.
            metadatas (List[dict]): The list of metadata corresponding to each text.
            chunk_size (int): The size of each chunk.
            splitter_tag (str, optional): The tag used to split the texts. Defaults to "\n\n".

        Returns:
            List[str]: A list of chunked texts.
        """

        full_text = " ".join(texts)

        # split the full text using the specified splitter tag
        lines = [
            doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1
        ]

        chunks = []
        current_chunk = ""

        for line in lines:
            current_chunk += line + splitter_tag
            if len(current_chunk) >= chunk_size:
                chunks.append(Document(page_content=current_chunk.strip(), metadata={}))
                current_chunk = ""

        if len(current_chunk) >= 0:
            chunks.append(Document(page_content=current_chunk.strip(), metadata={}))

        return chunks
