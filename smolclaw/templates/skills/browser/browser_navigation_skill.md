# Browser Navigation Skill Template

Use structured browser operations over visual guessing.

## Priorities

1. Read the current URL and page state.
2. Prefer direct URL transitions when target links are known.
3. Use DOM and link extraction before brute-force clicking.
4. If the current tab is dead, recover by switching to another live tab.
5. Return concise, structured outputs (JSON when requested).

## Safety

- Do not perform irreversible external actions without explicit user confirmation.
- Stop and report if authentication, payment, or other sensitive actions are required.
