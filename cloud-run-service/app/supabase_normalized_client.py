import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_connection_from_supabase_url():
    """Extract PostgreSQL connection details from Supabase URL"""
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    # Extract host from Supabase URL
    parsed_url = urlparse(supabase_url)
    host = parsed_url.netloc
    
    # Supabase uses a specific format for direct database connections
    # The host is the project reference, which is the subdomain of the URL
    project_ref = host.split('.')[0]
    
    # Connection parameters for direct PostgreSQL connection
    conn_params = {
        'host': f"{project_ref}.supabase.co",
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': supabase_key  # The service_role key works as the password
    }
    
    return conn_params

def get_rossmann_data(store_id: Optional[int] = None, 
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Get Rossmann data from normalized tables.
    
    Args:
        store_id: Optional filter by store ID
        date_from: Optional filter by start date (YYYY-MM-DD)
        date_to: Optional filter by end date (YYYY-MM-DD)
        limit: Maximum number of records to return
        
    Returns:
        List of dictionaries containing the data
    """
    try:
        # Build the query with filters
        query = "SELECT * FROM rossmann_combined WHERE 1=1"
        params = []
        
        if store_id is not None:
            query += " AND store_id = %s"
            params.append(store_id)
            
        if date_from is not None:
            query += " AND date >= %s"
            params.append(date_from)
            
        if date_to is not None:
            query += " AND date <= %s"
            params.append(date_to)
            
        query += " ORDER BY store_id, date LIMIT %s"
        params.append(limit)
        
        # Connect to the database
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        
        # Use RealDictCursor to get results as dictionaries
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error retrieving Rossmann data: {str(e)}")
        raise

def get_rossmann_stores() -> List[Dict[str, Any]]:
    """
    Get all Rossmann stores.
    
    Returns:
        List of dictionaries containing store information
    """
    try:
        # Connect to the database
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        
        # Use RealDictCursor to get results as dictionaries
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM rossmann_stores ORDER BY store_id")
            results = cursor.fetchall()
            
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error retrieving Rossmann stores: {str(e)}")
        raise

def get_rossmann_sales_by_date(store_id: Optional[int] = None,
                              date_from: Optional[str] = None,
                              date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get Rossmann sales data aggregated by date.
    
    Args:
        store_id: Optional filter by store ID
        date_from: Optional filter by start date (YYYY-MM-DD)
        date_to: Optional filter by end date (YYYY-MM-DD)
        
    Returns:
        List of dictionaries containing aggregated sales data
    """
    try:
        # Build the query with filters
        query = """
        SELECT 
            date, 
            SUM(sales) as total_sales, 
            SUM(customers) as total_customers,
            COUNT(*) as store_count
        FROM rossmann_sales
        WHERE 1=1
        """
        params = []
        
        if store_id is not None:
            query += " AND store_id = %s"
            params.append(store_id)
            
        if date_from is not None:
            query += " AND date >= %s"
            params.append(date_from)
            
        if date_to is not None:
            query += " AND date <= %s"
            params.append(date_to)
            
        query += " GROUP BY date ORDER BY date"
        
        # Connect to the database
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        
        # Use RealDictCursor to get results as dictionaries
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error retrieving Rossmann sales by date: {str(e)}")
        raise

def get_rossmann_sales_by_store(date_from: Optional[str] = None,
                               date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get Rossmann sales data aggregated by store.
    
    Args:
        date_from: Optional filter by start date (YYYY-MM-DD)
        date_to: Optional filter by end date (YYYY-MM-DD)
        
    Returns:
        List of dictionaries containing aggregated sales data
    """
    try:
        # Build the query with filters
        query = """
        SELECT 
            s.store_id,
            st.store_type,
            st.assortment,
            SUM(s.sales) as total_sales, 
            SUM(s.customers) as total_customers,
            COUNT(DISTINCT s.date) as days_count,
            AVG(s.sales) as avg_daily_sales
        FROM rossmann_sales s
        JOIN rossmann_stores st ON s.store_id = st.store_id
        WHERE 1=1
        """
        params = []
            
        if date_from is not None:
            query += " AND s.date >= %s"
            params.append(date_from)
            
        if date_to is not None:
            query += " AND s.date <= %s"
            params.append(date_to)
            
        query += " GROUP BY s.store_id, st.store_type, st.assortment ORDER BY s.store_id"
        
        # Connect to the database
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        
        # Use RealDictCursor to get results as dictionaries
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error retrieving Rossmann sales by store: {str(e)}")
        raise

def get_rossmann_dataset_info() -> Dict[str, Any]:
    """
    Get information about the Rossmann dataset.
    
    Returns:
        Dictionary with dataset information
    """
    try:
        # Connect to the database
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        
        # Use RealDictCursor to get results as dictionaries
        with conn.cursor() as cursor:
            # Get store count
            cursor.execute("SELECT COUNT(*) FROM rossmann_stores")
            store_count = cursor.fetchone()[0]
            
            # Get sales record count
            cursor.execute("SELECT COUNT(*) FROM rossmann_sales")
            sales_count = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM rossmann_sales")
            min_date, max_date = cursor.fetchone()
            
        conn.close()
        
        return {
            "name": "rossmann",
            "description": "Rossmann Store Sales dataset",
            "store_count": store_count,
            "sales_record_count": sales_count,
            "date_range": {
                "start": min_date.isoformat() if min_date else None,
                "end": max_date.isoformat() if max_date else None
            },
            "tables": ["rossmann_stores", "rossmann_sales", "rossmann_combined"]
        }
        
    except Exception as e:
        print(f"Error retrieving Rossmann dataset info: {str(e)}")
        raise 