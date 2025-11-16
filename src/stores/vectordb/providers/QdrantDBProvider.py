from ..VectorDBInterface import VectorDBInterface
from qdrant_client import QdrantClient, models
from ..VectorDBEnums import DistanceMethodEnums
from models.db_schemas import RetrievedDocument
from typing import List
import logging


class QdrantDBProvider(VectorDBInterface):
    """
    A vector database provider that uses Qdrant.
    """

    def __init__(
        self,
        db_client: str,
        default_vector_size: int = 1024,
        distance_method: str = None,
        index_threshold: int = 100,
    ):
        """
        Initializes the QdrantDBProvider.

        Args:
            db_client (str): The path to the Qdrant database.
            default_vector_size (int, optional): The default vector size. Defaults to 1024.
            distance_method (str, optional): The distance method to use. Defaults to None.
            index_threshold (int, optional): The minimum number of records required to create an index. Defaults to 100.
        """
        self.db_client = db_client
        self.distance_method = None
        self.client = None
        self.default_vector_size = default_vector_size

        # Map the distance method to the corresponding Qdrant distance method
        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        """
        Connects to the Qdrant database.
        """
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        """
        Disconnects from the Qdrant database.
        """
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        """
        Checks if a collection exists in the Qdrant database.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self) -> List:
        """
        Lists all collections in the Qdrant database.

        Returns:
            List: A list of all collections.
        """
        return self.client.get_collections()

    async def get_collection_info(self, collection_name: str) -> dict:
        """
        Gets information about a collection.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            dict: A dictionary containing information about the collection.
        """
        return self.client.get_collection(collection_name=collection_name)

    async def delete_collection(self, collection_name: str):
        """
        Deletes a collection from the Qdrant database.

        Args:
            collection_name (str): The name of the collection to delete.
        """
        if self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        """
        Creates a new collection in the Qdrant database.

        Args:
            collection_name (str): The name of the collection to create.
            embedding_size (int): The size of the embeddings to be stored in the collection.
            do_reset (bool, optional): Whether to reset the collection if it already exists. Defaults to False.

        Returns:
            bool: True if the collection was created successfully, False otherwise.
        """
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)

        if not self.is_collection_existed(collection_name):
            self.logger.info(
                f"Creating new Qdrant collection: {collection_name} with embedding size: {embedding_size}"
            )

            # Create a new collection with the specified vector parameters
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_method
                ),
            )

            return True

        return False

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

        Returns:
            bool: True if the record was inserted successfully, False otherwise.
        """
        if not self.is_collection_existed(collection_name):
            self.logger.error(
                f"Can not insert new record to non-existed collection: {collection_name}"
            )
            return False

        try:
            # Upload a single record to the collection
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=record_id,
                        vector=vector,
                        payload={"text": text, "metadata": metadata},
                    )
                ],
            )

        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True

    async def insert_many(
        self,
        collection_name: str,
        texts: list,
        vectors: list,
        metadata: list = None,
        record_ids: list = None,
        batch_size: int = 50,
    ):
        """
        Inserts multiple records into a collection.

        Args:
            collection_name (str): The name of the collection.
            texts (list): A list of texts to insert.
            vectors (list): A list of vectors corresponding to the texts.
            metadata (list, optional): A list of metadata for each record. Defaults to None.
            record_ids (list, optional): A list of IDs for each record. Defaults to None.
            batch_size (int, optional): The number of records to insert in each batch. Defaults to 50.

        Returns:
            bool: True if the records were inserted successfully, False otherwise.
        """
        if metadata is None:
            metadata = list(range(0, len(texts)))

        if record_ids is None:
            record_ids = [None] * len(texts)

        # Insert records in batches
        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={"text": batch_texts[x], "metadata": batch_metadata[x]},
                )
                for x in range(len(batch_texts))
            ]

            try:
                # Upload a batch of records to the collection
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int = 5
    ):
        """
        Searches for similar vectors in a collection.

        Args:
            collection_name (str): The name of the collection to search in.
            vector (list): The vector to search for.
            limit (int, optional): The maximum number of results to return. Defaults to 5.

        Returns:
            List[RetrievedDocument]: A list of retrieved documents, or None if no results were found.
        """
        # Search for the most similar vectors
        results = self.client.search(
            collection_name=collection_name, query_vector=vector, limit=limit
        )
        if not results or len(results) == 0:
            return None
        return [
            RetrievedDocument(**{"score": result.score, "text": result.payload["text"]})
            for result in results
        ]
