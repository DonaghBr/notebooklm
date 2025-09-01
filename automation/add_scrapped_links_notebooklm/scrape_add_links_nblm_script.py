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
import datetime


async def take_debug_screenshot(page, step_name):
    """Take a screenshot for debugging UI issues"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"debug_screenshot_{step_name}_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 Debug screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"⚠️ Could not take screenshot: {e}")
        return None


async def detect_notebooklm_version(page):
    """Try to detect NotebookLM version/changes for better error reporting"""
    try:
        # Look for version indicators in page title, meta tags, or specific elements
        title = await page.title()
        page_content = await page.content()
        
        version_info = {
            "title": title,
            "has_material_ui": ".mat-" in page_content or ".mdc-" in page_content,
            "has_dialog_role": 'role="dialog"' in page_content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        print(f"🔍 NotebookLM page info: {version_info['title']}")
        return version_info
    except Exception as e:
        print(f"⚠️ Could not detect page version: {e}")
        return {"error": str(e)}


async def enhanced_element_search(page, element_type="URL input"):
    """Enhanced element detection with multiple strategies"""
    strategies = []
    
    if element_type == "URL input":
        strategies = [
            # Strategy 1: Semantic approach
            {
                "name": "Semantic Search",
                "selectors": [
                    "input[placeholder*='URL' i]",
                    "input[placeholder*='http' i]", 
                    "input[aria-label*='URL' i]",
                    "input[title*='URL' i]"
                ]
            },
            # Strategy 2: Structural approach  
            {
                "name": "Dialog Structure",
                "selectors": [
                    "[role='dialog'] input:not([placeholder*='search' i])",
                    ".mdc-dialog input:not([placeholder*='search' i])",
                    ".mat-dialog-container input:not([placeholder*='search' i])"
                ]
            },
            # Strategy 3: Form context
            {
                "name": "Form Context", 
                "selectors": [
                    "form input[type='text']:not([placeholder*='search' i])",
                    "form input[type='url']",
                    "form textarea"
                ]
            },
            # Strategy 4: Material UI patterns
            {
                "name": "Material UI",
                "selectors": [
                    ".mat-mdc-input-element:not([placeholder*='search' i])",
                    ".mdc-text-field__input:not([placeholder*='search' i])"
                ]
            }
        ]
    
    print(f"🔍 Enhanced search for {element_type}...")
    
    for strategy in strategies:
        print(f"   🎯 Trying strategy: {strategy['name']}")
        for selector in strategy["selectors"]:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    # Additional validation
                    placeholder = await element.get_attribute("placeholder") or ""
                    aria_label = await element.get_attribute("aria-label") or ""
                    element_type_attr = await element.get_attribute("type") or ""
                    
                    print(f"      ✅ Found element with selector: {selector}")
                    print(f"         Type: {element_type_attr}, Placeholder: '{placeholder}', Aria-label: '{aria_label}'")
                    
                    return element, selector, strategy["name"]
                    
            except Exception as e:
                print(f"      ❌ Selector failed: {selector} - {e}")
                continue
    
    return None, None, None


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


def create_bulk_urls_text(links, output_file="bulk_urls.txt"):
    """
    Create a text file with all URLs separated by newlines for bulk addition to NotebookLM.
    
    Args:
        links (list): List of URLs to combine
        output_file (str): Output file path
    
    Returns:
        str: The combined URLs text
    """
    # Filter out non-URL entries (keep only actual HTTP URLs)
    url_links = [link for link in links if link.startswith('http')]
    
    urls_text = '\n'.join(url_links)
    
    # Save to file for manual fallback
    with open(output_file, 'w') as f:
        f.write(urls_text)
    
    print(f"📄 Created bulk URLs file: {output_file}")
    print(f"🔗 Contains {len(url_links)} URLs for bulk addition")
    
    return urls_text, url_links


async def add_links_bulk(notebook_url, links, profile_path):
    """
    Add links as sources to a NotebookLM notebook using bulk URL addition.
    
    Args:
        notebook_url (str): URL of the NotebookLM notebook
        links (list): List of links to add as sources
        profile_path (str): Path to the browser profile directory
    """
    profile_path = os.path.expanduser(profile_path)
    
    # Create bulk URLs text
    urls_text, url_links = create_bulk_urls_text(links)
    
    if not url_links:
        print("❌ No valid URLs found to add")
        return
    
    print(f"🚀 Adding {len(url_links)} URLs in bulk...")
    print(f"💡 Manual fallback: If automation fails, copy URLs from 'bulk_urls.txt'")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
        )
        page = await browser.new_page()
        await page.goto(notebook_url)
        
        print(f"📖 Navigated to notebook")
        await page.wait_for_timeout(3000)  # Wait for page to load

        try:
            # Step 1: Enhanced overlay dismissal - try multiple strategies
            print("🔄 Dismissing any blocking overlays...")
            
            # Strategy 1: Wait a bit longer for any overlays to fully appear
            await page.wait_for_timeout(5000)
            
            # Strategy 2: Try multiple overlay dismissal approaches
            overlay_strategies = [
                # Specific upload dialog backdrop
                ".cdk-overlay-backdrop.upload-dialog-backdrop",
                # General overlay backdrops
                ".cdk-overlay-backdrop",
                # Material UI overlays
                ".mdc-dialog__scrim",
                ".mat-overlay-backdrop",
                # Generic modal overlays
                "[data-testid*='overlay']",
                "[role='dialog']",
                ".modal-backdrop"
            ]
            
            for i, overlay_selector in enumerate(overlay_strategies):
                try:
                    overlay = page.locator(overlay_selector)
                    overlay_count = await overlay.count()
                    
                    if overlay_count > 0:
                        print(f"Found {overlay_count} overlay(s) with selector: {overlay_selector}")
                        
                        # Try clicking the overlay to dismiss it
                        await overlay.first.click()
                        await page.wait_for_timeout(1500)
                        print(f"Clicked overlay {i+1}")
                        
                        # Check if it's gone
                        remaining = await overlay.count()
                        if remaining > 0:
                            print(f" {remaining} overlay(s) still present")
                        else:
                            print(f"Overlay dismissed successfully")
                            
                except Exception as e:
                    print(f"Overlay strategy {i+1} failed: {e}")
                    continue
            
            # Strategy 3: Try Escape key to dismiss any remaining dialogs
            try:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(1000)
                await page.keyboard.press("Escape")  # Double tap just in case
                await page.wait_for_timeout(1000)
                print("   ⌨️  Sent Escape keys to dismiss dialogs")
            except:
                pass
            
            # Strategy 4: Check for specific close buttons
            close_selectors = [
                "button[aria-label*='close' i]",
                "button[aria-label*='dismiss' i]", 
                "[data-testid*='close']",
                ".close-button",
                "button:has-text('×')",
                "button:has-text('Close')"
            ]
            
            for close_selector in close_selectors:
                try:
                    close_button = page.locator(close_selector)
                    if await close_button.count() > 0:
                        await close_button.first.click()
                        await page.wait_for_timeout(1000)
                        print(f"   🔘 Clicked close button: {close_selector}")
                        break
                except:
                    continue
            
            # Step 2: Find and click the Add button
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
                print(f"❌ Could not find Add button")
                print(f"📄 Manual fallback: Copy URLs from 'bulk_urls.txt' and paste into NotebookLM")
                await browser.close()
                return
            
            await add_button.wait_for(state="visible", timeout=10000)
            await add_button.click()
            print("✅ Clicked Add button")
            
            # Step 3: Click on Website option
            await page.wait_for_timeout(2000)  # Wait for dialog to appear
            
            website_selectors = ["Website", "Web page", "Webpage", "Web", "URL", "Link"]
            source_button = None
            for option in website_selectors:
                try:
                    button = page.locator(f"text='{option}'").first
                    if await button.count() > 0:
                        source_button = button
                        break
                except:
                    continue
            
            if not source_button:
                print(f"❌ Could not find Website option")
                print(f"📄 Manual fallback: Copy URLs from 'bulk_urls.txt' and paste into NotebookLM")
                await browser.close()
                return
            
            await source_button.click()
            print("✅ Selected Website option")
            
            # Step 4: Find and fill the URL input with ALL URLs at once
            await page.wait_for_timeout(2000)
            
            # More specific selectors for NotebookLM URL input after selecting "Website"
            input_selectors = [
                # Most specific - look for URL-related placeholders first
                "input[placeholder*='Enter URL']",
                "input[placeholder*='Paste URL']", 
                "input[placeholder*='Add URL']",
                "input[placeholder*='https://']",
                "input[placeholder*='http://']",
                "input[placeholder*='URL']",
                "input[placeholder*='url']",
                "input[placeholder*='website']",
                "input[placeholder*='link']",
                # Type-specific selectors
                "input[type='url']",
                # Dialog-specific selectors (NotebookLM uses Material UI)
                "[role='dialog'] input[type='text']",
                ".mdc-dialog input[type='text']",
                ".mat-dialog-container input[type='text']",
                # Form-specific within dialog
                "form input[type='text']",
                # Material UI input elements within dialog context
                "[role='dialog'] .mat-mdc-input-element",
                ".mdc-dialog .mat-mdc-input-element", 
                ".mat-dialog-container .mat-mdc-input-element",
                # Generic textarea for URL input
                "[role='dialog'] textarea",
                ".mdc-dialog textarea",
                # Last resort - but more specific than before
                "input[type='text']:not([placeholder*='Search']):not([placeholder*='emoji'])"
            ]
            
            url_input = None
            print("🔍 Searching for URL input field...")
            
            for i, selector in enumerate(input_selectors):
                try:
                    input_elem = page.locator(selector).first
                    if await input_elem.count() > 0:
                        # Additional validation - check if it's not a search/emoji field
                        placeholder = await input_elem.get_attribute("placeholder") or ""
                        aria_label = await input_elem.get_attribute("aria-label") or ""
                        
                        # Skip emoji/search fields
                        if any(term in (placeholder + aria_label).lower() for term in ["emoji", "search"]):
                            print(f"   ⏭️  Skipping selector {i+1}: {selector} (emoji/search field)")
                            continue
                            
                        url_input = input_elem
                        print(f"   ✅ Found URL input with selector {i+1}: {selector}")
                        print(f"      Placeholder: '{placeholder}'")
                        print(f"      Aria-label: '{aria_label}'")
                        break
                except Exception as e:
                    print(f"   ❌ Selector {i+1} failed: {selector} - {e}")
                    continue
            
            if not url_input:
                print(f"❌ Could not find URL input field")
                print(f"🔍 Let me check what input fields are available...")
                
                # Debug: List all input elements to help identify the correct one
                try:
                    all_inputs = page.locator("input")
                    input_count = await all_inputs.count()
                    print(f"📊 Found {input_count} input elements on page:")
                    
                    for i in range(min(input_count, 10)):  # Limit to first 10
                        input_elem = all_inputs.nth(i)
                        input_type = await input_elem.get_attribute("type") or "text"
                        placeholder = await input_elem.get_attribute("placeholder") or ""
                        aria_label = await input_elem.get_attribute("aria-label") or ""
                        print(f"   {i+1}. type='{input_type}' placeholder='{placeholder}' aria-label='{aria_label}'")
                        
                except Exception as debug_e:
                    print(f"   Debug failed: {debug_e}")
                
                print(f"📄 Manual fallback: Copy URLs from 'bulk_urls.txt' and paste into NotebookLM")
                await browser.close()
                return
            
            # Clear and fill with ALL URLs
            await url_input.click()
            await url_input.fill("")  # Clear first
            await url_input.fill(urls_text)  # Add all URLs at once
            print(f"✅ Pasted {len(url_links)} URLs into input field")
            
            # Step 5: Find and click submit button
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
                print(f"❌ Could not find submit button")
                print(f"📄 Manual fallback: Copy URLs from 'bulk_urls.txt' and paste into NotebookLM")
                await browser.close()
                return
            
            await submit_button.click()
            print(f"✅ Submitted bulk URLs")
            
            # Wait for processing
            await page.wait_for_timeout(5000)
            print(f"🎉 Successfully submitted {len(url_links)} URLs for processing")
            
        except Exception as e:
            print(f"❌ Error during bulk addition: {str(e)}")
            print(f"📄 Manual fallback: Copy URLs from 'bulk_urls.txt' and paste into NotebookLM")
        
        await browser.close()


# Keep the old function as fallback
async def add_links_individual(notebook_url, links, profile_path):
    """
    Add links as sources to a NotebookLM notebook individually (legacy method).
    
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


