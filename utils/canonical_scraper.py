import requests
import re

def get_simplified_tiktok_live_url(url):
    """
    This function takes a TikTok URL, follows redirects, 
    and returns a simplified live URL in the format https://www.tiktok.com/@username/live.
    """
    try:
        headers = {
            'User-Agent': 'curl/7.64.1'
        }
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()

        final_url = response.url

        # Extract username from the URL
        match = re.search(r'@([^/]+)', final_url)
        if match:
            username = match.group(1)
            simplified_url = f"https://www.tiktok.com/@{username}/live"
            return simplified_url
        else:
            print("Could not extract username from the URL.")
            return None

    except requests.exceptions.RequestException as e:
        # Try to extract the URL from the exception object
        failed_url = url
        if e.response is not None:
            failed_url = e.response.url
        elif e.request is not None:
            failed_url = e.request.url

        match = re.search(r'@([^/]+)', failed_url)
        if match:
            username = match.group(1)
            simplified_url = f"https://www.tiktok.com/@{username}/live"
            print(f"Request failed, but extracted username: {username}")
            return simplified_url
        print(f"An error occurred with the request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None