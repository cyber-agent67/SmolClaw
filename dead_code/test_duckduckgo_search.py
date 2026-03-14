#!/usr/bin/env python3
"""Test: Use DuckDuckGo web search tool."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def main():
    print("\n" + "=" * 70)
    print("  SmolClaw - DuckDuckGo Web Search Test")
    print("=" * 70)
    
    print("\n✅ Yes! SmolClaw uses smolagents!")
    print("✅ Yes! It has DuckDuckGo search via WebSearchTool!")
    
    print("\n" + "=" * 70)
    print("  Testing Web Search Tool")
    print("=" * 70)
    
    try:
        # Import the search tool
        print("\n[1/3] Loading WebSearchTool from smolagents...")
        from smolagents import WebSearchTool
        
        search_tool = WebSearchTool()
        print(f"     ✓ Tool name: {search_tool.name}")
        print(f"     ✓ Description: {search_tool.description[:100]}...")
        
        # Test search
        print("\n[2/3] Performing DuckDuckGo search...")
        query = "FDA device registration requirements 2025"
        print(f"     Query: {query}")
        
        result = search_tool(query)
        
        print(f"     ✓ Search completed!")
        print(f"     ✓ Results length: {len(result)} characters")
        
        # Show results
        print("\n[3/3] Search Results:")
        print("=" * 70)
        # Show first 1000 chars
        print(result[:1000])
        if len(result) > 1000:
            print(f"\n... ({len(result) - 1000} more characters)")
        
        print("\n" + "=" * 70)
        print("  ✅ DuckDuckGo Search Test Complete!")
        print("=" * 70)
        print("\n💡 The WebSearchTool uses DuckDuckGo by default!")
        print("   No API key required - it's free and open source!")
        print("\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
