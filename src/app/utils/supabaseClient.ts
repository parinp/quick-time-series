import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase environment variables');
}

const supabase = createClient(supabaseUrl, supabaseKey);

export default supabase;

// Define interfaces for data types
interface SalesData {
  date: string;
  sales: number;
  store_id: number;
  customers?: number;
  open?: number;
  promo?: number;
  state_holiday?: string;
  school_holiday?: number;
  store_type?: string;
  assortment?: string;
  competition_distance?: number;
  competition_open_since_month?: number;
  competition_open_since_year?: number;
  promo2?: number;
  promo2_since_week?: number;
  promo2_since_year?: number;
  promo_interval?: string;
  [key: string]: any; // For any additional columns
}

// Interface for store ID data
interface StoreIdData {
  store_id: number;
}

// Function to fetch all unique store IDs directly from the database using RPC
export async function fetchAllStoreIds(): Promise<number[]> {
  try {
    // Use the RPC function to get distinct store IDs
    const { data, error } = await supabase
      .rpc('get_distinct_store_ids');
    
    if (error) {
      console.error('RPC error fetching store IDs:', error);
      
      // Fallback to direct query if RPC fails
      console.log('Falling back to direct query for store IDs');
      const { data: fallbackData, error: fallbackError } = await supabase
        .from('rossmann_sales')
        .select('store_id');
      
      if (fallbackError) {
        throw fallbackError;
      }
      
      // Use a Set to ensure uniqueness
      const storeIdSet = new Set<number>();
      fallbackData.forEach(item => storeIdSet.add(Number(item.store_id)));
      
      // Convert to array and sort
      const uniqueStoreIds = Array.from(storeIdSet).sort((a, b) => a - b);
      console.log(`Found ${uniqueStoreIds.length} unique store IDs using fallback method`);
      
      return uniqueStoreIds;
    }
    
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data format from RPC:', data);
      return [];
    }
    
    // Convert to array of numbers
    const storeIds = data.map((item: any) => {
      if (typeof item === 'object' && item !== null && 'store_id' in item) {
        return Number(item.store_id);
      } else if (typeof item === 'number') {
        return item;
      } else {
        console.warn('Unexpected store_id format:', item);
        return 0;
      }
    }).filter(id => id > 0);
    
    console.log(`Found ${storeIds.length} unique store IDs using RPC`);
    
    return storeIds;
  } catch (error) {
    console.error('Error fetching store IDs:', error);
    return [];
  }
}

// Function to fetch Rossmann sales data aggregated by date for all stores
export async function fetchRossmannData() {
  try {
    // Use the RPC function to get aggregated sales data by date
    const { data, error } = await supabase
      .rpc('get_aggregated_sales_by_date');
    
    if (error) {
      console.error('RPC error fetching aggregated data:', error);
      
      // Fallback to direct query and client-side aggregation
      console.log('Falling back to direct query and client-side aggregation');
      const { data: fallbackData, error: fallbackError } = await supabase
        .from('rossmann_sales')
        .select('*')
        .order('date');
      
      if (fallbackError) {
        throw fallbackError;
      }
      
      // Process the data to aggregate by date across all stores
      const aggregatedData: Record<string, SalesData> = {};
      
      fallbackData.forEach(item => {
        const date = item.date;
        if (!aggregatedData[date]) {
          // Initialize with the first record for this date, but set store_id to 0 to indicate "all stores"
          aggregatedData[date] = { 
            ...item, 
            sales: 0,
            store_id: 0, // Use 0 to indicate aggregated data for all stores
            customers: 0 // Reset customers to aggregate
          };
        }
        aggregatedData[date].sales += item.sales;
        // Aggregate customers if available
        if (item.customers) {
          aggregatedData[date].customers += item.customers;
        }
      });
      
      return Object.values(aggregatedData);
    }
    
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data format from RPC:', data);
      throw new Error('Invalid data format received from server');
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching Rossmann data:', error);
    throw error;
  }
}

// Function to fetch available datasets
export async function fetchAvailableDatasets() {
  try {
    return await fetchAllStoreIds();
  } catch (error) {
    console.error('Error fetching available datasets:', error);
    throw error;
  }
}

// Function to fetch data for a specific store
export async function fetchStoreData(storeId: number) {
  try {
    // Use the RPC function to get aggregated sales data by date for a specific store
    const { data, error } = await supabase
      .rpc('get_aggregated_sales_by_date_for_store', { store_id_param: storeId });
    
    if (error) {
      console.error('RPC error fetching store data:', error);
      
      // Fallback to direct query and client-side aggregation
      console.log(`Falling back to direct query for store ${storeId}`);
      const { data: fallbackData, error: fallbackError } = await supabase
        .from('rossmann_sales')
        .select('*')
        .eq('store_id', storeId)
        .order('date');
      
      if (fallbackError) {
        throw fallbackError;
      }
      
      // Process the data to aggregate by date for this specific store
      const aggregatedData: Record<string, SalesData> = {};
      
      fallbackData.forEach(item => {
        const date = item.date;
        if (!aggregatedData[date]) {
          // Initialize with all columns from the first record for this date
          aggregatedData[date] = { ...item, sales: 0 };
          if (item.customers) {
            aggregatedData[date].customers = 0;
          }
        }
        aggregatedData[date].sales += item.sales;
        // Aggregate customers if available
        if (item.customers) {
          aggregatedData[date].customers += item.customers;
        }
      });
      
      return Object.values(aggregatedData);
    }
    
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data format from RPC:', data);
      throw new Error('Invalid data format received from server');
    }
    
    return data;
  } catch (error) {
    console.error(`Error fetching data for store ${storeId}:`, error);
    throw error;
  }
} 