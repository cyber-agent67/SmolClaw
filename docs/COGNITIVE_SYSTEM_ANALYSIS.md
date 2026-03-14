# Cognitive System Architecture Analysis

## Question: Is SmolClaw a Distributed Cognitive System?

We're scanning the repository to check for these properties:
1. ✅ **Smolhand as pure function entity**
2. ✅ **Planner as probabilistic intent emitter**
3. ✅ **Runloop as deterministic finite automaton**
4. ✅ **Event-sourced architecture**

---

## 1. Smolhand as Pure Function Entity

### Current Implementation

**Location:** `smolclaw/tools/smolhand/runtime.py`

```python
def ensure_connected_page(url: str, headless: bool = False) -> str:
    """Declarative smolhand API to connect browser session to a single page."""
    if not isinstance(url, str) or not url.strip():
        return "Smolhand connection error: url must be a non-empty string."
    # ...
```

### Analysis

| Property | Status | Evidence |
|----------|--------|----------|
| **Pure functions** | ⚠️ PARTIAL | Functions have side effects (browser state) but are deterministic |
| **Stateless** | ❌ NO | Uses global `_SMOLHAND_BROWSER` singleton |
| **Referential transparency** | ⚠️ PARTIAL | Same input → same output, but depends on external browser state |
| **Function composition** | ✅ YES | Tools compose: `ensure_connected_page` → `set_browser_url` → `get_browser_snapshot` |

### Verdict: **60% Pure Function Entity**

**What's there:**
- ✅ Declarative API (`ensure_connected_page`)
- ✅ Deterministic behavior
- ✅ Clear input/output contracts
- ✅ Tool composition

**What's missing:**
- ❌ Global mutable state (`_SMOLHAND_BROWSER`)
- ❌ Side effects not isolated
- ❌ No explicit effect types

**To go deeper:**
```python
# Current (impure)
def ensure_connected_page(url: str) -> str:
    _ensure_browser_started()  # Side effect!
    # ...

# Pure function version (effect-typed)
def ensure_connected_page(url: str) -> Effect[ConnectionResult]:
    return Effect(
        lambda: _ensure_browser_started(),
        lambda browser: _set_url(browser, url),
        lambda snapshot: ConnectionResult(url, snapshot)
    )
```

---

## 2. Planner as Probabilistic Intent Emitter

### Current Implementation

**Location:** `smolclaw/agent/interactions/planner/GeneratePlan.py`

```python
class GeneratePlan:
    @staticmethod
    def execute(intent: Intent) -> Plan:
        plan = Plan()
        plan.goal = intent.user_input
        plan.requires_tools = True
        plan.requires_navigation = True
        plan.strategy = "Observe page, use tools, iterate until goal is met."
        plan.steps_description = [
            "Observe page state",
            "Choose tool actions",
            "Execute actions",
            "Return final answer",
        ]
        plan.confidence = 0.5  # ← Fixed probability!
        return plan
```

### Analysis

| Property | Status | Evidence |
|----------|--------|----------|
| **Intent input** | ✅ YES | `Intent` entity with `user_input`, `session_id`, `metadata` |
| **Probabilistic output** | ❌ NO | `confidence = 0.5` is hardcoded, not computed |
| **Strategy emission** | ⚠️ PARTIAL | Fixed strategy string, not sampled from distribution |
| **Step generation** | ❌ NO | Fixed steps, not dynamically generated |

### Verdict: **40% Probabilistic Intent Emitter**

**What's there:**
- ✅ `Intent` entity captures user intent
- ✅ `Plan` entity with confidence score
- ✅ Strategy field for approach
- ✅ Clear intent → plan transformation

**What's missing:**
- ❌ Confidence is hardcoded (0.5), not computed
- ❌ No probability distribution over plans
- ❌ No sampling from strategy space
- ❌ Fixed steps, not context-dependent

**To go deeper:**
```python
# Current (deterministic)
def execute(intent: Intent) -> Plan:
    plan.confidence = 0.5  # Fixed!
    plan.strategy = "Observe page, use tools..."  # Fixed!
    return plan

# Probabilistic version
def execute(intent: Intent) -> Plan:
    # Sample from distribution over strategies
    strategies = [
        ("direct_tool_use", 0.6),
        ("explore_then_act", 0.3),
        ("ask_clarification", 0.1),
    ]
    strategy = sample(strategies)  # ← Probabilistic!
    
    # Compute confidence from intent clarity
    confidence = compute_confidence(intent)  # ← Learned!
    
    # Generate steps based on strategy
    steps = generate_steps(strategy, intent)  # ← Dynamic!
    
    return Plan(strategy=strategy, confidence=confidence, steps=steps)
```

