from fyers_apiv3.FyersWebsocket import data_ws
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
from collections import deque
import threading
import pandas as pd
import requests
import time
import copy
import math

# ---------------------- CONFIG ----------------------
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbzZHMl9iYzVrZk93cHFPNC1JTjl3QndVOEx0WHRlMndzcVE0RGxFX1ROVFRJZTRqRUxhRDhpOFVmb01wZms4MWswNkJZYjU0YVo3N2Z2RDg5MlNqZk80UU82a25qUGYyYmZDLUlPSU1iTzJaRXZEST0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI1ZDc5ZjMzMDk4NzVjYzhlOGRhMDJlMjVhMTk3Y2QzMmJmMDlmN2UzNGMyNDNhZjI2ZWJmYmZmZiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDMyNiIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzYwMTQyNjAwLCJpYXQiOjE3NjAwNjI5MTEsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2MDA2MjkxMSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.67bB-aeqJyYj4fSELmOZrRqX27inZszwhPiP2VnQnp8'
OI_API_URL = "https://api-t1.fyers.in/data/options-chain-v3?symbol=NSE:NIFTY50-INDEX&strikecount=10"
OI_POLL_INTERVAL = 60  # seconds (match to your candle interval)
OI_SCALE_DIV = 1_000_000  # divide OI for nicer visual scaling in bars (adjust as needed)
STRIKE_BAR_HEIGHT = 30  # vertical thickness for horizontal OI bars (in price units)
# ----------------------------------------------------

