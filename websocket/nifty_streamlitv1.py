import streamlit as st
import matplotlib.pyplot as plt
from fyers_apiv3.FyersWebsocket import data_ws
from datetime import datetime
import threading, requests, time
from collections import deque
import pandas as pd
from matplotlib.patches import Rectangle

# ---------------------- CONFIG ----------------------
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcFF0blFtT0xkM1JxOWJmWDZNUUpkRW82dElpcHduRmhuWWQ5WjAtcmZ0bEJzTTZiUHdadVV0bzl3N2E2dm9rRlR4Vk1NenJGVGNZUjluUjkzT0Y1STVXQWJkSVdtMDVocXlvemtidGZWRGxRQ1ZIMD0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI1ZDc5ZjMzMDk4NzVjYzhlOGRhMDJlMjVhMTk3Y2QzMmJmMDlmN2UzNGMyNDNhZjI2ZWJmYmZmZiIsImlzRGRwaUVuYWJsZWQiOiJZIiwiaXNNdGZFbmFibGVkIjoiWSIsImZ5X2lkIjoiWFIyMDMyNiIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzY2MDE3ODAwLCJpYXQiOjE3NjU5ODg4MTYsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2NTk4ODgxNiwic3ViIjoiYWNjZXNzX3Rva2VuIn0.ulT7x32j04BdAuyF90xC_lVUs-zAtYaTcHDYe76IGkE'
OI_API_URL = "https://api-t1.fyers.in/data/options-chain-v3?symbol=NSE:NIFTY50-INDEX&strikecount=10"
OI_POLL_INTERVAL = 60
# ----------------------------------------------------

# Streamlit UI Setup
st.set_page_config(page_title="Nifty Live OI Chart", layout="wide")
st.title("📈 Nifty 50 - Live Candlestick Chart with OI Overlay")

chart_placeholder = st.empty()

