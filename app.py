"""
Indices Heatmap Visualizer

-- Dependencies to be installed --
pip install streamlit
pip install pandas
pip install matplotlib

Disclaimer:
The information provided is for educational and informational purposes only and
should not be construed as financial, investment, or legal advice. The content is based on publicly available
information and personal opinions and may not be suitable for all investors. Investing involves risks,
including the loss of principal.

Queries on feedback on the python screener can be sent to :
FabTrader (fabtraderinc@gmail.com)
www.fabtrader.in
YouTube: @fabtraderinc
X / Instagram / Telegram :  @Iamfabtrader
"""
from logging import exception
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import yfinance as yf


@st.cache_data(ttl=300)
def get_index_details(category):
    """
    Function that returns constituents and price change / mcap data for indices
    :param category: Index
    :return: Tuple containing (Dataframe, timestamp) with Price Change and Market Cap data for all index constituents
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'Upgrade-Insecure-Requests': "1",
        "DNT": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*,q=0.8",
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    category = category.upper().replace('&', '%26').replace(' ', '%20')

    try:
        ref_url = "https://www.nseindia.com/market-data/live-equity-market?symbol={category}"
        ref = requests.get(ref_url, headers=headers)
        url = f"https://www.nseindia.com/api/equity-stockIndices?index={category}"
        data = requests.get(url, headers=headers, cookies=ref.cookies.get_dict()).json()
        
        # Extract timestamp from API response
        api_timestamp = data.get('timestamp', None)
        
        df = pd.DataFrame(data['data'])
        if not df.empty:
            df = df.drop(["meta"], axis=1)
            df = df.set_index("symbol", drop=True)
            df['ffmc'] = round(df['ffmc']/10000000, 0)
            df = df.iloc[1:].reset_index(drop=False)
        return df, api_timestamp
    except Exception as e:
        print("Error Fetching Index Data from NSE. Aborting....")
        return pd.DataFrame(), None

@st.cache_data(ttl=300)
def get_stocks_below_ema(df, top_n=5):
    """
    Get stocks that are below their 20-day EMA and return top N stocks with highest drop percentage
    
    Args:
        df: DataFrame with stock symbols
        top_n: Number of top stocks to return (default 5)
    
    Returns:
        DataFrame with filtered stocks
    """
    if df.empty:
        return df
    
    stocks_below_ema = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=50)  # Get 50 days of data for 20-day EMA
    
    for _, row in df.iterrows():
        symbol = row['symbol']
        try:
            # Get historical data using yfinance
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 20:
                continue
            
            # Calculate 20-day EMA
            ema_20 = data['Close'].ewm(span=20, adjust=False).mean()
            current_price = data['Close'].iloc[-1]
            ema_value = ema_20.iloc[-1]
            
            # Check if stock is below EMA
            if current_price < ema_value:
                drop_percentage = ((ema_value - current_price) / ema_value) * 100
                stocks_below_ema.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'ema_20': ema_value,
                    'drop_percentage': drop_percentage,
                    'pChange': row['pChange'],
                    'ffmc': row['ffmc']
                })
                
        except Exception as e:
            # Skip stocks with errors
            continue
    
    if not stocks_below_ema:
        return pd.DataFrame()
    
    # Sort by drop percentage (highest drop first) and take top N
    stocks_below_ema.sort(key=lambda x: x['drop_percentage'], reverse=True)
    top_stocks = stocks_below_ema[:top_n]
    
    return pd.DataFrame(top_stocks)

# Include any additional NSE indices to list below
index_list = ['NIFTY 50', 'NIFTY NEXT 50', 'NIFTY MIDCAP 50', 'NIFTY MIDCAP 100', 'NIFTY MIDCAP 150',
                      'NIFTY SMALLCAP 50',
                      'NIFTY SMALLCAP 100', 'NIFTY SMALLCAP 250', 'NIFTY MIDSMALLCAP 400', 'NIFTY 100', 'NIFTY 200',
                      'NIFTY AUTO',
                      'NIFTY BANK', 'NIFTY ENERGY', 'NIFTY FINANCIAL SERVICES', 'NIFTY FINANCIAL SERVICES 25/50',
                      'NIFTY FMCG',
                      'NIFTY IT', 'NIFTY MEDIA', 'NIFTY METAL', 'NIFTY PHARMA', 'NIFTY PSU BANK', 'NIFTY REALTY',
                      'NIFTY PRIVATE BANK', 'Securities in F&O', 'Permitted to Trade',
                      'NIFTY DIVIDEND OPPORTUNITIES 50',
                      'NIFTY50 VALUE 20', 'NIFTY100 QUALITY 30', 'NIFTY50 EQUAL WEIGHT', 'NIFTY100 EQUAL WEIGHT',
                      'NIFTY100 LOW VOLATILITY 30', 'NIFTY ALPHA 50', 'NIFTY200 QUALITY 30',
                      'NIFTY ALPHA LOW-VOLATILITY 30',
                      'NIFTY200 MOMENTUM 30', 'NIFTY COMMODITIES', 'NIFTY INDIA CONSUMPTION', 'NIFTY CPSE',
                      'NIFTY INFRASTRUCTURE',
                      'NIFTY MNC', 'NIFTY GROWTH SECTORS 15', 'NIFTY PSE', 'NIFTY SERVICES SECTOR',
                      'NIFTY100 LIQUID 15',
                      'NIFTY MIDCAP LIQUID 15']


pd.set_option("display.max_rows", None, "display.max_columns", None)

# Set initial page configuration for app
st.set_page_config(
    page_title='Index Heat Map by Arjun Dagar',
    layout="centered")

# Apply fixed screen width for app (1440px)
st.markdown(
    f"""
    <style>
      .stAppViewContainer .stMain .stMainBlockContainer{{ max-width: 1440px; }}
    </style>    
  """,
    unsafe_allow_html=True,
)

# Streamlit App


header1, header2 = st.columns([3,1])
with header1:
# with st.container():
    st.image("https://i.ibb.co/vCC17YHZ/Whats-App-Image-2025-08-02-at-09-31-19-removebg-preview.png", width=100)
    st.subheader("NSE Indices Heatmap - Visualizer")
    col1, col2, _ = st.columns([2,1,1])
    index_filter = col1.selectbox("Choose Index", index_list, index=0)
    slice_by = col2.selectbox("Slice By", ["Market Cap","Gainers","Losers","Top 5 below 20 EMA"], index=0)

with header2:
    df, api_timestamp = get_index_details(index_filter)
    advances = df[df['pChange'] > 0].shape[0]
    declines = df[df['pChange'] < 0].shape[0]
    no_change = df[df['pChange'] == 0].shape[0]
    total_count = advances + declines + no_change

    # Plot pie chart

    fig = px.pie(names=['Advances','Declines','No Change'],
                 values=[advances, declines, no_change],
                 color=['Advances','Declines','No Change'],
                 # color_discrete_sequence=['#2ecc71', '#e74c3c', '#95a5a6'])
                 color_discrete_sequence=['#3AA864', '#F38039', '#F2F2F2'])
    fig.update_traces(hole=0.7)
    fig.update_traces(textinfo='none')
    fig.update_layout(
        width=200,  # width in pixels
        height=200,  # height in pixels
        showlegend=False,
        annotations=[dict(
            text=f'{advances}<br>Advances<br>{declines}<br>Declines',  # Line break for style
            x=0.5, y=0.5, font_size=14, showarrow=False
        )]
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0)  # left, right, top, bottom
    )
    st.plotly_chart(fig)


# Display last updated timestamp
if not df.empty:
    if api_timestamp:
        # Use API timestamp if available
        st.markdown(f"**Market Data Last Updated:** {api_timestamp}")
    else:
        st.markdown(f"**Last Updated:** NA")
    st.markdown("---")

if not df.empty:

    if slice_by == 'Market Cap':
        slice_factor = 'ffmc'
        color_scale = ['#ff7a3a', 'white', 'green']
    elif slice_by == 'Gainers':
        slice_factor = 'pChange'
        color_scale = ['white', '#a5eb79']
    elif slice_by == 'Losers':
        df = df[df["pChange"] < 0]
        df['Abs'] = df['pChange'].abs()
        slice_factor = 'Abs'
        color_scale = ['#ff7a3a', 'white']
    elif slice_by == 'Top 5 below 20 EMA':
        # Get stocks below 20 EMA
        st.info("🔍 **Top 5 below 20 EMA**: Shows stocks trading below their 20-day Exponential Moving Average, sorted by the highest percentage drop from EMA.")
        with st.spinner('Calculating 20-day EMA for stocks... This may take a few moments.'):
            ema_df = get_stocks_below_ema(df, top_n=5)
        if not ema_df.empty:
            df = ema_df
            slice_factor = 'drop_percentage'
            color_scale = ['#ff7a3a', 'white']
        else:
            st.warning("No stocks found below their 20-day EMA")
            st.stop()

    # Plotly Treemap
    st.divider()
    
    # Prepare custom data based on filter type
    if slice_by == 'Top 5 below 20 EMA':
        custom_data = ['pChange', 'current_price', 'ema_20']
    else:
        custom_data = ['pChange']
    
    fig = px.treemap(
        df,
        path=['symbol'],
        values=slice_factor,
        color='pChange',
        color_continuous_scale=color_scale,
        custom_data=custom_data
    )
    fig.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        width=500,height=1000,
        paper_bgcolor="rgba(0, 0, 0, 0)", plot_bgcolor="rgba(0, 0, 0, 0)",
        )

    # Customize hover template and text template based on filter type
    if slice_by == 'Top 5 below 20 EMA':
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Drop from EMA: %{value:.2f}%<br>Current Price: ₹%{customdata[1]:.2f}<br>EMA: ₹%{customdata[2]:.2f}<br>pChange: %{customdata[0]:.2f}%',
            texttemplate='<b>%{label}</b><br>Drop from EMA: %{value:.1f}%<br>Current Price: ₹%{customdata[1]:.0f}<br>EMA: ₹%{customdata[2]:.0f}<br>Today pChange: %{customdata[0]:.2f}%',
            textfont=dict(size=16),
            textposition='middle center'
        )
    else:
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Size: %{value}<br>pChange: %{customdata[0]:.2f}%',
            texttemplate='%{label}<br>%{customdata[0]:.2f}%',
            textposition='middle center'
        )
    fig.update_traces(textinfo="label+value")
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Failed to fetch data.")
st.write("")
st.write(":gray[Made with :heart: by Arjun Dagar. ©2025 HungerLoggy Pvt Lmt - All Rights Reserved]")
