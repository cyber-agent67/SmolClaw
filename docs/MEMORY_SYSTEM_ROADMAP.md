# Token-Efficient Memory System Roadmap

## Executive Summary

**Problem:** Naive memory injection dumps all past experiences into every LLM call, costing 100K+ tokens per run.

**Solution:** Tiered, compressed, semantically-searched memory that reduces token usage by 80-95% while improving recall quality.

**Timeline:** 4 weeks (phased implementation)

**ROI:** 50-100x token reduction → 79% cost savings per agent run

---

## Current State Analysis

### Before Optimization

```
Agent has 500 past experiences
Each experience = ~200 tokens
Total memory dump = 100,000 tokens per call

┌─────────────────────────────────────────┐
│ System Prompt          2,000 tokens     │
│ Tool Definitions       3,000 tokens     │
│ ALL 500 Experiences  100,000 tokens  ← 💀│
│ Page State             8,000 tokens     │
│ User Prompt            2,000 tokens     │
│ Response Reserve       4,000 tokens     │
├─────────────────────────────────────────┤
│ TOTAL                119,000 tokens     │
│ STATUS:              OVERFLOW ❌         │
│ COST PER RUN (GPT-4o): ~$5.00           │
└─────────────────────────────────────────┘
```

### After Optimization

```
Agent has 500 past experiences
Retrieves 3 relevant ones
Each compressed to ~40 tokens
Total memory injection = 2,000 tokens per call

┌─────────────────────────────────────────┐
│ System Prompt          2,000 tokens     │
│ Tool Definitions       3,000 tokens     │
│ HOT Memory (3 recent)  1,200 tokens  ← ✅│
│ WARM Memory (5 relevant)  800 tokens ← ✅│
│ COLD Summary             200 tokens  ← ✅│
│ Page State             8,000 tokens     │
│ User Prompt            2,000 tokens     │
│ Response Reserve       4,000 tokens     │
├─────────────────────────────────────────┤
│ TOTAL                 21,200 tokens     │
│ STATUS:              OPTIMAL ✅          │
│ SAVINGS:             82% fewer tokens   │
│ COST PER RUN (GPT-4o): ~$1.05           │
└─────────────────────────────────────────┘
```

---

## Architecture Overview

### New EIM Structure

```
smolclaw/agent/
│
├── entities/
│   ├── ... (existing entities)
│   ├── TokenBudget.py              # Controls token allocation
│   ├── CompressedMemory.py         # Token-efficient memory entry
│   ├── MemoryQuery.py              # Search query entity
│   └── MemorySearchResult.py       # Search results entity
│
├── interactions/
│   ├── ... (existing interactions)
│   │
│   ├── memory_optimization/        # NEW
│   │   ├── CompressExperience.py   # 5x compression
│   │   ├── InjectMemory.py         # Main injection point
│   │   ├── BudgetTokens.py         # Calculate available tokens
│   │   └── SummarizeHistory.py     # Progressive summarization
│   │
│   └── embedding/                  # NEW (Phase 2)
│       ├── GenerateEmbedding.py    # Local embeddings (free)
│       ├── ComputeSimilarity.py    # Cosine similarity (free)
│       └── SemanticSearch.py       # Semantic retrieval
│
├── repositories/
│   ├── ... (existing repositories)
│   └── MemoryIndexRepository.py    # Embedding index persistence
│
└── config/
    ├── ... (existing configs)
    └── MemoryConfig.py             # Memory system configuration
```

---

## Implementation Phases

### Phase 1: Quick Wins (Week 1) 🎯

**Goal:** 50-80% token reduction with minimal complexity

**Files to Create:** 5
**Lines of Code:** ~200
**New Dependencies:** None
**Time Required:** 4-6 hours

#### Deliverables

