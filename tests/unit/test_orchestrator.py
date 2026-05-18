"""Unit tests for orchestrator.py implementation."""

import pytest
from secagents.core.orchestrator import (
    Orchestrator,
    Intent,
    Task,
    TaskState,
    ExecutionGraph,
    RetryConfig,
    CircuitBreakerState,
)


class TestIntentClassification:
    """Tests for intent classification."""

    def test_classify_scan_intent(self):
        """Test SCAN intent classification."""
        orch = Orchestrator()
        assert orch.classify_intent("scan the target") == Intent.SCAN
        assert orch.classify_intent("exploit vulnerabilities") == Intent.SCAN
        assert orch.classify_intent("find security issues") == Intent.SCAN

    def test_classify_recon_intent(self):
        """Test RECON intent classification."""
        orch = Orchestrator()
        assert orch.classify_intent("enumerate subdomains") == Intent.RECON
        assert orch.classify_intent("discover endpoints") == Intent.RECON

    def test_classify_validate_intent(self):
        """Test VALIDATE intent classification."""
        orch = Orchestrator()
        assert orch.classify_intent("validate findings") == Intent.VALIDATE
        assert orch.classify_intent("confirm vulnerabilities") == Intent.VALIDATE

    def test_classify_report_intent(self):
        """Test REPORT intent classification."""
        orch = Orchestrator()
        assert orch.classify_intent("generate report") == Intent.REPORT
        assert orch.classify_intent("export findings") == Intent.REPORT

    def test_classify_plan_intent(self):
        """Test PLAN intent classification."""
        orch = Orchestrator()
        assert orch.classify_intent("plan the attack") == Intent.PLAN
        assert orch.classify_intent("decompose strategy") == Intent.PLAN

    def test_classify_query_intent(self):
        """Test QUERY intent classification (default)."""
        orch = Orchestrator()
        assert orch.classify_intent("what time is it") == Intent.QUERY
        assert orch.classify_intent("hello") == Intent.QUERY


class TestIntentDecomposition:
    """Tests for intent decomposition."""

    def test_decompose_scan_creates_four_tasks(self):
        """Test that SCAN intent creates 4-task pipeline."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.SCAN, {"target": "example.com"})
        assert len(graph.tasks) == 4
        assert graph.root_intent == Intent.SCAN

    def test_scan_creates_dependency_chain(self):
        """Test SCAN creates proper dependency chain."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.SCAN, {"target": "example.com"})
        
        # First task has no dependencies
        assert len(graph.tasks[0].depends_on) == 0
        # Each subsequent task depends on previous
        assert graph.tasks[1].depends_on == [graph.tasks[0].id]
        assert graph.tasks[2].depends_on == [graph.tasks[1].id]
        assert graph.tasks[3].depends_on == [graph.tasks[2].id]

    def test_decompose_recon_creates_one_task(self):
        """Test RECON intent creates single task."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.RECON, {"target": "example.com"})
        assert len(graph.tasks) == 1
        assert graph.tasks[0].agent == "recon"

    def test_decompose_validate_creates_one_task(self):
        """Test VALIDATE intent creates single task."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.VALIDATE, {"target": "example.com"})
        assert len(graph.tasks) == 1
        assert graph.tasks[0].agent == "validator"

    def test_decompose_report_creates_one_task(self):
        """Test REPORT intent creates single task."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.REPORT, {"target": "example.com"})
        assert len(graph.tasks) == 1
        assert graph.tasks[0].agent == "report"

    def test_decompose_plan_creates_one_task(self):
        """Test PLAN intent creates single task."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.PLAN, {"target": "example.com"})
        assert len(graph.tasks) == 1
        assert graph.tasks[0].agent == "planner"

    def test_decompose_query_creates_one_task(self):
        """Test QUERY intent creates single supervisor task."""
        orch = Orchestrator()
        graph = orch.decompose_intent(Intent.QUERY, {"target": "example.com"})
        assert len(graph.tasks) == 1
        assert graph.tasks[0].agent == "supervisor"


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    def test_circuit_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreakerState()
        assert not cb.is_open

    def test_circuit_opens_after_five_failures(self):
        """Test circuit opens after 5 failures."""
        cb = CircuitBreakerState()
        for _ in range(5):
            cb.record_failure()
        assert cb.is_open

    def test_circuit_closes_after_three_successes(self):
        """Test circuit closes after 3 consecutive successes."""
        cb = CircuitBreakerState()
        # Trip the circuit
        for _ in range(5):
            cb.record_failure()
        assert cb.is_open
        
        # Reset manually for testing
        cb.open_until = 0
        
        # Record successes
        for _ in range(3):
            cb.record_success()
        
        # Circuit should be closed (failures reset)
        assert cb.failures == 0
        assert cb.is_open is False

    def test_failure_resets_success_counter(self):
        """Test that a failure resets the success counter."""
        cb = CircuitBreakerState()
        cb.record_success()
        cb.record_success()
        assert cb.consecutive_successes == 2
        
        cb.record_failure()
        assert cb.consecutive_successes == 0


