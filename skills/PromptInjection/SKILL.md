# Prompt Injection & LLM Security Skill

## Attack Vectors
- **Direct Injection**: System prompt override via user message.
- **Indirect Injection**: Poisoned data from external sources (web, files).
- **Encoding Attacks**: Base64, Hex, or Unicode smuggling.
- **Goal Hijacking**: Diverting the agent's intent to malicious tasks.

## Validation Gates
1. Can the LLM be made to ignore previous instructions?
2. Can it be forced to output sensitive config?
3. Can it be tricked into executing unauthorized tools?
