#!/usr/bin/env python3
"""Test: Navigate to FDA website with a HEADED (visible) browser and cognitive analysis."""

import json
import time

from dotenv import load_dotenv
load_dotenv()

TARGET_URL = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRL/rl.cfm"


def main():
    print("\n" + "=" * 70)
    print("  SmolClaw - FDA Website Navigation (HEADED BROWSER)")
    print("=" * 70)

    print(f"\n🎯 Target: {TARGET_URL}")
    print("🖥️  Browser: HEADED (visible window)")
    print("\n⏳ Starting browser navigation...")
    print("=" * 70)

    try:
        print("\n[1/6] Loading browser modules...")
        from smolclaw.tools.smolhand import BrowserLayerService
        from smolclaw.cognitive import EventStore, IntentReceivedEvent

        print("[2/6] Initializing HEADED browser...")
        from smolclaw.agent.config.BrowserConfig import BrowserConfig
        from smolclaw.agent.interactions.browser.Initialize import InitializeBrowser

        config = BrowserConfig()
        config.headless = False
        browser = InitializeBrowser.execute(config)
        print("     ✓ Browser launched (visible window)")

        print(f"[3/6] Navigating to FDA website...")
        from smolclaw.agent.tools.ToolRegistry import set_browser_url, get_browser_snapshot

        nav_result = set_browser_url(TARGET_URL)
        print(f"     ✓ Navigation result: {nav_result[:100]}")

        print("[4/6] Waiting for page to load...")
        time.sleep(3)

        print("[5/6] Capturing page snapshot...")
        snapshot = get_browser_snapshot()
        snapshot_data = json.loads(snapshot)

        print("\n" + "=" * 70)
        print("  Page Information")
        print("=" * 70)
        print(f"\n📄 URL: {snapshot_data.get('url', 'N/A')}")
        print(f"📝 Title: {snapshot_data.get('title', 'N/A')}")
        print(f"📊 Links Found: {len(snapshot_data.get('links', []))}")

        links = snapshot_data.get('links', [])[:10]
        if links:
            print(f"\n🔗 Sample Links (first 10):")
            for i, link in enumerate(links, 1):
                href = link.get('href', '')[:60]
                text = link.get('text', '')[:40]
                print(f"   {i}. {text} → {href}")

        print("\n[6/6] Analyzing page with cognitive tools...")
        from smolclaw.cognitive_loop import CognitiveLoop

        loop = CognitiveLoop(max_loops=5)
        intent = f"""
        Analyze the current FDA page at {TARGET_URL}

        Tasks:
        1. Describe what sections are visible
        2. Identify the main purpose of this page
        3. List the main actions available
        4. Extract any important information
        """

        result = loop.process_intent(intent)

        print("\n" + "=" * 70)
        print("  Cognitive Analysis Results")
        print("=" * 70)
        print(f"\n✅ Success: {result.get('success', False)}")
        print(f"📄 Analysis: {result.get('result', 'N/A')[:500]}")

        state = loop.get_state()
        print(f"\n📊 Agent State: {state.get('agent_state', {}).get('state', 'unknown')}")
        print(f"📈 Events: {state.get('event_count', 0)}")

        print("\n" + "=" * 70)
        print("  ✅ FDA Website Test Complete (HEADED)")
        print("=" * 70)
        print("\n💡 Browser window is still open.")
        print("   You can interact with it manually or close it.\n")

        results = {
            'url': snapshot_data.get('url'),
            'title': snapshot_data.get('title'),
            'link_count': len(snapshot_data.get('links', [])),
            'sample_links': links,
            'cognitive_result': result,
            'timestamp': time.time(),
        }
        with open('fda_headed_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("📁 Results saved to: fda_headed_results.json\n")

        print("⏳ Browser will close in 10 seconds...")
        time.sleep(10)

        print("\n[Cleanup] Closing browser...")
        from smolclaw.agent.interactions.browser.Quit import QuitBrowser
        browser.is_running = True
        QuitBrowser.execute(browser)
        print("     ✓ Browser closed")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
