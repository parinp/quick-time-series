-- Create sample_data table
CREATE TABLE IF NOT EXISTS sample_data (
  id BIGSERIAL PRIMARY KEY,
  dataset_name TEXT NOT NULL UNIQUE,
  data JSONB NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create model_results table
CREATE TABLE IF NOT EXISTS model_results (
  id BIGSERIAL PRIMARY KEY,
  model_name TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  metrics JSONB NOT NULL,
  feature_importance JSONB,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
  id BIGSERIAL PRIMARY KEY,
  model_id BIGINT REFERENCES model_results(id),
  date TEXT NOT NULL,
  predicted_value DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sample_data_dataset_name ON sample_data(dataset_name);
CREATE INDEX IF NOT EXISTS idx_model_results_dataset_name ON model_results(dataset_name);
CREATE INDEX IF NOT EXISTS idx_model_results_user_id ON model_results(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for sample_data table
CREATE TRIGGER update_sample_data_updated_at
BEFORE UPDATE ON sample_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create RLS policies
-- Enable RLS on tables
ALTER TABLE sample_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Sample data policies (public read, authenticated write)
CREATE POLICY "Allow public read access to sample_data" ON sample_data
  FOR SELECT USING (true);

CREATE POLICY "Allow authenticated insert to sample_data" ON sample_data
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update to sample_data" ON sample_data
  FOR UPDATE USING (auth.role() = 'authenticated');

-- Model results policies (authenticated only)
CREATE POLICY "Allow authenticated read access to model_results" ON model_results
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated insert to model_results" ON model_results
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update to own model_results" ON model_results
  FOR UPDATE USING (auth.role() = 'authenticated' AND (user_id = auth.uid() OR user_id IS NULL));

-- Predictions policies (authenticated only)
CREATE POLICY "Allow authenticated read access to predictions" ON predictions
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated insert to predictions" ON predictions
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Create storage bucket for model files
INSERT INTO storage.buckets (id, name, public) VALUES ('models', 'models', true)
ON CONFLICT (id) DO NOTHING;

-- Set up storage policies
CREATE POLICY "Allow public read access to models" ON storage.objects
  FOR SELECT USING (bucket_id = 'models');

CREATE POLICY "Allow authenticated insert to models" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'models' AND auth.role() = 'authenticated'); 