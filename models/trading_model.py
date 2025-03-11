import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class TradingModel:
    def __init__(self):
        self.model = RandomForestClassifier()

    def preprocess_data(self, data):
        # Ensure 'Close' is a numeric column
        data['Close'] = pd.to_numeric(data['Close'], errors='coerce')

        # Optionally, drop rows with NaN values
        data.dropna(subset=['Close'], inplace=True)

        # Calculate SMA_20
        data['SMA_20'] = data['Close'].rolling(window=20).mean()

        # Calculate RSI
        data['RSI'] = self.compute_rsi(data['Close'])

        # Calculate Target (Next day's close price higher than current day's close)
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)

        # Drop any rows with NaN values after transformations
        data.dropna(inplace=True)

        return data

    def compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def train(self, data):
        data = self.preprocess_data(data)
        features = data[['SMA_20', 'RSI']]
        target = data['Target']
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        predictions = self.model.predict(X_test)
        print("Accuracy:", accuracy_score(y_test, predictions))

    def predict(self, features):
        return self.model.predict(features)

