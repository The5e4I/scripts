tool = {
    "type": "function",
    "function": {
        "name": "kiwix_list_books",
        "description": "List all available ZIM books on a Kiwix server. Returns book metadata including name, uuid, title, and other properties.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL of the kiwix server (e.g., http://127.0.0.1:8088)",
                    "default": "http://127.0.0.1:8088"
                },
                "q": {
                    "type": "string",
                    "description": "Search text in title or description.",
                }
            },
            "required": ["base_url"]
        }
    }
}


def execute(arguments):
    base_url = arguments.get("base_url", "http://127.0.0.1:8088")
    q = arguments.get("q")

    import urllib.parse
    import requests

    # Build URL with query parameters
    params = {
        'count': -1,  # Return all entries
    }

    if q:
        params['q'] = q

    url = f"{base_url.rstrip('/')}/catalog/v2/entries?{urllib.parse.urlencode(params)}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse OPDS XML to extract book information
        import xml.etree.ElementTree as ET

        ns = {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
              'atom': 'http://www.w3.org/2005/Atom',
              'dc': 'http://purl.org/dc/terms/',
              'thr': 'http://purl.org/syndication/thread/1.0'}

        try:
            root = ET.fromstring(response.text.encode('utf-8'))
        except ET.ParseError as e:
            return {"error": f"Failed to parse XML response: {str(e)}", "raw_response": response.text[:500]}

        # Extract metadata
        books = []
        total_results_elem = root.find('.//opensearch:totalResults', ns)
        total_results = int(total_results_elem.text) if total_results_elem is not None else 0

        start_elem = root.find('.//opensearch:startIndex', ns)
        start_index = int(start_elem.text) if start_elem is not None else 0

        for entry in root.findall('.//atom:entry', ns):
            title = entry.find('.//atom:title', ns)
            entry_id = entry.find('.//atom:id', ns)

            # Extract metadata using various namespaces
            tags_elem = entry.find('.//atom:category[@scheme="http://openstreetmap.org/spec/tag"]', ns) or \
                        entry.find('.//atom:category[@scheme="https://wiki.openstreetmap.org/wiki/Kiwix/Tags"]', ns)

            # Get all category elements for tags and categories
            categories = []
            category_elements = entry.findall('.//atom:category', ns)
            for cat in category_elements:
                term = cat.get('term', '')
                categories.append(term)

            book_info = {
                'title': title.text.strip() if title is not None and title.text else None,
                'uuid': entry_id.text.split('/')[-1] if entry_id is not None and entry_id.text else None,
                'name': None,
                # 'language': [],
                # 'category': [],
                # 'tags': [],
                # 'description': None,
                # 'size': None,
                # 'date': None
            }

            # Extract detailed metadata from link elements and other tags
            for child in entry:
                if child.tag == f'{{{ns["atom"]}}}link':
                    # Extract ZIM name from URL
                    href = child.get('href', '')
                    if href.startswith('/content/'):
                        # Extract the first segment after /content/
                        parts = href.strip('/').split('/')
                        if len(parts) >= 2:
                            book_info['name'] = parts[1]
            #     elif child.tag == f'{{{ns["dc"]}}}language':
            #         if child.text:
            #             book_info['language'].append(child.text)
            #     elif child.tag == f'{{{ns["dc"]}}}description':
            #         if child.text:
            #             book_info['description'] = child.text.strip()
            #     elif child.tag == f'{{{ns["dc"]}}}format':
            #         if child.text and child.text.endswith('B'):
            #             book_info['size'] = int(child.text[:-1].replace(',', ''))
            #     elif child.tag == f'{{{ns["dc"]}}}date':
            #         if child.text:
            #             book_info['date'] = child.text
            #     elif child.tag == f'{{{ns["atom"]}}}category':
            #         # Tag elements start with underscore
            #         term = child.get('term', '')
            #         if term.startswith('_') and 'lang:' not in term and 'category:' not in term:
            #             book_info['tags'].append(term.lstrip('_'))
            #
            # # Separate category from tags
            # all_terms = [c for c in categories]
            # book_info['category'] = [t.replace('category:', '').strip() for t in all_terms if 'category:' in t.lower()]

            books.append(book_info)

        return {
            "books": books,
            # "total": total_results,
            # "start": start_index,
            "count": len(books)
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch from kiwix server: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
