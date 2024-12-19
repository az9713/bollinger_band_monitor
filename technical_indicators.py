<<<<<<< HEAD
import numpy as np
import pandas as pd
### TODO: To add comprehensive key, values for all optional parameters.
class TechnicalIndicators:
    def __init__(self, data):
        """
        Initialize with a pandas DataFrame containing at least 'close' prices
        :param data: DataFrame with columns including ['close']
        """
        self.data = data
        
    def sma(self, period=20):
        """
        Simple Moving Average
        """
        return self.data['close'].rolling(window=period).mean()
    
    def ema(self, period=20):
        """
        Exponential Moving Average
        """
        return self.data['close'].ewm(span=period, adjust=False).mean()
    
    def rsi(self, period=14):
        """
        Relative Strength Index
        """
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Moving Average Convergence Divergence
        """
        fast_ema = self.data['close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = self.data['close'].ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'macd_histogram': macd_histogram
        })
    
    def bollinger_bands(self, window=20, std_dev=3):
        """
        Calculate Bollinger Bands
        
        Parameters:
        window (int): The window for moving average, default is 20
        std_dev (int): Number of standard deviations, default is 3
        
        Returns:
        DataFrame with Upper and Lower Bollinger Bands
        """
        sma = self.data['close'].rolling(window=window).mean()
        rolling_std = self.data['close'].rolling(window=window).std()
        
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        return pd.DataFrame({
            'BB_Upper': upper_band,
            'BB_Lower': lower_band
        })
    
    def stochastic_oscillator(self, period=14):
        """
        Stochastic Oscillator
        """
        low_min = self.data['low'].rolling(window=period).min()
        high_max = self.data['high'].rolling(window=period).max()
        
        k = 100 * ((self.data['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=3).mean()
        
        return pd.DataFrame({
            'k_line': k,
            'd_line': d
        })
    
    def check_recent_bb_crossings(self, months=2):
        """
        Check for recent instances where price range intersects with 3-sigma Bollinger Bands
        
        Parameters:
        months (int): Number of recent months to check, default is 2
        
        Returns:
        List of dictionaries containing band intersection information
        """
        # Calculate cutoff date for recent data
        last_date = self.data.index[-1]
        cutoff_date = last_date - pd.DateOffset(months=months)
        
        # Get recent data
        recent_data = self.data[self.data.index >= cutoff_date].copy()
        
        # Calculate Bollinger Bands if not already done
        bb_data = self.bollinger_bands()
        recent_bb = bb_data[bb_data.index >= cutoff_date]
        
        events = []
        
        # Check each day for price range vs bands
        for i in range(len(recent_data)):
            date = recent_data.index[i]
            
            # Get daily price range
            daily_high = recent_data['high'].iloc[i]
            daily_low = recent_data['low'].iloc[i]
            daily_open = recent_data['open'].iloc[i]
            daily_close = recent_data['close'].iloc[i]
            
            # Get band values
            upper_band = recent_bb['BB_Upper'].iloc[i]
            lower_band = recent_bb['BB_Lower'].iloc[i]
            
            # Check upper band
            if max(daily_high, daily_open, daily_close) > upper_band:
                max_price = max(daily_high, daily_open, daily_close)
                deviation = ((max_price - upper_band) / upper_band) * 100
                events.append({
                    'date': date,
                    'type': 'Above upper band',
                    'price': max_price,
                    'band_value': upper_band,
                    'deviation': deviation,
                    'description': (f"Price range extended above upper 3-sigma band. "
                                  f"High: {daily_high:.2f}, Open: {daily_open:.2f}, Close: {daily_close:.2f}")
                })
            
            # Check lower band
            if min(daily_low, daily_open, daily_close) < lower_band:
                min_price = min(daily_low, daily_open, daily_close)
                deviation = ((min_price - lower_band) / lower_band) * 100
                events.append({
                    'date': date,
                    'type': 'Below lower band',
                    'price': min_price,
                    'band_value': lower_band,
                    'deviation': deviation,
                    'description': (f"Price range extended below lower 3-sigma band. "
                                  f"Low: {daily_low:.2f}, Open: {daily_open:.2f}, Close: {daily_close:.2f}")
                })
        
        # Sort events by date (most recent first)
        events.sort(key=lambda x: x['date'], reverse=True)
        
        return events
    
    def print_bb_crossings(self, months=2, logger=None):
        """
        Print recent Bollinger Band intersections in a formatted way
        """
        events = self.check_recent_bb_crossings(months)
        
        # Get the date range for the analysis
        last_date = self.data.index[-1].strftime('%Y-%m-%d')
        start_date = (self.data.index[-1] - pd.DateOffset(months=months)).strftime('%Y-%m-%d')
        
        if not events:
            message = f"\nNo price points outside Bollinger Band (3-sigma) range found between {start_date} and {last_date}"
            if logger:
                logger.info(message)
            else:
                print(message)
            return
        
        header = f"\nPrices Outside Bollinger Band Range between {start_date} and {last_date}:"
        separator = "-" * 120
        format_header = f"{'Date':<12} {'Type':<25} {'Price':<10} {'Band Value':<12} {'% Deviation':<12} {'Description'}"
        
        if logger:
            logger.info(header)
            logger.info(separator)
            logger.info(format_header)
            logger.info(separator)
        else:
            print(header)
            print(separator)
            print(format_header)
            print(separator)
        
        for event in events:
            date_str = event['date'].strftime('%Y-%m-%d')
            message = (f"{date_str:<12} {event['type']:<25} {event['price']:<10.2f} "
                      f"{event['band_value']:<12.2f} {event['deviation']:>8.2f}% {event['description']}")
            if logger:
                logger.info(message)
            else:
=======
import numpy as np
import pandas as pd

class TechnicalIndicators:
    def __init__(self, data):
        """
        Initialize with a pandas DataFrame containing at least 'close' prices
        :param data: DataFrame with columns including ['close']
        """
        self.data = data
        
    def sma(self, period=20):
        """
        Simple Moving Average
        """
        return self.data['close'].rolling(window=period).mean()
    
    def ema(self, period=20):
        """
        Exponential Moving Average
        """
        return self.data['close'].ewm(span=period, adjust=False).mean()
    
    def rsi(self, period=14):
        """
        Relative Strength Index
        """
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Moving Average Convergence Divergence
        """
        fast_ema = self.data['close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = self.data['close'].ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'macd_histogram': macd_histogram
        })
    
    def bollinger_bands(self, window=20, std_dev=3):
        """
        Calculate Bollinger Bands
        
        Parameters:
        window (int): The window for moving average, default is 20
        std_dev (int): Number of standard deviations, default is 3
        
        Returns:
        DataFrame with Upper and Lower Bollinger Bands
        """
        sma = self.data['close'].rolling(window=window).mean()
        rolling_std = self.data['close'].rolling(window=window).std()
        
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        return pd.DataFrame({
            'BB_Upper': upper_band,
            'BB_Lower': lower_band
        })
    
    def stochastic_oscillator(self, period=14):
        """
        Stochastic Oscillator
        """
        low_min = self.data['low'].rolling(window=period).min()
        high_max = self.data['high'].rolling(window=period).max()
        
        k = 100 * ((self.data['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=3).mean()
        
        return pd.DataFrame({
            'k_line': k,
            'd_line': d
        })
    
    def check_recent_bb_crossings(self, months=2):
        """
        Check for recent Bollinger Band crossings within the specified months
        
        Parameters:
        months (int): Number of months to look back (default: 1)
        
        Returns:
        list: List of dictionaries containing crossing events
        """
        # Calculate cutoff date for recent data
        last_date = self.data.index[-1]
        cutoff_date = last_date - pd.DateOffset(months=months)
        
        # Get recent data
        recent_data = self.data[self.data.index >= cutoff_date].copy()
        
        # Calculate Bollinger Bands if not already done
        bb_data = self.bollinger_bands()
        recent_bb = bb_data[bb_data.index >= cutoff_date]
        
        events = []
        
        # Check each day for price range vs bands
        for i in range(len(recent_data)):
            date = recent_data.index[i]
            
            # Get daily price range
            daily_high = recent_data['high'].iloc[i]
            daily_low = recent_data['low'].iloc[i]
            daily_open = recent_data['open'].iloc[i]
            daily_close = recent_data['close'].iloc[i]
            
            # Get band values
            upper_band = recent_bb['BB_Upper'].iloc[i]
            lower_band = recent_bb['BB_Lower'].iloc[i]
            
            # Check upper band
            if max(daily_high, daily_open, daily_close) > upper_band:
                max_price = max(daily_high, daily_open, daily_close)
                deviation = ((max_price - upper_band) / upper_band) * 100
                events.append({
                    'date': date,
                    'type': 'Above upper band',
                    'price': max_price,
                    'band_value': upper_band,
                    'deviation': deviation,
                    'description': (f"Price range extended above upper 3-sigma band. "
                                  f"High: {daily_high:.2f}, Open: {daily_open:.2f}, Close: {daily_close:.2f}")
                })
            
            # Check lower band
            if min(daily_low, daily_open, daily_close) < lower_band:
                min_price = min(daily_low, daily_open, daily_close)
                deviation = ((min_price - lower_band) / lower_band) * 100
                events.append({
                    'date': date,
                    'type': 'Below lower band',
                    'price': min_price,
                    'band_value': lower_band,
                    'deviation': deviation,
                    'description': (f"Price range extended below lower 3-sigma band. "
                                  f"Low: {daily_low:.2f}, Open: {daily_open:.2f}, Close: {daily_close:.2f}")
                })
        
        # Sort events by date (most recent first)
        events.sort(key=lambda x: x['date'], reverse=True)
        
        return events
    
    def print_bb_crossings(self, months=2, logger=None):
        """
        Print recent Bollinger Band intersections in a formatted way
        """
        events = self.check_recent_bb_crossings(months)
        
        # Get the date range for the analysis
        last_date = self.data.index[-1].strftime('%Y-%m-%d')
        start_date = (self.data.index[-1] - pd.DateOffset(months=months)).strftime('%Y-%m-%d')
        
        if not events:
            message = f"\nNo price points outside Bollinger Band (3-sigma) range found between {start_date} and {last_date}"
            if logger:
                logger.info(message)
            else:
                print(message)
            return
        
        header = f"\nPrices Outside Bollinger Band Range between {start_date} and {last_date}:"
        separator = "-" * 120
        format_header = f"{'Date':<12} {'Type':<25} {'Price':<10} {'Band Value':<12} {'% Deviation':<12} {'Description'}"
        
        if logger:
            logger.info(header)
            logger.info(separator)
            logger.info(format_header)
            logger.info(separator)
        else:
            print(header)
            print(separator)
            print(format_header)
            print(separator)
        
        for event in events:
            date_str = event['date'].strftime('%Y-%m-%d')
            message = (f"{date_str:<12} {event['type']:<25} {event['price']:<10.2f} "
                      f"{event['band_value']:<12.2f} {event['deviation']:>8.2f}% {event['description']}")
            if logger:
                logger.info(message)
            else:
>>>>>>> e46b2bba6c68a9edac839545b3a5ad8f0efac8b2
                print(message)