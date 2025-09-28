# iteration 1

Removing all the tables in the registry, in favor of the ones which the agent
will likely need, affects correctness. It creates correct SQL more often but the
results are considerably worse.

I assume this is because:

- A shorter prompt helps the agent focus on creating correct SQL (no registry
  noise, only subset which it may need, better semantic JSON generation)

- The agent may misjudge which tables it'll need. It misses context, making up
  tables in next steps when it doesn't have what it needs because it has been
  mistakenly filtered out in a previous step.

- The format of each entry in the registry may be sub-optimal. It may break the
  flow of the prompt and affect performance negatively. Headings/subheadings in
  markdown, or separators, or the language used.

I onserve that the retry loop works for invalid columns, effectively getting it
right at the second try. This is a great improvement over i0, so a shorter
prompt avoids parts drowning in the context.

The agent encounters a lot of invalid relationships when converting from the
semantic JSON to the SQL query. The retry loop doesn't help for invalid joins.
This means we need better context when this happens (like injecting the
available join paths instead).

We probably need a RetryTranslation, event to not discard the natural language
-> semantic work. If this inner loop gets exhausted N times, we kick a
RetrySemantic event, which means each workflow has 15 oportunities. WIP.
