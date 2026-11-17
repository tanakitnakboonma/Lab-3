from flask import Flask, render_template, request

from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
    kohm_to_ohm,
)

app = Flask(__name__)

MODES = ("divider", "fixed", "emitter")

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

DEFAULTS = {
    "divider": {
        "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
        "re": "1", "beta": "100", "vbe": "0.70",
    },
    "fixed": {
        "vcc": "12", "rb": "1000", "rc": "2.2", "beta": "100", "vbe": "0.70",
    },
    "emitter": {
        "vcc": "12", "rb": "1000", "rc": "2.2", "re": "1",
        "beta": "100", "vbe": "0.70",
    },
}

FIELDS = {mode: tuple(defaults) for mode, defaults in DEFAULTS.items()}


def _render(mode, form, result=None, error=None):
    return render_template(
        "index.html",
        form=form,
        result=result,
        error=error,
        mode=mode,
        mode_label=MODE_LABELS.get(mode, ""),
        modes=[(value, MODE_LABELS[value]) for value in MODES],
    )


def _calculate(mode, form):
    if mode == "divider":
        return calculate_dc_bias(
            vcc=form["vcc"],
            r1=kohm_to_ohm(form["r1"], "R1"),
            r2=kohm_to_ohm(form["r2"], "R2"),
            rc=kohm_to_ohm(form["rc"], "RC"),
            re=kohm_to_ohm(form["re"], "RE"),
            beta=form["beta"],
            vbe=form["vbe"],
        )
    if mode == "fixed":
        return calculate_fixed_bias(
            vcc=form["vcc"],
            rb=kohm_to_ohm(form["rb"], "RB"),
            rc=kohm_to_ohm(form["rc"], "RC"),
            beta=form["beta"],
            vbe=form["vbe"],
        )
    if mode == "emitter":
        return calculate_emitter_bias(
            vcc=form["vcc"],
            rb=kohm_to_ohm(form["rb"], "RB"),
            rc=kohm_to_ohm(form["rc"], "RC"),
            re=kohm_to_ohm(form["re"], "RE"),
            beta=form["beta"],
            vbe=form["vbe"],
        )
    raise ValueError(f"ไม่รู้จักโหมดวงจร: {mode}")


@app.get("/")
def index():
    mode = request.args.get("mode", "divider")
    if mode not in MODES:
        mode = "divider"
    return _render(mode, DEFAULTS[mode])


@app.post("/calculate")
def calculate():
    mode = request.form.get("mode", "divider")
    if mode not in MODES:
        error = f"ไม่รู้จักโหมดวงจร: {mode or '(ว่าง)'} กรุณาเลือกโหมดจากรายการ"
        return _render("divider", DEFAULTS["divider"], error=error)

    form = {field: request.form.get(field, "") for field in FIELDS[mode]}
    try:
        result = _calculate(mode, form)
    except ValueError as error:
        return _render(mode, form, error=str(error))

    return _render(mode, form, result=result)
