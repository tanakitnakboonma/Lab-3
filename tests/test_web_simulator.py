import unittest
from unittest.mock import patch

import spice_engine
from app import app

FORM = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
    "rl": "10", "cin": "10", "cout": "10", "amplitude": "10",
    "frequency": "1", "duration": "5",
}


def _base_result(analysis):
    return {
        "status": "success",
        "engine": "ngspice 41",
        "model": spice_engine.MODEL_NAME,
        "analysis": analysis,
        "command": ["ngspice_con.exe", "-b", "circuit.cir"],
        "netlist": "* test netlist\nVCC vcc 0 DC 12\n",
        "log": "ngspice test log",
        "parameters": {
            "vcc": 12.0, "frequency_hz": 1000.0, "amplitude_v": 0.01,
        },
        "summary": {},
        "data": {},
    }


def _dc_result():
    result = _base_result("dc")
    result["data"] = {
        "vb": 1.9454, "ve": 1.2857, "vc": 9.1980,
        "vbe": 0.6597, "vce": 7.9123,
        "ib": 1.2123e-5, "ic": 1.2743e-3, "ie": 1.2864e-3,
        "currents_source": "ngspice .op device currents (wrdata)",
        "ic_from_rc_ohm": 1.2736e-3,
    }
    return result


def _ac_result():
    result = _base_result("ac")
    result["data"] = {
        "frequency_hz": [1.0, 100.0, 1000.0, 10_000.0],
        "gain_db": [0.5, 4.8, 4.86, 4.8],
        "phase_deg": [-2.0, -170.0, -179.9, -175.0],
    }
    result["summary"] = {
        "sweep_start_hz": 1.0,
        "sweep_stop_hz": 10_000.0,
        "points": 4,
        "max_gain_db": 4.86,
        "gain_at_source_db": 4.86,
        "phase_at_source_deg": -179.9,
        "cutoff": {
            "reference_db": 4.86,
            "threshold_db": 1.86,
            "lower_hz": 2.0,
            "upper_hz": 9000.0,
            "note": "",
        },
        "vin_reference": "v(base) after Cin",
        "vout_reference": "v(load) across RL after Cout",
    }
    return result


def _tran_result():
    result = _base_result("tran")
    result["data"] = {
        "time_s": [0.0, 0.001, 0.002, 0.003],
        "vin_v": [1.9, 1.91, 1.9, 1.89],
        "vout_v": [9.2, 9.18, 9.21, 9.22],
    }
    result["summary"] = {
        "points": 4,
        "vin_peak_to_peak_v": 0.02,
        "vout_peak_to_peak_v": 0.04,
        "phase_relation": "inverted (near 180 deg)",
        "vin_reference": "v(base) after Cin",
        "vout_reference": "v(load) across RL after Cout",
    }
    return result


class TestSimulatorPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, analysis="dc", **overrides):
        data = dict(FORM, analysis=analysis)
        data.update(overrides)
        return self.client.post("/simulate", data=data)

    def test_workspace_page_shows_analysis_selector_and_units(self):
        html = self.client.get("/?workspace=simulator").get_data(as_text=True)
        self.assertIn('name="analysis"', html)
        self.assertIn("DC Operating Point (.op)", html)
        self.assertIn("kΩ", html)
        self.assertIn("µF", html)
        self.assertIn("mV peak", html)
        self.assertIn("kHz", html)
        self.assertIn("Waiting for ngspice run", html)

    def test_unknown_analysis_is_rejected_without_engine_call(self):
        with patch("app.spice_engine.run_analysis") as run:
            html = self.post(analysis="bogus").get_data(as_text=True)
        run.assert_not_called()
        self.assertIn("ไม่รู้จักโหมดการวิเคราะห์", html)
        self.assertIn("Simulator mode:", html)
        self.assertIn("Run rejected", html)
        self.assertNotIn("Run status: SUCCESS", html)

    def test_invalid_number_is_rejected_without_engine_call(self):
        with patch("app.spice_engine.run_analysis") as run:
            html = self.post(r1="0").get_data(as_text=True)
        run.assert_not_called()
        self.assertIn('class="error"', html)
        self.assertIn("R1", html)
        self.assertNotIn("Run status: SUCCESS", html)

    def test_si_conversion_happens_at_http_boundary(self):
        with patch("app.spice_engine.run_analysis", return_value=_tran_result()) as run:
            self.post("tran")
        args = run.call_args.args
        self.assertEqual(args[0], "tran")
        self.assertEqual(args[1]["vcc"], 12.0)
        self.assertAlmostEqual(args[1]["r1"], 100_000.0)
        self.assertAlmostEqual(args[1]["cin"], 10e-6)
        self.assertAlmostEqual(args[1]["amplitude_v"], 0.01)
        self.assertAlmostEqual(args[1]["frequency_hz"], 1000.0)
        self.assertAlmostEqual(args[1]["duration_s"], 0.005)

    def test_dc_result_separates_spice_and_analytical_values(self):
        with patch("app.spice_engine.run_analysis", return_value=_dc_result()):
            html = self.post("dc").get_data(as_text=True)
        self.assertIn("Simulator mode: ", html)
        self.assertIn("Run status: SUCCESS", html)
        self.assertIn("ngspice 41", html)
        self.assertIn(spice_engine.MODEL_NAME, html)
        self.assertIn("DC operating point from ngspice", html)
        self.assertIn("Lab 3 analytical reference — not SPICE", html)
        self.assertIn("ngspice .op device currents (wrdata)", html)
        self.assertIn("* test netlist", html)

    def test_ac_result_has_gain_phase_charts_with_units(self):
        with patch("app.spice_engine.run_analysis", return_value=_ac_result()):
            html = self.post("ac").get_data(as_text=True)
        self.assertIn("AC frequency response from ngspice", html)
        self.assertIn("AC Frequency Response (.ac)", html)
        self.assertIn("Voltage gain magnitude", html)
        self.assertIn("Voltage gain phase", html)
        self.assertIn("Gain (dB)", html)
        self.assertIn("Phase (degrees)", html)
        self.assertIn("Frequency (Hz, log scale)", html)
        self.assertIn("<svg", html)
        self.assertIn("v(base) after Cin", html)

    def test_tran_result_has_waveform_chart_with_units(self):
        with patch("app.spice_engine.run_analysis", return_value=_tran_result()):
            html = self.post("tran").get_data(as_text=True)
        self.assertIn("Transient response from ngspice", html)
        self.assertIn("Input and output waveforms", html)
        self.assertIn("Time (s)", html)
        self.assertIn("Voltage (V)", html)
        self.assertIn("mV peak", html)
        self.assertIn("inverted (near 180 deg)", html)

    def test_engine_failure_never_shows_previous_result(self):
        with patch("app.spice_engine.run_analysis", return_value=_dc_result()):
            first = self.post("dc").get_data(as_text=True)
        self.assertIn("Run status: SUCCESS", first)

        with patch("app.spice_engine.run_analysis",
                   side_effect=spice_engine.SpiceError("ngspice รันไม่สำเร็จ")):
            second = self.post("dc").get_data(as_text=True)
        self.assertIn("ngspice รันไม่สำเร็จ", second)
        self.assertIn("Run rejected", second)
        self.assertNotIn("Run status: SUCCESS", second)
        self.assertNotIn("DC operating point from ngspice", second)
        self.assertNotIn("* test netlist", second)


if __name__ == "__main__":
    unittest.main()
