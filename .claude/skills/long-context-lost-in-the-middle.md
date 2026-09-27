# Skill: Long Context Placement

Structure a long prompt (multi-document QA, RAG, large agent handoff) so critical facts are not buried in the middle. Basis: Liu et al. 2023, "Lost in the Middle": models tend to use information at the start and end of a long context better than the middle. Treat this as a heuristic to test on the actual model, not a guarantee.

Use when a prompt is built from many chunks, documents or tool results. Skip for short single-document inputs.

## Steps
1. Gather: the question, the chunks (id, text, relevance score if available) and the token budget. Ask only for what is missing.
2. Rank chunks by relevance to the question.
3. Split: the top ~5-8 are high importance, the rest are supporting.
4. Lay out three sections: A (start) full high-importance chunks; B (middle) short summaries of supporting chunks; C (end) a brief recap of the critical facts, with the question restated last.
5. Fit the budget (about 1.3 tokens per word): drop the lowest-ranked material from B first and tell the user what was cut.
6. Instruct the model that all sections matter, and to cite chunk ids it used.
7. Optional evaluation: build three variants with the key fact in A, B and C, and compare answers to measure the position effect.

## Multi-agent use
For handoff prompts between agents: put the task and hard constraints first, restate them last, and keep bulky logs in the middle or reference them by path.