| File | Purpose | Priority |
|------|---------|----------|
| `config/MemoryConfig.py` | Configuration for token limits | ⭐⭐⭐ |
| `entities/TokenBudget.py` | Token budget calculation | ⭐⭐⭐ |
| `entities/CompressedMemory.py` | Compressed memory entity | ⭐⭐⭐ |
| `interactions/memory_optimization/CompressExperience.py` | 5x compression | ⭐⭐⭐ |
| `interactions/memory_optimization/InjectMemory.py` | Main injection | ⭐⭐⭐ |

#### Implementation Steps

**Step 1.1: Create MemoryConfig.py** (30 min)
```python
# smolclaw/agent/config/MemoryConfig.py
class MemoryConfig:
    def __init__(self):
        # Token limits
        self.total_context_window = 128000
        self.max_memory_tokens = 8000
        self.max_hot_tokens = 4000
        self.max_warm_tokens = 3000
        self.max_cold_tokens = 1000
        
        # Compression
        self.approx_chars_per_token = 4
        self.compress_after_n_experiences = 10
```

**Step 1.2: Create TokenBudget.py** (30 min)
```python
# smolclaw/agent/entities/TokenBudget.py
class TokenBudget:
    def __init__(self):
        self.total_context_window = 128000
        self.reserved_for_system_prompt = 2000
        self.reserved_for_tools = 3000
        self.reserved_for_response = 4000
        self.reserved_for_page_state = 8000
        self.available_for_memory = 0
    
    def calculate_available(self) -> int:
        used = (
            self.reserved_for_system_prompt +
            self.reserved_for_tools +
            self.reserved_for_response +
            self.reserved_for_page_state
        )
        self.available_for_memory = max(
            self.total_context_window - used, 0
        )
        return self.available_for_memory
```

**Step 1.3: Create CompressExperience.py** (1 hour)
```python
# smolclaw/agent/interactions/memory_optimization/CompressExperience.py
from entities.Experience import Experience
from entities.CompressedMemory import CompressedMemory
from config.MemoryConfig import MemoryConfig

class CompressExperience:
    @staticmethod
    def execute(experience: Experience, config: MemoryConfig = None) -> CompressedMemory:
        """
        Compress experience: 200 tokens → ~40 tokens
        
        Uses extractive compression — no LLM call needed.
        """
        if config is None:
            config = MemoryConfig()
        
        compressed = CompressedMemory()
        compressed.original_task = experience.task
        compressed.timestamp = experience.timestamp
        
        # Calculate original token count
        original_text = f"{experience.task} {experience.context} {experience.result}"
        compressed.original_token_count = len(original_text) // config.approx_chars_per_token
        
        # Extract key information only
        task_short = experience.task.split('.')[0].strip()[:100]
        outcome = "✓" if experience.success else "✗"
        result_short = str(experience.result)[:80] if experience.result else ""
        
        # Build compressed summary
        compressed.compressed_summary = f"{outcome} {task_short} → {result_short}"
        
        # Calculate compression stats
        compressed.compressed_token_count = len(compressed.compressed_summary) // config.approx_chars_per_token
        
        if compressed.original_token_count > 0:
            compressed.compression_ratio = compressed.compressed_token_count / compressed.original_token_count
        
        return compressed
```

