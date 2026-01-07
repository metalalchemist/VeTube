import sys
import os

# Add the project root to sys.path to resolve imports
sys.path.append(os.getcwd())

from utils import canonical_scraper

test_url = "https://vt.tiktok.com/ZSHECRLRUFvTj-bTw5p/"
print(f"Testing URL: {test_url}")

result = canonical_scraper.get_simplified_tiktok_live_url(test_url)
print(f"Result: {result}")

if result and "tiktok.com/@" in result and "/live" in result:
    print("SUCCESS: URL resolved correctly.")
else:
    print("FAILURE: URL could not be resolved.")
