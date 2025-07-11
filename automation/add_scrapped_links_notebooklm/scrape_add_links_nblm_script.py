#!/usr/bin/env python3
"""
NotebookLM Automation Script - Enhanced Version
Scrapes URLs from documentation sites and adds them to NotebookLM notebooks.
Features robust error handling and UI change resilience.
"""
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
    Add links as sources to a NotebookLM notebook with enhanced error handling.

    Args:
        notebook_url (str): URL of the NotebookLM notebook
        links (list): List of links to add as sources
        profile_path (str): Path to the browser profile directory
    """
    profile_path = os.path.expanduser(profile_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
        )
        page = await browser.new_page()
        await page.goto(notebook_url)
        
        print(f"📖 Navigated to notebook")
        await page.wait_for_timeout(3000)  # Wait for page to load

        successful_links = []
        failed_links = []

        for i, link in enumerate(links):
            print(f"🔗 Processing {i+1}/{len(links)}: {link[:60]}...")
            
            try:
                # Step 1: Dismiss any overlay dialogs
                try:
                    overlay_backdrop = page.locator(".cdk-overlay-backdrop")
                    if await overlay_backdrop.count() > 0:
                        await overlay_backdrop.click()
                        await page.wait_for_timeout(1000)
                except:
                    pass
                
                # Step 2: Find and click the Add button with multiple fallbacks
                add_selectors = [
                    "text='Add'",
                    "button:has-text('Add')",
                    "[data-testid*='add']",
                    "button[aria-label*='Add']",
                    ".add-button",
                    "button:has-text('+ Add')"
                ]
                
                add_button = None
                for selector in add_selectors:
                    try:
                        add_button = page.locator(selector).first
                        if await add_button.count() > 0:
                            break
                    except:
                        continue
                
                if not add_button or await add_button.count() == 0:
                    print(f"   ❌ Could not find Add button")
                    failed_links.append(link)
                    continue
                
                await add_button.wait_for(state="visible", timeout=10000)
                await add_button.click()
                
                # Step 3: Find and click the appropriate source type
                await page.wait_for_timeout(2000)  # Wait for dialog to appear
                
                # Determine source type options to look for
                if "youtube.com" in link:
                    target_options = ["YouTube", "Youtube", "YouTube video", "Video"]
                else:
                    target_options = ["Website", "Web page", "Webpage", "Web", "URL", "Link"]
                
                source_button = None
                for option in target_options:
                    try:
                        button = page.locator(f"text='{option}'").first
                        if await button.count() > 0:
                            source_button = button
                            break
                    except:
                        continue
                
                if not source_button:
                    print(f"   ❌ Could not find source type option")
                    failed_links.append(link)
                    # Try to close dialog
                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(1000)
                    except:
                        pass
                    continue
                
                await source_button.click()
                
                # Step 4: Find and fill the URL input with multiple fallbacks
                await page.wait_for_timeout(2000)
                
                input_selectors = [
                    "input[placeholder*='URL']",
                    "input[placeholder*='url']",
                    "input[placeholder*='link']",
                    "input[placeholder*='YouTube']",
                    "input[type='url']",
                    "input[type='text']",
                    ".mat-mdc-input-element",
                    "textarea"
                ]
                
                url_input = None
                for selector in input_selectors:
                    try:
                        input_elem = page.locator(selector).first
                        if await input_elem.count() > 0:
                            url_input = input_elem
                            break
                    except:
                        continue
                
                if not url_input:
                    print(f"   ❌ Could not find URL input field")
                    failed_links.append(link)
                    continue
                
                # Clear and fill the input
                await url_input.click()
                await url_input.fill("")  # Clear first
                await url_input.fill(link)
                
                # Step 5: Find and click submit button with multiple fallbacks
                await page.wait_for_timeout(1000)
                
                submit_selectors = [
                    "button:has-text('Insert')",
                    "button:has-text('Add')",
                    "button:has-text('Submit')",
                    "button:has-text('Save')",
                    "button[type='submit']",
                    ".mat-primary",
                    "button.mdc-button--raised"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        btn = page.locator(selector).first
                        if await btn.count() > 0:
                            submit_button = btn
                            break
                    except:
                        continue
                
                if not submit_button:
                    print(f"   ❌ Could not find submit button")
                    failed_links.append(link)
                    continue
                
                await submit_button.click()
                print(f"   ✅ Successfully added")
                successful_links.append(link)
                
                # Wait for processing
                await page.wait_for_timeout(3000)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                failed_links.append(link)
                
                # Try to escape any dialogs and continue
                try:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1000)
                except:
                    pass
                continue

        await browser.close()
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"✅ Successfully added: {len(successful_links)}")
        print(f"❌ Failed to add: {len(failed_links)}")
        
        if failed_links:
            print(f"\n❌ Failed links:")
            for link in failed_links:
                print(f"   - {link}")


def read_links_from_file(file_path):
    """Read links from a file, one link per line."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


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

                # Transform /html/ to /html-single/ in the URL
                if '/html/' in absolute_url:
                    absolute_url = absolute_url.replace('/html/', '/html-single/')
                
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
        description="NotebookLM Automation Tool - Enhanced Version",
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
            
        print(f"🚀 Adding {len(links)} sources to notebook...")
        asyncio.run(add_links(args.notebook, links, args.profile_path))
        sys.exit(0)

    # No valid mode selected
    print("❌ No valid operation specified. Use one of:")
    print("  --extract-toc URL  : Extract documentation links")
    print("  --login            : Authenticate with Google")
    print("  --notebook URL     : Add links to notebook (with --links or --links-file)")
    sys.exit(1)


if __name__ == "__main__":
    main() 