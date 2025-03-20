import xgboost as xgb
import duckdb
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import io
import gc
import logging
import sys
import shap
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Dict, List, Any, Optional, Union, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ChunkedXGBoostProcessor:
    """
    Memory-efficient XGBoost training using chunked data processing.
    Designed to work with large datasets by loading and processing them in chunks.
    """
    
    def __init__(
        self, 
        max_memory_mb: int = 256,
        xgb_params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the chunked processor.
        
        Args:
            max_memory_mb: Maximum memory target in MB
            xgb_params: XGBoost parameters
        """
        self.max_memory_mb = max_memory_mb
        self.xgb_params = xgb_params or {
            "objective": "reg:squarederror",
            "tree_method": "hist",  # Memory-efficient histogram method
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,  # Use subset of data for each tree
            "colsample_bytree": 0.8,  # Use subset of features for each tree
            "random_state": 42,
            "nthread": 1  # Force single thread for GCP Cloud Run
        }
        self.model = None
        self.feature_names = None
        self.metrics = {}
        self.test_data = None
        
    async def process_parquet_bytes(
        self,
        parquet_data: bytes,
        date_column: str,
        target_column: str,
        exclude_columns: Optional[List[str]] = None,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Process and train on parquet data provided as bytes.
        
        Args:
            parquet_data: Parquet file as bytes
            date_column: Name of the date column
            target_column: Name of the target column
            exclude_columns: Columns to exclude
            test_size: Fraction of data to use for testing
            
        Returns:
            Dictionary with model, metrics, and features
        """
        buffer = io.BytesIO(parquet_data)
        
        # Create DuckDB connection
        con = duckdb.connect(":memory:")
        
        # Register parquet file with DuckDB
        con.execute("INSTALL parquet")
        con.execute("LOAD parquet")
        
        # Get schema to identify columns
        table = pq.read_table(buffer, memory_map=True)
        all_columns = table.column_names
        
        # Create a list of columns to exclude, adding the date column to avoid one-hot encoding it
        exclude_columns_list = list(exclude_columns or [])
        if date_column not in exclude_columns_list:
            exclude_columns_list.append(date_column)
        columns_to_exclude = set(exclude_columns_list)
        
        # Define columns to include: everything except excluded columns, but always include date and target
        columns_to_include = [col for col in all_columns 
                            if col not in columns_to_exclude or col == target_column]
        
        # Always include date column separately for feature extraction
        if date_column not in columns_to_include:
            columns_to_include.append(date_column)
        
        # Print column information
        logger.info(f"All columns: {all_columns}")
        logger.info(f"Date column: {date_column}, Target column: {target_column}")
        
        # Count total rows
        total_rows = await self._count_rows(con, buffer)
        logger.info(f"Total rows in dataset: {total_rows}")
        
        # Calculate rows per chunk based on memory limit
        rows_per_25mb = await self._estimate_rows_per_memory(buffer, 25)
        logger.info(f"Estimated rows per 25MB: {rows_per_25mb}")
        
        # Determine if we need chunking
        if total_rows <= rows_per_25mb:
            # Process all data at once (similar to analyze_from_redis)
            logger.info("Dataset fits in memory, processing all at once")
            return await self._process_all_data(
                con, buffer, columns_to_include, date_column, target_column, test_size
            )
        else:
            # Process in chunks
            logger.info("Dataset too large, processing in chunks")
            return await self._process_in_chunks(
                con, buffer, columns_to_include, date_column, target_column, 
                test_size, rows_per_25mb, total_rows
            )
    
    async def _estimate_rows_per_memory(self, buffer: io.BytesIO, target_mb: int) -> int:
        """Estimate how many rows equals the target memory size."""
        try:
            # Read a sample of 1000 rows
            buffer.seek(0)
            # PyArrow doesn't support num_rows parameter, so we'll read the first few rows differently
            table = pq.read_table(buffer)
            # Convert a small portion to pandas to estimate size
            sample_size = min(1000, table.num_rows)
            sample_df = table.slice(0, sample_size).to_pandas()
            
            # Calculate memory usage per row (in MB)
            if len(sample_df) > 0:
                memory_per_row = sample_df.memory_usage(deep=True).sum() / len(sample_df) / (1024 * 1024)
                rows_per_target = int(target_mb / memory_per_row)
                logger.info(f"Memory per row: {memory_per_row:.6f} MB, Rows per {target_mb}MB: {rows_per_target}")
                return max(1000, rows_per_target)  # Minimum 1000 rows
            else:
                return 10000  # Default if empty sample
        except Exception as e:
            logger.warning(f"Error estimating rows per memory: {str(e)}")
            return 10000  # Default value
    
    async def _count_rows(self, con, buffer) -> int:
        """Count total rows in parquet file."""
        try:
            buffer.seek(0)
            table = pq.read_table(buffer)
            return table.num_rows
        except Exception as e:
            logger.warning(f"Could not count rows: {str(e)}. Estimating 1,000,000 rows.")
            return 1000000
    
    async def _process_all_data(
        self, 
        con, 
        buffer, 
        columns_to_include: List[str],
        date_column: str, 
        target_column: str,
        test_size: float
    ) -> Dict[str, Any]:
        """Process all data at once similar to analyze_from_redis."""
        # Load all data
        buffer.seek(0)
        con.register("data_view", pq.read_table(buffer))
        
        # Build SQL column list
        columns_sql = ", ".join([f'"{col}"' for col in columns_to_include])
        
        # Execute query to get all data
        query = f"SELECT {columns_sql} FROM data_view"
        df = con.execute(query).fetchdf()
        
        # Extract date features before preparing data
        df = self._extract_date_features(df, date_column)
        
        # Prepare data (handle categorical columns)
        df, categorical_encodings = self._prepare_data(df)
        
        # Log categorical encodings
        logger.info(f"Categorical encodings: {categorical_encodings}")
        
        # Split into train and test sets
        train_data, test_data = train_test_split(df, test_size=test_size, random_state=42)
        self.test_data = test_data.copy()
        
        # Log dataset shapes
        logger.info(f"Train data shape: {train_data.shape}, Test data shape: {test_data.shape}")
        
        # Split features and target
        X_train, y_train = self._split_features_target(train_data, date_column, target_column)
        X_test, y_test = self._split_features_target(test_data, date_column, target_column)
        
        # Store feature names
        self.feature_names = X_train.columns.tolist()
        
        # Train model
        dtrain = xgb.DMatrix(X_train, label=y_train)
        self.model = xgb.train(self.xgb_params, dtrain, num_boost_round=100)
        
        # Evaluate model
        dtest = xgb.DMatrix(X_test)
        y_pred = self.model.predict(dtest)
        
        # Calculate metrics
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        test_r2 = r2_score(y_test, y_pred)
        
        # Calculate training metrics
        dtrain_pred = self.model.predict(dtrain)
        train_rmse = np.sqrt(mean_squared_error(y_train, dtrain_pred))
        train_r2 = r2_score(y_train, dtrain_pred)
        
        self.metrics = {
            'test_rmse': float(test_rmse) if not np.isinf(test_rmse) and not np.isnan(test_rmse) else 0.0,
            'test_r2': float(test_r2) if not np.isinf(test_r2) and not np.isnan(test_r2) else 0.0,
            'train_rmse': float(train_rmse) if not np.isinf(train_rmse) and not np.isnan(train_rmse) else 0.0,
            'train_r2': float(train_r2) if not np.isinf(train_r2) and not np.isnan(train_r2) else 0.0
        }
        
        # Generate SHAP analysis
        shap_plots = self._generate_shap_plots(X_test, self.feature_names)
        
        # Get feature importance
        feature_importance = self.get_feature_importance()
        
        # Return results in the same format as analyze_from_redis
        return {
            'model': 'xgboost',
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'shap_plots': shap_plots,
            'processing_type': 'full',
            'total_rows': len(df)
        }
    
    async def _process_in_chunks(
        self,
        con, 
        buffer, 
        columns_to_include: List[str],
        date_column: str, 
        target_column: str,
        test_size: float,
        rows_per_chunk: int,
        total_rows: int
    ) -> Dict[str, Any]:
        """Process data in chunks for memory efficiency."""
        buffer.seek(0)
        con.register("data_view", pq.read_table(buffer))
        
        # Build SQL column list
        columns_sql = ", ".join([f'"{col}"' for col in columns_to_include])
        
        # Calculate training rows (80% of total)
        train_rows = int(total_rows * (1 - test_size))
        
        # Extract test data first (last 20%)
        test_offset = train_rows
        test_query = f"""
        SELECT {columns_sql} FROM data_view
        LIMIT {total_rows - train_rows} OFFSET {test_offset}
        """
        test_df = con.execute(test_query).fetchdf()
        
        # Extract date features before preparing test data
        test_df = self._extract_date_features(test_df, date_column)
        
        test_df, categorical_encodings = self._prepare_data(test_df)
        self.test_data = test_df.copy()
        
        # Log dataset shape
        logger.info(f"Test data shape: {test_df.shape}")
        
        # Split test features and target
        X_test, y_test = self._split_features_target(test_df, date_column, target_column)
        
        # Calculate number of chunks needed
        num_chunks = (train_rows + rows_per_chunk - 1) // rows_per_chunk
        logger.info(f"Processing {train_rows} training rows in {num_chunks} chunks of {rows_per_chunk} rows each")
        
        # To collect all training data for metrics calculation
        all_train_X = []
        all_train_y = []
        
        # Process first chunk to initialize model
        first_chunk_query = f"""
        SELECT {columns_sql} FROM data_view
        LIMIT {min(rows_per_chunk, train_rows)} OFFSET 0
        """
        first_chunk = con.execute(first_chunk_query).fetchdf()
        
        # Extract date features before applying transformations
        first_chunk = self._extract_date_features(first_chunk, date_column)
        
        first_chunk = self._apply_transformations(first_chunk, categorical_encodings)
        
        # Split features and target
        X_chunk, y_chunk = self._split_features_target(first_chunk, date_column, target_column)
        
        # Store feature names
        self.feature_names = X_chunk.columns.tolist()
        
        # Save for metrics calculation
        all_train_X.append(X_chunk.copy())
        all_train_y.append(y_chunk.copy())
        
        # Initialize model with first chunk
        dtrain = xgb.DMatrix(X_chunk, label=y_chunk)
        self.model = xgb.train(self.xgb_params, dtrain, num_boost_round=100 // num_chunks)
        
        # Release memory
        del dtrain, X_chunk, y_chunk, first_chunk
        gc.collect()
        
        # Process remaining chunks
        chunks_processed = 1
        for chunk_idx in range(1, num_chunks):
            offset = chunk_idx * rows_per_chunk
            limit = min(rows_per_chunk, train_rows - offset)
            
            if limit <= 0:
                break
                
            chunk_query = f"""
            SELECT {columns_sql} FROM data_view
            LIMIT {limit} OFFSET {offset}
            """
            
            chunk_df = con.execute(chunk_query).fetchdf()
            
            # Extract date features before applying transformations
            chunk_df = self._extract_date_features(chunk_df, date_column)
            
            chunk_df = self._apply_transformations(chunk_df, categorical_encodings)
            
            # Split features and target
            X_chunk, y_chunk = self._split_features_target(chunk_df, date_column, target_column)
            
            # Add missing columns if needed
            missing_features = set(self.feature_names) - set(X_chunk.columns)
            if missing_features:
                # Create a DataFrame with zeros for missing features
                missing_df = pd.DataFrame(0, 
                                         index=X_chunk.index, 
                                         columns=list(missing_features))
                # Use concat instead of individual column assignment to avoid fragmentation
                X_chunk = pd.concat([X_chunk, missing_df], axis=1)
                logger.info(f"Added {len(missing_features)} missing features to chunk {chunk_idx+1}")
            
            # Ensure columns order
            X_chunk = X_chunk[self.feature_names]
            
            # Save for metrics calculation
            all_train_X.append(X_chunk.copy())
            all_train_y.append(y_chunk.copy())
            
            # Continue training
            dtrain = xgb.DMatrix(X_chunk, label=y_chunk)
            self.model = xgb.train(
                self.xgb_params, 
                dtrain, 
                num_boost_round=100 // num_chunks,
                xgb_model=self.model
            )
            
            chunks_processed += 1
            logger.info(f"Processed chunk {chunk_idx+1}/{num_chunks}")
            
            # Release memory
            del dtrain, X_chunk, y_chunk, chunk_df
            gc.collect()
        
        # Combine all training data for metrics calculation
        # Only if we have a reasonable amount of data that fits in memory
        train_sample_size = min(len(all_train_X) * 1000, sum(len(x) for x in all_train_X))
        if train_sample_size > 0:
            # Create a sample for training metrics calculation
            if len(all_train_X) > 1:
                # Use a safer approach to sample data that ensures X and y match
                train_samples = []
                train_y_samples = []
                
                for X_chunk, y_chunk in zip(all_train_X, all_train_y):
                    # Calculate sample size for this chunk (up to 20% of rows)
                    chunk_sample_size = min(len(X_chunk), max(100, int(len(X_chunk) * 0.2)))
                    # Use same random state for reproducibility
                    sample_indices = np.random.RandomState(42).choice(len(X_chunk), chunk_sample_size, replace=False)
                    # Select the same indices for both X and y
                    train_samples.append(X_chunk.iloc[sample_indices])
                    train_y_samples.append(y_chunk.iloc[sample_indices])
                
                # Concatenate all samples
                train_X_sample = pd.concat(train_samples)
                train_y_sample = pd.concat(train_y_samples)
            else:
                train_X_sample = all_train_X[0]
                train_y_sample = all_train_y[0]
            
            # Make sure lengths match
            assert len(train_X_sample) == len(train_y_sample), "X and y sample lengths don't match"
            
            # Calculate training metrics on the sample
            dtrain_sample = xgb.DMatrix(train_X_sample, label=train_y_sample)
            train_pred = self.model.predict(dtrain_sample)
            train_rmse = np.sqrt(mean_squared_error(train_y_sample, train_pred))
            train_r2 = r2_score(train_y_sample, train_pred)
        else:
            # If we can't calculate training metrics, use zeros
            train_rmse = 0.0
            train_r2 = 0.0
        
        # Add missing columns to test data if needed
        missing_features = set(self.feature_names) - set(X_test.columns)
        if missing_features:
            # Create a DataFrame with zeros for missing features
            missing_df = pd.DataFrame(0, 
                                     index=X_test.index, 
                                     columns=list(missing_features))
            # Use concat instead of individual column assignment to avoid fragmentation
            X_test = pd.concat([X_test, missing_df], axis=1)
            logger.info(f"Added {len(missing_features)} missing features to test data")
        
        # Ensure columns order
        X_test = X_test[self.feature_names]
        
        # Evaluate on test set
        dtest = xgb.DMatrix(X_test)
        y_pred = self.model.predict(dtest)
        
        # Calculate metrics
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        test_r2 = r2_score(y_test, y_pred)
        
        self.metrics = {
            'test_rmse': float(test_rmse) if not np.isinf(test_rmse) and not np.isnan(test_rmse) else 0.0,
            'test_r2': float(test_r2) if not np.isinf(test_r2) and not np.isnan(test_r2) else 0.0,
            'train_rmse': float(train_rmse) if not np.isinf(train_rmse) and not np.isnan(train_rmse) else 0.0,
            'train_r2': float(train_r2) if not np.isinf(train_r2) and not np.isnan(train_r2) else 0.0,
            'chunks_processed': chunks_processed
        }
        
        # Generate SHAP plots
        shap_plots = self._generate_shap_plots(X_test, self.feature_names)
        
        # Get feature importance
        feature_importance = self.get_feature_importance()
        
        # Release memory
        del all_train_X, all_train_y
        gc.collect()
        
        # Return results in the same format as analyze_from_redis
        return {
            'model': 'xgboost',
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'shap_plots': shap_plots,
            'processing_type': 'chunked',
            'total_rows': total_rows,
            'rows_per_chunk': rows_per_chunk,
            'chunks_processed': chunks_processed
        }
    
    def _extract_date_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Extract useful features from the date column."""
        try:
            # Make a copy to avoid modifying the original
            df = df.copy()
            
            # Try to convert to datetime
            if date_column in df.columns:
                # Check if the column is already a datetime type
                if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                    try:
                        df[date_column] = pd.to_datetime(df[date_column])
                    except Exception as e:
                        logger.warning(f"Could not convert {date_column} to datetime: {str(e)}")
                        return df
                
                # Extract useful features from the date
                # df[f'{date_column}_year'] = df[date_column].dt.year
                # df[f'{date_column}_month'] = df[date_column].dt.month
                # df[f'{date_column}_day'] = df[date_column].dt.day
                # df[f'{date_column}_dayofweek'] = df[date_column].dt.dayofweek
                # df[f'{date_column}_quarter'] = df[date_column].dt.quarter
                # df[f'{date_column}_is_month_start'] = df[date_column].dt.is_month_start.astype(int)
                # df[f'{date_column}_is_month_end'] = df[date_column].dt.is_month_end.astype(int)
                # df[f'{date_column}_is_quarter_start'] = df[date_column].dt.is_quarter_start.astype(int)
                # df[f'{date_column}_is_quarter_end'] = df[date_column].dt.is_quarter_end.astype(int)
                
                # Drop the original date column 
                df = df.drop(date_column, axis=1)
                
                # logger.info(f"Extracted features from {date_column}")
            
            return df
        except Exception as e:
            logger.warning(f"Error extracting date features: {str(e)}")
            return df
    
    def _prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Prepare data for training by handling categorical columns."""
        # Find categorical columns (object dtype)
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        encodings = {}
        
        if categorical_columns:
            # Log categorical columns only if they exist
            logger.info(f"Categorical columns: {categorical_columns}")
            
            # One-hot encode categorical columns
            df = pd.get_dummies(df, columns=categorical_columns, drop_first=True)
            
            # Store encodings
            encodings['categorical_columns'] = categorical_columns
            
        return df, encodings
    
    def _apply_transformations(self, df: pd.DataFrame, encodings: Dict) -> pd.DataFrame:
        """Apply the same transformations to a new chunk of data."""
        # Apply one-hot encoding to categorical columns
        if 'categorical_columns' in encodings:
            categorical_columns = [col for col in encodings['categorical_columns'] if col in df.columns]
            if categorical_columns:
                df = pd.get_dummies(df, columns=categorical_columns, drop_first=True)
                
        return df
    
    def _split_features_target(
        self, df: pd.DataFrame, date_column: str, target_column: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Split DataFrame into features and target."""
        # Only drop target column
        X = df.drop([target_column], axis=1) if target_column in df.columns else df
        y = df[target_column] if target_column in df.columns else None
        return X, y
    
    def _generate_shap_plots(self, X_test: pd.DataFrame, feature_names: List[str]) -> Dict[str, str]:
        """Generate SHAP plots for the model."""
        try:
            # Create an explainer 
            explainer = shap.Explainer(self.model)
            
            # Take a small representative sample of the test data to avoid potential issues
            sample_size = min(100, len(X_test))
            X_sample = X_test.sample(sample_size, random_state=42) if len(X_test) > sample_size else X_test
            
            # Calculate SHAP values
            shap_values = explainer(X_sample, check_additivity=False)
            
            # Generate plots
            result = {}
            
            # SHAP Summary Plot (Bar)
            plt.figure(figsize=(10, 8))
            shap.plots.bar(shap_values, show=False)
            plt.tight_layout()
            result["bar_plot"] = self._get_plot_as_base64()
            
            # SHAP Summary Plot (Beeswarm)
            plt.figure(figsize=(12, 10))
            shap.plots.beeswarm(shap_values, show=False)
            plt.tight_layout()
            result["beeswarm_plot"] = self._get_plot_as_base64()
            
            # Generate waterfall plot for a single example (keep for backward compatibility)
            if len(X_sample) > 0:
                plt.figure(figsize=(10, 8))
                shap.plots.waterfall(shap_values[0], show=False)
                plt.tight_layout()
                result["waterfall_plot"] = self._get_plot_as_base64()
            
            # Generate force plots for different examples (low, medium, high predictions)
            if len(X_sample) >= 3:  # Need at least 3 examples
                # Get predictions for the sample
                dmatrix = xgb.DMatrix(X_sample)
                y_pred = self.model.predict(dmatrix)
                
                # Find indices for low, medium, and high predictions
                sorted_indices = np.argsort(y_pred)
                n_samples = len(sorted_indices)
                
                # Get indices for low (10th percentile), medium (50th percentile), and high (90th percentile)
                low_idx = sorted_indices[int(n_samples * 0.1)]
                med_idx = sorted_indices[int(n_samples * 0.5)]
                high_idx = sorted_indices[int(n_samples * 0.9)]
                
                # Generate force plot for low prediction example
                plt.figure(figsize=(14, 6))
                plt.title(f"Low Sales Example (Predicted: {y_pred[low_idx]:.2f})")
                shap.plots.force(shap_values[low_idx], matplotlib=True, show=False, figsize=(14, 3))
                plt.tight_layout(pad=3.0)
                result["waterfall_plot_low"] = self._get_plot_as_base64()
                
                # Generate force plot for medium prediction example
                plt.figure(figsize=(14, 6))
                plt.title(f"Medium Sales Example (Predicted: {y_pred[med_idx]:.2f})")
                shap.plots.force(shap_values[med_idx], matplotlib=True, show=False, figsize=(14, 3))
                plt.tight_layout(pad=3.0)
                result["waterfall_plot_medium"] = self._get_plot_as_base64()
                
                # Generate force plot for high prediction example
                plt.figure(figsize=(14, 6))
                plt.title(f"High Sales Example (Predicted: {y_pred[high_idx]:.2f})")
                shap.plots.force(shap_values[high_idx], matplotlib=True, show=False, figsize=(14, 3))
                plt.tight_layout(pad=3.0)
                result["waterfall_plot_high"] = self._get_plot_as_base64()
            
            return result
        except Exception as e:
            logger.error(f"Error generating SHAP plots: {str(e)}")
            return {"error": str(e)}
    
    def _get_plot_as_base64(self) -> str:
        """Convert the current matplotlib plot to a base64 string."""
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight", dpi=100)
        plt.close()
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode("utf-8")
        return img_str  # Return just the image string, not the data URI
    
    def get_feature_importance(self) -> List[Dict[str, Union[str, float]]]:
        """Get feature importance from the trained model."""
        if self.model is None or not self.feature_names:
            logger.warning("Cannot get feature importance without a trained model and feature names")
            return []
            
        # Extract feature importance scores from model
        importance_scores = self.model.get_score(importance_type='gain')
        
        # Create a list of dictionaries with feature name and importance
        feature_importance = []
        
        # Calculate total importance for normalization
        total_importance = sum(importance_scores.values())
        if total_importance == 0:
            total_importance = 1  # Avoid division by zero
        
        for feature in self.feature_names:
            if feature in importance_scores:
                score = importance_scores[feature]
                # Handle infinite or NaN values
                if np.isinf(score) or np.isnan(score):
                    score = 0.0
                # Normalize to a scale between 0 and 1
                normalized_score = score / total_importance
                feature_importance.append({
                    'feature': feature,
                    'importance': float(normalized_score)
                })
            else:
                # If feature not in importance scores, it wasn't used in the model
                feature_importance.append({
                    'feature': feature,
                    'importance': 0.0
                })
        
        # Sort by importance (descending)
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        return feature_importance 