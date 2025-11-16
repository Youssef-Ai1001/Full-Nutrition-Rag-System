from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from bson.objectid import ObjectId
from sqlalchemy.future import select
from sqlalchemy import func, delete


class ChunkModel(BaseDataModel):
    """
    This class handles all the database operations related to data chunks.
    """

    def __init__(self, db_client: object):
        """
        Initializes the ChunkModel.

        Args:
            db_client (object): The database client.
        """
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Creates an instance of the ChunkModel.

        Args:
            db_client (object): The database client.

        Returns:
            ChunkModel: An instance of the ChunkModel.
        """
        instance = cls(db_client)
        return instance

    async def insert_chunk(self, chunk: DataChunk):
        """
        Inserts a single chunk into the database.

        Args:
            chunk (DataChunk): The chunk to insert.

        Returns:
            DataChunk: The inserted chunk.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Add the chunk to the session
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)

        return chunk

    async def get_chunk(self, chunk_id: str):
        """
        Gets a single chunk from the database.

        Args:
            chunk_id (str): The ID of the chunk to get.

        Returns:
            DataChunk: The chunk, or None if it doesn't exist.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Select the chunk with the given ID
                result = await session.execute(
                    select(DataChunk).where(DataChunk.chunk_id == chunk_id)
                )
                chunk = result.scalar_one_or_none()
            return chunk

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        """
        Inserts multiple chunks into the database.

        Args:
            chunks (list): A list of chunks to insert.
            batch_size (int, optional): The number of chunks to insert in each batch. Defaults to 100.

        Returns:
            int: The number of inserted chunks.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Insert chunks in batches
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    session.add_all(batch)
            await session.commit()
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        """
        Deletes all chunks for a given project ID.

        Args:
            project_id (ObjectId): The ID of the project.

        Returns:
            int: The number of deleted chunks.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Delete all chunks with the given project ID
                stmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(stmt)
                await session.commit()
        return result.rowcount

    async def get_project_chunks(
        self, project_id: ObjectId, page_no: int = 1, page_size: int = 50
    ):
        """
        Gets all chunks for a given project ID.

        Args:
            project_id (ObjectId): The ID of the project.
            page_no (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The number of chunks per page. Defaults to 50.

        Returns:
            list: A list of chunks.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Select all chunks with the given project ID, with pagination
                stmt = (
                    select(DataChunk)
                    .where(DataChunk.chunk_project_id == project_id)
                    .offset((page_no - 1) * page_size)
                    .limit(page_size)
                )
                result = await session.execute(stmt)
                records = result.scalars().all()
        return records

    async def get_chunks_count_by_project_id(self, project_id: ObjectId):
        """
        Gets the total number of chunks for a given project ID.

        Args:
            project_id (ObjectId): The ID of the project.

        Returns:
            int: The total number of chunks.
        """
        total_count = 0
        async with self.db_client() as session:
            async with session.begin():
                # Get the total number of chunks with the given project ID
                count_sql = select(func.count(DataChunk.chunk_id)).where(
                    DataChunk.chunk_project_id == project_id
                )
                result = await session.execute(count_sql)
                total_count = result.scalar()
        return total_count
