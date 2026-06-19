# Artic Example Prompts

```text
@artic init
```

```text
@artic init quick
Product: AI meeting assistant for Korean startups.
Audience: startup operators and sales teams.
Goal: demo requests.
Vibe: clean SaaS, Toss-like clarity, trustworthy, mobile-first.
References: Linear for clarity, Shopify Polaris for trust/forms, Material for token discipline.
```

```text
@artic start
```

Expected public workflow: the agent writes `.artic/strategy.json` and `docs/artic-strategy.md`, then runs the compiler. If you invoke the raw compiler and strategy is missing, it writes `.artic/strategy-prompt.md` and exits non-zero so the agent can provide design direction.
