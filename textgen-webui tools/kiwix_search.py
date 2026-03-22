tool = {
    "type": "function",
    "function": {
        "name": "kiwix_search",
        "description": "Search within specific ZIM book(s) or across all books on a Kiwix server. Supports full-text search with pattern, pagination, and multiple book filtering.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL of the kiwix server (e.g., http://127.0.0.1:8088)",
                    "default": "http://127.0.0.1:8088"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search query text to find.",
                },
                "book_name": {
                    "type": "string",
                    "description": "Specific book name to search in (from /catalog/v2/entries 'name' field). Repeatable for multiple books.",
                },
                "book_ids": {
                    "type": "string",
                    "description": "Book UUID(s) to search in. Comma-separated for multiple.",
                },
                "filter_lang": {
                    "type": "string",
                    "description": "Filter books by language before searching. Comma-separated codes.",
                },
                "filter_category": {
                    "type": "string",
                    "description": "Filter books by category. Comma-separated.",
                },
                "format": {
                    "type": "string",
                    "description": "Result format. Either 'html' or 'xml'.",
                    "enum": ["html", "xml"],
                    "default": "html"
                },
                "page_length": {
                    "type": "integer",
                    "description": "Max search results to return (max 140, default: 25).",
                    "default": 25,
                    "minimum": 1,
                    "maximum": 140
                },
                "start": {
                    "type": "integer",
                    "description": "Pagination offset. Number of results to skip.",
                    "default": 0
                }
            },
            "required": ["base_url"]
        }
    }
}


def execute(arguments):
    base_url = arguments.get("base_url", "http://127.0.0.1:8088")
    pattern = arguments.get("pattern", "")
    book_name = arguments.get("book_name")
    book_ids = arguments.get("book_ids")
    filter_lang = arguments.get("filter_lang")
    filter_category = arguments.get("filter_category")
    format_type = arguments.get("format", "html")
    page_length = arguments.get("page_length", 25)
    start = arguments.get("start", 0)

    import urllib.parse
    import requests

    # Build URL with query parameters
    params = {}

    if pattern:
        params['pattern'] = pattern
    else:
        # Allow listing search parameters even without pattern for discovery
        pass

    # Book selection - prefer book_name over book_ids, filter_ over non-filter_
    if book_name:
        params['books.name'] = book_name
    elif book_ids:
        params['books.id'] = book_ids
    elif filter_lang:
        params['books.filter.lang'] = filter_lang
    elif filter_category:
        params['books.filter.category'] = filter_category
    # If none specified, search all books

    if filter_lang and not book_name:
        params['books.filter.lang'] = filter_lang
    if filter_category and not book_name:
        params['books.filter.category'] = filter_category

    if page_length:
        params['pageLength'] = min(page_length, 140)  # Enforce max
    if start:
        params['start'] = start

    # Always request format
    params['format'] = format_type

    url = f"{base_url.rstrip('/')}/search?{urllib.parse.urlencode(params)}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)  # Longer timeout for search
        response.raise_for_status()

        result = {
            "format": format_type,
            "search_url": url,
            "results": [],
            "raw_response": ""
        }

        if format_type == "xml":
            result["xml_content"] = response.text
        else:
            # Parse HTML for structured results
            result["html_content"] = response.text

        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search kiwix server: {str(e)}", "search_url": url}
    except Exception as e:
        return {"error": f"Unexpected error during search: {str(e)}", "search_url": url}
