from .BaseController import BaseController
from models.db_schemas import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json


class NLPController(BaseController):
    """
    This class handles all the NLP-related operations, such as indexing data into the vector database,
    searching the vector database, and answering questions using the RAG model.
    """

    def __init__(
        self, vectordb_client, generation_client, embedding_client, template_parser
    ):
        """
        Initializes the NLPController.

        Args:
            vectordb_client: The vector database client.
            generation_client: The text generation client.
            embedding_client: The text embedding client.
            template_parser: The template parser for constructing prompts.
        """
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        """
        Creates a unique collection name for a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            str: The collection name.
        """
        return f"Collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()

    async def reset_vector_db_collection(self, project: Project):
        """
        Resets the vector database collection for a project.

        Args:
            project (Project): The project object.

        Returns:
            The result of the delete_collection operation.
        """
        collection_name = self.create_collection_name(project_id=project.id)
        return await self.vectordb_client.delete_collection(
            collection_name=collection_name
        )

    async def get_vector_db_collection_info(self, project: Project):
        """
        Gets information about the vector database collection for a project.

        Args:
            project (Project): The project object.

        Returns:
            dict: A dictionary containing information about the collection.
        """
        collection_name = self.create_collection_name(project_id=project.id)
        collection_info = await self.vectordb_client.get_collection_info(
            collection_name=collection_name
        )
        return json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))

    async def index_into_vector_db(
        self,
        project: Project,
        chunks: List[DataChunk],
        chunks_ids: List[int],
        do_reset: bool = False,
    ):
        """
        Indexes the given chunks into the vector database.

        Args:
            project (Project): The project object.
            chunks (List[DataChunk]): A list of data chunks to index.
            chunks_ids (List[int]): A list of chunk IDs.
            do_reset (bool, optional): Whether to reset the collection before indexing. Defaults to False.

        Returns:
            bool: True if the indexing was successful.
        """
        # step 1 : get collection name
        collection_name = self.create_collection_name(project_id=project.id)

        # step 2 : manage items
        texts = [rec.chunk_content for rec in chunks]
        metadata = [rec.chunk_metadata for rec in chunks]

        vectors = self.embedding_client.embed_text(
            prompt=texts, document_type=DocumentTypeEnum.DOCUMENT.value
        )

        # step 3 : create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # step 4 : insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=chunks_ids,
        )

        return True

    async def search_vector_db_collection(
        self, project: Project, text: str, limit: int = 5
    ):
        """
        Searches the vector database collection for a project.

        Args:
            project (Project): The project object.
            text (str): The text to search for.
            limit (int, optional): The maximum number of results to return. Defaults to 5.

        Returns:
            The search results, or False if no results were found.
        """
        # step 1 : get collection name
        query_vector = None
        collection_name = self.create_collection_name(project_id=project.id)

        # step 2 : get prompt embedding vector
        vectors = self.embedding_client.embed_text(
            prompt=text, document_type=DocumentTypeEnum.QUERY.value
        )

        if not vectors or len(vectors) == 0:
            return False

        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]

        if not query_vector:
            return False

        # step 3 : do semantic search
        results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name, vector=query_vector, limit=limit
        )

        if not results:
            return False

        return results

    async def answer_rag_question(self, project: Project, query: str, limit: int = 5):
        """
        Answers a question using the RAG model.

        Args:
            project (Project): The project object.
            query (str): The question to answer.
            limit (int, optional): The maximum number of documents to retrieve. Defaults to 5.

        Returns:
            A tuple containing the answer, the full prompt, and the chat history.
        """
        # step 1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return None

        # step 2: construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompt = "\n".join(
            [
                self.template_parser.get(
                    "rag",
                    "document_prompt",
                    {
                        "doc_num": idx + 1,
                        "chunk_text": self.generation_client.process_prompt(doc.text),
                    },
                )
                for idx, doc in enumerate(retrieved_documents)
            ]
        )

        footer_prompt = self.template_parser.get(
            "rag", "footer_prompt", {"query": query}
        )

        # step 3: Construct Generation Client Prompts
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ]

        full_prompt = "\n\n".join([documents_prompt, footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history,
        )

        return answer, full_prompt, chat_history