class FyersCandleChart:
    def __init__(self, candle_interval=60, max_candles=50):
        """
        candle_interval: seconds per candle (60, 300, 900, ...)
        max_candles: number of candles to display
        """
        self.candle_interval = candle_interval
        self.max_candles = max_candles

        # Candle data storage
        self.candles = deque(maxlen=max_candles)  # completed candles
        self.current_candle = None
        self.candle_start_time = None

        # Tick info
        self.current_ltp = 0
        self.current_change = 0
        self.current_chp = 0
        self.prev_close = 0
        self.symbol = ""

        # OI data structures
        # per-strike dict: {strike: {'CE': oi, 'PE': oi, 'oich_CE': ..., 'oich_PE': ...}}
        self.oi_data = {}
        self.prev_oi_data = {}
        # history of total OI deltas (append on each poll)
        self.oi_change_history = deque(maxlen=max_candles)  # each item: {'time':ts, 'call': val, 'put': val}
        self.last_total_call_oi = None
        self.last_total_put_oi = None

        # Plot setup
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(16, 10),
                                                      gridspec_kw={'height_ratios': [4, 1]})
        self.fig.suptitle('Nifty 50 - Live Candlestick Chart with OI Overlay', fontsize=16, fontweight='bold', color='white')

        # Lock for thread safety
        self.lock = threading.Lock()

    # ----------------- WebSocket -> Candle aggregation -----------------
    def update_data(self, data):
        """Update candlestick data from WebSocket response"""
        try:
            with self.lock:
                ltp = data.get('ltp', 0)

                # Skip if invalid
                if ltp <= 0:
                    return

                self.current_ltp = ltp
                self.current_change = data.get('ch', 0)
                self.current_chp = data.get('chp', 0)
                self.prev_close = data.get('prev_close_price', 0)
                self.symbol = data.get('symbol', 'NSE:NIFTY50-INDEX')

                current_time = datetime.now()

                # Initialize first candle if None
                if self.current_candle is None:
                    self.candle_start_time = current_time
                    self.current_candle = {
                        'time': current_time,
                        'open': self.current_ltp,
                        'high': self.current_ltp,
                        'low': self.current_ltp,
                        'close': self.current_ltp,
                        'volume': 1
                    }
                    print(f"Started new candle at {current_time.strftime('%H:%M:%S')} - Open: {self.current_ltp:.2f}")
                else:
                    # Start new candle if interval passed
                    time_diff = (current_time - self.candle_start_time).total_seconds()
                    if time_diff >= self.candle_interval:
                        # finalize current candle
                        self.candles.append(self.current_candle.copy())
                        print(f"Completed candle: O={self.current_candle['open']:.2f} H={self.current_candle['high']:.2f} L={self.current_candle['low']:.2f} C={self.current_candle['close']:.2f}")

                        # start new candle
                        self.candle_start_time = current_time
                        self.current_candle = {
                            'time': current_time,
                            'open': self.current_ltp,
                            'high': self.current_ltp,
                            'low': self.current_ltp,
                            'close': self.current_ltp,
                            'volume': 1
                        }
                        print(f"Started new candle at {current_time.strftime('%H:%M:%S')} - Open: {self.current_ltp:.2f}")
                    else:
                        # update current candle
                        if self.current_candle['low'] == 0 or self.current_ltp < self.current_candle['low']:
                            self.current_candle['low'] = self.current_ltp
                        self.current_candle['high'] = max(self.current_candle['high'], self.current_ltp)
                        self.current_candle['close'] = self.current_ltp
                        self.current_candle['volume'] += 1
        except Exception as e:
            print(f"Error updating data: {e}")

    # ----------------- OI Data Integration -----------------
    def update_oi_data(self, oi_snapshot_raw):
        """
        oi_snapshot_raw: full JSON response from options-chain-v3 'data' object
        Expect 'callOi', 'putOi', and 'optionsChain' array with per-strike entries containing 'oi' and 'option_type'
        """
        try:
            with self.lock:
                # parse total call/put OI if present
                total_call_oi = oi_snapshot_raw.get('callOi')
                total_put_oi = oi_snapshot_raw.get('putOi')

                # build per-strike dict from optionsChain
                options_chain = oi_snapshot_raw.get('optionsChain', [])
                strikes = {}
                for o in options_chain:
                    try:
                        strike = int(o.get('strike_price', -1))
                    except Exception:
                        continue
                    if strike <= 0:
                        continue
                    if strike not in strikes:
                        strikes[strike] = {'CE': 0, 'PE': 0, 'oich_CE': 0, 'oich_PE': 0}
                    typ = o.get('option_type', '').upper()
                    oi = o.get('oi') or 0
                    oich = o.get('oich') or 0
                    if typ == 'CE':
                        strikes[strike]['CE'] = oi
                        strikes[strike]['oich_CE'] = oich
                    elif typ == 'PE':
                        strikes[strike]['PE'] = oi
                        strikes[strike]['oich_PE'] = oich

                # store prev per-strike and totals
                prev_total_call = self.last_total_call_oi
                prev_total_put = self.last_total_put_oi

                # compute total deltas (if totals provided prefer them; else compute from strikes)
                if total_call_oi is None:
                    total_call_oi = sum(v['CE'] for v in strikes.values())
                if total_put_oi is None:
                    total_put_oi = sum(v['PE'] for v in strikes.values())

                # compute deltas and push to history
                call_delta = None
                put_delta = None
                if prev_total_call is not None:
                    call_delta = total_call_oi - prev_total_call
                else:
                    call_delta = 0
                if prev_total_put is not None:
                    put_delta = total_put_oi - prev_total_put
                else:
                    put_delta = 0

                # append to history (timestamped)
                self.oi_change_history.append({
                    'time': datetime.now(),
                    'call': call_delta,
                    'put': put_delta
                })

                # update storage
                self.prev_oi_data = copy.deepcopy(self.oi_data)
                self.oi_data = strikes
                self.last_total_call_oi = total_call_oi
                self.last_total_put_oi = total_put_oi

        except Exception as e:
            print(f"Error updating OI data: {e}")

    # ----------------- Drawing utilities -----------------
    def draw_candlestick(self, ax, x, candle, width=0.6, is_current=False):
        """Draw a single candlestick"""
        open_price = candle['open']
        high_price = candle['high']
        low_price = candle['low']
        close_price = candle['close']

        color = '#00ff00' if close_price >= open_price else '#ff0000'
        edge_color = color
        if is_current:
            edge_color = 'yellow'
            width = 0.7

        # wick
        ax.plot([x, x], [low_price, high_price], color=color, linewidth=1.5, alpha=0.8)

        # body
        body_height = abs(close_price - open_price)
        body_bottom = min(open_price, close_price)

        if body_height < 0.01:
            ax.plot([x - width/2, x + width/2], [open_price, close_price], color=color, linewidth=2)
        else:
            rect = Rectangle((x - width/2, body_bottom), width, body_height,
                             facecolor=color, edgecolor=edge_color, linewidth=1.5, alpha=0.9)
            ax.add_patch(rect)

    # ----------------- Animation loop -----------------
    def animate(self, frame):
        """Animation function for live updates"""
        with self.lock:
            if self.current_candle is None:
                return

            # Clear axes
            self.ax1.clear()
            self.ax2.clear()

            # prepare candle list
            all_candles = list(self.candles) + [self.current_candle]
            if len(all_candles) == 0:
                return

            # Draw candlesticks
            for i, candle in enumerate(all_candles):
                is_current = (i == len(all_candles) - 1)
                self.draw_candlestick(self.ax1, i, candle, is_current=is_current)

            # previous close line
            if self.prev_close > 0:
                self.ax1.axhline(y=self.prev_close, color='#FFA500', linestyle='--', linewidth=1.5, label='Prev Close', alpha=0.7)

            # styling
            self.ax1.set_ylabel('Price (₹)', fontsize=12, fontweight='bold', color='white')
            self.ax1.set_xlabel('Time', fontsize=12, fontweight='bold', color='white')
            self.ax1.grid(True, alpha=0.2, linestyle='--', color='gray')

            # X-axis labels
            x_positions = list(range(len(all_candles)))
            x_labels = [candle['time'].strftime('%H:%M:%S') for candle in all_candles]
            step = max(1, len(all_candles) // 10)
            self.ax1.set_xticks([i for i in x_positions if i % step == 0])
            self.ax1.set_xticklabels([x_labels[i] for i in x_positions if i % step == 0],
                                     rotation=45, ha='right', fontsize=9)

            # add info box
            color = '#00ff00' if self.current_change >= 0 else '#ff0000'
            arrow = '▲' if self.current_change >= 0 else '▼'
            if self.current_candle:
                remaining_time = self.candle_interval - (datetime.now() - self.candle_start_time).total_seconds()
                info_text = f'{arrow} LTP: ₹{self.current_ltp:.2f} | Change: {self.current_change:+.2f} ({self.current_chp:+.2f}%) | Next Candle: {int(remaining_time)}s'
            else:
                info_text = f'{arrow} LTP: ₹{self.current_ltp:.2f} | Change: {self.current_change:+.2f} ({self.current_chp:+.2f}%)'
            self.ax1.text(0.02, 0.98, info_text, transform=self.ax1.transAxes,
                          fontsize=11, fontweight='bold', color=color,
                          verticalalignment='top',
                          bbox=dict(boxstyle='round', facecolor='black', alpha=0.8,
                                    edgecolor=color, linewidth=2))

            # show current candle OHLC
            if self.current_candle:
                ohlc_text = f"O: {self.current_candle['open']:.2f} | H: {self.current_candle['high']:.2f} | L: {self.current_candle['low']:.2f} | C: {self.current_candle['close']:.2f}"
                self.ax1.text(0.98, 0.98, ohlc_text, transform=self.ax1.transAxes,
                              fontsize=10, verticalalignment='top', horizontalalignment='right',
                              bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                              color='yellow')

            # ----------------- OI overlay (horizontal bars at strike levels) -----------------
            # We'll draw call OI bars to the left of the first candle and put OI bars to the right of the last candle.
            try:
                if self.oi_data:
                    # compute max oi for scaling
                    all_oi_vals = [v['CE'] for v in self.oi_data.values()] + [v['PE'] for v in self.oi_data.values()]
                    max_oi = max(all_oi_vals) if all_oi_vals else 1
                    # clamp to at least 1
                    max_oi = max(max_oi, 1)

                    # left boundary x for call bars and right boundary x for put bars
                    left_anchor = -0.5
                    right_anchor = len(all_candles) - 0.5

                    for strike, v in sorted(self.oi_data.items()):
                        # draw only strikes within visible price range (+/- padding)
                        try:
                            y = float(strike)
                        except Exception:
                            continue

                        # Skip if strike outside y-limits (we set limits later but quick check avoids drawing many)
                        # compute scaled length in x-units
                        ce = v.get('CE', 0)
                        pe = v.get('PE', 0)

                        # scaled length relative to max_oi and chart width
                        # give maximum width ~ 60% of candle count
                        max_width_units = max(1, int(len(all_candles) * 0.6))
                        ce_len_units = (ce / max_oi) * max_width_units
                        pe_len_units = (pe / max_oi) * max_width_units

                        # draw call OI to left
                        if ce_len_units > 0.01:
                            xmin = left_anchor - ce_len_units
                            xmax = left_anchor
                            self.ax1.hlines(y, xmin=xmin, xmax=xmax, linewidth=STRIKE_BAR_HEIGHT/10, color='green', alpha=0.25)
                            # annotate CE OI value slightly left of xmin
                            self.ax1.text(xmin - 0.2, y, f"{int(ce/1_000):,}k", va='center', ha='right', fontsize=7, color='white', alpha=0.7)

                        # draw put OI to right
                        if pe_len_units > 0.01:
                            xmin2 = right_anchor
                            xmax2 = right_anchor + pe_len_units
                            self.ax1.hlines(y, xmin=xmin2, xmax=xmax2, linewidth=STRIKE_BAR_HEIGHT/10, color='red', alpha=0.25)
                            # annotate PE OI value slightly right of xmax2
                            self.ax1.text(xmax2 + 0.2, y, f"{int(pe/1_000):,}k", va='center', ha='left', fontsize=7, color='white', alpha=0.7)
            except Exception as e:
                # keep animation running even if overlay drawing fails
                print("Error drawing OI overlay:", e)

            # ----------------- Volume / OI-change chart (ax2) -----------------
            # We prefer plotting OI deltas (call & put) aligned with the latest candles.
            try:
                # Build aligned arrays
                oi_hist = list(self.oi_change_history)
                # align length with candles for x positions: choose last N entries matching number of candles
                n_candles = len(all_candles)
                oi_len = len(oi_hist)
                # create x positions relative to available oi history
                if oi_len == 0:
                    call_vals = [0] * n_candles
                    put_vals = [0] * n_candles
                    x_vals = x_positions
                else:
                    # take last n_candles entries from oi_hist
                    hist_slice = oi_hist[-n_candles:]
                    call_vals = [h['call'] for h in hist_slice]
                    put_vals = [h['put'] for h in hist_slice]
                    # if hist_slice shorter than candles, left-pad with zeros
                    if len(hist_slice) < n_candles:
                        pad = [0] * (n_candles - len(hist_slice))
                        call_vals = pad + call_vals
                        put_vals = pad + put_vals
                    x_vals = x_positions

                # scale for plotting (so numbers fit and are readable). Use simple scaling by dividing OI by OI_SCALE_DIV
                call_plot = [v / OI_SCALE_DIV for v in call_vals]
                put_plot = [-(v / OI_SCALE_DIV) for v in put_vals]  # negative to show opposite direction

                # colors: green for call increase, red for put increase
                bar_width = 0.8
                # plot call and put side-by-side by offsetting x slightly
                offsets = [x - 0.2 for x in x_vals]
                offsets2 = [x + 0.2 for x in x_vals]
                self.ax2.bar(offsets, call_plot, width=0.4, label='Call OI Δ', alpha=0.6)
                self.ax2.bar(offsets2, put_plot, width=0.4, label='Put OI Δ', alpha=0.6)

                self.ax2.set_ylabel('OI Δ (scaled)', fontsize=10, fontweight='bold', color='white')
                self.ax2.set_xlabel('Time', fontsize=10, fontweight='bold', color='white')
                self.ax2.grid(True, alpha=0.2, linestyle='--', axis='y', color='gray')

                # set x ticks same as main chart
                self.ax2.set_xticks([i for i in x_positions if i % step == 0])
                self.ax2.set_xticklabels([x_labels[i] for i in x_positions if i % step == 0],
                                         rotation=45, ha='right', fontsize=9)

                # legend
                self.ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)
            except Exception as e:
                print("Error drawing OI Δ bars:", e)

            # Sync x-limits
            if len(all_candles) > 0:
                self.ax1.set_xlim(-0.5, len(all_candles) - 0.5)
                self.ax2.set_xlim(-0.5, len(all_candles) - 0.5)

            # Auto-scale y-axis
            try:
                all_highs = [c['high'] for c in all_candles if c['high'] > 0]
                all_lows = [c['low'] for c in all_candles if c['low'] > 0]

                if all_highs and all_lows:
                    y_min = min(all_lows)
                    y_max = max(all_highs)
                    if self.prev_close > 0:
                        y_min = min(y_min, self.prev_close)
                        y_max = max(y_max, self.prev_close)
                    price_range = y_max - y_min
                    padding = max(price_range * 0.05, 10)
                    self.ax1.set_ylim(y_min - padding, y_max + padding)
            except Exception:
                pass

            try:
                plt.tight_layout()
            except Exception:
                pass

    def start(self):
        """Start the live chart animation"""
        ani = FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        plt.show()

