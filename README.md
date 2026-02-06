# Data Cleaning and Validation Pipeline

**Author:** Haiwen Bao  
**Assignment:** Week 3 – Data Pipeline (IIMT3688)

## Overview

This repository implements a **data cleaning and validation pipeline** that processes raw scraped article data (e.g. New York Times) into clean, structured JSON and produces a quality report. It fulfils:

- **Data cleaning:** whitespace, HTML artifacts, encoding, dates (ISO), special characters  
- **Data validation:** required fields (title, content, url), URL format, content length minimums, invalid records flagged with reasons  
- **Quality report:** four metrics — (1) total records processed, (2) valid vs invalid counts, (3) completeness per field (%), (4) common validation failures  

## Requirements

- **Python 3.8+**
- **pandas** (for DataCleaner class)
- **python-dateutil** (optional, for better date parsing; falls back to standard library if not available)

## How to Run

1. **Cleaning** (raw → cleaned):  
   ```bash
   python cleaner.py
   ```  
   Or with arguments (per template argparse requirement):
   ```bash
   python cleaner.py sample_data.json cleaned_output.json --format json
   ```  
   Reads `sample_data.json` (default), writes `cleaned_output.json` (default, only valid records).

2. **Validation and quality report:**  
   ```bash
   python validator.py
   ```  
   Reads `sample_data.json` (original input) to generate `validation_result.json` and `quality_report.txt`.

Run from the directory containing `cleaner.py` and `validator.py`.

## Deliverables (File Descriptions)

| File | Description |
|------|-------------|
| `cleaner.py` | Data cleaning implementation using `DataCleaner` class (per template): load, clean, validate, save. |
| `validator.py` | Validation implementation (required fields, URL format, length minimums) and quality report generation. |
| `sample_data.json` | Sample input: raw scraped articles (`articles` array with `url`, `title`, `content`, `published`). |
| `cleaned_output.json` | Cleaned output: **only valid records** (after cleaning and validation filtering). |
| `quality_report.txt` | Generated report: total records; valid vs invalid counts; completeness per field (%); common validation failures. |
| `README.md` | This documentation. |
| `prompt-log.md` | AI-assisted development process and task log. |

## Data Format

- **Input/cleaned JSON:** `{ "generated_at": "<ISO date>", "articles": [ { "url", "title", "content", "published" }, ... ] }`  
- **Validation rules:** `title`, `content`, `url` required and non-empty; URL must be `http`/`https` with valid host; content length >= 120 characters (per course slides).

## Edge Cases Handled

- **Cleaner:** Missing or non-string fields → empty string; malformed dates → normalized to ISO or None; non-dict items in `articles` → filtered out during load.  
- **Validator:** Non-dict records and missing/invalid fields produce clear error reasons in validation results and in the quality report.

## Validation & Outputs Semantics

Per course template and slides (Week 3, slide 17), the `validate()` method in `DataCleaner` **filters out invalid articles**. Therefore:

- **`cleaned_output.json`**  
  - Contains **only valid records** that passed all validation checks:
    - Required fields present (title, content, url)
    - Content length >= 120 characters (per slide 17)
    - URL format valid (starts with http:// or https://)
  - This ensures the cleaned data is ready for Week 4 downstream analysis.

- **`validation_result.json`**  
  - Validates the **original input** (`sample_data.json`) to show all records, including those filtered out.
  - For each record, provides: `index`, `valid` (bool) and `reasons` (list of failure messages).  
  - Use this to see which records were filtered and why.

- **`quality_report.txt`**  
  - Reports on the **original input** (`sample_data.json`): total processed, valid/invalid counts, completeness %, common failures, and additional metrics.
  - Shows how many records were filtered during cleaning/validation.
  - When `invalid == 0`, includes *"All records passed validation."* and *"No validation failures detected."*.

> **Pipeline flow** (per template):  
> 1. `load()` → Load raw data  
> 2. `clean()` → Clean text, normalize dates, handle missing data, remove duplicates  
> 3. `validate()` → **Filter out invalid articles** (per template requirement)  
> 4. `save()` → Export only valid records to `cleaned_output.json`  
> 
> The separate `validator.py` reads the original `sample_data.json` to generate a comprehensive quality report showing all records (including filtered ones).
