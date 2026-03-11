# SmolClaw Cognitive System - Complete Architecture

## Overview

SmolClaw has been transformed into a **distributed cognitive system** with a **unified gateway architecture** that supports multiple interfaces (TUI, CLI, Telegram) all routing through a central gateway.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERFACES                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │  TUI Client  │     │  CLI Client  │     │  Telegram    │            │
│  │  (WebSocket) │     │  (WebSocket) │     │  (Future)    │            │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘            │
│         │                    │                    │                     │
│         └────────────────────┼────────────────────┘                     │
│                              │                                          │
│                              ▼                                          │
│                    ┌──────────────────┐                                │
│                    │   GATEWAY        │                                │
│                    │   (WebSocket +   │                                │
│                    │    REST API)     │                                │
│                    └────────┬─────────┘                                │
│                             │                                          │
│                             ▼                                          │
│                    ┌──────────────────┐                                │
│                    │  Session Manager │                                │
│                    │  - Per-session   │                                │
│                    │    cognitive     │                                │
│                    │    loops         │                                │
│                    │  - Persistence   │                                │
│                    └────────┬─────────┘                                │
│                             │                                          │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │              COGNITIVE CORE (per session)                         │ │
│  │                                                                   │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │ │
│  │  │  Probabilistic   │  │  Explicit DFA    │  │  Event         │ │ │
│  │  │  Planner         │  │  State Machine   │  │  Sourcing      │ │ │
│  │  │                  │  │                  │  │                │ │ │
│  │  │  - Strategy      │  │  - AWAIT_INTENT  │  │  - EventStore  │ │ │
│  │  │    sampling      │  │  - PLANNING      │  │  - Replay      │ │ │
│  │  │  - Learned       │  │  - EXECUTING     │  │  - Fold        │ │ │
│  │  │    confidence    │  │  - DONE/ERROR    │  │  - CQRS        │ │ │
│  │  │  - Bayesian      │  │                  │  │                │ │ │
│  │  │    updating      │  │                  │  │                │ │ │
│  │  └──────────────────┘  └──────────────────┘  └────────────────┘ │ │
│  │                                                                   │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │
│  │  │           Pure Functional Effects                            │ │
│  │  │                                                              │ │
│  │  │  Effect[T], Result[T,E], State[T], Event, EventStream       │ │
│  │  └──────────────────────────────────────────────────────────────┘ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                             │                                          │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    TOOLS                                         │ │
│  │  - smolhand (Browser + Small LLM)                                │ │
│  │  - smoleyes (Vision)                                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Gateway Architecture

### Gateway Server (`smolclaw/gateway/server.py`)

**Purpose:** Unified entry point for all interfaces

**Features:**
- WebSocket server for real-time communication
- REST API for programmatic access
- Session management with persistence
- Cognitive loop integration per session

**Endpoints:**
```
WebSocket: ws://{host}:{port}/ws?session_id={id}
REST API:
  - POST /api/v1/process       - Process intent
  - GET  /api/v1/session/{id}  - Get session state
  - GET  /api/v1/replay/{id}   - Replay events
  - GET  /api/v1/health        - Health check
```

**Session Management:**
- Each client gets a dedicated cognitive session
- Sessions have isolated event stores
- Automatic cleanup of expired sessions
- Optional persistence to disk

### TUI Client (`smolclaw/gateway/tui_client.py`)

**Purpose:** Interactive terminal UI that connects to gateway

**Features:**
- Real-time WebSocket communication
- Interactive command loop
- State display and event replay
- Session management

**Commands:**
```
cognitive> /state   - Show cognitive state
cognitive> /replay  - Replay events
cognitive> /exit    - Exit
cognitive> [intent] - Process intent
```

### Future Interfaces

**CLI Client:**
```python
# Direct WebSocket CLI
smolclaw cli --gateway ws://localhost:8765/ws
```

**Telegram Bot:**
```python
# Telegram bot that connects to gateway
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    ws = connect_to_gateway()
    ws.send_json({"type": "process", "prompt": message.text})
    response = ws.recv()
    bot.reply_to(message, response["result"])
```

---

## Cognitive Core Components

### 1. Pure Functional Effects

**Location:** `smolclaw/cognitive/effects.py`

**Types:**
- `Effect[T]` - Deferred computation with side effects
- `Result[T, E]` - Success or error
- `State[T]` - Stateful computation
- `Event` - Immutable event record
- `EventStream` - Immutable event stream

**Usage:**
```python
from smolclaw.cognitive import Effect, Success, Error

# Pure function
def add(a: int, b: int) -> int:
    return a + b

# Effectful computation
def read_file(path: str) -> Effect[str]:
    return Effect(lambda: open(path).read())

# Compose effects
result = read_file("data.txt").map(len).run()

# Error handling
result = safe_divide(10, 0)  # Returns Error("Division by zero")
```

### 2. Probabilistic Planner

**Location:** `smolclaw/cognitive/planner.py`

**Features:**
- Samples strategies from learned distributions
- Computes confidence from historical success rates
- Bayesian updating from outcomes
- Context-dependent plan generation

**Strategies:**
| Strategy | Prior | Use Case |
|----------|-------|----------|
| `direct_tool_use` | 0.6 | Clear goals with known tools |
| `explore_then_act` | 0.3 | Uncertain environments |
| `ask_clarification` | 0.1 | Ambiguous goals |

