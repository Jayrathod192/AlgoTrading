import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot

from fyers_apiv3.FyersWebsocket import data_ws
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
from collections import deque
import threading
import pandas as pd

class FyersCandleChart:
    def __init__(self, candle_interval=60, max_candles=50):
        """
        Initialize candlestick chart
        candle_interval: seconds for each candle (default 60s = 1 minute)
        max_candles: maximum number of candles to display
        """
        self.candle_interval = candle_interval
        self.max_candles = max_candles

        # Candle data storage
        self.candles = deque(maxlen=max_candles)
        self.current_candle = None
        self.candle_start_time = None

        # Current tick data
        self.current_ltp = 0
        self.current_change = 0
        self.current_chp = 0
        self.prev_close = 0
        self.symbol = ""

        # Setup plot
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(16, 10),
                                                       gridspec_kw={'height_ratios': [4, 1]})
        self.fig.suptitle('Nifty 50 - Live Candlestick Chart', fontsize=16, fontweight='bold', color='white')

        # Lock for thread safety
        self.lock = threading.Lock()

    def update_data(self, data):
        """Update candlestick data from WebSocket response"""
        try:
            with self.lock:
                ltp = data.get('ltp', 0)

                # Skip if LTP is 0 or invalid
                if ltp <= 0:
                    return

                self.current_ltp = ltp
                self.current_change = data.get('ch', 0)
                self.current_chp = data.get('chp', 0)
                self.prev_close = data.get('prev_close_price', 0)
                self.symbol = data.get('symbol', 'NSE:NIFTY50-INDEX')

                current_time = datetime.now()

                # Initialize first candle
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
                    # Check if we need to start a new candle
                    time_diff = (current_time - self.candle_start_time).total_seconds()

                    if time_diff >= self.candle_interval:
                        # Save current candle and start new one
                        self.candles.append(self.current_candle.copy())
                        print(f"Completed candle: O={self.current_candle['open']:.2f} H={self.current_candle['high']:.2f} L={self.current_candle['low']:.2f} C={self.current_candle['close']:.2f}")

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
                        # Update current candle - ensure low is properly set
                        if self.current_candle['low'] == 0 or self.current_ltp < self.current_candle['low']:
                            self.current_candle['low'] = self.current_ltp

                        self.current_candle['high'] = max(self.current_candle['high'], self.current_ltp)
                        self.current_candle['close'] = self.current_ltp
                        self.current_candle['volume'] += 1

        except Exception as e:
            print(f"Error updating data: {e}")

    def draw_candlestick(self, ax, x, candle, width=0.6, is_current=False):
        """Draw a single candlestick"""
        open_price = candle['open']
        high_price = candle['high']
        low_price = candle['low']
        close_price = candle['close']

        # Determine color (green for bullish, red for bearish)
        color = '#00ff00' if close_price >= open_price else '#ff0000'
        edge_color = '#00ff00' if close_price >= open_price else '#ff0000'

        if is_current:
            edge_color = 'yellow'
            width = 0.7

        # Draw high-low line (wick)
        ax.plot([x, x], [low_price, high_price], color=color, linewidth=1.5, alpha=0.8)

        # Draw open-close rectangle (body)
        body_height = abs(close_price - open_price)
        body_bottom = min(open_price, close_price)

        if body_height < 0.01:  # Doji or very small body
            body_height = 0.5
            ax.plot([x - width/2, x + width/2], [open_price, close_price],
                   color=color, linewidth=2)
        else:
            rect = Rectangle((x - width/2, body_bottom), width, body_height,
                           facecolor=color, edgecolor=edge_color, linewidth=1.5, alpha=0.9)
            ax.add_patch(rect)

    def animate(self, frame):
        """Animation function for live updates"""
        with self.lock:
            if self.current_candle is None:
                return

            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()

            # Prepare candle data for plotting
            all_candles = list(self.candles) + [self.current_candle]

            if len(all_candles) == 0:
                return

            # Draw candlesticks
            for i, candle in enumerate(all_candles):
                is_current = (i == len(all_candles) - 1)
                self.draw_candlestick(self.ax1, i, candle, is_current=is_current)

            # Add previous close line
            if self.prev_close > 0:
                self.ax1.axhline(y=self.prev_close, color='#FFA500',
                               linestyle='--', linewidth=1.5, label='Prev Close', alpha=0.7)

            # Styling for main chart
            self.ax1.set_ylabel('Price (₹)', fontsize=12, fontweight='bold', color='white')
            self.ax1.set_xlabel('Time', fontsize=12, fontweight='bold', color='white')
            self.ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
            self.ax1.grid(True, alpha=0.2, linestyle='--', color='gray')

            # Set x-axis labels with timestamps
            x_positions = range(len(all_candles))
            x_labels = [candle['time'].strftime('%H:%M:%S') for candle in all_candles]

            # Show every nth label to avoid crowding
            step = max(1, len(all_candles) // 10)
            self.ax1.set_xticks([i for i in x_positions if i % step == 0])
            self.ax1.set_xticklabels([x_labels[i] for i in x_positions if i % step == 0],
                                     rotation=45, ha='right', fontsize=9)

            # Add current price and change info
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

            # Show current candle OHLC
            if self.current_candle:
                ohlc_text = f"O: {self.current_candle['open']:.2f} | H: {self.current_candle['high']:.2f} | L: {self.current_candle['low']:.2f} | C: {self.current_candle['close']:.2f}"
                self.ax1.text(0.98, 0.98, ohlc_text, transform=self.ax1.transAxes,
                             fontsize=10, verticalalignment='top', horizontalalignment='right',
                             bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                             color='yellow')

            # Volume chart (bottom panel)
            volumes = [c['volume'] for c in all_candles]
            colors = ['#00ff00' if all_candles[i]['close'] >= all_candles[i]['open'] else '#ff0000'
                     for i in range(len(all_candles))]

            self.ax2.bar(x_positions, volumes, color=colors, alpha=0.6, width=0.8)
            self.ax2.set_ylabel('Ticks', fontsize=10, fontweight='bold', color='white')
            self.ax2.set_xlabel('Time', fontsize=10, fontweight='bold', color='white')
            self.ax2.grid(True, alpha=0.2, linestyle='--', axis='y', color='gray')

            # Match x-axis with candlestick chart
            self.ax2.set_xticks([i for i in x_positions if i % step == 0])
            self.ax2.set_xticklabels([x_labels[i] for i in x_positions if i % step == 0],
                                     rotation=45, ha='right', fontsize=9)

            # Set x-axis limits
            if len(all_candles) > 0:
                self.ax1.set_xlim(-0.5, len(all_candles) - 0.5)
                self.ax2.set_xlim(-0.5, len(all_candles) - 0.5)

            # Auto-scale y-axis with padding
            if all_candles:
                all_highs = [c['high'] for c in all_candles if c['high'] > 0]
                all_lows = [c['low'] for c in all_candles if c['low'] > 0]

                if all_highs and all_lows:
                    y_min = min(all_lows)
                    y_max = max(all_highs)
                    padding = (y_max - y_min) * 0.1
                    self.ax1.set_ylim(y_min - padding, y_max + padding)

            try:
                plt.tight_layout()
            except Exception:
                pass  # Ignore tight_layout warnings

    def start(self):
        """Start the live chart animation"""
        ani = FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        plt.show()


# Global chart instance - adjust candle_interval as needed
# candle_interval: 60 = 1 minute, 300 = 5 minutes, 900 = 15 minutes, etc.
chart = FyersCandleChart(candle_interval=60, max_candles=50)


def onmessage(message):
    """Callback function to handle incoming messages from the FyersDataSocket WebSocket."""
    # print("Response:", message)

    # Update chart with new data
    if isinstance(message, dict):
        chart.update_data(message)


def onerror(message):
    """Callback function to handle WebSocket errors."""
    print("Error:", message)


def onclose(message):
    """Callback function to handle WebSocket connection close events."""
    print("Connection closed:", message)


def onopen():
    """Callback function to subscribe to data type and symbols upon WebSocket connection."""
    print("WebSocket connection opened!")

    # Specify the data type and symbols you want to subscribe to
    data_type = "SymbolUpdate"
    symbols = ['NSE:NIFTY50-INDEX']

    # Subscribe to the specified symbols and data type
    fyers.subscribe(symbols=symbols, data_type=data_type)
    print(f"Subscribed to {symbols}")
    print(f"Candle interval: {chart.candle_interval} seconds")

    # Keep the socket running to receive real-time data
    fyers.keep_running()


# Replace with your actual access token
access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbzZHMl9iYzVrZk93cHFPNC1JTjl3QndVOEx0WHRlMndzcVE0RGxFX1ROVFRJZTRqRUxhRDhpOFVmb01wZms4MWswNkJZYjU0YVo3N2Z2RDg5MlNqZk80UU82a25qUGYyYmZDLUlPSU1iTzJaRXZEST0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI1ZDc5ZjMzMDk4NzVjYzhlOGRhMDJlMjVhMTk3Y2QzMmJmMDlmN2UzNGMyNDNhZjI2ZWJmYmZmZiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDMyNiIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzYwMTQyNjAwLCJpYXQiOjE3NjAwNjI5MTEsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2MDA2MjkxMSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.67bB-aeqJyYj4fSELmOZrRqX27inZszwhPiP2VnQnp8'

# Create a FyersDataSocket instance
fyers = data_ws.FyersDataSocket(
    access_token=access_token,
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


if __name__ == "__main__":
    print("=" * 60)
    print("Fyers Live Candlestick Chart")
    print("=" * 60)
    print(f"Candle Interval: {chart.candle_interval} seconds")
    print(f"Max Candles Display: {chart.max_candles}")
    print("=" * 60)

    # Start WebSocket in a separate thread
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()

    # Give WebSocket a moment to connect
    import time
    time.sleep(2)

    print("\nStarting live candlestick chart...")
    print("Chart will update as data arrives from WebSocket...")
    print("Each candle represents", chart.candle_interval, "seconds of trading data")
    print("\nChart window should open now...")

    # Start the chart (blocking call)
    try:
        chart.start()
    except Exception as e:
        print(f"Error starting chart: {e}")
        import traceback
        traceback.print_exc()