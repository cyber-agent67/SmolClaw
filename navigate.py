#!/usr/bin/env python3
"""
GitHub Release Information Extractor using Vision Models
Uses an MCP Server for browser automation and vision models for navigation.
"""

import json
import argparse
import base64
import os
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import config
from vision_helper import VisionAssistant

# Simple MCP Client for communicating with the server subprocess
class MCPClient:
    def __init__(self, server_script: str):
        self.server_script = server_script
        self.process = None
        self._request_id = 0

    async def start(self):
        """Start the MCP server subprocess"""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        # Use the same python interpreter
        cmd = [sys.executable, self.server_script]
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr, 
            env=env,
            limit=1024*1024*20  # Increase buffer limit to 20MB for large screenshots
        )
        print("MCP Server started.")
        
        # Initialize MCP Protocol (Handshake)
        # 1. Send initialize
        self._request_id += 1
        init_request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "navigate-client", "version": "1.0"}
            }
        }
        self.process.stdin.write(json.dumps(init_request).encode('utf-8') + b"\n")
        await self.process.stdin.drain()
        
        # Read initialize response
        while True:
            line = await self.process.stdout.readline()
            if not line: break
            try:
                msg = json.loads(line.decode('utf-8'))
                if msg.get("id") == self._request_id:
                     print("MCP Initialized.")
                     break
            except: pass
            
        # 2. Send initialized notification
        init_notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        self.process.stdin.write(json.dumps(init_notify).encode('utf-8') + b"\n")
        await self.process.stdin.drain()

    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool on the MCP server using JSON-RPC"""
        if arguments is None:
            arguments = {}
            
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        # Send Request
        request_json = json.dumps(request)
        self.process.stdin.write(request_json.encode('utf-8') + b"\n")
        await self.process.stdin.drain()
        
        # Read Response
        while True:
            line = await self.process.stdout.readline()
            if not line:
                raise Exception("MCP Server closed connection unexpectedly")
            
            try:
                message = json.loads(line.decode('utf-8'))
                if message.get("id") == self._request_id:
                    if "error" in message:
                         raise Exception(f"MCP Error: {message['error']}")
                    
                    # MCP returns a list of content items (TextContent/ImageContent)
                    # We usually want the text from the first item which contains our JSON result
                    result = message.get("result", {})
                    content = result.get("content", [])
                    if content and content[0]["type"] == "text":
                         # The server returns JSON string inside the text field
                         try:
                             return json.loads(content[0]["text"])
                         except:
                             return content[0]["text"]
                    return content
            except json.JSONDecodeError:
                continue

    async def stop(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("MCP Server stopped.")

class Navigator:
    def __init__(self, vision_model: str = config.VISION_MODEL):
        self.vision = VisionAssistant()
        self.client = MCPClient("mcp_server.py")
        self.max_steps = config.MAX_NAVIGATION_STEPS
        self.screenshot_dir = Path(config.SCREENSHOT_DIR)
        self.screenshot_dir.mkdir(exist_ok=True, parents=True)
        Path(config.DATA_DIR).mkdir(exist_ok=True, parents=True)
        
    async def setup(self):
        """Initialize MCP Client connection"""
        await self.client.start()

    async def execute_action(self, instruction: Dict[str, Any], step_count: int, screenshot_data: str) -> bool:
        """Execute a single action via MCP"""
        action = instruction.get("action")
        target_desc = instruction.get("element_description", "")
        print(f"[{step_count}] Executing Action: {action} ({target_desc})")
        
        if action == "done" or action == "extract":
            return True

        try:
            if action == "click":
                selectors = instruction.get("selectors", [])

                # Fetch selectors if missing
                if not selectors:
                    # Try using the new DOM querying tools for better element identification
                    try:
                        # First, try to find elements by text description
                        elements_by_text = await self.client.call_tool("find_elements_by_text", {
                            "text": target_desc,
                            "case_sensitive": False
                        })

                        if elements_by_text.get("count", 0) > 0:
                            elements = elements_by_text.get("elements", [])
                            # Select the most relevant element based on the description
                            for element in elements:
                                if target_desc.lower() in element.get("textContent", "").lower():
                                    # Try to create a selector from the element's attributes
                                    attrs = element.get("attributes", {})
                                    if attrs.get("id"):
                                        selectors = [f"#{attrs['id']}"]
                                        break
                                    elif attrs.get("data-testid"):
                                        selectors = [f"[data-testid='{attrs['data-testid']}']"]
                                        break
                                    elif attrs.get("class"):
                                        classes = attrs["class"].split()
                                        if classes:
                                            selectors = [f".{'.'.join(classes)}"]
                                            break

                            # If we still don't have selectors, try querying by tag
                            if not selectors:
                                for element in elements:
                                    tag = element.get("tagName", "")
                                    if tag:
                                        attrs = element.get("attributes", {})
                                        if attrs.get("class"):
                                            classes = attrs["class"].split()
                                            if classes:
                                                selectors = [f"{tag}.{'.'.join(classes)}"]
                                                break
                                        elif attrs.get("id"):
                                            selectors = [f"{tag}#{attrs['id']}"]
                                            break
                        else:
                            # If no elements found by text, try using the semantic DOM tree
                            print(f"   -> No elements found by text, trying semantic DOM tree...")
                            try:
                                # Get the semantic DOM tree to find elements
                                semantic_dom = await self.client.call_tool("get_clean_dom_tree", {
                                    "include_attributes": True,
                                    "include_text": True,
                                    "semantic_only": True
                                })

                                # This would require additional logic to parse the semantic DOM tree
                                # and find elements matching the target description
                                # For now, we'll fall back to the original method
                            except Exception as semantic_error:
                                print(f"   -> Semantic DOM tree search failed: {semantic_error}")
                    except Exception as e:
                        print(f"   -> DOM text search failed: {e}")
                        # Fallback to original method
                        res = await self.client.call_tool("get_page_html", {"max_length": 20000})
                        html_snippet = res.get("html", "")

                        print(f"Requesting selectors for: '{target_desc}'...")
                        selectors_data = await self.vision.suggest_dom_selectors(
                            goal=target_desc,
                            html_snippet=html_snippet,
                            screenshot_data=screenshot_data,
                            step_count=step_count
                        )
                        selectors = selectors_data.get("selectors", [])

                # Try clicking
                clicked = False
                for selector in selectors:
                    try:
                        print(f"   -> Clicking selector: {selector}")
                        await self.client.call_tool("click_element", {"selector": selector})
                        clicked = True
                        break
                    except Exception as e:
                        print(f"   -> Failed to click {selector}: {e}")

                if not clicked:
                     print("   -> All selectors failed.")

                return clicked

            elif action == "type":
                text = instruction.get("text", "")
                role = instruction.get("role", "textbox")
                
                # Fallback: specific fix for GitHub search if no selector logic in prompt
                if "search" in target_desc.lower() or "input" in role:
                    # Common GitHub search bar selector
                    selector = "input[name='q']" # Fallback heuristic
                    
                    try:
                        await self.client.call_tool("type_input", {"selector": selector, "text": text})
                        await self.client.call_tool("press_key", {"key": "Enter"})
                        return True
                    except Exception as e:
                        print(f"   -> Type failed: {e}")

            elif action == "navigate":
                url = instruction.get("url", "")
                if url:
                    print(f"   -> Navigating to {url}")
                    await self.client.call_tool("navigate_to_url", {"url": url})
                    return True
                    
        except Exception as e:
            print(f"Error executing action via MCP: {e}")
            return False
            
        return False

    async def step_vision_loop(self, goal: str, max_attempts: int = 5) -> bool:
        """Execute a vision-driven loop to achieve a specific sub-goal using MCP"""
        print(f"\n[Sub-Goal]: {goal}")

        for attempt in range(1, max_attempts + 1):
            # Get State via MCP
            state = await self.client.call_tool("get_page_state", {"include_screenshot": True})
            current_url = state.get("url", "")
            print(f"   Attempt {attempt}/{max_attempts} at {current_url}")

            screenshot_data = state.get("screenshot_base64", "")
            if not screenshot_data:
                print("   -> Failed to capture screenshot from MCP.")
                return False

            # Save screenshot for debug
            screenshot_path = self.screenshot_dir / f"goal_{goal[:10]}_{attempt}.png"
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))

            # Get Instruction
            instruction = await self.vision.get_navigation_instruction(
                screenshot_data=screenshot_data,
                current_url=current_url,
                step_name=f"{goal}_{attempt}",
                goal=goal
            )

            if not instruction:
                print("   -> No instruction.")
                return False

            action = instruction.get("action")
            print(f"   -> Plan: {action} ({instruction.get('element_description', '')})")

            if action in ["done", "extract"]:
                print("   -> Sub-goal considered complete.")
                return True

            success = await self.execute_action(instruction, attempt, screenshot_data)
            if not success:
                print("   -> Action failed.")

                # If action failed, try using enhanced DOM querying to find alternative elements
                try:
                    element_description = instruction.get("element_description", "")
                    if element_description:
                        print(f"   -> Trying enhanced DOM querying for: '{element_description}'")

                        # First, try using the A* DOM Finder to locate the element efficiently
                        print(f"   -> Trying A* DOM Finder for: '{element_description}'")
                        try:
                            dom_finder_result = await self.client.call_tool("find_element_on_page", {
                                "target_element": element_description,
                                "search_strategy": "by_importance"
                            })

                            if dom_finder_result.get("total_found", 0) > 0:
                                found_elements = dom_finder_result.get("found_elements", [])
                                print(f"   -> A* DOM Finder found {len(found_elements)} elements matching '{element_description}'")

                                # Try clicking the most important element first
                                for element in found_elements:
                                    selector = element.get("selector")
                                    if selector:
                                        try:
                                            print(f"   -> Trying A* DOM Finder selector: {selector}")
                                            await self.client.call_tool("click_element", {"selector": selector})
                                            print(f"   -> A* DOM Finder click succeeded: {selector}")
                                            success = True
                                            break  # Break after first successful click
                                        except Exception as e:
                                            print(f"   -> A* DOM Finder click failed: {e}")
                                            continue
                            else:
                                print(f"   -> A* DOM Finder didn't find elements, trying A* pathfinding")
                        except Exception as dom_finder_error:
                            print(f"   -> A* DOM Finder failed: {dom_finder_error}")

                        # If A* DOM Finder didn't work, try A* pathfinding
                        if not success:
                            print(f"   -> Trying A* pathfinding for: '{element_description}'")
                            try:
                                astar_result = await self.client.call_tool("find_path_to_element", {
                                    "target_element": element_description,
                                    "strategy": "shortest"
                                })

                                if astar_result.get("path_found", False):
                                    steps = astar_result.get("steps", [])
                                    print(f"   -> A* pathfinding found {len(steps)} steps to target")

                                    # Execute the path
                                    for step in steps:
                                        if step.get("action") == "click":
                                            selector = step.get("selector")
                                            if selector:
                                                try:
                                                    print(f"   -> Executing A* path step: clicking {selector}")
                                                    await self.client.call_tool("click_element", {"selector": selector})
                                                    print(f"   -> A* path step succeeded: {selector}")
                                                    success = True
                                                    break  # Break after first successful step
                                                except Exception as e:
                                                    print(f"   -> A* path step failed: {e}")
                                                    continue
                                else:
                                    print(f"   -> A* pathfinding didn't find direct path, continuing with other methods")
                            except Exception as astar_error:
                                print(f"   -> A* pathfinding failed: {astar_error}")

                        # If both A* methods failed, try using the traditional DOM querying methods
                        if not success:
                            # Use the new DOM querying tools to find alternative elements
                            elements_by_text = await self.client.call_tool("find_elements_by_text", {
                                "text": element_description,
                                "case_sensitive": False
                            })

                            if elements_by_text.get("count", 0) > 0:
                                print(f"   -> Found {elements_by_text['count']} elements matching '{element_description}'")

                                # Try clicking the first matching element
                                elements = elements_by_text.get("elements", [])
                                for element in elements:
                                    attrs = element.get("attributes", {})
                                    selector = None

                                    # Try to create a unique selector
                                    if attrs.get("id"):
                                        selector = f"#{attrs['id']}"
                                    elif attrs.get("data-testid"):
                                        selector = f"[data-testid='{attrs['data-testid']}']"
                                    elif attrs.get("class"):
                                        classes = attrs["class"].split()
                                        if classes:
                                            selector = f".{'.'.join(classes)}"

                                    if selector:
                                        try:
                                            print(f"   -> Trying alternative selector: {selector}")
                                            await self.client.call_tool("click_element", {"selector": selector})
                                            print(f"   -> Alternative click succeeded with selector: {selector}")
                                            success = True
                                            break
                                        except Exception as e:
                                            print(f"   -> Alternative click failed: {e}")
                                            continue

                        if not success:
                            # Try using the semantic DOM tree to find elements
                            print(f"   -> Trying semantic DOM tree search...")
                            try:
                                semantic_dom_result = await self.client.call_tool("get_clean_dom_tree", {
                                    "include_attributes": True,
                                    "include_text": True,
                                    "semantic_only": True
                                })

                                # This could be enhanced further to search the semantic DOM tree
                                # for elements matching the description
                            except Exception as semantic_error:
                                print(f"   -> Semantic DOM tree search failed: {semantic_error}")

                        if not success:
                            # Try querying elements by role if available
                            role = instruction.get("role", "")
                            if role:
                                query_result = await self.client.call_tool("query_elements", {
                                    "selector": f"[role='{role}'], button, a, input[type='{role}']"
                                })

                                if query_result.get("count", 0) > 0:
                                    elements = query_result.get("elements", [])
                                    for element in elements:
                                        # Check if this element matches our target
                                        text_content = element.get("textContent", "").lower()
                                        if element_description.lower() in text_content:
                                            attrs = element.get("attributes", {})
                                            selector = None

                                            if attrs.get("id"):
                                                selector = f"#{attrs['id']}"
                                            elif attrs.get("class"):
                                                classes = attrs["class"].split()
                                                if classes:
                                                    selector = f".{'.'.join(classes)}"

                                            if selector:
                                                try:
                                                    print(f"   -> Trying role-based selector: {selector}")
                                                    await self.client.call_tool("click_element", {"selector": selector})
                                                    print(f"   -> Role-based click succeeded with selector: {selector}")
                                                    success = True
                                                    break
                                                except Exception as e:
                                                    print(f"   -> Role-based click failed: {e}")
                                                    continue
                except Exception as dom_query_error:
                    print(f"   -> Enhanced DOM querying failed: {dom_query_error}")

        print("   -> Max attempts reached for this sub-goal.")
        return False

    async def run_structured_flow(self, start_url: str, final_goal: str, repo_name: str = None, extract_fields: list = None) -> Dict[str, Any]:
        """Refactored execution flow with AI-generated navigation steps via MCP."""
        if extract_fields is None:
            extract_fields = ["version", "tag", "author"]
            
        print(f"Starting Structured Navigation Flow (via MCP)...")
        
        # Step 1: Start at Homepage
        print("\n=== Initialize: Navigate to Start URL ===")
        try:
            await self.client.call_tool("navigate_to_url", {"url": start_url})
        except Exception as e:
            print(f"Failed to load start URL: {e}")
            return {}

        # Generate Plan
        print("\n=== Generating Navigation Plan ===")
        plan_goal = final_goal
        if repo_name and "openclaw" in repo_name:
             plan_goal = f"Find the latest release for repository '{repo_name}' on GitHub. Go to the repository, click Releases, click on the specific latest version title to see details, and then extract the data."
        
        steps = await self.vision.generate_navigation_plan(plan_goal)
        print("Generated Plan:")
        for i, s in enumerate(steps):
            print(f"  {i+1}. {s}")
            
        # Execute Steps
        for i, step_desc in enumerate(steps):
            print(f"\n=== STEP {i+1}: {step_desc} ===")
            if "extract" in step_desc.lower() and i == len(steps) - 1:
                print("   -> (Extraction Phase logic will be handled below)")
                continue

            success = await self.step_vision_loop(step_desc, max_attempts=4)
            if not success:
                print(f"   -> Warning: Step {i+1} might have failed or been skipped.")
        
        # Final Extraction
        print("\n=== FINAL: Extraction ===")
        state = await self.client.call_tool("get_page_state", {"include_screenshot": True})
        screenshot_data = state.get("screenshot_base64")
        html_content = state.get("html")
        
        data = await self.vision.extract_with_vision_and_html(
            screenshot_data,
            html_content[:50000],
            extract_fields=extract_fields
        )
        return data

    async def cleanup(self):
        """Clean up MCP resources"""
        await self.client.stop()

async def main():
    parser = argparse.ArgumentParser(description="GitHub Release Navigator (MCP Powered)")
    parser.add_argument("--repo", help="Repository in format 'owner/repo'")
    parser.add_argument("--url", default=config.GITHUB_HOMEPAGE, help="Starting URL")
    parser.add_argument("--prompt", help="Natural language prompt")
    parser.add_argument("--output", default=os.path.join("data", "output.json"), help="Output JSON file path")
    parser.add_argument("--vision-model", default=config.VISION_MODEL, help="Vision model to use")
    
    args = parser.parse_args()
    prompt = args.prompt
    start_url = args.url
    
    if args.repo and not prompt:
        prompt = f"Find the latest release for repository {args.repo}"
    
    print(f"Goal: {prompt}")
    print(f"Starting at: {start_url}")
    
    navigator = Navigator(vision_model=args.vision_model)
    
    try:
        await navigator.setup()
        if args.repo:
            result = await navigator.run_structured_flow(start_url, prompt, repo_name=args.repo)
        else:
             result = await navigator.run_structured_flow(start_url, prompt)
        
        output = {
            "repository": args.repo if args.repo else "unknown",
            "latest_release": result
        }
        
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