# Plan 026: Publish a site to open-sport-taxonomy.sweatstack.no (Cloudflare Pages)

> **Status: proposed.** First iteration ships **only the translation explorer**; the setup
> is deliberately a plain static directory so docs pages drop in later with no rework.

## Goal

Serve the browser explorer at **`https://open-sport-taxonomy.sweatstack.no`**, deployed
**locally** via `make deploy`.

## The simplification: fetch mappings from GitHub raw

The tool's only runtime dependency was `fetch("../mappings/{platform}.yaml")` — a relative
path that forced bundling the mappings and finagling where the tool sits. Point it at
**GitHub raw** instead:

```
MAPPINGS_BASE = "https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/main/mappings/"
```

Now the published site is **just the two static files** — no bundling, no build, no
relative-path constraints. `raw.githubusercontent.com` serves `access-control-allow-origin: *`,
so the cross-origin fetch works from any domain (and from `file://`). The deploy artifact is
literally the directory, uploaded as-is.

**Trade-offs (accepted, documented):**
- The live tool tracks **`main`** — mapping edits appear without redeploying (a feature:
  deploy the code once, data stays current). The cost: a broken `mappings/*.yaml` on `main`
  would surface in the live tool. `main` is CI-gated, so this is low risk; pin to a tag
  (`spec/v0.9.0`) in the URL if you ever want the tool frozen to a spec release.
- Adds a dependency on GitHub raw (availability, ~5-min CDN cache). Fine for an explorer.

## Decisions

### D1 — Rename `tool/` → `site/`

`site/` is the published **website** — the explorer now, docs/guides later. (Not `docs/`,
which is the internal spec: `taxonomy.md`, `translation.md`, `reference.md`.) The rename
touches only the `Makefile` target and two literal strings in `index.html`; README has no
tool link, and the `plans/` mentions are historical.

### D2 — `MAPPINGS_BASE` → GitHub raw (above). One-line change in `site/index.html`.

### D3 — No build step

The deploy artifact is `site/` exactly as committed (`index.html` + `translate.js`).
Nothing is generated, copied, or transformed — the simplest possible pipeline.

### D4 — `make deploy` (local, via Wrangler)

```make
deploy: ## Deploy site/ to Cloudflare Pages (production)
	@npx wrangler pages deploy site --project-name=open-sport-taxonomy --branch=main --commit-dirty=true

serve: ## Preview the site locally (mappings load from GitHub raw)
	@python3 -m http.server --directory site 0
```

`make deploy` is a single Wrangler call uploading the static dir. `make serve` replaces the
old `tool` target. (Wrangler is the official Cloudflare Pages CLI; `npx` means no global
install. Authenticate once with `wrangler login`, or set `CLOUDFLARE_API_TOKEN`.)

### D5 — Custom domain

`sweatstack.no` is already on Cloudflare, so add `open-sport-taxonomy.sweatstack.no` under
the Pages project's **Custom domains** — one click; DNS + TLS are provisioned automatically.

## Steps

1. `git mv tool site`; rename the Makefile `tool` target → `serve` (point `--directory` at
   `site`); fix the two `tool/`/`make tool` strings in `site/index.html`.
2. Set `MAPPINGS_BASE` to the GitHub raw URL (D2).
3. `make serve` → confirm all 7 platforms load and translate (mappings come from GitHub raw).
4. Create the Cloudflare Pages project `open-sport-taxonomy` (dashboard, or
   `wrangler pages project create`), production branch `main`.
5. `make deploy` → verify the explorer on the `*.pages.dev` URL.
6. Add the custom domain (D5); verify `https://open-sport-taxonomy.sweatstack.no` over TLS.
7. Commit the rename + `MAPPINGS_BASE` + Makefile changes.

## Verification

- `make serve` and the deployed domain both load the explorer; DevTools shows each
  `https://raw.githubusercontent.com/.../mappings/<platform>.yaml` returning 200.
- Editing a mapping on `main` is reflected on the live tool within the CDN cache window,
  **without** a redeploy.

## Prerequisites

- Wrangler authenticated locally (`wrangler login` or `CLOUDFLARE_API_TOKEN`); `node`/`npx`
  available.
- Cloudflare Pages project creatable on the SweatStack account (confirmed).

## Future (docs growth)

`site/` grows into a real docs site: add `site/index.html` as a landing page, move the
explorer to `site/explorer/`, and add rendered pages from `docs/*.md`. Because mappings load
from an absolute GitHub-raw URL, the explorer keeps working no matter where it sits — no
code change when it moves. Deployment stays `make deploy` (still just uploading `site/`); a
build step is added only if/when docs need rendering.

## Out of scope (iteration 1)

- No build pipeline, no Git-integration auto-deploy (deploys are local + on demand).
- No landing page, analytics, or SEO yet — just the explorer at the apex.
