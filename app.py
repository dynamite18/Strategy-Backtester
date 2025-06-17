import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Sidebar for inputs
st.sidebar.header("Trading Strategy Settings")
ticker = st.sidebar.text_input("Stock Symbol (e.g. RELIANCE.NS)", value="RELIANCE.NS")
interval = st.sidebar.selectbox("Interval", ["5m", "15m"], index=1)
period = st.sidebar.selectbox("Period", ["5d", "30d", "60d", "90d"], index=2)
target_pct = st.sidebar.number_input("Target Profit (%)", value=3.95)
stop_pct = st.sidebar.number_input("Stop Loss (%)", value=0.8)

st.title("📈 EMA Crossover Trading Strategy")

# Download and prepare data
data = yf.download(ticker, interval=interval, period=period)
data.dropna(inplace=True)
data.index = data.index.tz_convert('Asia/Kolkata')

# Calculate EMAs
data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
data['EMA21'] = data['Close'].ewm(span=21, adjust=False).mean()

# Buy Signal
data['Buy'] = (data['EMA9'] > data['EMA21']) & (data['EMA9'].shift(1) <= data['EMA21'].shift(1))

# Trade simulation
trades = []
in_trade = False

for i in range(1, len(data)):
    row = data.iloc[i]
    if not in_trade and row['Buy'].item():
        entry_price = row['Close'].item()
        entry_time = data.index[i]
        target_price = entry_price * (1 + target_pct / 100)
        stop_price = entry_price * (1 - stop_pct / 100)
        in_trade = True
    elif in_trade:
        high = row['High'].item()
        low = row['Low'].item()
        if high >= target_price:
            trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': target_price,
                'Profit': round(target_price - entry_price, 2)
            })
            in_trade = False
        elif low <= stop_price:
            trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': stop_price,
                'Profit': round(stop_price - entry_price, 2)
            })
            in_trade = False

# Show results
df_trades = pd.DataFrame(trades)
if not df_trades.empty:
    df_trades['Entry Time'] = pd.to_datetime(df_trades['Entry Time']).dt.tz_convert('Asia/Kolkata')
    df_trades['Exit Time'] = pd.to_datetime(df_trades['Exit Time']).dt.tz_convert('Asia/Kolkata')

    st.success("✅ Trades Executed")
    st.dataframe(df_trades)

    st.write(f"📊 Total Trades: {len(df_trades)}")
    st.write(f"💰 Total Profit: ₹{df_trades['Profit'].sum():.2f}")

    df_trades['Cumulative'] = df_trades['Profit'].cumsum()
    fig, ax = plt.subplots()
    df_trades.set_index('Exit Time')['Cumulative'].plot(ax=ax, title="Cumulative Profit")
    ax.set_ylabel("₹ Profit")
    ax.set_xlabel("Exit Time")
    ax.grid(True)
    st.pyplot(fig)
else:
    st.warning("⚠️ No trades executed based on the EMA crossover strategy.")
