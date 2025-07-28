# NotebookLM Automation Tools

Automate the process of extracting documentation URLs and adding them as sources to NotebookLM notebooks using browser automation.

## Scripts Overview

### `scrape_add_links_nblm_script.py` - Enhanced URL Extraction & Notebook Management
- **Based on** This code is adapted from https://github.com/sshnaidm/notebooklm/blob/master/automation/add_links_script.py   
- **Extract URLs** from documentation sites with version support
- **Combined workflows** - run extraction, authentication, and notebook loading in one command
- **Smart resource combination** - automatically combines scraped URLs with static CQA resources
- **Add URLs to NotebookLM** with authentication management
- **All-in-one solution** for extraction and notebook loading

## Features

- **URL Extraction**: Scrape documentation hierarchies with version support
- **Combined Workflows**: Run extract → login → add in single command
- **Static Resource Integration**: Automatically includes `CQA_res.txt` static links
- **Consistent File Handling**: Always uses `urls.txt` for predictable behavior
- **Version Support**: Defaults to "latest" or specify versions like 2.19, 2.20
- **Authentication Management**: Persistent Google login sessions
- **Bulk URL Loading**: Add multiple URLs to NotebookLM automatically
- **Error Handling**: Comprehensive error messages and recovery options
- **YouTube & Website Support**: Handles both content types

## Quick Start

### Prerequisites
- Python 3.7+
- A NotebookLM account

### Installation

#### Step 1: Navigate to Project Root
From the script directory, navigate to where the virtual environment is located:
```bash
# Navigate to project root (where .venv is located)
cd /Users/dobrenna/Documents/NLP_college/sandbox/add_links_notebook
```

#### Step 2: Activate Virtual Environment
Create a virtual environment
```bash
# Activate the existing virtual environment
python -m venv
```

```bash
# Activate the existing virtual environment
source .venv/bin/activate
```
# Install dependencies
python3 -m pip install -r requirements.txt

# Install browser binaries for Playwright
python3 -m playwright install


#### Step 3: Install Playwright Browser
```bash
# Verify Playwright is installed
playwright --version

# Install Chromium browser for automation
playwright install chromium
```

#### Step 4: Return to Script Directory
```bash
# Navigate back to script directory
cd notebooklm/automation/add_scrapped_links_notebooklm
```

**Note**: Always ensure the virtual environment is active (you should see `(.venv)` in your terminal prompt) before running the scripts.

### Complete Workflow (Recommended)

#### Option 1: Full Combined Workflow (One Command)
```bash
# Extract URLs, authenticate, and add to notebook in one command
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed" --login --notebook "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID"
```

#### Option 2: Step-by-Step Workflow

**Step 1: Extract URLs from Documentation**
```bash
# Extract from latest version (saves to urls.txt)
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed"

# Or specify versions
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed" --versions "latest,2.21,2.20"
```

**Step 2: Authenticate with Google (First time only)**
```bash
python3 scrape_add_links_nblm_script.py --login
```
- Opens browser window
- Log in to Google manually
- **IMPORTANT: Close the browser window after logging in** (saves session)

