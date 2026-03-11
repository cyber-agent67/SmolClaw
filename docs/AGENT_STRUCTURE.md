# SmolClaw Agent System Structure

## Overview

The **smolclaw.agent** package is the AI Agent core (THE BRAIN) of the SmolClaw system. It follows the Entity-Interaction Model (EIM) architecture.

## Directory Structure

```
smolclaw/agent/
│
├── __init__.py                          # Package exports
├── main.py                              # Main orchestration (run_agent_with_args)
│
├── config/                              # Configuration
│   ├── __init__.py
│   ├── BrowserConfig.py                 # Browser configuration
│   └── GatewayConfig.py                 # Gateway configuration
│
├── entities/                            # Pure state containers (EIM Entities)
│   ├── __init__.py
│   │
│   ├── actions/                         # Action entities
│   │   ├── __init__.py
│   │   ├── DeclarativeAction.py         # Declarative action definitions
│   │   └── ImperativeCommand.py         # Imperative command definitions
│   │
│   ├── browser/                         # Browser state entities
│   │   ├── __init__.py
│   │   ├── Address.py                   # Address information
│   │   ├── Browser.py                   # Browser state
│   │   ├── BrowserRegistry.py           # Browser registry
│   │   ├── DOMTree.py                   # DOM tree structure
│   │   ├── ElementTarget.py             # Element target definition
│   │   ├── GeoLocation.py               # Geolocation data
│   │   ├── NavigationStack.py           # Navigation history stack
│   │   ├── PageState.py                 # Page state (URL, title, source)
│   │   ├── ScoutResult.py               # Scout operation result
│   │   ├── Screenshot.py                # Screenshot data
│   │   └── Tab.py                       # Tab state
│   │
│   ├── chronicle/                       # Chronicle entities (SaaS automation)
│   │   ├── __init__.py
│   │   ├── agent_config.py
│   │   ├── analysis.py
│   │   ├── app_drift.py
│   │   ├── app_inventory.py
│   │   ├── credentials.py
│   │   ├── extraction_schema.py
│   │   ├── harvest.py
│   │   ├── navigation.py
│   │   ├── pipeline.py
│   │   ├── saas.py
│   │   ├── schedule_run.py
│   │   ├── settings.py
│   │   └── vault.py
│   │
│   ├── memory/                          # Memory entities
│   │   ├── __init__.py
│   │   ├── Experience.py                # Experience record
│   │   ├── ExperienceMemory.py          # Experience memory store
│   │   └── PromptCache.py               # Prompt cache entry
│   │
│   ├── perception/                      # Perception entities
│   │   ├── __init__.py
│   │   ├── DOMDescription.py            # DOM description
│   │   ├── PageDescription.py           # Page description
│   │   ├── PerceptionConfig.py          # Perception configuration
│   │   └── VisualDescription.py         # Visual description
│   │
│   ├── q_learning/                      # Q-learning entities
│   │   ├── __init__.py
│   │   └── scoring.py                   # Q-learning score state
│   │
│   └── runtime/                         # Runtime entities
│       ├── __init__.py
│       ├── Agent.py                     # Agent state
│       ├── AgentState.py                # Agent execution state
│       ├── EnhancedArgs.py              # Enhanced arguments
│       ├── ExecutionContract.py         # Execution contract
│       ├── GatewaySession.py            # Gateway session
│       ├── Intent.py                    # User intent
│       ├── Plan.py                      # Execution plan
│       └── ToolResult.py                # Tool execution result
│
├── interactions/                        # Business logic (EIM Interactions)
│   ├── __init__.py
│   │
│   ├── agent/                           # Agent lifecycle
│   │   ├── __init__.py
│   │   ├── Initialize.py                # Initialize agent
│   │   ├── Run.py                       # Run agent loop
│   │   └── Cleanup.py                   # Cleanup resources
│   │
│   ├── args/                            # Argument parsing
│   │   ├── __init__.py
│   │   └── Parse.py                     # Parse command-line args
│   │
│   ├── browser/                         # Browser operations
│   │   ├── __init__.py
│   │   ├── CloseAllBrowsers.py          # Close all browsers
│   │   ├── GetPageSource.py             # Get page source
│   │   ├── Initialize.py                # Initialize browser
│   │   ├── Quit.py                      # Quit browser
│   │   ├── RegisterBrowser.py           # Register browser
│   │   └── UnregisterBrowser.py         # Unregister browser
│   │
│   ├── chronicle/                       # Chronicle operations (SaaS)
│   │   ├── __init__.py
│   │   ├── drift_detection.py           # Detect UI drift
│   │   ├── exploration.py               # SaaS exploration
│   │   ├── extraction.py                # Data extraction
│   │   ├── login.py                     # SaaS login
│   │   ├── onboarding.py                # SaaS onboarding
│   │   └── pipeline.py                  # Pipeline execution
│   │
│   ├── dom/                             # DOM operations
│   │   ├── __init__.py
│   │   └── GetTree.py                   # Get DOM tree
│   │
│   ├── florence/                        # Florence-2 operations
│   │   ├── __init__.py
│   │   ├── CaptionImage.py              # Caption image
│   │   ├── DetectObjects.py             # Detect objects
│   │   ├── GroundElement.py             # Ground element
│   │   ├── LoadModel.py                 # Load Florence model
│   │   └── OCRImage.py                  # OCR on image
│   │
│   ├── gateway/                         # Gateway operations
│   │   ├── __init__.py
│   │   ├── HandleConnection.py          # Handle websocket connection
│   │   └── RouteMessage.py              # Route messages
│   │
│   ├── location/                        # Location operations
│   │   ├── __init__.py
│   │   ├── GetAddress.py                # Get address info
│   │   └── GetGeoLocation.py            # Get geolocation
│   │
│   ├── memory/                          # Memory operations
│   │   ├── __init__.py
│   │   ├── FindSimilarExperiences.py    # Find similar experiences
│   │   ├── GetSuccessfulPatterns.py     # Get successful patterns
│   │   ├── LoadExperiences.py           # Load experiences
│   │   └── SaveExperience.py            # Save experience
│   │
│   ├── navigation/                      # Navigation operations
│   │   ├── __init__.py
│   │   ├── ClosePopups.py               # Close popups
│   │   ├── GoBack.py                    # Navigate back
│   │   ├── GoToURL.py                   # Navigate to URL
│   │   └── SearchOnPage.py              # Search on page (Ctrl+F)
│   │
│   ├── output/                          # Output operations
│   │   ├── __init__.py
│   │   └── SaveResult.py                # Save result
│   │
│   ├── perception/                      # Perception operations
│   │   ├── __init__.py
│   │   ├── CapturePageState.py          # Capture page state
│   │   ├── DescribeDOM.py               # Describe DOM
│   │   ├── DescribeScreenshot.py        # Describe screenshot
│   │   ├── IdentifyElements.py          # Identify elements
│   │   ├── ImageAnalysis.py             # Image analysis
│   │   └── MergeDescriptions.py         # Merge descriptions
│   │
│   ├── planner/                         # Planning operations
│   │   ├── __init__.py
│   │   └── GeneratePlan.py              # Generate execution plan
│   │
│   ├── prompt/                          # Prompt operations
│   │   ├── __init__.py
│   │   ├── Enhance.py                   # Enhance prompt
│   │   ├── LoadCache.py                 # Load prompt cache
│   │   ├── Refine.py                    # Refine prompt
│   │   └── SaveCache.py                 # Save prompt cache
│   │
│   ├── runloop/                         # Run loop operations
│   │   ├── __init__.py
│   │   └── Execute.py                   # Execute run loop
│   │
│   ├── scout/                           # Scout operations
│   │   ├── __init__.py
│   │   └── FindPathToTarget.py          # Find path to target (Grappling Hook)
│   │
│   ├── screenshot/                      # Screenshot operations
│   │   ├── __init__.py
│   │   └── Capture.py                   # Capture screenshot
│   │
│   ├── smolhand/                        # Smolhand operations
│   │   ├── __init__.py
│   │   ├── Act.py                       # Act (smolhand)
│   │   ├── ExecuteCommand.py            # Execute command
│   │   ├── Extract.py                   # Extract (smolhand)
│   │   ├── Observe.py                   # Observe (smolhand)
│   │   ├── ResolveAction.py             # Resolve action
│   │   └── Transform.py                 # Transform (smolhand)
│   │
│   ├── tab/                             # Tab operations
│   │   ├── __init__.py
│   │   ├── Close.py                     # Close tab
│   │   ├── Create.py                    # Create tab
│   │   └── Switch.py                    # Switch tab
│   │
│   └── thinking/                        # Thinking operations
│       ├── __init__.py
│       └── Think.py                     # Think (cognitive strategy)
│
├── models/                              # Model implementations
│   ├── __init__.py
│   └── FlorenceModelSingleton.py        # Florence-2 model singleton
│
├── repositories/                        # Persistence layer
│   ├── __init__.py
│   ├── ExperienceRepository.py          # Experience persistence
│   ├── NavigationStackRepository.py     # Navigation stack persistence
│   └── PromptCacheRepository.py         # Prompt cache persistence
│
└── tools/                               # AI Agent tools (@tool decorated)
    ├── __init__.py
    ├── ToolRegistry.py                  # Main tool registry
    ├── SmolhandTools.py                 # Smolhand tool definitions
    │
    ├── exploration/                     # Exploration tool (A*)
    │   ├── __init__.py
    │   ├── entities.py                  # Exploration entities
    │   ├── interactions.py              # Exploration interactions
    │   └── tool.py                      # explore_dom_with_astar @tool
    │
    ├── q_learning/                      # Q-learning tool
    │   ├── __init__.py
    │   ├── entities.py                  # Q-learning entities
    │   ├── interactions.py              # Q-learning interactions
    │   └── tool.py                      # score_task_progress_q_learning @tool
    │
    └── vision/                          # Vision tool
        ├── __init__.py
        ├── entities.py                  # Vision entities
        ├── interactions.py              # Vision interactions
        └── tool.py                      # analyze_visual_context @tool
```

