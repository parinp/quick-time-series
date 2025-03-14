from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from utils import analyze_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ML Analysis API",
    description="API for XGBoost regression and SHAP analysis",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class AnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    dateColumn: str
    targetColumn: str

# Define API endpoints
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Analyze data using XGBoost and SHAP.
    
    Args:
        request: AnalysisRequest with data, dateColumn, and targetColumn
    
    Returns:
        Analysis results including metrics, feature importance, and SHAP plots
    """
    try:
        logger.info(f"Analyzing data with {len(request.data)} records, date column: {request.dateColumn}, target column: {request.targetColumn}")
        
        # Analyze the data
        results = analyze_data(request.data, request.dateColumn, request.targetColumn)
        
        return results
    
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "An error occurred during analysis", "message": str(e)}
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}

# Run the server if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True) 