**Step 3: Create NotebookLM Notebook**
1. Go to [NotebookLM](https://notebooklm.google.com/)
2. Create a new notebook
3. Copy the notebook URL

**Step 4: Add URLs to Notebook**
```bash
python3 scrape_add_links_nblm_script.py --notebook "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID"
```
**Note**: Automatically combines `urls.txt` (scraped URLs) + `CQA_res.txt` (static resources)

## Detailed Usage

### Combined Workflow Examples

```bash
# Full workflow (extract → login → add):
python3 scrape_add_links_nblm_script.py --extract-toc URL --login --notebook NOTEBOOK_URL

# Extract then add (uses urls.txt automatically):
python3 scrape_add_links_nblm_script.py --extract-toc URL --notebook NOTEBOOK_URL

# Login then add (uses existing urls.txt):
python3 scrape_add_links_nblm_script.py --login --notebook NOTEBOOK_URL
```

### URL Extraction Mode

#### Extract with Default Version (latest)
```bash
python3 scrape_add_links_nblm_script.py --extract-toc "BASE_URL"
```
*Always saves to `urls.txt` unless `--toc-output` specified*

#### Extract with Specific Versions
```bash
python3 scrape_add_links_nblm_script.py --extract-toc "BASE_URL" --versions "2.21,2.22,latest"
```

#### Extract with Custom Output File
```bash
python3 scrape_add_links_nblm_script.py --extract-toc "BASE_URL" --toc-output custom_file.txt
```

### Authentication Mode
```bash
python3 scrape_add_links_nblm_script.py --login
```

### Notebook Management Mode

#### Use Default Files (Recommended)
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL"
```
*Automatically combines:*
- `urls.txt` (scraped URLs)
- `CQA_res.txt` (static CQA resources)

#### Specify Custom Links File
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL" --links-file custom_links.txt
```
*Still includes `CQA_res.txt` automatically*

#### Add Individual URLs
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL" --links "https://example.com" "https://youtube.com/watch?v=xyz"
```

## Advanced Options

### All Command Line Options

**Help file**
- `--help`: Lists all available options

**Extraction Mode**:
- `--extract-toc URL`: Base documentation URL to scrape
- `--toc-output FILE`: Output file for extracted links (default: urls.txt)
- `--versions LIST`: Comma-separated versions (default: latest)

**Notebook Mode**:
- `--notebook URL`: NotebookLM notebook URL
- `--links-file FILE`: Links file (default: urls.txt, always includes CQA_res.txt)
- `--links URL [URL...]`: Individual URLs to add

**Authentication**:
- `--login`: Run authentication process
- `--profile-path PATH`: Browser profile directory (default: ~/.browser_automation)

**Combined Workflows**:
You can combine any of the three main operations in a single command:
- `--extract-toc` + `--notebook`: Extract then add
- `--login` + `--notebook`: Login then add  
- `--extract-toc` + `--login` + `--notebook`: Full workflow

### Consistent File Handling

The script now uses **predictable file handling** for easier workflows:

- **Extraction**: Always saves to `urls.txt` (unless `--toc-output` specified)
- **Notebook Mode**: Always reads from `urls.txt` (unless `--links-file` specified)
- **Resource Combination**: Always includes `CQA_res.txt` static resources
- **No Guessing**: Clear, consistent behavior every time

## Usage Examples

### Example 1: Red Hat OpenShift AI Documentation (Full Workflow)
```bash
# One command to do everything
python3 scrape_add_links_nblm_script.py \
  --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed" \
  --login \
  --notebook "https://notebooklm.google.com/notebook/abc123"
```

### Example 2: Extract Different Documentation, Reuse Login
```bash
# Extract AI Inference Server docs (overwrites urls.txt)
python3 scrape_add_links_nblm_script.py \
  --extract-toc "https://docs.redhat.com/en/documentation/red_hat_ai_inference_server" \
  --notebook "https://notebooklm.google.com/notebook/abc123"
```

### Example 3: Multiple Versions
```bash
# Extract from multiple versions
python3 scrape_add_links_nblm_script.py \
  --extract-toc "https://docs.example.com/product" \
  --versions "v1.0,v2.0,latest" \
  --notebook "https://notebooklm.google.com/notebook/xyz789"
```

## Troubleshooting

### Playwright Browser Installation Issues
**Error**: "Executable doesn't exist at .../Chromium.app/Contents/MacOS/Chromium"
**Solution**: Install Playwright browsers:
```bash
# Navigate to project root
cd /Users/dobrenna/Documents/NLP_college/sandbox/add_links_notebook

# Activate virtual environment
source .venv/bin/activate

# Install Chromium browser
playwright install chromium

# Return to script directory
cd notebooklm/automation/add_scrapped_links_notebooklm
```

### Virtual Environment Issues
**Error**: "ModuleNotFoundError" or missing packages
**Solutions**:
1. Ensure virtual environment is activated: `source .venv/bin/activate`
2. Check you're in the right directory: should see `(.venv)` in prompt
3. Verify Playwright installation: `playwright --version`

### Browser Lock Issues
**Error**: "ProcessSingleton" errors
**Solution**: Clear browser lock files:
```bash
rm -f ~/.browser_automation/SingletonLock ~/.browser_automation/SingletonCookie ~/.browser_automation/SingletonSocket
```

### No Links File Found
**Error**: "Main links file not found - urls.txt"
**Solutions**:
1. Run `--extract-toc` first to create `urls.txt`
2. Specify `--links-file` with an existing file
3. Provide `--links` with individual URLs

### Login Required Errors
**Error**: "Could not find Add button" (all links fail)
**Solution**: Re-run login process:
```bash
python3 scrape_add_links_nblm_script.py --login
```

### URL Extraction Failures
**Error**: 404 errors during extraction
**Solutions**:
- Verify the base URL is correct
- Check if the versions exist (try "latest" first)
- Ensure the documentation site is accessible

### Timeout Issues
**Error**: Script times out clicking buttons
**Solutions**:
- Clear browser lock files (see above)
- Ensure you closed the browser window after logging in
- Try running the login step again

## Generated Files

- **`urls.txt`**: Primary file for scraped URLs (gets overwritten with each extraction)
- **`CQA_res.txt`**: Static CQA resources (always included automatically)
- **Combined**: Script automatically merges both files when adding to notebook

## Notes

- **Virtual Environment**: Always activate your virtual environment (`source .venv/bin/activate`) before running scripts
- **Browser Installation**: One-time setup with `playwright install chromium`
- **Authentication**: Login session is saved in `~/.browser_automation` directory
- **File Consistency**: Always uses `urls.txt` for extracted URLs for predictable behavior
- **Resource Integration**: Automatically includes static CQA resources from `CQA_res.txt`
- **Rate Limiting**: Script waits 3 seconds between URLs to avoid overwhelming NotebookLM
- **Browser**: Uses Chromium in visible mode so you can see progress
- **Content Types**: Supports both website URLs and YouTube videos
- **File Format**: All URL files should have one URL per line
- **Combined Workflows**: Can run extraction, authentication, and notebook addition in single command

