# ✅ SmolEyes: Vision Tool Created!

## What Was Created

**SmolEyes** - A vision-based browser analysis tool that connects directly to the smol agent, just like smolhand!

## Package Structure

```
smolclaw/smoleyes/
├── __init__.py          # SmolEyes class + exports
├── runtime.py           # Core vision functions
│   ├── capture_screenshot_base64()
│   ├── analyze_with_florence()
│   ├── describe_page_visual()
│   ├── find_visual_element()
│   └── ...
│
└── tools.py             # @tool decorated functions
    ├── analyze_visual_context
    ├── describe_page_visual
    ├── find_visual_element
    ├── extract_text_from_screenshot
    └── detect_page_objects
```

## Tools Available to AI Agent

The AI Agent can now use these SmolEyes vision tools:

### 1. `analyze_visual_context(prompt_hint)`
Analyze page with Florence-2 vision model.

```python
analyze_visual_context("What can I do on this page?")
# → {"caption": "A webpage with navigation...", "url": "...", "title": "..."}
```

### 2. `describe_page_visual(prompt_hint)`
Detailed visual description.

```python
describe_page_visual("Describe the main content area")
# → {"caption": "The main content shows...", ...}
```

### 3. `find_visual_element(description, confidence)`
Find element by natural language description.

```python
find_visual_element("blue submit button")
# → {"found": true, "count": 1, "elements": [...]}
```

### 4. `extract_text_from_screenshot()`
OCR text extraction from page.

```python
extract_text_from_screenshot()
# → {"text": "Welcome to...\nSign In\n...", "task": "ocr"}
```

### 5. `detect_page_objects()`
Detect all objects on page.

```python
detect_page_objects()
# → {"count": 15, "objects": [{label, bbox, confidence}, ...]}
```

## Usage Examples

### Using SmolEyes Class

```python
from smolclaw.smoleyes import SmolEyes

eyes = SmolEyes()

# Describe page
result = eyes.describe_page("What buttons are visible?")
print(result["caption"])

# Find element
button = eyes.find("submit button")
if button["found"]:
    print(f"Found at: {button['elements'][0]['bbox']}")

# Read text (OCR)
text = eyes.read_text()
print(text["ocr"]["text"])

# Detect objects
objects = eyes.detect_objects()
print(f"Detected {objects['count']} objects")
```

### Using Runtime Functions

```python
from smolclaw.smoleyes import (
    capture_screenshot_base64,
    analyze_with_florence,
    describe_page_visual,
    find_visual_element,
)

# Capture screenshot
screenshot = capture_screenshot_base64()

# Analyze with Florence-2
result = analyze_with_florence(screenshot, task="DetailedCaption")

# Find element
element = find_visual_element("search icon", confidence_threshold=0.7)
```

### AI Agent Usage

The AI Agent automatically has access to SmolEyes tools:

```python
# Agent can call these directly
from smolclaw import run_agent_with_args

result = run_agent_with_args(args)

# Agent might use:
# - analyze_visual_context("What's on this page?")
# - find_visual_element("login button")
# - extract_text_from_screenshot()
# - detect_page_objects()
```

## Integration

### ToolRegistry Updated

All SmolEyes tools are registered in `smolclaw/agent/tools/ToolRegistry.py`:

```python
def _registry_tools():
    return [
        # ... other tools ...
        
        # SmolEyes vision tools
        analyze_visual_context,
        describe_page_visual,
        find_visual_element,
        extract_text_from_screenshot,
        detect_page_objects,
        
        # ... other tools ...
    ]
```

### Package Exports

Updated `smolclaw/__init__.py`:

```python
__all__ = [
    # ... other exports ...
    "smolhand",  # Browser automation + small LLM
    "smoleyes",  # Vision analysis
]

def __getattr__(name):
    # ...
    if name == "smoleyes":
        import smolclaw.smoleyes
        return smolclaw.smoleyes
```

## Comparison: SmolEyes vs SmolHand

| Feature | SmolEyes | SmolHand |
|---------|----------|----------|
| **Purpose** | Vision analysis | Small LLM tool-calling |
| **Model** | Florence-2 | Various (Qwen, Mistral) |
| **Input** | Screenshots | Text prompts |
| **Output** | Visual descriptions, OCR | Tool calls, text |
| **Use Case** | "What do I see?" | "What should I do?" |
| **Analogy** | 👁️ THE EYES | 👐 THE HANDS |

## Architecture Analogy

```
smolclaw (THE BODY)
    ├── agent (THE BRAAIN) - Makes decisions
    ├── smolhand (THE HANDS) - Manipulates browser
    └── smoleyes (THE EYES) - Sees and understands visually
```

## Files Created

1. **smolclaw/smoleyes/__init__.py**
   - SmolEyes class
   - All exports

2. **smolclaw/smoleyes/runtime.py**
   - Core vision functions
   - Florence-2 integration
   - Screenshot capture

3. **smolclaw/smoleyes/tools.py**
   - @tool decorated functions
   - Agent-facing tools

4. **docs/SMOLEYES.md**
   - Full documentation
   - Usage examples
   - API reference

## Files Updated

1. **smolclaw/agent/tools/ToolRegistry.py**
   - Added SmolEyes tools
   - Updated tool registry

2. **smolclaw/__init__.py**
   - Added smoleyes export

3. **README.md**
   - Updated architecture section
   - Added smoleyes description

## Use Cases

### 1. Accessibility Analysis
```python
eyes = SmolEyes()
desc = eyes.describe_page("Describe the page structure")
buttons = eyes.find("button")
```

### 2. Form Detection
```python
fields = eyes.find("text input field")
text = eyes.read_text()  # OCR for labels
```

### 3. Visual Search
```python
result = eyes.find("shopping cart icon")
if result["found"]:
    bbox = result["elements"][0]["bbox"]
```

### 4. OCR for Images
```python
text = eyes.read_text()
print("Text in image:", text["ocr"]["text"])
```

## Requirements

- Florence-2 model (auto-loaded)
- Browser with screenshot capability
- Helium/Selenium driver

## Summary

✅ **SmolEyes created** - Vision tool for AI Agent
✅ **5 tools available** - Analyze, describe, find, extract, detect
✅ **Integrated with agent** - Tools registered in ToolRegistry
✅ **High-level API** - SmolEyes class for easy usage
✅ **Documentation** - Full docs in docs/SMOLEYES.md

**The AI Agent now has EYES to see! 👁️🤖**

```python
from smolclaw.smoleyes import SmolEyes

eyes = SmolEyes()
result = eyes.describe_page("What can I do on this page?")
```

Just like smolhand provides "hands" for tool-calling, **smoleyes provides "eyes" for vision-based analysis!**
