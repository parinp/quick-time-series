// Define the structure for time series data
export interface TimeSeriesData {
  [key: string]: any;
}

// Define the structure for statistics
export interface Statistics {
  count: number;
  mean: number;
  median: number;
  min: number;
  max: number;
  stdDev: number;
}

// Define the structure for grouped data
export interface GroupedData {
  [key: string]: any;
}

// Define the structure for missing values
export interface MissingValues {
  [key: string]: number;
}

// Define the structure for time patterns
export interface TimePatterns {
  byMonth?: GroupedData[];
  byDayOfWeek?: GroupedData[];
  byYear?: GroupedData[];
  byQuarter?: GroupedData[];
}

// Define the structure for the Rossmann store data
export interface RossmannStoreData {
  Store: number;
  DayOfWeek: number;
  Date: string;
  Sales: number;
  Customers: number;
  Open: number;
  Promo: number;
  StateHoliday: string;
  SchoolHoliday: number;
}

// Define the structure for the Rossmann store information
export interface RossmannStoreInfo {
  Store: number;
  StoreType: string;
  Assortment: string;
  CompetitionDistance: number;
  CompetitionOpenSinceMonth: number;
  CompetitionOpenSinceYear: number;
  Promo2: number;
  Promo2SinceWeek: number;
  Promo2SinceYear: number;
  PromoInterval: string;
}

// Define the structure for Supabase Rossmann data
export interface SupabaseRossmannData {
  id: number;
  store_id: number;
  date: string;
  day_of_week: number;
  sales: number;
  customers: number;
  open: number;
  promo: number;
  state_holiday: string;
  school_holiday: number;
  store_type: string;
  assortment: string;
  competition_distance: number;
  competition_open_since_month: number;
  competition_open_since_year: number;
  promo2: number;
  promo2_since_week: number;
  promo2_since_year: number;
  promo_interval: string;
  created_at?: string;
}

// Define the structure for aggregated sales data
export interface AggregatedSalesData {
  date: string;
  sales: number;
}

// Define the structure for the data source
export interface DataSource {
  type: 'sample' | 'upload' | 'supabase';
  data: TimeSeriesData[];
  dateColumn?: string;
  targetColumn?: string;
}

// Define the structure for the visualization options
export interface VisualizationOptions {
  chartType: 'line' | 'bar' | 'scatter' | 'heatmap';
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  aggregateFunction?: 'mean' | 'sum' | 'count' | 'min' | 'max';
}

// Define the structure for the analysis results
export interface AnalysisResults {
  statistics?: Statistics;
  timePatterns?: TimePatterns;
  missingValues?: MissingValues;
  seasonalDecomposition?: any;
  autocorrelation?: number[];
  partialAutocorrelation?: number[];
} 