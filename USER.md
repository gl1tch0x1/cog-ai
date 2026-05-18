# USER.md — Dynamic User Profile

Evolves with each interaction. Updated by the orchestrator based on observed preferences and explicit user instructions.

## Profile

```yaml
handle: ""                    # User's preferred name or handle
role: analyst                 # analyst | pentester | bug_bounty_hunter | developer
experience_level: intermediate # beginner | intermediate | advanced | expert
preferred_output: markdown    # markdown | json | html | pdf
verbosity: normal             # quiet | normal | verbose | debug
```

## Preferences

```yaml
scan_preferences:
  default_threads: 10
  max_scan_depth: 3
  auto_validate: true         # Run validator automatically after scan
  auto_chain: true            # Run exploit chain correlation automatically
  include_low_severity: false # Include LOW findings in reports by default

report_preferences:
  format: markdown
  include_executive_summary: true
  include_poc_scripts: true
  include_remediation: true
  cvss_version: "3.1"

llm_preferences:
  preferred_provider: ""      # blank = auto-route
  cost_priority: balanced     # cheap | balanced | performance
  temperature: 0.1
```

## Scope History

```yaml
approved_scopes:
  - domain: ""
    added: ""
    workflow_count: 0
  
  # Add entries here as user approves new targets
```

## Session History

```yaml
recent_sessions:
  - session_id: ""
    target: ""
    date: ""
    findings_count: 0
    severity_breakdown:
      critical: 0
      high: 0
      medium: 0
      low: 0
```

## Notification Preferences

```yaml
notifications:
  slack_enabled: false
  jira_enabled: false
  email_enabled: false
  alert_on: [critical, high]   # severity levels that trigger alerts
```

## Learned Preferences

The orchestrator updates this section automatically based on observed behavior:

```yaml
learned:
  - observation: ""
    timestamp: ""
    applied: true
```

## Instructions

User-defined overrides (highest priority — always followed):

```yaml
instructions: []
# Example:
# - "Always include CVSS vector strings in findings"
# - "Skip LOW severity findings"
# - "Use Groq for all classification tasks"
```
