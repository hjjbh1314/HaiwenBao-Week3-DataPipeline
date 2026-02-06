"""
Sentinel Data Cleaner - Implementation
Week 3: Data Structuring

Complete data cleaner to process scraped news articles.
"""

import pandas as pd
import json
import re
import logging
import unicodedata
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

try:
    # Prefer python-dateutil if available (as in course slides)
    from dateutil import parser as date_parser  # type: ignore
except ImportError:
    date_parser = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Clean and structure scraped news articles.
    
    Per template requirements:
    - load(): Load JSON/CSV into pandas DataFrame
    - clean(): Clean text, normalize dates, handle missing data, remove duplicates
    - validate(): Filter out invalid articles
    - save(): Save DataFrame to JSON/CSV
    - get_stats(): Return quality statistics
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
        self.generated_at = None
        
        # Track stats for get_stats()
        self._initial_count = 0
        self._dropped_incomplete = 0
        self._dropped_duplicates = 0
        self._dropped_invalid = 0
    
    def load(self) -> 'DataCleaner':
        """
        Load data from input file.
        
        Returns:
            Self for method chaining
        """
        if not self.input_file.exists():
            logger.error("Input file not found: %s", self.input_file)
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        suffix = self.input_file.suffix.lower()
        
        if suffix == ".json":
            with open(self.input_file, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            
            # Handle wrapped format: {"generated_at": ..., "articles": [...]}
            # or flat array: [...]
            if isinstance(payload, dict):
                self.generated_at = payload.get("generated_at")
                records = payload.get("articles", payload.get("data", []))
                if not isinstance(records, list):
                    records = []
            else:
                records = payload if isinstance(payload, list) else []
            
            # Filter out non-dict elements (handle malformed data gracefully)
            records = [r for r in records if isinstance(r, dict)]
            self.df = pd.DataFrame(records)
            
        elif suffix == ".csv":
            self.df = pd.read_csv(self.input_file, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported input format: {suffix} (use JSON or CSV)")
        
        self._initial_count = len(self.df) if self.df is not None else 0
        logger.info("Loaded %d rows from %s", self._initial_count, self.input_file)
        return self
    
    def clean(self) -> 'DataCleaner':
        """
        Clean the data.
        
        Pipeline:
        1. Clean text columns (title, content)
        2. Normalize dates
        3. Handle missing data
        4. Remove duplicates
        
        Returns:
            Self for method chaining
        """
        if self.df is None:
            raise RuntimeError("DataCleaner.clean() called before load()")
        
        df = self.df.copy()
        
        # Ensure expected columns exist
        for col in ["title", "content", "url", "published"]:
            if col not in df.columns:
                df[col] = ""
        
        # 1. Clean text columns (title, content)
        logger.info("Cleaning text columns...")
        for col in ["title", "content"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).apply(self._clean_text)
        
        # 2. Normalize dates
        logger.info("Normalizing dates...")
        if "published" in df.columns:
            df["published"] = df["published"].apply(self._normalize_date)
        
        # 3. Handle missing data
        logger.info("Handling missing data...")
        required = ["title", "content", "url"]
        mask_incomplete = df[required].apply(
            lambda col: col.fillna("").astype(str).str.strip().eq("")
        ).any(axis=1)
        self._dropped_incomplete = int(mask_incomplete.sum())
        if self._dropped_incomplete > 0:
            logger.info("Dropping %d records with missing required fields", self._dropped_incomplete)
        df = df.loc[~mask_incomplete].copy()
        
        # 4. Remove duplicates
        logger.info("Removing duplicates...")
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["title", "url"], keep="first")
        self._dropped_duplicates = before_dedup - len(df)
        if self._dropped_duplicates > 0:
            logger.info("Dropped %d duplicate records", self._dropped_duplicates)
        
        self.df = df
        logger.info("Cleaning complete. Remaining rows: %d", len(self.df))
        return self
    
    def validate(self) -> 'DataCleaner':
        """
        Validate data quality.
        
        Filter out invalid articles:
        - Missing title or content
        - Content too short (< 120 chars per slide 17)
        - Invalid URL format
        
        Returns:
            Self for method chaining
        """
        if self.df is None:
            raise RuntimeError("DataCleaner.validate() called before load()/clean()")
        
        df = self.df.copy()
        
        def is_valid_row(row: pd.Series) -> bool:
            """Check if a row passes all validation rules."""
            title = str(row.get("title", "") or "").strip()
            content = str(row.get("content", "") or "").strip()
            url = str(row.get("url", "") or "").strip()
            
            # Missing title or content
            if not title or not content:
                return False
            
            # Content too short (< 120 chars per slide 17)
            if len(content) < 120:
                return False
            
            # Invalid URL format (must start with http:// or https://)
            if not url or not url.startswith(("http://", "https://")):
                return False
            
            return True
        
        before_validate = len(df)
        mask_valid = df.apply(is_valid_row, axis=1)
        df_valid = df.loc[mask_valid].copy()
        
        self._dropped_invalid = before_validate - len(df_valid)
        if self._dropped_invalid > 0:
            logger.info("Validation: filtered out %d invalid records", self._dropped_invalid)
        logger.info("Validation complete. Valid records: %d", len(df_valid))
        
        self.df = df_valid
        return self
    
    def save(self, format: str = 'json') -> 'DataCleaner':
        """
        Save cleaned data.
        
        Args:
            format: Output format ('json' or 'csv')
            
        Returns:
            Self for method chaining
        """
        if self.df is None:
            raise RuntimeError("DataCleaner.save() called before load()/clean()")
        
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            records = self.df.to_dict(orient="records")
            wrapper = {
                "generated_at": self.generated_at or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "articles": records,
            }
            try:
                with open(self.output_file, "w", encoding="utf-8") as handle:
                    json.dump(wrapper, handle, ensure_ascii=False, indent=2)
                logger.info("Saved cleaned JSON to %s", self.output_file)
            except Exception as e:
                logger.error("Error saving JSON file: %s", e)
                raise
        
        elif format.lower() == 'csv':
            try:
                self.df.to_csv(self.output_file, index=False, encoding="utf-8")
                logger.info("Saved cleaned CSV to %s", self.output_file)
            except Exception as e:
                logger.error("Error saving CSV file: %s", e)
                raise
        else:
            raise ValueError(f"Unsupported output format: {format}")
        
        return self
    
    def get_stats(self) -> Dict:
        """
        Get data quality statistics.
        
        Returns:
            Dictionary with quality metrics:
            - Total articles
            - Articles with dates
            - Articles with authors (if available)
            - Average content length
            - Duplicate count
        """
        if self.df is None:
            raise RuntimeError("DataCleaner.get_stats() called before load()/clean()")
        
        df = self.df
        total = len(df)
        
        # Articles with dates
        with_dates = 0
        if "published" in df.columns:
            with_dates = int(df["published"].notna().sum())
        
        # Articles with authors (if available)
        with_authors = 0
        if "author" in df.columns:
            with_authors = int(df["author"].notna().sum())
        
        # Average content length
        avg_content_len = 0.0
        if "content" in df.columns and total > 0:
            avg_content_len = float(df["content"].fillna("").astype(str).str.len().mean())
        
        stats = {
            "total_articles": total,
            "articles_with_dates": with_dates,
            "articles_with_authors": with_authors if "author" in df.columns else None,
            "avg_content_length": round(avg_content_len, 1),
            "duplicate_count": self._dropped_duplicates,
            "dropped_incomplete": self._dropped_incomplete,
            "dropped_invalid": self._dropped_invalid,
        }
        
        logger.info("Stats: %s", stats)
        return stats
    
    def _clean_text(self, text: str) -> str:
        """
        Clean a single text string.
        
        Remove extra whitespace, HTML entities, HTML tags, normalize encoding.
        """
        if text is None:
            return ""
        
        s = str(text)
        
        # Remove HTML tags
        s = re.sub(r"<[^>]+>", "", s)
        
        # Remove common scraped artifacts (Image, Video, Credit captions)
        s = re.sub(r"\bImage\s+", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"\bVideo\s+", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"Credit\s+Credit[.\s]*", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"Credit\s*$", "", s, flags=re.IGNORECASE)
        
        # Normalize whitespace (collapse multiple spaces/newlines to single space)
        s = re.sub(r"\s+", " ", s)
        
        # HTML entities
        entity_map = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&apos;": "'",
        }
        for entity, repl in entity_map.items():
            s = s.replace(entity, repl)
        
        # Normalize text encoding (NFC)
        s = unicodedata.normalize("NFC", s)
        
        # Handle special characters (curly quotes, dashes, etc.)
        replacements = {
            "\u2018": "'",  # left single quote
            "\u2019": "'",  # right single quote
            "\u201c": '"',  # left double quote
            "\u201d": '"',  # right double quote
            "\u2013": "-",  # en dash
            "\u2014": "-",  # em dash
            "\u00a0": " ",  # non-breaking space
        }
        for old, new in replacements.items():
            s = s.replace(old, new)
        
        # Remove control characters (except \n, \t, \r)
        s = "".join(
            c for c in s
            if unicodedata.category(c) != "Cc" or c in "\n\t\r"
        )
        
        return s.strip()
    
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Normalize date to ISO format.
        
        Parse various date formats and convert to ISO (YYYY-MM-DDTHH:MM:SSZ).
        Handle missing/invalid dates by returning None.
        """
        if not date_str:
            return None
        
        s = str(date_str).strip()
        if not s:
            return None
        
        # Prefer python-dateutil if available (as in course slides)
        if date_parser is not None:
            try:
                parsed = date_parser.parse(s)
                return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, TypeError):
                pass
        
        # Fallback: try standard library parsing
        try:
            # Try RFC 2822 format (e.g., "Mon, 02 Feb 2026 23:05:29 +0000")
            if re.match(r"^\w{3},\s*\d{1,2}\s+\w{3}\s+\d{4}", s):
                dt = parsedate_to_datetime(s)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Try ISO format (e.g., "2026-01-28T05:26:24-05:00" or "2026-01-28T05:26:24Z")
            if "T" in s and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Try date-only format (e.g., "2026-01-28")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                dt = datetime.fromisoformat(s)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            pass
        
        # If all parsing fails, return None (invalid date)
        return None


# Main script that:
# 1. Creates a DataCleaner instance
# 2. Loads, cleans, validates, and saves data
# 3. Prints quality statistics
# 4. Uses argparse for CLI interface

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean scraped news articles')
    parser.add_argument('input', nargs='?', default='sample_data.json',
                       help='Input JSON/CSV file (default: sample_data.json)')
    parser.add_argument('output', nargs='?', default='cleaned_output.json',
                       help='Output file path (default: cleaned_output.json)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    
    args = parser.parse_args()
    
    # Create DataCleaner instance
    cleaner = DataCleaner(args.input, args.output)
    
    # Load, clean, validate, and save data
    cleaner.load().clean().validate().save(format=args.format)
    
    # Print quality statistics
    stats = cleaner.get_stats()
    print("\n=== Cleaning Complete ===")
    print(f"Total articles: {stats['total_articles']}")
    print(f"Articles with dates: {stats['articles_with_dates']}")
    if stats['articles_with_authors'] is not None:
        print(f"Articles with authors: {stats['articles_with_authors']}")
    print(f"Average content length: {stats['avg_content_length']} chars")
    print(f"Dropped incomplete: {stats['dropped_incomplete']}")
    print(f"Dropped duplicates: {stats['duplicate_count']}")
    print(f"Dropped invalid: {stats['dropped_invalid']}")
