import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
from core.app.handlers.files import fileRouter
from core.app.handlers.data import dataRouter
from core.app.services.mongo_db import MongoDBService
from core.app.envirnoment import config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create a dependency for the MongoDB service
def get_db_service():
    """Dependency to get MongoDB service instance"""
    return MongoDBService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP tasks
    logger.info("Starting Document Processing API")
    try:
        # Example: Check and set up DB
        db = get_db_service()
        db._setup_indexes()
        logger.info("MongoDB indexes created")

        # You could also initialize redis/rabbitmq here
        # await redis.ping()
        # await rabbitmq.connect()
    except Exception as e:
        logger.exception("Startup failed", exc_info=e)
        raise e

    yield  # <-- Application runs here

    # SHUTDOWN tasks
    logger.info("Shutting down Document Processing API")
    # Cleanup logic if needed
    # await redis.close()
    # await rabbitmq.disconnect()


app = FastAPI(title="SPECWISE", version="0.0.1", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    # Create FastAPI app

    app = FastAPI(title="SPECWISE", version="0.0.1", lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(fileRouter)
    app.include_router(dataRouter)

    return app


# Initialize the application
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