# ---------------------- Chart Class ----------------------
class FyersCandleChart:
    def __init__(self, candle_interval=60, max_candles=60):
        self.candle_interval = candle_interval
        self.max_candles = max_candles
        self.candles = deque(maxlen=max_candles)
        self.current_candle = None
        self.candle_start_time = None
        self.oi_data = {}
        self.prev_oi_data = None
        self.lock = threading.Lock()

    def update_data(self, data):
        try:
            with self.lock:
                ltp = data.get('ltp', 0)
                if ltp <= 0:
                    return
                current_time = datetime.now()

                if self.current_candle is None:
                    self.candle_start_time = current_time
                    self.current_candle = {'time': current_time, 'open': ltp, 'high': ltp, 'low': ltp, 'close': ltp}
                else:
                    if (current_time - self.candle_start_time).total_seconds() >= self.candle_interval:
                        self.candles.append(self.current_candle.copy())
                        self.candle_start_time = current_time
                        self.current_candle = {'time': current_time, 'open': ltp, 'high': ltp, 'low': ltp, 'close': ltp}
                    else:
                        self.current_candle['high'] = max(self.current_candle['high'], ltp)
                        self.current_candle['low'] = min(self.current_candle['low'], ltp)
                        self.current_candle['close'] = ltp
        except Exception as e:
            print(f"Data update error: {e}")

    def update_oi_data(self, oi_raw):
        try:
            with self.lock:
                options_chain = oi_raw.get('optionsChain', [])
                strikes = {}
                for o in options_chain:
                    strike = o.get('strike_price')
                    typ = o.get('option_type')
                    if not strike or not typ:
                        continue
                    strike = int(strike)
                    if strike not in strikes:
                        strikes[strike] = {'CE': 0, 'PE': 0}
                    if typ == 'CE':
                        strikes[strike]['CE'] = o.get('oi', 0)
                    elif typ == 'PE':
                        strikes[strike]['PE'] = o.get('oi', 0)
                self.oi_data = strikes
        except Exception as e:
            print("OI update error:", e)

    def plot_oi_change(self, df_oi, ax2):
        if self.prev_oi_data is None:
            self.prev_oi_data = df_oi.copy()
            ax2.text(0.5, 0.5, "Waiting for OI change data...", ha="center", va="center", color="gray")
            return

        # Calculate ΔOI
        df_change = df_oi[['CE', 'PE']] - self.prev_oi_data[['CE', 'PE']]
        self.prev_oi_data = df_oi.copy()

        ax2.bar(df_change.index - 50, df_change['CE'] / 1_000_000, width=80, color='red', alpha=0.6, label="CE ΔOI")
        ax2.bar(df_change.index + 50, df_change['PE'] / 1_000_000, width=80, color='green', alpha=0.6, label="PE ΔOI")

        # Label values
        for idx in df_change.index:
            ce_val = df_change.loc[idx, 'CE'] / 1_000_000
            pe_val = df_change.loc[idx, 'PE'] / 1_000_000
            if abs(ce_val) > 0:
                ax2.text(idx - 50, ce_val, f"{ce_val:.1f}L", color='red', ha='center', va='bottom', fontsize=8)
            if abs(pe_val) > 0:
                ax2.text(idx + 50, pe_val, f"{pe_val:.1f}L", color='green', ha='center', va='bottom', fontsize=8)

        ax2.set_title("OI Change (ΔOI per Strike in Millions)")
        ax2.set_ylabel("ΔOI (Mn)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

    def plot(self):
        with self.lock:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
            candles = list(self.candles)
            if self.current_candle:
                candles.append(self.current_candle)
            if not candles:
                return fig

            # --- Candlestick Chart ---
            x_vals = range(len(candles))
            for i, c in enumerate(candles):
                color = 'green' if c['close'] >= c['open'] else 'red'
                ax1.plot([i, i], [c['low'], c['high']], color=color)
                rect = Rectangle((i - 0.3, min(c['open'], c['close'])), 0.6, abs(c['close'] - c['open']),
                                 facecolor=color, edgecolor='black')
                ax1.add_patch(rect)

            ax1.set_title("NIFTY Candlestick with CE/PE OI Overlay")
            ax1.set_ylabel("Price")

            # --- OI Overlay ---
            if self.oi_data:
                df_oi = pd.DataFrame(self.oi_data).T
                df_oi.index = df_oi.index.astype(int)
                df_oi = df_oi.sort_index()

                max_oi = max(df_oi['CE'].max(), df_oi['PE'].max())
                ce_vals = df_oi['CE'] / max_oi
                pe_vals = df_oi['PE'] / max_oi

                for strike in df_oi.index:
                    ce = ce_vals[strike] * 5  # Or adjust scaling factor as needed
                    pe = pe_vals[strike] * 5

                    ax1.barh(strike, -ce, color='red', alpha=0.5)
                    ax1.text(-ce - 0.3, strike, format_oi(df_oi['CE'][strike]),
                             ha='right', va='center', color='red', fontsize=8)

                    ax1.barh(strike, pe, color='green', alpha=0.5)
                    ax1.text(pe + 0.3, strike, format_oi(df_oi['PE'][strike]),
                             ha='left', va='center', color='green', fontsize=8)


                ax1.set_xlabel("OI Strength (Scaled)")
                ax1.grid(True, alpha=0.3)

                # --- Bottom OI Change Plot ---
                self.plot_oi_change(df_oi, ax2)
            else:
                ax2.text(0.5, 0.5, "Waiting for OI updates...", ha="center", va="center", color="gray")

            plt.tight_layout()
            return fig


def format_oi(value):
    """Format OI value in Cr or L based on magnitude"""
    if value >= 1e7:  # 1 crore or more
        return f"{value/1e7:.1f}Cr"
    else:  # Less than 1 crore
        return f"{value/1e5:.1f}L"

# ---------------------- WebSocket + OI Threads ----------------------
chart = FyersCandleChart()

def onmessage(message):
    if isinstance(message, dict):
        chart.update_data(message)

def onerror(msg): print("WebSocket Error:", msg)
def onclose(msg): print("WebSocket Closed:", msg)
def onopen():
    print("WebSocket connected.")
    fyers.subscribe(['NSE:NIFTY50-INDEX'], data_type="SymbolUpdate")
    fyers.keep_running()

fyers = data_ws.FyersDataSocket(
    access_token=ACCESS_TOKEN,
    log_path="",
    on_connect=onopen,
    on_close=onclose,
    on_error=onerror,
    on_message=onmessage
)

def start_websocket(): fyers.connect()

def fetch_oi():
    headers = {"Authorization": ACCESS_TOKEN}
    while True:
        try:
            resp = requests.get(OI_API_URL, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                chart.update_oi_data(data)
        except Exception as e:
            print("OI fetch error:", e)
        time.sleep(OI_POLL_INTERVAL)

# Start background threads once
if "started" not in st.session_state:
    threading.Thread(target=start_websocket, daemon=True).start()
    threading.Thread(target=fetch_oi, daemon=True).start()
    st.session_state.started = True

# ---------------------- Streamlit Display ----------------------
placeholder = st.empty()
while True:
    fig = chart.plot()
    placeholder.pyplot(fig)
    time.sleep(2)