**Step 1.4: Create InjectMemory.py** (2 hours)
```python
# smolclaw/agent/interactions/memory_optimization/InjectMemory.py
from typing import List
from entities.Experience import Experience
from entities.TokenBudget import TokenBudget
from config.MemoryConfig import MemoryConfig
from interactions.memory_optimization.CompressExperience import CompressExperience

class InjectMemory:
    @staticmethod
    def execute(
        experiences: List[Experience],
        current_goal: str = "",
        config: MemoryConfig = None,
        max_tokens: int = 2000
    ) -> str:
        """
        THE TOKEN SAVER.
        
        Instead of dumping all memory (100K+ tokens),
        this produces a surgically precise memory injection
        typically under 2000 tokens.
        
        Call this before every LLM invocation.
        """
        if config is None:
            config = MemoryConfig()
        
        # 1. BUDGET
        budget = TokenBudget()
        budget.calculate_available()
        actual_budget = min(budget.available_for_memory, max_tokens)
        
        # 2. SELECT (recent + relevant)
        # Take last N experiences that fit budget
        selected = []
        tokens_used = 0
        
        for exp in reversed(experiences[-20:]):  # Last 20 experiences
            compressed = CompressExperience.execute(exp, config)
            entry_tokens = compressed.compressed_token_count
            
            if tokens_used + entry_tokens > actual_budget:
                break
            
            selected.append(compressed)
            tokens_used += entry_tokens
        
        # 3. FORMAT
        sections = []
        
        if selected:
            sections.append("## Recent Experiences")
            for comp in selected[-5:]:  # Last 5
                sections.append(f"- {comp.compressed_summary}")
        
        result = "\n".join(sections)
        
        # Add token usage footer
        if result:
            result += f"\n[Memory: ~{tokens_used} tokens]"
        
        return result
```

**Step 1.5: Update RunAgent.py** (1 hour)
```python
# smolclaw/agent/interactions/agent/Run.py

# ADD at top:
from interactions.memory_optimization.InjectMemory import InjectMemory

# MODIFY execute() method:
@staticmethod
def execute(agent, prompt, start_url, experience_memory, navigation_stack):
    # ... existing code ...
    
    # TOKEN-OPTIMIZED MEMORY INJECTION
    memory_injection = InjectMemory.execute(
        experiences=experience_memory.experiences,
        current_goal=prompt,
        max_tokens=2000
    )
    
    # Build enhanced prompt WITH memory
    if memory_injection:
        enhanced_prompt = f"{memory_injection}\n\n---\n\n{prompt}"
    else:
        enhanced_prompt = prompt
    
    # Execute with enhanced prompt
    result = agent.code_agent.run(enhanced_prompt)
    
    return result
```

#### Testing Checklist

- [ ] Create 10 test experiences
- [ ] Run CompressExperience on each
- [ ] Verify 5x compression ratio
- [ ] Run InjectMemory with 2000 token budget
- [ ] Verify output < 2000 tokens
- [ ] Integrate into RunAgent
- [ ] Test full agent run with memory injection

#### Expected Results

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Memory tokens | 10,000-100,000 | 1,000-2,000 | 80-95% |
| Cost per run | $5.00 | $1.05 | 79% |
| Latency | High | Low | 50% faster |
| Implementation | N/A | 6 hours | 1 day |

---

### Phase 2: Semantic Search (Week 2-3) 🔍

**Goal:** Retrieve relevant memories, not just recent ones

**Files to Create:** 6
**Lines of Code:** ~400
**New Dependencies:** `sentence-transformers` (100MB model)
**Time Required:** 2-3 days

#### Deliverables

| File | Purpose | Priority |
|------|---------|----------|
| `config/MemoryConfig.py` (update) | Add embedding config | ⭐⭐ |
| `entities/MemoryQuery.py` | Search query entity | ⭐⭐ |
| `entities/MemorySearchResult.py` | Search results entity | ⭐⭐ |
| `interactions/embedding/GenerateEmbedding.py` | Local embeddings | ⭐⭐⭐ |
| `interactions/embedding/ComputeSimilarity.py` | Cosine similarity | ⭐⭐⭐ |
| `interactions/memory_optimization/SemanticSearch.py` | Semantic retrieval | ⭐⭐⭐ |

#### Implementation Steps

**Step 2.1: Install Dependencies** (10 min)
```bash
pip install sentence-transformers
```

