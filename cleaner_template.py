"""
Sentinel Data Cleaner - Starter Template
Week 3: Data Structuring

TODO: Complete this data cleaner to process scraped news articles.
"""

import pandas as pd
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime

# TODO: Set up logging


class DataCleaner:
    """
    Clean and structure scraped news articles.
    
    TODO: Complete the implementation.
    """
    
    def __init__(self, input_file: str, output_file: str):
        """
        Initialize the data cleaner.
        
        Args:
            input_file: Path to input JSON/CSV file
            output_file: Path to output file
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.df = None
    
    def load(self) -> 'DataCleaner':
        """
        Load data from input file.
        
        Returns:
            Self for method chaining
        """
        # TODO: Load JSON or CSV file into pandas DataFrame
        # Handle file not found errors
        # Log number of articles loaded
        pass
    
    def clean(self) -> 'DataCleaner':
        """
        Clean the data.
        
        Returns:
            Self for method chaining
        """
        # TODO: Implement cleaning pipeline:
        # 1. Clean text columns (title, content)
        # 2. Normalize dates
        # 3. Handle missing data
        # 4. Remove duplicates
        # Log each step
        pass
    
    def validate(self) -> 'DataCleaner':
        """
        Validate data quality.
        
        Returns:
            Self for method chaining
        """
        # TODO: Filter out invalid articles:
        # - Missing title or content
        # - Content too short (< 100 chars)
        # - Invalid URL format
        # Log validation results
        pass
    
    def save(self, format: str = 'json') -> 'DataCleaner':
        """
        Save cleaned data.
        
        Args:
            format: Output format ('json' or 'csv')
            
        Returns:
            Self for method chaining
        """
        # TODO: Save DataFrame to JSON or CSV
        # Handle file writing errors
        # Log save completion
        pass
    
    def get_stats(self) -> Dict:
        """
        Get data quality statistics.
        
        Returns:
            Dictionary with quality metrics
        """
        # TODO: Calculate and return:
        # - Total articles
        # - Articles with dates
        # - Articles with authors (if available)
        # - Average content length
        # - Duplicate count
        pass
    
    def _clean_text(self, text: str) -> str:
        """Clean a single text string."""
        # TODO: Remove extra whitespace, HTML entities, etc.
        pass
    
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date to ISO format."""
        # TODO: Parse various date formats and convert to ISO
        # Handle missing/invalid dates
        pass


# TODO: Create main script that:
# 1. Creates a DataCleaner instance
# 2. Loads, cleans, validates, and saves data
# 3. Prints quality statistics
# 4. Uses argparse for CLI interface

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean scraped news articles')
    parser.add_argument('input', help='Input JSON/CSV file')
    parser.add_argument('output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    # TODO: Implement main logic
    pass