# ----------------- chart instance -----------------
chart = FyersCandleChart(candle_interval=60, max_candles=50)

# ----------------- WebSocket callbacks -----------------
def onmessage(message):
    """Callback function to handle incoming messages from the FyersDataSocket WebSocket."""
    if isinstance(message, dict):
        chart.update_data(message)

def onerror(message):
    print("WebSocket Error:", message)

def onclose(message):
    print("WebSocket connection closed:", message)

def onopen():
    print("WebSocket connection opened!")
    data_type = "SymbolUpdate"
    symbols = ['NSE:NIFTY50-INDEX']
    fyers.subscribe(symbols=symbols, data_type=data_type)
    print(f"Subscribed to {symbols}")
    print(f"Candle interval: {chart.candle_interval} seconds")
    fyers.keep_running()

# ----------------- Create Fyers WebSocket instance -----------------
fyers = data_ws.FyersDataSocket(
    access_token=ACCESS_TOKEN,
    log_path="",
    litemode=False,
    write_to_file=False,
    reconnect=True,
    on_connect=onopen,
    on_close=onclose,
    on_error=onerror,
    on_message=onmessage
)

def start_websocket():
    """Start WebSocket connection in a separate thread"""
    print("Connecting to Fyers WebSocket...")
    fyers.connect()

