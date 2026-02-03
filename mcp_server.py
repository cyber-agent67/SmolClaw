#!/usr/bin/env python3
"""
MCP Server for Browser Navigation Limbs
Exposes browser control and A* navigation as tools for AI models
"""

import asyncio
import base64
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Global browser state
browser: Browser = None
context: BrowserContext = None
page: Page = None
playwright_instance = None


async def initialize_browser():
    """Initialize the browser if not already running"""
    global browser, context, page, playwright_instance
    
    if page is not None:
        return
    
    playwright_instance = await async_playwright().start()
    context = await playwright_instance.chromium.launch_persistent_context(
        user_data_dir="browser_data",
        headless=False,
        viewport={'width': 1920, 'height': 1080},
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    
    if len(context.pages) > 0:
        page = context.pages[0]
    else:
        page = await context.new_page()


async def cleanup_browser():
    """Cleanup browser resources"""
    global page, context, playwright_instance
    
    if page:
        await page.close()
    if context:
        await context.close()
    if playwright_instance:
        await playwright_instance.stop()


# Create MCP server
server = Server("github-navigator-limbs")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available browser control tools"""
    return [
        Tool(
            name="navigate_to_url",
            description="Navigate browser to a specific URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_current_url",
            description="Get the current page URL",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_page_html",
            description="Get the HTML content of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of HTML to return (default: 50000)",
                        "default": 50000
                    }
                }
            }
        ),
        Tool(
            name="get_all_links",
            description="Get all href links from the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_text": {
                        "type": "boolean",
                        "description": "Include link text (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_screenshot",
            description="Capture screenshot of current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full scrollable page (default: false - viewport only)",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="click_element",
            description="Click an element on the page using CSS selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of element to click"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="get_page_state",
            description="Get complete page state: URL, HTML, links, and screenshot in one call",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_screenshot": {
                        "type": "boolean",
                        "description": "Include base64 screenshot (default: true)",
                        "default": True
                    },
                    "html_max_length": {
                        "type": "integer",
                        "description": "Max HTML length (default: 20000)",
                        "default": 20000
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent]:
    """Handle tool calls"""
    await initialize_browser()
    
    try:
        if name == "navigate_to_url":
            url = arguments["url"]
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "current_url": page.url
                })
            )]
        
        elif name == "get_current_url":
            return [TextContent(
                type="text",
                text=json.dumps({
                    "url": page.url
                })
            )]
        
        elif name == "get_page_html":
            max_length = arguments.get("max_length", 50000)
            html = await page.content()
            if len(html) > max_length:
                html = html[:max_length]
            return [TextContent(
                type="text",
                text=json.dumps({
                    "html": html,
                    "truncated": len(await page.content()) > max_length
                })
            )]
        
        elif name == "get_all_links":
            include_text = arguments.get("include_text", True)
            
            if include_text:
                links = await page.evaluate("""() => {
                    const results = [];
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    anchors.forEach(a => {
                        results.push({
                            href: a.href.split('#')[0],
                            text: a.innerText.trim()
                        });
                    });
                    return results;
                }""")
            else:
                links = await page.evaluate("""() => {
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    return anchors.map(a => a.href.split('#')[0]);
                }""")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "links": links,
                    "count": len(links)
                })
            )]
        
        elif name == "get_screenshot":
            full_page = arguments.get("full_page", False)
            screenshot_path = Path("screenshots") / "mcp_screenshot.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            
            await page.screenshot(path=screenshot_path, full_page=full_page)
            
            with open(screenshot_path, "rb") as f:
                screenshot_data = base64.b64encode(f.read()).decode('utf-8')
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "screenshot_base64": screenshot_data,
                    "width": page.viewport_size["width"],
                    "height": page.viewport_size["height"]
                })
            )]
        
        elif name == "click_element":
            selector = arguments["selector"]
            element = page.locator(selector).first
            await element.click()
            await page.wait_for_load_state("networkidle")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "current_url": page.url
                })
            )]
        
        elif name == "get_page_state":
            include_screenshot = arguments.get("include_screenshot", True)
            html_max_length = arguments.get("html_max_length", 20000)
            
            # Get all state at once
            current_url = page.url
            html = await page.content()
            if len(html) > html_max_length:
                html = html[:html_max_length]
            
            links = await page.evaluate("""() => {
                const results = [];
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                anchors.forEach(a => {
                    results.push({
                        href: a.href.split('#')[0],
                        text: a.innerText.trim()
                    });
                });
                return results;
            }""")
            
            result = {
                "url": current_url,
                "html": html,
                "html_truncated": len(await page.content()) > html_max_length,
                "links": links,
                "link_count": len(links)
            }
            
            if include_screenshot:
                screenshot_path = Path("screenshots") / "mcp_state.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=False)
                
                with open(screenshot_path, "rb") as f:
                    result["screenshot_base64"] = base64.b64encode(f.read()).decode('utf-8')
            
            return [TextContent(
                type="text",
                text=json.dumps(result)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}"
                })
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            })
        )]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        await cleanup_browser()


if __name__ == "__main__":
    asyncio.run(main())
