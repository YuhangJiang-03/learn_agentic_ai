from langchain.tools import tool
import requests
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from rich import print
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re 




load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILIY_API_KEY"))

@tool
def web_search(query:str) -> str:
    """
    Perform a web search using the Tavily API.

    Args:
        query (str): The search query.

    Returns:
        str: The search results.
    """
    results = tavily.search(query=query, max_results=5)
    out = []
    for r in results['results']:
        out.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Snippet: {r['content'][:300]}\n"
            
        )
    return "\n----\n".join(out)

@tool
def scrape_url(url:str) -> str:
    """
    Scrape the content of a given URL.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The scraped content.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "referrer": "https://www.google.com/",
    }

    try: 
        # Fetch page
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()  # Raise an error for bad responses

        html = response.text

        # trafilatura extraction
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
        )

        if extracted and len(extracted.strip()) > 200:
            cleaned = re.sub(r'\s+', ' ', extracted)
            return cleaned[:5000]

        # readability extraction
        doc = Document(html)
        clean_html = doc.summary()
        soup = BeautifulSoup(clean_html, 'html.parser')

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",

        ]):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)

        if text and len(text.strip()) > 200:
            cleaned = re.sub(r'\s+', ' ', text)
            return cleaned[:5000] 

        # fallback full page extraction
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",

        ]):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)
        cleaned = re.sub(r'\s+', ' ', text)
        if cleaned:
            return cleaned[:5000]
        return "Failed to extract content from the URL."
    except requests.exceptions.Timeout:
        return "Request timed out while trying to access the URL."
    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {str(e)}"
    except Exception as e:
        return f"An error occurred while scraping the URL: {str(e)}"