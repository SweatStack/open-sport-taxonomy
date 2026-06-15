// @ts-check
//
// OpenSportTaxonomy — platform translation, reference implementation.
//
// A faithful, dependency-free port of the format-v3 algorithm specified in
// docs/translation.md. This module is PURE: it parses mapping text and runs
// encode/decode. It performs no I/O and touches no DOM, so it can be reused
// from a browser (see index.html), from Node, or from a test harness.
//
//   parseMapping(text) -> PlatformIndex     // mappings/<platform>.yaml text
//   decode(index, targetKey) -> sport        // platform target  -> OST sport
//   encode(index, sport) -> { target, via }  // OST sport        -> platform target
//
// A "target key" is a stable string identifying one platform target:
//   - integer platforms (Apple, Wahoo, Suunto):  "13"
//   - string  platforms (Strava, Polar, Garmin Training API):  "VirtualRide"
//   - Garmin FIT (sport/sub_sport pair):  "2/7"

/**
 * @typedef {{ kind: 'int' | 'str' | 'fit', key: string, value: string,
 *             sport?: number, subSport?: number }} Target
 * @typedef {{ target: Target, name: string, sport: string | null }} Entry
 * @typedef {{
 *   fallbackEncode: string,
 *   fallbackDecode: string,
 *   coarsening: Array<Record<string, number>>,
 *   byKey: Map<string, Entry>,
 *   order: string[],
 *   preferred: Map<string, string>,
 * }} PlatformIndex
 */

// ---------------------------------------------------------------------------
// Targets
// ---------------------------------------------------------------------------

/**
 * Normalise the raw text of a target value into a {@link Target}.
 * @param {string} raw
 * @returns {Target}
 */
export function normalizeTarget(raw) {
  const text = raw.trim();

  const fit = text.match(/^\{\s*sport:\s*(\d+)\s*,\s*sub_sport:\s*(\d+)\s*\}$/);
  if (fit) {
    const sport = Number(fit[1]);
    const subSport = Number(fit[2]);
    const key = `${sport}/${subSport}`;
    return { kind: 'fit', key, value: key, sport, subSport };
  }
  if (/^\d+$/.test(text)) {
    return { kind: 'int', key: text, value: text };
  }
  return { kind: 'str', key: text, value: text };
}

// ---------------------------------------------------------------------------
// Parsing
//
// Mapping files are regular enough to parse line-by-line, which (unlike a YAML
// parser) lets us keep the `# comment` after each target — the human-readable
// platform sport name we want to display.
// ---------------------------------------------------------------------------

/**
 * Parse the text of a `mappings/<platform>.yaml` file into a queryable index.
 * @param {string} text
 * @returns {PlatformIndex}
 */
export function parseMapping(text) {
  const lines = text.split(/\r?\n/);

  // `encode:` / `decode:` appear only inside the `fallback:` block.
  const encodeLine = lines.find((l) => /^\s+encode:/.test(l));
  const decodeLine = lines.find((l) => /^\s+decode:/.test(l));
  if (!encodeLine || !decodeLine) throw new Error('mapping is missing a fallback block');
  const fallbackEncode = normalizeTarget(encodeLine.replace(/^\s*encode:\s*/, '')).key;
  const fallbackDecode = decodeLine.replace(/^\s*decode:\s*/, '').trim();

  // `target_coarsening` (optional; Garmin FIT only): a list of `reset` rules.
  /** @type {Array<Record<string, number>>} */
  const coarsening = [];
  for (const line of lines) {
    const m = line.match(/^\s*-\s*reset:\s*\{(.+)\}\s*$/);
    if (!m) continue;
    /** @type {Record<string, number>} */
    const rule = {};
    for (const pair of m[1].split(',')) {
      const [field, value] = pair.split(':').map((s) => s.trim());
      rule[field] = Number(value);
    }
    coarsening.push(rule);
  }

  /** @type {Map<string, Entry>} */
  const byKey = new Map();
  /** @type {string[]} */
  const order = [];
  /** @type {Map<string, string>} */
  const preferred = new Map();

  /** @type {{ target: Target, name: string, sport: string | null, preferred: boolean } | null} */
  let current = null;
  const flush = () => {
    if (!current) return;
    byKey.set(current.target.key, {
      target: current.target,
      name: current.name,
      sport: current.sport,
    });
    order.push(current.target.key);
    if (current.preferred && current.sport) preferred.set(current.sport, current.target.key);
    current = null;
  };

  let inEntries = false;
  for (const line of lines) {
    if (/^entries:/.test(line)) {
      inEntries = true;
      continue;
    }
    if (!inEntries) continue;

    // A `#` only ever introduces a comment (never appears inside a value).
    const hash = line.indexOf('#');
    const code = hash >= 0 ? line.slice(0, hash) : line;
    const comment = hash >= 0 ? line.slice(hash + 1).trim() : '';

    const targetMatch = code.match(/^\s*-\s*target:\s*(.+?)\s*$/);
    if (targetMatch) {
      flush();
      current = { target: normalizeTarget(targetMatch[1]), name: comment, sport: null, preferred: false };
      continue;
    }
    if (!current) continue;

    const sportMatch = code.match(/^\s*sport:\s*(.+?)\s*$/);
    if (sportMatch) {
      const value = sportMatch[1].trim();
      current.sport = value === 'null' ? null : value;
      continue;
    }
    if (/^\s*preferred:\s*true\s*$/.test(code)) current.preferred = true;
  }
  flush();

  return { fallbackEncode, fallbackDecode, coarsening, byKey, order, preferred };
}

/**
 * @typedef {{ sport: string, label: string, code: string, mods: string[] }} StandardSport
 * @typedef {{ version: string, sports: StandardSport[] }} Catalogue
 */

