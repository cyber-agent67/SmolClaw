#!/usr/bin/env python3
"""
GitHub Release Information Extractor using Vision Models
Uses Playwright for browser automation and vision models for navigation
"""

import csv
import json
import heapq
import re
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
        self.vision = VisionAssistant() # logic moved to config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.max_steps = config.MAX_NAVIGATION_STEPS
        self.screenshot_dir = Path(config.SCREENSHOT_DIR)
        self.screenshot_dir.mkdir(exist_ok=True)
        Path(config.DATA_DIR).mkdir(exist_ok=True)
        
        # Experience Cache
        self.experience_file = Path(config.DATA_DIR) / "navigation_experience.json"
        self.experience = self._load_experience()

    def _load_experience(self) -> Dict[str, Any]:
        if self.experience_file.exists():
            try:
                with open(self.experience_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load experience: {e}")
        return {}

    def _save_experience(self):
        try:
            with open(self.experience_file, 'w') as f:
                json.dump(self.experience, f, indent=2)
        except Exception as e:
            print(f"Failed to save experience: {e}")

    def _get_state_key(self, url: str) -> str:
        """Normalize URL to serve as a state key"""
        # Remove query params and fragments for stable caching
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # We assume the path is specific enough for this task
        return urlunparse(parsed._replace(query="", fragment=""))

    async def setup(self):
        """Initialize Playwright browser with persistent context"""
        self.playwright = await async_playwright().start()
        
        # Use a user data directory for persistent context (non-incognito)
        user_data_dir = os.path.join(os.getcwd(), "browser_data")
        
        # launch_persistent_context returns a BrowserContext, not a Browser
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={'width': 1920, 'height': 1080},
            args=['--no-sandbox', '--disable-dev-shm-usage'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        # Persistent context usually opens a page by default, but let's ensure we have one
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

    async def execute_strategy_step(self, step_count: int) -> bool:
        """Execute one step of the navigation strategy, using cache if available"""
        
        current_url = self.page.url
        state_key = self._get_state_key(current_url)
        
        # Check Cache
        if state_key in self.experience:
            print(f"[{step_count}] Using CACHED experience for {state_key}")
            cached_instruction = self.experience[state_key]
            return await self._execute_instruction(cached_instruction, step_count, is_cached=True)

        # 1. Capture State
        screenshot_path = self.screenshot_dir / f"step_{step_count}.png"
        await self.page.screenshot(path=screenshot_path, full_page=True)
        
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode('utf-8')
            
        print(f"[{step_count}] Analyzing state at {current_url}...")
        
        # 2. Get Strategy from Claude
        instruction = await self.vision.get_navigation_instruction(
            screenshot_data=screenshot_data,
            current_url=current_url,
            step_name=f"step_{step_count}"
        )
        
        if not instruction:
            print("No instruction received from strategy model.")
            return False

        # Execute and potentially cache
        success = await self._execute_instruction(instruction, step_count, screenshot_data=screenshot_data, state_key=state_key)
        return success

    async def _execute_instruction(self, instruction: Dict[str, Any], step_count: int, 
                                 is_cached: bool = False, 
                                 screenshot_data: str = None, 
                                 state_key: str = None) -> bool:
        """Internal helper to execute an instruction and handle tagging/caching"""
        
        action = instruction.get("action")
        target_desc = instruction.get("element_description", "")
        print(f"Action: {action} - {json.dumps(target_desc)}")
        
        if action == "done":
            return True
            
        elif action == "click":
            selectors = instruction.get("selectors", [])
            
            # If not cached, we need to generate selectors
            if not is_cached and not selectors:
                # 3. Get Tagging from GPT-4o (Vision)
                # Get HTML snippet for context
                html_content = await self.page.evaluate("document.body.outerHTML")
                html_snippet = html_content[:20000] 
                
                print(f"Requesting selectors for: '{target_desc}'...")
                selectors_data = await self.vision.suggest_dom_selectors(
                    goal=target_desc,
                    html_snippet=html_snippet,
                    screenshot_data=screenshot_data,
                    step_count=step_count
                )
                selectors = selectors_data.get("selectors", [])
                print(f"GPT-4o suggested selectors: {selectors}")
                
                # Update instruction with discovered selectors for caching
                instruction["selectors"] = selectors

            # 4. Execute Click
            clicked = False
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible():
                        print(f"Clicking selector: {selector}")
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        clicked = True
                        break
                except Exception as e:
                    print(f"Failed to click {selector}: {e}")
                    continue
            
            if not clicked:
                if not is_cached:
                    print("Selectors failed. Attempting fallback by role/text...")
                    try:
                        role = instruction.get("role", "button")
                        await self.page.get_by_role(role, name=target_desc).first.click()
                        clicked = True
                    except:
                        try:
                            await self.page.get_by_text(target_desc).first.click()
                            clicked = True
                        except:
                            pass
            
            if clicked and not is_cached:
                # Save to experience only if successful interaction
                if state_key:
                    self.experience[state_key] = instruction
                    self._save_experience()
            
        elif action == "type":
            # Type usually doesn't need complex selectors, but could use the same logic
            text = instruction.get("text", "")
            role = instruction.get("role", "textbox")
            try:
                await self.page.get_by_role(role, name=target_desc).first.fill(text)
                await self.page.keyboard.press("Enter")
                if not is_cached and state_key:
                    self.experience[state_key] = instruction
                    self._save_experience()
            except Exception as e:
                print(f"Type failed: {e}")
                
        elif action == "navigate":
            url = instruction.get("url", "")
            if url:
                await self.page.goto(url)
                await self.page.wait_for_load_state("networkidle")
                if not is_cached and state_key:
                    self.experience[state_key] = instruction
                    self._save_experience()
                
        elif action == "extract":
            print("Strategy requested extraction.")
            return True 
            
        return False

    async def navigate_to_releases(self, repo: str = "openclaw/openclaw") -> Dict[str, Any]:
        """A* Navigation with Claude-powered heuristic calculation"""
        
        # Start at Repo
        start_url = f"https://github.com/{repo}"
        print(f"Navigating to {start_url}...")
        await self.page.goto(start_url)
        await self.page.wait_for_load_state("networkidle")
        
        # A* Search State
        visited_urls = {start_url}
        discovery_counts = {start_url: 1}
        pq = []
        
        # Evaluation logging
        csv_file = Path(config.DATA_DIR) / "search_evaluation.csv"
        visited_csv = Path(config.DATA_DIR) / "visited.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Score"])
        
        with open(visited_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "DiscoveryCount"])

        def get_url_depth(url: str) -> int:
            """Calculate depth based on URL path segments"""
            from urllib.parse import urlparse
            path = urlparse(url).path
            return len([s for s in path.split('/') if s])

        async def evaluate_page_links(page) -> list:
            """Phase 1: Discovery - Extract all links and page context for Brain"""
            p_url = page.url
            print(f"   -> Scanning: {p_url}")
            
            # Capture screenshot for Eyes
            screenshot_path = self.screenshot_dir / f"scan_{len(visited_urls)}.png"
            await page.screenshot(path=screenshot_path, full_page=False)  # Viewport only for speed
            with open(screenshot_path, "rb") as f:
                screenshot_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Get DOM tree for Brain
            dom_tree = await page.evaluate("document.body.outerHTML")
            
            # Extract all links
            links = await page.evaluate("""() => {
                const results = [];
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                anchors.forEach(a => {
                    const text = a.innerText.trim();
                    const html = a.outerHTML;
                    results.push({ href: a.href.split('#')[0], text, html });
                });
                return results;
            }""")
            
            # Filter to only GitHub links not yet visited
            candidates = []
            for link in links:
                href = link['href']
                if "github.com" not in href:
                    continue
                
                discovery_counts[href] = discovery_counts.get(href, 0) + 1
                
                if href in visited_urls:
                    continue
                
                candidates.append({
                    "url": href,
                    "text": link['text'][:200],  # Limit text length for API
                    "depth": get_url_depth(href),
                    "discovery_count": discovery_counts[href]
                })
            
            # Phase 2: Eyes → Brain → Scores
            if candidates:
                print(f"   -> Found {len(candidates)} new candidate links")
                scored_links = await self.vision.calculate_link_heuristics(
                    candidates=candidates,
                    repo=repo,
                    screenshot_data=screenshot_data,
                    dom_tree=dom_tree
                )
                
                # Build priority queue entries
                discovered_nodes = []
                for scored in scored_links:
                    h_score = scored.get("heuristic_value", 0)
                    url = scored["url"]
                    depth = scored["depth"]
                    
                    if h_score > 0:
                        depth_reward = depth * 100
                        popularity_bonus = discovery_counts.get(url, 1) * 10
                        f_score = h_score + depth_reward + popularity_bonus
                        discovered_nodes.append((-f_score, h_score, depth_reward, depth, url, scored.get("text", "")[:50]))
                
                return discovered_nodes
            
            return []

        # Bootstrap: score initial page links
        initial_nodes = await evaluate_page_links(self.page)
        for node in initial_nodes:
            heapq.heappush(pq, node)
        
        best_overall_page_info = None
        best_overall_f = -1
        max_loops = 50

        for i in range(max_loops):
            if not pq:
                print("A* Open Set is empty. Search exhaustive.")
                break
                
            neg_f, h_score, d_reward, u_depth, url, link_text = heapq.heappop(pq)
            f_score = -neg_f
            
            if url in visited_urls:
                continue
            
            print(f"--- A* Step {i+1} | F:{f_score} | H:{h_score} | Depth:{u_depth} | URL:{url[:60]} ---")
            
            try:
                new_page = await self.context.new_page()
                visited_urls.add(url)
                
                # Log to visited.csv
                with open(visited_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([url, discovery_counts.get(url, 1)])

                await new_page.goto(url, timeout=30000)
                await new_page.wait_for_load_state("networkidle")
                
                # Evaluation Log
                with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([url, f_score])

                # Ask Brain: Is the goal reached?
                print(f"   -> Asking Brain if goal is reached...")
                screenshot_path = self.screenshot_dir / f"goal_check_{i}.png"
                await new_page.screenshot(path=screenshot_path, full_page=False)
                with open(screenshot_path, "rb") as f:
                    screenshot_data = base64.b64encode(f.read()).decode('utf-8')
                
                dom_tree = await new_page.evaluate("document.body.outerHTML")
                
                goal_decision = await self.vision.is_goal_reached(
                    screenshot_data=screenshot_data,
                    url=url,
                    dom_tree=dom_tree,
                    repo=repo
                )
                
                print(f"   -> Brain decision: {goal_decision.get('goal_reached')} (confidence: {goal_decision.get('confidence')}%)")
                print(f"   -> Reasoning: {goal_decision.get('reasoning')}")

                if goal_decision.get("goal_reached") and goal_decision.get("confidence", 0) >= 80:
                    print(f"✓ Brain confirmed: Goal State Reached! URL: {url}")
                    self.page = new_page
                    return await self.extract_release_info_smart()

                # Track best release tag page as fallback
                if "releases/tag" in url:
                    if f_score > best_overall_f:
                        best_overall_f = f_score
                        if best_overall_page_info:
                            await best_overall_page_info['page'].close()
                        best_overall_page_info = {"page": new_page, "f": f_score, "url": url}
                    else:
                        await new_page.close()
                else:
                    # Explore children
                    child_nodes = await evaluate_page_links(new_page)
                    for node in child_nodes:
                        heapq.heappush(pq, node)
                    await new_page.close()
                
            except Exception as e:
                print(f"Failed to explore {url}: {e}")
                continue

        # Fallback to best found page
        if best_overall_page_info:
            print(f"Selecting Best Page (F={best_overall_f}): {best_overall_page_info['url']}")
            self.page = best_overall_page_info["page"]
            return await self.extract_release_info_smart()

        return {
            "repository": repo,
            "status": "Search Ended",
            "visited_count": len(visited_urls)
        }
        
    async def extract_release_info_smart(self) -> Dict[str, Any]:
        """Final extraction"""
        print("Starting extraction phase...")
        html_content = await self.page.content()
        screenshot_path = self.screenshot_dir / "final_extraction.png"
        await self.page.screenshot(path=screenshot_path, full_page=True)
        
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode('utf-8')
            
        # Use simple extraction
        return await self.vision.extract_with_vision_and_html(screenshot_data, html_content[:50000])
    
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
    parser = argparse.ArgumentParser(description="GitHub Release Navigator using Vision Models")
    parser.add_argument("--repo", default="openclaw/openclaw", help="Repository in format 'owner/repo'")
    parser.add_argument("--prompt", help="Natural language prompt for navigation")
    parser.add_argument("--output", default=os.path.join("data", "output.json"), help="Output JSON file path")
    parser.add_argument("--vision-model", default=config.VISION_MODEL, help="Vision model to use")
    
    args = parser.parse_args()
    
    print("Starting GitHub Navigator...")
    navigator = Navigator(vision_model=args.vision_model)
    
    try:
        await navigator.setup()
        
        # Start navigation
        if args.prompt:
            # For natural language prompts (bonus feature)
            print(f"Executing prompt: {args.prompt}")
            # Additional logic for prompt-based navigation
        else:
            # Standard repository navigation
            result = await navigator.navigate_to_releases(args.repo)
        
        # Save result
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Results saved to {args.output}")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await navigator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())