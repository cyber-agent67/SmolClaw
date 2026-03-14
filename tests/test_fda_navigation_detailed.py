#!/usr/bin/env python3
"""Test: Navigate to FDA website and extract information (detailed with event replay)."""

import json

from dotenv import load_dotenv
load_dotenv()

from smolclaw.cognitive_loop import CognitiveLoop

TARGET_URL = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRL/rl.cfm"


def main():
    print("\n" + "=" * 70)
    print("  SmolClaw Cognitive System - FDA Website Navigation")
    print("=" * 70)

    print(f"\n🎯 Target Website: {TARGET_URL}")
    print("\n📋 Task: Navigate to the FDA Registration & Listing page")
    print("   and describe what information is available")

    loop = CognitiveLoop(max_loops=15, persistence_path="./fda_test_events")

    intent = f"""
    Navigate to {TARGET_URL}

    Tasks:
    1. Go to the FDA Registration & Listing page
    2. Describe what you see on the page
    3. Identify the main sections and links
    4. Tell me what actions can be performed on this page

    Use your vision and exploration tools to analyze the page.
    """

    print(f"\n📝 Intent: Navigate and analyze FDA website")
    print("\n" + "=" * 70)
    print("  Starting Cognitive Processing")
    print("=" * 70)

    try:
        result = loop.process_intent(intent)
        state = loop.get_state()
        events = loop.replay()

        print("\n" + "=" * 70)
        print("  Cognitive Processing Results")
        print("=" * 70)

        print(f"\n✅ Success: {result.get('success', False)}")
        print(f"📄 Result Summary: {result.get('result', 'N/A')[:300]}")

        print(f"\n📊 Final Agent State: {state.get('agent_state', {}).get('state', 'unknown')}")
        print(f"📈 Total Events: {state.get('event_count', 0)}")

        planner_stats = state.get('planner_stats', {})
        print(f"\n🧠 Planner Statistics:")
        print(f"   - Plans Generated: {planner_stats.get('total_plans', 0)}")
        print(f"   - Success Rate: {planner_stats.get('success_rate', 0):.1%}")

        print(f"\n📋 Event Summary:")
        event_types = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        for event_type, count in sorted(event_types.items()):
            print(f"   - {event_type}: {count}")

        read_model = state.get('read_model', {})
        if read_model:
            print(f"\n📊 Read Model:")
            print(f"   - Current Goal: {read_model.get('current_goal', 'N/A')[:100]}")
            print(f"   - Tools Used: {len(read_model.get('executed_tools', []))}")

        print("\n" + "=" * 70)
        print("  ✅ FDA Website Test Complete")
        print("=" * 70)
        print(f"\n💾 Event log saved to: ./fda_test_events/\n")

        with open('fda_test_results.json', 'w') as f:
            json.dump({'result': result, 'state': state, 'event_count': len(events)}, f, indent=2, default=str)

        print("📁 Detailed results saved to: fda_test_results.json\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
