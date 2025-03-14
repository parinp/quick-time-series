import pandas as pd
import os
import numpy as np
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_dataframe_for_json(df):
    """Clean a DataFrame to make it JSON serializable"""
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Define integer columns based on schema
    integer_columns = [
        'store_id', 'competition_distance', 'competition_open_since_month', 
        'competition_open_since_year', 'promo2', 'promo2_since_week', 
        'promo2_since_year', 'sales', 'customers', 'open', 'promo', 
        'school_holiday', 'day_of_week'
    ]
    
    # First, replace all NaN values with None
    df_clean = df_clean.replace({np.nan: None})
    
    # Process each column
    for col in df_clean.columns:
        # For integer columns, use pd.to_numeric with coerce
        if col in integer_columns and col in df_clean.columns:
            # First convert to numeric, coercing errors to NaN
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').astype("Int64")
            
    return df_clean

def upload_to_supabase(table_name, df, batch_size=500):
    """Uploads a Pandas DataFrame to Supabase in batches."""
    print(f"Preparing {table_name} data for upload...")
    
    # Clean the DataFrame for JSON serialization
    df_clean = clean_dataframe_for_json(df)
    
    # Convert DataFrame to list of dictionaries
    data = df_clean.to_dict(orient='records')
    
    # Final check to ensure no NaN values remain
    for record in data:
        for key, value in list(record.items()):
            if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                record[key] = None
    
    # Verify JSON serialization
    try:
        # Test with a sample
        sample = data[:min(10, len(data))]
        json_str = json.dumps(sample)
        print("Sample data is JSON serializable")
        
        # Print first record for debugging
        if sample:
            print("\nSample record:")
            for key, value in sample[0].items():
                print(f"  {key}: {value} ({type(value).__name__})")
        
        # Extra check for NaN values in the JSON string
        if "NaN" in json_str or "nan" in json_str:
            print("Warning: NaN values found in JSON string. Fixing...")
            for record in data:
                for key, value in list(record.items()):
                    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                        record[key] = None
    except TypeError as e:
        print(f"JSON serialization error: {e}")
        return False
    
    print(f"Uploading {len(data)} records to {table_name} table...")
    
    try:
        # Clear existing data
        try:
            supabase.rpc(f"truncate_rossmann_{table_name}").execute()
            print(f"Cleared existing {table_name} data")
        except Exception as e:
            print(f"Could not truncate table: {e}")
            print("Proceeding with insert anyway...")
        
        # Upload in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                supabase.table(f"rossmann_{table_name}").insert(batch).execute()
                print(f"Uploaded records {i+1} to {min(i+batch_size, len(data))} of {len(data)}")
            except Exception as e:
                print(f"Error uploading batch {i//batch_size + 1}: {e}")
                return False
        
        print(f"Successfully uploaded {len(data)} records to {table_name} table")
        return True
    
    except Exception as e:
        print(f"Error uploading data: {e}")
        return False

def main():
    print("Rossmann Dataset Uploader (Simplified Version)")
    print("==============================================")
    
    # Default paths
    default_store_path = "../data/rossmann-store-sales/store.csv"
    default_train_path = "../data/rossmann-store-sales/train.csv"
    
    # Check if default paths exist
    if os.path.exists(default_store_path) and os.path.exists(default_train_path):
        store_path = default_store_path
        train_path = default_train_path
        print(f"Using default data paths:\n- Store: {store_path}\n- Train: {train_path}")
    else:
        print("Default data paths not found.")
        store_path = input("Enter path to store.csv: ")
        train_path = input("Enter path to train.csv: ")
    
    # Load store data
    print("\nLoading store data...")
    store_df = pd.read_csv(store_path)
    
    # Rename columns to match database schema
    column_mapping = {
        'Store': 'store_id',
        'StoreType': 'store_type',
        'Assortment': 'assortment',
        'CompetitionDistance': 'competition_distance',
        'CompetitionOpenSinceMonth': 'competition_open_since_month',
        'CompetitionOpenSinceYear': 'competition_open_since_year',
        'Promo2': 'promo2',
        'Promo2SinceWeek': 'promo2_since_week',
        'Promo2SinceYear': 'promo2_since_year',
        'PromoInterval': 'promo_interval'
    }
    store_df = store_df.rename(columns=column_mapping)
    
    # Upload store data
    store_success = upload_to_supabase("stores", store_df)
    
    if store_success:
        # Ask about limiting records
        limit_option = input("\nLimit the number of sales records? (recommended for testing) (y/n): ").lower()
        limit_records = None
        if limit_option == 'y':
            try:
                limit_records = int(input("Enter maximum number of records (e.g., 10000): "))
            except ValueError:
                print("Invalid input, using all records")
        
        # Load train data
        print("\nLoading train data...")
        train_df = pd.read_csv(train_path)
        
        # Apply limit if specified
        if limit_records:
            print(f"Limiting to {limit_records} records...")
            train_df = train_df.head(limit_records)
        
        # Rename columns to match database schema
        column_mapping = {
            'Store': 'store_id',
            'Date': 'date',
            'DayOfWeek': 'day_of_week',
            'Sales': 'sales',
            'Customers': 'customers',
            'Open': 'open',
            'Promo': 'promo',
            'StateHoliday': 'state_holiday',
            'SchoolHoliday': 'school_holiday'
        }
        train_df = train_df.rename(columns=column_mapping)
        
        # Convert date column to proper format
        train_df['date'] = pd.to_datetime(train_df['date'])
        train_df['date'] = train_df['date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None)
        
        # Upload train data
        train_success = upload_to_supabase("sales", train_df)
        
        if train_success:
            print("\nSuccess! Both Rossmann datasets have been uploaded to Supabase.")
            print("You can now use them in the Time Series Analysis API.")
        else:
            print("\nFailed to upload train data.")
    else:
        print("\nFailed to upload store data.")

if __name__ == "__main__":
    main()
