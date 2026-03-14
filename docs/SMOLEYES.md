# SmolEyes: Vision-Based Browser Analysis

## Overview

**SmolEyes** is a vision tool for SmolClaw that provides Florence-2 vision model integration for browser analysis. It connects directly to the smol agent as a vision interface, similar to how smolhand provides tool-calling capabilities.

## Quick Start

```python
# Use the SmolEyes class
from smolclaw.smoleyes import SmolEyes

eyes = SmolEyes()

# Describe page
result = eyes.describe_page("What buttons are visible?")
print(result["caption"])

# Find element
button = eyes.find("blue submit button")
if button["found"]:
    print(f"Found at: {button['elements'][0]['bbox']}")

# Extract text
text = eyes.read_text()
print(text["ocr"]["text"])
```

## Tools Available to AI Agent

When the AI Agent runs, it can use these SmolEyes tools:

### 1. `analyze_visual_context(prompt_hint)`

Analyze current page visual context with detailed caption.

```python
# Agent usage
analyze_visual_context("What can I do on this page?")
analyze_visual_context("Describe the layout")
```

**Returns:**
```json
{
  "caption": "A webpage with a navigation bar at the top...",
  "url": "https://example.com",
  "title": "Example Page"
}
```

### 2. `describe_page_visual(prompt_hint)`

Describe current page using detailed visual analysis.

```python
# Agent usage
describe_page_visual("Describe the main content area")
describe_page_visual("What form fields are visible?")
```

### 3. `find_visual_element(description, confidence_threshold)`

Find visual element by natural language description.

```python
# Agent usage
find_visual_element("red delete button")
find_visual_element("search icon", confidence_threshold=0.7)
```

**Returns:**
```json
{
  "found": true,
  "count": 1,
  "elements": [
    {
      "label": "button",
      "bbox": [100, 200, 150, 250],
      "confidence": 0.89
    }
  ]
}
```

### 4. `extract_text_from_screenshot()`

Extract all text visible on page using OCR.

```python
# Agent usage
extract_text_from_screenshot()
```

**Returns:**
```json
{
  "text": "Welcome to Example.com\nSign In\nRegister\n...",
  "task": "ocr"
}
```

### 5. `detect_page_objects()`

Detect all objects on current page.

```python
# Agent usage
detect_page_objects()
```

**Returns:**
```json
{
  "count": 15,
  "objects": [
    {"label": "button", "bbox": [...], "confidence": 0.92},
    {"label": "text", "bbox": [...], "confidence": 0.88},
    ...
  ]
}
```

## Runtime API

### Capture Screenshot

```python
from smolclaw.smoleyes import capture_screenshot_base64

screenshot_b64 = capture_screenshot_base64()
# Returns: Base64-encoded PNG
```

### Analyze with Florence-2

```python
from smolclaw.smoleyes import analyze_with_florence

# Caption
result = analyze_with_florence(screenshot_b64, task="Caption")

# Detailed caption
result = analyze_with_florence(screenshot_b64, task="DetailedCaption")

# Object detection
result = analyze_with_florence(screenshot_b64, task="ObjectDetection")

# OCR
result = analyze_with_florence(screenshot_b64, task="OCR")
```

### Describe Page

```python
from smolclaw.smoleyes import describe_page_visual

# Basic description
result = describe_page_visual()

# With hint
result = describe_page_visual(prompt_hint="Focus on the navigation menu")

# With OCR
result = describe_page_visual(include_ocr=True)

# With object detection
result = describe_page_visual(include_objects=True)
```

### Find Visual Element

```python
from smolclaw.smoleyes import find_visual_element

# Find button
result = find_visual_element("blue submit button")

# With confidence threshold
result = find_visual_element("search icon", confidence_threshold=0.8)
```

### Extract Text from Region

```python
from smolclaw.smoleyes import extract_text_from_region

result = extract_text_from_region(x=100, y=200, width=300, height=150)
```

## SmolEyes Class

High-level interface for vision analysis:

```python
from smolclaw.smoleyes import SmolEyes

eyes = SmolEyes()

# Describe page
result = eyes.describe_page("What can I do here?")
# → dict with caption

# Find element
button = eyes.find("submit button")
# → dict with found, count, elements

# Read text
text = eyes.read_text()
# → dict with OCR results

# Detect objects
objects = eyes.detect_objects()
# → dict with detected objects

# Capture screenshot
screenshot = eyes.capture()
# → base64 string
```

