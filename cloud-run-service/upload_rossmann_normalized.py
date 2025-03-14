import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
import psycopg2
from psycopg2.extras import execute_values
import time
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def get_connection_from_supabase_url():
    """Extract PostgreSQL connection details from Supabase URL"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
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

def upload_rossmann_store_data(store_path):
    """Upload Rossmann store data to normalized table"""
    print("Loading Rossmann store data...")
    
    if not os.path.exists(store_path):
        print(f"Error: {store_path} not found")
        return False
    
    # Load the data
    store_df = pd.read_csv(store_path)
    
    # Connect to the database
    try:
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # First, clear existing data
        cursor.execute("TRUNCATE TABLE rossmann_stores CASCADE")
        
        # Prepare data for insertion
        columns = list(store_df.columns)
        values = [tuple(x) for x in store_df.to_numpy()]
        
        # Generate the SQL query
        insert_query = f"""
        INSERT INTO rossmann_stores (
            store_id, store_type, assortment, competition_distance, 
            competition_open_since_month, competition_open_since_year,
            promo2, promo2_since_week, promo2_since_year, promo_interval
        ) VALUES %s
        """
        
        # Execute the query with all values
        execute_values(cursor, insert_query, values)
        
        # Commit the transaction
        conn.commit()
        
        print(f"Successfully uploaded {len(store_df)} store records")
        return True
        
    except Exception as e:
        print(f"Error uploading store data: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def upload_rossmann_train_data(train_path, batch_size=10000, limit_records=None):
    """Upload Rossmann train data to normalized table in batches"""
    print("Loading Rossmann train data...")
    
    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found")
        return False
    
    # Load the data
    print("Reading CSV file...")
    train_df = pd.read_csv(train_path)
    
    # Apply limit if specified
    if limit_records:
        print(f"Limiting to {limit_records} records...")
        train_df = train_df.head(limit_records)
    
    # Convert date column to proper format
    train_df['Date'] = pd.to_datetime(train_df['Date'])
    
    total_records = len(train_df)
    print(f"Processing {total_records} sales records...")
    
    # Connect to the database
    try:
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # First, clear existing data
        cursor.execute("TRUNCATE TABLE rossmann_sales")
        
        # Process in batches
        start_time = time.time()
        for i in range(0, total_records, batch_size):
            batch = train_df.iloc[i:i+batch_size]
            
            # Prepare data for insertion
            values = [
                (
                    row['Store'], 
                    row['Date'].strftime('%Y-%m-%d'), 
                    row['Sales'], 
                    row['Customers'], 
                    row['Open'], 
                    row['Promo'], 
                    row['StateHoliday'], 
                    row['SchoolHoliday']
                ) 
                for _, row in batch.iterrows()
            ]
            
            # Generate the SQL query
            insert_query = """
            INSERT INTO rossmann_sales (
                store_id, date, sales, customers, open, promo, state_holiday, school_holiday
            ) VALUES %s
            """
            
            # Execute the query with batch values
            execute_values(cursor, insert_query, values)
            
            # Commit the batch
            conn.commit()
            
            # Calculate progress
            progress = min(100, (i + len(batch)) / total_records * 100)
            elapsed = time.time() - start_time
            records_per_sec = (i + len(batch)) / elapsed if elapsed > 0 else 0
            
            print(f"Progress: {progress:.1f}% ({i + len(batch)}/{total_records}) - {records_per_sec:.1f} records/sec")
        
        print(f"\nSuccessfully uploaded {total_records} sales records in {time.time() - start_time:.1f} seconds")
        return True
        
    except Exception as e:
        print(f"Error uploading sales data: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def check_env_file():
    """Check if .env file exists with Supabase credentials"""
    if not os.path.exists(".env") and not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")):
        print("Error: .env file not found or Supabase credentials not set")
        print("\nPlease create a .env file in the cloud-run-service directory with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_key")
        return False
    return True

def check_database_tables():
    """Check if the required tables exist in the database"""
    try:
        conn_params = get_connection_from_supabase_url()
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'rossmann_stores'
            )
        """)
        stores_exists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'rossmann_sales'
            )
        """)
        sales_exists = cursor.fetchone()[0]
        
        conn.close()
        
        if not stores_exists or not sales_exists:
            print("Error: Required tables do not exist in the database")
            print("Please run the supabase_rossmann_normalized.sql script first")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error checking database tables: {str(e)}")
        return False

if __name__ == "__main__":
    print("Rossmann Dataset Uploader for Time Series Analysis API (Normalized Version)")
    print("=====================================================================")
    
    # Check if .env file exists with Supabase credentials
    if not check_env_file():
        sys.exit(1)
    
    # Check if database tables exist
    if not check_database_tables():
        sys.exit(1)
    
    # Default paths
    default_train_path = "../data/rossmann-store-sales/train.csv"
    default_store_path = "../data/rossmann-store-sales/store.csv"
    
    # Check if default paths exist
    default_paths_exist = os.path.exists(default_train_path) and os.path.exists(default_store_path)
    
    if not default_paths_exist:
        print("\nDefault data paths not found:")
        print(f"- Train data: {default_train_path}")
        print(f"- Store data: {default_store_path}")
        print("\nPlease enter the paths to your Rossmann dataset files:")
        
        train_path = input("Path to train.csv: ").strip()
        store_path = input("Path to store.csv: ").strip()
    else:
        print("\nFound Rossmann dataset files at default locations:")
        print(f"- Train data: {default_train_path}")
        print(f"- Store data: {default_store_path}")
        
        use_default = input("Use these files? (y/n): ").lower()
        if use_default == 'y':
            train_path = default_train_path
            store_path = default_store_path
        else:
            train_path = input("Path to train.csv: ").strip()
            store_path = input("Path to store.csv: ").strip()
    
    # Ask about limiting records
    limit_option = input("\nLimit the number of sales records? (recommended for testing) (y/n): ").lower()
    limit_records = None
    if limit_option == 'y':
        try:
            limit_records = int(input("Enter maximum number of records (e.g., 100000): "))
        except ValueError:
            print("Invalid input, using all records")
    
    # Upload data
    print("\n1. Uploading store data...")
    store_success = upload_rossmann_store_data(store_path)
    
    if store_success:
        print("\n2. Uploading train data...")
        train_success = upload_rossmann_train_data(train_path, limit_records=limit_records)
    
    if store_success and train_success:
        print("\nSuccess! Both Rossmann datasets have been uploaded to normalized tables in Supabase.")
        print("You can now use them in the Time Series Analysis API.")
        print("\nTo query the data, you can use the rossmann_combined view which joins both tables.")
    else:
        print("\nUpload process completed with errors. Please check the messages above.") 