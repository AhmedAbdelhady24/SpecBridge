# Output contract

Return only one JSON Artifact, with title, purpose, scope, non_goals, requirements, stories, edge_cases, dependencies, risks, success_metrics and open_questions. Follow the caller-supplied JSON Schema exactly; do not add prose fences or extra fields.

Every structured statement has text, source_ids and kind. Requirements add id; stories add id, requirement_ids and a nonempty acceptance_criteria list. Open questions are plain text. Keep provisional IDs unique and ensure every story links to a requirement in the same response. Recommendations can cite the motivating idea without claiming that the idea establishes the recommendation as fact.

The purpose gives the intended outcome in context; it is not proof of business value. Non-goals describe proposed boundaries. Success metrics propose observable checks without inventing approved numerical targets. Questions must identify consequential unresolved choices, including audience, scope or acceptance decisions when absent from evidence. Owners and deadlines remain unresolved unless explicitly present in a selected source.
