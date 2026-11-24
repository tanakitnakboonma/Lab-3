import math

from flask import Flask, render_template, request

import charts
import spice_engine
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

WORKSPACES = ("bias", "simulator")
ANALYSES = spice_engine.ANALYSES
ANALYSIS_LABELS = {
    "dc": "DC Operating Point (.op)",
    "ac": "AC Frequency Response (.ac)",
    "tran": "Transient Response (.tran)",
}

SPICE_DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "amplitude": "10",
    "frequency": "1",
    "duration": "5",
}

CIRCUIT_FIELDS = ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout")
SIM_FIELDS = {
    "dc": CIRCUIT_FIELDS,
    "ac": CIRCUIT_FIELDS + ("frequency",),
    "tran": CIRCUIT_FIELDS + ("amplitude", "frequency", "duration"),
}
KOHM_FIELDS = ("r1", "r2", "rc", "re", "rl")
MICROFARAD_FIELDS = ("cin", "cout")

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "rl": "RL",
    "cin": "Cin",
    "cout": "Cout",
    "amplitude": "Amplitude",
    "frequency": "Frequency",
    "duration": "Duration",
}

FIELD_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "rl": "kΩ",
    "cin": "µF",
    "cout": "µF",
    "amplitude": "mV peak",
    "frequency": "kHz",
    "duration": "ms",
}


def _render(
    mode,
    form,
    result=None,
    error=None,
    workspace="bias",
    analysis="dc",
    sim_form=None,
    sim_result=None,
    sim_error=None,
    analytical=None,
    charts_by_name=None,
    mode_label=None,
    analysis_label_override=None,
):
    if workspace not in WORKSPACES:
        workspace = "bias"
    if analysis not in ANALYSES:
        analysis = "dc"
    return render_template(
        "index.html",
        form=form,
        result=result,
        error=error,
        mode=mode,
        mode_label=mode_label or MODE_LABELS.get(mode, "Unknown"),
        modes=[(value, MODE_LABELS[value]) for value in MODES],
        workspace=workspace,
        workspaces=(("bias", "DC Bias (Lab 3)"), ("simulator", "CE Simulator (Lab 4)")),
        analysis=analysis,
        analysis_label=analysis_label_override or ANALYSIS_LABELS[analysis],
        analyses=[(value, ANALYSIS_LABELS[value]) for value in ANALYSES],
        sim_form=sim_form if sim_form is not None else dict(SPICE_DEFAULTS),
        sim_result=sim_result,
        sim_error=sim_error,
        analytical=analytical,
        charts=charts_by_name or {},
        field_labels=FIELD_LABELS,
        field_units=FIELD_UNITS,
        sim_fields=SIM_FIELDS[analysis],
        engine_name=spice_engine.ENGINE_NAME,
        model_name=spice_engine.MODEL_NAME,
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


def _positive(label, value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} ต้องเป็นตัวเลข") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} ต้องเป็นจำนวนจำกัด")
    if number <= 0:
        raise ValueError(f"{label} ต้องมากกว่าศูนย์")
    return number


def _strict_positive(label, value):
    """Reject zero as well; kept separate for engine-provided feedback."""
    return _positive(label, value)


def _simulation_values(analysis, form):
    """Convert the displayed units (kΩ/µF/mV/kHz/ms) into SI before the adapter."""
    values = {name: _positive(FIELD_LABELS[name], form[name]) for name in SIM_FIELDS[analysis]}
    si = {"vcc": values["vcc"]}
    for name in KOHM_FIELDS:
        si[name] = values[name] * 1000.0
    for name in MICROFARAD_FIELDS:
        si[name] = values[name] * 1e-6
    si["amplitude_v"] = values.get("amplitude", float(SPICE_DEFAULTS["amplitude"])) * 1e-3
    si["frequency_hz"] = values.get("frequency", float(SPICE_DEFAULTS["frequency"])) * 1e3
    si["duration_s"] = values.get("duration", float(SPICE_DEFAULTS["duration"])) * 1e-3
    return si


def _analytical_reference(form):
    """Lab 3 approximation, shown only as a clearly labelled comparison."""
    return calculate_dc_bias(
        vcc=form["vcc"],
        r1=kohm_to_ohm(form["r1"], "R1"),
        r2=kohm_to_ohm(form["r2"], "R2"),
        rc=kohm_to_ohm(form["rc"], "RC"),
        re=kohm_to_ohm(form["re"], "RE"),
        beta=100,
        vbe=0.70,
    )


