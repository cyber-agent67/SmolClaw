# GitHub Release Navigator

A vision-based tool that autonomously navigates GitHub to extract release information without hardcoded selectors.

## Features

- Uses vision models (GPT-4V/Claude) to understand page content
- No hardcoded CSS selectors or XPath
- Autonomous navigation from GitHub homepage to releases
- Structured JSON output
- Natural language prompt support (bonus)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium