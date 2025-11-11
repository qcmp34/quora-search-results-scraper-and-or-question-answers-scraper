thonimport argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any

# Ensure src directory is on sys.path so we can import sibling packages
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from extractors.quora_parser import QuoraScraper  # type: ignore
from outputs.exporters import export_data  # type: ignore

def setup_logging(verbosity: int) -> logging.Logger:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logger = logging.getLogger("quora_scraper")
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger

def load_config(path: str, logger: logging.Logger) -> Dict[str, Any]:
    if not os.path.exists(path):
        logger.warning("Config file '%s' not found. Using default configuration.", path)
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.debug("Loaded configuration from %s", path)
        return config
    except Exception as exc:
        logger.error("Failed to load config '%s': %s", path, exc)
        return {}

def load_inputs(path: str, logger: logging.Logger) -> List[str]:
    if not os.path.exists(path):
        logger.error("Inputs file '%s' does not exist.", path)
        return []

    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)

    if not urls:
        logger.warning("No URLs or queries found in '%s'.", path)
    else:
        logger.info("Loaded %d URLs/queries from '%s'.", len(urls), path)
    return urls

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Quora Search Results and Question-Answers Scraper"
    )
    parser.add_argument(
        "--config",
        default=os.path.join(CURRENT_DIR, "config", "settings.example.json"),
        help="Path to JSON configuration file.",
    )
    parser.add_argument(
        "--inputs",
        default=os.path.join(os.path.dirname(CURRENT_DIR), "data", "inputs.sample.txt"),
        help="Path to the inputs text file containing search URLs or question URLs.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(CURRENT_DIR), "data"),
        help="Directory to write output files into.",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "csv", "excel", "html"],
        default="json",
        help="Primary output format.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of questions per search page to scrape.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v, -vv).",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging(args.verbose)

    config = load_config(args.config, logger)
    urls = load_inputs(args.inputs, logger)

    if not urls:
        logger.error("No work to do. Exiting.")
        return

    scraper = QuoraScraper(config=config, logger=logger)

    all_records: List[Dict[str, Any]] = []
    for url in urls:
        try:
            logger.info("Scraping: %s", url)
            records = scraper.scrape_url(url, limit_per_search=args.limit)
            logger.info("Fetched %d records from %s", len(records), url)
            all_records.extend(records)
        except Exception as exc:
            logger.exception("Error scraping '%s': %s", url, exc)

    if not all_records:
        logger.warning("No records extracted from any URL.")
        return

    os.makedirs(args.output_dir, exist_ok=True)

    base_filename = "quora_results"
    output_path = export_data(
        records=all_records,
        output_dir=args.output_dir,
        base_filename=base_filename,
        fmt=args.output_format,
    )

    logger.info("Exported %d records to %s", len(all_records), output_path)

if __name__ == "__main__":
    main()