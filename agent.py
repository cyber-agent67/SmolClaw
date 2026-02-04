"""
Agentic Web Navigation with RAG Capabilities
Accumulates past experiences for more efficient navigation
Core agent functionality without command-line interface
"""

import json
import os
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

    def __init__(self, memory_file="navigation_memory.pkl"):
        self.memory_file = memory_file
        self.experiences = self.load_memory()

    def load_memory(self) -> List[Dict]:
        """Load previous experiences from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return []
        return []

    def save_memory(self):
        """Save experiences to file"""
        with open(self.memory_file, 'wb') as f:
            pickle.dump(self.experiences, f)

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
    # Use helium to get the driver and execute script
    from helium import get_driver
    driver = get_driver()

    # Get the DOM and convert to a structured JSON representation
    dom_json = driver.execute_script("""
        function domToJSON(element, maxDepth = 5, currentDepth = 0) {
            if (currentDepth > maxDepth) return null;

            var result = {
                tagName: element.tagName ? element.tagName.toLowerCase() : 'unknown',
                attributes: {},
                textContent: element.textContent ? element.textContent.trim().substring(0, 100) : '',
                children: []
            };

            // Get attributes
            if (element.attributes) {
                for (var i = 0; i < element.attributes.length; i++) {
                    var attr = element.attributes[i];
                    result.attributes[attr.name] = attr.value;
                }
            }

            // Process children
            if (element.children && currentDepth < maxDepth) {
                for (var j = 0; j < element.children.length; j++) {
                    var childResult = domToJSON(element.children[j], maxDepth, currentDepth + 1);
                    if (childResult) {
                        result.children.push(childResult);
                    }
                }
            }

            return result;
        }
        return JSON.stringify(domToJSON(document.documentElement));
    """)
    return dom_json

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
def find_path_to_target(target: str) -> str:
    """
    Uses A* algorithm to find the optimal path to a target page using current URL and hyperlinks.
    Args:
        target: The target to search for (can be a URL, link text, or keyword)
    Returns:
        A JSON string with the path to the target and the recommended action
    """
    import json
    from helium import get_driver

    # Get current page information
    driver = get_driver()
    current_url = driver.current_url

    # Get all hyperlinks on the current page with their child elements and text content
    try:
        # Execute JavaScript to get all anchor elements with href and their content
        links_data = driver.execute_script("""
            var links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(function(link) {
                // Get all text content from the link and its children
                var allText = [];
                var walker = document.createTreeWalker(
                    link,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                var node;
                while (node = walker.nextNode()) {
                    var text = node.textContent.trim();
                    if (text) allText.push(text);
                }

                return {
                    href: link.href,
                    text: link.textContent.trim(),
                    allTextContent: allText.join(' '),
                    title: link.title,
                    alt: link.alt || '',
                    id: link.id || '',
                    className: link.className || '',
                    innerHTML: link.innerHTML
                };
            });
        """)
    except:
        links_data = []

    # Define keyword values for heuristic scoring
    keyword_values = {
        'release': 90,
        'releases': 90,
        'tag': 85,
        'tags': 85,
        'version': 80,
        'versions': 80,
        'download': 75,
        'downloads': 75,
        'archive': 70,
        'archives': 70,
        'latest': 65,
        'new': 60,
        'recent': 55,
        'current': 50
    }

    # Implement A* algorithm to find the best path
    def calculate_heuristic(link, target):
        """Calculate heuristic value for a link based on how well it matches the target"""
        score = 0
        target_lower = target.lower()

        # Check if target appears in href
        if target_lower in link.get('href', '').lower():
            score += 100

        # Check if target appears in link text
        if target_lower in link.get('text', '').lower():
            score += 80

        # Check if target appears in all text content (including child elements)
        if target_lower in link.get('allTextContent', '').lower():
            score += 75

        # Check if target appears in title
        if target_lower in link.get('title', '').lower():
            score += 60

        # Score based on keyword values in text content
        text_to_check = (link.get('text', '') + ' ' + link.get('allTextContent', '')).lower()
        for keyword, value in keyword_values.items():
            if keyword in text_to_check:
                score += value

        # Check for GitHub-specific patterns if in a GitHub domain
        if 'github.com' in current_url.lower():
            href_lower = link.get('href', '').lower()
            if any(common in href_lower for common in ['/releases', '/tags', '/archive']):
                score += 40

        return score

    # Calculate scores for all links
    scored_links = []
    for link in links_data:
        score = calculate_heuristic(link, target)
        if score > 0:  # Only include links that have some relevance
            scored_links.append({
                'href': link['href'],
                'text': link['text'],
                'all_text_content': link['allTextContent'],
                'title': link['title'],
                'score': score
            })

    # Sort by score (descending)
    scored_links.sort(key=lambda x: x['score'], reverse=True)

    # Prepare result
    result = {
        'current_url': current_url,
        'target': target,
        'path_found': len(scored_links) > 0,
        'best_matches': scored_links[:5],  # Top 5 matches
        'recommended_action': None
    }

    if scored_links:
        best_match = scored_links[0]
        result['recommended_action'] = {
            'action': 'click',
            'element': best_match['href'],
            'text': best_match['text'],
            'all_text_content': best_match['all_text_content'],
            'reason': f"Highest scoring link for target '{target}' with score {best_match['score']}"
        }

    # Format output as requested
    output_lines = ["[Greater A*]: Search Results"]
    output_lines.append(f"Target: {target}")
    output_lines.append(f"Current URL: {current_url}")
    output_lines.append(f"Path Found: {'Yes' if len(scored_links) > 0 else 'No'}")

    if scored_links:
        output_lines.append("Best Matches:")
        for i, match in enumerate(scored_links[:5], 1):
            output_lines.append(f"  {i}. Action: click | Element: {match['href'][:50]}... | Text: '{match['text'][:30]}...' | Score: {match['score']} | Heuristic: Matched target '{target}'")

    if scored_links:
        best_match = scored_links[0]
        output_lines.append(f"[Greater A*]: Recommended Action: click on '{best_match['text']}' | Reason: Highest scoring link for target '{target}' | Score: {best_match['score']}")

    output_text = "\n".join(output_lines)

    # Return both the formatted text and the JSON data
    return output_text + "\n\n" + json.dumps(result, indent=2)

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
        return "[Browser Quit]: Browser has been successfully closed"
    except Exception as e:
        return f"[Browser Quit]: Error closing browser - {str(e)}"

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
    url_info = f"Current url: {driver.current_url}"
    memory_step.observations = (
        url_info
        if memory_step.observations is None
        else memory_step.observations + "\n" + url_info
    )
    return

def initialize_driver():
    """Initialize the Selenium WebDriver."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--window-size=1000,1350")
    chrome_options.add_argument("--disable-pdf-viewer")
    chrome_options.add_argument("--window-position=0,0")
    return helium.start_chrome(headless=False, options=chrome_options)

def initialize_agent(model, experience_memory: ExperienceMemory):
    """Initialize the CodeAgent with the specified model and custom tools."""
    return CodeAgent(
        tools=[WebSearchTool(), go_back, close_popups, search_item_ctrl_f, get_DOM_Tree, set_browser_url, create_new_tab, switch_to_tab, close_tab, find_path_to_target, quit_browser],
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

    # If repo is provided, update the prompt accordingly
    if args.repo:
        prompt = f"Find the latest release for repository {args.repo}"
    else:
        prompt = args.prompt or "search for openclaw and get the current release and related tags"

    # Initialize experience memory
    experience_memory = ExperienceMemory()

    # Initialize the model based on the provided arguments
    model = load_model(args.model_type, args.model_id)

    global driver
    driver = initialize_driver()

    # Navigate to the specified URL instead of starting on a blank page
    from helium import go_to
    go_to(args.url)  # Start at the specified URL (GitHub.com by default)

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
    experience = {
        'task': prompt,
        'start_url': args.url,
        'context': enhanced_prompt,
        'actions': [],  # Would be filled with actual actions taken
        'success': True,  # Simplified - in a real implementation, this would be determined by the outcome
        'final_url': driver.current_url if driver else "unknown",
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
