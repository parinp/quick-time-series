import yfinance as yf
from pytrends.request import TrendReq
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np
import os
import dotenv
from psycopg2 import pool
import json
import ast


dotenv.load_dotenv()


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

# Connect to Google Trends
nid_cookies = ast.literal_eval(os.getenv("GOOGLE_TRENDS_COOKIES"))
# pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), proxies=['https://34.203.233.13:80',], retries=2, backoff_factor=0.1, requests_args={'verify':False})
pytrends = TrendReq(hl='en-US', tz=360, retries=3, backoff_factor=0.1,requests_args={'headers': {'Cookie': json.dumps(nid_cookies).encode('utf-8')}})

def initialize_database():
    """Create necessary tables in Supabase PostgreSQL database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create tables with proper schema
        # Stock price data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                date TIMESTAMP NOT NULL,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(ticker, date)
            )
        """)
        
        # Google Trends data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_data (
                id SERIAL PRIMARY KEY,
                keyword VARCHAR(255) NOT NULL,
                date TIMESTAMP NOT NULL,
                interest INT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(keyword, date)
            )
        """)
        
        # Combined analysis table for ML features
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_features (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                price_open FLOAT,
                price_close FLOAT,
                price_change_pct FLOAT,
                volume BIGINT,
                trend_interest INT,
                volatility_5d FLOAT,
                momentum_5d FLOAT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(ticker, date)
            )
        """)
        
        conn.commit()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def fetch_yahoo_finance_data(ticker, period="1mo", interval="1d"):
    """Fetches historical stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        df.reset_index(inplace=True)
        
        # Ensure DataFrame has expected columns
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"Missing required column: {column}")
        
        # Rename columns to lowercase for PostgreSQL
        df.columns = [col.lower() for col in df.columns]
        
        print(f"Fetched {len(df)} records for {ticker}")
        return df
    except Exception as e:
        print(f"Error fetching Yahoo Finance data for {ticker}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def fetch_google_trends_data(keyword, timeframe='today 1-m'):
    """Fetches Google Trends data for a given keyword."""

    try:
        pytrends.build_payload(kw_list=[keyword], timeframe=timeframe, geo='US')
        df = pytrends.interest_over_time()
        
        if df.empty:
            print(f"No Google Trends data found for {keyword}")
            return pd.DataFrame()
            
        # Remove partial data column and prepare for database
        if 'isPartial' in df.columns:
            df = df.drop('isPartial', axis=1)
        
        df.reset_index(inplace=True)
        df.columns = ['date', 'interest']  # Rename to match our schema
        df['keyword'] = keyword
        
        print(f"Fetched {len(df)} Google Trends records for {keyword}")
        return df[['keyword', 'date', 'interest']]  # Reorder columns
    except Exception as e:
        print(f"Error fetching Google Trends data for {keyword}: {e}")
        return pd.DataFrame()

def store_stock_data(df, ticker):
    """Stores stock price data in the database."""
    if df.empty:
        print("No stock data to store")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Prepare data for insertion
        df['ticker'] = ticker
        columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        
        # Convert records to list of tuples
        records = [tuple(row) for row in df[columns].itertuples(index=False)]
        
        # Insert data with conflict handling
        query = """
            INSERT INTO stock_prices (ticker, date, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        execute_values(cursor, query, records)
        conn.commit()
        
        print(f"Stored {len(records)} stock price records for {ticker}")
    except Exception as e:
        print(f"Error storing stock data: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def store_trend_data(df):
    """Stores Google Trends data in the database."""
    if df.empty:
        print("No trend data to store")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Prepare data for insertion
        columns = ['keyword', 'date', 'interest']
        
        # Convert records to list of tuples
        records = [tuple(row) for row in df[columns].itertuples(index=False)]
        
        # Insert data with conflict handling
        query = """
            INSERT INTO trend_data (keyword, date, interest)
            VALUES %s
            ON CONFLICT (keyword, date) DO UPDATE SET
                interest = EXCLUDED.interest
        """
        execute_values(cursor, query, records)
        conn.commit()
        
        print(f"Stored {len(records)} trend data records")
    except Exception as e:
        print(f"Error storing trend data: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def create_ml_features(ticker, keyword):
    """Generate and store ML features by combining stock and trend data."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Join stock and trend data and calculate features
        query = """
            INSERT INTO ml_features (
                date, ticker, price_open, price_close, price_change_pct,
                volume, trend_interest, volatility_5d, momentum_5d
            )
            WITH recent_prices AS (
                SELECT 
                    s.date,
                    s.ticker,
                    s.open as price_open,
                    s.close as price_close,
                    ((s.close - s.open) / s.open) * 100 as price_change_pct,
                    s.volume,
                    t.interest as trend_interest,
                    (SELECT STDDEV(sp.close) FROM stock_prices sp 
                     WHERE sp.ticker = s.ticker AND 
                     sp.date BETWEEN s.date - INTERVAL '5 days' AND s.date) as volatility_5d,
                    (SELECT (s.close - MIN(sp.close)) / MIN(sp.close) * 100 FROM stock_prices sp 
                     WHERE sp.ticker = s.ticker AND 
                     sp.date BETWEEN s.date - INTERVAL '5 days' AND s.date) as momentum_5d
                FROM 
                    stock_prices s
                LEFT JOIN 
                    trend_data t ON DATE(s.date) = DATE(t.date) AND t.keyword = %s
                WHERE 
                    s.ticker = %s
                    AND s.date >= NOW() - INTERVAL '30 days'
            )
            SELECT 
                date, ticker, price_open, price_close, price_change_pct,
                volume, trend_interest, volatility_5d, momentum_5d
            FROM 
                recent_prices
            ON CONFLICT (ticker, date) DO UPDATE SET
                price_open = EXCLUDED.price_open,
                price_close = EXCLUDED.price_close,
                price_change_pct = EXCLUDED.price_change_pct,
                volume = EXCLUDED.volume,
                trend_interest = EXCLUDED.trend_interest,
                volatility_5d = EXCLUDED.volatility_5d,
                momentum_5d = EXCLUDED.momentum_5d
        """
        
        cursor.execute(query, (keyword, ticker))
        conn.commit()
        
        count = cursor.rowcount
        print(f"Created/updated {count} ML feature records")
    except Exception as e:
        print(f"Error creating ML features: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def data_collection_pipeline(tickers, keywords, period="1mo"):
    """Run the complete data collection pipeline."""
    # Initialize database tables
    # initialize_database()
    
    # Process each ticker and corresponding keyword
    for ticker, keyword in zip(tickers, keywords):
        print(f"Processing {ticker} with keyword {keyword}...")
        
        # Fetch and store stock data
        stock_data = fetch_yahoo_finance_data(ticker, period=period)
        store_stock_data(stock_data, ticker)
        
        # Fetch and store trends data
        trend_data = fetch_google_trends_data(keyword)
        store_trend_data(trend_data)
        
        # Create ML features
        create_ml_features(ticker, keyword)
        
        # Avoid rate limiting
        time.sleep(1)
    
    print("Data collection pipeline completed")

# Example usage
if __name__ == "__main__":
    # tickers = ["AAPL", "MSFT", "GOOGL"]
    # keywords = ["Apple", "Microsoft", "Google"]

    tickers = ["AAPL"]
    keyword = ["Apple"]

    data_collection_pipeline(tickers, keyword)