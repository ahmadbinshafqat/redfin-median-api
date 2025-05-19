"""
Main entry point for the Redfin Median Price API.
"""

import os
from dotenv import load_dotenv

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from app.database import connect_to_mongo, close_mongo_connection
from app.routes import router

load_dotenv()

# API Information
API_TITLE = os.getenv("API_TITLE")
API_DESCRIPTION = os.getenv("API_DESCRIPTION")
API_VERSION = os.getenv("API_VERSION")

# Lifespan event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    client, collection = await connect_to_mongo()
    app.state.mongo_client = client
    app.state.mongo_collection = collection
    yield
    # Shutdown
    await close_mongo_connection(app.state.mongo_client)

# Create FastAPI app with lifespan
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

# Include routers
app.include_router(router)

# Run the app with uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
