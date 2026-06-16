// @ts-check
//
// OpenSportTaxonomy — synthetic activity log for the filtering demo. PURE: no
// I/O, no DOM. Builds a deterministic, believable training history so the
// filtering page has realistic data to filter. NOT real data — every activity
// is generated from a fixed seed, so the same ~150 activities appear on every
// load (a live `Math.random` would reshuffle the log each time).
//
// The persona is a cyclist-runner who dabbles broadly: heavy road cycling and
// road running, a thick layer of indoor/commute variants, and a long tail of
// swims, hikes, indoor rows, alpine days, and (roller) skiing. No seasonality —
// activities spread uniformly across the trailing ~12 months.

import { parseSport } from "./translate.js";

const SEED = "open-sport-taxonomy/filtering/v1";
const DAYS = 365;

// Relative frequency per canonical sport string. Every sport here is seeded at
// least once (a "coverage floor"), so any catalogued query returns something;
// the rest of the log is filled in proportion to these weights. `generic` and
// `hand_cycling` are intentionally absent — not this athlete.
const WEIGHTS = {
  "cycling": 5,
  "cycling.road": 16,
  "cycling.gravel": 9,
  "cycling.mountain": 5,
  "cycling.mountain+assisted": 1,
  "cycling.cyclocross": 2,
  "cycling.time_trial": 1,
  "cycling.track": 1,
  "cycling+stationary": 10,
  "cycling+stationary+virtual": 7,
  "cycling+commute": 7,
  "cycling+assisted": 1,
  "running": 6,
  "running.road": 14,
  "running.trail": 7,
  "running.track": 2,
  "running+stationary": 8,
  "running+stationary+virtual": 4,
  "running+race": 2,
  "swimming": 1,
  "swimming.pool": 6,
  "swimming.open_water": 3,
  "walking": 4,
  "walking.hiking": 6,
  "walking+stationary": 1,
  "rowing": 1,
  "rowing+stationary": 4,
  "rowing+stationary+virtual": 1,
  "xc_skiing": 1,
  "xc_skiing.classic": 2,
  "xc_skiing.skate": 2,
  "xc_skiing.double_poling": 1,
  "xc_skiing+roller": 1,
  "xc_skiing.classic+roller": 1,
  "xc_skiing.skate+roller": 1,
  "alpine_skiing": 2,
  "snowboarding": 1,
};

// Per-base-code metric profile: plausible speed (m/s, for deriving distance from
// duration), duration range (minutes), a title pool, and whether a distance
// reads sensibly (false for downhill snow sports — duration only). Keyed by the
// modality (first dot segment); modifiers nudge a few specifics below.
const PROFILES = {
  cycling: { speed: 7.2, min: 60, max: 200, distance: true,
    titles: ["Endurance ride", "Z2 base", "Long ride", "Café ride", "Sweet-spot intervals", "Tempo loop"] },
  running: { speed: 3.0, min: 35, max: 80, distance: true,
    titles: ["Easy run", "Z2 run", "Tempo run", "Threshold session", "Long run", "Recovery shakeout"] },
  swimming: { speed: 0.9, min: 25, max: 60, distance: true,
    titles: ["Technique set", "Threshold 100s", "Endurance swim", "Pull buoy session"] },
  walking: { speed: 1.3, min: 30, max: 90, distance: true,
    titles: ["Morning walk", "Dog walk", "Recovery walk", "City stroll"] },
  rowing: { speed: 3.3, min: 20, max: 50, distance: true,
    titles: ["Steady state", "Interval pieces", "2k test prep", "Recovery row"] },
  xc_skiing: { speed: 3.5, min: 60, max: 150, distance: true,
    titles: ["Endurance ski", "Interval session", "Technique day", "Long tour"] },
  alpine_skiing: { speed: 0, min: 150, max: 320, distance: false,
    titles: ["Resort day", "Powder morning", "Piste laps"] },
  snowboarding: { speed: 0, min: 120, max: 300, distance: false,
    titles: ["Park session", "Powder day", "Resort laps"] },
};