---

## 3. Runloop as Deterministic Finite Automaton

### Current Implementation

**Location:** `smolclaw/agent/interactions/runloop/Execute.py`

```python
class ExecuteRunloop:
    @staticmethod
    def execute(intent: Intent, max_loops: int = 10) -> AgentState:
        state = AgentState()
        state.goal = intent.user_input
        state.max_loops = max_loops
        
        plan = GeneratePlan.execute(intent)
        state.current_phase = "planning"
        state.context.extend(plan.steps_description)
        
        # Execute
        state.current_phase = "executing"
        state.final_answer = runner.run(intent.user_input, max_loops=max_loops)
        state.loop_count = 1
        state.current_phase = "done"
        state.done = True
        
        return state
```

### Analysis

| Property | Status | Evidence |
|----------|--------|----------|
| **Discrete states** | ✅ YES | `current_phase`: "await_intent" → "planning" → "executing" → "done" |
| **Deterministic transitions** | ✅ YES | Fixed state machine flow |
| **State transitions** | ⚠️ PARTIAL | Phases change, but not explicit transition function |
| **Terminal states** | ✅ YES | `done = True`, `current_phase = "done"` or `"error"` |

### Verdict: **70% Deterministic Finite Automaton**

**What's there:**
- ✅ Clear state phases: `await_intent` → `planning` → `executing` → `done`
- ✅ Deterministic flow (no randomness in transitions)
- ✅ Terminal states (`done`, `error`)
- ✅ State entity (`AgentState`) tracks current phase

**What's missing:**
- ❌ No explicit transition function `δ(state, input) → state`
- ❌ No formal state machine definition
- ❌ Transitions embedded in code, not declarative
- ❌ No transition guards or conditions

**To go deeper:**
```python
# Current (implicit state machine)
state.current_phase = "planning"
# ... do planning ...
state.current_phase = "executing"

# Explicit DFA version
class AgentState(Enum):
    AWAIT_INTENT = "await_intent"
    PLANNING = "planning"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"

class Transition:
    def __init__(self, from_state: AgentState, event: str, to_state: AgentState, guard: Callable):
        self.from_state = from_state
        self.event = event
        self.to_state = to_state
        self.guard = guard

# Explicit transition table
TRANSITIONS = [
    Transition(AgentState.AWAIT_INTENT, "intent_received", AgentState.PLANNING, lambda _: True),
    Transition(AgentState.PLANNING, "plan_generated, AgentState.EXECUTING, lambda plan: plan.confidence > 0.3),
    Transition(AgentState.EXECUTING, "success", AgentState.DONE, lambda result: result.success),
    Transition(AgentState.EXECUTING, "error", AgentState.ERROR, lambda _: True),
]

def transition(state: AgentState, event: str, context: dict) -> AgentState:
    for t in TRANSITIONS:
        if t.from_state == state and t.event == event and t.guard(context):
            return t.to_state
    return state  # No transition
```

---

## 4. Event-Sourced Architecture

### Current Implementation

**Locations:**
- `smolclaw/agent/repositories/ExperienceRepository.py`
- `smolclaw/agent/entities/memory/Experience.py`
- `smolclaw/agent/entities/browser/Tab.py` (history)
- `smolclaw/agent/entities/chronicle/harvest.py` (actions performed)

```python
# Experience entity (event-like)
class Experience:
    def __init__(self):
        self.task: str = ""
        self.success: bool = False
        self.steps: List[str] = []
        self.outcome: str = ""
        self.timestamp: str = ""

# Tab history (event log)
class Tab:
    def __init__(self):
        self.url: str = ""
        self.history: List[str] = []  # ← Event log!
        self.active: bool = False

# Harvest actions (event stream)
class HarvestResult:
    actions_performed: list[HarvestAction] = []  # ← Event stream!
    settings_tree: list[SettingsNode] = []
```

### Analysis

| Property | Status | Evidence |
|----------|--------|----------|
| **Event log** | ⚠️ PARTIAL | `Tab.history`, `HarvestResult.actions_performed` |
| **State from events** | ❌ NO | State not reconstructed from events |
| **Event persistence** | ⚠️ PARTIAL | `ExperienceRepository.save/load` |
| **Event replay** | ❌ NO | No replay mechanism |
| **Temporal ordering** | ⚠️ PARTIAL | Timestamps on experiences |

