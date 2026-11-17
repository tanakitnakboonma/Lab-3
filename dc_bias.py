"""DC bias calculations for an NPN common-emitter stage.

Pure engineering logic: this module knows nothing about Flask, HTML or HTTP.
All function arguments and return values use SI units (V, A, ohm).
"""

import math

VCE_SATURATION = 0.2


def _to_float(label, value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} ต้องเป็นตัวเลข") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} ต้องเป็นจำนวนจำกัด")
    return number


def _require_positive(label, value):
    number = _to_float(label, value)
    if number <= 0:
        raise ValueError(f"{label} ต้องมากกว่าศูนย์")
    return number


def kohm_to_ohm(value_kohm, label="ความต้านทาน"):
    """แปลง kΩ เป็น Ω (รับ str หรือ number)"""
    value_ohm = _to_float(label, value_kohm) * 1000
    if not math.isfinite(value_ohm):
        raise ValueError(f"{label} ต้องเป็นจำนวนจำกัด")
    if value_ohm <= 0:
        raise ValueError(f"{label} ต้องมากกว่าศูนย์ (kΩ)")
    return value_ohm


def _region(ib, vce, cutoff_condition="VCC ≤ VBE"):
    """จัดโหมดการทำงานจากสมการ forward-active (ไม่แก้สมการใหม่)"""
    if ib <= 0:
        return "Cutoff", (f"{cutoff_condition} หรือ IB ≤ 0: อยู่ในโหมด Cutoff "
                          "ค่าที่แสดงมาจากสมการ forward-active และไม่ใช่ค่าที่ใช้ได้จริง")
    if vce < VCE_SATURATION:
        return "Saturation", (f"VCE < {VCE_SATURATION} V: อยู่ในโหมด Saturation หรือใกล้เคียง "
                              "ผลจาก forward-active approximation ไม่น่าเชื่อถือ")
    return "Forward Active", ""


def _operating_point(vcc, rc, beta, vbe, ib, re):
    """คำนวณกระแส/แรงดันที่เหลือจาก IB แล้วคืน dict ผลลัพธ์มาตรฐาน"""
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    region, warning = _region(ib, vce)

    return {
        "vth": None,
        "rth": None,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "region": region,
        "warning": warning,
    }


def calculate_fixed_bias(vcc, rb, rc, beta, vbe):
    """Fixed Bias: RB จาก VCC ไป Base, Emitter ต่อลงกราวด์ (VE = 0)"""
    vcc = _require_positive("VCC", vcc)
    rb = _require_positive("RB", rb)
    rc = _require_positive("RC", rc)
    beta = _require_positive("β", beta)
    vbe = _to_float("VBE", vbe)
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")

    ib = (vcc - vbe) / rb
    return _operating_point(vcc, rc, beta, vbe, ib, 0.0)


def calculate_emitter_bias(vcc, rb, rc, re, beta, vbe):
    """Emitter Bias แบบแหล่งจ่ายเดียว: RB จาก VCC ไป Base, RE จาก Emitter ลงกราวด์"""
    vcc = _require_positive("VCC", vcc)
    rb = _require_positive("RB", rb)
    rc = _require_positive("RC", rc)
    re = _require_positive("RE", re)
    beta = _require_positive("β", beta)
    vbe = _to_float("VBE", vbe)
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")

    ib = (vcc - vbe) / (rb + (beta + 1) * re)
    return _operating_point(vcc, rc, beta, vbe, ib, re)


def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe):
    """Voltage Divider Bias: R1 จาก VCC ไป Base, R2 จาก Base ลงกราวด์, RE จาก Emitter ลงกราวด์"""
    vcc = _require_positive("VCC", vcc)
    r1 = _require_positive("R1", r1)
    r2 = _require_positive("R2", r2)
    rc = _require_positive("RC", rc)
    re = _require_positive("RE", re)
    beta = _require_positive("β", beta)
    vbe = _to_float("VBE", vbe)
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ib = (vth - vbe) / (rth + (beta + 1) * re)

    result = _operating_point(vcc, rc, beta, vbe, ib, re)
    result["vth"] = vth
    result["rth"] = rth
    if vth <= vbe or ib <= 0:
        result["region"] = "Cutoff"
        result["warning"] = ("VTH ≤ VBE หรือ IB ≤ 0: อยู่ในโหมด Cutoff "
                             "ค่าที่แสดงมาจากสมการ forward-active และไม่ใช่ค่าที่ใช้ได้จริง")
    return result
