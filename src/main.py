from fastapi import FastAPI
from routes import base, data, nlp
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.TemplateParser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# from utils.metrics import setup_metrics

# Create a FastAPI application
app = FastAPI()

# # Setup Prometheus metrics
# setup_metrics(app)

@app.on_event("startup")
async def startup_span():
    """
    This function is called when the application starts up.
    It initializes the database connection, LLM providers, and vector database.
    """
    settings = get_settings()

    # Connect to the PostgreSQL database
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    app.db_engine = create_async_engine(postgres_conn)
    app.db_client = sessionmaker(
        app.db_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create LLM and vector database provider factories
    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(config=settings, db_client=app.db_client)

    # Set up the text generation client
    app.generation_client = llm_provider_factory.create(
        provider_name=settings.GENERATION_BACKEND
    )
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    # Set up the text embedding client
    app.embedding_client = llm_provider_factory.create(
        provider_name=settings.EMBEDDING_BACKEND
    )
    app.embedding_client.set_embedding_model(
        model_id=settings.EMBEDDING_MODEL_ID,
        embedding_size=settings.EMBEDDING_MODEL_SIZE,
    )

    # Set up the vector database client
    app.vectordb_client = vectordb_provider_factory.create(
        provider_name=settings.VECTOR_DB_BACKEND
    )
    await app.vectordb_client.connect()

    # Set up the template parser
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )


@app.on_event("shutdown")
async def shutdown_span():
    """
    This function is called when the application shuts down.
    It closes the database connection and disconnects from the vector database.
    """
    await app.db_engine.dispose()
    await app.vectordb_client.disconnect()


# Include the API routers
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
