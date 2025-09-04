import requests
from bs4 import BeautifulSoup

def get_username_from_canonical_link(url):
    """
    This function takes a URL, fetches the HTML content, finds the canonical link,
    and extracts the username from it.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        canonical_link_tag = soup.find('link', {'rel': 'canonical'})
        if not canonical_link_tag or not canonical_link_tag.has_attr('href'):
            print("Could not find the canonical link tag with href attribute.")
            return None

        href = canonical_link_tag['href']
        print(href)
        return href
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with the request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None