**Usage:**
```python
from smolclaw.cognitive import ProbabilisticPlanner

planner = ProbabilisticPlanner()

# Generate plan (learns confidence)
plan = planner.plan("Find release notes")
print(f"Strategy: {plan.strategy}, Confidence: {plan.confidence}")

# Learn from outcome
planner.update_from_outcome(plan.strategy, success=True)
```

### 3. Explicit DFA State Machine

**Location:** `smolclaw/cognitive/state_machine.py`

**States:**
```python
class AgentState(Enum):
    AWAIT_INTENT = "await_intent"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAIT_CLARIFICATION = "await_clarification"
    DONE = "done"
    ERROR = "error"
```

**Transitions:**
| From | Event | To | Guard |
|------|-------|---|-------|
| AWAIT_INTENT | INTENT_RECEIVED | PLANNING | intent exists |
| PLANNING | PLAN_GENERATED | EXECUTING | confidence > 0.3 |
| EXECUTING | GOAL_ACHIEVED | DONE | success |
| ANY | ERROR_OCCURRED | ERROR | - |

**Usage:**
```python
from smolclaw.cognitive import create_dfa, AgentEvent

dfa = create_dfa()
dfa.fire_event(AgentEvent.INTENT_RECEIVED, {"intent": "goal"})
# State: AWAIT_INTENT → PLANNING
```

### 4. Event Sourcing

**Location:** `smolclaw/cognitive/event_sourcing.py`

**Event Types:**
- `IntentReceivedEvent`
- `PlanGeneratedEvent`
- `ToolExecutedEvent`
- `NavigationEvent`
- `TaskCompletedEvent`
- `ErrorEvent`

**Features:**
- Append-only event store
- State reconstruction via fold
- Event replay for debugging
- CQRS (separate read/write models)

**Usage:**
```python
from smolclaw.cognitive import EventStore, IntentReceivedEvent

store = EventStore(persistence_path="./events")

# Append events
store.append(IntentReceivedEvent(intent="goal"))

# Replay
events = store.replay()

# Fold (reconstruct state)
state = store.fold(initial_state, reducer)
```

---

## Usage Guide

### 1. Start Gateway

```bash
# Start gateway server
smolclaw gateway start --port 8765 --api-port 8766

# With persistence
smolclaw gateway start --persistence ~/.smolclaw/gateway_sessions
```

### 2. Connect TUI Client

```bash
# Connect to gateway
smolclaw tui

# Or specify custom gateway URL
smolclaw tui --url ws://localhost:8765/ws
```

### 3. Use REST API

```bash
# Process intent
curl -X POST http://localhost:8766/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"intent": "Find release notes", "session_id": "my_session"}'

# Get session state
curl http://localhost:8766/api/v1/session/my_session

# Replay events
curl http://localhost:8766/api/v1/replay/my_session?from_version=0
```

### 4. Programmatic Use

```python
from smolclaw import CognitiveLoop

# Create cognitive loop
loop = CognitiveLoop(persistence_path="./events")

# Process intent
result = loop.process_intent("Find release notes")

# Get state
state = loop.get_state()
print(state["agent_state"])

# Replay events
events = loop.replay()
```

---

## Testing

### Run Tests

```bash
# Install package
pip install -e .

# Run cognitive system tests
python -m smolclaw.cognitive_loop --prompt "Test" --show-state
```

### Test Gateway

```bash
# Terminal 1: Start gateway
smolclaw gateway start

# Terminal 2: Connect TUI
smolclaw tui
```

---

## File Structure

```
smolclaw/
├── cognitive/                    # Cognitive core
│   ├── __init__.py
│   ├── effects.py               # Effect types
│   ├── planner.py               # Probabilistic planner
│   ├── state_machine.py         # Explicit DFA
│   └── event_sourcing.py        # Event store
│
├── gateway/                      # Gateway server
│   ├── __init__.py
│   ├── server.py                # Gateway server
│   └── tui_client.py            # TUI client
│
├── tools/                        # Tool integrations
│   ├── smolhand/                # Browser + Small LLM
│   └── smoleyes/                # Vision analysis
│
├── cognitive_loop.py             # Cognitive runloop
└── cli.py                        # CLI interface
```

---

## Key Benefits

| Property | Before | After |
|----------|--------|-------|
| **Interfaces** | Single CLI | ✅ TUI, CLI, Gateway (Telegram future) |
| **Side Effects** | Hidden | ✅ Explicit (Effect types) |
| **Planning** | Deterministic | ✅ Probabilistic (learns) |
| **State** | Implicit | ✅ Explicit (DFA) |
| **History** | Lost | ✅ Event sourcing |
| **Sessions** | None | ✅ Multi-session gateway |
| **Persistence** | None | ✅ Event persistence |
| **Debugging** | Hard | ✅ Event replay |

---

## Next Steps

1. **Deploy Gateway** - Run gateway on server for remote access
2. **Add Telegram Bot** - Implement Telegram interface
3. **Web Interface** - Add web-based UI
4. **ML Integration** - Train strategy probabilities on historical data
5. **Distributed Deployment** - Split into microservices

---

## Summary

✅ **Cognitive System:** Pure functions, probabilistic planning, explicit DFA, event sourcing
✅ **Gateway Architecture:** All interfaces (TUI, CLI, Telegram) route through gateway
✅ **Session Management:** Per-session cognitive loops with persistence
✅ **Multi-Interface:** WebSocket + REST API support

**You've built a distributed cognitive system with a unified gateway architecture!** 🧠🤖
