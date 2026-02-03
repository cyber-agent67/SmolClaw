#!/usr/bin/env python3
"""
Complete scraping script demonstrating all A* power tools working together
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the parent project directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from navigate import MCPClient


async def complete_scraping_demo():
    """Complete scraping demo using all A* power tools"""
    print("Complete Scraping Demo with A* Power Tools")
    print("=" * 60)
    
    # Start the MCP server client
    client = MCPClient("mcp_server.py")
    
    try:
        await client.start()
        
        print("\n1. Starting at GitHub homepage...")
        result = await client.call_tool("navigate_to_url", {"url": "https://github.com"})
        print(f"   [OK] Navigated to: {result['current_url']}")
        
        print("\n" + "="*60)
        print("PHASE 1: A* PAGE FINDER - Discovering relevant pages")
        print("="*60)
        
        # Use A* Page Finder to find documentation pages
        print("\n2. Using A* Page Finder to find API documentation...")
        docs_result = await client.call_tool("find_valuable_pages", {
            "topic": "api documentation",
            "max_pages": 3
        })
        print(f"   [OK] Found {len(docs_result['top_pages'])} API documentation pages:")
        for i, page in enumerate(docs_result['top_pages'], 1):
            print(f"     {i}. '{page['text']}' -> {page['url']}")
            print(f"        Heuristic Score: {page['heuristic_score']:.4f}, Relevance: {page['relevance']}")
        
        # Select the highest-scoring documentation page
        if docs_result['top_pages']:
            selected_doc_page = docs_result['top_pages'][0]
            print(f"\n3. Navigating to selected documentation page: {selected_doc_page['url']}")
            nav_result = await client.call_tool("navigate_to_url", {"url": selected_doc_page['url']})
            print(f"   [OK] Navigated to: {nav_result['current_url']}")
        
        print("\n" + "="*60)
        print("PHASE 2: A* DOM FINDER - Locating specific elements")
        print("="*60)
        
        # Use A* DOM Finder to find specific elements on the documentation page
        print("\n4. Using A* DOM Finder to locate 'authentication' section...")
        auth_result = await client.call_tool("find_element_on_page", {
            "target_element": "authentication",
            "search_strategy": "by_importance"
        })
        print(f"   [OK] Found {auth_result['total_found']} elements related to 'authentication'")
        if auth_result['found_elements']:
            top_auth = auth_result['found_elements'][0]
            print(f"   [OK] Top result: {top_auth['tag']} element with selector '{top_auth['selector']}'")
            print(f"   [OK] Heuristic Score: {top_auth['heuristic_score']:.4f}")
            print(f"   [OK] Text: '{top_auth['text'][:100]}...'")
        
        # Find API endpoints
        print("\n5. Using A* DOM Finder to locate 'API endpoints'...")
        endpoint_result = await client.call_tool("find_element_on_page", {
            "target_element": "api endpoints",
            "search_strategy": "by_importance"
        })
        print(f"   [OK] Found {endpoint_result['total_found']} elements related to 'api endpoints'")
        if endpoint_result['found_elements']:
            top_endpoint = endpoint_result['found_elements'][0]
            print(f"   [OK] Top result: {top_endpoint['tag']} element with selector '{top_endpoint['selector']}'")
            print(f"   [OK] Heuristic Score: {top_endpoint['heuristic_score']:.4f}")
        
        print("\n" + "="*60)
        print("PHASE 3: A* PATHFINDING - Navigating to target elements")
        print("="*60)
        
        # Use A* Pathfinding to find a specific element
        print("\n6. Using A* Pathfinding to find 'REST API' section...")
        path_result = await client.call_tool("find_path_to_element", {
            "target_element": "REST API",
            "strategy": "shortest"
        })
        print(f"   [OK] Path found: {path_result['path_found']}")
        if path_result['path_found']:
            print(f"   [OK] Steps required: {len(path_result['steps'])}")
            print(f"   [OK] Total cost: {path_result['total_cost']}")
            for i, step in enumerate(path_result['steps'], 1):
                print(f"     Step {i}: {step['action']} '{step['element_text'][:50]}...' using selector '{step['selector']}'")
        
        print("\n" + "="*60)
        print("PHASE 4: COMBINED A* POWER TOOLS - Complex scraping task")
        print("="*60)
        
        # Navigate back to GitHub homepage
        print("\n7. Returning to GitHub homepage for comprehensive scraping...")
        await client.call_tool("navigate_to_url", {"url": "https://github.com"})
        
        # Find trending repositories using A* tools
        print("\n8. Using A* Page Finder to find 'trending' related pages...")
        trending_result = await client.call_tool("find_valuable_pages", {
            "topic": "trending repositories",
            "max_pages": 2
        })
        print(f"   [OK] Found {len(trending_result['top_pages'])} trending-related pages:")
        for i, page in enumerate(trending_result['top_pages'], 1):
            print(f"     {i}. '{page['text']}' -> {page['url']}")
            print(f"        Heuristic Score: {page['heuristic_score']:.4f}")
        
        # Find search functionality
        print("\n9. Using A* DOM Finder to locate search elements...")
        search_result = await client.call_tool("find_element_on_page", {
            "target_element": "search",
            "search_strategy": "by_importance"
        })
        print(f"   [OK] Found {search_result['total_found']} search-related elements")
        if search_result['found_elements']:
            top_search = search_result['found_elements'][0]
            print(f"   [OK] Top search element: {top_search['tag']} with selector '{top_search['selector']}'")
            print(f"   [OK] Heuristic Score: {top_search['heuristic_score']:.4f}")
        
        # Get current page state for final analysis
        print("\n10. Getting final page state...")
        state = await client.call_tool("get_page_state", {"include_screenshot": False})
        print(f"   [OK] Current URL: {state['url']}")
        print(f"   [OK] Found {state['link_count']} links on the page")
        
        print("\n" + "="*60)
        print("COMPLETE SCRAPING DEMO FINISHED SUCCESSFULLY!")
        print("="*60)
        
        print("\nA* Power Tools Used:")
        print("[OK] A* Page Finder: Discovered relevant documentation pages")
        print("[OK] A* DOM Finder: Located specific elements on pages")
        print("[OK] A* Pathfinding: Found optimal paths to target elements")
        print("[OK] Combined usage: Performed complex scraping tasks")
        print("[OK] Heuristic scoring: Ranked results by relevance")
        
    except Exception as e:
        print(f"Error during complete scraping demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(complete_scraping_demo())