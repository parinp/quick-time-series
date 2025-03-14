import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
sys.path.append('./app')
from supabase_client import upload_sample_data

# Load environment variables
load_dotenv()

def estimate_json_size_mb(data):
    """Estimate the size of JSON data in MB"""
    json_str = json.dumps(data)
    size_bytes = len(json_str.encode('utf-8'))
    size_mb = size_bytes / (1024 * 1024)
    return size_mb

def upload_rossmann_train_data(train_path, limit_records=False):
    """Upload Rossmann train data to Supabase"""
    print("Loading Rossmann train data...")
    
    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found")
        return False
    
    # Load the data
    train_df = pd.read_csv(train_path)
    
    # Convert to list of dictionaries
    data = train_df.to_dict(orient='records')
    
    # Estimate size
    estimated_size_mb = estimate_json_size_mb(data)
    print(f"Estimated data size: {estimated_size_mb:.2f} MB")
    
    # Warn if size is large
    if estimated_size_mb > 100:
        print(f"WARNING: Data size is large ({estimated_size_mb:.2f} MB). This may exceed Supabase free tier limits (500MB total).")
        print("Supabase free tier includes 500MB database storage.")
        
        if limit_records:
            # Calculate how many records would fit in ~100MB
            records_per_mb = len(data) / estimated_size_mb
            safe_record_count = int(100 * records_per_mb)
            safe_record_count = min(safe_record_count, len(data))
            
            print(f"Limiting to {safe_record_count} records (approximately 100MB)...")
            data = data[:safe_record_count]
        else:
            proceed = input("Do you want to proceed with uploading all records? (y/n): ")
            if proceed.lower() != 'y':
                print("Upload cancelled.")
                return False
    
    # Upload to Supabase
    print(f"Uploading {len(data)} records to Supabase...")
    upload_sample_data(
        dataset_name="rossmann_train",
        data=data,
        description="Rossmann Store Sales train data"
    )
    print("Upload complete!")
    return True

def upload_rossmann_store_data(store_path):
    """Upload Rossmann store data to Supabase"""
    print("Loading Rossmann store data...")
    
    if not os.path.exists(store_path):
        print(f"Error: {store_path} not found")
        return False
    
    # Load the data
    store_df = pd.read_csv(store_path)
    
    # Convert to list of dictionaries
    data = store_df.to_dict(orient='records')
    
    # Estimate size
    estimated_size_mb = estimate_json_size_mb(data)
    print(f"Estimated data size: {estimated_size_mb:.2f} MB")
    
    # Upload to Supabase (store data is small, no need to limit)
    print(f"Uploading {len(data)} records to Supabase...")
    upload_sample_data(
        dataset_name="rossmann_store",
        data=data,
        description="Rossmann Store information data"
    )
    print("Upload complete!")
    return True

def check_env_file():
    """Check if .env file exists with Supabase credentials"""
    if not os.path.exists(".env") and not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")):
        print("Error: .env file not found or Supabase credentials not set")
        print("\nPlease create a .env file in the cloud-run-service directory with:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_key")
        return False
    return True

if __name__ == "__main__":
    print("Rossmann Dataset Uploader for Time Series Analysis API")
    print("====================================================")
    
    # Check if .env file exists with Supabase credentials
    if not check_env_file():
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
    limit_records = input("\nLimit train data to stay within 100MB? (recommended for free tier) (y/n): ").lower() == 'y'
    
    # Upload data
    print("\n1. Uploading store data...")
    store_success = upload_rossmann_store_data(store_path)
    
    if store_success:
        print("\n2. Uploading train data...")
        train_success = upload_rossmann_train_data(train_path, limit_records)
    
    if store_success and train_success:
        print("\nSuccess! Both Rossmann datasets have been uploaded to Supabase.")
        print("You can now use them in the Time Series Analysis API.")
    else:
        print("\nUpload process completed with errors. Please check the messages above.") 