from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch 
import json
import dotenv

dotenv.load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Financial Analytics API", 
              description="API for stock analysis with ML and LLM insights",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL connection details
DB_PARAMS = {
    "dbname": os.getenv("SUPABASE_DBNAMESPACE"),  # Supabase default database name
    "user": os.getenv("SUPABASE_USER"),    # Get from Supabase dashboard
    "password": os.getenv("SUPABASE_PASSWORD"),  # Get from Supabase dashboard
    "host": os.getenv("SUPABASE_HOST"),  # Get from Supabase dashboard
    "port": os.getenv("SUPABASE_PORT"),  # Get from Supabase dashboard
}

# Create a connection pool
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,  # Adjust based on your needs and Supabase limits
    **DB_PARAMS
)

def get_connection():
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)

# Configure Google Gemini API
# Initialize Gemini model
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY_GEMINI"))
model_id = "gemini-2.0-flash"

# Dependency to get DB connection from pool
def get_db():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

# Pydantic models for request/response
class StockData(BaseModel):
    date: datetime
    ticker: str
    open: float
    close: float
    high: float
    low: float
    volume: int

class MLFeature(BaseModel):
    date: datetime
    ticker: str
    price_open: float
    price_close: float
    price_change_pct: float
    volume: int
    trend_interest: Optional[int]
    volatility_5d: Optional[float]
    momentum_5d: Optional[float]

class PredictionResult(BaseModel):
    date: datetime
    ticker: str
    predicted_price: float
    confidence: float
    features_used: List[str]

class LLMInsight(BaseModel):
    ticker: str
    analysis: str
    key_points: List[str]
    recommendation: str
    confidence: str

# API Routes
@app.get("/")
def read_root():
    return {"message": "Financial Analytics API is running"}

