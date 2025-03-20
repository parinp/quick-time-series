from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    dateColumn: str
    targetColumn: str
    multipleWaterfallPlots: bool = False

class RedisAnalysisRequest(BaseModel):
    """Request model for analyzing data from Redis"""
    dataset_id: str
    dateColumn: str
    targetColumn: str
    multipleWaterfallPlots: bool = False
    delete_after_analysis: bool = True
    exclude_columns: Optional[List[str]] = None

class MemoryEfficientAnalysisRequest(BaseModel):
    """Request model for memory-efficient ML analysis from Redis"""
    dataset_id: str
    dateColumn: str
    targetColumn: str
    exclude_columns: Optional[List[str]] = None
    test_size: float = 0.2
    max_memory_mb: int = 100
    processor_type: Optional[str] = "chunked"  # Only "chunked" is supported
    delete_after_analysis: bool = True 