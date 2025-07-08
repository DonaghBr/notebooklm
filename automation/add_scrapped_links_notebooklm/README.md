# NotebookLM Automation Tools

Automate the process of extracting documentation URLs and adding them as sources to NotebookLM notebooks using browser automation.

## 🛠️ Scripts Overview

### `scrape_add_links_nblm_script.py` - Enhanced URL Extraction & Notebook Management
- **Based on** This code is adapted from https://github.com/sshnaidm/notebooklm/blob/master/automation/add_links_script.py   
- **Extract URLs** from documentation sites with version support
- **Smart file detection** for seamless workflow
- **Add URLs to NotebookLM** with authentication management
- **All-in-one solution** for extraction and notebook loading

## ✨ Features

- ✅ **URL Extraction**: Scrape documentation hierarchies with version support
- ✅ **Smart File Handling**: Auto-detects available URL files
- ✅ **Version Support**: Defaults to "latest" or specify custom versions
- ✅ **Authentication Management**: Persistent Google login sessions
- ✅ **Bulk URL Loading**: Add multiple URLs to NotebookLM automatically
- ✅ **Error Handling**: Comprehensive error messages and recovery options
- ✅ **YouTube & Website Support**: Handles both content types

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- A NotebookLM account

### Installation

#### Step 1: Create Virtual Environment
```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

#### Step 2: Install Dependencies
```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Install browser binaries for Playwright
python3 -m playwright install
```

**Note**: Always activate your virtual environment before running the scripts:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### Complete Workflow (Recommended)

#### Step 1: Extract URLs from Documentation
```bash
# Extract from latest version (default)
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed" --toc-output my_links.txt

# Or specify versions
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed" --versions "latest,2.21,2.20" --toc-output my_links.txt
```

#### Step 2: Authenticate with Google (First time only)
```bash
python3 scrape_add_links_nblm_script.py --login
```
- Opens browser window
- Log in to Google manually
- **🔑 IMPORTANT: Close the browser window after logging in** (saves session)

#### Step 3: Create NotebookLM Notebook
1. Go to [NotebookLM](https://notebooklm.google.com/)
2. Create a new notebook
3. Copy the notebook URL

#### Step 4: Add URLs to Notebook
```bash
python3 scrape_add_links_nblm_script.py --notebook "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID"
```
**Note**: No need to specify `--links-file` - it automatically detects your extracted URLs!

## 📖 Detailed Usage

### URL Extraction Mode

#### Extract with Default Version (latest)
```bash
python3 scrape_add_links_nblm_script.py --extract-toc "BASE_URL" --toc-output output.txt
```

#### Extract with Specific Versions
```bash
python3 scrape_add_links_nblm_script.py --extract-toc "BASE_URL" --versions "2.21,2.22,latest" --toc-output output.txt
```

### Notebook Management Mode

#### Auto-detect Links File
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL"
```
Automatically searches for: `urls.txt`, `my_links.txt`, `urls_clean.txt`

#### Specify Links File
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL" --links-file custom_links.txt
```

#### Add Individual URLs
```bash
python3 scrape_add_links_nblm_script.py --notebook "NOTEBOOK_URL" --links "https://example.com" "https://youtube.com/watch?v=xyz"
```

### Authentication Mode
```bash
python3 scrape_add_links_nblm_script.py --login
```

## 🔧 Advanced Options

### All Command Line Options

**Extraction Mode**:
- `--extract-toc URL`: Base documentation URL to scrape
- `--toc-output FILE`: Output file for extracted links (default: urls.txt)
- `--versions LIST`: Comma-separated versions (default: latest)

**Notebook Mode**:
- `--notebook URL`: NotebookLM notebook URL
- `--links-file FILE`: Links file (auto-detects if not specified)
- `--links URL [URL...]`: Individual URLs to add

**Authentication**:
- `--login`: Run authentication process
- `--profile-path PATH`: Browser profile directory (default: ~/.browser_automation)

### Smart File Detection

When `--links-file` is not specified, the script automatically searches for:
1. `urls.txt` (default extraction output)
2. `my_links.txt` (common custom name)
3. `urls_clean.txt` (your clean file)

## 🎯 Usage Examples

### Example 1: Red Hat OpenShift AI Documentation
```bash
# Extract latest documentation
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed"

# Login (first time only)
python3 scrape_add_links_nblm_script.py --login

# Add to notebook (auto-detects urls.txt)
python3 scrape_add_links_nblm_script.py --notebook "https://notebooklm.google.com/notebook/abc123"
```

### Example 2: Multiple Versions
```bash
# Extract from multiple versions
python3 scrape_add_links_nblm_script.py --extract-toc "https://docs.example.com/product" --versions "v1.0,v2.0,latest" --toc-output multi_version_links.txt

# Add to notebook
python3 scrape_add_links_nblm_script.py --notebook "https://notebooklm.google.com/notebook/xyz789" --links-file multi_version_links.txt
```

### Example 3: Using the Simple Script
```bash
# Login
python3 add_links_script.py --login

# Add URLs
python3 add_links_script.py --notebook "https://notebooklm.google.com/notebook/abc123" --links-file urls_clean.txt
```

## 🛠️ Troubleshooting

### Virtual Environment Issues
**Error**: "ModuleNotFoundError" or missing packages
**Solutions**:
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Install dependencies: `python3 -m pip install -r requirements.txt`
3. Install browser binaries: `python3 -m playwright install`

### Browser Lock Issues
**Error**: "ProcessSingleton" errors
**Solution**: Clear browser lock files:
```bash
rm -f ~/.browser_automation/SingletonLock ~/.browser_automation/SingletonCookie ~/.browser_automation/SingletonSocket
```

### No Links File Found
**Error**: "No links file found!"
**Solutions**:
1. Run `--extract-toc` first to create a links file
2. Specify `--links-file` with an existing file
3. Provide `--links` with individual URLs

### Login Required Errors
**Error**: Authentication failures
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

## 📁 Generated Files

- `urls.txt`: Default extraction output
- `my_links.txt`: Common custom extraction output
- `urls_clean.txt`: Your cleaned URL file (from RTF conversion)

## 📝 Notes

- **Virtual Environment**: Always activate your virtual environment (`source venv/bin/activate`) before running scripts
- **Dependencies**: All required packages are listed in `requirements.txt` for easy installation
- **Authentication**: Login session is saved in `~/.browser_automation` directory
- **Rate Limiting**: Script waits 2 seconds between URLs to avoid overwhelming NotebookLM
- **Browser**: Uses Chromium in visible mode so you can see progress
- **Content Types**: Supports both website URLs and YouTube videos
- **File Format**: All URL files should have one URL per line

## 🎉 Your Red Hat OpenShift AI Documentation

Your setup is perfect for creating a comprehensive NotebookLM assistant with Red Hat OpenShift AI documentation. The extracted URLs cover:

- Installation and configuration
- Data science workflows
- Model serving and management
- Troubleshooting and best practices
- Tutorials and examples

This creates an AI assistant that can help with OpenShift AI questions across all documentation versions! 