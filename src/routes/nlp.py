from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schema.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
import logging
from controllers import NLPController
from models import ResponseSignal
from tqdm.auto import tqdm


logger = logging.getLogger("uvicorn.error")

# Create an API router for the NLP endpoints
nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(
    request: Request,
    project_id: int,
    push_request: PushRequest,
):
    """
    Indexes the data of a project into the vector database.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project to index.
        push_request (PushRequest): The request body.

    Returns:
        JSONResponse: A JSON response indicating the status of the indexing process.
    """

    # Create model instances
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    # Get the project from the database
    project = await project_model.get_or_create_project(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value},
        )

    # Create an NLP controller instance
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0

    # step 1 : create collection if not exists
    collection_name = nlp_controller.create_collection_name(project_id=project.id)
    _ = await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        embedding_size=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_reset,
    )

    # step 2 : Batch process chunks
    total_chunks_count = await chunk_model.get_chunks_count_by_project_id(
        project_id=project.id
    )

    # Create a progress bar
    pbar = tqdm(
        total=total_chunks_count, desc="Indexing Chunks", unit="chunk", position=0
    )

    # Process chunks in batches
    while has_records:
        page_chunks = await chunk_model.get_project_chunks(
            project_id=project.id, page_no=page_no
        )
        if len(page_chunks):
            page_no += 1

        if not page_chunks or len(page_chunks) == 0:
            has_records = 0
            break

        chunks_ids = [c.chunk_id for c in page_chunks]
        idx += len(page_chunks)

        # Index the chunks into the vector database
        is_inserted = await nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids=chunks_ids,
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"Signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value},
            )

        pbar.update(len(page_chunks))
        inserted_items_count += len(page_chunks)

    return JSONResponse(
        content={
            "Signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(
    request: Request,
    project_id: int,
):
    """
    Gets information about the index of a project.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project.

    Returns:
        JSONResponse: A JSON response containing the index information.
    """
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_or_create_project(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    # Get the collection information from the vector database
    collection_info = await nlp_controller.get_vector_db_collection_info(
        project=project
    )

    return JSONResponse(
        content={
            "Signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info,
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request,
    project_id: int,
    search_request: SearchRequest,
):
    """
    Searches the index of a project.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project.
        search_request (SearchRequest): The request body.

    Returns:
        JSONResponse: A JSON response containing the search results.
    """
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_or_create_project(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    # Search the vector database
    results = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value,
            },
        )

    return JSONResponse(
        content={
            "Signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": [result.dict() for result in results],
        },
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):
    """
    Answers a question using the RAG model.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project.
        search_request (SearchRequest): The request body.

    Returns:
        JSONResponse: A JSON response containing the answer.
    """

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_or_create_project(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    # Answer the question using the RAG model
    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project, query=search_request.text, limit=search_request.limit
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Signal": ResponseSignal.RAG_ANSWER_ERROR.value},
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history,
        }
    )
