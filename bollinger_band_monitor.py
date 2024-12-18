from data_loader import DataLoader
from technical_indicators import TechnicalIndicators
import pandas as pd
import logging
import time
from datetime import timedelta

def monitor_bollinger_bands(root_dir, file_pattern='.us.txt', log_level=1):
    """
    Monitor stock price movements relative to 3-sigma Bollinger Bands for multiple stocks.
    
    Parameters:
    root_dir (str): Root directory to search for data files
    file_pattern (str): Pattern to match data files (default: '.us.txt')
    log_level (int): Logging detail level (1=minimal [default], 2=medium, 3=detailed)
    """
    crossing_details = {}
    files_processed = 0
    files_with_errors = 0
    start_time = time.time()  # Start timing
    
    try:
        # Initialize data loader
        loader = DataLoader(root_dir, file_pattern)
        logger = loader.logger
        total_files = len(loader.data_files)
        
        logger.info(f"\nStarting analysis of {total_files} files...")
        
        # Process each data file
        for symbol, data in loader.load_all_data():
            files_processed += 1
            progress_pct = (files_processed / total_files) * 100
            
            # Level 1: Show progress percentage every 5 files or at completion
            if log_level == 1:
                if files_processed % 5 == 0 or files_processed == total_files:
                    logger.info(f"Progress: {progress_pct:.1f}% ({files_processed}/{total_files})")
            
            # Level 2 & 3: Show detailed progress
            else:
                logger.info("\n" + "="*80)
                logger.info(f"Analyzing {symbol} ({files_processed}/{total_files})")
                logger.info("="*80)
                
                if log_level == 3:
                    logger.info("Data Overview:")
                    logger.info(f"Columns available: {data.columns.tolist()}")
                    logger.info(f"\nAnalysis period:")
                    logger.info(f"From: {data.index[0].strftime('%Y-%m-%d')}")
                    logger.info(f"To:   {data.index[-1].strftime('%Y-%m-%d')}")
            
            # Technical Analysis
            try:
                ti = TechnicalIndicators(data)
                data['SMA_20'] = ti.sma(20)
                data['EMA_20'] = ti.ema(20)
                data['RSI'] = ti.rsi()
                macd_data = ti.macd()
                data = pd.concat([data, macd_data], axis=1)
                bb_data = ti.bollinger_bands()
                data = pd.concat([data, bb_data], axis=1)
                
                events = ti.check_recent_bb_crossings(months=2)
                if events:
                    crossing_details[symbol] = events
                    
                if log_level == 3:
                    logger.info(f"\nAnalyzing price movements outside 3-sigma Bollinger Bands for {symbol}...")
                    ti.print_bb_crossings(months=2, logger=logger)
                
            except Exception as e:
                files_with_errors += 1
                if log_level >= 2:
                    logger.error(f"Error in technical analysis for {symbol}: {str(e)}")
                continue
        
        # Calculate elapsed time
        end_time = time.time()
        elapsed_time = timedelta(seconds=int(end_time - start_time))
        
        # Summary section
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS SUMMARY")
        logger.info("="*80)
        logger.info(f"\nTotal run time: {elapsed_time}")
        
        # Level 2 & 3: Show processing statistics
        if log_level >= 2:
            logger.info("\nProcessing Statistics:")
            logger.info(f"Total files found:     {total_files}")
            logger.info(f"Files processed:       {files_processed}")
            logger.info(f"Files with errors:     {files_with_errors}")
            logger.info(f"Successful analysis:   {files_processed - files_with_errors}")
        
        # All levels: Show crossing summary without timestamps
        if crossing_details:
            logger.info("\nStocks with Bollinger Band crossings in the last 2 months:")
            
            if log_level == 1:
                for symbol, events in crossing_details.items():
                    sorted_events = sorted(events, key=lambda x: x['date'])
                    crossing_sequence = []
                    for event in sorted_events:
                        if 'Above' in event['type']:
                            crossing_sequence.append('up')
                        else:
                            crossing_sequence.append('down')
                    sequence_str = ', '.join(crossing_sequence)
                    logger.info(f"{symbol}: {sequence_str}")
            
            elif log_level == 2:
                for symbol, events in crossing_details.items():
                    logger.info(f"\n{symbol}:")
                    for event in events:
                        date_str = event['date'].strftime('%Y-%m-%d')
                        logger.info(f"  {date_str} - {event['type']}")
            
            else:  # level 3
                logger.info("-" * 120)
                for symbol, events in crossing_details.items():
                    logger.info(f"\n{symbol}:")
                    for event in events:
                        date_str = event['date'].strftime('%Y-%m-%d')
                        logger.info(f"  {date_str} - {event['type']} "
                                   f"(Price: {event['price']:.2f}, "
                                   f"Band: {event['band_value']:.2f}, "
                                   f"Deviation: {event['deviation']:.2f}%)")
            
            logger.info(f"\nTotal: {len(crossing_details)} out of {files_processed} "
                       f"stocks ({(len(crossing_details)/files_processed)*100:.1f}%) "
                       f"showed significant price movements")
        else:
            logger.info("\nNo stocks found with Bollinger Band crossings in the last 2 months "
                       f"out of {files_processed} stocks analyzed.")
            
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        return

if __name__ == "__main__":
    root_directory = r"C:\Users\simon\Downloads\a\llm_projects\stock_project\d_us_txt__mini"
    monitor_bollinger_bands(root_directory, log_level=1)
  