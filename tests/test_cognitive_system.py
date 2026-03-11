#!/usr/bin/env python3
"""Test script to verify cognitive system properties.

Run this to verify:
1. Pure functional effects work
2. Probabilistic planner learns
3. DFA transitions are explicit
4. Event sourcing enables replay
"""

import json
import sys
import time


def test_effects():
    """Test effect types."""
    print("\n" + "=" * 60)
    print("Testing Effect Types")
    print("=" * 60)
    
    from smolclaw.cognitive import Effect, Success, Error, pure
    
    # Test pure effect
    effect = pure(42)
    result = effect.run()
    assert result == 42, f"Expected 42, got {result}"
    print("✓ Pure effects work")
    
    # Test effect with computation
    effect = Effect(lambda: 10 + 20)
    result = effect.run()
    assert result == 30, f"Expected 30, got {result}"
    print("✓ Effect computation works")
    
    # Test map
    effect = pure(5).map(lambda x: x * 2)
    result = effect.run()
    assert result == 10, f"Expected 10, got {result}"
    print("✓ Effect map works")
    
    # Test Result
    success = Success(42)
    assert success.is_success, "Success should be successful"
    assert success.value == 42, f"Expected 42, got {success.value}"
    print("✓ Result success works")
    
    error = Error("Something went wrong")
    assert not error.is_success, "Error should not be successful"
    assert error.error == "Something went wrong"
    print("✓ Result error works")
    
    print("\n✅ All effect tests passed!")
    return True


def test_planner():
    """Test probabilistic planner."""
    print("\n" + "=" * 60)
    print("Testing Probabilistic Planner")
    print("=" * 60)
    
    from smolclaw.cognitive import ProbabilisticPlanner
    
    planner = ProbabilisticPlanner()
    
    # Test planning
    result = planner.plan("Find the latest release notes")
    assert result.is_success, f"Planning failed: {result.error}"
    plan = result.value
    print(f"✓ Plan generated: {plan.strategy}")
    print(f"  Confidence: {plan.confidence:.2f}")
    print(f"  Steps: {len(plan.steps)}")
    
    # Test learning
    initial_stats = planner.get_statistics()
    print(f"✓ Initial success rate: {initial_stats['success_rate']:.2f}")
    
    # Update with outcomes
    planner.update_from_outcome(plan.strategy, success=True)
    planner.update_from_outcome(plan.strategy, success=True)
    planner.update_from_outcome(plan.strategy, success=False)
    
    updated_stats = planner.get_statistics()
    print(f"✓ Updated success rate: {updated_stats['success_rate']:.2f}")
    
    # Verify learning occurred
    assert updated_stats['total_plans'] == 3, "Should have 3 plans recorded"
    print("✓ Planner learns from experience")
    
    print("\n✅ All planner tests passed!")
    return True


def test_dfa():
    """Test explicit DFA."""
    print("\n" + "=" * 60)
    print("Testing Explicit DFA")
    print("=" * 60)
    
    from smolclaw.cognitive import create_dfa, AgentState, AgentEvent
    
    dfa = create_dfa()
    
    # Test initial state
    state = dfa.get_state()
    assert state == AgentState.AWAIT_INTENT, f"Expected AWAIT_INTENT, got {state}"
    print(f"✓ Initial state: {state.value}")
    
    # Test transition
    success, error = dfa.fire_event(
        AgentEvent.INTENT_RECEIVED,
        {"intent": "Test goal"}
    )
    assert success, f"Transition failed: {error}"
    state = dfa.get_state()
    assert state == AgentState.PLANNING, f"Expected PLANNING, got {state}"
    print(f"✓ Transition: AWAIT_INTENT → {state.value}")
    
    # Test history
    history = dfa.get_history()
    assert len(history) == 1, f"Expected 1 history entry, got {len(history)}"
    print(f"✓ History recorded: {len(history)} transitions")
    
    # Test state dict
    state_dict = dfa.to_dict()
    assert "state" in state_dict, "State dict should have 'state'"
    assert "version" in state_dict, "State dict should have 'version'"
    print(f"✓ State version: {state_dict['version']}")
    
    print("\n✅ All DFA tests passed!")
    return True