### Verdict: **30% Event-Sourced Architecture**

**What's there:**
- ✅ `Experience` entities (event-like records)
- ✅ `Tab.history` (URL navigation log)
- ✅ `HarvestResult.actions_performed` (action event stream)
- ✅ `ExperienceRepository` for persistence
- ✅ Timestamps on experiences

**What's missing:**
- ❌ State not reconstructed from events (no `fold` operation)
- ❌ No event replay mechanism
- ❌ No event store (just file-based save/load)
- ❌ No event versioning or schema evolution
- ❌ No CQRS (Command Query Responsibility Segregation)

**To go deeper:**
```python
# Current (state-based)
class AgentState:
    goal: str
    context: List[str]
    final_answer: str

# Event-sourced version
class Event:
    pass

class IntentReceived(Event):
    intent: str
    timestamp: datetime

class PlanGenerated(Event):
    plan: Plan
    timestamp: datetime

class ToolExecuted(Event):
    tool_name: str
    result: str
    timestamp: datetime

class TaskCompleted(Event):
    answer: str
    timestamp: datetime

# Event store
class EventStore:
    def __init__(self):
        self.events: List[Event] = []
    
    def append(self, event: Event):
        self.events.append(event)
    
    def replay(self, from_version: int = 0) -> AgentState:
        state = AgentState()
        for event in self.events[from_version:]:
            state = state.apply(event)  # ← Fold events into state
        return state
```

---

## Overall Assessment

### Current Architecture Score

| Component | Score | Status |
|-----------|-------|--------|
| Smolhand (Pure Functions) | 60% | ⚠️ Partial |
| Planner (Probabilistic) | 40% | ⚠️ Partial |
| Runloop (DFA) | 70% | ✅ Mostly |
| Event Sourcing | 30% | ❌ Minimal |

**Overall: 50% - Hybrid Imperative/Functional Architecture**

### What You Have

✅ **Strong foundations:**
- Clear entity/interaction separation (EIM pattern)
- Explicit state machines (phases)
- Event-like records (experiences, actions)
- Declarative APIs (smolhand)

⚠️ **Missing for full cognitive system:**
- Pure functional effects (no global state)
- True probabilistic planning (learned confidence)
- Explicit DFA transitions (transition tables)
- Full event sourcing (replay, fold, CQRS)

---

## Roadmap to Distributed Cognitive System

### Phase 1: Pure Functions (2-3 weeks)
- [ ] Remove global `_SMOLHAND_BROWSER` singleton
- [ ] Add explicit effect types (`Effect[T]`)
- [ ] Isolate side effects to boundaries
- [ ] Make all tool functions pure

### Phase 2: Probabilistic Planner (3-4 weeks)
- [ ] Learn confidence from historical success rates
- [ ] Sample strategies from learned distribution
- [ ] Generate dynamic plans based on context
- [ ] Add Bayesian updating for plan confidence

### Phase 3: Explicit DFA (1-2 weeks)
- [ ] Define `AgentState` enum
- [ ] Create explicit transition table
- [ ] Add transition guards
- [ ] Make transitions declarative

### Phase 4: Event Sourcing (4-6 weeks)
- [ ] Define event types for all state changes
- [ ] Implement event store
- [ ] Add state reconstruction from events
- [ ] Implement event replay
- [ ] Add CQRS (separate read/write models)

### Phase 5: Distribution (8-12 weeks)
- [ ] Split into microservices (Planner, Executor, Memory)
- [ ] Add message queues between services
- [ ] Implement eventual consistency
- [ ] Add distributed tracing

---

## Conclusion

**Current State:** You have a **well-structured imperative system with functional leanings**.

**Not yet:** A true distributed cognitive system.

**Potential:** The architecture has **excellent foundations** for evolving into one:
- EIM pattern is a stepping stone to functional effects
- Phase-based execution is close to DFA
- Experience records are proto-events
- Clear separation of concerns enables distribution

**Recommendation:** If you want a cognitive system, follow the roadmap above. If you want a practical agent that works well now, **you're already there** - the current architecture is solid!

---

## Key Files Analyzed

```
smolclaw/tools/smolhand/runtime.py          # Smolhand implementation
smolclaw/agent/interactions/planner/        # Planner
smolclaw/agent/interactions/runloop/        # Runloop
smolclaw/agent/entities/runtime/            # State entities
smolclaw/agent/repositories/                # Persistence
smolclaw/agent/entities/chronicle/          # Event-like records
```