## Key Components

### 1. Entities (State Containers)

Pure data structures with no business logic:
- **Browser entities**: Browser, Tab, NavigationStack, PageState, etc.
- **Memory entities**: Experience, ExperienceMemory, PromptCache
- **Runtime entities**: Agent, AgentState, Plan, ToolResult
- **Perception entities**: PageDescription, VisualDescription, DOMDescription

### 2. Interactions (Business Logic)

Stateless operations that work on entities:
- **Agent interactions**: Initialize, Run, Cleanup
- **Browser interactions**: Initialize, Quit, Register, Unregister
- **Navigation interactions**: GoToURL, GoBack, SearchOnPage
- **Tab interactions**: Create, Switch, Close
- **Memory interactions**: LoadExperiences, SaveExperience
- **Perception interactions**: CapturePageState, DescribeScreenshot

### 3. Tools (AI Agent Interface)

@tool decorated functions for agent use:
- **Vision tools**: analyze_visual_context
- **Exploration tools**: explore_dom_with_astar
- **Q-learning tools**: score_task_progress_q_learning
- **Browser tools**: get_DOM_Tree, set_browser_url, etc.
- **Scout tools**: find_path_to_target

### 4. Repositories (Persistence)

Data access layer:
- **ExperienceRepository**: Experience persistence
- **NavigationStackRepository**: Navigation stack persistence
- **PromptCacheRepository**: Prompt cache persistence

