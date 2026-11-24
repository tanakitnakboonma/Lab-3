import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import spice_engine
from spice_engine import SpiceError

BASE_SI = {
    "vcc": 12.0,
    "r1": 100_000.0,
    "r2": 22_000.0,
    "rc": 2_200.0,
    "re": 1_000.0,
    "rl": 10_000.0,
    "cin": 10e-6,
    "cout": 10e-6,
    "amplitude_v": 10e-3,
    "frequency_hz": 1_000.0,
    "duration_s": 5e-3,
}


def _engine_available() -> bool:
    try:
        spice_engine.find_ngspice()
    except SpiceError:
        return False
    return True


class TestValidation(unittest.TestCase):
    def test_accepts_finite_si_values(self):
        clean = spice_engine.validate_parameters(BASE_SI)
        self.assertEqual(clean["r1"], 100_000.0)
        self.assertEqual(clean["frequency_hz"], 1_000.0)

    def test_rejects_bad_and_out_of_range_values(self):
        cases = [
            ("vcc", "abc"),
            ("vcc", float("nan")),
            ("vcc", 0),
            ("r1", -1),
            ("rl", 1e12),
            ("cin", 0),
            ("frequency_hz", 0),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                values = dict(BASE_SI)
                values[key] = value
                with self.assertRaises(SpiceError):
                    spice_engine.validate_parameters(values)

    def test_unknown_analysis_is_rejected_before_engine_lookup(self):
        with self.assertRaises(SpiceError):
            spice_engine.build_netlist("foobar", BASE_SI)
        with self.assertRaises(SpiceError):
            spice_engine.run_analysis("foobar", BASE_SI, binary="not-used")


class TestNetlist(unittest.TestCase):
    def test_each_netlist_has_only_its_own_analysis(self):
        dc = spice_engine.build_netlist("dc", BASE_SI)
        ac = spice_engine.build_netlist("ac", BASE_SI)
        tran = spice_engine.build_netlist("tran", BASE_SI)

        self.assertIn("op", dc)
        self.assertNotIn("ac dec", dc)
        self.assertNotIn("tran ", dc)

        self.assertIn("ac dec", ac)
        self.assertNotIn("\nop\n", ac)
        self.assertNotIn("tran ", ac)

        self.assertIn("tran ", tran)
        self.assertNotIn("ac dec", tran)
        self.assertNotIn("\nop\n", tran)

    def test_teaching_model_and_si_values_are_in_netlist(self):
        netlist = spice_engine.build_netlist("tran", BASE_SI)
        self.assertIn(spice_engine.MODEL_NAME, netlist)
        self.assertIn("VCC vcc 0 DC 12", netlist)
        self.assertIn("R1 vcc base 100000", netlist)
        self.assertIn("CIN src base 1e-05", netlist)
        self.assertIn("SIN(0 0.01 1000)", netlist)

    def test_form_text_cannot_reach_netlist(self):
        values = dict(BASE_SI)
        values["vcc"] = "12 ; shell injection"
        with self.assertRaises(SpiceError):
            spice_engine.build_netlist("dc", values)


class TestEngineLookup(unittest.TestCase):
    def test_environment_override_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "ngspice.exe"
            fake.write_text("stub", encoding="utf-8")
            with patch.dict(os.environ, {"NGSPICE_BINARY": str(fake)}):
                self.assertEqual(spice_engine.find_ngspice(), str(fake))

    def test_missing_engine_reports_thai_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {}, clear=True), \
                 patch("spice_engine.shutil.which", return_value=None), \
                 patch("spice_engine.Path.home", return_value=Path(directory)):
                with self.assertRaises(SpiceError) as context:
                    spice_engine.find_ngspice()
        self.assertIn("ไม่พบ ngspice", str(context.exception))


class TestParsers(unittest.TestCase):
    def test_parse_dc_handles_extra_first_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / spice_engine.DC_DATA_FILE
            path.write_text(
                " vcc v(base) v(emitter) v(collector) ib_a ic_a\n"
                " 1.2e+01 1.94543611e+00 1.28573861e+00 "
                "9.19803184e+00 1.21228951e-05 1.27427819e-03\n",
                encoding="utf-8",
            )
            data = spice_engine._parse_dc(Path(directory), BASE_SI, "log")
        self.assertAlmostEqual(data["vb"], 1.94543611)
        self.assertAlmostEqual(data["ic"], 0.00127427819)
        self.assertAlmostEqual(data["ie"], data["ib"] + data["ic"])
        self.assertIn("wrdata", data["currents_source"])

    def test_parse_ac_handles_duplicate_scale_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / spice_engine.AC_DATA_FILE
            path.write_text(
                " frequency frequency frequency gain_db phase_deg\n"
                " 1 1 0 0 179\n"
                " 1000 1000 0 6 -180\n"
                " 10000000 10000000 0 -2 -170\n",
                encoding="utf-8",
            )
            data, summary = spice_engine._parse_ac(Path(directory), BASE_SI)
        self.assertEqual(data["frequency_hz"], [1.0, 1000.0, 10_000_000.0])
        self.assertEqual(data["phase_deg"], [179.0, 180.0, 190.0])
        self.assertEqual(summary["points"], 3)
        self.assertAlmostEqual(summary["gain_at_source_db"], 6.0)

    def test_parse_tran_handles_duplicate_time_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / spice_engine.TRAN_DATA_FILE
            path.write_text(
                " time time v(base) v(load)\n"
                " 0 0 1.9 0\n"
                " 0.001 0.001 1.91 -0.02\n"
                " 0.002 0.002 1.9 0.01\n",
                encoding="utf-8",
            )
            data, summary = spice_engine._parse_tran(Path(directory), BASE_SI)
        self.assertEqual(data["time_s"], [0.0, 0.001, 0.002])
        self.assertIn(summary["phase_relation"], ("inverted (near 180 deg)", "undetermined"))

    def test_empty_table_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / spice_engine.AC_DATA_FILE
            path.write_text("frequency gain_db phase_deg\n", encoding="utf-8")
            with self.assertRaises(SpiceError):
                spice_engine._parse_ac(Path(directory), BASE_SI)


