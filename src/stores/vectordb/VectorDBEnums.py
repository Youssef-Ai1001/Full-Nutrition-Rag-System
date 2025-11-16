from enum import Enum


class VectorDBEnums(Enum):
    """
    This enum represents the supported vector database providers.
    """

    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"


class DistanceMethodEnums(Enum):
    """
    This enum represents the supported distance methods.
    """

    COSINE = "cosine"
    DOT = "dot"


class PgVectorTableSchemeEnums(Enum):
    """
    This enum represents the table scheme for the pgvector extension.
    """

    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector"


class PgVectorDistanceMethodEnums(Enum):
    """
    This enum represents the distance methods for the pgvector extension.
    """

    COSINE = "vector_cosine_ops"
    DOT = "vector_l2_ops"


class PgVectorIndexTypeEnums(Enum):
    """
    This enum represents the index types for the pgvector extension.
    """

    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
