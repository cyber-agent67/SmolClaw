"""
Vision model integration for navigation and extraction
"""

import json
import os
import base64
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import config
from pathlib import Path

class VisionAssistant:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        try:
            from anthropic import AsyncAnthropic
            self.anthropic_client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        except ImportError:
            self.anthropic_client = None
            print("Anthropic client not initialized (package might be missing)")

        self.strategy_model = config.STRATEGY_MODEL
        self.tagging_model = config.TAGGING_MODEL
        self.max_tokens = 1000
        
    async def get_navigation_instruction(self, screenshot_data: str, 
                                        current_url: str, 
                                        step_name: str,
                                        goal: str = None) -> Optional[Dict[str, Any]]:
        """Get navigation instruction from vision model"""
        
        system_prompt = """You are a web navigation assistant. Analyze the screenshot and provide the next action to reach the goal.

Available actions:
1. click - Click on an element (specify element_description and role)
2. type - Type text into an element (specify element_description, role, and text)
3. press - Press a key (specify key)
4. navigate - Go to a URL (specify url)
5. extract - Extract information from current page
6. done - Navigation is complete (goal reached)

Respond ONLY with valid JSON in this format:
{
    "action": "click|type|press|navigate|extract|done",
    "element_description": "description of element to interact with",
    "role": "button|link|textbox|heading|etc",
    "text": "text to type (for type action)",
    "key": "Enter|Escape|Tab|etc (for press action)",
    "url": "https://... (for navigate action)"
}"""
        
        # Default behavior if no specific goal provided (fallback to original task)
        task_context = """
        1. If at GitHub homepage: Find and use the search bar
        2. If at search results: Click on the correct repository
        3. If at repository page: Find and click the "Releases" link/tab
        4. If at releases page: Extract the latest release information
        """
        
        if goal:
            task_context = f"GOAL: {goal}\n\nDetermine the next logical step to achieve this goal."

        user_prompt = f"""
Current URL: {current_url}
Current Step: {step_name}

{task_context}

Based on the screenshot, what is the next action?
Provide only the JSON response.
"""
        
        try:
            if "claude" in self.strategy_model and self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.strategy_model,
                    max_tokens=self.max_tokens,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": user_prompt
                                }
                            ]
                        }
                    ]
                )
                content = response.content[0].text
            else:
                # Fallback or if strategy model is OpenAI
                response = await self.openai_client.chat.completions.create(
                    model=self.strategy_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{screenshot_data}"
                            }}
                        ]}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.1
                )
                content = response.choices[0].message.content
            
            # Clean response (remove markdown code blocks)
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Error getting navigation instruction: {e}")
            return None
    
    async def calculate_link_heuristics(self, candidates: list, repo: str, screenshot_data: str = None, dom_tree: str = None) -> list:
        """Eyes report to Brain, Brain calculates heuristics
        
        Flow: Eyes (GPT-4o) → Brain (Claude) → Returns scores for A*
        
        Args:
            candidates: List of dicts with keys: url, text, depth, discovery_count
            repo: Repository name (e.g., 'openclaw/openclaw')
            screenshot_data: Base64 encoded screenshot (for Eyes)
            dom_tree: HTML DOM snippet (for Brain's analysis)
            
        Returns:
            List of candidates with added 'heuristic_value' key
        """
        
        if not candidates:
            return []
        
        # STEP 1: Eyes (GPT-4o) describe what they see
        visual_description = ""
        if screenshot_data:
            try:
                print("   -> Eyes (GPT-4o) analyzing page visually...")
                eyes_prompt = f"""You are the Eyes for a web navigation system. Describe what you see on this GitHub page.

Focus on:
- Page type (repository home, releases page, tag page, etc.)
- Key visible elements (buttons, tabs, badges like 'Latest')
- Visual hierarchy and prominent links
- Any version numbers or release indicators

Be concise but specific. Your description will help the Brain make navigation decisions."""

                response = await self.openai_client.chat.completions.create(
                    model=self.tagging_model,
                    messages=[
                        {"role": "system", "content": "You are the Eyes of a web navigation system. Describe what you see clearly and concisely."},
                        {"role": "user", "content": [
                            {"type": "text", "text": eyes_prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{screenshot_data}"
                            }}
                        ]}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                visual_description = response.choices[0].message.content
                print(f"   -> Eyes report: {visual_description[:150]}...")
            except Exception as e:
                print(f"   -> Eyes failed to analyze: {e}")
                visual_description = "Visual analysis unavailable."
        
        # STEP 2: Prepare link candidates for Brain
        candidate_summary = []
        for i, cand in enumerate(candidates):
            candidate_summary.append({
                "index": i,
                "url": cand["url"],
                "text": cand["text"][:100],
            })
        
        # STEP 3: Brain (Claude) scores links using Eyes' report + DOM + candidates
        brain_system_prompt = f"""You are the Brain of a web navigation system seeking the LATEST release for repository '{repo}'.

You receive:
1. Visual description from the Eyes (what the page looks like)
2. DOM tree snippet (HTML structure)
3. List of candidate links

Score each link 0-1000 based on relevance to finding the LATEST release:
- Direct /releases or /releases/tag/latest links: 800-1000
- Links with "Latest", "Release", version numbers: 500-700
- Tags, Downloads: 300-500
- General repo navigation: 100-200
- Irrelevant: 0-50

Consider the Eyes' visual report heavily - if Eyes see a "Latest" badge next to a link, score it very high.

Return JSON: [{{"index": 0, "heuristic_value": 850, "reasoning": "why"}}, ...]"""

        brain_user_prompt = f"""**Eyes' Visual Report:**
{visual_description}

**DOM Tree (snippet):**
{dom_tree[:3000] if dom_tree else "Not provided"}

**Candidate Links ({len(candidates)} total):**
{json.dumps(candidate_summary, indent=2)}

Score each link for finding the LATEST release of '{repo}'."""

        try:
            print(f"   -> Brain (Claude) reasoning about {len(candidates)} links...")
            
            # Use Claude (Brain) for strategic reasoning
            if "claude" in self.strategy_model and self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.strategy_model,
                    max_tokens=3000,
                    temperature=0.1,
                    system=brain_system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": brain_user_prompt
                        }
                    ]
                )
                content = response.content[0].text
            else:
                # Fallback to OpenAI if Claude not available
                response = await self.openai_client.chat.completions.create(
                    model=self.strategy_model,
                    messages=[
                        {"role": "system", "content": brain_system_prompt},
                        {"role": "user", "content": brain_user_prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.1
                )
                content = response.choices[0].message.content
            
            # Parse Brain's response
            content = content.replace('```json', '').replace('```', '').strip()
            scores = json.loads(content)
            
            # Merge scores back into candidates
            score_map = {s["index"]: s["heuristic_value"] for s in scores}
            for i, cand in enumerate(candidates):
                cand["heuristic_value"] = score_map.get(i, 0)
            
            return candidates
            
        except Exception as e:
            print(f"   -> Brain reasoning failed: {e}")
            # Fallback: return candidates with default score
            for cand in candidates:
                cand["heuristic_value"] = 50
            return candidates
    
    async def is_goal_reached(self, screenshot_data: str, url: str, dom_tree: str, repo: str) -> dict:
        """Brain decides if the current page has reached the goal (latest release info)
        
        Returns:
            {
                "goal_reached": true/false,
                "confidence": 0-100,
                "reasoning": "explanation"
            }
        """
        
        # Eyes first
        visual_description = ""
        if screenshot_data:
            try:
                eyes_prompt = """Describe this GitHub page. Focus on:
- Is this a release/tag page?
- Do you see "Latest" badge or indicator?
- What version/tag information is visible?
- Is this clearly the latest release page?"""

                response = await self.openai_client.chat.completions.create(
                    model=self.tagging_model,
                    messages=[
                        {"role": "system", "content": "You are the Eyes. Describe what you see."},
                        {"role": "user", "content": [
                            {"type": "text", "text": eyes_prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{screenshot_data}"
                            }}
                        ]}
                    ],
                    max_tokens=300,
                    temperature=0.1
                )
                visual_description = response.choices[0].message.content
            except Exception as e:
                print(f"   -> Eyes failed: {e}")
                visual_description = "Visual unavailable"
        
        # Brain decides
        brain_prompt = f"""**Mission**: Find the LATEST release page for repository '{repo}'.

**Current URL**: {url}

**Eyes' Report**:
{visual_description}

**DOM Snippet**:
{dom_tree[:2000]}

**Decision Required**: Has the goal been reached?

Evaluate:
1. Is this a /releases/tag/ page?
2. Does it show "Latest" badge/indicator?
3. Is this clearly the most recent release?

Return JSON:
{{
    "goal_reached": true/false,
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}"""

        try:
            if "claude" in self.strategy_model and self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.strategy_model,
                    max_tokens=500,
                    temperature=0.1,
                    system="You are the Brain deciding if the navigation goal is reached.",
                    messages=[{"role": "user", "content": brain_prompt}]
                )
                content = response.content[0].text
            else:
                response = await self.openai_client.chat.completions.create(
                    model=self.strategy_model,
                    messages=[
                        {"role": "system", "content": "You are the Brain deciding if the navigation goal is reached."},
                        {"role": "user", "content": brain_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                content = response.choices[0].message.content
            
            content = content.replace('```json', '').replace('```', '').strip()
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"   -> Brain goal check failed: {e}")
            return {"goal_reached": False, "confidence": 0, "reasoning": "Error in evaluation"}
    
    
    
    async def extract_release_info(self, screenshot_data: str) -> Optional[Dict[str, Any]]:
        """Extract release information from screenshot"""
        
        prompt = """Extract the latest release information from this GitHub releases page.

Look for:
1. Version/tag name (e.g., v1.0.0, v2024.1.1)
2. Commit hash/tag (short SHA)
3. Author/uploader username
4. (Optional) Release notes, publish date, download links

Return ONLY valid JSON in this format:
{
    "version": "v1.0.0",
    "tag": "abc1234",
    "author": "username",
    "published_at": "2024-01-01T00:00:00Z",
    "downloads": [
        {"name": "file.zip", "url": "https://...", "size": "1.2 MB"}
    ]
}"""
        
        try:
            if "claude" in self.model:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
                
                response = await client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.1,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )
                content = response.content[0].text
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{screenshot_data}"
                            }}
                        ]}
                    ],
                    max_tokens=1500,
                    temperature=0.1
                )
                content = response.choices[0].message.content
            
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Error extracting release info: {e}")
            return {"version": "", "tag": "", "author": ""}
    async def extract_release_info_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract release information from HTML using the model"""
        
        system_prompt = "You are an expert at extracting structured data from HTML. Identify the latest release information."
        
        prompt = """Analyze the provided HTML from a GitHub releases page and extract the latest release information.
        
        Critically, find the AUTHOR or UPLOADER username who created the release.
        
        Look for:
        1. Version/tag name
        2. Commit hash/tag
        3. Author/uploader username
        
        Return ONLY valid JSON in this format:
        {
            "version": "v1.0.0",
            "tag": "abc1234",
            "author": "username",
            "published_at": "2024-01-01T00:00:00Z"
        }"""
        
        try:
            if "claude" in self.model:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
                
                response = await client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"{prompt}\n\nHTML Content:\n{html_content}"
                                }
                            ]
                        }
                    ]
                )
                content = response.content[0].text
            else:
                # Fallback for OpenAI (might hit token limits if HTML is huge, but usually fine for newer models)
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{prompt}\n\nHTML Content:\n{html_content}"}
                    ],
                    max_tokens=4000,
                    temperature=0.1
                )
                content = response.choices[0].message.content
            
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Error extracting release info from HTML: {e}")
            return {"version": "", "tag": "", "author": "Error extracting"}
            
    async def generate_navigation_plan(self, goal: str) -> list:
        """Generate a high-level navigation plan (list of steps) based on the goal"""
        
        system_prompt = "You are a Navigation Planner. Break down the user's goal into 4-6 clear, sequential, linear steps for a web agent."
        
        prompt = f"""Goal: {goal}
        
        Standard GitHub Release Flow (Reference):
        1. Navigate to GitHub homepage
        2. Search for the repository
        3. Click on the repository link
        4. Click on 'Releases'
        5. Click on the specific tag/title of the latest release (to view full details)
        6. Extract the release information
        
        Return valid JSON:
        {{
            "steps": [
                "Step 1 description",
                "Step 2 description",
                ...
            ]
        }}
        """
        
        try:
            if "claude" in self.strategy_model and self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.strategy_model,
                    max_tokens=1000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            else:
                response = await self.openai_client.chat.completions.create(
                    model=self.strategy_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.1
                )
                content = response.choices[0].message.content
                
            content = content.replace('```json', '').replace('```', '').strip()
            plan = json.loads(content)
            return plan.get("steps", [])
            
        except Exception as e:
            print(f"Error generating plan: {e}")
            # Fallback plan
            return [
                "Navigate to https://github.com",
                f"Search for repository mentioned in '{goal}'",
                "Click on the repository link",
                "Click on 'Releases'",
                "Click on the latest release tag",
                "Extract release information"
            ]

    async def suggest_dom_selectors(self, goal: str, html_snippet: str, screenshot_data: str = None, step_count: int = 0) -> Dict[str, Any]:
        """Ask Claude for DOM selector heuristics based on the goal, using Vision + HTML"""
        
        # Save debug artifacts as requested by user
        debug_dir = Path("debug_artifacts")
        debug_dir.mkdir(exist_ok=True)
        
        timestamp = step_count
        html_path = debug_dir / f"step_{timestamp}_context.html"
        img_path = debug_dir / f"step_{timestamp}_view.png"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_snippet)
            
        if screenshot_data:
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
                
        print(f"Saved debug artifacts to {html_path} and {img_path}")

        system_prompt = "You are an Expert Web Navigator. Your goal is to guide a DOM-based scraper to the correct element."
        
        prompt = f"""Target: {goal}
        
        I am on a webpage and need to interact with a specific element.
        
        1. Analyze the Screenshot to locate the visual element relevant to '{goal}'.
        2. Analyze the HTML snippet to find the corresponding DOM element.
        3. Provide specific CSS selectors to locate this element.
        
        CRITICAL: If I am looking for the 'Latest' release, look for the 'Latest' badge or tag and identifying the container or link associated with it.
        
        Return JSON format:
        {{
            "selectors": ["selector 1", "selector 2"],
            "rationale": "I see the element at [location] and it corresponds to this HTML..."
        }}
        """
        
        try:
            # Use GPT-4o (or configured tagging model) for selector generation
            # The prompt is specifically for GPT-4o vision
            response = await self.openai_client.chat.completions.create(
                model=self.tagging_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"{prompt}\n\nHTML Context:\n{html_snippet}"},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{screenshot_data}"
                        }}
                    ]}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            content = response.choices[0].message.content

            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error suggesting selectors with GPT-4o: {e}")
            
            # Fallback to Claude for reasoning-based selector suggestions
            if self.anthropic_client and "claude" in self.strategy_model:
                try:
                    print("Falling back to Claude for selector reasoning...")
                    
                    messages = []
                    if screenshot_data:
                        messages.append({
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_data}},
                                {"type": "text", "text": f"{prompt}\n\nHTML Context:\n{html_snippet}"}
                            ]
                        })
                    else:
                        messages.append({
                            "role": "user",
                            "content": f"{prompt}\n\nHTML Context:\n{html_snippet}"
                        })
                    
                    response = await self.anthropic_client.messages.create(
                        model=self.strategy_model,
                        max_tokens=1000,
                        temperature=0.1,
                        system=system_prompt,
                        messages=messages
                    )
                    content = response.content[0].text
                    content = content.replace('```json', '').replace('```', '').strip()
                    return json.loads(content)
                except Exception as claude_error:
                    print(f"Claude fallback also failed: {claude_error}")
            
            return {"selectors": []}

    async def extract_with_vision_and_html(self, screenshot_data: str, html_content: str, extract_fields: list = None) -> Dict[str, Any]:
        """Extract information using both visual context and HTML.
        Prioritizes GPT (Vision) as requested for final extraction.
        """
        
        if extract_fields is None:
            extract_fields = ["version", "tag", "author"]
        
        # Build dynamic field descriptions
        field_descriptions = {
            "version": "Version number (e.g., v1.0.0, v2026.2.1)",
            "tag": "Git commit hash or tag name (short form)",
            "author": "Author/uploader username (look for user links, hovercards, or 'releases by' text)",
            "release_notes": "Brief summary of release notes/changes",
            "published_at": "Publication date (ISO format if available)",
            "downloads": "List of download assets with name, url, size"
        }
        
        # Build required fields list
        fields_list ="\n".join([f"{i+1}. {field}: {field_descriptions.get(field, field)}" 
                                  for i, field in enumerate(extract_fields)])
        
        # Build example JSON
        example_json = {field: f"<{field}_value>" for field in extract_fields}
        
        system_prompt = "You are an intelligent extraction assistant. Use the visual screenshot and HTML to extract accurate data."
        
        prompt = f"""Extract the latest release information from this GitHub release page.
        
