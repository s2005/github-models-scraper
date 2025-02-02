# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.7.0",
#     "pydantic>=2.5.0",
#     "requests>=2.31.0"
# ]
# ///

from typing import List, Optional, Generator, Any
import click
from rich.console import Console
from rich.table import Table
from pydantic import BaseModel
import requests
import json
from pathlib import Path
import logging
from rich.logging import RichHandler
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("github_marketplace")

console = Console()

class CacheError(Exception):
    """Custom exception for cache-related errors."""
    pass

class GithubModels(BaseModel):
    """Configuration for GitHub models fetching."""
    GITHUB_MARKETPLACE_BASE_URL: str = "https://github.com/marketplace"
    model_family: Optional[str] = None
    type: str = "models"
    cache_dir: Path = Path("cache")
    cache_timeout: int = 3600  # 1 hour default cache timeout

def get_cache_path(config: GithubModels, page: int) -> Path:
    """Generate cache file path for a specific page."""
    cache_key = f"models_page{page}"
    if config.model_family:
        cache_key += f"_{config.model_family}"
    return config.cache_dir / f"{cache_key}.json"

def load_cached_data(cache_path: Path, cache_timeout: int) -> Optional[dict]:
    """Load data from cache if it exists and is not expired."""
    try:
        if not cache_path.is_file():
            return None

        # Check cache age
        mod_time = cache_path.stat().st_mtime
        if time.time() - mod_time > cache_timeout:
            logger.debug(f"Cache expired for {cache_path}")
            return None

        logger.info(f"Using cached data from: {cache_path}")
        with cache_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Successfully loaded cache from {cache_path}")
            return data

    except Exception as e:
        logger.warning(f"Error loading cache {cache_path}: {str(e)}")
        return None

