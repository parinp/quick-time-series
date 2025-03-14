-- Add the day_of_week column to the rossmann_sales table
ALTER TABLE public.rossmann_sales 
ADD COLUMN IF NOT EXISTS day_of_week integer NULL;

-- Add a comment to explain the column
COMMENT ON COLUMN public.rossmann_sales.day_of_week IS 'Day of week (1 = Monday, 7 = Sunday)';

-- Create an index on the new column for better query performance
CREATE INDEX IF NOT EXISTS idx_rossmann_sales_day_of_week 
ON public.rossmann_sales USING btree (day_of_week);

-- Create an index on the combination of store_id and day_of_week for queries that filter on both
CREATE INDEX IF NOT EXISTS idx_rossmann_sales_store_day 
ON public.rossmann_sales USING btree (store_id, day_of_week);

-- Update the view if it exists (first check if it exists to avoid errors)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'rossmann_combined') THEN
        DROP VIEW IF EXISTS rossmann_combined;
        
        CREATE VIEW rossmann_combined AS
        SELECT 
            s.id,
            s.store_id,
            s.date,
            s.day_of_week,
            s.sales,
            s.customers,
            s.open,
            s.promo,
            s.state_holiday,
            s.school_holiday,
            st.store_type,
            st.assortment,
            st.competition_distance,
            st.competition_open_since_month,
            st.competition_open_since_year,
            st.promo2,
            st.promo2_since_week,
            st.promo2_since_year,
            st.promo_interval
        FROM 
            rossmann_sales s
        JOIN 
            rossmann_stores st ON s.store_id = st.store_id;
    END IF;
END
$$; 