def _make_charts(analysis, result):
    data = result["data"]
    if analysis == "ac":
        return {
            "gain": charts.svg_line_chart(
                "Voltage gain magnitude",
                [{"name": "|Vout/Vin|", "color": "#0e8f84",
                  "x": data["frequency_hz"], "y": data["gain_db"]}],
                "Frequency (Hz, log scale)",
                "Gain (dB)",
                x_log=True,
            ),
            "phase": charts.svg_line_chart(
                "Voltage gain phase",
                [{"name": "Phase(Vout/Vin)", "color": "#1d6a99",
                  "x": data["frequency_hz"], "y": data["phase_deg"]}],
                "Frequency (Hz, log scale)",
                "Phase (degrees)",
                x_log=True,
            ),
        }
    if analysis == "tran":
        return {
            "waveform": charts.svg_line_chart(
                "Input and output waveforms",
                [
                    {"name": "Vin at base", "color": "#0e8f84",
                     "x": data["time_s"], "y": data["vin_v"]},
                    {"name": "Vout at RL", "color": "#b2622f",
                     "x": data["time_s"], "y": data["vout_v"]},
                ],
                "Time (s)",
                "Voltage (V)",
            ),
        }
    return {}


@app.get("/")
def index():
    requested_mode = request.args.get("mode", "divider")
    mode = requested_mode if requested_mode in MODES else "divider"
    error = None
    label = None
    if requested_mode not in MODES:
        error = (
            f"ไม่รู้จักโหมดวงจร: {requested_mode or '(ว่าง)'} "
            "กรุณาเลือกโหมดจากรายการ"
        )
        label = f"Unknown ({requested_mode or '(ว่าง)'})"

    workspace = request.args.get("workspace", "bias")
    if workspace not in WORKSPACES:
        workspace = "bias"
    analysis = request.args.get("analysis", "dc")
    sim_error = None
    if analysis not in ANALYSES:
        sim_error = (
            f"ไม่รู้จักโหมดการวิเคราะห์: {analysis or '(ว่าง)'} "
            "กรุณาเลือก DC, AC หรือ Transient"
        )
        analysis = "dc"

    return _render(
        mode,
        DEFAULTS[mode],
        error=error,
        mode_label=label,
        workspace=workspace,
        analysis=analysis,
        sim_error=sim_error,
    )


@app.post("/calculate")
def calculate():
    mode = request.form.get("mode", "divider")
    if mode not in MODES:
        error = f"ไม่รู้จักโหมดวงจร: {mode or '(ว่าง)'} กรุณาเลือกโหมดจากรายการ"
        return _render(
            "divider",
            DEFAULTS["divider"],
            error=error,
            mode_label=f"Unknown ({mode or '(ว่าง)'})",
        )

    form = {field: request.form.get(field, "") for field in FIELDS[mode]}
    try:
        result = _calculate(mode, form)
    except ValueError as error:
        return _render(mode, form, error=str(error))

    return _render(mode, form, result=result)


@app.post("/simulate")
def simulate():
    analysis = request.form.get("analysis", "dc")
    if analysis not in ANALYSES:
        error = (
            f"ไม่รู้จักโหมดการวิเคราะห์: {analysis or '(ว่าง)'} "
            "กรุณาเลือก DC, AC หรือ Transient"
        )
        return _render(
            "divider",
            DEFAULTS["divider"],
            workspace="simulator",
            analysis="dc",
            analysis_label_override=f"Unknown ({analysis or '(ว่าง)'})",
            sim_error=error,
        )

    sim_form = {
        field: request.form.get(field, SPICE_DEFAULTS[field])
        for field in SIM_FIELDS[analysis]
    }
    try:
        si_values = _simulation_values(analysis, sim_form)
        result = spice_engine.run_analysis(analysis, si_values)
        analytical = _analytical_reference(sim_form) if analysis == "dc" else None
        chart_data = _make_charts(analysis, result)
    except (ValueError, spice_engine.SpiceError) as error:
        return _render(
            "divider",
            DEFAULTS["divider"],
            workspace="simulator",
            analysis=analysis,
            sim_form=sim_form,
            sim_error=str(error),
        )

    return _render(
        "divider",
        DEFAULTS["divider"],
        workspace="simulator",
        analysis=analysis,
        sim_form=sim_form,
        sim_result=result,
        analytical=analytical,
        charts_by_name=chart_data,
    )
