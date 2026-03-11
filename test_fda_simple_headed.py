#!/usr/bin/env python3
"""Simple test: Navigate to FDA website with HEADED browser."""

import sys
import os
import time

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def main():
    print("\n" + "=" * 70)
    print("  SmolClaw - FDA Website Test (HEADED BROWSER)")
    print("=" * 70)
    
    target_url = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRL/rl.cfm"
    
    print(f"\n🎯 Target: {target_url}")
    print("🖥️  Browser: HEADED (visible)")
    print("\n⏳ Starting...")
    
    try:
        # Initialize browser
        print("\n[1/4] Initializing browser...")
        from smolclaw.agent.config.BrowserConfig import BrowserConfig
        from smolclaw.agent.interactions.browser.Initialize import InitializeBrowser
        
        config = BrowserConfig()
        config.headless = False  # HEADED!
        browser = InitializeBrowser.execute(config)
        print("     ✓ Browser launched")
        
        # Navigate
        print(f"\n[2/4] Navigating to FDA...")
        from smolclaw.agent.tools.ToolRegistry import set_browser_url, get_browser_snapshot
        
        result = set_browser_url(target_url)
        print(f"     ✓ {result[:80]}")
        
        # Wait
        print("\n[3/4] Waiting for page load (5 sec)...")
        time.sleep(5)
        
        # Get snapshot
        print("\n[4/4] Getting page info...")
        snapshot = get_browser_snapshot()
        
        import json
        data = json.loads(snapshot)
        
        print("\n" + "=" * 70)
        print("  Page Loaded Successfully!")
        print("=" * 70)
        print(f"\n📄 URL: {data.get('url', 'N/A')}")
        print(f"📝 Title: {data.get('title', 'N/A')}")
        print(f"🔗 Links: {len(data.get('links', []))}")
        
        print("\n" + "=" * 70)
        print("  ✅ Success! Browser is open and visible.")
        print("=" * 70)
        print("\n💡 The browser window should be visible on your screen.")
        print("   It will close automatically in 10 seconds.")
        print("\n")
        
        # Wait so user can see
        for i in range(10, 0, -1):
            print(f"   Closing in {i}... ", end='\r', flush=True)
            time.sleep(1)
        
        # Cleanup
        print("\n[Cleanup] Closing browser...")
        browser.is_running = True
        from smolclaw.agent.interactions.browser.Quit import QuitBrowser
        QuitBrowser.execute(browser)
        print("     ✓ Closed")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
