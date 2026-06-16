// @ts-check
//
// OpenSportTaxonomy — taxonomy operations, reference implementation.
//
// The taxonomy-side companion to `translate.js`'s translation engine. PURE: no
// I/O, no DOM. It answers two questions the filtering demo is built on, both
// specified in docs/taxonomy.md:
//
//   classifyTier(s, atoms)        // which of the three nested validity tiers s reaches
//   isSubsport(activity, query)   // does `activity` fall under `query` in the hierarchy
//
// The validity tiers (docs/taxonomy.md §"Standard sports, atoms, and labels"):
//   well-formed  ⊇  known-atoms  ⊇  standard
// plus "malformed" below well-formed for strings that fail the lexical grammar.

import { parseSport } from "./translate.js";

/**
 * Canonical lexical grammar for a well-formed OST string. This MUST stay in
 * sync with docs/taxonomy.md §"The well-formed grammar" — that doc is the
 * source of truth; this is its machine mirror.
 *
 * A dotted code path, then zero or more `+`modifiers; each segment is lowercase
 * letters with single internal underscores and at least one letter; dots live
 * only inside the code (never after a `+`); no empty segments.
 */
export const WELL_FORMED = /^[a-z]+(?:_[a-z]+)*(?:\.[a-z]+(?:_[a-z]+)*)*(?:\+[a-z]+(?:_[a-z]+)*)*$/;

/**
 * Does `s` match the well-formed lexical grammar? (Tier 1.)
 * @param {string} s
 * @returns {boolean}
 */
export function isWellFormed(s) {
  return WELL_FORMED.test(s);
}

/**
 * The canonical form of a sport string: its code plus its modifiers sorted and
 * de-duplicated. `parseSport` already sorts, so this only de-duplicates.
 * @param {string} s
 * @returns {string}
 */
export function canonical(s) {
  const { code, mods } = parseSport(s);
  const unique = [...new Set(mods)];
  return unique.length ? `${code}+${unique.join("+")}` : code;
}

/**
 * @typedef {{ codes: Set<string>, groups: Map<string, string | null>,
 *             catalogue: Set<string> }} Atoms
 */

/**
 * Build the atom tables `classifyTier` needs from a parsed catalogue. `codes`
 * is every bare (modifier-free) catalogue code; `groups` maps each declared
 * modifier to its group (or null); `catalogue` is every canonical catalogue
 * string, for the exact `standard` check.
 * @param {import("./translate.js").Catalogue} cat
 * @returns {Atoms}
 */
export function buildAtoms(cat) {
  const codes = new Set(cat.sports.filter((s) => s.mods.length === 0).map((s) => s.code));
  const groups = new Map(cat.modifiers.map((m) => [m.code, m.group]));
  const catalogue = new Set(cat.sports.map((s) => s.sport));
  return { codes, groups, catalogue };
}

/**
 * Classify `s` into the highest validity tier it reaches.
 *
 * `malformed`    — fails the lexical grammar.
 * `well-formed`  — parses, but the code or a modifier is unknown, or two
 *                  modifiers collide in a group, or a modifier repeats.
 * `known-atoms`  — known code, all modifiers declared and group-valid (≤1 per
 *                  group, no repeats), but not catalogued verbatim.
 * `standard`     — the canonical string is a catalogue entry.
 *
 * @param {string} s
 * @param {Atoms} atoms
 * @returns {"malformed" | "well-formed" | "known-atoms" | "standard"}
 */
export function classifyTier(s, atoms) {
  if (!isWellFormed(s)) return "malformed";
  if (atoms.catalogue.has(canonical(s))) return "standard";

  const { code, mods } = parseSport(s);
  if (!atoms.codes.has(code)) return "well-formed";
  if (new Set(mods).size !== mods.length) return "well-formed"; // a modifier repeats

  const seenGroups = new Set();
  for (const mod of mods) {
    if (!atoms.groups.has(mod)) return "well-formed"; // unknown modifier
    const group = atoms.groups.get(mod);
    if (group) {
      if (seenGroups.has(group)) return "well-formed"; // two modifiers, one group
      seenGroups.add(group);
    }
  }
  return "known-atoms";
}

/**
 * Sub-sport containment (docs/taxonomy.md §"Sub-sport containment"): is
 * `activity` the same as, or more specific than, `query`? True iff `activity`'s
 * code equals `query`'s code or is a descendant of it in the dot tree, AND
 * `activity`'s modifiers are a superset of `query`'s. This is the filter's core:
 * a bare `cycling` (no modifiers ⊆ everything) contains every cycling
 * descendant and modifier variant; `cycling+stationary` narrows to the indoor
 * ones.
 * @param {string} activity  a canonical OST sport string
 * @param {string} query     a well-formed OST sport string
 * @returns {boolean}
 */
export function isSubsport(activity, query) {
  const a = parseSport(activity);
  const q = parseSport(query);
  const codeMatches = a.code === q.code || a.code.startsWith(q.code + ".");
  if (!codeMatches) return false;
  const aMods = new Set(a.mods);
  return q.mods.every((m) => aMods.has(m));
}
