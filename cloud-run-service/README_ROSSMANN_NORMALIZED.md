# Rossmann Dataset Uploader (Normalized Version)

This script uploads the Rossmann dataset to properly normalized tables in your Supabase database, optimized for multi-user dashboard access and efficient querying.

## Why Normalized Tables Instead of JSONB?

For a multi-user dashboard application, normalized tables offer significant advantages:

1. **Better Query Performance**: Normalized tables allow for more efficient filtering, sorting, and aggregation operations, which are crucial for interactive dashboards.

2. **Reduced Storage**: Normalized data typically uses less storage than JSONB, which stores field names with every record.

3. **Data Integrity**: Proper relationships between tables (store data and sales data) are enforced with foreign keys.

4. **Optimized for Concurrent Access**: PostgreSQL handles concurrent access to normalized tables very efficiently, which is important for multi-user scenarios.

5. **Better Indexing**: Normalized tables allow for more efficient indexing strategies, improving query performance.

## Prerequisites

1. A Supabase account and project
2. The Rossmann dataset files:
   - `train.csv` - The main Rossmann sales data
   - `store.csv` - The store information data
3. Python 3.7+ installed on your local machine
4. PostgreSQL client libraries (for psycopg2)

## Setup Instructions

### 1. Set up your environment

Create a `.env` file in the `cloud-run-service` directory with your Supabase credentials:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

You can find these values in your Supabase project dashboard under Project Settings > API. 
**Important**: For direct database access, you need to use the **service_role** key, not the anon key.

### 2. Install required packages

Make sure you have the required packages installed:

```bash
pip install pandas psycopg2-binary python-dotenv
```

### 3. Prepare your database

You need to create the normalized tables in your Supabase database:

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Create a new query
4. Copy and paste the contents of `supabase_rossmann_normalized.sql`
5. Run the query

This will create:
- `rossmann_stores` table - Contains store information
- `rossmann_sales` table - Contains sales data with foreign key to stores
- `rossmann_combined` view - A convenient view that joins both tables

### 4. Run the script

Navigate to the `cloud-run-service` directory and run:

```bash
python upload_rossmann_normalized.py
```

The script will:
1. Check for your Supabase credentials
2. Verify that the required tables exist in the database
3. Look for the Rossmann dataset files in the default location
4. Upload the data to your Supabase database in an optimized way

## Performance Optimizations

The script includes several optimizations for handling large datasets:

1. **Batch Processing**: Sales data is uploaded in batches to manage memory usage
2. **Progress Reporting**: Real-time progress updates with upload speed
3. **Efficient SQL**: Uses PostgreSQL's `execute_values` for bulk inserts
4. **Transaction Management**: Proper handling of database transactions

## Accessing the Data in Your Application

After uploading, you can access the data in several ways:

1. **Using the Combined View**: Query the `rossmann_combined` view to get joined data:
   ```sql
   SELECT * FROM rossmann_combined WHERE store_id = 1 ORDER BY date;
   ```

2. **Separate Tables**: Query the individual tables for specific needs:
   ```sql
   SELECT * FROM rossmann_stores WHERE store_type = 'a';
   SELECT * FROM rossmann_sales WHERE date BETWEEN '2015-01-01' AND '2015-01-31';
   ```

3. **From Your API**: Update your FastAPI endpoints to query these tables instead of the JSONB format.

## Troubleshooting

If you encounter any issues:

1. **Connection errors**: Make sure you're using the service_role key, not the anon key
2. **Permission errors**: Check that your Supabase policies are correctly set up
3. **Missing psycopg2**: Run `pip install psycopg2-binary`
4. **Table not found**: Make sure you've run the SQL setup script first 