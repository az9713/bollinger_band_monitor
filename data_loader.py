import pandas as pd
from pathlib import Path
import logging
import sys

class DataLoader:
    def __init__(self, root_dir, file_pattern='.us.txt'):
        """
        Initialize DataLoader with root directory and file pattern
        
        Parameters:
        root_dir (str): Root directory to start searching for files
        file_pattern (str): File pattern to match (default: '.us.txt')
        """
        self.root_dir = root_dir
        self.file_pattern = file_pattern
        self.logger = None
        self.setup_logging()
        self.data_files = self._find_data_files()
        
    def setup_logging(self):
        """Set up logging to both file and console with the same format"""
        self.logger = logging.getLogger('DataLoader')
        self.logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = Path(self.root_dir).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Create log file path with timestamp
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'stock_analysis_{timestamp}.log'
        
        # Write README.md to log directory
        readme_content = """# Stock Market Bollinger Band Analysis

This application analyzes stock market data to identify significant price movements relative to Bollinger Bands. It processes historical stock data files and identifies when prices cross the 3-sigma Bollinger Bands, indicating potential trading opportunities.

## Features

- Processes multiple stock data files in batch
- Identifies price crossings of 3-sigma Bollinger Bands
- Supports three levels of logging detail
- Generates timestamped log files
- Provides progress updates during processing
- Creates summary reports of significant price movements
- Automatically processes subdirectories containing "stock" in their name

## Requirements

- Python 3.x
- pandas
- numpy

## Usage

The main program can be run with different logging levels:

```
python bollinger_band_monitor.py [root_directory] [log_level]
```

### Arguments

- `root_directory`: Directory containing stock data files (default: current directory)
- `log_level`: Detail level of output (default: 1)
  - Level 1: Minimal output with progress and brief crossing summaries
  - Level 2: Medium detail with dates and crossing types
  - Level 3: Full detail including prices and deviations

### Example Command

```
python bollinger_band_monitor.py "C:\\Users\\simon\\Downloads\\stock_data" 1
```

## Input Data Format

The program expects stock data files with the following:
- File extension: .us.txt
- CSV format with columns: ticker, period, date, time, open, high, low, close, volume, openint
- Date format: YYYYMMDD

## Output

### Log Files
- Created in a 'logs' directory next to the data directory
- Named with timestamp: stock_analysis_YYYYMMDD_HHMMSS.log

### Sample Level 1 Output
```
Starting analysis of 100 files...
Progress: 25.0% (25/100)
Progress: 50.0% (50/100)
Progress: 75.0% (75/100)
Progress: 100.0% (100/100)

ANALYSIS SUMMARY
================================================================================
Total run time: 0:02:15

Stocks with Bollinger Band crossings in the last 2 months:
AAPL: up, down, up
GOOGL: up
MSFT: down, down

Total: 3 out of 100 stocks (3.0%) showed significant price movements
```

### Sample Level 2 Output
Includes dates and crossing types for each event.

### Sample Level 3 Output
Includes full details with prices, band values, and deviation percentages.

## Technical Details

- Calculates 20-day Simple Moving Average (SMA)
- Uses 3-sigma Bollinger Bands
- Analyzes last 2 months of data for crossings
- Processes files in batches for efficiency
- Handles missing data and errors gracefully

## Error Handling

- Skips invalid data files
- Reports processing errors in log
- Continues processing after individual file errors
- Provides error statistics in summary

## Notes

- Only processes directories containing "stock" in their name
- All subdirectories under a "stock" directory are included
- Progress updates every 5 files
- Creates new log file for each run
"""
        
        # Write README.md to log directory
        readme_path = log_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # Create formatters and handlers with just the message
        formatter = logging.Formatter('%(message)s')
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Add both handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Log file created at: {log_file}")
        self.logger.info(f"README.md created at: {readme_path}")

    def _find_data_files(self):
        """
        Recursively find all files matching the pattern.
        Once a 'stock' folder is found, include all its subfolders.
        """
        data_files = []
        root_path = Path(self.root_dir)
        
        try:
            print("\nScanning directories:")
            # First, find directories containing 'stock'
            stock_dirs = []
            for d in root_path.rglob('*'):
                if d.is_dir():
                    print(f"Visiting: {d.name}")
                    if 'stock' in d.name.lower():
                        stock_dirs.append(d)
                        # Also add all subdirectories of this stock directory
                        stock_dirs.extend([subd for subd in d.rglob('*') if subd.is_dir()])
            
            print(f"\nFound {len(stock_dirs)} directories in stock-related paths:")
            for d in stock_dirs:
                print(f"Processing directory: {d.name}")
            
            # Search for files in all identified directories
            for dir_path in stock_dirs:
                for file_path in dir_path.glob(f'*{self.file_pattern}'):
                    if file_path.is_file():
                        data_files.append(file_path)
            
            print(f"\nFound {len(data_files)} data files:")
            for file in data_files:
                print(f"- {file.parent.name}/{file.name}")
            
            return data_files
            
        except Exception as e:
            raise Exception(f"Error searching for data files: {str(e)}")

    def load_data(self, file_path):
        """Load data from a single file"""
        try:
            data = pd.read_csv(file_path, 
                             skiprows=1,
                             names=['ticker', 'period', 'date', 'time', 
                                   'open', 'high', 'low', 'close', 
                                   'volume', 'openint'])
            
            if data.empty:
                raise ValueError(f"No data found in file: {file_path}")
            
            data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
            data.set_index('date', inplace=True)
            
            columns_needed = ['open', 'high', 'low', 'close', 'volume']
            data = data[columns_needed]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading data from {file_path}: {str(e)}")
            raise

    def load_all_data(self):
        """Generator that yields data from each file"""
        for file_path in self.data_files:
            try:
                print(f"\nProcessing: {file_path.parent.name}/{file_path.name}")
                data = self.load_data(file_path)
                yield file_path.stem, data
            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}")
                continue