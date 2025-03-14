import supabase from './supabaseClient';

async function testSupabaseConnection() {
  try {
    console.log('Testing Supabase connection...');
    
    // Test connection by getting the server version
    const { data: versionData, error: versionError } = await supabase.rpc('version');
    
    if (versionError) {
      console.error('Error connecting to Supabase:', versionError);
      return;
    }
    
    console.log('Connected to Supabase:', versionData);
    
    // Check rossmann_sales table
    const { data: salesData, error: salesError } = await supabase
      .from('rossmann_sales')
      .select('date, sales')
      .limit(5);
    
    if (salesError) {
      console.error('Error fetching sales data:', salesError);
      return;
    }
    
    console.log('Sample sales data:', salesData);
    
    // Count total records in rossmann_sales
    const { count: salesCount, error: countError } = await supabase
      .from('rossmann_sales')
      .select('*', { count: 'exact', head: true });
    
    if (countError) {
      console.error('Error counting sales records:', countError);
      return;
    }
    
    console.log('Total sales records:', salesCount);
    
    // Get unique dates
    const { data: datesData, error: datesError } = await supabase
      .from('rossmann_sales')
      .select('date')
      .order('date');
    
    if (datesError) {
      console.error('Error fetching dates:', datesError);
      return;
    }
    
    const uniqueDates = new Set(datesData.map(item => item.date));
    console.log('Number of unique dates:', uniqueDates.size);
    console.log('Sample dates:', Array.from(uniqueDates).slice(0, 5));
    
  } catch (error) {
    console.error('Unexpected error:', error);
  }
}

// Run the test
testSupabaseConnection();

export default testSupabaseConnection; 