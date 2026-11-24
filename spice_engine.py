"""ngspice adapter for the Lab 04 CE voltage-divider reference circuit.

Pure engineering code: no Flask, no HTML, no HTTP.  Every circuit value passed
to this module is in SI units (V, A, ohm, F, Hz, s).  The adapter validates the
values, writes an isolated netlist, starts ngspice as a list-argument subprocess
with a timeout, and parses the real output files.  Failures are reported as
SpiceError instead of returning old/partial data as a successful result.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ENGINE_NAME = "ngspice"
MODEL_NAME = "LAB_NPN"
ANALYSES = ("dc", "ac", "tran")

NETLIST_FILE = "circuit.cir"
LOG_FILE = "run.log"
RAW_FILE = "run.raw"
DC_DATA_FILE = "op_data.txt"
AC_DATA_FILE = "ac_data.txt"
TRAN_DATA_FILE = "tran_data.txt"

AC_START_HZ = 1.0
AC_STOP_HZ = 10_000_000.0
DEFAULT_TIMEOUT_SECONDS = 30
MAX_TRAN_POINTS = 20_000

# Teaching Gummel-Poon model.  It is deliberately named LAB_NPN rather than a
# commercial part number: the parameters are printed below in the netlist and
# in the UI so a run can be reproduced without guessing a device library.
MODEL_LINE = (
    ".model LAB_NPN NPN("
    "IS=1e-14 BF=100 BR=1 VAF=100 "
    "ISE=1e-14 NE=1.5 ISC=1e-14 NC=1.2 "
    "RB=10 RC=1 RE=0 "
    "CJC=2p CJE=3p TF=40n TR=400n)"
)

_NUMBER_RE = re.compile(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$")


class SpiceError(Exception):
    """Validation, engine, run or result-parsing failure (message in Thai)."""


def _positive(label: str, value, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SpiceError(f"{label} ต้องเป็นตัวเลข") from error
    if not math.isfinite(number):
        raise SpiceError(f"{label} ต้องเป็นจำนวนจำกัด")
    if number < low:
        raise SpiceError(f"{label} ต้องไม่น้อยกว่า {low:g}")
    if number > high:
        raise SpiceError(f"{label} ต้องไม่มากกว่า {high:g}")
    return number


def validate_parameters(values) -> dict:
    """Check every SI input and return a clean float dict for the netlist."""
    return {
        "vcc": _positive("VCC", values.get("vcc"), 0.1, 100.0),
        "r1": _positive("R1", values.get("r1"), 1.0, 1e9),
        "r2": _positive("R2", values.get("r2"), 1.0, 1e9),
        "rc": _positive("RC", values.get("rc"), 1.0, 1e9),
        "re": _positive("RE", values.get("re"), 1.0, 1e9),
        "rl": _positive("RL", values.get("rl"), 1.0, 1e9),
        "cin": _positive("Cin", values.get("cin"), 1e-12, 1e-3),
        "cout": _positive("Cout", values.get("cout"), 1e-12, 1e-3),
        "amplitude_v": _positive("Amplitude", values.get("amplitude_v"), 1e-9, 100.0),
        "frequency_hz": _positive("Frequency", values.get("frequency_hz"), 1.0, 1e9),
        "duration_s": _positive("Duration", values.get("duration_s"), 1e-6, 1.0),
    }


def _fmt(value: float) -> str:
    """Numeric-only formatting keeps form text out of the SPICE command path."""
    return f"{value:.10g}"


def _tran_step(duration: float, frequency: float) -> float:
    by_points = duration / MAX_TRAN_POINTS
    by_cycles = 1.0 / (frequency * 50.0)
    return max(by_points, by_cycles)


def build_netlist(analysis: str, values: dict) -> str:
    """Return a netlist containing only the requested analysis directive."""
    if analysis not in ANALYSES:
        raise SpiceError(f"ไม่รู้จักการวิเคราะห์: {analysis}")

    p = validate_parameters(values)
    lines = [
        "* Lab 04 - CE voltage-divider amplifier (reference circuit)",
        f"* BJT model: {MODEL_NAME} (teaching Gummel-Poon, not a commercial part)",
        f"VCC vcc 0 DC {_fmt(p['vcc'])}",
        (
            f"VIN src 0 DC 0 AC 1 "
            f"SIN(0 {_fmt(p['amplitude_v'])} {_fmt(p['frequency_hz'])})"
        ),
        f"R1 vcc base {_fmt(p['r1'])}",
        f"R2 base 0 {_fmt(p['r2'])}",
        f"RC vcc collector {_fmt(p['rc'])}",
        f"RE emitter 0 {_fmt(p['re'])}",
        f"CIN src base {_fmt(p['cin'])}",
        f"COUT collector load {_fmt(p['cout'])}",
        f"RL load 0 {_fmt(p['rl'])}",
        "Q1 collector base emitter LAB_NPN",
        MODEL_LINE,
        ".options numdgt=9",
        ".control",
        "set noaskquit",
        "set wr_vecnames",
        "set wr_singlescale",
    ]

    if analysis == "dc":
        lines.extend(
            [
                "op",
                "let ib_a = @q1[ib]",
                "let ic_a = @q1[ic]",
                f"wrdata {DC_DATA_FILE} v(base) v(emitter) v(collector) ib_a ic_a",
                "print v(base) v(emitter) v(collector) @q1[ib] @q1[ic]",
            ]
        )
    elif analysis == "ac":
        lines.extend(
            [
                f"ac dec 20 {_fmt(AC_START_HZ)} {_fmt(AC_STOP_HZ)}",
                # Vin reference is v(base), i.e. after Cin at the transistor
                # base node.  Vout is v(load), after Cout across RL.
                "let gain_db = vdb(load) - vdb(base)",
                # ngspice vp() returns radians here; convert explicitly so the
                # plotted/summarised phase is genuinely in degrees.
                "let phase_deg = (vp(load) - vp(base)) * 57.29577951308232",
                (
                    f"wrdata {AC_DATA_FILE} frequency gain_db phase_deg "
                    "vdb(base) vdb(load)"
                ),
            ]
        )
    else:
        step = _tran_step(p["duration_s"], p["frequency_hz"])
        lines.extend(
            [
                f"tran {_fmt(step)} {_fmt(p['duration_s'])} 0 {_fmt(step)}",
                f"wrdata {TRAN_DATA_FILE} time v(base) v(load)",
            ]
        )

    lines.extend([".endc", ".end", ""])
    return "\n".join(lines)


def find_ngspice(explicit: str | None = None) -> str:
    """Resolve the external executable without ever invoking a shell."""
    candidates = [explicit, os.environ.get("NGSPICE_BINARY"), shutil.which("ngspice")]
    home = Path.home()
    candidates.extend(
        [
            r"C:\Program Files\ngspice\Spice64\bin\ngspice.exe",
            r"C:\Program Files (x86)\ngspice\Spice64\bin\ngspice.exe",
            r"C:\ProgramData\chocolatey\lib\ngspice\tools\Spice64\bin\ngspice.exe",
            str(home / "AppData" / "Local" / "ngspice-47" / "Spice64" / "bin" / "ngspice.exe"),
            str(home / "AppData" / "Local" / "ngspice-conda" / "app" / "Library" / "bin" / "ngspice_con.exe"),
            str(home / "AppData" / "Local" / "ngspice-conda" / "app" / "Library" / "bin" / "ngspice.exe"),
            "/usr/local/bin/ngspice",
            "/usr/bin/ngspice",
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise SpiceError(
        "ไม่พบ ngspice ให้รัน กรุณาติดตั้งแล้วเพิ่มใน PATH "
        "หรือตั้งค่า NGSPICE_BINARY ให้ชี้ถึง executable ของ ngspice"
    )


def _looks_numeric(token: str) -> bool:
    return bool(_NUMBER_RE.match(token.strip().lstrip("#")))


def _normalise_header(header: list[str]) -> list[str]:
    return [re.sub(r"[^a-z0-9]+", "", name.lower().lstrip("#")) for name in header]


def _column_index(header: list[str] | None, candidates: tuple[str, ...], default: int) -> int:
    if not header:
        return default
    normalised = _normalise_header(header)
    for candidate in candidates:
        wanted = re.sub(r"[^a-z0-9]+", "", candidate.lower())
        for index, name in enumerate(normalised):
            if wanted in name or name in wanted:
                return index
    return default


def _read_table(path: Path, minimum_columns: int) -> tuple[list[str] | None, list[list[float]]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise SpiceError(f"อ่านผลการจำลองไม่ได้: {path.name}") from error

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise SpiceError(f"ไฟล์ผลการจำลอง {path.name} ว่างเปล่า")

    header = None
    start = 0
    first_tokens = lines[0].split()
    if first_tokens and not all(_looks_numeric(token) for token in first_tokens):
        header = [token.strip().lstrip("#") for token in first_tokens]
        start = 1

    data_lines = lines[start:]
    if not data_lines:
        raise SpiceError(f"ไฟล์ผลการจำลอง {path.name} ไม่มีข้อมูลตัวเลข")

    widths = [len(line.split()) for line in data_lines[:20]]
    width = max(widths)
    offset = 0
    if header and width == len(header):
        offset = 0
    elif header and width == len(header) + 1:
        offset = 1  # wrdata may prepend a row index
    else:
        header = None

    rows: list[list[float]] = []
    for line in data_lines:
        parts = line.split()[offset:]
        if len(parts) < minimum_columns:
            continue
        try:
            values = [float(part) for part in parts]
        except ValueError:
            continue
        if all(math.isfinite(value) for value in values):
            rows.append(values)

    if not rows:
        raise SpiceError(f"ไฟล์ผลการจำลอง {path.name} ไม่มีข้อมูลตัวเลขที่ใช้ได้")
    return header, rows


def _parse_dc_log(log: str) -> dict | None:
    nodes = {}
    for name, key in (("base", "vb"), ("emitter", "ve"), ("collector", "vc")):
        match = re.search(rf"^\s*{name}\s+([-+0-9.eE]+)\s*$", log, re.MULTILINE)
        if not match:
            return None
        nodes[key] = float(match.group(1))

    ib_match = re.search(r"\bIB\s*:\s*([-+0-9.eE]+)", log)
    ic_match = re.search(r"\bIC\s*:\s*([-+0-9.eE]+)", log)
    if not ib_match or not ic_match:
        return None
    nodes["ib"] = float(ib_match.group(1))
    nodes["ic"] = float(ic_match.group(1))
    nodes["currents_source"] = "ngspice .op device currents (log)"
    return nodes


def _parse_dc(workdir: Path, params: dict, log: str) -> dict:
    data = None
    data_file = workdir / DC_DATA_FILE
    if data_file.exists():
        header, rows = _read_table(data_file, 5)
        last = rows[-1]
        ib_index = _column_index(header, ("ib_a", "ib", "base current"), 3)
        ic_index = _column_index(header, ("ic_a", "ic", "collector current"), 4)
        vb_index = _column_index(header, ("vbase", "v(base)", "base"), 0)
        ve_index = _column_index(header, ("vemitter", "v(emitter)", "emitter"), 1)
        vc_index = _column_index(header, ("vcollector", "v(collector)", "collector"), 2)
        indices = {vb_index, ve_index, vc_index, ib_index, ic_index}
        if len(indices) == 5 and max(indices) < len(last):
            data = {
                "vb": last[vb_index],
                "ve": last[ve_index],
                "vc": last[vc_index],
                "ib": last[ib_index],
                "ic": last[ic_index],
                "currents_source": "ngspice .op device currents (wrdata)",
            }

    if data is None:
        data = _parse_dc_log(log)

    if data is None:
        raise SpiceError(
            "ngspice รันสำเร็จ แต่ไม่พบ VB/VE/VC หรือกระแส Q1 ในผล .op "
            "จึงไม่นำค่าใดมาแสดง"
        )

    if not all(math.isfinite(data[key]) for key in ("vb", "ve", "vc", "ib", "ic")):
        raise SpiceError("ผล .op มีค่าไม่จำกัด (NaN/Inf) จึงไม่นำค่าใดมาแสดง")

    data["ie"] = data["ib"] + data["ic"]
    data["vbe"] = data["vb"] - data["ve"]
    data["vce"] = data["vc"] - data["ve"]
    data["ic_from_rc_ohm"] = (params["vcc"] - data["vc"]) / params["rc"]
    data["vb_source_node_v"] = params["amplitude_v"]  # provenance for transient source
    return data


def _unwrap_degrees(values: list[float]) -> list[float]:
    result = list(values)
    for index in range(1, len(result)):
        while result[index] - result[index - 1] > 180:
            result[index] -= 360
        while result[index] - result[index - 1] < -180:
            result[index] += 360
    return result


def _interpolate_log(freqs: list[float], values: list[float], target: float) -> float | None:
    if target < freqs[0] or target > freqs[-1]:
        return None
    for index in range(1, len(freqs)):
        if freqs[index] >= target:
            ratio = math.log(target / freqs[index - 1]) / math.log(freqs[index] / freqs[index - 1])
            return values[index - 1] + ratio * (values[index] - values[index - 1])
    return None


def _cutoffs(freqs: list[float], gains: list[float]) -> dict:
    target = max(gains) - 3.0
    crossings: list[float] = []
    for index in range(1, len(freqs)):
        first, second = gains[index - 1] - target, gains[index] - target
        if first == 0:
            crossings.append(freqs[index - 1])
        elif first * second < 0:
            ratio = abs(first) / (abs(first) + abs(second))
            crossings.append(
                math.exp(
                    math.log(freqs[index - 1])
                    + ratio * (math.log(freqs[index]) - math.log(freqs[index - 1]))
                )
            )

    if len(crossings) >= 2:
        return {
            "reference_db": max(gains),
            "threshold_db": target,
            "lower_hz": crossings[0],
            "upper_hz": crossings[-1],
            "note": "",
        }
    if len(crossings) == 1:
        side = "lower_hz" if gains[0] < target < gains[-1] else "upper_hz"
        return {
            "reference_db": max(gains),
            "threshold_db": target,
            side: crossings[0],
            "note": "อีกจุดตัด -3 dB ไม่อยู่ในช่วง sweep",
        }
    return {
        "reference_db": max(gains),
        "threshold_db": target,
        "note": "not determined in sweep range",
    }


def _parse_ac(workdir: Path, params: dict) -> tuple[dict, dict]:
    data_file = workdir / AC_DATA_FILE
    header, rows = _read_table(data_file, 5)
    freq_i = _column_index(header, ("frequency", "freq"), 0)
    gain_i = _column_index(header, ("gaindb", "gain_db", "gain"), 1)
    phase_i = _column_index(header, ("phasedeg", "phase_deg", "phase"), 2)
    indices = {freq_i, gain_i, phase_i}
    if len(indices) != 3 or max(indices) >= len(rows[0]):
        raise SpiceError("รูปแบบผล .ac ไม่ตรงที่คาด จึงไม่สร้างกราฟ Bode")

    rows.sort(key=lambda row: row[freq_i])
    freqs = [row[freq_i] for row in rows]
    gains = [row[gain_i] for row in rows]
    phases = _unwrap_degrees([row[phase_i] for row in rows])
    if any(value <= 0 for value in freqs):
        raise SpiceError("ผล .ac มีความถี่ไม่เป็นบวก จึงไม่นำค่าใดมาแสดง")

    source_hz = params["frequency_hz"]
    summary = {
        "sweep_start_hz": freqs[0],
        "sweep_stop_hz": freqs[-1],
        "points": len(freqs),
        "max_gain_db": max(gains),
        "gain_at_source_db": _interpolate_log(freqs, gains, source_hz),
        "phase_at_source_deg": _interpolate_log(freqs, phases, source_hz),
        "cutoff": _cutoffs(freqs, gains),
        "vin_reference": "v(base) after Cin",
        "vout_reference": "v(load) across RL after Cout",
    }
    return {"frequency_hz": freqs, "gain_db": gains, "phase_deg": phases}, summary


def _parse_tran(workdir: Path, params: dict) -> tuple[dict, dict]:
    data_file = workdir / TRAN_DATA_FILE
    header, rows = _read_table(data_file, 3)
    time_i = _column_index(header, ("time",), 0)
    vin_i = _column_index(header, ("vbase", "v(base)", "vin"), 1)
    vout_i = _column_index(header, ("vload", "v(load)", "vout"), 2)
    indices = {time_i, vin_i, vout_i}
    if len(indices) != 3 or max(indices) >= len(rows[0]):
        raise SpiceError("รูปแบบผล .tran ไม่ตรงที่คาด จึงไม่สร้างกราฟสัญญาณตามเวลา")

    rows.sort(key=lambda row: row[time_i])
    times = [row[time_i] for row in rows]
    vin = [row[vin_i] for row in rows]
    vout = [row[vout_i] for row in rows]

    tail_start = max(0, int(len(rows) * 0.6))
    tail_in = vin[tail_start:]
    tail_out = vout[tail_start:]
    mean_in = sum(tail_in) / len(tail_in)
    mean_out = sum(tail_out) / len(tail_out)
    covariance = sum((a - mean_in) * (b - mean_out) for a, b in zip(tail_in, tail_out))
    if covariance == 0:
        relation = "undetermined"
    else:
        relation = "inverted (near 180 deg)" if covariance < 0 else "non-inverted"

    summary = {
        "points": len(times),
        "time_stop_s": times[-1],
        "vin_peak_to_peak_v": max(tail_in) - min(tail_in),
        "vout_peak_to_peak_v": max(tail_out) - min(tail_out),
        "phase_relation": relation,
        "vin_reference": "v(base) after Cin",
        "vout_reference": "v(load) across RL after Cout",
    }
    return {"time_s": times, "vin_v": vin, "vout_v": vout}, summary


def _engine_version(log: str) -> str:
    match = re.search(r"ngspice[-\s](\d+(?:\.\d+)?)", log, re.IGNORECASE)
    return f"ngspice {match.group(1)}" if match else ENGINE_NAME


def run_analysis(
    analysis: str,
    values: dict,
    binary: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    working_dir: str | Path | None = None,
) -> dict:
    """Run one real ngspice analysis and return parsed data with provenance."""
    if analysis not in ANALYSES:
        raise SpiceError(f"ไม่รู้จักการวิเคราะห์: {analysis}")
    params = validate_parameters(values)
    netlist = build_netlist(analysis, params)
    executable = find_ngspice(binary)

    def execute(workdir: Path) -> dict:
        # Never let a previous run's files be mistaken for this run's output.
        for stale in (LOG_FILE, RAW_FILE, DC_DATA_FILE, AC_DATA_FILE, TRAN_DATA_FILE):
            (workdir / stale).unlink(missing_ok=True)
        netlist_path = workdir / NETLIST_FILE
        netlist_path.write_text(netlist, encoding="utf-8")
        command = [
            executable,
            "-b",
            "-o",
            LOG_FILE,
            "-r",
            RAW_FILE,
            NETLIST_FILE,
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                shell=False,
            )
        except FileNotFoundError as error:
            raise SpiceError(f"ไม่พบ ngspice ที่ตำแหน่ง {executable}") from error
        except subprocess.TimeoutExpired as error:
            raise SpiceError(
                f"ngspice ใช้เวลาเกิน {timeout:g} วินาที จึงยุติการรัน "
                "และไม่แสดงผลเก่า"
            ) from error
        except OSError as error:
            raise SpiceError(f"เริ่ม ngspice ไม่ได้: {error}") from error

        console = "\n".join(
            part for part in (completed.stdout, completed.stderr) if part
        )
        log_path = workdir / LOG_FILE
        if log_path.exists():
            log = log_path.read_text(encoding="utf-8", errors="replace")
            if console.strip():
                log = f"{log}\n{console}"
        else:
            log = console
        if not log.strip():
            log = "(ngspice ไม่ได้เขียน log)"

        fatal = re.search(
            r"(?im)^\s*(error|fatal error|convergence failed|"
            r"could not find|no such file)",
            log,
        )
        if completed.returncode != 0 or fatal:
            detail = fatal.group(0) if fatal else f"exit code {completed.returncode}"
            raise SpiceError(f"ngspice รันไม่สำเร็จ ({detail}) — {log[-700:]}")

        if analysis == "dc":
            data, summary = _parse_dc(workdir, params, log), {}
        elif analysis == "ac":
            data, summary = _parse_ac(workdir, params)
        else:
            data, summary = _parse_tran(workdir, params)

        return {
            "status": "success",
            "engine": _engine_version(log),
            "model": MODEL_NAME,
            "analysis": analysis,
            "command": command,
            "netlist": netlist,
            "log": log,
            "data": data,
            "summary": summary,
            "parameters": params,
        }

    if working_dir is not None:
        return execute(Path(working_dir))
    with tempfile.TemporaryDirectory(prefix="lab04-ngspice-") as temporary:
        return execute(Path(temporary))
