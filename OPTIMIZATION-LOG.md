# Antenna Optimization Log

## 2026-07-01 — FOX (4.1 KDFW) re-aim for World Cup; ABC traded away

**Goal:** Re-maximize FOX 4.1 for World Cup soccer while keeping CBS/ABC at
least as good, and improve NBC if possible. Same rig: `mike-ubuntu`,
HDHomeRun at `hdhomerun.local`, ClearStream 2V in the network closet.

**Starting state was NOT the 06-21 FOX-optimized aim** — the antenna had moved
between sessions into an NBC-favoring position (FOX had fallen back to ~71–78,
its baseline; NBC/CBS were up). Confirmed the FOX↔NBC tradeoff is real, and
found a second, sharper one: **FOX↔ABC**.

**Method:** Added an `--aim` mode to the script (live watch of a focused 2-channel
pair with per-channel peak tracking) — far better for hunting than the old
all-6 `--watch`. Hunted azimuth then tilt while reading FOX against its rival.

**Key finding — the closet has hit its ceiling.** FOX and ABC are directly
anti-correlated here: every tilt/azimuth that lifts FOX nulls ABC, and vice
versa. Laying the antenna *flatter* (more horizontal) is the FOX win; standing
it up or rotating ~5° left recovers ABC at FOX's expense. The clean middle
spot exists but is **not hand-reproducible** (sub-2° precision). So the stated
constraint (FOX up AND ABC held) is unsatisfiable at this location. Chose
FOX-max for the tournament; ABC is the deliberate sacrifice.

### Result — FOX-max position (kept), flatter tilt + center azimuth

Signal Quality (SQ), today's starting state vs. locked FOX-max:

| Ch       | Start SQ | FOX-max SQ | Note                              |
|----------|----------|------------|-----------------------------------|
| 4.1 FOX  | ~75      | **95**     | now the strongest major, SYM:100  |
| 5.1 NBC  | ~84      | 79         | ~held                             |
| 8.8 ABC  | ~89      | **70**     | traded away; dips to ~55, still decodes |
| 11.1 CBS | 100      | 100        | held                              |
| 13.1 PBS | ~95      | 93         | held                              |
| 33.1 CW  | ~84      | 85         | held                              |

FOX at SQ 95 / SYM 100 is a bigger win than 06-21 ever got (~80). ABC at ~70
is above the dropout cliff and still decodes, but has lost its margin and will
glitch occasionally — acceptable only because FOX is the priority right now.

**Antenna position is flatter/more horizontal than the 06-21 aim.** Photograph
and secure it — it's touchy and ABC is already marginal, so a bump loses FOX.

### Raw data (committed)

- `antenna_scan_20260630_19*.json` — the NBC-favoring starting state (3 passes).
- `antenna_scan_fox-flat-tilt_20260701_174623.json` — first flat-tilt scan (ABC
  read a spurious 48 here; two follow-ups showed ABC ~82, so ignore that 48).
- `antenna_scan_fox-final-2026-07-01_20260701_180317.json` — locked FOX-max.

### Revert / next time

- **After the World Cup, revert** for ABC's sake: stand the antenna up / rotate
  ~5° left to recover ABC to ~92 (costs FOX back down to ~78).
- **The real fix is the attic install.** This session proved the closet is
  multipath-limited — you can only rob one channel to feed another. A higher
  antenna with clear line of sight to Cedar Hill should lift FOX *and* ABC
  together. That's the trigger the 06-21 log called for, and we've now hit it.

---

## 2026-06-21 — FOX (4.1 KDFW) aiming pass

**Goal:** Maximize FOX 4.1 reception (for soccer) without sacrificing the other
Cedar Hill majors. Run from `mike-ubuntu`; HDHomeRun at `hdhomerun.local`
(192.168.68.84), ClearStream 2V antenna.

**Method:** Narrowed `MAJOR_CHANNELS` to `['4.1']` and ran `--watch` for live
feedback while slowly rotating the antenna. Found a peak, then reverted the
channel list and ran full scans to confirm no other channel regressed.

### Result — clear win, kept after this session

Antenna ended in an unusual orientation (roughly aimed SSE toward Cedar Hill,
~160°). Photos of the exact position:

- `antenna-position-2026-06-21_wide.jpg` — wide shot, antenna on its articulating
  clamp mount in the network closet by the shelf.
- `antenna-position-2026-06-21_tilt.jpg` — close-up showing the upward tilt and
  off-axis aim that produced the win. This is the orientation to restore if it
  gets bumped.

Signal Quality (SQ) before vs. after, by virtual channel:

| Ch       | Baseline SQ | Optimized SQ (avg of 2 clean passes) |
|----------|-------------|--------------------------------------|
| 4.1 FOX  | 70          | ~80                                  |
| 5.1 NBC  | 51          | ~59                                  |
| 8.8 ABC  | 95          | ~90                                  |
| 11.1 CBS | 78          | ~88                                  |
| 13.1 PBS | 68          | ~90                                  |
| 33.1 CW  | 59          | ~75                                  |

FOX rose ~10 points to a steady ~80% SQ with `SYM:100` — comfortably above the
ATSC dropout cliff, clean for live sports. PBS/CW/CBS jumped, NBC ticked up,
ABC dipped 5 points but is still rock-solid at 90. No channel was robbed to
feed FOX (everything's co-located at Cedar Hill, so aim helps them together).

This was a *quality* (SNR/multipath) problem, not a *power* problem — FOX
strength was already 85%. Fix was aiming, not a preamp. A preamp would have
boosted noise too and risked front-end overload at this signal level.

### Raw data (committed, normally gitignored)

- `antenna_scan_20260621_180337.json` — baseline (original antenna position)
- `antenna_scan_fox-optimized_20260621_181548.json` — first post-aim scan;
  FOX shows SQ:0% here because the `--watch` thread still held the tuner. Ignore.
- `antenna_scan_20260621_181649.json` / `..._181658.json` — two clean confirmation
  passes after the tuner was freed. These are the trustworthy numbers above.

### Measurement caveat

`SymbolQualityPercent` flaps between 0 and 100 across passes — a sampling
artifact (status read a hair before the tuner fully settles), not real dropout.
The `time.sleep(1)` tuner-lock wait is marginal; bump to 1.5s if it bothers you.
Only one tuner job at a time — kill any `--watch` process before running a scan,
or you'll get spurious SQ:0% readings.

### Next time / open items

- **NBC 5.1 is now the weakest at ~59% SQ.** It's the next aiming target, but
  expect a tradeoff hunt against FOX — improving one may cost the other.
- **Secure the antenna.** It's in an awkward physical position; clamp/tape it so
  a bump doesn't undo this.
- **If FOX SQ ever won't hold above ~75%**, that's the trigger for the planned
  attic install (antenna higher, clear of the roofline), and *then* possibly a
  preamp to offset attic insertion loss — prove it's needed first.
