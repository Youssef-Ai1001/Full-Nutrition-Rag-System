from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (
    PgVectorTableSchemeEnums,
    PgVectorIndexTypeEnums,
    DistanceMethodEnums,
    PgVectorDistanceMethodEnums,
)
import logging
from typing import List
from models.db_schemas import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VectorDBInterface):
    """
    A vector database provider that uses PostgreSQL with the pgvector extension.
    """

    def __init__(
        self,
        db_client: str,
        default_vector_size: int = 1024,
        distance_method: str = None,
        index_threshold: int = 100,
    ):
        """
        Initializes the PGVectorProvider.

        Args:
            db_client (str): The database client.
            default_vector_size (int, optional): The default vector size. Defaults to 1024.
            distance_method (str, optional): The distance method to use. Defaults to None.
            index_threshold (int, optional): The minimum number of records required to create an index. Defaults to 100.
        """
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold

        # Map the distance method to the corresponding pgvector distance method
        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method = PgVectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            distance_method = PgVectorDistanceMethodEnums.DOT.value

        self.pgvector_table_prefix = PgVectorTableSchemeEnums._PREFIX.value
        self.distance_method = distance_method

        self.logger = logging.getLogger("uvicorn")
        self.default_index_name = (
            lambda collection_name: f"{collection_name}_vector_idx"
        )

    async def connect(self):
        """
        Connects to the database and creates the vector extension if it doesn't exist.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Create the vector extension if it doesn't exist
                await session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
                await session.commit()

    async def disconnect(self):
        """
        Disconnects from the database.
        """
        engine = self.db_client.kw.get("bind")
        if engine:
            await engine.dispose()

    async def is_collection_existed(self, collection_name: str) -> bool:
        """
        Checks if a collection (table) exists in the database.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        record = None
        async with self.db_client() as session:
            async with session.begin():
                # Check if the table exists in the pg_tables
                list_tbl = sql_text(
                    "SELECT * FROM pg_tables WHERE tablename = :collection_name"
                )
                results = await session.execute(
                    list_tbl, {"collection_name": collection_name}
                )
                record = results.scalar_one_or_none()
        return record

    async def list_all_collections(self) -> List:
        """
        Lists all collections (tables) in the database that have the pgvector prefix.

        Returns:
            List: A list of collection names.
        """
        records = []
        async with self.db_client() as session:
            async with session.begin():
                # Select all tables that have the pgvector prefix
                list_tbl = sql_text(
                    "SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix"
                )
                results = await session.execute(
                    list_tbl, {"prefix": self.pgvector_table_prefix}
                )
                records = results.scalar().all()
        return records

    async def get_collection_info(self, collection_name: str) -> dict:
        """
        Gets information about a collection (table).

        Args:
            collection_name (str): The name of the collection.

        Returns:
            dict: A dictionary containing information about the collection, or None if the collection doesn't exist.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Get table information from pg_tables
                table_info_sql = sql_text(
                    f"""
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes 
                    FROM pg_tables 
                    WHERE tablename = '{collection_name}'
                """
                )
                # Get the number of records in the table
                count_sql = sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')

                table_info = await session.execute(table_info_sql)
                table_data = table_info.fetchone()
                if not table_data:
                    return None

                record_count = (await session.execute(count_sql)).scalar_one()

                return {
                    "table_info": dict(table_data._mapping),
                    "record_count": record_count,
                }

    async def delete_collection(self, collection_name: str):
        """
        Deletes a collection (table).

        Args:
            collection_name (str): The name of the collection.

        Returns:
            bool: True if the collection was deleted successfully.
        """
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")

                # Drop the table if it exists
                delete_sql = sql_text(f'DROP TABLE IF EXISTS "{collection_name}"')
                await session.execute(delete_sql)
                await session.commit()

        return True

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        """
        Creates a new collection (table).

        Args:
            collection_name (str): The name of the collection.
            embedding_size (int): The size of the embeddings.
            do_reset (bool, optional): Whether to reset the collection if it already exists. Defaults to False.

        Returns:
            bool: True if the collection was created successfully, False otherwise.
        """
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        is_collection_existed = await self.is_collection_existed(
            collection_name=collection_name
        )

        if not is_collection_existed:
            self.logger.info(f"Creating collection: {collection_name}")
            async with self.db_client() as session:
                async with session.begin():
                    # Create a new table with the specified columns
                    create_sql = sql_text(
                        f'CREATE TABLE "{collection_name}" ('
                        f"{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY,"
                        f"{PgVectorTableSchemeEnums.TEXT.value} text, "
                        f"{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), "
                        f"{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT '{{}}', "
                        f"{PgVectorTableSchemeEnums.CHUNK_ID.value} integer, "
                        f"FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)"
                        ")"
                    )
                    await session.execute(create_sql)
                    await session.commit()
            return True

        return False

    async def is_index_existed(self, collection_name: str) -> bool:
        """
        Checks if a vector index exists for a collection.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                # Check if the index exists in pg_indexes
                check_sql = sql_text(
                    f"""
                    SELECT 1
                    FROM pg_indexes
                    WHERE tablename = '{collection_name}'
                    AND indexname = '{index_name}'
                    """
                )

                results = await session.execute(check_sql)

                return bool(results.scalar_one_or_none())

    async def create_vector_index(
        self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value
    ):
        """
        Creates a vector index for a collection.

        Args:
            collection_name (str): The name of the collection.
            index_type (str, optional): The type of index to create. Defaults to PgVectorIndexTypeEnums.HNSW.value.

        Returns:
            bool: True if the index was created successfully, False otherwise.
        """
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            return False

        async with self.db_client() as session:
            async with session.begin():
                # Get the number of records in the table
                count_sql = sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')
                results = await session.execute(count_sql)
                records_count = results.scalar_one()

                # Only create an index if the number of records is above the threshold
                if records_count < self.index_threshold:
                    self.logger.info(
                        f"Skipping index creation for {collection_name} as record count {records_count} is below threshold {self.index_threshold}."
                    )
                    return False

                self.logger.info(
                    f"START: Creating vector index for collection: {collection_name}"
                )

                index_name = self.default_index_name(collection_name)

                # Create a new index on the vector column
                create_index_sql = sql_text(
                    f'CREATE INDEX "{index_name}" ON "{collection_name}" '
                    f"USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})"
                )
                await session.execute(create_index_sql)
                await session.commit()

                self.logger.info(
                    f"END: Created vector index for collection: {collection_name}"
                )

    async def reset_vector_index(
        self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value
    ) -> bool:
        """
        Resets the vector index for a collection.

        Args:
            collection_name (str): The name of the collection.
            index_type (str, optional): The type of index to create. Defaults to PgVectorIndexTypeEnums.HNSW.value.

        Returns:
            bool: True if the index was reset successfully.
        """
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                # Drop the index if it exists
                drop_sql = sql_text(f'DROP INDEX IF EXISTS "{index_name}"')
                await session.execute(drop_sql)

        return await self.create_vector_index(
            collection_name=collection_name, index_type=index_type
        )

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
        is_collection_existed = await self.is_collection_existed(
            collection_name=collection_name
        )
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        if not record_id:
            self.logger.error("record_id is required for inserting a document.")
            return False

        async with self.db_client() as session:
            async with session.begin():
                # Insert a new record into the table
                insert_sql = sql_text(
                    f'INSERT INTO "{collection_name}" '
                    f"({PgVectorTableSchemeEnums.TEXT.value}, "
                    f"{PgVectorTableSchemeEnums.VECTOR.value}, "
                    f"{PgVectorTableSchemeEnums.METADATA.value}, "
                    f"{PgVectorTableSchemeEnums.CHUNK_ID.value}) "
                    f"VALUES (:text, :vector, :metadata, :chunk_id)"
                )

                metadata_json = (
                    json.dumps(metadata, ensure_ascii=False)
                    if metadata is not None
                    else "{}"
                )

                await session.execute(
                    insert_sql,
                    {
                        "text": text,
                        "vector": "[" + ",".join([str(v) for v in vector]) + "]",
                        "metadata": metadata_json,
                        "chunk_id": record_id,
                    },
                )
                await session.commit()
                await self.create_vector_index(collection_name=collection_name)

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
        is_collection_existed = await self.is_collection_existed(
            collection_name=collection_name
        )

        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        if len(vectors) != len(record_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False

        if not metadata or len(metadata) == 0:
            metadata = [None] * len(texts)

        async with self.db_client() as session:
            async with session.begin():
                # Insert records in batches
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    batch_vectors = vectors[i : i + batch_size]
                    batch_metadata = metadata[i : i + batch_size]
                    batch_record_ids = record_ids[i : i + batch_size]

                    values = []

                    for _text, _vector, _metadata, _record_id in zip(
                        batch_texts, batch_vectors, batch_metadata, batch_record_ids
                    ):
                        metadata_json = (
                            json.dumps(_metadata, ensure_ascii=False)
                            if _metadata is not None
                            else "{}"
                        )
                        values.append(
                            {
                                "text": _text,
                                "vector": "["
                                + ",".join([str(v) for v in _vector])
                                + "]",
                                "metadata": metadata_json,
                                "chunk_id": _record_id,
                            }
                        )
                    # Insert a batch of records into the table
                    batch_insert_sql = sql_text(
                        f'INSERT INTO "{collection_name}" '
                        f"({PgVectorTableSchemeEnums.TEXT.value}, "
                        f"{PgVectorTableSchemeEnums.VECTOR.value}, "
                        f"{PgVectorTableSchemeEnums.METADATA.value}, "
                        f"{PgVectorTableSchemeEnums.CHUNK_ID.value}) "
                        f"VALUES (:text, :vector, :metadata, :chunk_id)"
                    )

                    await session.execute(batch_insert_sql, values)

        await self.create_vector_index(collection_name=collection_name)

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
            List[RetrievedDocument]: A list of retrieved documents, or False if the collection doesn't exist.
        """
        is_collection_existed = await self.is_collection_existed(
            collection_name=collection_name
        )

        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        vector = "[" + ",".join([str(v) for v in vector]) + "]"

        async with self.db_client() as session:
            async with session.begin():
                # Search for the most similar vectors using the specified distance method
                search_sql = sql_text(
                    f"SELECT {PgVectorTableSchemeEnums.TEXT.value} as text, 1 - ({PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) as score"
                    f' FROM "{collection_name}"'
                    " ORDER BY score DESC "
                    f"LIMIT {limit}"
                )

                results = await session.execute(search_sql, {"vector": vector})

                records = results.fetchall()

                return [
                    RetrievedDocument(text=record.text, score=record.score)
                    for record in records
                ]
