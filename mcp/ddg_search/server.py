#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Server
Provides web search functionality using DuckDuckGo.
"""
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("DuckDuckGoSearch")

# Rate limiting configuration
_last_search_time = 0
_min_search_interval = 1.0  # seconds between searches

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

def _check_rate_limit():
    """Enforce rate limiting between searches."""
    global _last_search_time
    current_time = time.time()
    
    if current_time - _last_search_time < _min_search_interval:
        sleep_time = _min_search_interval - (current_time - _last_search_time)
        time.sleep(sleep_time)
    
    _last_search_time = time.time()

def _validate_search_params(query: str, max_results: int) -> Dict[str, Any]:
    """Validate search parameters."""
    if not query or not query.strip():
        return {"error": "Query cannot be empty"}
    
    if max_results < 1 or max_results > 50:
        return {"error": "max_results must be between 1 and 50"}
    
    return {}

@mcp.tool
def search_text(
    query: str, 
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for text content using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-50)
        region: Search region (e.g., "wt-wt", "us-en", "uk-en")
        safesearch: Safe search setting ("on", "moderate", "off")
        timelimit: Time limit for results ("d", "w", "m", "y")
    
    Returns:
        Dictionary containing search results and metadata
    """
    if not DDGS_AVAILABLE:
        return {
            "error": "DuckDuckGo search library not available. Install with: pip install duckduckgo-search"
        }
    
    # Validate parameters
    validation_error = _validate_search_params(query, max_results)
    if validation_error:
        return validation_error
    
    try:
        _check_rate_limit()
        
        with DDGS() as ddgs:
            results = ddgs.text(
                keywords=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results
            )
            
            return {
                "success": True,
                "query": query,
                "region": region,
                "safesearch": safesearch,
                "timelimit": timelimit,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}",
            "query": query
        }

@mcp.tool
def search_news(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for news articles using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-50)
        region: Search region (e.g., "wt-wt", "us-en", "uk-en")
        safesearch: Safe search setting ("on", "moderate", "off")
        timelimit: Time limit for results ("d", "w", "m")
    
    Returns:
        Dictionary containing news search results and metadata
    """
    if not DDGS_AVAILABLE:
        return {
            "error": "DuckDuckGo search library not available. Install with: pip install duckduckgo-search"
        }
    
    # Validate parameters
    validation_error = _validate_search_params(query, max_results)
    if validation_error:
        return validation_error
    
    try:
        _check_rate_limit()
        
        with DDGS() as ddgs:
            results = ddgs.news(
                keywords=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results
            )
            
            return {
                "success": True,
                "query": query,
                "region": region,
                "safesearch": safesearch,
                "timelimit": timelimit,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"News search failed: {str(e)}",
            "query": query
        }

@mcp.tool
def search_images(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    size: Optional[str] = None,
    color: Optional[str] = None,
    type_image: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for images using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-50)
        region: Search region (e.g., "wt-wt", "us-en", "uk-en")
        safesearch: Safe search setting ("on", "moderate", "off")
        size: Image size ("Small", "Medium", "Large", "Wallpaper")
        color: Color filter ("Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Pink", "Brown", "Black", "Gray", "Teal", "White", "Monochrome")
        type_image: Image type ("photo", "clipart", "gif", "transparent", "line")
    
    Returns:
        Dictionary containing image search results and metadata
    """
    if not DDGS_AVAILABLE:
        return {
            "error": "DuckDuckGo search library not available. Install with: pip install duckduckgo-search"
        }
    
    # Validate parameters
    validation_error = _validate_search_params(query, max_results)
    if validation_error:
        return validation_error
    
    try:
        _check_rate_limit()
        
        with DDGS() as ddgs:
            results = ddgs.images(
                keywords=query,
                region=region,
                safesearch=safesearch,
                size=size,
                color=color,
                type_image=type_image,
                max_results=max_results
            )
            
            return {
                "success": True,
                "query": query,
                "region": region,
                "safesearch": safesearch,
                "size": size,
                "color": color,
                "type_image": type_image,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Image search failed: {str(e)}",
            "query": query
        }

