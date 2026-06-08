# Agent guidelines

Guidance for AI agents (Claude Code and others) working in this repository.

## Git

- **Never switch branches.** Do not run `git checkout <branch>`, `git switch`, or
  otherwise change the checked-out branch — and do not create-and-switch to a new
  branch — unless the user **explicitly** asks for it in that request. Work on whatever
  branch is currently checked out. If you believe a branch change is needed, stop and
  ask first.
- Commit or push only when the user asks.

## Workflow

- The `Makefile` is the canonical entry point: `make test` (lint + tests),
  `make lint`, `make generate`, `make fix`. See `CONTRIBUTING.md`.
- After editing `schema.yaml` or any `mappings/<platform>.yaml`, run `make generate`
  before `make lint`.
