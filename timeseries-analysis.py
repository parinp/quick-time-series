import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from sklearn.preprocessing import StandardScaler
from scipy import stats
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

def select_csv_file():
    """Open a file dialog for the user to select a CSV file"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring dialog to front
    file_path = filedialog.askopenfilename(
        title="Select CSV File with Sales Data",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    return file_path

def analyze_sales_timeseries():
    """Launch UI to select file and columns, then analyze time series sales data"""
    # Create main window
    root = tk.Tk()
    root.title("Sales Time Series Analysis")
    root.geometry("600x350")
    root.resizable(True, True)
    
    # Variables to store selections
    file_path_var = tk.StringVar()
    date_column_var = tk.StringVar()
    sales_column_var = tk.StringVar()
    
    # Function to load CSV and update dropdown options
    def load_csv():
        file_path = select_csv_file()
        if file_path:
            file_path_var.set(file_path)
            try:
                # Read only the header to get column names
                df_headers = pd.read_csv(file_path, nrows=0)
                column_names = df_headers.columns.tolist()
                
                # Update dropdowns with column names
                date_dropdown['values'] = column_names
                sales_dropdown['values'] = column_names
                
                # Auto-select date and sales columns if they exist
                date_cols = [col for col in column_names if 'date' in col.lower()]
                if date_cols:
                    date_column_var.set(date_cols[0])
                
                sales_cols = [col for col in column_names if 'sale' in col.lower()]
                if sales_cols:
                    sales_column_var.set(sales_cols[0])
                
                status_label.config(text=f"File loaded: {file_path.split('/')[-1]}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")
    
    # Function to run analysis
    def run_analysis():
        file_path = file_path_var.get()
        date_column = date_column_var.get()
        sales_column = sales_column_var.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return
        
        if not date_column:
            messagebox.showerror("Error", "Please select a date column.")
            return
        
        if not sales_column:
            messagebox.showerror("Error", "Please select a sales column.")
            return
        
        # Close the UI
        root.destroy()
        
        # Run the analysis
        process_and_analyze_data(file_path, date_column, sales_column)
    
    # UI Components
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    # File selection
    ttk.Label(frame, text="Step 1: Select your sales data CSV file", font=('Arial', 12, 'bold')).grid(column=0, row=0, sticky=tk.W, pady=(0, 10), columnspan=2)
    
    file_button = ttk.Button(frame, text="Browse Files...", command=load_csv)
    file_button.grid(column=0, row=1, sticky=tk.W, pady=5)
    
    status_label = ttk.Label(frame, text="No file selected")
    status_label.grid(column=1, row=1, sticky=tk.W, padx=10, pady=5)
    
    # Column selection
    ttk.Label(frame, text="Step 2: Select your date and sales columns", font=('Arial', 12, 'bold')).grid(column=0, row=2, sticky=tk.W, pady=(20, 10), columnspan=2)
    
    ttk.Label(frame, text="Date Column:").grid(column=0, row=3, sticky=tk.W, pady=5)
    date_dropdown = ttk.Combobox(frame, textvariable=date_column_var, width=30)
    date_dropdown.grid(column=1, row=3, sticky=tk.W, pady=5)
    
    ttk.Label(frame, text="Sales Column:").grid(column=0, row=4, sticky=tk.W, pady=5)
    sales_dropdown = ttk.Combobox(frame, textvariable=sales_column_var, width=30)
    sales_dropdown.grid(column=1, row=4, sticky=tk.W, pady=5)
    
    # Run button
    run_button = ttk.Button(frame, text="Run Analysis", command=run_analysis)
    run_button.grid(column=0, row=5, columnspan=2, pady=(20, 0))
    
    # Style configuration
    style = ttk.Style()
    style.configure('TButton', font=('Arial', 11))
    style.configure('TLabel', font=('Arial', 11))
    style.configure('TCombobox', font=('Arial', 11))
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    root.mainloop()

def process_and_analyze_data(csv_file, date_column, sales_column):
    """
    Analyze time series sales data and explain potential influencing factors
    
    Parameters:
    csv_file (str): Path to CSV file containing sales data
    date_column (str): Name of the date column
    sales_column (str): Name of the sales column
    """
    print(f"Loading data from {csv_file}")
    print(f"Using '{date_column}' as date column and '{sales_column}' as sales column")
    
    # Load the data
    try:
        df = pd.read_csv(csv_file)
        
        # Convert date column to datetime
        df[date_column] = pd.to_datetime(df[date_column])
        df.set_index(date_column, inplace=True)
        
        # Basic statistics
        print("\n--- BASIC STATISTICS ---")
        stats_summary = df[sales_column].describe()
        print(stats_summary)
        
        # Time series visualization
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df[sales_column])
        plt.title(f"{sales_column} Over Time")
        plt.xlabel("Date")
        plt.ylabel(sales_column)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("sales_over_time.png")
        print("\nSales time series plot saved as 'sales_over_time.png'")
        
        # Check for stationarity
        print("\n--- STATIONARITY CHECK ---")
        adf_result = adfuller(df[sales_column].dropna())
        print(f"ADF Statistic: {adf_result[0]}")
        print(f"p-value: {adf_result[1]}")
        
        # Explain null hypothesis in plain language
        print("\nWhat does this mean?")
        if adf_result[1] <= 0.05:
            print("The time series is stationary. In simple terms, this means the data's basic properties")
            print("(like average and variance) remain constant over time. This makes it easier to predict")
            print("future values because the pattern of the data isn't changing fundamentally.")
        else:
            print("The time series is non-stationary. In simple terms, this means the data's basic properties")
            print("(like average and variance) are changing over time. This could indicate trends, seasonal")
            print("patterns, or structural shifts in your sales that make simple prediction more challenging.")
        
        print("\nThe null hypothesis in this test assumes your data is non-stationary (has trends or")
        print("seasonal patterns). When we reject this hypothesis (p-value ≤ 0.05), we're saying there's")
        print("strong statistical evidence that your data is actually stationary.")
        
        # Time series decomposition
        try:
            print("\n--- TIME SERIES DECOMPOSITION ---")
            # Check if we have enough data points for decomposition
            if len(df) >= 4:
                # Try to determine the frequency
                if len(df) >= 365:
                    freq = 365  # Daily data for a year
                elif len(df) >= 52:
                    freq = 52   # Weekly data for a year
                elif len(df) >= 12:
                    freq = 12   # Monthly data for a year
                elif len(df) >= 4:
                    freq = 4    # Quarterly data for a year
                else:
                    freq = 2    # Minimum frequency
                
                decomposition = seasonal_decompose(df[sales_column], model='additive', period=freq)
                
                # Plot decomposition
                fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10))
                decomposition.observed.plot(ax=ax1)
                ax1.set_title('Observed')
                decomposition.trend.plot(ax=ax2)
                ax2.set_title('Trend')
                decomposition.seasonal.plot(ax=ax3)
                ax3.set_title('Seasonality')
                decomposition.resid.plot(ax=ax4)
                ax4.set_title('Residuals')
                plt.tight_layout()
                plt.savefig("sales_decomposition.png")
                print("Time series decomposition saved as 'sales_decomposition.png'")
                print("\nWhat does this mean?")
                print("We've broken down your sales data into three key components:")
                print("1. Trend: The long-term direction your sales are moving (up, down, or flat)")
                print("2. Seasonality: Recurring patterns that happen at regular intervals")
                print("3. Residuals: Unexplained variations that don't fit the trend or seasonality")
                print("\nThis helps identify what's driving your sales changes - is it a steady growth trend,")
                print("predictable seasonal patterns, or random fluctuations?")
                
                # Seasonality analysis
                seasonal_data = decomposition.seasonal
                high_season_idx = seasonal_data.idxmax()
                low_season_idx = seasonal_data.idxmin()
                print(f"\nPeak sales season: {high_season_idx}")
                print(f"Low sales season: {low_season_idx}")
            else:
                print("Not enough data points for decomposition analysis")
        except Exception as e:
            print(f"Could not perform decomposition: {str(e)}")
        
        # Check for outliers
        print("\n--- OUTLIER ANALYSIS ---")
        z_scores = stats.zscore(df[sales_column].dropna())
        outliers = np.abs(z_scores) > 3
        if np.sum(outliers) > 0:
            print(f"Found {np.sum(outliers)} outliers (using 3-sigma rule)")
            outlier_dates = df.index[outliers]
            print("Outlier dates:", outlier_dates.tolist())
            print("\nWhat does this mean?")
            print("These are unusual sales periods that differ significantly from your normal patterns.")
            print("They might represent special events, promotions, data errors, or external factors")
            print("affecting your business. Investigating these specific dates could reveal valuable insights.")
        else:
            print("No significant outliers detected")
            print("\nWhat does this mean?")
            print("Your sales follow relatively consistent patterns without extreme spikes or drops.")
            print("This suggests stable business operations or that any variations fall within")
            print("expected normal fluctuations.")
        
        # Analyze potential factors affecting sales
        print("\n--- FACTORS AFFECTING SALES ---")
        analyze_factors(df, sales_column)
        
        print("\n--- SUMMARY INSIGHTS ---")
        generate_insights(df, sales_column)
        
        # Final explanation
        print("\n--- WHAT TO DO WITH THESE INSIGHTS ---")
        print("1. Look at the trend to understand your long-term business direction")
        print("2. Use seasonality patterns to plan inventory, staffing, and promotions")
        print("3. Investigate outliers to understand exceptional circumstances")
        print("4. Consider the factors most correlated with sales for business planning")
        print("5. Use the stationarity results to inform your forecasting approach")
        
        return df
    
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        return None

def analyze_factors(df, sales_col):
    """Analyze how different factors correlate with sales"""
    # Identify numeric columns as potential factors
    potential_factors = df.select_dtypes(include=[np.number]).columns.tolist()
    potential_factors = [col for col in potential_factors if col != sales_col]
    
    if not potential_factors:
        print("No additional numeric factors found in the dataset.")
        print("\nWhat does this mean?")
        print("Your dataset only contains the sales values without other variables that might explain")
        print("what's driving your sales. Consider adding data like marketing spend, pricing, competitor")
        print("activity, economic indicators, or weather to gain deeper insights.")
        return
    
    print(f"Analyzing {len(potential_factors)} potential factors:")
    
    # Calculate correlation with sales
    correlations = []
    for factor in potential_factors:
        corr = df[factor].corr(df[sales_col])
        if not pd.isna(corr):
            correlations.append((factor, corr))
    
    # Sort by absolute correlation
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Print correlations
    for factor, corr in correlations:
        strength = ""
        if abs(corr) >= 0.7:
            strength = "Strong"
        elif abs(corr) >= 0.3:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        direction = "positive" if corr > 0 else "negative"
        print(f"- {factor}: {strength} {direction} correlation ({corr:.3f})")
    
    print("\nWhat does this mean?")
    print("Correlation measures how closely two variables move together:")
    print("- Positive correlation: When this factor increases, sales tend to increase")
    print("- Negative correlation: When this factor increases, sales tend to decrease")
    print("- Stronger correlations (closer to 1 or -1) suggest more reliable relationships")
    print("\nRemember: Correlation doesn't prove causation. These relationships show connection,")
    print("not necessarily that one factor directly causes sales changes.")
    
    # Plot correlations for top factors
    if correlations:
        plt.figure(figsize=(10, 6))
        factors, corrs = zip(*correlations[:min(5, len(correlations))])
        colors = ['green' if c > 0 else 'red' for c in corrs]
        plt.bar(factors, [abs(c) for c in corrs], color=colors)
        plt.axhline(y=0.3, color='gray', linestyle='--', alpha=0.7)
        plt.axhline(y=0.7, color='gray', linestyle='--', alpha=0.7)
        plt.title('Top Factors Correlation with Sales')
        plt.ylabel('Absolute Correlation')
        plt.ylim(0, 1)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig("factor_correlations.png")
        print("\nFactor correlation chart saved as 'factor_correlations.png'")
        
        # Create scatter plots for top 2 factors
        if len(correlations) >= 2:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # First factor
            ax1.scatter(df[correlations[0][0]], df[sales_col], alpha=0.6)
            ax1.set_title(f"Sales vs {correlations[0][0]}")
            ax1.set_xlabel(correlations[0][0])
            ax1.set_ylabel(sales_col)
            
            # Second factor
            ax2.scatter(df[correlations[1][0]], df[sales_col], alpha=0.6)
            ax2.set_title(f"Sales vs {correlations[1][0]}")
            ax2.set_xlabel(correlations[1][0])
            ax2.set_ylabel(sales_col)
            
            plt.tight_layout()
            plt.savefig("top_factor_scatterplots.png")
            print("Top factor scatter plots saved as 'top_factor_scatterplots.png'")

def generate_insights(df, sales_col):
    """Generate high-level insights about the sales data"""
    # Calculate year-over-year growth if possible
    try:
        df['year'] = df.index.year
        yearly_sales = df.groupby('year')[sales_col].sum()
        
        if len(yearly_sales) >= 2:
            yoy_growth_pct = (yearly_sales.iloc[-1] / yearly_sales.iloc[-2] - 1) * 100
            print(f"Year-over-year growth: {yoy_growth_pct:.2f}%")
            
            # Compare with previous year-over-year growth if enough data
            if len(yearly_sales) >= 3:
                prev_yoy_growth_pct = (yearly_sales.iloc[-2] / yearly_sales.iloc[-3] - 1) * 100
                growth_change = yoy_growth_pct - prev_yoy_growth_pct
                
                if growth_change > 0:
                    print(f"Growth is accelerating (+{growth_change:.2f}% change in growth rate)")
                else:
                    print(f"Growth is decelerating ({growth_change:.2f}% change in growth rate)")
        
        # Print yearly sales
        print("\nYearly sales summary:")
        for year, sales in yearly_sales.items():
            print(f"- {year}: {sales:.2f}")
    except Exception as e:
        print("Couldn't calculate year-over-year growth:", str(e))
    
    # Check for seasonality patterns
    try:
        df['month'] = df.index.month
        monthly_avg = df.groupby('month')[sales_col].mean()
        
        high_month = monthly_avg.idxmax()
        low_month = monthly_avg.idxmin()
        highest = monthly_avg.max()
        lowest = monthly_avg.min()
        
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        print(f"\nHighest average sales: {month_names[high_month]} ({highest:.2f})")
        print(f"Lowest average sales: {month_names[low_month]} ({lowest:.2f})")
        
        seasonality_ratio = highest / lowest
        if seasonality_ratio > 1.5:
            print(f"Strong seasonal pattern detected (high/low ratio: {seasonality_ratio:.2f})")
            print("This means your sales vary significantly throughout the year.")
        elif seasonality_ratio > 1.2:
            print(f"Moderate seasonal pattern detected (high/low ratio: {seasonality_ratio:.2f})")
            print("This means your sales have noticeable but not extreme seasonal variations.")
        else:
            print(f"Weak or no seasonal pattern detected (high/low ratio: {seasonality_ratio:.2f})")
            print("This means your sales remain relatively consistent throughout the year.")
    except Exception as e:
        print("Couldn't analyze seasonality:", str(e))
    
    # General trend analysis
    try:
        first_half = df[sales_col].iloc[:len(df)//2].mean()
        second_half = df[sales_col].iloc[len(df)//2:].mean()
        
        if second_half > first_half * 1.1:
            print("\nOverall trend: Strong upward trend")
            print("Your business is growing substantially over the analyzed period.")
        elif second_half > first_half * 1.02:
            print("\nOverall trend: Slight upward trend")
            print("Your business is showing modest growth over the analyzed period.")
        elif second_half < first_half * 0.9:
            print("\nOverall trend: Strong downward trend")
            print("Your business is experiencing significant decline over the analyzed period.")
        elif second_half < first_half * 0.98:
            print("\nOverall trend: Slight downward trend")
            print("Your business is showing a slight decline over the analyzed period.")
        else:
            print("\nOverall trend: Relatively stable")
            print("Your business is maintaining consistent sales levels over the analyzed period.")
    except Exception as e:
        print("Couldn't analyze overall trend:", str(e))

if __name__ == "__main__":
    analyze_sales_timeseries()