def save_to_cache(data: Any, cache_path: Path) -> None:
    """Save data to cache file."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved to cache: {cache_path}")
    except Exception as e:
        logger.error(f"Error saving to cache {cache_path}: {str(e)}")
        raise CacheError(f"Failed to save cache: {str(e)}")

def fetch_page_with_cache(url: str, params: dict, headers: dict, cache_path: Path, cache_timeout: int) -> tuple[List[dict], bool]:
    """Fetch a page with caching support."""
    # Try to load from cache first
    cached_data = load_cached_data(cache_path, cache_timeout)
    if cached_data is not None:
        logger.debug("Using cached data")
        return cached_data.get("models", []), cached_data.get("has_next_page", False)

    # If no cache or expired, fetch from API
    try:
        logger.debug(f"Making request to {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        # Log first 1000 chars to avoid huge logs
        logger.debug(f"Raw response: {response.text[:1000]}...")
        
        data = response.json()
        models = data.get("results", [])

        # Check if there's a next page by looking at the response
        # GitHub usually returns 20 items per page
        has_next_page = bool(data.get("next_page_url") or (len(models) == 20))

        # Save to cache
        cache_data = {
            "models": models,
            "has_next_page": has_next_page,
            "cached_at": datetime.now().isoformat()
        }
        save_to_cache(cache_data, cache_path)
        
        return models, has_next_page

    except Exception as e:
        logger.error(f"Error fetching page: {str(e)}")
        
        # If fetch fails but we have expired cache, use it as fallback
        if cache_path.exists():
            logger.warning("Fetch failed, using expired cache as fallback")
            cached_data = load_cached_data(cache_path, float('inf'))  # Ignore timeout for fallback
            if cached_data:
                return cached_data.get("models", []), cached_data.get("has_next_page", False)
            
        raise CacheError(f"Failed to fetch data and no cache available at {cache_path}")

def get_marketplace_models(config: GithubModels) -> Generator[dict, None, None]:
    """
    Fetch all models from GitHub marketplace using pagination and caching.
    
    Args:
        config: GithubModels configuration
        
    Yields:
        Models one at a time as they are fetched
    """    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    
    page = 1
    total_models = 0
    
    while True:
        params = {"type": config.type, "page": page}
        if config.model_family:
            params["model_family"] = config.model_family

        cache_path = get_cache_path(config, page)
        try:
            models, has_next_page = fetch_page_with_cache(
                config.GITHUB_MARKETPLACE_BASE_URL,
                params,
                headers,
                cache_path,
                config.cache_timeout
            )
            
            for model in models:
                total_models += 1
                logger.debug(f"Found model {total_models} on page {page}")
                
                yield {
                    "id": model.get("original_name", model.get("name")),
                    "registry": model.get("registry", ""),
                    "name": model.get("friendly_name", model.get("name")),
                    "original_name": model.get("original_name", model.get("name")),
                    "friendly_name": model.get("friendly_name", model.get("name")),
                    "task": model.get("task", "unknown"),
                    "publisher": model.get("publisher", ""),
                    "license": model.get("license", ""),
                    "description": model.get("description", ""),                
                    "summary": model.get("summary", ""),
                    "model_family": model.get("model_family", "unknown"),
                    "model_version": model.get("model_version", ""),
                    "notes": model.get("notes", ""),
                    "tags": model.get("tags", []),
                    "rate_limit_tier": model.get("rate_limit_tier", ""),
                    "supported_languages": model.get("supported_languages", []),
                    "max_output_tokens": model.get("max_output_tokens", ""),
                    "max_input_tokens": model.get("max_input_tokens", ""),
                    "training_data_date": model.get("training_data_date", ""),
                    "evaluation": model.get("evaluation", ""),
                    "license_description": model.get("license_description", ""),
                    "static_model": model.get("static_model", False),
                    "supported_input_modalities": model.get("supported_input_modalities", []),
                    "type": model.get("type", ""),
                    "model_url": model.get("model_url", ""),
                    "page": page
                }
            
            if not has_next_page or not models:
                break
                
            page += 1
            logger.debug(f"Moving to page {page}")
            
        except CacheError as e:
            logger.error(f"Cache error on page {page}: {str(e)}")
            break

def save_to_json(data: List[dict], output_file: Path) -> None:
    """Save models data to JSON file."""
    try:
        logger.debug(f"Saving data to {output_file}")
        output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        logger.info(f"Data saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}", exc_info=True)

def display_models(models: List[dict]) -> None:
    """Display models in a formatted table."""
    logger.debug("Preparing to display models in table format")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Task")
    table.add_column("Model Family")
    table.add_column("Description")
    table.add_column("Page")

    for model in models:
        table.add_row(
            model['name'],
            model['task'],
            model['model_family'],
            model['description'][:100] + '...' if len(model['description']) > 100 else model['description'],
            str(model['page'])
        )

    console.print(table)

@click.command()
@click.option('--output', '-o', 
              type=click.Path(path_type=Path),
              help='Output JSON file path')
@click.option('--model-family', '-m',
              help='Filter by model family (e.g., DeepSeek)')
@click.option('--format', '-f',
              type=click.Choice(['table', 'json']), 
              default='table',
              help='Output format (default: table)')
@click.option('--debug', '-d',
              is_flag=True,
              help='Enable debug logging')
@click.option('--cache-dir', 
              type=click.Path(path_type=Path),
              default='.cache',
              help='Cache directory path')
@click.option('--cache-timeout', 
              type=int,
              default=3600,
              help='Cache timeout in seconds (default: 1 hour)')
def main(output: Optional[Path], 
         model_family: Optional[str], 
         format: str, 
         debug: bool,
         cache_dir: Path,
         cache_timeout: int) -> None:
    """
    Fetch and display models from GitHub marketplace.
    
    Example:
        python script.py -m DeepSeek -f json -o models.json -d --cache-timeout 7200
    """
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    config = GithubModels(
        model_family=model_family,
        cache_dir=cache_dir,
        cache_timeout=cache_timeout
    )
    
    logger.info("Fetching models from GitHub marketplace...")
    models = list(get_marketplace_models(config))
    
    if not models:
        logger.warning("No models found")
        return

    if format == 'table':
        display_models(models)
    
    if output:
        save_to_json(models, output)
        
    logger.info(f"Found {len(models)} models across {max(model['page'] for model in models)} pages")

if __name__ == '__main__':
    main()
