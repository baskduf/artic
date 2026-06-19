# Contributing

Thanks for improving Artic.

Before opening a PR:

1. Keep `skills/artic/` and plugin skill copies in sync.
2. Keep all README translations structurally synchronized.
3. Run:

```bash
python3 -m pytest -q
python3 skills/artic/scripts/scaffold_artic_files.py --root /tmp/artic-smoke
python3 skills/artic/scripts/validate_artic_outputs.py --root /tmp/artic-smoke
```

Do not add references that encourage exact brand cloning. Artic extracts reusable design principles only.