/**
 * Parse `schema.yaml` text into the standard-sports catalogue. Like
 * {@link parseMapping}, this reads the regular YAML line-by-line — no library —
 * and is PURE (no I/O, no DOM). Only `version:` and the `sports:` section are
 * extracted; modifiers ride along inside each combination's canonical string.
 * @param {string} text
 * @returns {Catalogue}
 */
export function parseSchema(text) {
  const lines = text.split(/\r?\n/);
  let version = '';
  /** @type {StandardSport[]} */
  const sports = [];
  /** @type {'sports' | 'modifiers' | null} */
  let section = null;
  /** @type {{ sport: string, label: string } | null} */
  let current = null;
  const flush = () => {
    if (current && current.sport) {
      const [code, ...mods] = current.sport.split('+');
      sports.push({ sport: current.sport, label: current.label, code, mods });
    }
    current = null;
  };

  for (const line of lines) {
    const versionMatch = line.match(/^version:\s*"?([^"]+?)"?\s*$/);
    if (versionMatch) {
      version = versionMatch[1];
      continue;
    }
    if (/^sports:\s*$/.test(line)) {
      section = 'sports';
      continue;
    }
    if (/^modifiers:\s*$/.test(line)) {
      flush();
      section = 'modifiers';
      continue;
    }
    if (section !== 'sports') continue;

    const sportMatch = line.match(/^\s*-\s*sport:\s*(.+?)\s*$/);
    if (sportMatch) {
      flush();
      current = { sport: sportMatch[1].trim(), label: '' };
      continue;
    }
    const labelMatch = line.match(/^\s*label:\s*(.+?)\s*$/);
    if (labelMatch && current) current.label = labelMatch[1].trim();
  }
  flush();

  return { version, sports };
}

// ---------------------------------------------------------------------------
// Decode  (platform target -> OST sport)
//
// A direct lookup against the platform-keyed table. `target_coarsening` gives
// forward-compatible fallback for targets newer than the bundled snapshot;
// it never fires when decoding a platform's own enumerated targets, but is
// included so this stays a complete reference for the spec.
// ---------------------------------------------------------------------------

/**
 * @param {PlatformIndex} index
 * @param {string} targetKey
 * @returns {string} the OST sport string
 */
export function decode(index, targetKey) {
  const entry = index.byKey.get(targetKey);
  if (entry) return entry.sport ?? index.fallbackDecode;

  for (const rule of index.coarsening) {
    const candidate = applyReset(targetKey, rule);
    if (candidate === targetKey) continue; // rule was a no-op for this input
    const coarsened = index.byKey.get(candidate);
    if (coarsened) return coarsened.sport ?? index.fallbackDecode;
  }
  return index.fallbackDecode;
}

/**
 * Rewrite a Garmin FIT target key (`"sport/sub_sport"`) by a `reset` rule.
 * @param {string} fitKey
 * @param {Record<string, number>} rule
 * @returns {string}
 */
function applyReset(fitKey, rule) {
  let [sport, subSport] = fitKey.split('/').map(Number);
  if ('sport' in rule) sport = rule.sport;
  if ('sub_sport' in rule) subSport = rule.sub_sport;
  return `${sport}/${subSport}`;
}

// ---------------------------------------------------------------------------
// Encode  (OST sport -> platform target)
//
// An unbounded domain (any code x any subset of modifiers), so a hierarchical
// search rather than a lookup: try the most specific candidate first, walking
// the OST tree. Modifiers dominate discipline depth — dropping `+stationary`
// to keep `.road` would render an indoor trainer ride as an outdoor route, a
// worse error than dropping `.road` to keep `+stationary`.
// ---------------------------------------------------------------------------

/**
 * @param {PlatformIndex} index
 * @param {string} sport  a canonical OST sport string
 * @returns {{ target: string, via: string | null }}
 *   `target` is the platform target key; `via` is the candidate that matched,
 *   or `null` when the platform has no equivalent and the fallback was used.
 */
export function encode(index, sport) {
  for (const candidate of candidates(sport)) {
    const target = index.preferred.get(candidate);
    if (target !== undefined) return { target, via: candidate };
  }
  return { target: index.fallbackEncode, via: null };
}

/**
 * Candidate OST sport strings, most specific first. Modifiers are preserved
 * while the discipline walks up the tree, then dropped and the tree walked
 * again.
 * @param {string} sport
 * @returns {Generator<string>}
 */
function* candidates(sport) {
  const { code, mods } = parseSport(sport);
  const lineage = ancestry(code); // [code, parent, grandparent, ...]

  for (const ancestor of lineage) yield withMods(ancestor, mods);
  if (mods.length) {
    for (const ancestor of lineage) yield ancestor;
  }
}

/**
 * Split a sport string into its code and its sorted modifiers.
 * @param {string} sport
 * @returns {{ code: string, mods: string[] }}
 */
function parseSport(sport) {
  const [code, ...mods] = sport.split('+');
  return { code, mods: mods.slice().sort() };
}

/**
 * The dot-notation lineage of a code, nearest first: `cycling.road.crit`
 * yields `["cycling.road.crit", "cycling.road", "cycling"]`. Computed
 * mechanically — no schema lookup needed.
 * @param {string} code
 * @returns {string[]}
 */
function ancestry(code) {
  const lineage = [];
  let current = code;
  for (;;) {
    lineage.push(current);
    const dot = current.lastIndexOf('.');
    if (dot < 0) break;
    current = current.slice(0, dot);
  }
  return lineage;
}

/**
 * Recompose a canonical sport string from a code and sorted modifiers.
 * @param {string} code
 * @param {string[]} mods  already sorted
 * @returns {string}
 */
function withMods(code, mods) {
  return mods.length ? `${code}+${mods.join('+')}` : code;
}
