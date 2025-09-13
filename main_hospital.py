# main_hospital.py
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ------------------- Data Loading -------------------
def load_data(file_path: str = "Hospital_Management_Data.xlsx"):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {e}")

# ------------------- Cleaning Functions -------------------
def rename_columns(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
    return df

def check_missing_values(df):
    return df.isnull().sum()

def fill_missing_values(df, value=0):
    return df.fillna(value)

def drop_missing_values(df):
    return df.dropna()

def remove_duplicates(df, subset=None):
    if subset is None:
        return df.drop_duplicates()
    return df.drop_duplicates(subset=subset)

def change_column_dtype(df, column, dtype):
    try:
        df[column] = df[column].astype(dtype)
    except Exception as e:
        print(f"Error converting {column}: {e}")
    return df

def clean_text_column(df, column):
    if column in df.columns:
        df[column] = df[column].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

# ------------------- Analysis Functions -------------------
def top_n_products_by_revenue(df, n=10):
    return df.groupby('product_name')['sales_revenue'].sum().sort_values(ascending=False).head(n)

def top_n_regions_by_revenue(df, n=10):
    return df.groupby('region')['sales_revenue'].sum().sort_values(ascending=False).head(n)

def monthly_sales(df):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    # return df.groupby('month')['units_sold','sales_revenue'].sum().sort_index()
    return df.groupby('month')[['units_sold', 'sales_revenue']].sum().sort_index()


def product_monthly_series(df, product_id_or_name):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    # df = df[df['product_id'].astype(str) == str(product_id_or_name) | (df['product_name'] == product_id_or_name)]
    df = df[(df['product_id'].astype(str) == str(product_id_or_name)) | (df['product_name'] == product_id_or_name)]

    if df.empty:
        return pd.Series(dtype=float)
    s = df.groupby(pd.Grouper(key='date', freq='M'))['units_sold'].sum().asfreq('M').fillna(0)
    return s

# Simple moving-average forecast (naive)
def moving_average_forecast(series, window=3, periods=3):
    """
    series: pandas Series indexed by datetime (monthly)
    returns: pandas Series of forecasted periods
    """
    if series.empty:
        return pd.Series(dtype=float)
    last = series.dropna()
    if len(last) < 1:
        return pd.Series(dtype=float)
    ma = last.rolling(window=window, min_periods=1).mean()
    last_ma = ma.iloc[-1]
    # produce forecasted index
    freq = series.index.freq or pd.tseries.frequencies.to_offset('M')
    start = series.index[-1] + freq
    idx = pd.date_range(start=start, periods=periods, freq=freq)
    forecasts = pd.Series([last_ma]*periods, index=idx)
    return forecasts

# Reorder alerts
def reorder_alerts(df):
    df = df.copy()
    alerts = df[df['stock_available'] <= df['reorder_level']]
    return alerts[['product_id','product_name','region','stock_available','reorder_level','supplier_name']]

# Revenue summary
def revenue_summary(df):
    total_revenue = df['sales_revenue'].sum()
    revenue_by_category = df.groupby('category')['sales_revenue'].sum().sort_values(ascending=False)
    return {'total_revenue': total_revenue, 'by_category': revenue_by_category}

# ------------------- Chart Functions -------------------
def generate_charts(df, charts_dir="charts"):
    os.makedirs(charts_dir, exist_ok=True)
    chart_paths = {}

    # Ensure date is datetime
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # 1. Monthly Sales Trend (Units)
    monthly = df.set_index('date').resample('M').sum()
    if 'units_sold' in monthly.columns:
        plt.figure()
        monthly['units_sold'].plot()
        plt.title("Monthly Units Sold")
        plt.xlabel("Month")
        plt.ylabel("Units Sold")
        p = os.path.join(charts_dir, "monthly_units_sold.png")
        plt.tight_layout()
        plt.savefig(p)
        plt.close()
        chart_paths['monthly_units_sold'] = p

    # 2. Top Products by Revenue (Bar)
    top_products = df.groupby('product_name')['sales_revenue'].sum().sort_values(ascending=False).head(10)
    if not top_products.empty:
        plt.figure()
        top_products.plot(kind='bar')
        plt.title("Top 10 Products by Revenue")
        plt.ylabel("Sales Revenue")
        plt.xticks(rotation=45, ha='right')
        p = os.path.join(charts_dir, "top_products_revenue.png")
        plt.tight_layout()
        plt.savefig(p)
        plt.close()
        chart_paths['top_products_revenue'] = p

    # 3. Region Sales (Bar)
    region_sales = df.groupby('region')['sales_revenue'].sum().sort_values(ascending=False)
    if not region_sales.empty:
        plt.figure(figsize=(10,5))
        region_sales.plot(kind='bar')
        plt.title("Sales by Region (Cities in Maharashtra)")
        plt.ylabel("Sales Revenue")
        plt.xticks(rotation=45, ha='right')
        p = os.path.join(charts_dir, "region_sales.png")
        plt.tight_layout()
        plt.savefig(p)
        plt.close()
        chart_paths['region_sales'] = p

    # 4. Stock Levels (Bar for lowest stock)
    low_stock = df.groupby('product_name')['stock_available'].min().sort_values().head(20)
    if not low_stock.empty:
        plt.figure(figsize=(10,5))
        low_stock.plot(kind='bar')
        plt.title("Lowest Stock by Product (min across regions)")
        plt.ylabel("Stock Available")
        plt.xticks(rotation=45, ha='right')
        p = os.path.join(charts_dir, "low_stock_products.png")
        plt.tight_layout()
        plt.savefig(p)
        plt.close()
        chart_paths['low_stock_products'] = p

    # 5. Reorder Alerts (Pie: % of products needing reorder)
    alerts = reorder_alerts(df)
    total_products = df['product_id'].nunique()
    if total_products > 0:
        counts = [len(alerts), total_products - len(alerts)]
        labels = ['Need Reorder', 'OK']
        plt.figure()
        plt.pie(counts, labels=labels, autopct='%1.1f%%')
        plt.title("Reorder Status")
        p = os.path.join(charts_dir, "reorder_status.png")
        plt.tight_layout()
        plt.savefig(p)
        plt.close()
        chart_paths['reorder_status'] = p

    return chart_paths

# ------------------- Export -------------------
def export_cleaned_data(df, file_name="hospital_cleaned_data.xlsx"):
    df.to_excel(file_name, index=False)
    return file_name

def export_alerts(alerts_df, file_name="reorder_alerts.xlsx"):
    alerts_df.to_excel(file_name, index=False)
    return file_name

# ------------------- Utilities -------------------
def prepare_dataframe_for_app(df):
    df = rename_columns(df)
    # ensure numeric columns exist and correct types
    for col in ['units_sold','sales_revenue','stock_available','reorder_level','cost_price','selling_price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # ensure date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df
