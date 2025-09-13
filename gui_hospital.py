# gui_hospital.py
import streamlit as st
import pandas as pd
from main_hospital import (
    load_data, prepare_dataframe_for_app, check_missing_values, fill_missing_values,
    drop_missing_values, remove_duplicates, rename_columns,
    top_n_products_by_revenue, top_n_regions_by_revenue, monthly_sales,
    product_monthly_series, moving_average_forecast, reorder_alerts,
    revenue_summary, generate_charts, export_cleaned_data, export_alerts
)

def main():
    st.set_page_config(page_title="Hospital Management System", layout="wide")
    st.title("🏥 Hospital Management System")
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Data Cleaning & Analysis",
        "Inventory & Reorder Alerts",
        "Sales & Forecasting",
        "View Charts",
        "Export"
    ])

    # Load data once
    if "df" not in st.session_state:
        try:
            df = load_data("Hospital_Management_Data.xlsx")
            df = prepare_dataframe_for_app(df)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    df = st.session_state.df

    if page == "Data Cleaning & Analysis":
        st.header("🧹 Data Cleaning & Analysis")
        st.subheader("1. Missing Values")
        st.write(check_missing_values(df))

        st.subheader("2. Cleaning")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fill missing with 0"):
                df = fill_missing_values(df)
                st.session_state.df = df
                st.success("Filled missing with 0.")
            if st.button("Drop missing rows"):
                df = drop_missing_values(df)
                st.session_state.df = df
                st.success("Dropped rows with missing values.")
        with col2:
            if st.button("Remove duplicates (product_id)"):
                df = remove_duplicates(df, subset=['product_id'])
                st.session_state.df = df
                st.success("Removed duplicates.")
            if st.button("Normalize columns"):
                df = rename_columns(df)
                st.session_state.df = df
                st.success("Normalized columns.")

        st.subheader("3. Quick Summaries")
        st.write("Top products by revenue:")
        st.write(top_n_products_by_revenue(df, n=10))
        st.write("Top regions by revenue:")
        st.write(top_n_regions_by_revenue(df, n=10))
        if st.checkbox("Show raw data (first 50)"):
            st.dataframe(df.head(50))

    elif page == "Inventory & Reorder Alerts":
        st.header("📦 Inventory & Reorder Alerts")
        alerts = reorder_alerts(df)
        st.write(f"Products needing reorder: {len(alerts)}")
        st.dataframe(alerts)
        if st.button("Export reorder alerts to Excel"):
            fname = export_alerts(alerts)
            st.success(f"Alerts exported to {fname}")

    elif page == "Sales & Forecasting":
        st.header("📈 Sales & Forecasting")
        st.write("Monthly sales overview:")
        ms = monthly_sales(df)
        st.line_chart(ms['units_sold'])

        st.subheader("Forecast units sold for a product (simple moving average)")
        product = st.selectbox("Select product name", options=sorted(df['product_name'].unique()))
        window = st.slider("MA window (months)", 1, 6, 3)
        periods = st.slider("Forecast months", 1, 6, 3)
        series = product_monthly_series(df, product)
        if series.empty:
            st.warning("No time series data for this product.")
        else:
            st.write("Historical (last 24 months):")
            st.line_chart(series.tail(24))
            forecast = moving_average_forecast(series, window=window, periods=periods)
            st.write("Forecast:")
            st.line_chart(pd.concat([series.tail(24), forecast]))

    elif page == "View Charts":
        st.header("📊 Charts")
        if st.button("Generate charts"):
            charts = generate_charts(df)
            st.success("Charts generated.")
            for name, path in charts.items():
                st.image(path, caption=name, use_column_width=True)

    elif page == "Export":
        st.header("💾 Export")
        if st.button("Export cleaned data"):
            fname = export_cleaned_data(df)
            st.success(f"Exported cleaned data to {fname}")

if __name__ == "__main__":
    main()
