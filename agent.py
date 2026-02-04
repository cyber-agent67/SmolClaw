"""
Agentic Web Navigation with RAG Capabilities
Accumulates past experiences for more efficient navigation
Core agent functionality without command-line interface
"""

import json
import os
import time
import base64
from typing import Dict, Any, List
from datetime import datetime
import pickle
import re

# Import for browser automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import for smolagents framework
from io import BytesIO
from time import sleep
import helium
from dotenv import load_dotenv
from PIL import Image

from smolagents import CodeAgent, WebSearchTool, tool
from smolagents.agents import ActionStep
from smolagents.cli import load_model

# Global driver variable for helium
# global driver

# Navigation stack to maintain history for go_back functionality
navigation_stack = []

# Tab management for helium browser
class TabManager:
    def __init__(self):
        self.tabs = {}  # Dictionary to store tab information
        self.current_tab = None
        self.tab_counter = 0

    def create_new_tab(self, url=None):
        """Create a new tab and optionally navigate to a URL"""
        from helium import switch_to, start_chrome
        import helium

        self.tab_counter += 1
        tab_id = f"tab_{self.tab_counter}"

        # In helium, we simulate tabs by storing URLs
        self.tabs[tab_id] = {
            'id': tab_id,
            'url': url,
            'history': [url] if url else [],
            'active': True
        }

        self.current_tab = tab_id
        if url:
            helium.go_to(url)

        return tab_id

    def switch_tab(self, tab_id):
        """Switch to a specific tab"""
        if tab_id in self.tabs:
            self.current_tab = tab_id
            from helium import go_to
            current_url = self.tabs[tab_id]['url']
            if current_url:
                go_to(current_url)
            return True
        return False

    def close_tab(self, tab_id):
        """Close a specific tab"""
        if tab_id in self.tabs:
            del self.tabs[tab_id]
            if self.current_tab == tab_id:
                # Switch to another available tab
                available_tabs = list(self.tabs.keys())
                if available_tabs:
                    self.current_tab = available_tabs[0]
                else:
                    self.current_tab = None
            return True
        return False

    def get_active_tab(self):
        """Get the current active tab"""
        return self.current_tab

    def get_all_tabs(self):
        """Get all tabs"""
        return self.tabs

# Initialize tab manager
tab_manager = TabManager()

class ExperienceMemory:
    """RAG-based memory system to store and retrieve navigation experiences"""

    def __init__(self, memory_file="navigation_missions.json"):
        self.memory_file = memory_file
        self.experiences = self.load_memory()

    def load_memory(self) -> List[Dict]:
        """Load previous experiences from JSON file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_memory(self):
        """Save experiences to JSON file"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.experiences, f, indent=2)

    def add_experience(self, experience: Dict):
        """Add a new experience to memory"""
        experience['timestamp'] = datetime.now().isoformat()
        self.experiences.append(experience)
        self.save_memory()

    def find_similar_experiences(self, current_context: str, threshold: float = 0.7) -> List[Dict]:
        """Find similar past experiences based on context"""
        # For now, using a simple keyword matching approach
        # In a more advanced implementation, this would use embeddings
        similar = []
        context_lower = current_context.lower()

        for exp in self.experiences:
            exp_context = exp.get('context', '').lower()
            # Simple similarity check
            if any(keyword in exp_context for keyword in context_lower.split()[:5]):  # Check first 5 keywords
                similar.append(exp)

        return similar[-5:]  # Return last 5 similar experiences

    def get_successful_patterns(self, task_description: str) -> List[Dict]:
        """Retrieve successful navigation patterns for similar tasks"""
        patterns = []
        for exp in self.experiences:
            if exp.get('task') == task_description and exp.get('success', False):
                patterns.append(exp)
        return patterns

