import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

DEFAULT_WIKIPEDIA_URLS = [
    "https://en.wikipedia.org/wiki/Formula_One",
    "https://en.wikipedia.org/wiki/History_of_Formula_One",
    "https://en.wikipedia.org/wiki/Formula_One_car",
    "https://en.wikipedia.org/wiki/Lewis_Hamilton",
    "https://en.wikipedia.org/wiki/Max_Verstappen",
    "https://en.wikipedia.org/wiki/Scuderia_Ferrari",
    "https://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One",
    "https://en.wikipedia.org/wiki/List_of_Formula_One_World_Drivers%27_Champions",
    "https://en.wikipedia.org/wiki/Monaco_Grand_Prix",
    "https://en.wikipedia.org/wiki/Formula_One_regulations",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_wiki_html(html_content: str) -> str:
    """
    Parses Wikipedia page HTML, extracts main article content,
    retains section headers prefixed with '## ', cleans references and boilerplate,
    and returns formatted plain text.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    content_div = soup.find("div", id="mw-content-text")
    if not content_div:
        content_div = soup.find("div", id="content") or soup.body

    if not content_div:
        return ""

    # Remove non-article boilerplate, sidebars, navigation, edit links, references list
    unwanted_selectors = [
        "sup.reference",
        "span.mw-editsection",
        "table.infobox",
        "table.navbox",
        "div.navbox",
        "div.reflist",
        "div.references",
        "div.catlinks",
        "div.shortdescription",
        "div.seealso",
        "table.sidebar",
        "table.vertical-navbox",
        "style",
        "script",
        "noscript",
        "div.noprint",
        "div.mw-jump-link",
        "div.thumb",
        "figure",
        "div.hatnote",
    ]
    for selector in unwanted_selectors:
        for tag in content_div.select(selector):
            tag.decompose()

    text_parts = []
    
    # Iterate through direct children or elements of main content parser
    parser_output = content_div.find("div", class_="mw-parser-output") or content_div

    for elem in parser_output.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol"], recursive=True):
        if elem.name in ["h1", "h2", "h3", "h4"]:
            header_text = elem.get_text().strip()
            # Clean header text
            header_text = re.sub(r'\[edit\]', '', header_text, flags=re.IGNORECASE).strip()
            if header_text and header_text.lower() not in ["see also", "references", "external links", "further reading", "notes"]:
                text_parts.append(f"\n\n## {header_text}\n")
        elif elem.name in ["p", "ul", "ol"]:
            elem_text = elem.get_text().strip()
            if elem_text:
                # Remove inline reference citations like [1], [2][3], [citation needed]
                elem_text = re.sub(r'\[\d+\]', '', elem_text)
                elem_text = re.sub(r'\[citation needed\]', '', elem_text, flags=re.IGNORECASE)
                elem_text = re.sub(r'\[note \d+\]', '', elem_text, flags=re.IGNORECASE)
                # Clean extra spaces
                elem_text = re.sub(r' +', ' ', elem_text)
                text_parts.append(elem_text)

    full_text = "\n\n".join(text_parts)
    # Clean multiple consecutive blank lines
    full_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()
    return full_text


def get_filename_from_url(url: str) -> str:
    """Extracts a clean filename from Wikipedia URL."""
    path = urllib.parse.urlparse(url).path
    page_name = path.split('/')[-1]
    page_name = urllib.parse.unquote(page_name)
    page_name = re.sub(r'[^\w\-]', '_', page_name)
    return f"{page_name}.txt"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "scraped_pages")

def scrape_pages(urls: list[str] = None, output_dir: str = None) -> dict[str, str]:
    """
    Scrapes a list of Wikipedia URLs, saves each extracted text to output_dir as a .txt file,
    and returns a dictionary mapping filename to extracted text.
    """
    if urls is None:
        urls = DEFAULT_WIKIPEDIA_URLS

    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)
    scraped_data = {}

    print(f"--- STEP 1: Starting Web Scraping ({len(urls)} pages) ---")
    for url in urls:
        filename = get_filename_from_url(url)
        filepath = os.path.join(output_dir, filename)
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            extracted_text = clean_wiki_html(resp.text)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(extracted_text)
                
            char_count = len(extracted_text)
            scraped_data[filename] = extracted_text
            print(f"  ✓ Extracted {char_count:>6,d} characters -> {filename} ({url})")
            
        except Exception as e:
            print(f"  ✗ Failed to scrape {url}: {e}")

    print(f"--- Scraping Complete. Total files saved: {len(scraped_data)} in '{output_dir}/' ---\n")
    return scraped_data


if __name__ == "__main__":
    scrape_pages()
