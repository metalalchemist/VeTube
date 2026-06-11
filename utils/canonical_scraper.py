import httpx
import re
import asyncio
from setup import network

async def get_simplified_tiktok_live_url(url):
    """
    This function takes a TikTok URL, follows redirects asynchronously,
    and returns a simplified live URL in the format https://www.tiktok.com/@username/live.
    """
    try:
        # Usamos el cliente global de setup.network.client
        # Activamos follow_redirects=True solo para esta petición
        response = await network.client.get(url, follow_redirects=True)
        response.raise_for_status()
        final_url = str(response.url)

        # Extract username from the URL
        match = re.search(r'@([^/]+)', final_url)
        if match:
            username = match.group(1)
            simplified_url = f"https://www.tiktok.com/@{username}/live"
            return simplified_url
        else:
            print("Could not extract username from the URL.")
            return None

    except httpx.HTTPStatusError as e:
        # Try to extract the URL from the response
        failed_url = str(e.response.url)
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
