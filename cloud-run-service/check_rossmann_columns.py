import pandas as pd
import os

def check_columns(file_path, file_name):
    """Check column names in a CSV file"""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return
    
    print(f"\n{file_name} columns:")
    print("=" * 50)
    
    # Load the data
    df = pd.read_csv(file_path)
    
    # Print original column names
    print("Original column names:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")
    
    # Print lowercase column names
    print("\nLowercase column names:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col.lower()}")
    
    # Print sample data
    print("\nSample data (first row):")
    for col in df.columns:
        val = df[col].iloc[0] if len(df) > 0 else None
        print(f"  {col}: {val} ({type(val).__name__})")

# Default paths
store_path = "../data/rossmann-store-sales/store.csv"
train_path = "../data/rossmann-store-sales/train.csv"

# Check if default paths exist
if os.path.exists(store_path) and os.path.exists(train_path):
    check_columns(store_path, "Store data")
    check_columns(train_path, "Train data")
else:
    print("Default data paths not found. Please enter the paths to your Rossmann dataset files:")
    store_path = input("Path to store.csv: ").strip()
    train_path = input("Path to train.csv: ").strip()
    
    if os.path.exists(store_path):
        check_columns(store_path, "Store data")
    
    if os.path.exists(train_path):
        check_columns(train_path, "Train data") 