**Step 2.2: Create GenerateEmbedding.py** (2 hours)
```python
# smolclaw/agent/interactions/embedding/GenerateEmbedding.py
from typing import List, Optional
from config.MemoryConfig import MemoryConfig

class _EmbeddingModelSingleton:
    """Local embedding model — loaded once, no API cost"""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def is_loaded(self) -> bool:
        return self._model is not None
    
    def load(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {model_name}...")
            self._model = SentenceTransformer(model_name)
            print("Embedding model loaded.")
        except ImportError:
            print("sentence-transformers not installed. Using fallback.")
            self._model = "tfidf_fallback"
    
    def encode(self, text: str) -> List[float]:
        if self._model is None:
            self.load()
        
        if self._model == "tfidf_fallback":
            return _tfidf_fallback(text)
        
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

def _tfidf_fallback(text: str, dim: int = 384) -> List[float]:
    """Ultra-cheap fallback: hash-based embedding, zero API cost"""
    import hashlib
    
    embedding = [0.0] * dim
    words = text.lower().split()
    
    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        embedding[idx] += 1.0
    
    # Normalize
    magnitude = sum(x * x for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    
    return embedding

_singleton = _EmbeddingModelSingleton()

class GenerateEmbedding:
    @staticmethod
    def execute(text: str, config: MemoryConfig = None) -> List[float]:
        """
        Generates an embedding vector for text.
        Uses LOCAL model — zero API token cost.
        """
        if not _singleton.is_loaded:
            _singleton.load()
        
        return _singleton.encode(text)
```

**Step 2.3: Create ComputeSimilarity.py** (30 min)
```python
# smolclaw/agent/interactions/embedding/ComputeSimilarity.py
from typing import List

class ComputeSimilarity:
    @staticmethod
    def execute(embedding_a: List[float], embedding_b: List[float]) -> float:
        """
        Computes cosine similarity between two embeddings.
        Pure math — no API calls, no token cost.
        """
        if len(embedding_a) != len(embedding_b):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        magnitude_a = sum(a * a for a in embedding_a) ** 0.5
        magnitude_b = sum(b * b for b in embedding_b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
```

**Step 2.4: Create SemanticSearch.py** (3 hours)
```python
# smolclaw/agent/interactions/memory_optimization/SemanticSearch.py
from typing import List
from entities.MemoryQuery import MemoryQuery
from entities.MemorySearchResult import MemorySearchResult
from entities.CompressedMemory import CompressedMemory
from config.MemoryConfig import MemoryConfig
from interactions.embedding.GenerateEmbedding import GenerateEmbedding
from interactions.embedding.ComputeSimilarity import ComputeSimilarity

class SemanticSearch:
    @staticmethod
    def execute(
        query: MemoryQuery,
        compressed_memories: List[CompressedMemory],
        config: MemoryConfig = None
    ) -> MemorySearchResult:
        """
        Finds the most relevant memories using semantic similarity.
        
        Cost: ZERO LLM tokens
        - Embedding: local model
        - Similarity: pure math
        - Retrieval: array lookup
        """
        if config is None:
            config = MemoryConfig()
        
        result = MemorySearchResult()
        result.query_text = query.query_text
        
        if not compressed_memories:
            result.formatted_injection = ""
            return result
        
        # Embed the query (local model, free)
        query_embedding = GenerateEmbedding.execute(query.query_text, config)
        
        # Compute similarities (pure math, free)
        scored = []
        for memory in compressed_memories:
            # Embed memory text
            memory_embedding = GenerateEmbedding.execute(
                memory.compressed_summary, config
            )
            
            similarity = ComputeSimilarity.execute(
                query_embedding, memory_embedding
            )
            
            if similarity >= query.min_relevance:
                scored.append({
                    'memory': memory,
                    'similarity': similarity
                })
        
        # Sort by relevance
        scored.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Budget-aware selection
        tokens_used = 0
        selected = []
        
        for item in scored[:query.max_results]:
            memory = item['memory']
            entry_tokens = memory.compressed_token_count
            
            if tokens_used + entry_tokens > query.token_budget:
                break
            
            memory.relevance_score = item['similarity']
            selected.append(memory)
            tokens_used += entry_tokens
        
        result.results = selected
        result.total_tokens_used = tokens_used
        
        return result
```

