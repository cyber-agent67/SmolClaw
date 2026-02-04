#!/usr/bin/env python3
"""
Web Navigation Agent using Vision Models
Implements autonomous web navigation with A* algorithms
"""

import json
import argparse
import os
import sys
from pathlib import Path

# Add the current directory to the path to import agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Global registry to keep track of browser instances
class BrowserRegistry:
    def __init__(self):
        self.active_browsers = []

    def register_browser(self, browser):
        """Register a browser instance"""
        if browser not in self.active_browsers:
            self.active_browsers.append(browser)

    def unregister_browser(self, browser):
        """Unregister a browser instance"""
        if browser in self.active_browsers:
            self.active_browsers.remove(browser)

    def close_all_browsers(self):
        """Close all registered browser instances"""
        print("Closing all registered browsers...")
        for browser in self.active_browsers[:]:  # Copy the list to avoid modification during iteration
            try:
                if browser:
                    # Use helium to properly close the browser
                    import helium
                    helium.kill_browser()
            except:
                pass  # Ignore errors when closing browsers
        self.active_browsers.clear()

# Global browser registry
browser_registry = BrowserRegistry()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Web Navigation Agent (Autonomous Web Navigation Implementation)")
    parser.add_argument("--url", default="https://www.google.com", help="Starting URL")
    parser.add_argument("--prompt", help="Natural language prompt")
    parser.add_argument("--output", default=os.path.join("data", "output.json"), help="Output JSON file path")

    # Additional arguments for model configuration
    parser.add_argument("--model-type", type=str, default="LiteLLMModel",
                       help="The model type to use (e.g., OpenAIServerModel, LiteLLMModel, TransformersModel, InferenceClientModel)")
    parser.add_argument("--model-id", type=str, default="gpt-4o",
                       help="The model ID to use for the specified model type")

    return parser.parse_args()

def main():
    args = parse_arguments()

    try:
        # Import agent here to avoid circular dependencies
        from agent import run_agent_with_args

        # Enhance the prompt to make the agent smarter about navigation
        enhanced_prompt = f"""
        You are an autonomous web navigation agent operating as a MACHINE, not a human.
        You do NOT browse like a person. You operate using structured programmatic access to URLs, DOM trees, link graphs, and browser controls.

        Your task: {args.prompt}

        ENVIRONMENT INFORMATION:
        1. Current URL: {args.url}
        2. You have access to the full DOM tree of the current page
        3. You can see all hyperlinks and hrefs that connect directly to other pages

        NAVIGATION STRATEGY:
        1. First, use the WebSearchTool to understand the directory structure of the target site
        2. Learn about the site's URL patterns and navigation structure
        3. Parse the DOM tree to understand the current page structure
        4. Identify hyperlinks and hrefs that lead to the target destination
        5. If you find a direct link to the next page you need, CHANGE THE URL DIRECTLY
        6. Navigate efficiently by using URL navigation when possible
        7. Trust structured data (DOM, URLs) over visual elements
        8. Minimize clicks by going directly to target URLs when available

        Remember: You are a machine operating in a browser environment.
        You see DOM trees, URLs, and structured data - not visual elements.
        When you see a hyperlink to your target, navigate directly via URL.

        IMPORTANT: When you have completed the task, use the quit_browser() tool to close the browser.
        """

        # Create a mock args object with the enhanced prompt
        import types
        enhanced_args = types.SimpleNamespace(
            url=args.url,
            prompt=enhanced_prompt,
            output=args.output,
            model_type=args.model_type,
            model_id=args.model_id
        )

        # Call the agent with parsed arguments
        result = run_agent_with_args(enhanced_args)

        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Just save the raw result from the agent
        output = result if result else {"error": "No result returned from agent"}

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to {args.output}")
        print(json.dumps(output, indent=2))

    finally:
        # Always close all registered browsers when the navigation process ends, even if there's an error
        try:
            from agent import cleanup_resources
            cleanup_resources()
        except:
            pass  # If cleanup function doesn't exist, use the registry method
            browser_registry.close_all_browsers()

if __name__ == "__main__":
    main()