## Use Cases

### 1. Accessibility Analysis

```python
eyes = SmolEyes()

# Check if page has proper visual structure
result = eyes.describe_page("Describe the page structure")
print(result["caption"])

# Find all buttons
buttons = eyes.find("button")
print(f"Found {buttons['count']} buttons")
```

### 2. Form Detection

```python
# Find form fields
fields = eyes.find("text input field")
if fields["found"]:
    print("Form detected")

# Extract labels
text = eyes.read_text()
print("Form labels:", text["ocr"]["text"])
```

### 3. Visual Regression

```python
# Capture before
before = eyes.capture()

# ... perform action ...

# Capture after
after = eyes.capture()

# Compare (future feature)
# diff = eyes.compare(before, after)
```

### 4. Icon/Button Detection

```python
# Find specific button
result = eyes.find("red delete button", confidence_threshold=0.7)

if result["found"]:
    bbox = result["elements"][0]["bbox"]
    print(f"Button at: {bbox}")
```

### 5. OCR for Images

```python
# Extract text from infographic
text = eyes.read_text()
print("Text in image:", text["ocr"]["text"])
```

## Integration with AI Agent

The AI Agent automatically has access to SmolEyes tools:

```python
# Agent can call these tools directly
from smolclaw import run_agent_with_args

args = parse_args()
result = run_agent_with_args(args)

# Agent might use:
# - analyze_visual_context("What's on this page?")
# - find_visual_element("login button")
# - extract_text_from_screenshot()
```

## Architecture

```
smolclaw.smoleyes
├── runtime.py          # Core vision functions
│   ├── capture_screenshot_base64()
│   ├── analyze_with_florence()
│   ├── describe_page_visual()
│   └── find_visual_element()
│
├── tools.py            # @tool decorated functions
│   ├── analyze_visual_context
│   ├── describe_page_visual
│   ├── find_visual_element
│   ├── extract_text_from_screenshot
│   └── detect_page_objects
│
└── __init__.py         # SmolEyes class + exports
```

## Comparison: SmolEyes vs SmolHand

| Feature | SmolEyes | SmolHand |
|---------|----------|----------|
| **Purpose** | Vision analysis | Small LLM tool-calling |
| **Model** | Florence-2 | Various (Qwen, Mistral, etc.) |
| **Input** | Screenshots | Text prompts |
| **Output** | Visual descriptions, OCR | Tool calls, text responses |
| **Use Case** | "What do I see?" | "What should I do?" |

## Examples

### Example 1: Page Understanding

```python
from smolclaw.smoleyes import SmolEyes

eyes = SmolEyes()

# Understand page
desc = eyes.describe_page("What is this page about?")
print(desc["caption"])

# Find actions
buttons = eyes.find("button")
print(f"Available actions: {buttons['count']} buttons")
```

### Example 2: Form Filling

```python
# Find form fields
fields = eyes.find("input field")
text_fields = eyes.find("text input")

# Extract labels
text = eyes.read_text()
print("Form fields:", text["ocr"]["text"])
```

### Example 3: Visual Search

```python
# Find specific element
result = eyes.find("shopping cart icon")

if result["found"]:
    print(f"Cart found at: {result['elements'][0]['bbox']}")
else:
    print("Cart icon not visible")
```

## Requirements

- Florence-2 model (loaded automatically)
- Browser with screenshot capability
- Helium/Selenium driver

## Future Features

- [ ] Multi-image comparison
- [ ] Visual element clicking (with coordinates)
- [ ] Region-specific OCR
- [ ] Custom vision model support
- [ ] Visual diffing for regression testing

## Summary

**SmolEyes** gives the AI Agent "eyes" to see and understand web pages visually:

- 📸 **Screenshot capture**
- 👁️ **Florence-2 vision analysis**
- 🔍 **Object detection**
- 📝 **OCR text extraction**
- 🎯 **Visual element grounding**

Just like smolhand provides "hands" for tool-calling, smoleyes provides "eyes" for vision-based analysis! 👁️🤖
