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

## Taxonomy & mapping conventions

See [`docs/taxonomy.md`](docs/taxonomy.md) before adding or editing modality codes or
platform mappings. Two rules that are easy to get wrong:

- **Relatedness is biomechanical, not nominal.** A shared name or shared equipment does
  not make two things the same modality. Same movement pattern → same modality
  (subdivide as a discipline). A circumstance that doesn't change the movement (indoor,
  virtual, assisted, roller, race) → modifier (`+`). Different movement → separate
  modality (hand cycling is NOT cycling; alpine skiing is NOT xc_skiing). Intensity and
  metabolic load are ignored.
- **`null` vs `generic` in mappings.** A platform's catch-all bucket → `generic`. A
  specific activity OST doesn't model → `null`. Never send a named activity to `generic`
  just because it's a vague workout.
