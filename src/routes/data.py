from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schema.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.db_schemas import DataChunk, Asset
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController

logger = logging.getLogger("uvicorn.error")

# Create an API router for the data endpoints
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_file(
    request: Request,
    project_id: int,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):
    """
    Uploads a file to a project.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project.
        file (UploadFile): The file to upload.
        app_settings (Settings, optional): The application settings. Defaults to Depends(get_settings).

    Returns:
        JSONResponse: A JSON response indicating the status of the file upload.
    """

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_or_create_project(project_id=project_id)

    # Validate the file properties
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"Signal": result_signal}
        )

    # Generate a unique file path
    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_file_path(
        orig_file_name=file.filename, project_id=project_id
    )

    try:
        # Write the file to the disk
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)

    except Exception as e:

        logger.error(f"Error while uploading file {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Signal": ResponseSignal.FILE_UPLOAD_FAILED.value},
        )

    # Store the asset in the database
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    # project.id is already an ObjectId
    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path),
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
        content={
            "Signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request, project_id: int, process_request: ProcessRequest
):
    """
    Processes the files of a project into chunks.

    Args:
        request (Request): The incoming request.
        project_id (int): The ID of the project.
        process_request (ProcessRequest): The request body.

    Returns:
        JSONResponse: A JSON response indicating the status of the processing.
    """

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_or_create_project(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    project_files_ids = {}
    if process_request.file_id:
        # Get the asset record for the given file ID
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.id,  # Use project.id which is an ObjectId
            asset_name=process_request.file_id,
        )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                },
            )

        project_files_ids = {asset_record.id: asset_record.asset_name}

    else:
        # Get all assets for the project
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {rec.asset_id: rec.asset_name for rec in project_files}

    if len(project_files_ids) == 0:
        logger.error(
            f"No files found for project {project_id}. Project ID in DB: {project.id}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
                "debug_info": {
                    "project_id": project_id,
                    "db_project_id": str(project.id),
                },
            },
        )

    process_controller = ProcessController(project_id=project_id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    # Reset the vector database collection and chunks if requested
    if do_reset == 1:
        collection_name = nlp_controller.create_collection_name(project_id=project.id)

        _ = await request.app.vectordb_client.delete_collection(
            collection_name=collection_name
        )

        deleted_count = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )
        logger.info(f"Deleted {deleted_count} existing chunks for project {project_id}")

    # Process each file
    for asset_id, file_id in project_files_ids.items():
        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue

        # Process the file content into chunks
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
        )

        if file_chunks is None or len(file_chunks) == 0:

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.PROCESSING_FAILED.value},
            )

        # Create DataChunk objects for each chunk
        file_chunks_records = [
            DataChunk(
                chunk_content=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.id,  # Already an ObjectId
                chunk_asset_id=asset_id,  # Already an ObjectId from the dict key
            )
            for i, chunk in enumerate(file_chunks)
        ]

        # Insert the chunks into the database
        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files,
        }
    )
