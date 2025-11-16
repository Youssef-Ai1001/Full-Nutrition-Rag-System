from .providers import QdrantDBProvider, PGVectorProvider
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker


class VectorDBProviderFactory:
    """
    A factory class for creating vector database providers.

    This class is responsible for creating instances of vector database providers
    based on the provided configuration. It supports different providers like
    Qdrant and PGVector.
    """

    def __init__(self, config: dict, db_client: sessionmaker = None):
        """
        Initializes the VectorDBProviderFactory.

        Args:
            config (dict): A dictionary containing the configuration for the vector database.
            db_client (sessionmaker, optional): The database client. Defaults to None.
        """
        self.config = config
        self.base_controller = BaseController()
        self.db_client = db_client

    def create(self, provider_name: str):
        """
        Creates a vector database provider instance.

        Args:
            provider_name (str): The name of the provider to create.

        Returns:
            An instance of the vector database provider, or None if the provider is not supported.
        """
        # Check if the provider is Qdrant
        if provider_name == VectorDBEnums.QDRANT.value:
            # Get the path to the Qdrant database
            qdrant_db_client = self.base_controller.get_database_path(
                db_name=self.config.VECTOR_DB_PATH
            )
            # Create and return a QdrantDBProvider instance
            return QdrantDBProvider(
                db_client=qdrant_db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        # Check if the provider is PGVector
        if provider_name == VectorDBEnums.PGVECTOR.value:
            # Create and return a PGVectorProvider instance
            return PGVectorProvider(
                db_client=self.db_client,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        # Return None if the provider is not supported
        return None
