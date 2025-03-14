import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase environment variables');
}

const supabase = createClient(supabaseUrl, supabaseKey);

export default supabase;

// Function to fetch Rossmann sales data
export async function fetchRossmannData(limit = 10000) {
  try {
    // Use the rossmann_combined view to get both sales and store data
    const { data, error } = await supabase
      .from('rossmann_combined')
      .select('*')
      .limit(limit);
    
    if (error) {
      throw error;
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
    const { data, error } = await supabase
      .from('rossmann_stores')
      .select('store_id')
      .order('store_id');
    
    if (error) {
      throw error;
    }
    
    return data.map(item => item.store_id);
  } catch (error) {
    console.error('Error fetching available datasets:', error);
    throw error;
  }
}

// Function to fetch data for a specific store
export async function fetchStoreData(storeId: number) {
  try {
    const { data, error } = await supabase
      .from('rossmann_combined')
      .select('*')
      .eq('store_id', storeId)
      .order('date');
    
    if (error) {
      throw error;
    }
    
    return data;
  } catch (error) {
    console.error(`Error fetching data for store ${storeId}:`, error);
    throw error;
  }
} 