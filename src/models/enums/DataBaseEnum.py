from enum import Enum


class DataBaseEnum(str, Enum):
    """
    This enum represents the names of the collections in the database.
    """

    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_CHUNK_NAME = "chunks"
    COLLECTION_ASSET_NAME = "assets"
