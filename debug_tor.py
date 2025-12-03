import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    url = "https://cryptopida.com"
    # Tor Browser usually listens on 9150, standalone Tor on 9050
    proxy_server = "socks5://127.0.0.1:9150" 
    
    print(f"Testing access to {url} via Tor proxy ({proxy_server})...")
    print("Make sure Tor Browser is OPEN and connected!")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False, # Headless often blocked even with Tor, safer to show it
                proxy={"server": proxy_server}
            )
            
            context = await browser.new_context(
                ignore_https_errors=True
            )
            
            page = await context.new_page()
            
            # Apply stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            try:
                print("Verifying Tor connection via https://check.torproject.org ...")
                await page.goto("https://check.torproject.org", timeout=60000)
                title = await page.title()
                print(f"Tor Check Title: {title}")
                if "Congratulations" in await page.content():
                    print("Tor connection verified!")
                else:
                    print("Warning: Tor check page loaded but didn't confirm Tor usage.")

                print(f"Navigating to {url}...")
                response = await page.goto(url, timeout=90000, wait_until="domcontentloaded")
                print(f"Initial Status: {response.status}")
                
                if response.status == 202 or response.status == 503:
                    print("Received 202/503, likely a challenge page. Waiting...")
                    await page.wait_for_timeout(10000)
                
                try:
                    title = await page.title()
                    print(f"Title: {title}")
                except Exception as e:
                    print(f"Could not get title: {e}")

                content = await page.content()
                if "403" in content or "Forbidden" in content:
                    print("Result: Blocked (403 Forbidden).")
                elif "Just a moment" in content or "Challenge" in content:
                    print("Result: Cloudflare Challenge detected.")
                    await page.screenshot(path="tor_challenge.png")
                    print("Screenshot saved to tor_challenge.png")
                else:
                    print("Result: Success! Content accessed.")
                    print(f"Content length: {len(content)}")
                    print("--- Snippet ---")
                    print(content[:500])
                    
            except Exception as e:
                print(f"Navigation Error: {e}")
                print("Hint: Is Tor Browser running? If using standalone Tor, change port to 9050.")
            
            await browser.close()
            
    except Exception as e:
        print(f"Browser Launch Error: {e}")
        print("Could not connect to Tor proxy. Please ensure Tor Browser is running.")

if __name__ == "__main__":
    asyncio.run(main())
