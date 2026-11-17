# Lab 03 BJT Bias Modes — Implementation Plan

**Goal:** Add Fixed Bias and Emitter Bias to the Lab 02 Flask app in a new `lab03/` folder, keeping Voltage Divider results identical.

**Architecture:** Pure math in `dc_bias.py` (three functions, one result-dict shape), HTTP dispatch + unit conversion in `app.py`, server-rendered Jinja form in `templates/index.html`. No JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-bjt-bias-design.md`
**Course sheet:** `lab03/docs/lab03-assignment.html`

## Global Constraints

- Python ≥ 3.10, Flask 3.1.3, `unittest` only; no new test files.
- `dc_bias.py` must not import Flask.
- UI English, errors/warnings Thai, identifiers English.
- Resistances are kΩ on the form, Ω inside `dc_bias.py`.
- Do not touch `electrical.py`, `test_electrical.py`, or `lab02/`.
- Never commit `.venv/`, `.env`, `__pycache__/`.

## Review Focus

- `RB = 0` in Fixed/Emitter → error, page must not crash (A5).
- Mode switched but stale previous result still shown → results must name the mode.
- Unknown `mode` value must error, not fall back to divider.
- Divider with Lab 02 A1 inputs → identical numbers (regression).
- `mode` missing from form → treated as divider so Lab 02 tests keep passing.

---

### Task 1: Create `lab03/` from `lab02/`

**Files:** copy tree, drop `__pycache__/`

- [ ] Copy `lab02/` → `lab03/`, delete `lab03/__pycache__/`
- [ ] Copy lab sheet to `lab03/docs/lab03-assignment.html`
- [ ] Verify: `python -m unittest discover -s lab03/tests -t lab03 -v` → 24 pass

### Task 2: Engineering functions in `dc_bias.py`

**Interfaces (produced):**
```python
calculate_fixed_bias(vcc, rb, rc, beta, vbe) -> dict
calculate_emitter_bias(vcc, rb, rc, re, beta, vbe) -> dict
```
Both return `{vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warning}` with SI units;
`vth`/`rth` are `None`; fixed bias has `ve == 0` and `vb == vbe`.

- [ ] Add `_require_positive(label, value)`; reuse in all three functions
- [ ] Add `_operating_point(vcc, rc, beta, vbe, ib, re)` and `_region(ib, vce)`
- [ ] Fixed: `IB = (VCC − VBE) / RB`, `VE = 0`, `VB = VBE`, `VCE = VC`
- [ ] Emitter: `IB = (VCC − VBE) / (RB + (β+1)·RE)`, `VE = IE·RE`
- [ ] Run `tests/test_dc_bias.py` → still 24 total pass (divider untouched)

### Task 3: Mode dispatch in `app.py`

**Interfaces (consumed):** the three `calculate_*` functions above.

- [ ] `MODES = ("divider", "fixed", "emitter")`, `MODE_LABELS`, per-mode field tuples and defaults
- [ ] `GET /` reads `request.args.get("mode", "divider")`, unknown → divider, renders that mode's fields
- [ ] `POST /calculate`: unknown mode → Thai error; per-mode `kohm_to_ohm` conversion; dispatch via `if/elif`
- [ ] Missing `mode` → `divider` (Lab 02 compatibility)
- [ ] Verify all three modes with `app.test_client()` (valid + `rb=0`)

### Task 4: Template

- [ ] Mode select + "Load form" (GET) above the calculate form
- [ ] Hidden `mode`; conditional fields: divider `r1 r2 re`, fixed `rb`, emitter `rb re`
- [ ] Schematic: RB branch for fixed/emitter, R2 only for divider, RE except fixed
- [ ] Results panel shows `Mode: <label>` and existing rows; error panel unchanged
- [ ] Update `test_web.py` branding assertions only (`Week 3 Goal`)

### Task 5: Browser acceptance A1–A5

Expected (independent hand calculation, VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.70 V):

| Case | Input | IC (mA) | VCE (V) |
|---|---|---|---|
| A1 Divider | R1 100, R2 22, RE 1 kΩ | 1.2299 | 8.0521 |
| A2 Fixed | RB 1000 kΩ | 1.1300 | 9.5140 |
| A3 Emitter | RB 1000, RE 1 kΩ | 1.0263 | 8.7055 |
| A4 Emitter | RB 1000, RE 2 kΩ | 0.9384 | 8.0402 |
| A5 Fixed | RB 0 | error, page healthy | — |

- [ ] Start `python -m flask --app app run` in `lab03/`
- [ ] Run A1–A5 with browser tools, capture snapshot text + one screenshot
- [ ] Record method = OpenCode Browser (Playwright MCP NOT RUN: no Node/npx)

### Task 6: Docs, commit

- [ ] `lab03/docs/validation.md` — hand calc + A1–A5 table + method note
- [ ] `lab03/docs/design-note.md` — three modes, formulas, units
- [ ] `lab03/README.md` — modes, formulas, run/test, validation links
- [ ] Root `README.md` — Lab 03 section
- [ ] `git status` / `git diff --staged` check, commit on `main`
