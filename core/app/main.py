

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # check db connection
    # check redis connection
    # check rabbitmq connection
    yield

app = FastAPI(title="SPECWISE", version="0.0.1", lifespan=lifespan)