#### Testing Checklist

- [ ] Install sentence-transformers
- [ ] Test GenerateEmbedding with sample text
- [ ] Verify embedding dimension (384)
- [ ] Test ComputeSimilarity with identical vectors (should be 1.0)
- [ ] Test SemanticSearch with 10 compressed memories
- [ ] Verify relevant memories ranked higher than random
- [ ] Measure embedding time (<100ms per query)
- [ ] Measure similarity time (<10ms per comparison)

#### Expected Results

| Metric | Phase 1 | Phase 2 | Improvement |
|--------|---------|---------|-------------|
| Retrieval | Recent only | Semantic | Better recall |
| Relevance | Low | High | 3x better |
| Token cost | 2,000 | 2,000 | Same |
| Latency | Fast | Fast | <100ms overhead |
| Implementation | 6 hours | 2-3 days | Worth it |

---

### Phase 3: Production Scale (Week 4) 🏭

**Goal:** Handle 1000+ experiences efficiently

**Files to Create:** 4
**Lines of Code:** ~300
**New Dependencies:** None (uses existing)
**Time Required:** 1-2 days

#### Deliverables

| File | Purpose | Priority |
|------|---------|----------|
| `repositories/MemoryIndexRepository.py` | Index persistence | ⭐⭐ |
| `interactions/memory_optimization/BuildIndex.py` | Build embedding index | ⭐⭐ |
| `interactions/memory_optimization/Deduplicate.py` | Remove duplicates | ⭐ |
| `interactions/memory_optimization/SummarizeHistory.py` | Progressive summary | ⭐⭐ |

#### When to Implement

- [ ] You have 100+ experiences stored
- [ ] Memory search is getting slow (>1 second)
- [ ] You notice duplicate memories
- [ ] Context window still overflowing

#### Implementation Priority: LOW

**Only implement Phase 3 if you actually need it.** Most agents won't reach 1000 experiences until they've been running for months.

---

## Decision Tree

```
Do you have < 50 experiences?
├─ YES → Implement Phase 1 ONLY
└─ NO → Continue ↓

Do you have < 500 experiences?
├─ YES → Implement Phase 1 + Phase 2
└─ NO → Continue ↓

Do you have > 1000 experiences?
├─ YES → Implement Phase 1 + 2 + 3
└─ NO → You're over-engineering, stop
```

---

## Cost-Benefit Analysis

### Phase 1 (Quick Wins)

**Cost:**
- 6 hours development time
- 0 new dependencies
- 200 lines of code

**Benefit:**
- 80% token reduction
- $4 savings per agent run
- Pays for itself in 2 agent runs

**ROI:** ⭐⭐⭐⭐⭐ (Implement immediately)

---

### Phase 2 (Semantic Search)

**Cost:**
- 2-3 days development time
- 100MB model download
- 400 lines of code

**Benefit:**
- 3x better memory recall
- Relevant memories, not just recent
- Still zero API token cost

**ROI:** ⭐⭐⭐⭐ (Implement when you have 50+ experiences)

---

### Phase 3 (Production Scale)

**Cost:**
- 1-2 days development time
- 300 lines of code
- Added complexity

**Benefit:**
- Handles 1000+ experiences
- Prevents index bloat
- Marginal improvement for most users

**ROI:** ⭐⭐ (Implement only if you actually need it)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_memory_compression.py
def test_compress_experience():
    exp = Experience(
        task="Find FDA registration requirements",
        context="Navigated to FDA website...",
        result="Found requirements page",
        success=True
    )
    
    compressed = CompressExperience.execute(exp)
    
    assert compressed.original_token_count > 100
    assert compressed.compressed_token_count < 50
    assert compressed.compression_ratio < 0.5