@app.get("/api/stocks/{ticker}", response_model=List[StockData])
def get_stock_data(ticker: str, days: int = 30, conn=Depends(get_db)):
    """Get historical stock data for a specific ticker"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT date, ticker, open, close, high, low, volume
            FROM stock_prices
            WHERE ticker = %s
            AND date >= NOW() - INTERVAL '%s DAYS'
            ORDER BY date DESC;
        """
        cursor.execute(query, (ticker, days))
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends/{keyword}", response_model=List[Dict[str, Any]])
def get_trend_data(keyword: str, days: int = 30, conn=Depends(get_db)):
    """Get Google Trends data for a specific keyword"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT date, keyword, interest
            FROM trend_data
            WHERE keyword = %s
              AND date >= NOW() - INTERVAL '%s DAYS'
            ORDER BY date DESC
        """
        cursor.execute(query, (keyword, days))
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No trend data found for keyword {keyword}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/features/{ticker}", response_model=List[MLFeature])
def get_ml_features(ticker: str, days: int = 30, conn=Depends(get_db)):
    """Get ML features for a specific ticker"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT date, ticker, price_open, price_close, price_change_pct,
                   volume, trend_interest, volatility_5d, momentum_5d
            FROM ml_features
            WHERE ticker = %s
              AND date >= NOW() - INTERVAL '%s DAYS'
            ORDER BY date DESC
        """
        cursor.execute(query, (ticker, days))
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No ML features found for ticker {ticker}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/{ticker}", response_model=PredictionResult)
def predict_price(ticker: str, days_ahead: int = Query(1, ge=1, le=7), conn=Depends(get_db)):
    """Generate price prediction for a specific ticker"""
    try:
        # This is a simplified ML inference endpoint
        # In a real implementation, you would:
        # 1. Load your trained model
        # 2. Get the latest features from the database
        # 3. Run inference on your model
        # 4. Return the prediction
        
        # Placeholder - in production, replace with actual ML model inference
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT price_close, volatility_5d, momentum_5d
            FROM ml_features
            WHERE ticker = %s
            ORDER BY date DESC
            LIMIT 1
        """
        cursor.execute(query, (ticker,))
        latest_data = cursor.fetchone()
        cursor.close()
        
        if not latest_data:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        # Simplified price prediction logic (replace with your ML model)
        latest_price = latest_data['price_close']
        volatility = latest_data['volatility_5d'] or 0
        momentum = latest_data['momentum_5d'] or 0
        
        # Simple formula (replace with your ML model prediction)
        predicted_change = (momentum / 100) - (volatility / 200)
        predicted_price = latest_price * (1 + predicted_change * days_ahead / 30)
        
        # Create prediction result
        prediction = {
            "date": (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d"),
            "ticker": ticker,
            "predicted_price": round(predicted_price, 2),
            "confidence": 0.7,  # Placeholder - derive from model in production
            "features_used": ["price_close", "volatility_5d", "momentum_5d"]
        }
        
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{ticker}", response_model=LLMInsight)
async def get_llm_analysis(ticker: str, days: int = 30, conn=Depends(get_db)):
    """Generate LLM-based analysis for a specific ticker"""
    try:
        # Get stock data
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT s.date, s.ticker, s.open, s.close, s.high, s.low, s.volume,
                   t.interest as trend_interest
            FROM stock_prices s
            LEFT JOIN trend_data t ON DATE(s.date) = DATE(t.date) AND t.keyword = %s
            WHERE s.ticker = %s
              AND s.date >= NOW() - INTERVAL '%s DAYS'
            ORDER BY s.date
        """
        
        # Map ticker to keyword (in production, store this mapping in a config table)
        keyword_map = {"AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google"}
        keyword = keyword_map.get(ticker, ticker)
        
        cursor.execute(query, (keyword, ticker, days))
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        # Format data for LLM
        df = pd.DataFrame(result)
        
        # Calculate key metrics
        start_price = df['close'].iloc[0]
        end_price = df['close'].iloc[-1]
        price_change = ((end_price - start_price) / start_price) * 100
        max_price = df['high'].max()
        min_price = df['low'].min()
        avg_volume = df['volume'].mean()
        
        # Format trend data if available
        trend_data = "No trend data available"
        if 'trend_interest' in df.columns and not df['trend_interest'].isna().all():
            trend_start = df['trend_interest'].iloc[0]
            trend_end = df['trend_interest'].iloc[-1]
            trend_change = ((trend_end - trend_start) / trend_start) * 100 if trend_start > 0 else 0
            trend_data = f"Google Trends interest changed from {trend_start} to {trend_end} ({trend_change:.2f}% change)"
        
        # Create prompt for Gemini
        prompt = f"""
        Analyze the following data for {ticker} stock over the past {days} days:
        
        - Starting price: ${start_price:.2f}
        - Current price: ${end_price:.2f}
        - Price change: {price_change:.2f}%
        - Highest price: ${max_price:.2f}
        - Lowest price: ${min_price:.2f}
        - Average daily volume: {int(avg_volume):,}
        - {trend_data}
        
        Provide:
        1. A concise analysis of the stock's performance
        2. Three key points investors should consider
        3. A recommendation (Buy, Hold, or Sell)
        4. Confidence level in the recommendation (Low, Medium, High)
        
        Format your response as a JSON object with the following keys:
        "analysis", "key_points" (as a list), "recommendation", "confidence"
        """
        
        # Get response from Gemini
        response = client.models.generate_content(model=model_id,
                                                  contents=prompt,
                                                  config=GenerateContentConfig(response_mime_type="application/json"))
        
        # Parse the response
        try:
            # Try to extract JSON from the response text
            response_text = response.text
            
            # Handle potential text formatting from Gemini
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
            else:
                json_str = response_text
                
            insight = json.loads(json_str)
            
            # Ensure we have all required fields
            required_fields = ["analysis", "key_points", "recommendation", "confidence"]
            for field in required_fields:
                if field not in insight:
                    insight[field] = "Not provided" if field != "key_points" else []
            
            # Add ticker
            insight["ticker"] = ticker
            
            return insight
        except Exception as e:
            # Fallback if JSON parsing fails
            print(f"Error parsing Gemini response: {e}")
            return {
                "ticker": ticker,
                "analysis": "Analysis could not be generated at this time.",
                "key_points": ["Data available is limited", "Consider researching further", "Technical analysis recommends caution"],
                "recommendation": "Hold",
                "confidence": "Low"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the app with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)