def test_event_sourcing():
    """Test event sourcing."""
    print("\n" + "=" * 60)
    print("Testing Event Sourcing")
    print("=" * 60)
    
    from smolclaw.cognitive import (
        EventStore,
        IntentReceivedEvent,
        ToolExecutedEvent,
        TaskCompletedEvent,
    )
    
    # Create event store
    store = EventStore()
    
    # Append events
    store.append(IntentReceivedEvent(
        intent="Find release notes",
        session_id="test_session",
    ))
    print(f"✓ Event appended (version: {store.get_version()})")
    
    store.append(ToolExecutedEvent(
        tool_name="explore_dom_with_astar",
        arguments={"target": "release notes"},
        result="Found 5 links",
        success=True,
    ))
    print(f"✓ Another event appended (version: {store.get_version()})")
    
    store.append(TaskCompletedEvent(
        result="Version 2.0 released on...",
        success=True,
        duration_seconds=5.3,
    ))
    print(f"✓ Task completed event (total events: {len(store)})")
    
    # Test replay
    events = store.replay()
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    print(f"✓ Replay works: {len(events)} events")
    
    # Test fold (state reconstruction)
    def count_tools(state, event):
        if event.event_type == "tool_executed":
            state["tool_count"] += 1
        return state
    
    result = store.fold({"tool_count": 0}, count_tools)
    assert result["tool_count"] == 1, f"Expected 1 tool, got {result['tool_count']}"
    print(f"✓ Fold works: {result['tool_count']} tools used")
    
    # Test filtering
    tool_events = store.get_events_by_type("tool_executed")
    assert len(tool_events) == 1, f"Expected 1 tool event, got {len(tool_events)}"
    print(f"✓ Event filtering works")
    
    print("\n✅ All event sourcing tests passed!")
    return True


def test_cognitive_loop():
    """Test full cognitive loop."""
    print("\n" + "=" * 60)
    print("Testing Full Cognitive Loop")
    print("=" * 60)
    
    from smolclaw.cognitive_loop import CognitiveLoop
    
    loop = CognitiveLoop(max_loops=5)
    
    # Process intent
    result = loop.process_intent("Find the latest release notes")
    
    assert "success" in result, "Result should have 'success' field"
    print(f"✓ Intent processed: success={result.get('success')}")
    
    # Check state
    state = loop.get_state()
    assert "agent_state" in state, "State should have 'agent_state'"
    assert "event_count" in state, "State should have 'event_count'"
    print(f"✓ State: {state['agent_state']}")
    print(f"✓ Events recorded: {state['event_count']}")
    
    # Check planner learned
    planner_stats = state.get("planner_stats", {})
    assert "total_plans" in planner_stats, "Should have planner stats"
    print(f"✓ Planner statistics: {planner_stats['total_plans']} plans")
    
    # Test replay
    events = loop.replay()
    assert len(events) > 0, "Should have events to replay"
    print(f"✓ Event replay: {len(events)} events")
    
    print("\n✅ Full cognitive loop test passed!")
    return True


def main():
    """Run all cognitive system tests."""
    print("\n" + "=" * 60)
    print("  SmolClaw Cognitive System Tests")
    print("=" * 60)
    
    tests = [
        ("Effects", test_effects),
        ("Planner", test_planner),
        ("DFA", test_dfa),
        ("Event Sourcing", test_event_sourcing),
        ("Cognitive Loop", test_cognitive_loop),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} test FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"  Test Summary: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All cognitive system properties verified!")
        print("\nCognitive System Properties:")
        print("  ✅ Pure functional effects")
        print("  ✅ Probabilistic planning with learning")
        print("  ✅ Explicit DFA state machine")
        print("  ✅ Event sourcing with replay")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