```

```python
# tests/test_memory_injection.py
def test_inject_memory_within_budget():
    experiences = [create_test_experience(i) for i in range(20)]
    
    injection = InjectMemory.execute(
        experiences=experiences,
        max_tokens=2000
    )
    
    tokens_used = len(injection) // 4
    assert tokens_used <= 2000
```

### Integration Tests

```python
# tests/test_memory_end_to_end.py
def test_full_agent_run_with_memory():
    # Run agent 10 times
    for i in range(10):
        result = run_agent_with_prompt(f"Test task {i}")
        
        # Verify memory injection
        assert memory_tokens_used < 2000
        assert compression_ratio < 0.5
```

### Performance Benchmarks

```python
# tests/benchmark_memory.py
def benchmark_memory_injection():
    experiences = [create_test_experience(i) for i in range(100)]
    
    start = time.time()
    injection = InjectMemory.execute(experiences, max_tokens=2000)
    elapsed = time.time() - start
    
    print(f"Memory injection: {elapsed*1000:.2f}ms")
    print(f"Tokens used: {len(injection)//4}")
    
    # Should be < 100ms for 100 experiences
    assert elapsed < 0.1
```

---

## Migration Guide

### From No Memory → Phase 1

**Before:**
```python
# Old approach: dump all experiences
prompt = f"Past experiences: {all_experiences}\n\nTask: {current_task}"
```

**After:**
```python
# New approach: token-optimized injection
from interactions.memory_optimization.InjectMemory import InjectMemory

memory_injection = InjectMemory.execute(
    experiences=experience_memory.experiences,
    current_goal=current_task,
    max_tokens=2000
)

prompt = f"{memory_injection}\n\n---\n\n{current_task}"
```

**Changes Required:**
- 1 file modified: `interactions/agent/Run.py`
- 3 files added: `CompressExperience.py`, `InjectMemory.py`, `MemoryConfig.py`
- 0 breaking changes

---

### From Phase 1 → Phase 2

**Before:**
```python
# Phase 1: Recent experiences only
memory_injection = InjectMemory.execute(
    experiences=experiences[-20:]  # Last 20
)
```

**After:**
```python
# Phase 2: Semantic search
from interactions.memory_optimization.SemanticSearch import SemanticSearch

query = MemoryQuery(
    query_text=current_goal,
    max_results=5,
    min_relevance=0.4,
    token_budget=2000
)

search_result = SemanticSearch.execute(
    query=query,
    compressed_memories=all_compressed_memories
)