class TestFailureModes(unittest.TestCase):
    def test_timeout_is_reported(self):
        with patch("spice_engine.find_ngspice", return_value="ngspice"), \
             patch("spice_engine.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["ngspice"], 30)):
            with self.assertRaises(SpiceError) as context:
                spice_engine.run_analysis("dc", BASE_SI, timeout=30)
        self.assertIn("เกิน", str(context.exception))

    def test_nonzero_exit_is_reported(self):
        completed = subprocess.CompletedProcess(["ngspice"], 1, "", "boom")
        with patch("spice_engine.find_ngspice", return_value="ngspice"), \
             patch("spice_engine.subprocess.run", return_value=completed):
            with self.assertRaises(SpiceError) as context:
                spice_engine.run_analysis("dc", BASE_SI)
        self.assertIn("รันไม่สำเร็จ", str(context.exception))

    def test_empty_output_is_reported(self):
        completed = subprocess.CompletedProcess(["ngspice"], 0, "", "")
        with patch("spice_engine.find_ngspice", return_value="ngspice"), \
             patch("spice_engine.subprocess.run", return_value=completed):
            with self.assertRaises(SpiceError) as context:
                spice_engine.run_analysis("dc", BASE_SI)
        self.assertIn("ไม่พบ VB/VE/VC", str(context.exception))

    def test_parse_failure_is_not_masked_as_success(self):
        completed = subprocess.CompletedProcess(["ngspice"], 0, "ok", "")
        with patch("spice_engine.find_ngspice", return_value="ngspice"), \
             patch("spice_engine.subprocess.run", return_value=completed), \
             patch("spice_engine._parse_ac", side_effect=SpiceError("parse failed")):
            with self.assertRaises(SpiceError) as context:
                spice_engine.run_analysis("ac", BASE_SI)
        self.assertEqual(str(context.exception), "parse failed")

    def test_stale_output_files_are_deleted_before_run(self):
        completed = subprocess.CompletedProcess(["ngspice"], 1, "", "")
        with tempfile.TemporaryDirectory() as directory:
            stale = Path(directory) / spice_engine.DC_DATA_FILE
            stale.write_text("stale success data", encoding="utf-8")
            with patch("spice_engine.find_ngspice", return_value="ngspice"), \
                 patch("spice_engine.subprocess.run", return_value=completed):
                with self.assertRaises(SpiceError):
                    spice_engine.run_analysis("dc", BASE_SI, working_dir=directory)
            self.assertFalse(stale.exists())


@unittest.skipUnless(_engine_available(), "ngspice executable not available")
class TestRealNgspice(unittest.TestCase):
    def test_real_dc_ac_tran_runs_return_parsed_data(self):
        for analysis in spice_engine.ANALYSES:
            with self.subTest(analysis=analysis):
                result = spice_engine.run_analysis(analysis, BASE_SI, timeout=30)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["analysis"], analysis)
                self.assertIn("ngspice", result["engine"])
                self.assertIn("command", result)
                self.assertTrue(result["netlist"])
                self.assertTrue(result["log"].strip())
                self.assertFalse(result["command"][0].lower().endswith("ngspice.exe")
                                 and "con" not in result["command"][0].lower())

                if analysis == "dc":
                    for key in ("vb", "ve", "vc", "ib", "ic", "ie", "vbe", "vce"):
                        self.assertIsInstance(result["data"][key], float)
                    self.assertGreater(result["data"]["ic"], 0)
                elif analysis == "ac":
                    self.assertGreater(len(result["data"]["frequency_hz"]), 10)
                    self.assertEqual(len(result["data"]["gain_db"]),
                                     len(result["data"]["phase_deg"]))
                    self.assertLess(result["summary"]["phase_at_source_deg"], -90)
                else:
                    self.assertGreater(len(result["data"]["time_s"]), 10)
                    self.assertEqual(len(result["data"]["vin_v"]),
                                     len(result["data"]["vout_v"]))
                    self.assertGreater(result["summary"]["vout_peak_to_peak_v"], 0)


if __name__ == "__main__":
    unittest.main()
