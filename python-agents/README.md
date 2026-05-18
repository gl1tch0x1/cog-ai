# Python Agents

LLM-powered security agents for SecAgents.

## Agents

| Agent | Role | Description |
|-------|------|-------------|
| Supervisor | Coordinator | Approves phase transitions, monitors health |
| Planner | Planning | Decomposes objectives into task plans |
| Recon | Discovery | Dispatches to Go recon services |
| WebSecurity | Testing | XSS, SQLi, SSRF, LFI, RCE, SSTI |
| APISecurity | Testing | BOLA, mass assignment, JWT, rate limiting |
| Validator | Validation | Replays PoCs, confirms findings |
| Report | Reporting | Generates Markdown/HTML/PDF/JSON reports |

## Structure

```
secagents/
├── agents/       # Agent implementations
├── prompts/      # System prompts per agent
├── evaluators/   # Output quality evaluation
└── workflows/    # Workflow definitions
```

## Usage

```python
from secagents import PlannerAgent

agent = PlannerAgent()
output = await agent.execute({
    "objective": "Find vulnerabilities",
    "scope": {"target": "example.com"}
})
print(output.result["phases"])
```
