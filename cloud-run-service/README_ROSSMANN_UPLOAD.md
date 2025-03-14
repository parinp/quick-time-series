# Rossmann Dataset Uploader (Local Version)

This script allows you to upload only the Rossmann dataset to your Supabase database for use with the Time Series Analysis API. This version is designed to run completely locally without any Google Cloud dependencies.

## Prerequisites

1. A Supabase account and project
2. The Rossmann dataset files:
   - `train.csv` - The main Rossmann sales data
   - `store.csv` - The store information data
3. Python 3.7+ installed on your local machine

## Setup Instructions

### 1. Set up your environment

Create a `.env` file in the `cloud-run-service` directory with your Supabase credentials:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

You can find these values in your Supabase project dashboard under Project Settings > API.

Alternatively, you can rename the provided `.env.rossmann` file:

```bash
cp .env.rossmann .env
```

Then edit the `.env` file to add your actual Supabase credentials.

### 2. Install required packages

Make sure you have the required packages installed:

```bash
pip install pandas supabase python-dotenv
```

### 3. Prepare your database

You need to create the necessary table in your Supabase database. You can do this by:

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Create a new query
4. Copy and paste the contents of `supabase_rossmann_setup.sql`
5. Run the query

This will create the `sample_data` table needed to store the Rossmann dataset.

### 4. Run the script

Navigate to the `cloud-run-service` directory and run:

```bash
python upload_rossmann_only.py
```

The script will:
1. Check for your Supabase credentials
2. Look for the Rossmann dataset files in the default location (`../data/rossmann-store-sales/`)
3. If not found, prompt you to enter the paths to your files
4. Upload the data to your Supabase database

## Data Size Considerations

The Rossmann train dataset can be quite large. The script will:
- Estimate the size of the data before uploading
- Warn you if it exceeds 100MB (which may approach Supabase free tier limits)
- Offer to limit the number of records to stay within reasonable limits

## Running the API Locally

After uploading the data, you can run the FastAPI application locally:

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Navigate to the app directory:
   ```bash
   cd app
   ```

3. Run the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

4. Access the API at http://localhost:8000

## Troubleshooting

If you encounter any issues:

1. **Connection errors**: Check your Supabase URL and key in the `.env` file
2. **File not found errors**: Make sure the paths to your dataset files are correct
3. **Database errors**: Ensure the `sample_data` table exists in your Supabase database
4. **Import errors**: Make sure all required packages are installed

## Using the Data in the API

Once uploaded, you can access the Rossmann dataset in the Time Series Analysis API using the `/sample_data` endpoint with the dataset name "rossmann_train" or "rossmann_store". 