class TestExecutionGraph:
    """Tests for ExecutionGraph."""

    def test_ready_tasks_includes_root_with_no_deps(self):
        """Test ready_tasks includes root tasks with no dependencies."""
        graph = ExecutionGraph()
        t1 = Task(agent="agent1")
        graph.tasks = [t1]
        
        ready = graph.ready_tasks
        assert len(ready) == 1
        assert ready[0].id == t1.id

    def test_ready_tasks_excludes_pending_with_deps(self):
        """Test ready_tasks excludes pending tasks with unsatisfied dependencies."""
        graph = ExecutionGraph()
        t1 = Task(agent="agent1")
        t2 = Task(agent="agent2", depends_on=[t1.id])
        graph.tasks = [t1, t2]
        
        ready = graph.ready_tasks
        assert len(ready) == 1
        assert ready[0].id == t1.id

    def test_ready_tasks_unlocks_after_dependency_done(self):
        """Test ready_tasks includes task after dependency completes."""
        graph = ExecutionGraph()
        t1 = Task(agent="agent1")
        t2 = Task(agent="agent2", depends_on=[t1.id])
        graph.tasks = [t1, t2]
        
        # Mark t1 as done
        t1.state = TaskState.DONE
        
        ready = graph.ready_tasks
        assert len(ready) == 1
        assert ready[0].id == t2.id

    def test_is_complete_false_when_pending(self):
        """Test is_complete is False when tasks are pending."""
        graph = ExecutionGraph()
        t1 = Task(agent="agent1", state=TaskState.PENDING)
        graph.tasks = [t1]
        assert not graph.is_complete

    def test_is_complete_true_when_all_done_or_failed(self):
        """Test is_complete is True when all tasks are done or failed."""
        graph = ExecutionGraph()
        t1 = Task(agent="agent1", state=TaskState.DONE)
        t2 = Task(agent="agent2", state=TaskState.FAILED)
        graph.tasks = [t1, t2]
        assert graph.is_complete


class TestAggregateResults:
    """Tests for result aggregation."""

    @pytest.mark.asyncio
    async def test_aggregates_done_tasks(self):
        """Test aggregation includes done task outputs."""
        orch = Orchestrator()
        graph = ExecutionGraph()
        
        t1 = Task(agent="agent1", output={"result": "data1"})
        t1.state = TaskState.DONE
        graph.tasks = [t1]
        
        results = await orch.aggregate_results(graph)
        assert "agent1" in results
        assert results["agent1"] == {"result": "data1"}

    @pytest.mark.asyncio
    async def test_aggregation_includes_metadata(self):
        """Test aggregation includes metadata."""
        orch = Orchestrator()
        graph = ExecutionGraph(root_intent=Intent.SCAN)
        
        t1 = Task(agent="agent1", output={"result": "data1"})
        t1.state = TaskState.DONE
        graph.tasks = [t1]
        
        results = await orch.aggregate_results(graph)
        assert "_metadata" in results
        assert results["_metadata"]["completed"] == 1
        assert results["_metadata"]["root_intent"] == "scan"

    @pytest.mark.asyncio
    async def test_aggregation_tracks_failures(self):
        """Test aggregation tracks failed tasks."""
        orch = Orchestrator()
        graph = ExecutionGraph()
        
        t1 = Task(agent="agent1", output={"error": "failed"})
        t1.state = TaskState.FAILED
        graph.tasks = [t1]
        
        results = await orch.aggregate_results(graph)
        assert results["_metadata"]["failed"] == 1
        assert len(results["_metadata"]["errors"]) == 1


