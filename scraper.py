import asyncio
from playwright.async_api import async_playwright
import argparse
import sys
import os

async def scrape_ads_transparency(queries, region="AU", max_pages=1, headless=True, output_file=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        unique_urls = set()
        
        # Load existing domains if file exists to avoid duplicates
        if output_file and os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    for line in f:
                        unique_urls.add(line.strip())
                print(f"Loaded {len(unique_urls)} existing domains from {output_file}")
            except Exception as e:
                print(f"Error reading existing file: {e}")

        # Open file in append mode
        f_out = open(output_file, "a", encoding="utf-8") if output_file else None
        
        try:
            for query in queries:
                print(f"\n--- Processing query: {query} ---")
                url = f"https://adstransparency.google.com/?region={region}"
                
                try:
                    await page.goto(url)
                    
                    # Wait for the search input
                    search_input = page.locator("input[type='text']").first
                    await search_input.wait_for(state="visible", timeout=10000)
                    
                    await search_input.fill(query)
                    await page.wait_for_timeout(2000) # Wait for suggestions
                    
                    # Try to click "See more results"
                    see_more = page.locator("text='See more results'")
                    if await see_more.count() > 0 and await see_more.first.is_visible():
                        print("Clicking 'See more results'...")
                        await see_more.first.click()
                    else:
                        # Check for suggestions
                        suggestions = page.locator("material-select-item")
                        count = await suggestions.count()
                        
                        if count > 0:
                            # print("Clicking the first suggestion...", file=sys.stderr)
                            await suggestions.first.click()
                        else:
                            # print("No suggestions found, pressing Enter...", file=sys.stderr)
                            await search_input.press("Enter")
                    
                    print("Waiting for results page to load...")
                    await page.wait_for_timeout(3000)

                    # Click "By domain" tab
                    print("Clicking 'By domain'...")
                    by_domain_tab = page.locator("text='By domain'")
                    if await by_domain_tab.count() > 0:
                        try:
                            # Use force=True to bypass potential overlays or ripple effects
                            await by_domain_tab.first.click(force=True)
                        except Exception as e:
                            print(f"Click failed, trying JS click: {e}")
                            await by_domain_tab.first.evaluate("element => element.click()")
                        
                        await page.wait_for_timeout(3000) # Wait for domain list to load
                    else:
                        print("Could not find 'By domain' tab. Skipping this query.")
                        continue

                    # Scraping loop
                    page_num = 0
                    while True:
                        if max_pages > 0 and page_num >= max_pages:
                            break

                        print(f"Scraping page {page_num + 1} for '{query}'...")
                        await page.wait_for_timeout(2000) # Wait for content to load

                        # Broad search for domain-like text
                        # Based on debug HTML, the items are material-select-item with role='option'
                        rows = await page.locator("material-select-item[role='option']").all()
                        if not rows:
                            rows = await page.locator("div[role='row']").all()
                        if not rows:
                            rows = await page.locator("div[role='listitem']").all()
                        
                        found_on_page = 0
                        if rows:
                            print(f"Found {len(rows)} rows/items. Extracting text...")
                            for row in rows:
                                # Try to find the specific name element
                                name_el = row.locator(".name")
                                if await name_el.count() > 0:
                                    text = await name_el.first.inner_text()
                                else:
                                    text = await row.inner_text()

                                # Simple heuristic to find domain in text
                                lines = text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if '.' in line and ' ' not in line and len(line) > 3:
                                        # Exclude common non-domain words
                                        if line.lower() not in ['verified', 'unverified', 'about', 'ads']:
                                            if line not in unique_urls:
                                                unique_urls.add(line)
                                                print(line)
                                                if f_out:
                                                    f_out.write(line + "\n")
                                                    f_out.flush()
                                                found_on_page += 1
                        else:
                            # Fallback: Get all text and filter
                            print("No rows found. Scanning all text...")
                            body_text = await page.locator("body").inner_text()
                            lines = body_text.split('\n')
                            import re
                            for line in lines:
                                line = line.strip()
                                if re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', line):
                                     if line.lower() not in ['google.com', 'adstransparency.google.com']:
                                        if line not in unique_urls:
                                            unique_urls.add(line)
                                            print(line)
                                            if f_out:
                                                f_out.write(line + "\n")
                                                f_out.flush()
                                            found_on_page += 1
                        
                        print(f"Found {found_on_page} new domains on page {page_num + 1}.")

                        # Pagination
                        next_button = page.locator("material-button[aria-label='Next page']").or_(page.locator("div[aria-label='Next page']"))
                        
                        if await next_button.count() > 0:
                                if await next_button.first.get_attribute("aria-disabled") == "true":
                                    print("Next button is disabled. Reached end of results.")
                                    break
                                
                                # If we are about to stop due to max_pages, don't click next
                                if max_pages > 0 and page_num >= max_pages - 1:
                                    break

                                print("Clicking Next page...")
                                try:
                                    await next_button.first.click()
                                except:
                                    await next_button.first.click(force=True)
                                
                                await page.wait_for_timeout(2000) # Wait for next page load
                        else:
                            print("Next button not found.")
                            break
                        
                        page_num += 1
                
                except Exception as e:
                    print(f"Error during processing of '{query}': {e}")
                    continue

        finally:
            if f_out:
                f_out.close()
                print(f"Results saved to {output_file}", file=sys.stderr)
            await browser.close()

def main():
    parser = argparse.ArgumentParser(description="Scrape Google Ads Transparency Center")
    parser.add_argument("queries", nargs='*', help="The search queries (e.g., 'Nike' 'Google')")
    parser.add_argument("--query-file", help="File containing search queries (one per line)")
    parser.add_argument("--region", default="AU", help="Region code (default: AU)")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum number of pages to scrape per query")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (not headless)")
    parser.add_argument("--output", help="Output file to save results (e.g., results.txt)")
    
    args = parser.parse_args()
    
    queries = args.queries
    if args.query_file:
        if os.path.exists(args.query_file):
            try:
                with open(args.query_file, 'r', encoding='utf-8') as f:
                    file_queries = [line.strip() for line in f if line.strip()]
                    queries.extend(file_queries)
            except Exception as e:
                print(f"Error reading query file: {e}")
                sys.exit(1)
        else:
            print(f"Error: Query file '{args.query_file}' not found.")
            sys.exit(1)

    if not queries:
        print("Please provide at least one search query via command line or --query-file.")
        sys.exit(1)

    asyncio.run(scrape_ads_transparency(queries, args.region, args.max_pages, headless=not args.visible, output_file=args.output))

if __name__ == "__main__":
    main()
