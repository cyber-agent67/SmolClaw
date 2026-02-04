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
        # Create the prompt refinement function
        def refine_prompt_with_opus(raw_prompt):
            import hashlib
            import json
            import re
            
            # Simple keyword/prompt cache
            cache_file = "keyword_cache.json"
            cache = {}
            
            # Load cache if exists
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache = json.load(f)
                except:
                    pass
            
            # Create a "bag of words" string of the raw prompt to use as key
            # 1. Lowercase and remove punctuation
            clean_prompt = re.sub(r'[^\w\s]', '', raw_prompt.lower())
            # 2. Split into words, sort them, and join
            words = sorted(list(set(clean_prompt.split())))
            bag_of_words = " ".join(words)
            
            print(f"Prompt Bag-of-Words: '{bag_of_words}'")
            
            if bag_of_words in cache:
                print(f"Loading refined prompt from cache for '{raw_prompt}'")
                return cache[bag_of_words]

            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    print("Warning: ANTHROPIC_API_KEY not found. Using raw prompt.")
                    return raw_prompt
                    
                client = anthropic.Anthropic(api_key=api_key)
                print(f"Refining prompt with Claude (actually Sonnet 4.5)... '{raw_prompt}'")
                
                message = client.beta.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    temperature=0,
                    system="You are an expert Prompt Engineer for an autonomous web agent. Your goal is to take a user's raw request and rewrite it into a precise, step-by-step strategic instruction that maximizes the agent's success rate. Analyze the intent, break it down, and output ONLY the refined prompt. IMPORTANT: Make sure the final instruction explicitly tells the agent to return the requested information in a clear and concise JSON format, and to use `final_answer(...)` to terminate.",
                    messages=[
                        {"role": "user", "content": f"Refine this user request for a web agent: {raw_prompt}"}
                    ],
                    betas=["context-1m-2025-08-07"]
                )
                refined = message.content[0].text
                print(f"Refined Prompt: {refined}")
                
                # Save to cache
                cache[bag_of_words] = refined
                with open(cache_file, 'w') as f:
                    json.dump(cache, f, indent=2)
                    
                return refined
            except Exception as e:
                print(f"Prompt refinement failed: {e}. Using raw prompt.")
                return raw_prompt

        # Refine the prompt
        refined_user_prompt = refine_prompt_with_opus(args.prompt) if args.prompt else "Perform a web search and navigate to find relevant information"

        # Define the system prompt with the REFINED user prompt
        enhanced_prompt = f"""
        You are an intelligent, autonomous web navigation agent acting as a STRATEGIC ADVISOR and EXECUTIONER.
        Your goal is not just to "click buttons", but to understand the *human intent* behind the request and deliver the most helpful result.

        USER REQUEST (Refined): "{refined_user_prompt}"

        **ADVISOR PROTOCOL (Phase 1: Deep Cognition)**
        CRITICAL: You are powered by a multi-model architecture.
        You MUST start every complex task by using your `think` tool.
        This triggers your "Higher Cognition" (Claude) to analyze the user's request and build a high-level strategy.
        
        DO NOT PROCEED WITHOUT THINKING FIRST.
        
        1. **Call `think(query=...)`**: Ask your higher brain how to approach this specific user goal.
        2. **Execute Strategy**: Follow the plan returned by the thought engine.

        **EXECUTION PROTOCOL (Phase 2: ReAct - Reason & Act)**
        Operate as a machine, but follow the Advisor's plan.
        Use the following loop for every step:

        1. **OBSERVE**: Scan the current URL and DOM. What relevant information is present?
        2. **CHECK PLAN**: Are we on track with the Advisor's strategy?
        3. **THINK**: CRITICAL! You MUST output a "Thought:" block explaining your reasoning before generating code.
           Example:
           Thought: The user wants to find the release. The Advisor said to check the 'Releases' tab. I see a link for 'Releases'. I will click it.
        4. **ACT**: Generate Python code to use tools (WebSearch, set_browser_url, Grappling Hook/find_path_to_target, etc.).

        **NAVIGATION RULES**:
        - **Scout Ahead**: Use `find_path_to_target` (Grappling Hook) to find the best link before clicking.
        - **Search First**: If the destination is ambiguous, use `WebSearchTool` to find the exact entry point.
        - **Structured Data**: Prefer extracting data from the DOM properties or structured text over visual guesses.

        **ENVIRONMENT**:
        - Current URL: {args.url}
        - Tools allow: DOM access, URL navigation, Tab management, Searching, Deep Thinking.

        IMPORTANT:
        - When completed, IMMEDIATELY output a code block with the final result, formatted clearly for the user.
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