class TestRouteTask:
    """Tests for task routing."""

    @pytest.mark.asyncio
    async def test_routes_to_registered_agent(self):
        """Test task is routed to registered agent."""
        orch = Orchestrator()
        
        async def mock_agent(action, input_data):
            return {"output": "test"}
        
        orch.register_agent("test_agent", mock_agent)
        task = Task(agent="test_agent")
        
        executor = await orch.route_task(task)
        assert executor == mock_agent

    @pytest.mark.asyncio
    async def test_raises_error_for_missing_agent(self):
        """Test error is raised for non-existent agent."""
        orch = Orchestrator()
        task = Task(agent="nonexistent")
        
        with pytest.raises(ValueError):
            await orch.route_task(task)

    @pytest.mark.asyncio
    async def test_rejects_when_circuit_open(self):
        """Test routing is rejected when circuit is open."""
        orch = Orchestrator()
        
        async def mock_agent(action, input_data):
            return {"output": "test"}
        
        orch.register_agent("test_agent", mock_agent)
        
        # Open circuit
        cb = orch._circuit_breakers["test_agent"]
        for _ in range(5):
            cb.record_failure()
        
        task = Task(agent="test_agent")
        
        with pytest.raises(RuntimeError):
            await orch.route_task(task)


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        orch = Orchestrator()
        config = orch._retry_config
        
        assert config.max_retries == 3
        assert config.initial_backoff == 1.0
        assert config.backoff_multiplier == 2.0

    def test_custom_retry_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(max_retries=5, initial_backoff=2.0)
        orch = Orchestrator(retry_config=config)
        
        assert orch._retry_config.max_retries == 5
        assert orch._retry_config.initial_backoff == 2.0


class TestEventHandling:
    """Tests for event handling."""

    @pytest.mark.asyncio
    async def test_events_emitted_on_action(self):
        """Test events are emitted during orchestration."""
        orch = Orchestrator()
        events = []
        
        def handler(data):
            events.append(data)
        
        orch.on_event("test_event", handler)
        await orch._emit("test_event", {"key": "value"})
        
        assert len(events) == 1
        assert events[0]["key"] == "value"

    @pytest.mark.asyncio
    async def test_async_event_handler(self):
        """Test async event handlers work."""
        orch = Orchestrator()
        events = []
        
        async def async_handler(data):
            events.append(data)
        
        orch.on_event("test_event", async_handler)
        await orch._emit("test_event", {"key": "value"})
        
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_exception_in_handler_doesnt_break_emit(self):
        """Test exceptions in handlers don't break emit."""
        orch = Orchestrator()
        events = []
        
        def bad_handler(data):
            raise ValueError("handler error")
        
        def good_handler(data):
            events.append(data)
        
        orch.on_event("test_event", bad_handler)
        orch.on_event("test_event", good_handler)
        
        # Should not raise
        await orch._emit("test_event", {"key": "value"})
        
        # Good handler should still be called
        assert len(events) == 1


@pytest.mark.asyncio
async def test_execute_graph_with_no_tasks():
    """Test execute_graph with empty graph."""
    orch = Orchestrator()
    graph = ExecutionGraph()
    
    results = await orch.execute_graph(graph)
    assert results["_metadata"]["total_tasks"] == 0


@pytest.mark.asyncio
async def test_execute_graph_single_task():
    """Test execute_graph with single independent task."""
    orch = Orchestrator()
    
    async def mock_executor(action, input_data):
        return {"result": "success"}
    
    orch.register_agent("test_agent", mock_executor)
    
    graph = ExecutionGraph()
    task = Task(agent="test_agent", action="test")
    graph.tasks = [task]
    
    results = await orch.execute_graph(graph)
    assert results["_metadata"]["completed"] == 1
    assert "test_agent" in results


@pytest.mark.asyncio
async def test_execute_respects_dependencies():
    """Test execution respects task dependencies."""
    orch = Orchestrator()
    
    execution_order = []
    
    async def executor1(action, input_data):
        execution_order.append("task1")
        return {"result": "data1"}
    
    async def executor2(action, input_data):
        execution_order.append("task2")
        return {"result": "data2"}
    
    orch.register_agent("agent1", executor1)
    orch.register_agent("agent2", executor2)
    
    graph = ExecutionGraph()
    t1 = Task(agent="agent1", action="action1")
    t2 = Task(agent="agent2", action="action2", depends_on=[t1.id])
    graph.tasks = [t1, t2]
    
    await orch.execute_graph(graph)
    
    # Task 1 must execute before task 2
    assert execution_order.index("task1") < execution_order.index("task2")
