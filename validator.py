"""
Data validation implementation for cleaned article records.
Checks required fields, URL format, content length minimums; flags invalid records with reasons.
"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


# Default minimum lengths (configurable)
# Per course slides (Week 3, slide 17): Content length >= 120 characters
DEFAULT_TITLE_MIN_LENGTH = 1
DEFAULT_CONTENT_MIN_LENGTH = 120

REQUIRED_FIELDS = ("title", "content", "url")
VALID_URL_SCHEMES = ("http", "https")


def check_required_fields(article: dict) -> list[str]:
    """Check that title, content, url exist and are non-empty. Returns list of violation reasons."""
    reasons = []
    for field in REQUIRED_FIELDS:
        value = article.get(field)
        if value is None:
            reasons.append(f"missing required field: '{field}'")
        elif not isinstance(value, str):
            reasons.append(f"field '{field}' must be a string")
        elif not value.strip():
            reasons.append(f"required field '{field}' is empty")
    return reasons


def validate_url_format(url: str) -> list[str]:
    """Validate URL has http/https scheme and valid netloc. Returns list of violation reasons."""
    reasons = []
    if not url or not isinstance(url, str):
        reasons.append("url is missing or not a string")
        return reasons
    url = url.strip()
    if not url:
        reasons.append("url is empty")
        return reasons
    try:
        parsed = urlparse(url)
        if parsed.scheme not in VALID_URL_SCHEMES:
            reasons.append(f"url must use scheme http or https, got: {parsed.scheme or '(none)'}")
        if not parsed.netloc:
            reasons.append("url has no host (netloc)")
        # Basic sanity: netloc should look like a domain (has a dot or is localhost)
        if parsed.netloc and "." not in parsed.netloc and parsed.netloc.lower() != "localhost":
            reasons.append("url netloc does not look like a valid host")
    except Exception as e:
        reasons.append(f"url parse error: {e}")
    return reasons


def check_content_length_minimums(
    article: dict,
    title_min_length: int = DEFAULT_TITLE_MIN_LENGTH,
    content_min_length: int = DEFAULT_CONTENT_MIN_LENGTH,
) -> list[str]:
    """Check title and content meet minimum length. Returns list of violation reasons."""
    reasons = []
    title = article.get("title")
    content = article.get("content")
    if title is not None and isinstance(title, str):
        if len(title.strip()) < title_min_length:
            reasons.append(
                f"title length {len(title.strip())} below minimum {title_min_length}"
            )
    if content is not None and isinstance(content, str):
        if len(content.strip()) < content_min_length:
            reasons.append(
                f"content length {len(content.strip())} below minimum {content_min_length}"
            )
    return reasons


def validate_record(
    article: dict,
    index: int,
    title_min_length: int = DEFAULT_TITLE_MIN_LENGTH,
    content_min_length: int = DEFAULT_CONTENT_MIN_LENGTH,
) -> dict[str, Any]:
    """
    Validate a single article. Returns dict with keys:
    - index: int
    - valid: bool
    - reasons: list[str] (empty if valid)
    - record_summary: optional short description (url or title) for reporting
    """
    all_reasons: list[str] = []

    if not isinstance(article, dict):
        return {
            "index": index,
            "valid": False,
            "reasons": ["record is not a valid object (expected dict)"],
            "record_summary": str(article)[:80] if article is not None else f"index {index}",
        }

    all_reasons.extend(check_required_fields(article))
    url = article.get("url") if isinstance(article.get("url"), str) else ""
    all_reasons.extend(validate_url_format(url))
    all_reasons.extend(
        check_content_length_minimums(
            article,
            title_min_length=title_min_length,
            content_min_length=content_min_length,
        )
    )

    record_summary = (article.get("url") or article.get("title") or str(index))[:80]
    if isinstance(record_summary, str) and len(record_summary) > 80:
        record_summary = record_summary[:77] + "..."

    return {
        "index": index,
        "valid": len(all_reasons) == 0,
        "reasons": all_reasons,
        "record_summary": record_summary,
    }


def validate_articles(
    articles: list[dict],
    title_min_length: int = DEFAULT_TITLE_MIN_LENGTH,
    content_min_length: int = DEFAULT_CONTENT_MIN_LENGTH,
) -> dict[str, Any]:
    """
    Validate a list of articles. Returns dict with:
    - total: int
    - valid_count: int
    - invalid_count: int
    - results: list of per-record validation result dicts
    - invalid_records: list of results for invalid records only (with reasons)
    """
    if not isinstance(articles, list):
        articles = []
    results = [
        validate_record(a, i, title_min_length=title_min_length, content_min_length=content_min_length)
        for i, a in enumerate(articles)
    ]
    valid_count = sum(1 for r in results if r["valid"])
    invalid_records = [r for r in results if not r["valid"]]
    return {
        "total": len(articles),
        "valid_count": valid_count,
        "invalid_count": len(invalid_records),
        "results": results,
        "invalid_records": invalid_records,
    }


def load_json(path: Path) -> dict:
    """Load JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_validation(
    input_path: str | Path,
    output_path: str | Path | None = None,
    title_min_length: int = DEFAULT_TITLE_MIN_LENGTH,
    content_min_length: int = DEFAULT_CONTENT_MIN_LENGTH,
) -> dict[str, Any]:
    """
    Load JSON from input_path (expects { "articles": [ ... ] } or list of articles),
    run validation, optionally write validation report to output_path.
    Returns the validation result dict.
    """
    input_path = Path(input_path)
    data = load_json(input_path)
    articles = data.get("articles", data) if isinstance(data, dict) else data
    if not isinstance(articles, list):
        articles = []
    result = validate_articles(
        articles,
        title_min_length=title_min_length,
        content_min_length=content_min_length,
    )
    if output_path:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def format_validation_report(result: dict[str, Any]) -> str:
    """Produce a human-readable validation report (e.g. for quality_report or console)."""
    lines = [
        "=== Data Validation Report ===",
        f"Total records:  {result['total']}",
        f"Valid:         {result['valid_count']}",
        f"Invalid:       {result['invalid_count']}",
        "",
    ]
    if result["invalid_records"]:
        lines.append("Invalid records (with reasons):")
        for r in result["invalid_records"]:
            lines.append(f"  Index {r['index']}: {r['record_summary']}")
            for reason in r["reasons"]:
                lines.append(f"    - {reason}")
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quality Report
# ---------------------------------------------------------------------------

