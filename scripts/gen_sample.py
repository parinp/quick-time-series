import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def create_representative_sample(input_file, output_file, sample_size=1000):
    """
    Creates a representative sample of rows from a CSV file.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to save the output CSV file
        sample_size (int): Number of rows to sample (default: 1000)
    """
    # Read the original CSV file
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Check if sample size is smaller than the dataset
    if len(df) <= sample_size:
        print(f"Dataset only has {len(df)} rows, which is less than or equal to the requested sample size.")
        df.to_csv(output_file, index=False)
        print(f"Saved entire dataset to {output_file}")
        return
    
    # Use stratified sampling if categorical column is available
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    
    if len(categorical_columns) > 0:
        # Use the first categorical column for stratification
        strat_column = categorical_columns[0]
        print(f"Using stratified sampling based on column: {strat_column}")
        
        # Handle rare categories by grouping them
        value_counts = df[strat_column].value_counts()
        rare_categories = value_counts[value_counts < 10].index
        
        if len(rare_categories) > 0:
            df[strat_column + '_grouped'] = df[strat_column].apply(
                lambda x: 'RARE_CATEGORY' if x in rare_categories else x
            )
            strat_column = strat_column + '_grouped'
        
        # Perform stratified sampling
        try:
            df_sample, _ = train_test_split(
                df, 
                train_size=sample_size,
                stratify=df[strat_column],
                random_state=42
            )
        except ValueError:
            print("Stratified sampling failed, falling back to random sampling with representative numeric columns")
            df_sample = random_sampling_with_numeric_representation(df, sample_size)
    else:
        print("No categorical columns found for stratification, using numeric representation approach")
        df_sample = random_sampling_with_numeric_representation(df, sample_size)
    
    # Save the sampled data to a new CSV file
    df_sample.to_csv(output_file, index=False)
    print(f"Successfully saved {len(df_sample)} sampled rows to {output_file}")
    
    # Print some statistics to verify representativeness
    print("\nComparing sample statistics with original data:")
    numeric_cols = df.select_dtypes(include=np.number).columns[:5]  # Limit to first 5 numeric columns
    
    for col in numeric_cols:
        orig_mean = df[col].mean()
        sample_mean = df_sample[col].mean()
        orig_std = df[col].std()
        sample_std = df_sample[col].std()
        
        print(f"Column: {col}")
        print(f"  Original  - Mean: {orig_mean:.4f}, Std: {orig_std:.4f}")
        print(f"  Sampled   - Mean: {sample_mean:.4f}, Std: {sample_std:.4f}")
        print(f"  Difference- Mean: {abs(orig_mean - sample_mean):.4f}, Std: {abs(orig_std - sample_std):.4f}")
        print()

def random_sampling_with_numeric_representation(df, sample_size):
    """
    Performs random sampling while trying to maintain distribution of numeric columns.
    """
    numeric_cols = df.select_dtypes(include=np.number).columns
    
    if len(numeric_cols) > 0:
        # Try using k-means to create representative clusters
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        # Select numeric columns for clustering
        X = df[numeric_cols].fillna(df[numeric_cols].mean())
        
        # Standardize the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine number of clusters (sqrt of sample size is a common heuristic)
        n_clusters = min(int(np.sqrt(sample_size)), len(df) // 5)
        n_clusters = max(n_clusters, 2)  # At least 2 clusters
        
        # Apply k-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df['cluster'] = kmeans.fit_predict(X_scaled)
        
        # Sample from each cluster proportionally
        sampled_rows = []
        for cluster_id in range(n_clusters):
            cluster_df = df[df['cluster'] == cluster_id]
            cluster_prop = len(cluster_df) / len(df)
            cluster_samples = max(1, int(sample_size * cluster_prop))
            if len(cluster_df) > cluster_samples:
                sampled_rows.append(cluster_df.sample(cluster_samples, random_state=42))
            else:
                sampled_rows.append(cluster_df)
        
        # Combine all sampled clusters
        df_sample = pd.concat(sampled_rows)
        
        # If we got too many samples, randomly drop some
        if len(df_sample) > sample_size:
            df_sample = df_sample.sample(sample_size, random_state=42)
        
        # Remove the temporary cluster column
        df_sample = df_sample.drop('cluster', axis=1)
    else:
        # If no numeric columns, use simple random sampling
        df_sample = df.sample(sample_size, random_state=42)
    
    return df_sample

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a representative sample of CSV data.')
    parser.add_argument('input_file', help='Path to the input CSV file')
    parser.add_argument('output_file', help='Path to save the output CSV file')
    parser.add_argument('--size', type=int, default=1000, help='Number of rows to sample (default: 1000)')
    
    args = parser.parse_args()
    
    create_representative_sample(args.input_file, args.output_file, args.size)