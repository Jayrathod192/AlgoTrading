from fyers_apiv3.FyersWebsocket import data_ws


def onmessage(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Response:", message)


def onerror(message):
    """
    Callback function to handle WebSocket errors.

    Parameters:
        message (dict): The error message received from the WebSocket.


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
    # Specify the data type and symbols you want to subscribe to
    data_type = "SymbolUpdate"

    # Subscribe to the specified symbols and data type
    symbols = ['NSE:SBIN-EQ', 'NSE:ADANIENT-EQ']
    fyers.subscribe(symbols=symbols, data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()


# Replace the sample access token with your actual access token obtained from Fyers
access_token ="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MzY1OTU3NzcsImV4cCI6MTczNjY0MTg1NywibmJmIjoxNzM2NTk1Nzc3LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbmdsbEJxTll3VGM2bWJZVE5BXzQ0djNKWm82d1pLV19YbDBBQWFqbmVpR0t2cEw2R2RkR3l4SklVRU43d3B2ZGE5cUFrLW5LQ2dsbmhkbHhQTFB3dUFrYWRqZk1TU1dxbld2bDUyc3hWZEpYdTVvRT0iLCJkaXNwbGF5X25hbWUiOiJSYXRob2QgSmlnbmVzaCIsIm9tcyI6IksxIiwiaHNtX2tleSI6IjczMzRmNzdmZmVmMWNhMGM0Yzk4Njc3OGFiY2ZlOTJjM2RkYTc2YTU2ODlmYTc4YzZlNWY5YTYzIiwiZnlfaWQiOiJYUjIwMzI2IiwiYXBwVHlwZSI6MTAwLCJwb2FfZmxhZyI6Ik4ifQ.xtpEp3192i9SKk8RLh1lS-UUukACypFBlXozHHmCT8U"
# Create a FyersDataSocket instance with the provided parameters
fyers = data_ws.FyersDataSocket(
    access_token=access_token,       # Access token in the format "appid:accesstoken"
    log_path="",                     # Path to save logs. Leave empty to auto-create logs in the current directory.
    litemode=False,                  # Lite mode disabled. Set to True if you want a lite response.
    write_to_file=False,              # Save response in a log file instead of printing it.
    reconnect=True,                  # Enable auto-reconnection to WebSocket on disconnection.
    on_connect=onopen,               # Callback function to subscribe to data upon connection.
    on_close=onclose,                # Callback function to handle WebSocket connection close events.
    on_error=onerror,                # Callback function to handle WebSocket errors.
    on_message=onmessage             # Callback function to handle incoming messages from the WebSocket.
)



# Establish a connection to the Fyers WebSocket
fyers.connect()
fyers.keep_running()

# ------------------------------------------------------------------------------------------------------------------------------------------
# Sample Success Response
# ------------------------------------------------------------------------------------------------------------------------------------------
#
# {
#     "ltp":606.4,
#     "vol_traded_today":3045212,
#     "last_traded_time":1690953622,
#     "exch_feed_time":1690953622,
#     "bid_size":2081,
#     "ask_size":903,
#     "bid_price":606.4,
#     "ask_price":606.45,
#     "last_traded_qty":5,
#     "tot_buy_qty":749960,
#     "tot_sell_qty":1092063,
#     "avg_trade_price":608.2,
#     "low_price":605.85,
#     "high_price":610.5,
#     "open_price":609.85,
#     "prev_close_price":620.2,
#     "type":"sf",
#     "symbol":"NSE:SBIN-EQ",
#     "ch":-13.8,
#     "chp":-2.23
# }
