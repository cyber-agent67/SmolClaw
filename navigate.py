#!/usr/bin/env python3
"""
GitHub Release Information Extractor using Vision Models
Uses Playwright for browser automation and vision models for navigation.
"""

import json
import argparse
import base64
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import config

from playwright.async_api import async_playwright
from vision_helper import VisionAssistant

class Navigator:
    def __init__(self, vision_model: str = config.VISION_MODEL):
        self.vision = VisionAssistant()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.max_steps = config.MAX_NAVIGATION_STEPS
        self.screenshot_dir = Path(config.SCREENSHOT_DIR)
        self.screenshot_dir.mkdir(exist_ok=True, parents=True) # Ensure parents exist
        Path(config.DATA_DIR).mkdir(exist_ok=True, parents=True)
        
        # Experience Cache (Simple implementation)
        self.experience_file = Path(config.DATA_DIR) / "navigation_experience.json"
        
    async def setup(self):
        """Initialize Playwright browser with persistent context"""
        self.playwright = await async_playwright().start()
        
        # Use a user data directory for persistent context (non-incognito)
        user_data_dir = os.path.join(os.getcwd(), "browser_data")
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={'width': 1280, 'height': 800}, # Standard desktop size
            args=['--no-sandbox', '--disable-dev-shm-usage'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

    async def execute_action(self, instruction: Dict[str, Any], step_count: int, screenshot_data: str) -> bool:
        """Execute a single action from the strategy model"""
        action = instruction.get("action")
        target_desc = instruction.get("element_description", "")
        print(f"[{step_count}] Executing Action: {action} ({target_desc})")
        
        if action == "done":
            return True
            
        elif action == "extract":
            return True

        elif action == "click":
            # Try to click using selectors provided or fallback to text/role
            selectors = instruction.get("selectors", [])
            clicked = False
            
            # If no selectors, we might need to ask for them (Lazy selector generation)
            if not selectors:
                html_snippet = await self.page.evaluate("document.body.outerHTML")
                html_snippet = html_snippet[:20000]
                print(f"Requesting selectors for: '{target_desc}'...")
                selectors_data = await self.vision.suggest_dom_selectors(
                    goal=target_desc,
                    html_snippet=html_snippet,
                    screenshot_data=screenshot_data,
                    step_count=step_count
                )
                selectors = selectors_data.get("selectors", [])
                
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible():
                        print(f"   -> Clicking selector: {selector}")
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        clicked = True
                        break
                except Exception as e:
                    print(f"   -> Failed to click {selector}: {e}")
            
            if not clicked:
                print("   -> Selectors failed. Attempting fallback by role/text...")
                try:
                    role = instruction.get("role", "button")
                    await self.page.get_by_role(role, name=target_desc).first.click()
                    clicked = True
                except:
                    try:
                        await self.page.get_by_text(target_desc).first.click()
                        clicked = True
                    except Exception as e:
                        print(f"   -> Fallback click failed: {e}")
            
            if clicked:
                try:
                    await self.page.wait_for_timeout(2000) # Wait for UI update
                    await self.page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass
            return clicked

        elif action == "type":
            text = instruction.get("text", "")
            role = instruction.get("role", "textbox")
            try:
                # Try generic selectors first
                await self.page.get_by_role(role).first.fill(text)
                await self.page.keyboard.press("Enter")
                await self.page.wait_for_load_state("networkidle")
                await self.page.wait_for_timeout(2000)
                return True
            except:
                try: # Specific for GitHub search (common fallback)
                    await self.page.locator("input[name='q']").first.fill(text)
                    await self.page.keyboard.press("Enter")
                    await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(2000)
                    return True
                except Exception as e:
                    print(f"   -> Type failed: {e}")

        elif action == "navigate":
            url = instruction.get("url", "")
            if url:
                print(f"   -> Navigating to {url}")
                await self.page.goto(url)
                await self.page.wait_for_load_state("networkidle")
                return True
                
        return False

    async def run_sequential_flow(self, start_url: str, prompt: str, extract_fields: list = None) -> Dict[str, Any]:
        """
        Execute the sequential Navigation Flow
        """
        if extract_fields is None:
            extract_fields = ["version", "tag", "author"]
            
        print(f"Starting navigation at {start_url}...")
        try:
            await self.page.goto(start_url)
            await self.page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Failed to load start URL: {e}")
            return {}

        for step in range(1, self.max_steps + 1):
            print(f"\n--- Step {step} ---")
            current_url = self.page.url
            
            # 1. Capture State
            screenshot_path = self.screenshot_dir / f"step_{step}.png"
            await self.page.screenshot(path=screenshot_path, full_page=False)
            
            with open(screenshot_path, "rb") as f:
                screenshot_data = base64.b64encode(f.read()).decode('utf-8')
                
            # 2. Get Instruction
            instruction = await self.vision.get_navigation_instruction(
                screenshot_data=screenshot_data,
                current_url=current_url,
                step_name=f"step_{step}", # Passing step name as context
                goal=prompt
            )
            
            if not instruction:
                print("No instruction received. Stopping.")
                break
                
            print(f"Plan: {instruction.get('action')} - {instruction.get('element_description', '')}")
            
            # 3. Check for completion/extraction
            if instruction.get("action") in ["extract", "done"]:
                print("Target reached. Initiating extraction...")
                html_content = await self.page.content()
                
                # Extract
                data = await self.vision.extract_with_vision_and_html(
                    screenshot_data,
                    html_content[:50000],
                    extract_fields=extract_fields
                )
                return data
            
            # 4. Execute Action
            success = await self.execute_action(instruction, step, screenshot_data)
            if not success:
                print("Action failed. Waiting and retrying once...")
                await self.page.wait_for_timeout(2000)
                success = await self.execute_action(instruction, step, screenshot_data)
                if not success:
                    print("Action failed again.")
        
        return {"status": "failed", "reason": "Max steps or navigation failure"}

    async def cleanup(self):
        """Clean up resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    parser = argparse.ArgumentParser(description="GitHub Release Navigator")
    parser.add_argument("--repo", help="Repository in format 'owner/repo'")
    parser.add_argument("--url", default=config.GITHUB_HOMEPAGE, help="Starting URL")
    parser.add_argument("--prompt", help="Natural language prompt")
    parser.add_argument("--output", default=os.path.join("data", "output.json"), help="Output JSON file path")
    parser.add_argument("--vision-model", default=config.VISION_MODEL, help="Vision model to use")
    
    args = parser.parse_args()
    
    # Determine mode
    prompt = args.prompt
    start_url = args.url
    
    if args.repo and not prompt:
        prompt = f"Find the latest release for repository {args.repo}"
    
    print(f"Goal: {prompt}")
    print(f"Starting at: {start_url}")
    
    navigator = Navigator(vision_model=args.vision_model)
    
    try:
        await navigator.setup()
        
        result = await navigator.run_sequential_flow(start_url, prompt)
        
        # Format output
        output = {
            "repository": args.repo if args.repo else "unknown",
            "latest_release": result
        }
        
        # Save
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
            
        print(f"Results saved to {args.output}")
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await navigator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())