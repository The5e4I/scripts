from modules.web_search import truncate_content_by_tokens

tool = {
    "type": "function",
    "function": {
        "name": "kiwix_fetch_article",
        "description": "Fetch the full content of an article from a ZIM book. Returns the article as HTML or markdown text with configurable token limits.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL of the kiwix server (e.g., http://127.0.0.1:8088)",
                    "default": "http://127.0.0.1:8088"
                },
                "book_name": {
                    "type": "string",
                    "description": "The ZIM book name (from /catalog/v2/entries 'name' field).",
                },
                "path": {
                    "type": "string",
                    "description": "Path to article within the ZIM file (e.g., 'A/Apple', 'wiki/A/Botany'). Use empty or '/' for main page.",
                    "default": ""
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum number of tokens to return. Use -1 for unlimited (up to server limits).",
                    "default": 8192
                },
                "convert_to_markdown": {
                    "type": "boolean",
                    "description": "Convert HTML response to markdown.",
                    "default": True
                },
                "use_raw": {
                    "type": "boolean",
                    "description": "Use /raw endpoint (guaranteed no server processing) vs /content.",
                    "default": False
                }
            },
            "required": ["base_url", "book_name"]
        }
    }
}


def execute(arguments):
    base_url = arguments.get("base_url", "http://127.0.0.1:8088")
    book_name = arguments.get("book_name", "")
    path = arguments.get("path", "").lstrip('/')
    max_tokens = arguments.get("max_tokens", 8192)
    convert_to_markdown = arguments.get("convert_to_markdown", True)
    use_raw = arguments.get("use_raw", False)

    import urllib.parse
    import requests

    # Build content URL
    # For main page of ZIM: path can be empty or "/"
    if not path:
        article_path = book_name  # /content/BOOK_NAME redirects to main page
    elif path == "/":
        article_path = f"{book_name}/"  # /content/BOOK_NAME/ also works
    else:
        article_path = f"{book_name}/{path}"

    if use_raw:
        url = f"{base_url.rstrip('/')}/raw/{urllib.parse.quote_plus(book_name)}/content/{urllib.parse.quote_plus(path) if path else ''}"
        # Fix empty path for raw
        if not path:
            url = f"{base_url.rstrip('/')}/raw/{urllib.parse.quote_plus(book_name)}/"
    else:
        if path:
            url = f"{base_url.rstrip('/')}/content/{urllib.parse.quote_plus(article_path)}"
        else:
            url = f"{base_url.rstrip('/')}/content/{urllib.parse.quote_plus(book_name)}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)  # Very long timeout for large content

        # Check for HTTP errors
        if response.status_code >= 400:
            return {
                "error": f"Failed to fetch article. HTTP {response.status_code}",
                "status_code": response.status_code,
                "url": url,
                "message": response.text[:200]
            }

        if response.status_code >= 300 and response.status_code < 400:
            return {
                "error": f"Redirect received: {response.status_code}",
                "url": url,
                "redirect_url": response.headers.get('Location', ''),
                "status_code": response.status_code
            }

        html_content = response.text

        # Convert to markdown if requested
        content_to_process = html_content

        if convert_to_markdown:
            try:
                # Import trafilatura like the fetch_webpage tool does
                import trafilatura
                content_to_process = trafilatura.extract(
                    html_content,
                    output_format='markdown',
                    url=url
                ) or html_content
            except ImportError:
                pass  # Skip conversion if trafilatura not available
            except Exception:
                pass  # Use original HTML on failure

        # Truncate if token limit specified
        if max_tokens > 0:
            content = truncate_content_by_tokens(content_to_process, max_tokens=max_tokens)
        else:
            content = content_to_process

        # Extract title from response if possible
        import re
        title = book_name
        title_match = re.search(r'<title>([^<]+)</title>', html_content)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Try to find first H1
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
            if h1_match:
                title = h1_match.group(1).strip()

        return {
            "title": title,
            "book_name": book_name,
            "url": url,
            "path": path if path else "/",
            "content": content,
            "raw_content": html_content if not convert_to_markdown else None,
            "size_chars": len(content)
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": f"Network error fetching article: {str(e)}",
            "url": url,
            "book_name": book_name,
            "path": path
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "url": url,
            "book_name": book_name,
            "path": path
        }
