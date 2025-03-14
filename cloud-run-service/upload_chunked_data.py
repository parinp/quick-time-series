import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
import math
import time
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

def upload_data_in_chunks(df, dataset_name, description, chunk_size=5000):
    """
    Upload data to Supabase in chunks to avoid memory issues
    
    Args:
        df: DataFrame containing the data
        dataset_name: Name of the dataset
        description: Description of the dataset
        chunk_size: Number of records per chunk
    """
    total_records = len(df)
    num_chunks = math.ceil(total_records / chunk_size)
    
    print(f"Uploading {total_records} records in {num_chunks} chunks...")
    
    # Process each chunk
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_records)
        
        # Get chunk
        chunk_df = df.iloc[start_idx:end_idx]
        
        # Convert to list of dictionaries
        chunk_data = chunk_df.to_dict(orient='records')
        
        # Estimate size
        chunk_size_mb = estimate_json_size_mb(chunk_data)
        
        print(f"Chunk {i+1}/{num_chunks}: {len(chunk_data)} records, {chunk_size_mb:.2f} MB")
        
        # Create chunk dataset name
        chunk_dataset_name = f"{dataset_name}_chunk_{i+1}"
        
        # Upload chunk
        upload_sample_data(
            dataset_name=chunk_dataset_name,
            data=chunk_data,
            description=f"{description} (Chunk {i+1}/{num_chunks})"
        )
        
        print(f"Chunk {i+1}/{num_chunks} uploaded successfully")
        
        # Sleep to avoid rate limiting
        if i < num_chunks - 1:
            time.sleep(1)
    
    print(f"All {num_chunks} chunks uploaded successfully")
    print(f"To access the data, use the dataset names: {dataset_name}_chunk_1 to {dataset_name}_chunk_{num_chunks}")

def upload_rossmann_train_data_chunked(chunk_size=5000):
    """Upload Rossmann train data to Supabase in chunks"""
    print("Loading Rossmann train data...")
    
    # Check if the data file exists
    train_path = "../data/rossmann-store-sales/train.csv"
    
    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found")
        return
    
    # Load the data
    train_df = pd.read_csv(train_path)
    
    # Upload in chunks
    upload_data_in_chunks(
        train_df,
        dataset_name="rossmann_train",
        description="Rossmann Store Sales train data",
        chunk_size=chunk_size
    )

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
    
    # Store data is small, no need for chunking
    data = store_df.to_dict(orient='records')
    
    # Estimate size
    estimated_size_mb = estimate_json_size_mb(data)
    print(f"Estimated data size: {estimated_size_mb:.2f} MB")
    
    # Upload to Supabase
    print(f"Uploading {len(data)} records to Supabase...")
    upload_sample_data(
        dataset_name="rossmann_store",
        data=data,
        description="Rossmann Store information data"
    )
    print("Upload complete!")

def upload_house_sales_data_chunked(chunk_size=5000):
    """Upload House Sales KC sample data to Supabase in chunks"""
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
    
    # Upload in chunks
    upload_data_in_chunks(
        df,
        dataset_name="house_sales_kc",
        description="House Sales in King County, USA",
        chunk_size=chunk_size
    )

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
    
    if dataset in ['rossmann_train', 'all'] and os.path.exists(rossmann_train_path):
        chunk_size = int(input("Chunk size for Rossmann train data (default: 5000): ") or "5000")
        print("\nUploading Rossmann train data...")
        train_df = pd.read_csv(rossmann_train_path)
        upload_data_in_chunks(
            train_df,
            dataset_name="rossmann_train",
            description="Rossmann Store Sales train data",
            chunk_size=chunk_size
        )
    
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
        chunk_size = int(input("Chunk size for House Sales data (default: 5000): ") or "5000")
        print("\nUploading House Sales KC data...")
        df = pd.read_csv(house_sales_path)
        df['date'] = pd.to_datetime(df['date'])
        upload_data_in_chunks(
            df,
            dataset_name="house_sales_kc",
            description="House Sales in King County, USA",
            chunk_size=chunk_size
        )

if __name__ == "__main__":
    print("Time Series Analysis API - Chunked Data Uploader")
    print("===============================================")
    
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
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python upload_chunked_data.py [rossmann_train|rossmann_store|house_sales|all] [chunk_size]")
        print("  chunk_size: Optional chunk size (default: 5000)")
        sys.exit(1)
    
    dataset = sys.argv[1].lower()
    
    # Get chunk size if provided
    chunk_size = 5000
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        chunk_size = int(sys.argv[2])
    
    if dataset == "rossmann_train":
        upload_rossmann_train_data_chunked(chunk_size)
    elif dataset == "rossmann_store":
        upload_rossmann_store_data()
    elif dataset == "house_sales":
        upload_house_sales_data_chunked(chunk_size)
    elif dataset == "all":
        upload_rossmann_train_data_chunked(chunk_size)
        upload_rossmann_store_data()
        upload_house_sales_data_chunked(chunk_size)
    else:
        print(f"Unknown dataset: {dataset}")
        print("Available datasets: rossmann_train, rossmann_store, house_sales, all")
        sys.exit(1) 