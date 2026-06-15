// @ts-check
//
// Shared UI: a ⇄ button that opens a native HTML popover listing how one OST
// sport encodes to every platform. Used by both the standard-sports browser and
// the translation explorer, so the control looks and behaves identically.
//
// It uses the native Popover API (`popover="auto"` + `popovertarget`), so the
// browser handles outside-click dismissal, Escape, and closing any other open
// popover. We only position it (on its `toggle` event) and close it on
// scroll/resize. The component injects its own styles once, so the two pages
// share one source of truth for both behaviour and appearance.

import { encode } from "./translate.js";

const INFO_SVG =
  '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor"' +
  ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/>' +
  '<line x1="12" y1="8" x2="12.01" y2="8"/></svg>';

const STYLES = `
.xlate-btn {
  display: inline-flex; align-items: center; justify-content: center;
  align-self: center; flex: 0 0 auto;
  width: 1.3rem; height: 1.3rem; padding: 0; vertical-align: middle;
  color: var(--muted, #8a8a8a); background: none; border: none;
  border-radius: 0.3rem; cursor: pointer;
  transition: color 0.1s, background 0.1s;
}
.xlate-btn:hover { color: var(--accent, #0b66c3); background: var(--zebra, #fafafa); }

.xlate-popover {
  position: fixed; margin: 0; inset: auto; z-index: 50;
  max-width: min(24rem, calc(100vw - 1rem));
  background: #fff; border: 1px solid var(--line, #e3e3e3); border-radius: 0.5rem;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.13);
  padding: 0.75rem 0.9rem; font-size: 0.88rem; color: var(--ink, #1a1a1a);
  opacity: 0; transition: opacity 0.1s ease;
}
.xlate-popover .pop-head {
  margin: 0 0 0.55rem; padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line, #e3e3e3);
}
.xlate-popover .pop-title {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.92rem; font-weight: 600; overflow-wrap: anywhere;
}
.xlate-popover .pop-label { margin-top: 0.3rem; font-size: 0.85rem; }
.xlate-popover .pop-label .pop-key { color: var(--muted, #8a8a8a); margin-right: 0.6rem; }
.xlate-popover dl { display: grid; grid-template-columns: auto auto; gap: 0.3rem 1.1rem; margin: 0; }
.xlate-popover dt { color: var(--muted, #8a8a8a); }
.xlate-popover dd { margin: 0; }
.xlate-popover dd.fallback code { opacity: 0.5; }
.xlate-popover code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.85em; padding: 0.05rem 0.34rem;
  color: var(--ink, #1a1a1a); background: #f1f1f1; border-radius: 0.3rem;
}
`;

let stylesInjected = false;
let seq = 0;
let openPopoverEl = null;

function ensureStyles() {
  if (stylesInjected) return;
  const style = document.createElement("style");
  style.textContent = STYLES;
  document.head.append(style);
  stylesInjected = true;
}

/** Place the popover beside its trigger, flipping/clamping to the viewport. */
function positionPopover(pop, btn) {
  const r = btn.getBoundingClientRect();
  const gap = 8;
  const pw = pop.offsetWidth;
  const ph = pop.offsetHeight;
  let left = r.right + gap;
  if (left + pw > window.innerWidth - gap) left = r.left - pw - gap; // flip left
  left = Math.max(gap, Math.min(left, window.innerWidth - pw - gap));
  let top = r.top;
  top = Math.max(gap, Math.min(top, window.innerHeight - ph - gap));
  pop.style.left = `${left}px`;
  pop.style.top = `${top}px`;
}

/** Fill a popover with the sport's label, canonical string, and per-platform targets. */
function fillPopover(pop, sport, ctx) {
  pop.querySelector(".pop-title").textContent = sport;
  pop.querySelector(".pop-value").textContent = ctx.labels.get(sport) ?? sport;
  const list = pop.querySelector("dl");
  const frag = document.createDocumentFragment();
  for (const p of ctx.platforms) {
    const dt = document.createElement("dt");
    dt.textContent = p.label;
    const dd = document.createElement("dd");
    const code = document.createElement("code");
    const index = ctx.indices.get(p.id);
    if (!index) {
      code.textContent = "n/a";
      dd.classList.add("fallback");
    } else {
      const { target, via } = encode(index, sport);
      const entry = index.byKey.get(target);
      code.textContent = entry ? entry.target.value : target;
      if (entry && entry.name) dd.title = entry.name;
      if (via === null) dd.classList.add("fallback");
    }
    dd.append(code);
    frag.append(dt, dd);
  }
  list.replaceChildren(frag);
}

/**
 * Create a ⇄ button and its native popover for `sport`. Returns a fragment
 * holding both; insert it wherever the button should appear (the popover is
 * inert until shown and renders in the top layer, so its DOM position is free).
 * @param {string} sport canonical OST sport string
 * @param {{platforms: Array<{id:string,label:string}>, indices: Map, labels: Map}} ctx
 * @returns {DocumentFragment}
 */
export function createXlateButton(sport, ctx) {
  ensureStyles();
  const popId = `xpop-${seq++}`;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "xlate-btn";
  btn.setAttribute("popovertarget", popId);
  btn.setAttribute("aria-label", `Show how ${sport} translates to each platform`);
  btn.innerHTML = INFO_SVG;

  const pop = document.createElement("div");
  pop.id = popId;
  pop.className = "xlate-popover";
  pop.popover = "auto";
  pop.innerHTML =
    '<div class="pop-head"><div class="pop-title"></div>' +
    '<div class="pop-label"><span class="pop-key">Label</span><span class="pop-value"></span></div>' +
    "</div><dl></dl>";
  pop.addEventListener("toggle", (event) => {
    if (event.newState === "open") {
      if (!pop.dataset.filled) {
        fillPopover(pop, sport, ctx);
        pop.dataset.filled = "1";
      }
      positionPopover(pop, btn);
      pop.style.opacity = "1";
      btn.classList.add("open");
      openPopoverEl = pop;
    } else {
      pop.style.opacity = "0";
      btn.classList.remove("open");
      if (openPopoverEl === pop) openPopoverEl = null;
    }
  });

  const frag = document.createDocumentFragment();
  frag.append(btn, pop);
  return frag;
}

/** Close the open popover, if any. Call on scroll, resize, or before a re-render. */
export function closeXlatePopover() {
  openPopoverEl?.hidePopover();
}
