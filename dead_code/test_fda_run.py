#!/usr/bin/env python3
"""Test run: Navigate to FDA website using SmolClaw cognitive system."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from smolclaw.cognitive_loop import CognitiveLoop

def main():
    print("\n" + "=" * 70)
    print("  SmolClaw Cognitive System - FDA Website Test")
    print("=" * 70)
    
    # Target URL
    target_url = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRL/rl.cfm"
    
    print(f"\n🎯 Target: {target_url}")
    print("\nStarting cognitive loop...")
    
    # Create cognitive loop
    loop = CognitiveLoop(max_loops=10)
    
    # Process intent
    intent = f"Navigate to {target_url} and tell me what you see on the page"
    
    print(f"\n📝 Intent: {intent}")
    print("\n" + "=" * 70)
    
    try:
        result = loop.process_intent(intent)
        
        print("\n" + "=" * 70)
        print("  Result")
        print("=" * 70)
        print(f"\n✅ Success: {result.get('success', False)}")
        print(f"📄 Result: {result.get('result', 'N/A')[:500]}")
        
        # Show state
        state = loop.get_state()
        print(f"\n📊 Agent State: {state.get('agent_state', 'unknown')}")
        print(f"📈 Events Recorded: {state.get('event_count', 0)}")
        
        # Show planner stats
        planner_stats = state.get('planner_stats', {})
        print(f"🧠 Plans Generated: {planner_stats.get('total_plans', 0)}")
        print(f"📊 Success Rate: {planner_stats.get('success_rate', 0):.1%}")
        
        print("\n" + "=" * 70)
        print("  ✅ Test Complete")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
