import os
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("MOONSHOT_API_KEY")

url = "https://api.moonshot.cn/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}

print(f"Testing URL: {url}")
print(f"Key: {api_key[:5]}...")

try:
    response = httpx.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