# Define tools for the smolagents framework
@tool
def get_DOM_Tree() -> str:
    """
    Retrieves the full DOM tree of the current page as a structured JSON string.
    """
    import concurrent.futures
    from bs4 import BeautifulSoup
    from helium import get_driver

    # Helper function for recursive parsing (logic moved from server)
    def element_to_dict(element):
        if element.name is None:  # It's a NavigableString (text)
            return {"type": "text", "content": element.strip()} if element.strip() else None
        
        result = {
            "tag": element.name,
            "attrs": element.attrs,
            "children": []
        }
        
        for child in element.children:
            child_dict = element_to_dict(child)
            if child_dict:
                result["children"].append(child_dict)
        return result

    def parse_html_in_thread(html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # For the agent, we might want to limit the tree size or return the whole thing
            # using the recursive function
            return json.dumps(element_to_dict(soup))
        except Exception as e:
            return f"Error parsing HTML: {str(e)}"

    # Main tool logic
    driver = get_driver()
    html_content = driver.page_source

    # Use a thread to perform the parsing
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(parse_html_in_thread, html_content)
        try:
            return future.result(timeout=30) # 30 second timeout
        except Exception as e:
            return f"Error during threaded parsing: {str(e)}"

# Remove the get_page_html tool as requested

@tool
def set_browser_url(url: str) -> str:
    """
    Sets the browser to navigate to a specific URL.
    Args:
        url: The URL to navigate to
    Returns:
        A confirmation message with the current URL after navigation
    """
    from helium import go_to, get_driver
    global navigation_stack, tab_manager

    # Add current URL to navigation stack before navigating
    driver = get_driver()
    current_url = driver.current_url
    if not navigation_stack or navigation_stack[-1] != current_url:
        navigation_stack.append(current_url)

    go_to(url)
    driver = get_driver()

    # Update tab manager with new URL
    if tab_manager.current_tab:
        tab_manager.tabs[tab_manager.current_tab]['url'] = driver.current_url
        tab_manager.tabs[tab_manager.current_tab]['history'].append(driver.current_url)

    return f"Successfully navigated to: {driver.current_url}"

@tool
def create_new_tab(url: str = None) -> str:
    """
    Creates a new browser tab and optionally navigates to a URL.
    Args:
        url: Optional URL to navigate to in the new tab
    Returns:
        A confirmation message with the new tab ID
    """
    global tab_manager
    tab_id = tab_manager.create_new_tab(url)
    return f"Created new tab with ID: {tab_id}"

@tool
def switch_to_tab(tab_id: str) -> str:
    """
    Switches to the specified browser tab.
    Args:
        tab_id: The ID of the tab to switch to
    Returns:
        A confirmation message
    """
    global tab_manager
    success = tab_manager.switch_tab(tab_id)
    if success:
        return f"Switched to tab: {tab_id}"
    else:
        return f"Failed to switch to tab: {tab_id}"

@tool
def close_tab(tab_id: str) -> str:
    """
    Closes the specified browser tab.
    Args:
        tab_id: The ID of the tab to close
    Returns:
        A confirmation message
    """
    global tab_manager
    success = tab_manager.close_tab(tab_id)
    if success:
        return f"Closed tab: {tab_id}"
    else:
        return f"Failed to close tab: {tab_id}"

@tool
def find_path_to_target(target: str, keyword_values: str = None) -> str:
    """
    The 'Grappling Hook' / Scout tool. Uses a Depth-1 Lookahead Search to find the best link.
    
    NO LLM usage. Pure algorithmic scouting:
    1. Scans current page for top candidates.
    2. Opens a BACKGROUND TAB to visit/hook each candidate.
    3. Analyzes the CONTENT of the destination page.
    4. Returns the single best URL that matches your target.
    
    Use this to "Grapple" to a destination with high confidence especially for navigation steps like finding 'Login'.
    
    Args:
        target: The target concept or keyword to find (e.g., "latest release", "about page", "login")
        keyword_values: Optional JSON scoring weights
    Returns:
        JSON string with the "best_url" to navigate to, and the "reasoning".
    """
    import json
    import time
    from helium import get_driver
    
    driver = get_driver()
    original_window = driver.current_window_handle
    current_url = driver.current_url
    
    # 1. SCOUT CURRENT PAGE
    try:
        links_data = driver.execute_script("""
            var links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(function(link) {
                return {
                    href: link.href,
                    text: link.innerText.trim(),
                    title: link.title || ''
                };
            });
        """)
    except:
        return json.dumps({"error": "Failed to extract links from current page"})

    if keyword_values:
        try:
            weights = json.loads(keyword_values)
        except:
            weights = {}
    else:
        weights = {}

    def get_score(text, target, weights):
        text = text.lower()
        target = target.lower()
        score = 0
        if target in text: score += 50
        for w, val in weights.items():
            if w.lower() in text: score += val
        return score

    # Rank candidates by Link Text first
    scored_candidates = []
    seen_hrefs = set()
    
    for l in links_data:
        href = l['href']
        if href in seen_hrefs or href == current_url or 'javascript:' in href: continue
        seen_hrefs.add(href)
        
        score = get_score(l['text'] + " " + l['title'], target, weights)
        scored_candidates.append({**l, 'initial_score': score})
    
    # Take top 3 candidates to Scout
    scored_candidates.sort(key=lambda x: x['initial_score'], reverse=True)
    top_candidates = scored_candidates[:3]
    
    best_candidate = None
    best_final_score = -1
    
    scout_logs = []

    # 2. LAUNCH GRAPPLING HOOK (New Tab)
    # Open new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        if not top_candidates:
             scout_logs.append("No links found on current page.")
        
        for candidate in top_candidates:
            url = candidate['href']
            try:
                # Go to page
                driver.get(url)
                # Quick content scrape
                page_text = driver.find_element_by_tag_name('body').text[:10000] # First 10k chars
                
                # Score content
                relevance_score = get_score(page_text, target, weights)
                # Bonus if title matches
                if target.lower() in driver.title.lower():
                    relevance_score += 30
                
                final_score = candidate['initial_score'] + relevance_score
                
                log = f"Scouted {url} | TextScore: {candidate['initial_score']} | ContentScore: {relevance_score} | Total: {final_score}"
                scout_logs.append(log)
                
                if final_score > best_final_score:
                    best_final_score = final_score
                    best_candidate = candidate
                    best_candidate['final_score'] = final_score
                    best_candidate['found_on_page'] = True
                    
            except Exception as e:
                scout_logs.append(f"Failed to scout {url}: {str(e)}")
                
    finally:
        # 3. CLEANUP
        # Check if tab is still open before closing
        try:
            if len(driver.window_handles) > 1:
                driver.close() # Close scout tab
            driver.switch_to.window(original_window)
        except:
             pass

    # 4. RESULT
    if best_candidate and best_final_score > 0:
        return json.dumps({
            "best_url": best_candidate['href'],
            "confidence_score": best_candidate['final_score'],
            "reason": f"Grappling Hook verified content relevance. {best_candidate['text']}",
            "logs": scout_logs
        }, indent=2)
    else:
        return json.dumps({
            "error": "No good path found.",
            "logs": scout_logs,
            "top_links_checked": [c['href'] for c in top_candidates]
        }, indent=2)

@tool
def get_address() -> str:
    """
    Gets the current address information from the browser or system.
    Returns:
        A string containing the current address information
    """
    import socket
    from helium import get_driver

    try:
        # Get the current URL from the browser
        driver = get_driver()
        current_url = driver.current_url

        # Get the hostname of the current system
        hostname = socket.gethostname()

        # Get the local IP address
        local_ip = socket.gethostbyname(hostname)

        # Execute JavaScript to get geolocation from the browser
        # Note: Geolocation is asynchronous, so we'll return a placeholder for now
        # and let the agent know that geolocation requires special handling
        location_data = {
            "note": "Browser geolocation requires special handling due to asynchronous nature",
            "javascript_geolocation": "navigator.geolocation.getCurrentPosition() can be used but requires callbacks/promises"
        }

        # Construct address information
        address_info = {
            "current_page_url": current_url,
            "system_hostname": hostname,
            "local_ip_address": local_ip,
            "browser_title": driver.title if driver.title else "No Title",
            "geolocation_data": location_data
        }

        import json
        return json.dumps(address_info, indent=2)
    except Exception as e:
        return f"Error getting address information: {str(e)}"


@tool
def get_geolocation() -> str:
    """
    Gets the physical location from the browser's geolocation service.
    Returns:
        A string containing the geolocation information
    """
    from helium import get_driver
    import json
    import socket

    try:
        driver = get_driver()

        # Execute JavaScript to get geolocation from the browser
        # We'll use a timeout mechanism to handle the asynchronous nature
        result = driver.execute_script("""
            // Create a temporary element to store the result
            var resultElement = document.createElement('div');
            resultElement.id = 'geolocation-result';
            resultElement.style.display = 'none';
            document.body.appendChild(resultElement);

            function handleLocation(position) {
                var coords = position.coords;
                var locationData = {
                    latitude: coords.latitude,
                    longitude: coords.longitude,
                    accuracy: coords.accuracy,
                    altitude: coords.altitude,
                    altitudeAccuracy: coords.altitudeAccuracy,
                    heading: coords.heading,
                    speed: coords.speed,
                    timestamp: position.timestamp,
                    success: true
                };
                resultElement.textContent = JSON.stringify(locationData);
            }

            function handleError(error) {
                var errorData = {
                    error: error.message,
                    code: error.code,
                    success: false
                };
                resultElement.textContent = JSON.stringify(errorData);
            }

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(handleLocation, handleError, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000
                });
            } else {
                var errorData = {
                    error: "Geolocation is not supported by this browser",
                    success: false
                };
                resultElement.textContent = JSON.stringify(errorData);
            }

            // Wait for 5 seconds and return whatever result we have
            setTimeout(function() {
                if (resultElement.textContent === '') {
                    var timeoutData = {
                        error: "Timeout waiting for geolocation",
                        success: false
                    };
                    resultElement.textContent = JSON.stringify(timeoutData);
                }
            }, 5000);
        """)

        # Wait a moment for the geolocation to complete
        import time
        time.sleep(6)  # Wait for the geolocation request to complete

        # Get the result from the temporary element
        location_result = driver.execute_script("""
            var element = document.getElementById('geolocation-result');
            if (element) {
                var result = element.textContent;
                element.remove(); // Clean up
                return result;
            }
            return JSON.stringify({error: "Geolocation result element not found", success: false});
        """)

        # Parse the result
        try:
            location_data = json.loads(location_result) if location_result else {"error": "No location data returned", "success": False}
        except:
            location_data = {"error": "Could not parse location data", "success": False, "raw_result": location_result}

        # Get system information as well
        system_info = {
            "system_hostname": socket.gethostname(),
            "local_ip_address": socket.gethostbyname(socket.gethostname()),
        }

        result = {
            "geolocation": location_data,
            "system_info": system_info
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting geolocation: {str(e)}"


@tool
def quit_browser() -> str:
    """
    Safely quits the browser and provides output confirmation.
    Returns:
        A confirmation message indicating the browser was closed
    """
    import helium
    try:
        helium.kill_browser()
        return "[Browser Quit]: Browser has been successfully closed. To finish the task, you MUST now output a code block with your final answer."
    except Exception as e:

        return f"[Browser Quit]: Error closing browser - {str(e)}"

@tool
def think(query: str) -> str:
    """
    The 'Cognitive Engine' (Claude 3 Opus). Call this tool to THINK STRATEGICALLY before acting.
    
    This uses a specialized "Thought Engine" pattern:
    1. It pauses to reason internally (generating a step-by-step plan).
    2. It evaluates its own plan for confidence.
    3. It returns a guiding strategy.
    
    Use this when:
    - You are starting a complex task.
    - You need to interpret vague user intent.
    - You want to verify if your next move is optimal.

    Args:
        query: The context or dilemma you need to think about.
    Returns:
        The strategic thought process and plan.
    """
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Thinking Error: ANTHROPIC_API_KEY not found in environment."
            
        client = anthropic.Anthropic(api_key=api_key)

        # 1. Define the Cognition Tool
        thought_tool = {
            "name": "thought_engine",
            "description": "A tool for extended cognition. Use this to break down complex problems, plan steps, and verify logic before responding.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Detailed internal monologue and step-by-step planning."
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "0-1 scale of how sure the model is about the plan."
                    }
                },
                "required": ["reasoning"]
            }
        }
        messages = [{"role": "user", "content": query}]
        
        # 2. Force Opus to use the thought tool first
        # Accessing beta features requires using client.beta.messages.create
        response = client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system="You are the Strategic Brain of an autonomous web agent. Your goal is to analyze the situation, deduce the optimal strategy, and guide the agent. You must use the 'thought_engine' to reason step-by-step before giving your final plan. CRITICAL: If the task is complete based on current observations, your plan MUST tell the agent to call `final_answer(...)` immediately to terminate.",
            tools=[thought_tool],
            tool_choice={"type": "tool", "name": "thought_engine"},
            messages=messages,
            betas=["context-1m-2025-08-07"]
        )


        # Capture the "Extended Cognition"
        thought_output = "No reasoning provided."
        tool_use_id = None
        
        for block in response.content:
            if block.type == 'tool_use' and block.name == 'thought_engine':
                thought_output = block.input.get('reasoning', '')
                tool_use_id = block.id
                break

        # 3. Finalize Output
        # Append the thought to history and let Opus finish the task
        messages.append({"role": "assistant", "content": response.content})
        
        # CRITICAL FIX: If a tool was used, we MUST provide the tool result before the user speaks again
        if tool_use_id:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": "Thoughts recorded successfully."
                    }
                ]
            })
        
        # Now add the instruction to execute the plan
        messages.append({
            "role": "user", 
            "content": "Thought processed. Now execute your plan and provide the final response."
        })

        final_response = client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system="You are the Strategic Brain of an autonomous web agent. Synthesize your previous thoughts into a clear, actionable plan for the agent. If the task is done, explicitly command the agent to use `final_answer()`.",
            messages=messages,
            betas=["context-1m-2025-08-07"]
        )
        
        return f"--- THOUGHT ENGINE ---\n{thought_output}\n\n--- STRATEGIC PLAN ---\n{final_response.content[0].text}"

    except Exception as e:
        return f"Thinking unavailable: {str(e)}"

