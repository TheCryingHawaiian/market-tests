import yfinance as yf

df = yf.download("AAPL", period="60d", interval="5m")

# Extract the 'Close' column safely as a simple 1D series
close_data = df['Close']
close_data.to_csv("aapl_5m.csv", header=["Close"])
print("Clean CSV created.")