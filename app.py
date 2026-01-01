import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
from io import BytesIO

st.set_page_config(page_title="Marketing Performance Analyzer", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 1rem;}
    .sub-header {font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

def to_percent_float(s):
    if pd.isna(s): return np.nan
    if isinstance(s, (int, float)): return float(s)*100 if s <= 1 else float(s)
    s = str(s).replace('%', '').replace(',', '.').strip()
    if s == '': return np.nan
    val = float(s)
    return val if val > 1 else val*100

def to_currency_number(x):
    if pd.isna(x): return np.nan
    s = re.sub(r"[^\d,.\-]", "", str(x))
    if "," in s and "." in s: s = s.replace(",", "")
    elif "," in s: s = s.replace(",", "")
    try: return float(s)
    except: return np.nan

def create_bubble_chart(df, COL_X, COL_Y, COL_POAS, COL_LABEL, COL_ABS_SPEND, currency_symbol):
    sizeref = 2.0 * df[COL_ABS_SPEND].max() / (100 ** 2)
    poas_clipped = df[COL_POAS].clip(1.0, 3.0)
    
    fig = go.Figure(go.Scatter(
        x=df[COL_X],
        y=df[COL_Y],
        mode="markers+text",
        text=df[COL_LABEL],
        textposition="middle right",
        textfont=dict(size=14),
        marker=dict(
            size=df[COL_ABS_SPEND],
            sizemode="area",
            sizeref=sizeref,
            sizemin=4,
            line=dict(width=2, color="white"),
            opacity=0.8,
            color=poas_clipped,
            colorscale=[[0,"#d73027"],[0.1,"#ffd34d"],[0.5,"#fff176"],[1,"#1a9850"]],
            cmin=1.0,
            cmax=3.0
        ),
        customdata=np.column_stack((df[COL_POAS], df[COL_ABS_SPEND])),
        hovertemplate="<b>%{text}</b><br>Ad Spend %: %{x:.2f}%<br>Revenue %: %{y:.2f}%<br>POAS: %{customdata[0]:.2f}<br>Spend: " + currency_symbol + "%{customdata[1]:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Bubble Chart: % of Ad Spend vs % of Revenue<br><sub>(Bubble SIZE = Absolute Ad Spend, COLOR = POAS)</sub>",
        xaxis_title="% of Ad Spend",
        yaxis_title="% of Revenue",
        width=1800,
        height=1400,
        plot_bgcolor="white"
    )
    
    return fig

st.markdown('<div class="main-header">📊 Marketing Performance Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Bubble Chart & Quadrant Analysis</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    st.sidebar.header("📋 Column Mapping")
    all_cols = list(df.columns)
    
    COL_X = st.sidebar.selectbox("% of Adspend", all_cols, index=all_cols.index("% of Adspend") if "% of Adspend" in all_cols else 0)
    COL_Y = st.sidebar.selectbox("% of Revenue", all_cols, index=all_cols.index("% Of Revenue") if "% Of Revenue" in all_cols else 0)
    COL_POAS = st.sidebar.selectbox("POAS", all_cols, index=all_cols.index("POAS") if "POAS" in all_cols else 0)
    COL_LABEL = st.sidebar.selectbox("Brand", all_cols, index=all_cols.index("Brand") if "Brand" in all_cols else 0)
    
    spend_candidates = [c for c in all_cols if "spend" in c.lower() and "%" not in c]
    COL_ABS_SPEND = st.sidebar.selectbox("Ad Spend", all_cols, index=all_cols.index(spend_candidates[0]) if spend_candidates else 0)
    
    df[COL_X] = df[COL_X].apply(to_percent_float)
    df[COL_Y] = df[COL_Y].apply(to_percent_float)
    df[COL_ABS_SPEND] = df[COL_ABS_SPEND].apply(to_currency_number)
    df[COL_POAS] = pd.to_numeric(df[COL_POAS], errors='coerce')
    df = df.dropna(subset=[COL_X, COL_Y, COL_ABS_SPEND, COL_POAS, COL_LABEL])
    
    currency_symbol = "€" if "€" in COL_ABS_SPEND else "$"
    
    tab1, tab2, tab3 = st.tabs(["📈 Chart", "🎯 Quadrants", "📊 Data"])
    
    with tab1:
        fig = create_bubble_chart(df, COL_X, COL_Y, COL_POAS, COL_LABEL, COL_ABS_SPEND, currency_symbol)
        st.plotly_chart(fig, use_container_width=True)
        
        buffer = BytesIO()
        fig.write_html(buffer)
        st.download_button("📥 Download Chart (HTML)", buffer.getvalue(), "chart.html", "text/html")
    
    with tab2:
        median_x, median_y = df[COL_X].median(), df[COL_Y].median()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Brands", len(df))
        col2.metric("Total Spend", f"{currency_symbol}{df[COL_ABS_SPEND].sum():,.0f}")
        col3.metric("Avg POAS", f"{df[COL_POAS].mean():.2f}")
        
        def assign_quadrant(row):
            if row[COL_X] >= median_x and row[COL_Y] >= median_y: return "Q1: CASH COWS"
            elif row[COL_X] < median_x and row[COL_Y] >= median_y: return "Q2: STARS ⭐"
            elif row[COL_X] < median_x and row[COL_Y] < median_y: return "Q3: TEST & LEARN"
            else: return "Q4: URGENT ACTION ⚠️"
        
        df['Quadrant'] = df.apply(assign_quadrant, axis=1)
        df['Efficiency'] = df[COL_Y] / df[COL_X]
        
        for q in ["Q2: STARS ⭐", "Q1: CASH COWS", "Q4: URGENT ACTION ⚠️", "Q3: TEST & LEARN"]:
            qd = df[df['Quadrant'] == q]
            if len(qd) == 0: continue
            
            with st.expander(f"{q} - {len(qd)} Brands ({len(qd)/len(df)*100:.1f}%)", expanded=True):
                for _, row in qd.sort_values(COL_ABS_SPEND, ascending=False).iterrows():
                    st.write(f"**{row[COL_LABEL]}** | {currency_symbol}{row[COL_ABS_SPEND]:,.0f} | POAS: {row[COL_POAS]:.2f}")
        
        st.download_button("📥 Download Analysis (CSV)", df.to_csv(index=False), "analysis.csv", "text/csv")
    
    with tab3:
        st.dataframe(df, use_container_width=True)
else:
    st.info("👆 Upload an Excel or CSV file to begin")