@tool
def search_item_ctrl_f(text: str, nth_result: int = 1) -> str:
    """
    Searches for text on the current page via Ctrl + F and jumps to the nth occurrence.
    Args:
        text: The text to search for
        nth_result: Which occurrence to jump to (default: 1)
    """
    from helium import get_driver
    driver = get_driver()
    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
    if nth_result > len(elements):
        raise Exception(
            f"Match n°{nth_result} not found (only {len(elements)} matches found)"
        )
    result = f"Found {len(elements)} matches for '{text}'."
    elem = elements[nth_result - 1]
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    result += f"Focused on element {nth_result} of {len(elements)}"
    return result

@tool
def go_back() -> None:
    """Goes back to previous page using navigation stack."""
    from helium import go_to, get_driver
    global navigation_stack

    if len(navigation_stack) > 1:
        # Remove current page and go back to previous
        navigation_stack.pop()
        if navigation_stack:
            previous_url = navigation_stack[-1]
            go_to(previous_url)
            return f"Returned to previous page: {previous_url}"
    else:
        # Use driver's native back function if no navigation stack
        driver = get_driver()
        driver.back()
        return "Navigated back using browser history"

@tool
def close_popups() -> str:
    """
    Closes any visible modal or pop-up on the page. Use this to dismiss pop-up windows! This does not work on cookie consent banners.
    """
    from helium import press
    press(Keys.ESCAPE)
    return "Pressed ESC key to close popups"

