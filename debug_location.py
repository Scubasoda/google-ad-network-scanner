import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    url = "https://cryptopida.com"
    print(f"Testing access to {url} from simulated UK location...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Configure context to mimic a user in London, UK
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/London",
            geolocation={"latitude": 51.5074, "longitude": -0.1278},
            permissions=["geolocation"],
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        
        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        try:
            response = await page.goto(url, timeout=30000)
            print(f"Status: {response.status}")
            print(f"Title: {await page.title()}")
            
            content = await page.content()
            if "403" in content or "Forbidden" in content:
                print("Result: Still blocked (403 Forbidden).")
            else:
                print("Result: Success! Content accessed.")
                
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
