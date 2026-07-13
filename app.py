import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="AR Dashboard", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .kpi-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        color: #333333;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #E0E0E0;
    }
    .kpi-title { font-size: 16px; color: #666666; }
    .kpi-value { font-size: 30px; font-weight: bold; margin-top: 10px; color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    data_dir = "data"
    
    # 1. Load Mapping Data
    mapping_file = os.path.join(data_dir, "assign_ar_team.xlsx")
    if not os.path.exists(mapping_file):
        return pd.DataFrame()
    df_mapping = pd.read_excel(mapping_file)
    df_mapping['Valid_From'] = pd.to_datetime(df_mapping['Valid_From'])
    df_mapping['Valid_To'] = pd.to_datetime(df_mapping['Valid_To'])
    
    # 2. Load AR Data Files
    all_data = []
    
    for filename in os.listdir(data_dir):
        if filename.startswith("AR_DATA_MONTH_") and filename.endswith(".xlsx"):
            filepath = os.path.join(data_dir, filename)
            
            # Extract month and day using regex
            month_match = re.search(r"MONTH_(\d+)", filename)
            day_match = re.search(r"DAY_(\d+)", filename)
            
            if not month_match:
                continue
                
            m = int(month_match.group(1))
            
            # If day exists, use it. Otherwise assume end of month (approximate 28th for simplicity)
            if day_match:
                d = int(day_match.group(1))
            else:
                d = 28 
                
            report_date = pd.to_datetime(f"2026-{m:02d}-{d:02d}")
            
            # Read data
            df = pd.read_excel(filepath)
            
            # Clean numeric columns (handle '-   ' and string types)
            # Find the header glitch: '2026-07-13 00:00:00' should be '7 - 13'
            for col in df.columns:
                if isinstance(col, datetime):
                    df.rename(columns={col: "7 - 13"}, inplace=True)
            
            cols_to_clean = ['0 - 6', '7 - 13', '14 - 20', '21 - 29', '30 - 37', '38 - 45', '45 UP', '60 UP', 'Bal Due', 'Total Amt', 'CR Limit']
            for c in cols_to_clean:
                if c in df.columns:
                    df[c] = df[c].replace(r'^\s*-\s*$', 0, regex=True)
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df['Report_Date'] = report_date
            df['Report_Month'] = report_date.strftime("%Y-%m")
            
            all_data.append(df)
            
    if not all_data:
        return pd.DataFrame()
        
    df_all = pd.concat(all_data, ignore_index=True)
    
    # 3. Apply SCD Type 2 Mapping
    df_merged = pd.merge(df_all, df_mapping, how="left", left_on="Sales Person Code", right_on="sales_person_code")
    
    # Filter valid dates OR keep unmapped sales persons (Valid_From is NaT)
    mask_mapped = (df_merged['Report_Date'] >= df_merged['Valid_From']) & (df_merged['Report_Date'] <= df_merged['Valid_To'])
    mask_unmapped = df_merged['Valid_From'].isna()
    df_merged = df_merged[mask_mapped | mask_unmapped]
    
    # Fill missing AR persons just in case
    df_merged['ar_person'] = df_merged['ar_person'].fillna("Unassigned")
    
    return df_merged

# --- MAIN APP ---
def main():
    st.title("C-Level AR Dashboard")
    
    df = load_data()
    
    if df.empty:
        st.error("No data found. Please check the 'data/' directory.")
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filters")
    
    # Automatically use the latest Report Date for the current snapshot (no UI filter needed)
    latest_date = df['Report_Date'].max()
    df_month = df[df['Report_Date'] == latest_date]
    
    st.sidebar.markdown(f"**Current Report Date:** {latest_date.strftime('%Y-%m-%d')}")
    
    # AR Person Filter
    ar_persons = ["All"] + sorted(df_month['ar_person'].unique().tolist())
    selected_ar = st.sidebar.selectbox("AR Person", ar_persons)
    if selected_ar != "All":
        df_month = df_month[df_month['ar_person'] == selected_ar]
        
    # Sales Person Filter
    sales_persons = ["All"] + sorted(df_month['Sales Person Code'].unique().tolist())
    selected_sales = st.sidebar.selectbox("Sales Person", sales_persons)
    if selected_sales != "All":
        df_month = df_month[df_month['Sales Person Code'] == selected_sales]
        
    # Customer Filter
    customers = ["All"] + sorted(df_month['Name'].unique().tolist())
    selected_cust = st.sidebar.selectbox("Customer", customers)
    if selected_cust != "All":
        df_month = df_month[df_month['Name'] == selected_cust]

    # --- KPI CARDS ---
    total_ar = df_month['Bal Due'].sum()
    total_overdue = df_month['Total Amt'].sum()
    percent_overdue = (total_overdue / total_ar * 100) if total_ar > 0 else 0
    total_customers = df_month['Cust #'].nunique()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-title">Total AR Amount</div><div class="kpi-value">${total_ar:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Balance Overdue</div><div class="kpi-value">${total_overdue:,.0f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-title">% Overdue</div><div class="kpi-value">{percent_overdue:.1f}%</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Customers</div><div class="kpi-value">{total_customers:,}</div></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # --- TREND CHARTS (EDIT INTERACTIONS: Ignore Date Filter) ---
    st.subheader("Trend Analysis (Historical Snapshot Data)")
    st.caption("This chart retains the full history for the selected filters, ignoring the Report Date slicer.")
    
    # Create a dataframe for trends that ignores the Date filter, but respects AR/Sales/Customer filters
    df_trend = df.copy()
    if selected_ar != "All": df_trend = df_trend[df_trend['ar_person'] == selected_ar]
    if selected_sales != "All": df_trend = df_trend[df_trend['Sales Person Code'] == selected_sales]
    if selected_cust != "All": df_trend = df_trend[df_trend['Name'] == selected_cust]
    
    # Format Date as string for categorical x-axis
    df_trend['Date_Str'] = df_trend['Report_Date'].dt.strftime("%Y-%m-%d")
    
    # --- COMPARISON CHART ---
    cols_7up = ['7 - 13', '14 - 20', '21 - 29', '30 - 37', '38 - 45', '45 UP', '60 UP']
    df_trend['7UP_Sum'] = df_trend[cols_7up].sum(axis=1)
    
    comp_trend = df_trend.groupby('Date_Str').apply(
        lambda x: pd.Series({
            'Total Overdue Accounts': x[x['Total Amt'] > 0]['Cust #'].nunique(),
            'Overdue 7 UP Accounts': x[x['7UP_Sum'] > 0]['Cust #'].nunique()
        })
    ).reset_index()

    comp_trend_melted = comp_trend.melt(id_vars='Date_Str', var_name='Category', value_name='Customers')

    fig_comp = px.bar(
        comp_trend_melted, 
        x='Date_Str', 
        y='Customers',
        color='Category',
        barmode='group',
        text_auto='.0f',
        title="Comparison: Overdue 7UP vs Total Overdue Accounts",
        color_discrete_sequence=['#4C72B0', '#DD8452']
    )
    fig_comp.update_layout(xaxis_type='category', xaxis_title="", yaxis_title="No. of Customers", legend_title_text="")
    st.plotly_chart(fig_comp, use_container_width=True)
    
    st.write("---")
    
    # Group by date
    trend_group = df_trend.groupby('Date_Str')[cols_7up + ['0 - 6', 'Total Amt']].sum().reset_index()
    
    # Plotly Trend Charts
    cols = st.columns(2)
    
    buckets_to_plot = ['Total Amt', '60 UP', '45 UP', '38 - 45', '30 - 37', '21 - 29', '14 - 20', '7 - 13', '0 - 6']
    
    for i, b in enumerate(buckets_to_plot):
        fig = px.bar(trend_group, x='Date_Str', y=b, title=f"Trend: {b}", text_auto='.2s')
        fig.update_layout(xaxis_type='category', xaxis_title="", yaxis_title="Amount")
        cols[i % 2].plotly_chart(fig, use_container_width=True)

    st.write("---")
    st.subheader("Detailed Data Table")
    st.dataframe(df_month[['Cust #', 'Name', 'ar_person', 'Sales Person Code', 'Bal Due', 'Total Amt'] + cols_7up], use_container_width=True)

if __name__ == "__main__":
    main()
