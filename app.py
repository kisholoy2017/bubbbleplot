import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
from io import BytesIO

st.set_page_config(page_title="Marketing Performance Analyzer", layout="wide", page_icon="📊")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 1rem;}
    .sub-header {font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem;}
    .metric-box {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
    .quadrant-header {font-size: 1.5rem; font-weight: bold; margin-top: 1rem;}
    .brand-item {padding: 0.3rem; margin: 0.2rem 0; background-color: #ffffff; border-left: 3px solid #1f77b4;}
</style>
""", unsafe_allow_html=True)

# Helper functions
def to_percent_float(s):
    if pd.isna(s):
        return np.nan
    if isinstance(s, (int, float)):
        return float(s)*100 if s <= 1 else float(s)
    s = str(s).replace('%', '').replace(',', '.').strip()
    if s == '':
        return np.nan
    val = float(s)
    return val if val > 1 else val*100

def to_currency_number(x):
    if pd.isna(x):
        return np.nan
    s = str(x)
    s_clean = re.sub(r"[^\d,.\-]", "", s)
    if "," in s_clean and "." in s_clean:
        s_clean = s_clean.replace(",", "")
    else:
        if "," in s_clean and s_clean.count(",") >= 1 and s_clean.count(",") <= 3:
            s_clean = s_clean.replace(",", "")
    try:
        return float(s_clean)
    except:
        return np.nan

def create_bubble_chart(df, COL_X, COL_Y, COL_POAS, COL_LABEL, COL_ABS_SPEND, currency_symbol):
    FIG_WIDTH = 1800
    FIG_HEIGHT = 1400
    MAX_BUBBLE_PX = 100
    
    sizeref = 2.0 * df[COL_ABS_SPEND].max() / (MAX_BUBBLE_PX ** 2)
    
    poas_clipped = df[COL_POAS].clip(lower=1.0, upper=3.0)
    
    colorscale = [
        [0.0, "#d73027"],
        [0.1, "#ffd34d"],
        [0.5, "#fff176"],
        [1.0, "#1a9850"]
    ]
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
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
                colorscale=colorscale,
                cmin=1.0,
                cmax=3.0
            ),
            customdata=np.column_stack((df[COL_POAS], df[COL_ABS_SPEND])),
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"{COL_X}: %{{x:.2f}}%<br>"
                + f"{COL_Y}: %{{y:.2f}}%<br>"
                + "POAS: %{customdata[0]:.2f}<br>"
                + f"{COL_ABS_SPEND}: {currency_symbol}%{{customdata[1]:,.0f}}<extra></extra>"
            )
        )
    )
    
    fig.update_layout(
        title=dict(
            text="Bubble Chart: % of Ad Spend vs % of Revenue<br>"
                 "<sub>(Bubble SIZE = Absolute Ad Spend, COLOR = POAS)</sub>",
            font=dict(size=24)
        ),
        xaxis_title="% of Ad Spend",
        yaxis_title="% of Revenue",
        width=FIG_WIDTH,
        height=FIG_HEIGHT,
        plot_bgcolor="white",
        margin=dict(l=80, r=60, t=120, b=80)
    )
    fig.update_xaxes(showgrid=True, gridcolor="lightgray", zeroline=False, 
                     tickfont=dict(size=20), title_font=dict(size=28))
    fig.update_yaxes(showgrid=True, gridcolor="lightgray", zeroline=False,
                     tickfont=dict(size=20), title_font=dict(size=28))
    
    return fig

# Main app
st.markdown('<div class="main-header">📊 Marketing Performance Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Bubble Chart & Quadrant Analysis</div>', unsafe_allow_html=True)

# File upload
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['xlsx', 'xls', 'csv'])

if uploaded_file is not None:
    # Load data
    if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    df.columns = [c.strip() for c in df.columns]
    
    # Column selection
    st.sidebar.header("📋 Column Mapping")
    all_cols = list(df.columns)
    
    COL_X = st.sidebar.selectbox("% of Adspend Column", all_cols, 
                                  index=all_cols.index("% of Adspend") if "% of Adspend" in all_cols else 0)
    COL_Y = st.sidebar.selectbox("% of Revenue Column", all_cols,
                                  index=all_cols.index("% Of Revenue") if "% Of Revenue" in all_cols else 0)
    COL_POAS = st.sidebar.selectbox("POAS Column", all_cols,
                                     index=all_cols.index("POAS") if "POAS" in all_cols else 0)
    COL_LABEL = st.sidebar.selectbox("Brand/Label Column", all_cols,
                                      index=all_cols.index("Brand") if "Brand" in all_cols else 0)
    
    # Find absolute spend column
    CANDIDATE_ABS = "€ Ads Spend"
    if CANDIDATE_ABS in df.columns:
        COL_ABS_SPEND = CANDIDATE_ABS
    else:
        lower_cols = {c.lower(): c for c in df.columns}
        candidates = [
            orig for low, orig in lower_cols.items()
            if ("ads" in low or "ad " in low or "advert" in low)
            and ("spend" in low or "cost" in low or "expense" in low)
            and "%" not in orig and "percent" not in low
        ]
        COL_ABS_SPEND = candidates[0] if candidates else all_cols[0]
    
    COL_ABS_SPEND = st.sidebar.selectbox("Absolute Ad Spend Column", all_cols,
                                          index=all_cols.index(COL_ABS_SPEND) if COL_ABS_SPEND in all_cols else 0)
    
    # Process data
    df[COL_X] = df[COL_X].apply(to_percent_float)
    df[COL_Y] = df[COL_Y].apply(to_percent_float)
    df[COL_ABS_SPEND] = df[COL_ABS_SPEND].apply(to_currency_number)
    df[COL_POAS] = pd.to_numeric(df[COL_POAS], errors='coerce')
    
    df = df.dropna(subset=[COL_X, COL_Y, COL_ABS_SPEND, COL_POAS, COL_LABEL]).copy()
    
    currency_symbol = "€" if "€" in COL_ABS_SPEND or "eur" in COL_ABS_SPEND.lower() else "$"
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Bubble Chart", "🎯 Quadrant Analysis", "📊 Data Table"])
    
    with tab1:
        st.subheader("Interactive Bubble Chart")
        fig = create_bubble_chart(df, COL_X, COL_Y, COL_POAS, COL_LABEL, COL_ABS_SPEND, currency_symbol)
        st.plotly_chart(fig, use_container_width=True)
        
        # Download chart
        buffer = BytesIO()
        fig.write_html(buffer)
        st.download_button(
            label="📥 Download Interactive Chart (HTML)",
            data=buffer.getvalue(),
            file_name="bubble_chart_interactive.html",
            mime="text/html"
        )
    
    with tab2:
        st.subheader("Quadrant Analysis")
        
        # Calculate medians
        median_x = df[COL_X].median()
        median_y = df[COL_Y].median()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Brands", len(df))
        with col2:
            st.metric("Total Spend", f"{currency_symbol}{df[COL_ABS_SPEND].sum():,.0f}")
        with col3:
            st.metric("Average POAS", f"{df[COL_POAS].mean():.2f}")
        
        st.markdown("---")
        
        # Assign quadrants
        def assign_quadrant(row):
            if row[COL_X] >= median_x and row[COL_Y] >= median_y:
                return "Q1: CASH COWS"
            elif row[COL_X] < median_x and row[COL_Y] >= median_y:
                return "Q2: STARS ⭐"
            elif row[COL_X] < median_x and row[COL_Y] < median_y:
                return "Q3: TEST & LEARN"
            else:
                return "Q4: URGENT ACTION ⚠️"
        
        df['Quadrant'] = df.apply(assign_quadrant, axis=1)
        df['Efficiency_Score'] = df[COL_Y] / df[COL_X]
        
        quadrant_info = {
            "Q2: STARS ⭐": {
                "description": "Low Spend, High Revenue - Most Efficient",
                "urgency": "🟢 SCALE UP",
                "action": "Increase investment immediately - huge opportunity!",
                "color": "#1a9850"
            },
            "Q1: CASH COWS": {
                "description": "High Spend, High Revenue - Core Performers",
                "urgency": "🟢 MAINTAIN",
                "action": "Keep investing, these are your backbone brands",
                "color": "#4575b4"
            },
            "Q4: URGENT ACTION ⚠️": {
                "description": "High Spend, Low Revenue - Underperformers",
                "urgency": "🔴 OPTIMIZE/CUT",
                "action": "Immediate review needed - optimize or reduce spend",
                "color": "#d73027"
            },
            "Q3: TEST & LEARN": {
                "description": "Low Spend, Low Revenue - Minor Players",
                "urgency": "🟡 MONITOR",
                "action": "Keep testing, decide to scale or cut based on trends",
                "color": "#fee08b"
            }
        }
        
        # Display quadrants
        for q in ["Q2: STARS ⭐", "Q1: CASH COWS", "Q4: URGENT ACTION ⚠️", "Q3: TEST & LEARN"]:
            q_data = df[df['Quadrant'] == q]
            
            if len(q_data) == 0:
                continue
            
            info = quadrant_info[q]
            
            with st.expander(f"{q} - {len(q_data)} Brands ({len(q_data)/len(df)*100:.1f}%)", expanded=True):
                st.markdown(f"**{info['description']}**")
                st.markdown(f"**Urgency:** {info['urgency']}")
                st.markdown(f"**Action:** {info['action']}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Spend", f"{currency_symbol}{q_data[COL_ABS_SPEND].sum():,.0f}")
                with col2:
                    st.metric("% of Ad Spend", f"{q_data[COL_X].sum():.1f}%")
                with col3:
                    st.metric("% of Revenue", f"{q_data[COL_Y].sum():.1f}%")
                with col4:
                    st.metric("Avg POAS", f"{q_data[COL_POAS].mean():.2f}")
                
                st.markdown("**Brands:**")
                q_data_sorted = q_data.sort_values(COL_ABS_SPEND, ascending=False)
                
                for idx, row in q_data_sorted.iterrows():
                    st.markdown(
                        f"**{row[COL_LABEL]}** | "
                        f"Spend: {currency_symbol}{row[COL_ABS_SPEND]:,.0f} | "
                        f"POAS: {row[COL_POAS]:.2f} | "
                        f"Ad%: {row[COL_X]:.1f}% | "
                        f"Rev%: {row[COL_Y]:.1f}%"
                    )
        
        st.markdown("---")
        st.subheader("🏆 Top & Bottom Performers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 3 Most Efficient Brands**")
            top_efficient = df.nlargest(3, 'Efficiency_Score')
            for idx, row in top_efficient.iterrows():
                st.success(f"**{row[COL_LABEL]}** | Efficiency: {row['Efficiency_Score']:.2f}x | POAS: {row[COL_POAS]:.2f}")
        
        with col2:
            st.markdown("**Bottom 3 Least Efficient Brands**")
            bottom_efficient = df.nsmallest(3, 'Efficiency_Score')
            for idx, row in bottom_efficient.iterrows():
                st.error(f"**{row[COL_LABEL]}** | Efficiency: {row['Efficiency_Score']:.2f}x | POAS: {row[COL_POAS]:.2f}")
        
        # Download analysis
        analysis_export = df[[COL_LABEL, COL_X, COL_Y, COL_ABS_SPEND, COL_POAS, 'Quadrant', 'Efficiency_Score']].copy()
        analysis_export = analysis_export.sort_values(['Quadrant', COL_ABS_SPEND], ascending=[True, False])
        
        csv = analysis_export.to_csv(index=False)
        st.download_button(
            label="📥 Download Quadrant Analysis (CSV)",
            data=csv,
            file_name="quadrant_analysis.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("Complete Data Table")
        st.dataframe(df, use_container_width=True)

else:
    st.info("👆 Please upload an Excel or CSV file to begin analysis")
    
    st.markdown("### Expected File Format:")
    st.markdown("""
    Your file should contain the following columns:
    - **Brand** (or similar): Brand names
    - **% of Adspend**: Percentage of total ad spend
    - **% Of Revenue**: Percentage of total revenue
    - **POAS**: Return on ad spend
    - **€ Ads Spend** (or similar): Absolute ad spend amount
    """)
