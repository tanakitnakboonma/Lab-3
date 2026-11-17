# Lab 03 — BJT DC Bias Web App (three bias modes)

**Date:** 2026-11-17
**Source spec:** `ENG29_2121_Lab03_BJT_Bias_Web_App.html` (course lab sheet, copied to `lab03/docs/lab03-assignment.html`)

## Intent

Extend the Lab 02 Flask app so the same form can compute the DC operating point of
three NPN common-emitter bias circuits, and verify the results in a real browser:

| Mode | Extra inputs |
|---|---|
| Voltage Divider Bias (existing, unchanged) | R1, R2, RE |
| Fixed Bias | RB |
| Emitter Bias (single supply) | RB, RE |

All modes share VCC, RC, β, VBE. Forward-active approximation, constant β/VBE.

## Goals

- Divider results identical to Lab 02 for the same inputs (A1).
- Formulas live in `dc_bias.py` as separate functions; `app.py` only dispatches.
- One result dict shape for all modes (`vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warning`).
- Per-mode input validation; unknown mode is an error, never silently divider.
- Form shows only the fields the selected mode needs; mode change reloads the page
  (no JavaScript required); results/errors state which mode they belong to.

## Non-goals

- No SPICE, load line, AC/transient, bypass capacitors.
- No new unit-test suite and no Playwright automation script (course rule); the
  existing 24 Lab 02 tests are kept as regression tests.
- No changes to Lab 1 files or to `lab02/`.

## Constraints

- Python ≥ 3.10 (machine: 3.14.2), Flask 3.1.3, `unittest` only.
- `dc_bias.py` is pure engineering logic: no Flask/HTML imports.
- UI text English, error/warning messages Thai, identifiers English (Lab 02 AGENTS.md).
- Resistances entered in kΩ and converted to Ω once at the HTTP boundary.
- Out of forward-active (IB ≤ 0 or VCE < 0.2 V) → warning, not an error.

## Approaches considered

1. **New `lab03/` folder copied from `lab02/`** (chosen) — preserves Lab 02 evidence
   and its 24 passing tests, matches the repo's per-lab folder layout, root README
   lists labs.
2. Edit `lab02/` in place — no duplication, but rewrites the submitted Lab 02 and its
   evidence; rejected.
3. Rebuild as a new app — explicitly forbidden by the lab sheet ("ไม่ต้องทำเว็บใหม่");
   rejected.

## Design

- `lab03/dc_bias.py`
  - keep `kohm_to_ohm`, `_to_float`, `calculate_dc_bias` behavior
  - add `calculate_fixed_bias(vcc, rb, rc, beta, vbe)` and
    `calculate_emitter_bias(vcc, rb, rc, re, beta, vbe)`
  - shared helpers `_require_positive`, `_operating_point`, `_region`
  - fixed/emitter return `vth=None, rth=None`; fixed returns `ve=0`
- `lab03/app.py`
  - `MODES`, `MODE_LABELS`, per-mode field lists/defaults
  - `GET /?mode=…` renders that mode's form; unknown `mode` in query falls back to
    divider (a query typo is not a calculation)
  - `POST /calculate` dispatches on `form["mode"]` (default `divider` when absent,
    for Lab 02 compatibility); unknown mode → Thai error
- `lab03/templates/index.html`
  - mode `<select>` + "Load form" (GET) form
  - hidden `mode` in the calculate form; conditional fields and schematic parts
  - results header shows the mode label
- `lab03/tests/*` unchanged except Lab-03 branding strings in `test_web.py`
- `lab03/docs/validation.md` — independent hand calculations + A1–A5 browser run
- `lab03/README.md` and root `README.md` updated

## Verification

- `python -m unittest discover -s lab03/tests -t lab03 -v` → 24 tests pass
- Flask on `127.0.0.1:5000`, cases A1–A5 run through the OpenCode Browser tool
  (Playwright MCP unavailable: no Node/npx on this machine), recorded with
  screenshot + visible text in `lab03/docs/validation.md`
