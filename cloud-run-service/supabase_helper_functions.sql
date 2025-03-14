-- Create a function to truncate the rossmann_sales table
-- This is needed because the Supabase API doesn't support TRUNCATE directly
CREATE OR REPLACE FUNCTION truncate_rossmann_sales()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER -- This runs with the privileges of the function creator
AS $$
BEGIN
  TRUNCATE TABLE rossmann_sales;
END;
$$;

-- Create a function to truncate the rossmann_stores table
CREATE OR REPLACE FUNCTION truncate_rossmann_stores()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  TRUNCATE TABLE rossmann_stores CASCADE;
END;
$$;

-- Create a function to get the count of records in each table
CREATE OR REPLACE FUNCTION get_rossmann_record_counts()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  store_count integer;
  sales_count integer;
  result json;
BEGIN
  SELECT COUNT(*) INTO store_count FROM rossmann_stores;
  SELECT COUNT(*) INTO sales_count FROM rossmann_sales;
  
  SELECT json_build_object(
    'store_count', store_count,
    'sales_count', sales_count
  ) INTO result;
  
  RETURN result;
END;
$$;

-- Grant access to these functions for authenticated users
GRANT EXECUTE ON FUNCTION truncate_rossmann_sales TO authenticated;
GRANT EXECUTE ON FUNCTION truncate_rossmann_stores TO authenticated;
GRANT EXECUTE ON FUNCTION get_rossmann_record_counts TO authenticated; 