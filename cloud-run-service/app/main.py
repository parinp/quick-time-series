from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import traceback
import json
import uvicorn

from eda import perform_eda
from model import train_model, train_time_series_model, make_predictions, detect_change_points
from utils import add_time_features, create_lag_features, create_rolling_features, detect_outliers, impute_missing_values
from supabase_client import get_sample_data, get_available_datasets, save_model_results, save_predictions, upload_sample_data

app = FastAPI(
    title="Time Series Analysis API",
    description="API for time series data analysis, model training, and predictions",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define data models
class DataRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: Optional[str] = None
    target_column: Optional[str] = None

class SampleDataRequest(BaseModel):
    dataset_name: str = "rossmann"

class TrainRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    features: List[str]
    test_size: Optional[float] = 0.2
    random_state: Optional[int] = 42

class TimeSeriesTrainRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    features: List[str]
    date_column: str
    n_splits: Optional[int] = 5
    random_state: Optional[int] = 42

class PredictRequest(BaseModel):
    model: str  # Base64 encoded model
    data: List[Dict[str, Any]]

class TimeFeatureRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: str

class LagFeatureRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: str
    target_column: str
    lags: List[int]

class RollingFeatureRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: str
    target_column: str
    windows: List[int]

class OutlierDetectionRequest(BaseModel):
    data: List[Dict[str, Any]]
    column: str
    method: Optional[str] = "zscore"
    threshold: Optional[float] = 3.0

class ImputationRequest(BaseModel):
    data: List[Dict[str, Any]]
    method: Optional[str] = "mean"

class ChangePointRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: str
    target_column: str
    n_bkps: Optional[int] = 5

class SaveModelRequest(BaseModel):
    model_name: str
    dataset_name: str
    metrics: Dict[str, Any]
    feature_importance: Dict[str, float]
    user_id: Optional[str] = None

class SavePredictionsRequest(BaseModel):
    model_id: int
    predictions: List[float]
    dates: List[str]

class UploadSampleDataRequest(BaseModel):
    dataset_name: str
    data: List[Dict[str, Any]]
    description: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Time Series Analysis API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/eda")
def eda_endpoint(request: DataRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Perform EDA
        eda_results = perform_eda(df, request.date_column, request.target_column)
        return eda_results
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
def train_endpoint(request: TrainRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Train model
        model_results = train_model(
            df, 
            request.target_column, 
            request.features,
            request.test_size,
            request.random_state
        )
        return model_results
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train_time_series")
def train_time_series_endpoint(request: TimeSeriesTrainRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Train time series model
        model_results = train_time_series_model(
            df, 
            request.target_column, 
            request.features,
            request.date_column,
            request.n_splits,
            request.random_state
        )
        return model_results
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_endpoint(request: PredictRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Make predictions
        predictions = make_predictions(request.model, df)
        return predictions
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_time_features")
def time_features_endpoint(request: TimeFeatureRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Add time features
        df_with_features = add_time_features(df, request.date_column)
        
        # Convert back to list of dictionaries
        result = df_with_features.to_dict(orient='records')
        return {"data": result}
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_lag_features")
def lag_features_endpoint(request: LagFeatureRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Add lag features
        df_with_features = create_lag_features(df, request.date_column, request.target_column, request.lags)
        
        # Convert back to list of dictionaries
        result = df_with_features.to_dict(orient='records')
        return {"data": result}
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_rolling_features")
def rolling_features_endpoint(request: RollingFeatureRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Add rolling features
        df_with_features = create_rolling_features(df, request.date_column, request.target_column, request.windows)
        
        # Convert back to list of dictionaries
        result = df_with_features.to_dict(orient='records')
        return {"data": result}
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_outliers")
def outlier_detection_endpoint(request: OutlierDetectionRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Detect outliers
        outliers = detect_outliers(df, request.column, request.method, request.threshold)
        
        # Get indices of outliers
        outlier_indices = [i for i, is_outlier in enumerate(outliers) if is_outlier]
        
        # Get outlier values
        outlier_values = df.iloc[outlier_indices][request.column].tolist()
        
        return {
            "outlier_indices": outlier_indices,
            "outlier_values": outlier_values,
            "outlier_count": len(outlier_indices),
            "total_count": len(df),
            "outlier_percentage": len(outlier_indices) / len(df) * 100 if len(df) > 0 else 0
        }
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/impute_missing_values")
def imputation_endpoint(request: ImputationRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Impute missing values
        df_imputed = impute_missing_values(df, request.method)
        
        # Convert back to list of dictionaries
        result = df_imputed.to_dict(orient='records')
        return {"data": result}
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_change_points")
def change_point_endpoint(request: ChangePointRequest):
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        
        # Detect change points
        change_points = detect_change_points(df, request.date_column, request.target_column, request.n_bkps)
        
        return change_points
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Sample data endpoints
@app.get("/sample_datasets")
def get_sample_datasets_endpoint():
    """Get a list of available sample datasets"""
    try:
        datasets_info = get_available_datasets()
        return datasets_info
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sample_data")
def get_sample_data_endpoint(request: SampleDataRequest):
    """Get sample data from Supabase"""
    try:
        data = get_sample_data(request.dataset_name)
        return {"data": data, "dataset_name": request.dataset_name, "record_count": len(data)}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_sample_data")
def upload_sample_data_endpoint(request: UploadSampleDataRequest):
    """Upload sample data to Supabase"""
    try:
        upload_sample_data(request.dataset_name, request.data, request.description)
        return {"message": f"Sample data '{request.dataset_name}' uploaded successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_model_results")
def save_model_results_endpoint(request: SaveModelRequest):
    """Save model results to Supabase"""
    try:
        model_id = save_model_results(
            request.model_name,
            request.dataset_name,
            request.metrics,
            request.feature_importance,
            request.user_id
        )
        return {"model_id": model_id, "message": "Model results saved successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_predictions")
def save_predictions_endpoint(request: SavePredictionsRequest):
    """Save predictions to Supabase"""
    try:
        save_predictions(request.model_id, request.predictions, request.dates)
        return {"message": "Predictions saved successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # This is used when running locally
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True) 