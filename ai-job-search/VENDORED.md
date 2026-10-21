# Vendored copy

This folder is a vendored copy of [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)
(MIT License, see `LICENSE`), copied at upstream commit `e16acee3abdaae57f8026789338a3c6eebf4608b`.

It is self-contained and is not imported by the InternPilot backend or frontend.
Run Claude Code from inside this folder so its `.claude/` commands, skills and agents
(and their root-relative paths) resolve correctly:

```bash
cd ai-job-search
python tools/install_portal_clis.py   # needs Bun
claude                                # then /setup, /scrape, /apply <url>, ...
```

To update, re-copy the upstream repo over this folder (excluding `.git`) and bump the commit above.
Personal data written by `/setup` and `/apply` is covered by this folder's own `.gitignore`
only partially (profile files under `.claude/skills/job-application-assistant/` and `CLAUDE.md`
are tracked) - review `git status` before committing.