FIELDS_FOR_COMPLETENESS = ("url", "title", "content", "published")


def _completeness_per_field(articles: list[dict]) -> dict[str, float]:
    """Compute completeness percentage per field (non-empty value). Returns dict field -> percentage 0-100."""
    total = len(articles)
    if total == 0:
        return {f: 0.0 for f in FIELDS_FOR_COMPLETENESS}
    counts: dict[str, int] = {f: 0 for f in FIELDS_FOR_COMPLETENESS}
    for a in articles:
        if not isinstance(a, dict):
            continue
        for field in FIELDS_FOR_COMPLETENESS:
            val = a.get(field)
            if val is not None and isinstance(val, str) and val.strip():
                counts[field] += 1
            elif val is not None and not isinstance(val, str):
                counts[field] += 1  # e.g. number
    return {f: round(100.0 * counts[f] / total, 1) for f in FIELDS_FOR_COMPLETENESS}


def _common_validation_failures(validation_result: dict[str, Any]) -> list[tuple[str, int]]:
    """Aggregate validation reasons from invalid_records. Returns list of (reason, count) sorted by count desc."""
    reasons: list[str] = []
    for r in validation_result.get("invalid_records", []):
        reasons.extend(r.get("reasons", []))
    counts = Counter(reasons)
    return counts.most_common()


