import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
import math
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

def upload_rossmann_train_data(limit_records=False):
    """Upload Rossmann train data to Supabase"""
    print("Loading Rossmann train data...")
    
    # Check if the data file exists
    train_path = "../data/rossmann-store-sales/train.csv"
    
    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found")
        return
    
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
                return
    
    # Upload to Supabase
    print(f"Uploading {len(data)} records to Supabase...")
    upload_sample_data(
        dataset_name="rossmann_train",
        data=data,
        description="Rossmann Store Sales train data"
    )
    print("Upload complete!")

def upload_rossmann_store_data():
    """Upload Rossmann store data to Supabase"""
    print("Loading Rossmann store data...")
    
    # Check if the data file exists
    store_path = "../data/rossmann-store-sales/store.csv"
    
    if not os.path.exists(store_path):
        print(f"Error: {store_path} not found")
        return
    
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

def upload_house_sales_data(limit_records=False):
    """Upload House Sales KC sample data to Supabase"""
    print("Loading House Sales KC data...")
    
    # Check if the data file exists
    data_path = "../data/House Sales KC/kc_house_data.csv"
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return
    
    # Load the data
    df = pd.read_csv(data_path)
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert to list of dictionaries
    data = df.to_dict(orient='records')
    
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
                return
    
    # Upload to Supabase
    print(f"Uploading {len(data)} records to Supabase...")
    upload_sample_data(
        dataset_name="house_sales_kc",
        data=data,
        description="House Sales in King County, USA"
    )
    print("Upload complete!")

def check_data_paths():
    """Check if data paths exist and suggest fixes if they don't"""
    rossmann_train_path = "../data/rossmann-store-sales/train.csv"
    rossmann_store_path = "../data/rossmann-store-sales/store.csv"
    house_sales_path = "../data/House Sales KC/kc_house_data.csv"
    
    paths_exist = True
    
    if not os.path.exists(rossmann_train_path):
        paths_exist = False
        print(f"Error: {rossmann_train_path} not found")
        
    if not os.path.exists(rossmann_store_path):
        paths_exist = False
        print(f"Error: {rossmann_store_path} not found")
        
    if not os.path.exists(house_sales_path):
        paths_exist = False
        print(f"Error: {house_sales_path} not found")
    
    if not paths_exist:
        print("\nSuggested fixes:")
        print("1. Make sure you're running the script from the cloud-run-service directory")
        print("2. Create the following directory structure and download the datasets:")
        print("   - ../data/rossmann-store-sales/train.csv")
        print("   - ../data/rossmann-store-sales/store.csv")
        print("   - ../data/House Sales KC/kc_house_data.csv")
        print("3. Or update the file paths in this script to match your local file structure")
        
        # Ask for custom paths
        use_custom_paths = input("\nWould you like to enter custom file paths? (y/n): ")
        if use_custom_paths.lower() == 'y':
            return False
    
    return paths_exist

def upload_with_custom_paths():
    """Upload data using custom file paths provided by the user"""
    print("\nEnter the full paths to your data files:")
    
    # Get custom paths
    rossmann_train_path = input("Rossmann train.csv path: ").strip()
    rossmann_store_path = input("Rossmann store.csv path: ").strip()
    house_sales_path = input("House Sales KC kc_house_data.csv path: ").strip()
    
    dataset = input("\nWhich dataset to upload? (rossmann_train/rossmann_store/house_sales/all): ").lower()
    limit_records = input("Limit records to stay within 100MB? (y/n): ").lower() == 'y'
    
    # Validate and upload
    if dataset in ['rossmann_train', 'all'] and os.path.exists(rossmann_train_path):
        print("\nUploading Rossmann train data...")
        train_df = pd.read_csv(rossmann_train_path)
        data = train_df.to_dict(orient='records')
        
        estimated_size_mb = estimate_json_size_mb(data)
        print(f"Estimated data size: {estimated_size_mb:.2f} MB")
        
        if limit_records and estimated_size_mb > 100:
            records_per_mb = len(data) / estimated_size_mb
            safe_record_count = int(100 * records_per_mb)
            data = data[:safe_record_count]
            print(f"Limited to {safe_record_count} records")
        
        upload_sample_data(
            dataset_name="rossmann_train",
            data=data,
            description="Rossmann Store Sales train data"
        )
        print("Rossmann train data uploaded successfully!")
    
    if dataset in ['rossmann_store', 'all'] and os.path.exists(rossmann_store_path):
        print("\nUploading Rossmann store data...")
        store_df = pd.read_csv(rossmann_store_path)
        data = store_df.to_dict(orient='records')
        
        upload_sample_data(
            dataset_name="rossmann_store",
            data=data,
            description="Rossmann Store information data"
        )
        print("Rossmann store data uploaded successfully!")
    
    if dataset in ['house_sales', 'all'] and os.path.exists(house_sales_path):
        print("\nUploading House Sales KC data...")
        df = pd.read_csv(house_sales_path)
        df['date'] = pd.to_datetime(df['date'])
        data = df.to_dict(orient='records')
        
        estimated_size_mb = estimate_json_size_mb(data)
        print(f"Estimated data size: {estimated_size_mb:.2f} MB")
        
        if limit_records and estimated_size_mb > 100:
            records_per_mb = len(data) / estimated_size_mb
            safe_record_count = int(100 * records_per_mb)
            data = data[:safe_record_count]
            print(f"Limited to {safe_record_count} records")
        
        upload_sample_data(
            dataset_name="house_sales_kc",
            data=data,
            description="House Sales in King County, USA"
        )
        print("House Sales KC data uploaded successfully!")

if __name__ == "__main__":
    print("Time Series Analysis API - Sample Data Uploader")
    print("==============================================")
    
    # Check if .env file exists with Supabase credentials
    if not os.path.exists(".env") and not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")):
        print("Error: .env file not found or Supabase credentials not set")
        print("Please create a .env file with SUPABASE_URL and SUPABASE_KEY")
        sys.exit(1)
    
    # Check if data paths exist
    paths_exist = check_data_paths()
    
    if not paths_exist:
        upload_with_custom_paths()
        sys.exit(0)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python upload_sample_data.py [rossmann_train|rossmann_store|house_sales|all] [--limit]")
        print("  --limit: Optional flag to limit data size to approximately 100MB")
        sys.exit(1)
    
    dataset = sys.argv[1].lower()
    limit_records = "--limit" in sys.argv
    
    if dataset == "rossmann_train":
        upload_rossmann_train_data(limit_records)
    elif dataset == "rossmann_store":
        upload_rossmann_store_data()
    elif dataset == "house_sales":
        upload_house_sales_data(limit_records)
    elif dataset == "all":
        upload_rossmann_train_data(limit_records)
        upload_rossmann_store_data()
        upload_house_sales_data(limit_records)
    else:
        print(f"Unknown dataset: {dataset}")
        print("Available datasets: rossmann_train, rossmann_store, house_sales, all")
        sys.exit(1) 