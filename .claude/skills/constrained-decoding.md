# Skill: Constrained Decoding

Make outputs that code will parse (agent-to-agent handoffs, tool calls, DB writes) structurally valid by construction, not by asking politely in the prompt.

## Steps
1. Classify the output: if code parses it, apply this skill; if only a human reads it, free text is fine.
2. Define the contract first: write the JSON Schema (or enum list, or grammar) before writing the prompt.
3. Separate reasoning from answer: free-text reasoning first (a `reasoning` field or an earlier turn), then a `final_answer` matching the schema. Constrain only the final part.
4. Enforce, strongest first: (a) provider-native structured output or a forced tool call with the schema; (b) a constrained-decoding library or grammar backend for self-hosted models; (c) last resort, schema validation at the consumer with at most 2 retries, then fail loudly.
5. Validate at the receiving side anyway; on failure reject and report, never silently repair.

## Notes
- Mechanism: tokens that would break the schema get their logits masked before sampling, so invalid output is impossible rather than merely unlikely.
- Inside this project's Claude Code subagent chains there is no decoding layer we control. An explicit schema in the persona prompt (as the Pipeline agents do with `=== FILE ===` blocks) plus consumer-side validation is a prompt-level contract, not a guarantee. Say so explicitly.
- Before recommending a specific provider feature, check current API docs (claude-api skill).
