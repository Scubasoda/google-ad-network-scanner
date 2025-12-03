# Google Ad Network Scanner

This tool automates the process of scraping advertiser domains from the Google Ads Transparency Center and analyzing their content using the Moonshot AI (Kimi) LLM to identify potential cryptocurrency scams or legitimate businesses.

## Features

*   **Google Ads Scraper (`scraper.py`):**
    *   Scrapes advertiser domains based on search queries (e.g., "Bitcoin", "Crypto").
    *   Supports pagination and region selection.
    *   Saves unique domains to a text file.
*   **Domain Scanner (`scanner.py`):**
    *   Visits each scraped domain using Playwright.
    *   **Tor Support:** Automatically detects and uses Tor (if running) to bypass IP blocks and hide identity.
    *   **Stealth Mode:** Uses `playwright-stealth` and manual evasions to avoid bot detection.
    *   **Content Analysis:** Extracts text content and sends it to Moonshot AI (Kimi) to determine:
        *   Summary of the website.
        *   Relevance to cryptocurrency/trading.
        *   Legitimacy assessment (Legit vs. Suspicious/Scam).
        *   Contact information extraction.

## Prerequisites

*   Python 3.8+
*   [Tor Browser](https://www.torproject.org/download/) (Optional, but recommended for bypassing blocks)
*   Moonshot AI API Key

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Scubasoda/google-ad-network-scanner.git
    cd google-ad-network-scanner
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  Create a `.env` file in the root directory and add your Moonshot API key:
    ```env
    MOONSHOT_API_KEY=sk-your_api_key_here
    ```

## Usage

### 1. Scrape Domains

Run the scraper to collect domains from Google Ads Transparency Center.

```bash
python scraper.py "Bitcoin" "Ethereum" --region AU --max-pages 2 --output crypto_domains.txt
```

*   `"Query"`: Search terms.
*   `--region`: Country code (default: AU).
*   `--max-pages`: Number of pages to scrape per query.
*   `--output`: File to save the domains.

### 2. Scan and Analyze Domains

Run the scanner to visit the domains and analyze them with AI.

**Important:** For best results and to avoid IP bans, open the **Tor Browser** before running the scanner. The script will automatically detect it.

```bash
python scanner.py
```

*   Reads domains from `crypto_domains.txt`.
*   Saves analysis to `domain_analysis.txt`.

## Tor Integration

The scanner automatically checks for a Tor proxy on ports `9150` (Tor Browser) or `9050` (Standalone Tor).
*   **If detected:** It routes all traffic through Tor and launches the browser in **headful mode** (visible) to mimic human behavior and reduce bot detection rates.
*   **If not detected:** It runs using your standard connection in headless mode.

## Output Example

The `domain_analysis.txt` will contain entries like:

```text
--- Domain: example-crypto-site.com ---
1. This website claims to be a leading crypto trading platform offering 500% returns.
2. Yes (Cryptocurrency/Trading).
3. Potentially suspicious/scammy. The promise of guaranteed high returns is a common red flag. No physical address is listed.
4. Contact: support@example-crypto-site.com
```

## Disclaimer

This tool is for educational and research purposes only. Use responsibly.
