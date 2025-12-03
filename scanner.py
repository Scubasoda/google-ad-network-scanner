import asyncio
import os
import sys
import traceback
import socket
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from openai import OpenAI
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# API_KEY = os.getenv("MOONSHOT_API_KEY")
API_KEY = "sk-tjtcxB4I80RFfhPVqaL1Ot5tQNw4nC7PBF88SWkMrG4C1bjV"

if not API_KEY or API_KEY == "your_api_key_here":
    print("Error: MOONSHOT_API_KEY not found or not set in .env file.")
    print("Please edit .env and add your actual API key.")
    sys.exit(1)

# Initialize OpenAI client for Moonshot AI
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.moonshot.ai/v1",
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    sys.exit(1)

def check_tor_proxy():
    """Checks if Tor proxy is available on port 9150 (Tor Browser) or 9050 (Standalone)."""
    for port in [9150, 9050]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return f"socks5://127.0.0.1:{port}"
        except:
            pass
    return None

async def get_page_content(context, url):
    """Fetches the text content of a webpage using an existing browser context."""
    page = None
    try:
        page = await context.new_page()
        
        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Add https:// if missing
        if not url.startswith("http"):
            target_url = f"https://{url}"
        else:
            target_url = url
            
        print(f"Visiting {target_url}...")
        
        try:
            # Increased timeout for Tor
            response = await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            # Handle Cloudflare/DDOS-Guard challenges (202 Accepted / 503 Service Unavailable)
            if response and (response.status == 202 or response.status == 503):
                print(f"  -> Received status {response.status}, waiting for challenge resolution...")
                await page.wait_for_timeout(15000)
                
        except Exception as e:
            print(f"  -> Error navigating to {url}: {e}")
            return None

        content = await page.content()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        return text
        
    except Exception as e:
        print(f"  -> Unexpected error fetching {url}: {e}")
        return None
    finally:
        if page:
            await page.close()

def analyze_content(text, domain):
    """Sends the content to Kimi LLM for analysis."""
    if not text:
        return "No content extracted."
    
    # Truncate text
    max_chars = 15000 
    if len(text) > max_chars:
        text = text[:max_chars] + "...(truncated)"

    prompt = f"""
    Analyze the following website content for the domain '{domain}'.
    
    1. Summarize what this website is about in 1-2 sentences.
    2. Is this website related to cryptocurrency, trading, or investing? (Yes/No)
    3. Does it appear to be a legitimate business or potentially suspicious/scammy? (Briefly explain why)
    4. Extract any contact emails or social media links if mentioned.

    Website Content:
    {text}
    """

    try:
        completion = client.chat.completions.create(
            model="kimi-k2-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes website content for risk assessment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error calling Kimi API: {e}"

async def main():
    input_file = "crypto_domains.txt"
    output_file = "domain_analysis.txt"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Read domains
    with open(input_file, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip()]

    print(f"Found {len(domains)} domains to scan.")

    # Verify API Key before starting
    print("Verifying API key...")
    try:
        client.models.list()
        print("API key verified successfully.")
    except Exception as e:
        print(f"API Key Verification Failed: {e}")
        print("Please check your MOONSHOT_API_KEY in .env")
        return
    
    # Check for Tor
    tor_proxy = check_tor_proxy()
    if tor_proxy:
        print(f"Tor proxy detected at {tor_proxy}. Using Tor for anonymity.")
    else:
        print("Tor proxy not found. Running without Tor (some sites may block access).")

    # Launch browser ONCE
    async with async_playwright() as p:
        print("Launching browser...")
        
        launch_args = {"headless": True}
        if tor_proxy:
            launch_args["proxy"] = {"server": tor_proxy}
            launch_args["headless"] = False # Show browser when using Tor to reduce bot detection
            
        browser = await p.chromium.launch(**launch_args)
        
        # Create context with ignore_https_errors
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            java_script_enabled=True
        )

        # Open output file
        with open(output_file, "a", encoding="utf-8") as f_out:
            for i, domain in enumerate(domains):
                print(f"\n[{i+1}/{len(domains)}] Processing: {domain}")
                
                # 1. Get Content
                content = await get_page_content(context, domain)
                
                if content:
                    print(f"  -> Extracted {len(content)} characters. Analyzing...")
                    
                    # 2. Analyze with Kimi
                    # Run in executor to avoid blocking the async loop
                    loop = asyncio.get_running_loop()
                    analysis = await loop.run_in_executor(None, analyze_content, content, domain)
                    
                    # 3. Save Result
                    result_block = f"--- Domain: {domain} ---\n{analysis}\n\n"
                    
                    # Safe print
                    try:
                        print(f"  -> Analysis complete.")
                    except:
                        pass
                        
                    f_out.write(result_block)
                    f_out.flush()
                else:
                    print("  -> Failed to extract content.")
                    f_out.write(f"--- Domain: {domain} ---\nFailed to extract content.\n\n")
                    f_out.flush()

                # Sleep briefly
                await asyncio.sleep(1)
        
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nCritical Error: {e}")
        traceback.print_exc()
