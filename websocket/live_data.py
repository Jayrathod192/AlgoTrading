from fyers_apiv3.FyersWebsocket import data_ws
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
from collections import deque
import threading

class FyersLiveChart:
    def __init__(self, max_points=100):
        self.max_points = max_points
        self.timestamps = deque(maxlen=max_points)
        self.prices = deque(maxlen=max_points)
        self.highs = deque(maxlen=max_points)
        self.lows = deque(maxlen=max_points)

        # Current data
        self.current_ltp = 0
        self.current_change = 0
        self.current_chp = 0
        self.prev_close = 0
        self.symbol = ""

        # Setup plot
        plt.style.use('seaborn-v0_8-darkgrid')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(14, 9),
                                                       gridspec_kw={'height_ratios': [3, 1]})
        self.fig.suptitle('Nifty 50 Live Chart', fontsize=16, fontweight='bold')

        # Lock for thread safety
        self.lock = threading.Lock()

    def update_data(self, data):
        """Update data from WebSocket response"""
        try:
            with self.lock:
                self.current_ltp = data.get('ltp', 0)
                self.current_change = data.get('ch', 0)
                self.current_chp = data.get('chp', 0)
                self.prev_close = data.get('prev_close_price', 0)
                self.symbol = data.get('symbol', 'NSE:NIFTY50-INDEX')

                current_time = datetime.now()
                self.timestamps.append(current_time)
                self.prices.append(self.current_ltp)
                self.highs.append(data.get('high_price', self.current_ltp))
                self.lows.append(data.get('low_price', self.current_ltp))

                print(f"Updated: LTP={self.current_ltp:.2f}, Change={self.current_change:+.2f} ({self.current_chp:+.2f}%)")

        except Exception as e:
            print(f"Error updating data: {e}")

    def animate(self, frame):
        """Animation function for live updates"""
        with self.lock:
            if len(self.prices) < 2:
                return

            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()

            # Convert to lists for plotting
            times = list(self.timestamps)
            prices = list(self.prices)
            highs = list(self.highs)
            lows = list(self.lows)

            # Main price chart
            self.ax1.plot(times, prices, color='#2962FF', linewidth=2.5, label='LTP', marker='o', markersize=3)
            self.ax1.fill_between(times, prices, alpha=0.2, color='#2962FF')

            # Add high/low bands
            self.ax1.plot(times, highs, color='#00C853', linestyle='--',
                         alpha=0.6, linewidth=1.5, label='High')
            self.ax1.plot(times, lows, color='#D50000', linestyle='--',
                         alpha=0.6, linewidth=1.5, label='Low')

            # Previous close line
            if self.prev_close > 0:
                self.ax1.axhline(y=self.prev_close, color='#FF6F00',
                               linestyle=':', linewidth=2, label='Prev Close', alpha=0.8)

            # Styling for main chart
            self.ax1.set_ylabel('Price (₹)', fontsize=12, fontweight='bold')
            self.ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
            self.ax1.grid(True, alpha=0.3, linestyle='--')

            # Add current price and change info
            color = '#00C853' if self.current_change >= 0 else '#D50000'
            arrow = '▲' if self.current_change >= 0 else '▼'
            info_text = f'{arrow} LTP: ₹{self.current_ltp:.2f} | Change: {self.current_change:+.2f} ({self.current_chp:+.2f}%)'

            self.ax1.text(0.02, 0.98, info_text, transform=self.ax1.transAxes,
                         fontsize=12, fontweight='bold', color=color,
                         verticalalignment='top',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, edgecolor=color, linewidth=2))

            # Add high/low info
            day_high = max(highs) if highs else 0
            day_low = min(lows) if lows else 0
            range_text = f'Day Range: ₹{day_low:.2f} - ₹{day_high:.2f}'
            self.ax1.text(0.98, 0.98, range_text, transform=self.ax1.transAxes,
                         fontsize=10, verticalalignment='top', horizontalalignment='right',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

            # Volume/Change indicator (bottom panel)
            changes = [p - self.prev_close for p in prices]
            colors = ['#00C853' if c >= 0 else '#D50000' for c in changes]
            bar_width = (times[-1] - times[0]).total_seconds() / len(times) / 86400 if len(times) > 1 else 0.0003
            self.ax2.bar(times, changes, color=colors, alpha=0.7, width=bar_width, edgecolor='black', linewidth=0.5)
            self.ax2.axhline(y=0, color='black', linewidth=1.5)
            self.ax2.set_ylabel('Change from Prev Close (₹)', fontsize=10, fontweight='bold')
            self.ax2.set_xlabel('Time', fontsize=10, fontweight='bold')
            self.ax2.grid(True, alpha=0.3, linestyle='--', axis='y')

            # Format time labels
            if len(times) > 0:
                self.ax1.set_xlim(times[0], times[-1])
                self.ax2.set_xlim(times[0], times[-1])

            # Rotate x-axis labels
            for ax in [self.ax1, self.ax2]:
                ax.tick_params(axis='x', rotation=45, labelsize=9)
                ax.tick_params(axis='y', labelsize=9)

            plt.tight_layout()

    def start(self):
        """Start the live chart animation"""
        ani = FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        plt.show()


# Global chart instance
chart = FyersLiveChart(max_points=100)


def onmessage(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.
    """
    print("Response:", message)

    # Update chart with new data
    if isinstance(message, dict):
        chart.update_data(message)


def onerror(message):
    """
    Callback function to handle WebSocket errors.
    """
    print("Error:", message)


def onclose(message):
    """
    Callback function to handle WebSocket connection close events.
    """
    print("Connection closed:", message)


def onopen():
    """
    Callback function to subscribe to data type and symbols upon WebSocket connection.
    """
    print("WebSocket connection opened!")

    # Specify the data type and symbols you want to subscribe to
    data_type = "SymbolUpdate"
    symbols = ['NSE:NIFTY50-INDEX']

    # Subscribe to the specified symbols and data type
    fyers.subscribe(symbols=symbols, data_type=data_type)
    print(f"Subscribed to {symbols}")

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
    # Start WebSocket in a separate thread
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()

    # Give WebSocket a moment to connect
    import time
    time.sleep(2)

    print("Starting live chart...")
    print("Chart will update as data arrives from WebSocket...")

    # Start the chart (blocking call)
    chart.start()