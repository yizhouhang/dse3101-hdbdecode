import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import os

def hdb_price_trend(t):
    st.title(t["price1"])

    # Load Data
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(BASE_DIR, "resale_price_cleaned.csv")

    df = pd.read_csv(data_path)
    df = df.dropna(subset=['resale_price', 'month'])
    df['month'] = pd.to_datetime(df['month'])

    # Create price category
    conditions = [
        (df['resale_price'] < 300000),
        (df['resale_price'] >= 300000) & (df['resale_price'] < 500000),
        (df['resale_price'] >= 500000) & (df['resale_price'] < 700000),
        (df['resale_price'] >= 700000) & (df['resale_price'] < 1000000),
        (df['resale_price'] >= 1000000)
    ]
    categories = ['<300k', '300k-500k', '500k-700k', '700k-1M', '>=1M']
    df['Price Category'] = np.select(conditions, categories, default='Unknown')

    category_counts = df.groupby(['month', 'Price Category']).size().unstack(fill_value=0)
    category_counts = category_counts[['<300k', '300k-500k', '500k-700k', '700k-1M', '>=1M']]
    category_counts.index = pd.to_datetime(category_counts.index)

    # Plot stacked bar chart
    st.subheader(t["price2"])
    fig, ax = plt.subplots(figsize=(12, 6))
    category_counts.plot(kind='bar', stacked=True, colormap='viridis', width=0.8, ax=ax)
    ax.set_title("Resale Transactions by Price Category")
    ax.set_ylabel("Transaction Count")
    ax.set_xlabel("")
    ax.set_xticks(range(0, len(category_counts.index), 3))
    years = category_counts.index.year.unique()
    xticks = [category_counts.index.get_loc(f"{year}-01-01") for year in years if f"{year}-01-01" in category_counts.index.strftime('%Y-%m-%d').values]
    ax.set_xticks(xticks)
    ax.set_xticklabels(years, rotation=0, fontsize=10)
    ax.legend(title="Price Category")
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(fig)

    # Key trends
    st.subheader(t["price3"])
    st.markdown(
        f"""
        - {t['price4']}
        - {t['price5']}
        - {t['price6']}
        - {t['price7']}
        - {t['price8']}
        """
    )

    # Trend over time
    st.subheader(t["price9"])
    st.warning(t["price10"])

    bins = [40, 50, 60, 70, 80, 90, 100]
    labels = ["40-50", "50-60", "60-70", "70-80", "80-90", "90-99"]
    df["lease_range"] = pd.cut(df["remaining_lease"], bins=bins, labels=labels, right=False)

    towns = sorted(df['town'].unique().tolist())
    room_types = sorted(df['flat_type'].unique().tolist())
    lease_ranges = sorted(df['lease_range'].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_town = st.selectbox(t["price11"], ["All"] + towns)
    with col2:
        selected_room = st.selectbox(t["price12"], ["All"] + room_types)
    with col3:
        selected_lease = st.selectbox(t["price13"], ["All"] + lease_ranges)

    if selected_town != "All":
        df = df[df["town"] == selected_town]
    if selected_room != "All":
        df = df[df["flat_type"] == selected_room]
    if selected_lease != "All":
        df = df[df["lease_range"] == selected_lease]

    trend_data = df.groupby('month')['resale_price'].mean().reset_index()
    fig = px.line(trend_data, x='month', y='resale_price',
                  labels={'month': '', 'resale_price': 'Average Resale Price'},
                  markers=True)
    fig.update_traces(mode="lines+markers", hovertemplate="%{x}: $%{y:.2f}")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown(t["contact"])