### 5. Config (Configuration)

Configuration management:
- **BrowserConfig**: Browser configuration
- **GatewayConfig**: Gateway configuration

## Entity-Interaction Model (EIM)

The agent follows the EIM pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTITY-INTERACTION MODEL                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ENTITIES (Pure State)          INTERACTIONS (Logic)        │
│  ┌────────────────────┐         ┌────────────────────┐     │
│  │  Browser           │  ────►  │  InitializeBrowser │     │
│  │  - driver          │         │  QuitBrowser       │     │
│  │  - is_running      │         │  RegisterBrowser   │     │
│  │  - headless        │         └────────────────────┘     │
│  └────────────────────┘                                      │
│                                                              │
│  ┌────────────────────┐         ┌────────────────────┐     │
│  │  Tab               │  ────►  │  CreateTab         │     │
│  │  - url             │         │  SwitchTab         │     │
│  │  - history         │         │  CloseTab          │     │
│  │  - active          │         └────────────────────┘     │
│  └────────────────────┘                                      │
│                                                              │
│  ┌────────────────────┐         ┌────────────────────┐     │
│  │  ExperienceMemory  │  ────►  │  LoadExperiences   │     │
│  │  - experiences     │         │  SaveExperience    │     │
│  └────────────────────┘         └────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tool Integration

Tools bridge EIM to smolagents:

```python
# smolclaw/agent/tools/ToolRegistry.py

@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    """Use SmolEyes vision AI to analyze the current page's visual content."""
    from smolclaw.tools.smoleyes.tools import analyze_visual_context as eyes_tool
    
    recovery_note = _recover_live_page("analyze_visual_context")
    payload = eyes_tool(prompt_hint)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload
```

## Main Entry Point

```python
# smolclaw/agent/main.py

def run_agent_with_args(args):
    """Main orchestration function."""
    load_dotenv()
    
    # Initialize memory
    experience_memory = ExperienceMemory()
    LoadExperiences.execute(experience_memory)
    
    # Initialize navigation
    navigation_stack = NavigationStack()
    navigation_stack.stack = [args.url]
    
    # Initialize browser
    config = BrowserConfig()
    browser = InitializeBrowser.execute(config)
    
    # Initialize agent
    agent = InitializeAgent.execute(
        model_type=args.model_type,
        model_id=args.model_id,
        screenshot_callback=screenshot_callback,
    )
    
    # Run agent
    return RunAgent.execute(
        agent=agent,
        prompt=prompt,
        start_url=args.url,
        experience_memory=experience_memory,
        navigation_stack=navigation_stack,
    )
```

## Summary

The **smolclaw.agent** package provides:
- **Clean separation**: Entities (state) vs Interactions (logic)
- **Modular tools**: Each intelligence as a separate @tool
- **Persistence**: Repositories for experiences, navigation, prompts
- **Configuration**: Browser and gateway configuration
- **Extensibility**: Easy to add new entities, interactions, and tools

**Location:** `smolclaw/agent/`
**Purpose:** AI Agent core (THE BRAIN)
**Pattern:** Entity-Interaction Model (EIM)