memory_injection = format_search_result(search_result)
```

**Changes Required:**
- 4 files added: `GenerateEmbedding.py`, `ComputeSimilarity.py`, `SemanticSearch.py`, `MemoryQuery.py`
- 1 dependency: `sentence-transformers`
- Backward compatible: Phase 1 still works

---

## Success Metrics

### Week 1 (Phase 1 Complete)

- [ ] Memory tokens reduced by >50%
- [ ] Agent runs successfully with compressed memory
- [ ] No regression in task completion rate
- [ ] Token usage logs show 80% reduction

### Week 3 (Phase 2 Complete)

- [ ] Semantic search returns relevant memories
- [ ] Embedding generation <100ms per query
- [ ] Similarity computation <10ms per comparison
- [ ] Users report better agent memory recall

### Month 2 (Production)

- [ ] System handles 500+ experiences
- [ ] Memory injection <200ms total latency
- [ ] Cost per agent run reduced by 79%
- [ ] Zero context window overflows

---

## Risks & Mitigations

### Risk 1: Over-Engineering

**Symptom:** Implementing Phase 3 before having 100 experiences

**Mitigation:**
- Follow the decision tree
- Measure actual experience count
- Only optimize when you have data

### Risk 2: Embedding Model Size

**Symptom:** 100MB model download is too large for deployment

**Mitigation:**
- Use TF-IDF fallback (built-in)
- Use smaller model (`paraphrase-MiniLM-L3-v2`, 60MB)
- Cache embeddings on disk

### Risk 3: Compression Loses Information

**Symptom:** Agent can't recall important details

**Mitigation:**
- Keep raw experiences in storage
- Only compress for injection
- Adjust compression ratio in MemoryConfig

### Risk 4: Semantic Search Returns Irrelevant Memories

**Symptom:** Low relevance scores (<0.3)

**Mitigation:**
- Increase `min_relevance` threshold
- Improve compression to keep key details
- Add keyword filtering as fallback

---

## Future Enhancements (Post-Roadmap)

### Tiered Memory (L1/L2/L3 Cache)

Like CPU cache:
- L1 (Hot): Last 3 actions, full detail
- L2 (Warm): Semantically relevant, compressed
- L3 (Cold): Running summary, heavily compressed

**When:** After 1000+ experiences

---

### Memory Consolidation

Periodically merge similar experiences:
- Find clusters of similar memories
- Merge into single "meta-experience"
- Reduces index size by 50%

**When:** After 500+ experiences

---

### Forgetting Mechanism

Actively forget low-value memories:
- Evict memories with low relevance scores
- Evict memories older than 30 days
- Keep only high-signal experiences

**When:** When storage > 10GB

---

### Multi-Agent Memory Sharing

Share memories across agent instances:
- Central memory server
- Agents contribute experiences
- All agents benefit from collective learning

**When:** Running 10+ agent instances

---

## Getting Started Checklist

### Today (Phase 1 Start)

- [ ] Read this roadmap completely
- [ ] Create `config/MemoryConfig.py`
- [ ] Create `entities/TokenBudget.py`
- [ ] Test token budget calculation

### Tomorrow (Phase 1 Continue)

- [ ] Create `entities/CompressedMemory.py`
- [ ] Create `interactions/memory_optimization/CompressExperience.py`
- [ ] Test compression on 10 experiences
- [ ] Verify 5x compression ratio

### Day 3 (Phase 1 Complete)

- [ ] Create `interactions/memory_optimization/InjectMemory.py`
- [ ] Update `interactions/agent/Run.py` to use InjectMemory
- [ ] Run full agent test with memory injection
- [ ] Measure token savings (should be >50%)

### Week 2 (Phase 2 Start - Optional)

- [ ] Install `sentence-transformers`
- [ ] Create `interactions/embedding/GenerateEmbedding.py`
- [ ] Test embedding generation
- [ ] Verify embedding dimension (384)

### Week 3 (Phase 2 Complete - Optional)

- [ ] Create `interactions/embedding/ComputeSimilarity.py`
- [ ] Create `interactions/memory_optimization/SemanticSearch.py`
- [ ] Test semantic search with 50 experiences
- [ ] Verify relevant memories ranked higher

---

## Summary

### What to Implement

| Phase | When | Effort | ROI |
|-------|------|--------|-----|
| **Phase 1** | NOW | 6 hours | ⭐⭐⭐⭐⭐ |
| **Phase 2** | When 50+ experiences | 2-3 days | ⭐⭐⭐⭐ |
| **Phase 3** | When 1000+ experiences | 1-2 days | ⭐⭐ |

### Key Principles

1. **Measure first** - Don't optimize without data
2. **Compress at save time** - Not at query time
3. **Local embeddings** - Zero API cost
4. **Progressive summarization** - O(1) token cost
5. **Budget-aware** - Never exceed context window

### Expected Outcomes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Memory tokens | 100,000 | 2,000 | 98% reduction |
| Cost per run | $5.00 | $1.05 | 79% savings |
| Latency | High | Low | 50% faster |
| Recall quality | Poor | Excellent | 3x better |

---

## Questions?

This roadmap is designed to be **pragmatic, not perfect**. Start with Phase 1, measure results, and only proceed to Phase 2 if you actually need it.

**Most agents will never need Phase 3.**

**Contact:** Add questions to GitHub issues or discuss in SmolClaw community.

---

**Last Updated:** March 2026
**Version:** 1.0
**Status:** Ready for Implementation
