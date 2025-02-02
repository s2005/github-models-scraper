# GitHub Models Scraper

Automated tool for tracking and archiving GitHub Marketplace models data. The scraper runs every 6 hours and maintains a historical record of changes in the marketplace.

## Features

- Automated data collection from GitHub Marketplace
- JSON output with detailed model information
- Historical tracking of changes
- Cached requests to respect API limits
- Rich console output for local debugging

## Data Structure

The scraped data is stored in `models.json` and includes:
- Model name and ID
- Registry information
- Task type and model family
- Licensing information
- Token limits
- Supported languages and modalities
- And more

## Local Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper with default settings
python script.py

# Run with specific model family filter
python script.py -m DeepSeek

# Save output to JSON
python script.py -f json -o models.json

# Enable debug logging
python script.py -d
```

## Options

- `-o, --output`: Output JSON file path
- `-m, --model-family`: Filter by model family
- `-f, --format`: Output format (table/json)
- `-d, --debug`: Enable debug logging
- `--cache-dir`: Cache directory path
- `--cache-timeout`: Cache timeout in seconds

## Automated Updates

This repository uses GitHub Actions to automatically run the scraper every 6 hours. The workflow:
1. Runs the scraper
2. Checks for changes in the data
3. Commits and pushes updates if changes are found

## License

MIT