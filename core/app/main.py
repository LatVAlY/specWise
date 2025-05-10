

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
from core.app.handlers.files import fileRouter
from core.app.handlers.data import dataRouter
from core.app.services.mongo_db import MongoDBService
from core.app.envirnoment import config
@asynccontextmanager
async def lifespan(app: FastAPI):
    # check db connection
    # check redis connection
    # check rabbitmq connection
    yield

app = FastAPI(title="SPECWISE", version="0.0.1", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    

    # Create a dependency for the MongoDB service
    def get_db_service():
        """Dependency to get MongoDB service instance"""
        return MongoDBService()
    
    # Include routers with dependencies
    app.include_router(fileRouter)
    app.include_router(dataRouter)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Document Processing API")
        # Any startup tasks, like ensuring indexes exist
        db = get_db_service()
        db._setup_indexes()
        logger.info("MongoDB indexes created")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Document Processing API")
        # Any cleanup tasks if needed
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok"}
    
    return app

# Initialize the application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)