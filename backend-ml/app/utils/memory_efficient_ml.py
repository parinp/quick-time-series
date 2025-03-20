import logging
import time
import traceback
import psutil
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
import os
import gc
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Import our processing modules
from app.utils.chunked_processor import ChunkedXGBoostProcessor

# Configure logging
logger = logging.getLogger(__name__)

class MemoryEfficientML:
    """
    Memory-efficient ML trainer using chunked data processing.
    Optimized for single-CPU environments like GCP Cloud Run within free tier limits.
    """
    
    def __init__(
        self,
        max_memory_mb: int = 256,  # Reduced default memory to stay within GCP free tier
        processor_type: str = "chunked",  # Always use chunked processor
        log_resources: bool = True  # Added resource logging option
    ):
        """
        Initialize the memory-efficient ML trainer.
        
        Args:
            max_memory_mb: Maximum memory target in MB
            processor_type: Type of processor to use (only "chunked" supported)
            log_resources: Whether to log resource usage statistics
        """
        self.max_memory_mb = max_memory_mb
        self.processor_type = "chunked"  # Always use chunked processor
        self.processor = None
        self.log_resources = log_resources
        self.resources_log = {
            'memory_readings': [],
            'start_time': None,
            'end_time': None,
            'peak_memory_mb': 0
        }
        
        # XGBoost parameters - optimized for efficiency while maintaining reasonable accuracy
        self.xgb_params = {
            "objective": "reg:squarederror",
            "tree_method": "hist",  # Memory-efficient histogram method
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,  # Use subset of data for each tree
            "colsample_bytree": 0.8,  # Use subset of features for each tree
            "random_state": 42,
            "nthread": 1  # Force single thread for GCP Cloud Run
        }
    
    def _determine_processor_type(self, data_size: int) -> str:
        """
        Determine the type of processor to use based on data size and configuration.
        
        Args:
            data_size: Size of data in bytes
            
        Returns:
            Type of processor to use (always "chunked")
        """
        # Only log data size in MB
        data_size_mb = data_size / (1024*1024)
        logger.info(f"Data size: {data_size_mb:.2f} MB")
        return "chunked"
    
    def _initialize_processor(self, processor_type: str, data_size: int):
        """
        Initialize the chunked processor.
        
        Args:
            processor_type: Type of processor to initialize (ignored, always chunked)
            data_size: Size of data in bytes for optimization
        """
        # Always use chunked processor
        self.processor = ChunkedXGBoostProcessor(
            max_memory_mb=self.max_memory_mb,
            xgb_params=self.xgb_params
        )
        
        # Record memory after initialization
        if self.log_resources:
            self._log_memory("initialization_complete")
    
    def _log_memory(self, checkpoint: str):
        """Log current memory usage."""
        if not self.log_resources:
            return
            
        try:
            process = __import__('psutil').Process(os.getpid())
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)
            
            self.resources_log['memory_readings'].append((checkpoint, memory_usage_mb))
            self.resources_log['peak_memory_mb'] = max(self.resources_log['peak_memory_mb'], memory_usage_mb)
            
            # Only log memory usage, nothing else
            logger.info(f"Memory usage: {memory_usage_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"Failed to log memory usage: {str(e)}")
    
    async def process_parquet_bytes(
        self,
        parquet_data: bytes,
        date_column: str,
        target_column: str,
        exclude_columns: Optional[List[str]] = None,
        test_size: float = 0.2,
        processor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process parquet data provided as bytes.
        
        Args:
            parquet_data: Parquet file as bytes
            date_column: Name of the date column
            target_column: Name of the target column
            exclude_columns: Columns to exclude
            test_size: Fraction of data to use for testing
            processor_type: Type of processor to use
            
        Returns:
            Dictionary with model, metrics, and features
        """
        try:
            # Start resource tracking
            if self.log_resources:
                import time
                self.resources_log['start_time'] = time.time()
                self._log_memory("process_start")
            
            # Determine processor type based on data size
            data_size = len(parquet_data)
            processor_type = self._determine_processor_type(data_size)
            
            # Initialize the chunked processor
            self._initialize_processor(processor_type, data_size)
            
            # Process the data
            result = await self.processor.process_parquet_bytes(
                parquet_data=parquet_data,
                date_column=date_column,
                target_column=target_column,
                exclude_columns=exclude_columns,
                test_size=test_size
            )
            
            # Add processor type to result
            result["processor_type"] = processor_type
            
            # Add memory usage info and resource tracking
            if self.log_resources:
                self._log_memory("process_complete")
                import time
                self.resources_log['end_time'] = time.time()
                processing_time = self.resources_log['end_time'] - self.resources_log['start_time']
                
                result["resource_usage"] = {
                    "peak_memory_mb": self.resources_log['peak_memory_mb'],
                    "processing_time_seconds": processing_time
                }
                
                # Keep this summary log for total resource usage
                logger.info(f"Resource usage summary: Peak memory: {self.resources_log['peak_memory_mb']:.2f} MB, Processing time: {processing_time:.2f}s")
            else:
                # Just get current memory if not logging full resources
                process = __import__('psutil').Process(os.getpid())
                memory_info = process.memory_info()
                current_memory_mb = memory_info.rss / (1024 * 1024)
                result["resource_usage"] = {
                    "memory_mb": current_memory_mb
                }
            
            # Cleanup to reduce memory usage
            gc.collect()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in memory-efficient processing: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def process_parquet_file(
        self,
        file_path: str,
        date_column: str,
        target_column: str,
        exclude_columns: Optional[List[str]] = None,
        test_size: float = 0.2,
        processor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process and train on parquet data from a file.
        
        Args:
            file_path: Path to the parquet file
            date_column: Name of the date column
            target_column: Name of the target column
            exclude_columns: Columns to exclude
            test_size: Fraction of data to use for testing
            processor_type: Override processor type selection (ignored, always chunked)
            
        Returns:
            Dictionary with model, metrics, and features
        """
        try:
            # Read file
            with open(file_path, 'rb') as f:
                parquet_data = f.read()
            
            # Process using the bytes method
            return await self.process_parquet_bytes(
                parquet_data=parquet_data,
                date_column=date_column,
                target_column=target_column,
                exclude_columns=exclude_columns,
                test_size=test_size,
                processor_type="chunked"  # Always use chunked processor
            )
        except Exception as e:
            logger.error(f"Error processing parquet file: {str(e)}", exc_info=True)
            raise
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        Args:
            X: DataFrame with features
            
        Returns:
            Array of predictions
        """
        if self.processor is None:
            raise ValueError("No model has been trained yet")
        
        return self.processor.predict(X)
    
    def get_feature_importance(self) -> List[Dict[str, Union[str, float]]]:
        """
        Get feature importance from the trained model.
        
        Returns:
            List of dictionaries with feature names and importance scores
        """
        if self.processor is None:
            raise ValueError("No model has been trained yet")
        
        return self.processor.get_feature_importance()
    
    @property
    def model(self):
        """Get the trained model."""
        if self.processor is None:
            raise ValueError("No model has been trained yet")
        return self.processor.model
    
    @property
    def feature_names(self):
        """Get the feature names used by the model."""
        if self.processor is None:
            raise ValueError("No model has been trained yet")
        return self.processor.feature_names
    
    @property
    def metrics(self):
        """Get the model metrics."""
        if self.processor is None:
            raise ValueError("No model has been trained yet")
        return self.processor.metrics 