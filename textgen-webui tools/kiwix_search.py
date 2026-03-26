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
                    "description": "Base URL of the kiwix server",
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
                "format": {
                    "type": "string",
                    "description": "Result format. Either 'html' or 'xml'.",
                    "enum": ["html", "xml"],
                    "default": "html"
                },
                "page_length": {
                    "type": "integer",
                    "description": "Max search results to return (max 140, default: 25).",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
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
    format_type = arguments.get("format", "html")
    page_length = arguments.get("page_length", 5)
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
    # If none specified, search all books

    if page_length:
        params['pageLength'] = min(page_length, 20)  # Enforce max
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
            # "results": [],
            # "raw_response": ""
        }

        if format_type == "xml":
            from lxml import etree
            tree = etree.fromstring(response.text.encode())

            contents = []

            for item in tree.findall(".//channel/item"):
                content = {
                    "title": item.findtext("title"),
                    "url": item.findtext("link"),
                    "description": item.findtext("description"),
                    # "book": item.findtext("book/title"),
                    # "wordCount": item.findtext("wordCount"),
                }
                contents.append(content)

            # Namespace map
            ns = {
                "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
                "atom": "http://www.w3.org/2005/Atom"
            }

            output = {
                "description": tree.findtext(".//channel/description"),
                "totalResults": tree.findtext(".//opensearch:totalResults", namespaces=ns),
                "startIndex": tree.findtext(".//opensearch:startIndex", namespaces=ns),
                "contents": contents
            }

            result["xml_content"] = output
        else:
            # Parse HTML for structured results
            from lxml import html
            tree = html.fromstring(response.text)

            # Extract header info
            header_text = tree.xpath('//div[@class="header"]//text()')
            header_clean = " ".join(h.strip() for h in header_text if h.strip())

            contents = []
            items = tree.xpath('//div[@class="results"]/ul/li')
            for item in items:
                title = item.xpath('.//a/text()')
                link = item.xpath('.//a/@href')
                snippet = item.xpath('.//cite//text()')

                content = {
                    "title": title[0].strip() if title else None,
                    "url": link[0] if link else None,
                    "snippet": " ".join(s.strip() for s in snippet if s.strip()),
                }

                contents.append(content)

            result["summary"] = header_clean
            result["html_content"] = contents
        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search kiwix server: {str(e)}", "search_url": url}
    except Exception as e:
        return {"error": f"Unexpected error during search: {str(e)}", "search_url": url}