// Modality-and-modifier nudges to the base profile, applied by canonical string.
const OVERRIDES = {
  "cycling.road": { speed: 8.3 },
  "cycling.gravel": { speed: 6.9, max: 240 },
  "cycling.mountain": { speed: 5.0, min: 60, max: 150, titles: ["Trail ride", "Singletrack loop", "Technical XC"] },
  "cycling.cyclocross": { speed: 6.0, min: 45, max: 90, titles: ["CX intervals", "Skills + ride", "Race simulation"] },
  "cycling.time_trial": { speed: 11.0, min: 30, max: 70, titles: ["TT effort", "FTP test", "Race-pace block"] },
  "cycling.track": { speed: 11.5, min: 40, max: 80, titles: ["Track session", "Flying laps", "Madison drills"] },
  "cycling+stationary": { speed: 8.0, min: 45, max: 90, titles: ["Trainer session", "FTP intervals", "Z2 on the trainer"] },
  "cycling+stationary+virtual": { speed: 8.0, min: 45, max: 90, titles: ["Zwift race", "Group ride", "Virtual climb"] },
  "cycling+commute": { speed: 5.5, min: 20, max: 45, titles: ["Commute in", "Commute home", "Ride to work"] },
  "running.road": { speed: 3.1, min: 30, max: 80 },
  "running.trail": { speed: 2.6, min: 50, max: 130, titles: ["Trail run", "Hill reps", "Long trail"] },
  "running.track": { speed: 3.6, min: 35, max: 60, titles: ["Track intervals", "400 reps", "Speed session"] },
  "running+stationary": { speed: 3.0, min: 30, max: 60, titles: ["Treadmill run", "Incline session", "Treadmill intervals"] },
  "running+stationary+virtual": { speed: 3.0, min: 30, max: 60, titles: ["Virtual 5k", "Treadmill race", "Guided run"] },
  "running+race": { speed: 3.3, min: 90, max: 220, titles: ["Half marathon", "10k race", "Marathon"] },
  "swimming.pool": { speed: 0.95, titles: ["Pool session", "Threshold 100s", "Technique set"] },
  "swimming.open_water": { speed: 0.82, min: 30, max: 75, titles: ["Open-water swim", "Lake loop", "Sea swim"] },
  "walking.hiking": { speed: 1.1, min: 90, max: 300, titles: ["Day hike", "Summit hike", "Forest loop"] },
  "walking+stationary": { speed: 1.3, min: 30, max: 60, titles: ["Treadmill walk", "Incline walk"] },
  "rowing+stationary": { speed: 3.3, titles: ["Erg steady state", "Erg intervals", "2k test"] },
  "rowing+stationary+virtual": { speed: 3.3, titles: ["Virtual row", "Online regatta"] },
  "xc_skiing+roller": { speed: 4.2, min: 45, max: 120, titles: ["Rollerski endurance", "Rollerski intervals"] },
  "xc_skiing.classic+roller": { speed: 4.0, min: 45, max: 120, titles: ["Classic rollerski", "Technique rollerski"] },
  "xc_skiing.skate+roller": { speed: 4.4, min: 45, max: 120, titles: ["Skate rollerski", "V2 intervals"] },
  "xc_skiing.classic": { titles: ["Classic ski", "Long classic tour", "Double-pole drills"] },
  "xc_skiing.skate": { titles: ["Skate ski", "V2 intervals", "Skate technique"] },
  "xc_skiing.double_poling": { speed: 4.0, titles: ["Double-pole session", "DP intervals"] },
};

/** xmur3 string hash → 32-bit seed. */
function xmur3(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return h >>> 0;
  };
}

/** mulberry32 PRNG → deterministic floats in [0, 1). */
function mulberry32(a) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Resolve a sport's metric profile by merging the base modality with overrides. */
function profileFor(sport) {
  const { code } = parseSport(sport);
  const base = PROFILES[code.split(".")[0]] ?? PROFILES.cycling;
  return { ...base, ...(OVERRIDES[sport] ?? {}) };
}

/**
 * Generate the synthetic activity log: `count` activities, deterministic from a
 * fixed seed, newest first.
 * @param {import("./translate.js").Catalogue} catalogue
 * @param {number} [count]
 * @returns {Array<{date: Date, sport: string, label: string, title: string,
 *                   durationSec: number, distanceM: number | null}>}
 */
export function generateActivities(catalogue, count = 150) {
  const rng = mulberry32(xmur3(SEED)());
  const randInt = (min, max) => min + Math.floor(rng() * (max - min + 1));
  const pick = (arr) => arr[Math.floor(rng() * arr.length)];

  const labels = new Map(catalogue.sports.map((s) => [s.sport, s.label]));

  // Sample the whole log by weight (so heavy sports stay prominent), then repair
  // coverage: a fixed seed can leave a rare sport at zero, so donate a slot from
  // the most over-sampled sport to each missing one. This keeps the weighted
  // shape while guaranteeing every weighted sport appears at least once — so any
  // catalogued query returns something to filter.
  const weighted = Object.entries(WEIGHTS).filter(([sport]) => labels.has(sport));
  const total = weighted.reduce((sum, [, w]) => sum + w, 0);
  const pickSport = () => {
    let r = rng() * total;
    for (const [sport, w] of weighted) {
      r -= w;
      if (r <= 0) return sport;
    }
    return weighted[weighted.length - 1][0];
  };

  const sports = Array.from({ length: count }, pickSport);
  const counts = new Map();
  for (const s of sports) counts.set(s, (counts.get(s) ?? 0) + 1);
  for (const [sport] of weighted) {
    if (counts.has(sport)) continue;
    let donor = null;
    let max = 1;
    for (const [s, c] of counts) {
      if (c > max) {
        max = c;
        donor = s;
      }
    }
    if (!donor) break;
    sports[sports.lastIndexOf(donor)] = sport;
    counts.set(donor, counts.get(donor) - 1);
    counts.set(sport, 1);
  }

  const now = new Date();
  const activities = sports.slice(0, count).map((sport) => {
    const p = profileFor(sport);
    const durationSec = randInt(p.min, p.max) * 60;
    const distanceM = p.distance && p.speed > 0
      ? Math.round((durationSec * p.speed * (0.9 + rng() * 0.2)) / 10) * 10
      : null;

    const date = new Date(now);
    date.setDate(date.getDate() - randInt(0, DAYS - 1));
    date.setHours(randInt(6, 19), pick([0, 15, 30, 45]), 0, 0);

    return { date, sport, label: labels.get(sport) ?? sport, title: pick(p.titles), durationSec, distanceM };
  });

  activities.sort((a, b) => b.date.getTime() - a.date.getTime());
  return activities;
}