def save_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    sleep(1.0)  # Let JavaScript animations happen before taking the screenshot
    try:
        driver = helium.get_driver()
        current_step = memory_step.step_number
        if driver is not None:
            for previous_memory_step in (
                agent.memory.steps
            ):  # Remove previous screenshots from logs for lean processing
                if (
                    isinstance(previous_memory_step, ActionStep)
                    and previous_memory_step.step_number <= current_step - 2
                ):
                    previous_memory_step.observations_images = None
            png_bytes = driver.get_screenshot_as_png()
            image = Image.open(BytesIO(png_bytes))
            print(f"Captured a browser screenshot: {image.size} pixels")
            memory_step.observations_images = [
                image.copy()
            ]  # Create a copy to ensure it persists, important!

        # Update observations with current URL using Helium
        from helium import get_driver
        driver = get_driver()
        if driver is not None:
            url_info = f"Current url: {driver.current_url}"
        else:
            url_info = "Current url: Driver closed"
        memory_step.observations = (
            url_info
            if memory_step.observations is None
            else memory_step.observations + "\n" + url_info
        )
    except:
        # If driver is not available, just continue without screenshot
        url_info = "Current url: Unable to access driver"
        memory_step.observations = (
            url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info
        )
    return

def initialize_driver():
    """Initialize the Selenium WebDriver."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--window-size=1000,1350")
    chrome_options.add_argument("--disable-pdf-viewer")
    chrome_options.add_argument("--window-position=0,0")
    
    # Use the existing user profile
    # C:\Users\darcy\AppData\Local\Google\Chrome\User Data\Profile 16
    user_data_path = r"C:\Users\darcy\AppData\Local\Google\Chrome\User Data"
    profile_dir = "Profile 16"
    
    # KILL CHROME BEFORE STARTING to release the profile lock
    # This is aggressive but necessary for repurposing a real user profile
    import platform
    import subprocess
    if platform.system() == "Windows":
        try:
            # Kill chrome.exe to free up the User Data Dir
            print(f"Forcefully closing Chrome to unlock profile '{profile_dir}'...")
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3.0) # Wait longer for file locks to release
        except Exception as e:
            print(f"Warning: Failed to kill existing Chrome processes: {e}")

    chrome_options.add_argument(f"user-data-dir={user_data_path}")
    chrome_options.add_argument(f"profile-directory={profile_dir}")
    
    # Critical fixes for stability
    # Removed remote-debugging-port as it caused hangs. Letting Selenium find its own port.
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    return helium.start_chrome(headless=False, options=chrome_options)

def initialize_agent(model, experience_memory: ExperienceMemory):
    """Initialize the CodeAgent with the specified model and custom tools."""
    return CodeAgent(
        tools=[WebSearchTool(), go_back, close_popups, search_item_ctrl_f, get_DOM_Tree, set_browser_url, create_new_tab, switch_to_tab, close_tab, find_path_to_target, get_address, get_geolocation, think],
        model=model,
        additional_authorized_imports=["helium"],
        step_callbacks=[save_screenshot],
        max_steps=20,
        verbosity_level=2,
    )

def run_agent_with_args(args):
    """Function to run the agent with provided arguments, called by navigate.py"""
    # Load environment variables
    load_dotenv()

    # Use the provided prompt directly
    prompt = args.prompt or "Perform a web search and navigate to find relevant information"

    # Initialize experience memory
    experience_memory = ExperienceMemory()

    # Initialize the model based on the provided arguments
    model = load_model(args.model_type, args.model_id)

    global driver
    
    driver = initialize_driver()

    # Navigate to the specified URL instead of starting on a blank page
    from helium import go_to
    go_to(args.url)  # Start at the specified URL

    # Add initial URL to navigation stack
    global navigation_stack
    navigation_stack = [args.url]

    agent = initialize_agent(model, experience_memory)

    # Prepare the prompt with context about past experiences
    similar_experiences = experience_memory.find_similar_experiences(prompt)
    if similar_experiences:
        experience_context = "Past successful experiences for similar tasks:\n"
        for exp in similar_experiences:
            if exp.get('success', False):
                experience_context += f"- Task: {exp.get('task')}\n"
                experience_context += f"- Result: {exp.get('result', 'Success')}\n"
    else:
        experience_context = ""

    # Enhance the prompt with experience context
    enhanced_prompt = f"{experience_context}\n\n{prompt}"

    # Run the agent with the enhanced prompt
    agent.python_executor("from helium import *")
    result = agent.run(enhanced_prompt)

    # After execution, save the experience
    # Safely get final URL
    final_url = "unknown"
    try:
        if driver:
            final_url = driver.current_url
    except:
        pass

    experience = {
        'task': prompt,
        'start_url': args.url,
        'context': enhanced_prompt,
        'actions': [],  # Would be filled with actual actions taken
        'success': True,  # Simplified - in a real implementation, this would be determined by the outcome
        'final_url': final_url,
        'result': str(result) if result else "No result"
    }
    experience_memory.add_experience(experience)

    # Return the result for navigate.py to process
    return result

def cleanup_resources():
    """Clean up browser resources when the agent finishes"""
    global driver
    try:
        if driver:
            import helium
            helium.kill_browser()
    except:
        pass  # Ignore errors during cleanup
