#!/usr/bin/env python3
import asyncio
import argparse
import os
from playwright.async_api import async_playwright
import requests
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin


async def login(profile_path):
    """
    Open a browser for the user to log in to their Google account and save the profile.

    Args:
        profile_path (str): Path to the browser profile directory
    """
    profile_path = os.path.expanduser(profile_path)

    async with async_playwright() as p:
        # This is where your cookies and login sessions will be stored
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
        )
        page = await browser.new_page()
        await page.goto("https://accounts.google.com")

        print("Please log in manually and then close the browser window when done.")
        try:
            await page.wait_for_timeout(60000 * 10)  # 10 minutes to log in
        except Exception as e:
            print(f"Finished with {e}")


async def add_links(notebook_url, links, profile_path):
    """
    Add links as sources to a NotebookLM notebook.

    Args:
        notebook_url (str): URL of the NotebookLM notebook
        links (list): List of links to add as sources
        profile_path (str): Path to the browser profile directory
    """
    profile_path = os.path.expanduser(profile_path)

    async with async_playwright() as p:
        # This is where your cookies and login sessions will be stored
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,  # Set to True if you want to run in the background
        )
        page = await browser.new_page()
        await page.goto(notebook_url)

        for link in links:
            # Wait for the page to load and dismiss any overlay dialogs
            try:
                # Check if there's an overlay dialog and dismiss it
                overlay_backdrop = page.locator(".cdk-overlay-backdrop")
                if await overlay_backdrop.count() > 0:
                    await overlay_backdrop.click()
                    await page.wait_for_timeout(1000)  # Wait for dialog to close
            except:
                pass  # Continue if no overlay found
            
            # Wait for the page to load and the "Add source" button to be visible
            # Using text content as a locator can be robust to some UI changes
            add_button = page.locator("text='Add'")
            await add_button.wait_for(state="visible")
            
            # Wait for any overlays to disappear and button to be clickable
            await page.wait_for_timeout(1000)
            
            # Click the "Add source" button with force if needed
            await add_button.click(force=True)

            # Wait for the source options to appear and click "Webpage" or "Youtube"
            # Again, using text content
            if "youtube.com" in link:
                text_to_click = "YouTube"
            else:
                text_to_click = "Website"
            await page.locator(f"text='{text_to_click}'").wait_for(state="visible")
            await page.locator(f"text='{text_to_click}'").click()

            # Selector for the modal container based on the provided HTML
            modal_selector = ".mat-mdc-dialog-inner-container"

            # Wait for the modal container to be visible
            await page.locator(modal_selector).wait_for(state="visible", timeout=15000)

            # Now, locate the input field within this modal by finding the label
            # and navigating to the associated input within its form field container.
            # This chain finds the modal, then the mat-label with specific text,
            # goes up to its ancestor mat-form-field, and finds the input inside.
            if "youtube.com" in link:
                text_to_fill = "Paste YouTube URL"
            else:
                text_to_fill = "Paste URL"
            url_input_locator = (
                page.locator(modal_selector)
                .locator(f"mat-label:text('{text_to_fill}')")
                .locator("xpath=ancestor::mat-form-field")
                .locator("input")
            )

            # Fill the input field. Playwright's fill() waits for the element to be actionable.
            # Use a robust timeout for the fill action itself
            await url_input_locator.fill(link, timeout=20000)

            # Locate the "Insert" button *within* the modal
            # We find the button that contains the text "Insert"
            insert_button_selector = f"{modal_selector} button:has-text('Insert')"

            # Click the "Insert" button.
            # Playwright's click() waits for the element to be actionable (including enabled).
            await page.locator(insert_button_selector).click(timeout=20000)

            print(f"Added source: {link}")

            # Wait for the source to be processed
            await page.wait_for_timeout(2000)  # Wait for 2 seconds

        await browser.close()