REQUIRED FIELDS:
{fields_list}
        
Return ONLY valid JSON in this format:
{json.dumps(example_json, indent=2)}

Be precise and extract exact values from the page."""
        
        try:
            # User explicit request: Use GPT Vision model over Claude for extraction
            # We use self.tagging_model which is configured as gpt-4o in config
            extraction_model = self.tagging_model 
            
            # Helper to run OpenAI extraction
            async def run_openai_extraction():
                response = await self.openai_client.chat.completions.create(
                    model=extraction_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                                {"type": "text", "text": f"{prompt}\n\nHTML Content:\n{html_content}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_data}"}}
                        ]}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content

            # Helper to run Claude extraction 
            async def run_claude_extraction():
                response = await self.anthropic_client.messages.create(
                    model=self.strategy_model,
                    max_tokens=4000,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": f"{prompt}\n\nHTML Content:\n{html_content}"
                                }
                            ]
                        }
                    ]
                )
                return response.content[0].text

            content = ""
            # Prioritize OpenAI (GPT-4o) if available
            if self.openai_client and "gpt" in extraction_model:
                try:
                    print(f"   -> Extracting with {extraction_model} (Visual + HTML)...")
                    content = await run_openai_extraction()
                except Exception as gpt_error:
                    print(f"GPT extraction failed, trying fallback: {gpt_error}")
                    if self.anthropic_client:
                        content = await run_claude_extraction()
            elif self.anthropic_client:
                 print(f"   -> Extracting with {self.strategy_model} (Visual + HTML)...")
                 content = await run_claude_extraction()
            else:
                 # Last resort attempt with whatever client exists
                 content = await run_openai_extraction()
                
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Error in combined extraction: {e}")
            return {}
            
    # Bonus: Natural language prompt processing
    async def process_natural_language_prompt(self, prompt: str, screenshot_data: str) -> Dict[str, Any]:
        """Process natural language prompts for flexible queries"""
        system_prompt = """You are a web navigation and information extraction assistant. 
        Process the user's natural language query and determine what actions are needed."""
        
        # Implementation for bonus challenge
        pass