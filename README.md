# GitHub Models Scraper

Automated tool for tracking and archiving GitHub Marketplace models data. The scraper runs every 6 hours and maintains a historical record of changes in the marketplace.

## Features

- Automated data collection from GitHub Marketplace
- JSON output with detailed model information
- Historical tracking of changes
- Cached requests to respect API limits
- Rich console output for local debugging

## Installation and Usage

### Using uv (Recommended)

The script uses PEP 723 inline script dependencies, which works seamlessly with `uv run`:

```bash
# Install uv if you haven't already
pip install uv

# Run the script directly - uv will handle dependencies
uv run script.py
```

The script includes this magic comment header:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.7.0",
#     "pydantic>=2.5.0",
#     "requests>=2.31.0"
# ]
# ///
```

`uv` will automatically create a temporary virtual environment with these dependencies installed. This process takes just a few milliseconds once the `uv` cache has been populated.

### Traditional Installation

If you prefer not to use `uv`, you can install dependencies traditionally:

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
- `--cache-dir`: Cache directory path (default: .cache)
- `--cache-timeout`: Cache timeout in seconds

## Data Structure

The scraped data is stored in `models.json` and includes:
- Model name and ID
- Registry information
- Task type and model family
- Licensing information
- Token limits
- Supported languages and modalities
- And more

## Automated Updates

This repository uses GitHub Actions to automatically run the scraper once per day. The workflow:
1. Runs the scraper
2. Checks for changes in the data
3. Commits and pushes updates if changes are found

## Acknowledgments

This project was inspired by and builds upon the work of several excellent resources:

- [Simon Willison](https://simonwillison.net/) - For his pioneering work on GitHub scraping tools and workflows, particularly the [openai-models scraper](https://github.com/simonw/scrape-openai-models)
- [OpenWebUI community](https://openwebui.com/), specifically [@theonehong's models scraper](https://openwebui.com/f/theonehong/github_market_models_manifold) - For insights into marketplace data structure
- [Anthropic Claude 3.5](https://www.anthropic.com/claude) - For assistance in code development and optimization

## License

MIT