def read_links_from_file(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

# New extraction function (standalone operation)
def extract_toc_links(base_url, versions=None, output_file="urls.txt"):
    """
    Extract documentation links from a base URL with optional version support
    
    Args:
        base_url (str): Base documentation URL (without version)
        versions (list): List of versions to process (default: ["latest"])
        output_file (str): Output file path
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Default to "latest" if no versions specified
    if versions is None or len(versions) == 0:
        versions = ["latest"]
        print("No versions specified, defaulting to 'latest'")
    else:
        print(f"Processing specified versions: {', '.join(versions)}")
    
    # Clean up base URL (remove trailing slash)
    base_url = base_url.rstrip('/')
    
    all_links = set()
    
    # Process each version
    for version in versions:
        version_url = f"{base_url.rstrip('/')}/{version}"
        print(f"Extracting content links from: {version_url}")
        
        try:
            response = requests.get(version_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            version_links = set()
            
            # Extract all hrefs from the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip invalid links
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                    
                # Convert to absolute URL
                absolute_url = urljoin(version_url, href)
                
                # Filter for URLs containing the specific base path
                if base_url in absolute_url:
                    # Filter out non-content URLs
                    if not any(absolute_url.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip')):
                        version_links.add(absolute_url)
            
            print(f"✅ Extracted {len(version_links)} links for version {version}")
            all_links.update(version_links)
            
        except Exception as e:
            print(f"❌ Failed to extract from {version_url}: {str(e)}")
    
    # Write all links to file
    if all_links:
        with open(output_file, 'w') as f:
            f.write("\n".join(sorted(all_links)))
        
        print(f"\n✅ Success! Extracted {len(all_links)} total links to {output_file}")
        print("Sample links:")
        for sample in sorted(all_links)[:5]:
            print(f" - {sample}")
        return True
    else:
        print("❌ No valid links extracted")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM Automation Tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--notebook", help="URL of the NotebookLM notebook")
    parser.add_argument("--login", action="store_true", 
                        help="Authenticate with Google account")
    parser.add_argument("--profile-path", default="~/.browser_automation",
                        help="Browser profile directory (default: ~/.browser_automation)")
    
    # Extraction mode arguments
    parser.add_argument("--extract-toc", metavar="URL",
                        help="Base documentation URL to scrape\n"
                             "Example: https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed")
    parser.add_argument("--toc-output", default="urls.txt",
                        help="Output file for extracted links (default: urls.txt)\n"
                             "Note: This file can be used with --links-file for notebook mode")
    parser.add_argument("--versions", 
                        help="Comma-separated list of versions to process\n"
                             "Example: --versions 2.21,2.22,2.23\n"
                             "Default: 'latest' if not specified")
    
    # Link source options (only used with --notebook)
    link_group = parser.add_argument_group('Link sources')
    link_group.add_argument("--links", nargs="+", 
                           help="List of links to add")
    link_group.add_argument("--links-file", default="urls.txt",
                           help="File containing links to add (default: urls.txt)\n"
                                "Auto-detects available files if not specified")

    args = parser.parse_args()

    # Extraction mode
    if args.extract_toc:
        # Process versions if specified
        versions = [v.strip() for v in args.versions.split(',') if v.strip()] if args.versions else None
        
        success = extract_toc_links(
            base_url=args.extract_toc,
            versions=versions,
            output_file=args.toc_output
        )
        sys.exit(0 if success else 1)

    # Login mode
    if args.login:
        print("Starting authentication process...")
        asyncio.run(login(args.profile_path))
        print("✅ Login completed successfully")
        sys.exit(0)

    # Link addition mode
    if args.notebook:
        if args.links:
            links = args.links
        else:
            # Smart file detection - try to find the most appropriate file
            if args.links_file != "urls.txt":
                # User specified a custom file
                target_file = args.links_file
            else:
                # User didn't specify, try to find the best available file
                possible_files = [
                    "urls.txt",      # Default
                    "my_links.txt",  # Common extraction output
                    "urls_clean.txt" # Your clean file
                ]
                
                target_file = None
                for file in possible_files:
                    if os.path.exists(file):
                        target_file = file
                        break
                
                if target_file is None:
                    print("❌ Error: No links file found!")
                    print("Available options:")
                    print("  1. Run --extract-toc first to create a links file")
                    print("  2. Specify --links-file with an existing file")
                    print("  3. Provide --links with individual URLs")
                    sys.exit(1)
            
            print(f"Using links from: {target_file}")
            try:
                links = read_links_from_file(target_file)
            except FileNotFoundError:
                print(f"❌ Error: Links file not found - {target_file}")
                print("Run with --extract-toc first or provide --links")
                sys.exit(1)
        
        if not links:
            print("❌ No links found to process")
            sys.exit(1)
            
        print(f"Adding {len(links)} sources to notebook...")
        asyncio.run(add_links(args.notebook, links, args.profile_path))
        print("✅ Sources added successfully")
        sys.exit(0)

    # No valid mode selected
    print("❌ No valid operation specified. Use one of:")
    print("  --extract-toc URL  : Extract documentation links")
    print("  --login            : Authenticate with Google")
    print("  --notebook URL     : Add links to notebook (with --links or --links-file)")
    sys.exit(1)


if __name__ == "__main__":
    main()