@mcp.tool
def search_videos(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: Optional[str] = None,
    resolution: Optional[str] = None,
    duration: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for videos using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-50)
        region: Search region (e.g., "wt-wt", "us-en", "uk-en")
        safesearch: Safe search setting ("on", "moderate", "off")
        timelimit: Time limit for results ("d", "w", "m")
        resolution: Video resolution ("high", "standard")
        duration: Video duration ("short", "medium", "long")
    
    Returns:
        Dictionary containing video search results and metadata
    """
    if not DDGS_AVAILABLE:
        return {
            "error": "DuckDuckGo search library not available. Install with: pip install duckduckgo-search"
        }
    
    # Validate parameters
    validation_error = _validate_search_params(query, max_results)
    if validation_error:
        return validation_error
    
    try:
        _check_rate_limit()
        
        with DDGS() as ddgs:
            results = ddgs.videos(
                keywords=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                resolution=resolution,
                duration=duration,
                max_results=max_results
            )
            
            return {
                "success": True,
                "query": query,
                "region": region,
                "safesearch": safesearch,
                "timelimit": timelimit,
                "resolution": resolution,
                "duration": duration,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Video search failed: {str(e)}",
            "query": query
        }

@mcp.tool
def get_search_status() -> Dict[str, Any]:
    """
    Get the current status of the DuckDuckGo search service.
    
    Returns:
        Dictionary containing service status and capabilities
    """
    return {
        "service": "DuckDuckGo Search MCP Server",
        "ddgs_library_available": DDGS_AVAILABLE,
        "rate_limiting": {
            "enabled": True,
            "min_interval_seconds": _min_search_interval
        },
        "capabilities": {
            "text_search": DDGS_AVAILABLE,
            "news_search": DDGS_AVAILABLE,
            "image_search": DDGS_AVAILABLE,
            "video_search": DDGS_AVAILABLE
        },
        "max_results_limit": 50,
        "supported_regions": [
            "wt-wt (No region)", "us-en (United States)", "uk-en (United Kingdom)",
            "de-de (Germany)", "fr-fr (France)", "es-es (Spain)", "it-it (Italy)",
            "jp-jp (Japan)", "kr-kr (Korea)", "cn-zh (China)", "ru-ru (Russia)"
        ],
        "safesearch_options": ["on", "moderate", "off"],
        "timelimit_options": ["d (day)", "w (week)", "m (month)", "y (year)"]
    }

@mcp.resource("file://search_guide")
def get_search_guide() -> str:
    """Get a comprehensive guide for using DuckDuckGo search tools."""
    guide = {
        "description": "DuckDuckGo Search MCP Server - Web search functionality",
        "installation": {
            "required_package": "duckduckgo-search",
            "install_command": "pip install duckduckgo-search"
        },
        "tools": {
            "search_text": "Search for web pages and text content",
            "search_news": "Search for news articles",
            "search_images": "Search for images with filtering options",
            "search_videos": "Search for videos with quality/duration filters",
            "get_search_status": "Check service status and capabilities"
        },
        "search_operators": {
            "exact_phrase": 'Use quotes: "cats and dogs"',
            "exclude_terms": 'Use minus: cats -dogs',
            "include_terms": 'Use plus: cats +dogs',
            "file_types": 'Use filetype: cats filetype:pdf',
            "site_search": 'Use site: dogs site:example.com',
            "title_search": 'Use intitle: intitle:dogs',
            "url_search": 'Use inurl: inurl:cats'
        },
        "parameters": {
            "region": "Search region (wt-wt for worldwide, us-en for US, etc.)",
            "safesearch": "Content filtering (on/moderate/off)",
            "timelimit": "Time filter (d/w/m/y for day/week/month/year)",
            "max_results": "Number of results (1-50)"
        },
        "rate_limiting": {
            "enabled": True,
            "min_interval": "1 second between searches",
            "purpose": "Prevent API abuse and ensure service stability"
        },
        "best_practices": [
            "Use specific keywords for better results",
            "Combine search operators for precise queries",
            "Respect rate limits to maintain service availability",
            "Check search_status before making requests",
            "Use appropriate max_results to balance speed and comprehensiveness"
        ]
    }
    return json.dumps(guide, indent=2)

@mcp.resource("file://region_codes")
def get_region_codes() -> str:
    """Get a list of supported region codes for searches."""
    regions = {
        "regions": {
            "wt-wt": "No region (worldwide)",
            "us-en": "United States",
            "uk-en": "United Kingdom", 
            "ca-en": "Canada",
            "ca-fr": "Canada (French)",
            "au-en": "Australia",
            "de-de": "Germany",
            "fr-fr": "France",
            "es-es": "Spain",
            "it-it": "Italy",
            "nl-nl": "Netherlands",
            "ru-ru": "Russia",
            "jp-jp": "Japan",
            "kr-kr": "Korea",
            "cn-zh": "China",
            "in-en": "India",
            "br-pt": "Brazil",
            "mx-es": "Mexico",
            "ar-es": "Argentina",
            "se-sv": "Sweden",
            "no-no": "Norway",
            "dk-da": "Denmark",
            "fi-fi": "Finland"
        },
        "note": "Use these codes in the 'region' parameter for localized search results"
    }
    return json.dumps(regions, indent=2)

if __name__ == "__main__":
    mcp.run()