# ----------------- OI Polling Thread -----------------
def fetch_oi_periodically():
    headers = {"Authorization": f"{ACCESS_TOKEN}"}
    while True:
        try:
            resp = requests.get(OI_API_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # data format: { "code":200, "data":{...}}
                inner = data.get('data') or {}
                # update chart OI data
                chart.update_oi_data(inner)
            else:
                print(f"OI API returned status {resp.status_code}")
        except Exception as e:
            print("Error fetching OI data:", e)
        # sleep for configured interval
        time.sleep(OI_POLL_INTERVAL)

# ----------------- Entrypoint -----------------
if __name__ == "__main__":
    print("=" * 60)
    print("Fyers Live Candlestick Chart WITH OI Overlay")
    print("=" * 60)
    print(f"Candle Interval: {chart.candle_interval} seconds")
    print(f"Max Candles Display: {chart.max_candles}")
    print("=" * 60)

    # start websocket thread
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()

    # start OI fetch thread
    oi_thread = threading.Thread(target=fetch_oi_periodically, daemon=True)
    oi_thread.start()

    # small delay for connections
    time.sleep(2)

    print("\nStarting live candlestick chart...")
    print("Chart will update as data arrives from WebSocket and OI REST API...")
    try:
        chart.start()
    except Exception as e:
        print(f"Error starting chart: {e}")
        import traceback
        traceback.print_exc()