# Use bulk addition by default, with fallback option
async def add_links(notebook_url, links, profile_path, use_bulk=True):
    """
    Add links as sources to a NotebookLM notebook.
    
    Args:
        notebook_url (str): URL of the NotebookLM notebook
        links (list): List of links to add as sources
        profile_path (str): Path to the browser profile directory
        use_bulk (bool): Whether to use bulk addition (default: True)
    """
    if use_bulk:
        await add_links_bulk(notebook_url, links, profile_path)
    else:
        await add_links_individual(notebook_url, links, profile_path)


def read_links_from_file(file_path):
    """Read links from a file, one link per line."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def combine_links_from_files(main_file, static_file="CQA_res.txt", skip_static=False):
    """
    Combine links from main file and static CQA_res.txt file.
    
    Args:
        main_file (str): Path to the main links file (scraped URLs)
        static_file (str): Path to the static links file (default: CQA_res.txt)
    
    Returns:
        list: Combined list of unique links
    """
    all_links = []
    
    # Read main file (scraped URLs)
    try:
        main_links = read_links_from_file(main_file)
        all_links.extend(main_links)
        print(f"📄 Loaded {len(main_links)} links from {main_file}")
    except FileNotFoundError:
        print(f"❌ Main links file not found: {main_file}")
        return []
    
    # Only try to read static file if not skipping
    if not skip_static:
        try:
            static_links = read_links_from_file(static_file)
            all_links.extend(static_links)
            print(f"📄 Loaded {len(static_links)} static links from {static_file}")
        except FileNotFoundError:
            print(f"⚠️  Static links file not found: {static_file} (skipping)")
    else:
        print(f"⏭️  Skipping static file {static_file} (--skip-cqa flag used)")
    
    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for link in all_links:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
    
    print(f"🔗 Total unique links to process: {len(unique_links)}")
    return unique_links


def detect_version_in_url(url):
    """
    Detect if a URL contains a version pattern and extract it.
    
    Args:
        url (str): URL to analyze
        
    Returns:
        tuple: (base_url_without_version, detected_version) or (original_url, None)
    """
    import re
    
    # Remove trailing slash for consistent processing
    url = url.rstrip('/')
    
    # Pattern to match version at the end of URL
    # Matches: /latest, /3.2, /v3.2, /2.21.1, etc.
    version_pattern = r'/(latest|v?\d+\.\d+(?:\.\d+)?)$'
    
    match = re.search(version_pattern, url)
    if match:
        version = match.group(1)
        base_url = url[:match.start()]
        return base_url, version
    
    return url, None


def extract_toc_links(base_url, versions=None, output_file="urls.txt"):
    """
    Extract documentation links from a base URL with smart version detection
    
    Args:
        base_url (str): Documentation URL (with or without version)
                       If version detected in URL and no versions specified, uses detected version
                       If version detected in URL and versions specified, uses specified versions
        versions (list): List of versions to process (default: detected version or "latest")
        output_file (str): Output file path
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Check if URL already contains a version
    clean_base_url, detected_version = detect_version_in_url(base_url)
    
    if detected_version:
        print(f"🔍 Detected version '{detected_version}' in URL")
        if versions is None or len(versions) == 0:
            # Use the detected version
            versions = [detected_version]
            print(f"Using detected version: {detected_version}")
        else:
            # User specified versions, use those instead
            print(f"Ignoring detected version '{detected_version}', using specified versions: {', '.join(versions)}")
        base_url = clean_base_url
    else:
        # No version detected in URL
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
        description="NotebookLM Automation Tool - Enhanced Version\n"
                   "Supports combined workflows: extract URLs, authenticate, and add to notebook in one command.\n"
                   "NEW: Bulk URL addition - adds all URLs at once for faster, more reliable processing.\n"
                   "Example: python3 script.py --extract-toc URL --login --notebook NOTEBOOK_URL",
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
                             "Always uses urls.txt unless explicitly changed for consistency")
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
                                "Will also include CQA_res.txt if available")
    link_group.add_argument("--individual", action="store_true",
                           help="Use individual URL addition instead of bulk (slower, legacy method)")
    link_group.add_argument("--skip-cqa", action="store_true",
                       help="Skip including CQA_res.txt when using file-based links")

    args = parser.parse_args()

    # Track operations to perform
    operations_performed = 0
    
    # Step 1: Extraction mode (if specified)
    if args.extract_toc:
        print("🔍 Step 1: Extracting documentation links...")
        # Process versions if specified
        versions = [v.strip() for v in args.versions.split(',') if v.strip()] if args.versions else None
        
        success = extract_toc_links(
            base_url=args.extract_toc,
            versions=versions,
            output_file=args.toc_output
        )
        if not success:
            print("❌ Extraction failed, stopping workflow")
            sys.exit(1)
        operations_performed += 1
        print("✅ Extraction completed successfully\n")

    # Step 2: Login mode (if specified)
    if args.login:
        print("🔐 Step 2: Starting authentication process...")
        asyncio.run(login(args.profile_path))
        print("✅ Login completed successfully\n")
        operations_performed += 1

    # Step 3: Link addition mode (if specified)
    if args.notebook:
        print("📚 Step 3: Adding links to notebook...")
        if args.links:
            # Direct links provided via command line
            links = args.links
        else:
            # File-based links with combination logic
            # Always use urls.txt for consistency unless user specifies otherwise
            main_file = args.links_file  # This will be urls.txt by default
            
            # Check if main file exists
            if not os.path.exists(main_file):
                print(f"❌ Error: Main links file not found - {main_file}")
                print("Available options:")
                print("  1. Run --extract-toc first to create a links file")
                print("  2. Specify --links-file with an existing file")
                print("  3. Provide --links with individual URLs")
                sys.exit(1)
            
            # Combine links from main file + CQA_res.txt (unless skipped)
            links = combine_links_from_files(main_file, skip_static=args.skip_cqa)
        
        if not links:
            print("❌ No links found to process")
            sys.exit(1)
            
        print(f"🚀 Adding {len(links)} sources to notebook...")
        asyncio.run(add_links(args.notebook, links, args.profile_path, not args.individual))
        operations_performed += 1
        print("✅ Notebook update completed successfully")

    # No valid operations selected
    if operations_performed == 0:
        print("❌ No valid operation specified. You can combine multiple operations:")
        print("  --extract-toc URL  : Extract documentation links to urls.txt")
        print("  --login            : Authenticate with Google")
        print("  --notebook URL     : Add links from urls.txt + CQA_res.txt to notebook (bulk mode)")
        print("  --skip-cqa         : Don't include CQA_res.txt when using file-based links")
        print("\nExamples:")
        print("  # Full workflow (extract → login → add in bulk):")
        print("  python3 script.py --extract-toc URL --login --notebook NOTEBOOK_URL")
        print("  # Extract then add (uses urls.txt automatically, bulk mode):")
        print("  python3 script.py --extract-toc URL --notebook NOTEBOOK_URL")
        print("  # Login then add (uses existing urls.txt, bulk mode):")
        print("  python3 script.py --login --notebook NOTEBOOK_URL")
        print("  # Use only custom file (skip CQA_res.txt):")
        print("  python3 script.py --notebook NOTEBOOK_URL --links-file custom.txt --skip-cqa")
        print("  # Use individual addition (slower, legacy):")
        print("  python3 script.py --notebook NOTEBOOK_URL --individual")
        sys.exit(1)
    
    print(f"\n🎉 Workflow completed! Performed {operations_performed} operation(s).")
    sys.exit(0)


if __name__ == "__main__":
    main() 