def _additional_metrics(articles: list[dict]) -> dict[str, Any]:
    """Compute optional metrics: date range (published), avg content length."""
    dates: list[str] = []
    content_lengths: list[int] = []
    for a in articles if isinstance(articles, list) else []:
        if not isinstance(a, dict):
            continue
        pub = a.get("published")
        if pub and isinstance(pub, str) and pub.strip():
            dates.append(pub.strip())
        content = a.get("content")
        if content is not None and isinstance(content, str):
            content_lengths.append(len(content.strip()))
    date_range = ""
    if dates:
        try:
            parsed = [datetime.fromisoformat(d.replace("Z", "+00:00")[:19]) for d in dates]
            min_d, max_d = min(parsed), max(parsed)
            date_range = f"{min_d.date()} to {max_d.date()}"
        except (ValueError, TypeError):
            date_range = f"{len(dates)} records with dates"
    avg_content = round(sum(content_lengths) / len(content_lengths), 0) if content_lengths else 0
    return {"date_range": date_range, "avg_content_length_chars": int(avg_content)}


def generate_quality_report(
    cleaned_data_path: str | Path,
    validation_result: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Generate quality_report.txt with:
    - Total records processed
    - Valid vs. invalid counts
    - Completeness percentage per field
    - Common validation failures (reason and count)
    """
    cleaned_data_path = Path(cleaned_data_path)
    output_path = Path(output_path)
    data = load_json(cleaned_data_path)
    articles = data.get("articles", data) if isinstance(data, dict) else data
    if not isinstance(articles, list):
        articles = []
    total = validation_result.get("total", len(articles))
    valid_count = validation_result.get("valid_count", 0)
    invalid_count = validation_result.get("invalid_count", 0)
    completeness = _completeness_per_field(articles)
    common_failures = _common_validation_failures(validation_result)
    extra = _additional_metrics(articles)

    lines = [
        "==========================================",
        "         DATA QUALITY REPORT",
        "==========================================",
        "",
        "1. RECORDS PROCESSED",
        "   Total records processed:  " + str(total),
        "   Valid:                    " + str(valid_count),
        "   Invalid:                  " + str(invalid_count),
        "",
    ]
    if invalid_count == 0 and total > 0:
        lines.append("   All records passed validation.")
        lines.append("")
    lines.extend([
        "2. COMPLETENESS PER FIELD (%)",
        "   (Percentage of records with non-empty value)",
        "",
    ])
    for field in FIELDS_FOR_COMPLETENESS:
        lines.append(f"   {field:12}  {completeness[field]:5.1f}%")
    lines.extend([
        "",
        "3. COMMON VALIDATION FAILURES",
        "   (Reason and count across invalid records)",
        "",
    ])
    if common_failures:
        for reason, count in common_failures:
            lines.append(f"   [{count:3}]  {reason}")
    else:
        lines.append("   No validation failures detected.")
    lines.extend([
        "",
        "4. ADDITIONAL METRICS",
        "   Date range (published):   " + (extra.get("date_range") or "N/A"),
        "   Avg content length:      " + str(extra.get("avg_content_length_chars", 0)) + " chars",
        "",
        "==========================================",
    ])

    text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Main entrypoint for validation and quality report generation.
    
    Reads the original sample_data.json (before cleaning) to generate
    a comprehensive quality report that includes all records, including
    those that were filtered out during cleaning.
    """
    base = Path(__file__).resolve().parent
    # Read original input to see all records (including invalid ones)
    original_input = base / "sample_data.json"
    # Also read cleaned output to compute completeness on cleaned data
    cleaned_input = base / "cleaned_output.json"
    output_file = base / "validation_result.json"
    quality_report_file = base / "quality_report.txt"

    if not original_input.exists():
        print(f"Original input file not found: {original_input}")
        return

    # Validate the original input to see all records
    result = run_validation(original_input, output_path=output_file)
    print(format_validation_report(result))
    print(f"Detailed result written to: {output_file}")

    # Generate quality report using cleaned data for completeness metrics
    # but validation results from original data
    report_input = cleaned_input if cleaned_input.exists() else original_input
    generate_quality_report(report_input, result, quality_report_file)
    print(f"Quality report written to: {quality_report_file}")


if __name__ == "__main__":
    main()
