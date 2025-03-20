from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import logging
import time
import traceback
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ML Analysis API",
    description="API for XGBoost regression and SHAP analysis",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:8000",  # Local API development
        "https://simple-timeseries-analysis.vercel.app",  # Vercel production
        "*",  # Allow all origins during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Import routers
from .routers.health import router as health_router
from .routers.analysis import router as analysis_router

# Include routers
app.include_router(health_router)
app.include_router(analysis_router)

# Log startup
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    logger.info(f"Environment: {os.environ.get('ENV', 'development')}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True) 