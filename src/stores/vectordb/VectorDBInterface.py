from abc import abstractmethod, ABC
from typing import List
from models.db_schemas import RetrievedDocument


class VectorDBInterface(ABC):
    """
    An interface for interacting with a vector database.

    This class defines the abstract methods that any vector database provider
    should implement to ensure a consistent API for vector operations.
    """

    @abstractmethod
    async def connect(self):
        """
        Connects to the vector database.
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """
        Disconnects from the vector database.
        """
        pass

    @abstractmethod
    async def is_collection_existed(self, collection_name: str) -> bool:
        """
        Checks if a collection exists in the vector database.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        pass

    @abstractmethod
    async def list_all_collections(self) -> List:
        """
        Lists all collections in the vector database.

        Returns:
            List: A list of all collection names.
        """
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict:
        """
        Gets information about a collection.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            dict: A dictionary containing information about the collection.
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """
        Deletes a collection from the vector database.

        Args:
            collection_name (str): The name of the collection to delete.
        """
        pass

    @abstractmethod
    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        """
        Creates a new collection in the vector database.

        Args:
            collection_name (str): The name of the collection to create.
            embedding_size (int): The size of the embeddings to be stored in the collection.
            do_reset (bool, optional): Whether to reset the collection if it already exists. Defaults to False.
        """
        pass

    @abstractmethod
    async def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict = None,
        record_id: str = None,
    ):
        """
        Inserts a single record into a collection.

        Args:
            collection_name (str): The name of the collection.
            text (str): The text of the record.
            vector (list): The vector representation of the text.
            metadata (dict, optional): Additional metadata for the record. Defaults to None.
            record_id (str, optional): The ID of the record. Defaults to None.
        """
        pass

    @abstractmethod
    async def insert_many(
        self,
        collection_name: str,
        texts: list,
        vectors: list,
        metadata: list = None,
        record_id: list = None,
        batch_size: int = 50,
    ):
        """
        Inserts multiple records into a collection.

        Args:
            collection_name (str): The name of the collection.
            texts (list): A list of texts to insert.
            vectors (list): A list of vectors corresponding to the texts.
            metadata (list, optional): A list of metadata for each record. Defaults to None.
            record_id (list, optional): A list of IDs for each record. Defaults to None.
            batch_size (int, optional): The number of records to insert in each batch. Defaults to 50.
        """
        pass

    @abstractmethod
    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int
    ) -> List[RetrievedDocument]:
        """
        Searches for similar vectors in a collection.

        Args:
            collection_name (str): The name of the collection to search in.
            vector (list): The vector to search for.
            limit (int): The maximum number of results to return.

        Returns:
            List[RetrievedDocument]: A list of retrieved documents.
        """
        pass
