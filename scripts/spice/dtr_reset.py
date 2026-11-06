#!/usr/bin/env python3
"""SPICE checks for the FTDI DTR auto-reset on NRST.

Circuit (PCB/stackup/board.kdl): FTDI DTR -> C_DTR 1 µF -> NRST. NRST has the STM32's internal
pull-up (25-55 kΩ) and the 100 nF glitch filter Cnrst to GND. D_NRST (BAT54S) clamps NRST: its
lower diode from GND (A1) to NRST (COM), its upper diode from NRST (COM) to +3V3 (K2).

    python3 scripts/spice/dtr_reset.py              # every scenario, exit 1 on any failure
    python3 scripts/spice/dtr_reset.py --no-clamp   # remove the BAT54S to see what it is doing

Timeline per run (starting from the DC operating point: rail up, DTR low): the cable's DTR goes
high at 1 ms (adapter plugged in / port idle), settles,
falls at 500 ms (the flasher or a terminal opens the port), stays low for 1 s (port held open:
the board must not stay in reset), then rises at 1.5 s (port closed).
"""
import argparse
import sys

from ngspice_harness import NgSpice, report, time_above
from spice_lib import corners, diode, run_matrix

# ---- Values (mirror board.kdl; keep in sync) ---------------------------------------------------
C_DTR = "1u"          # C_DTR, CL10A105KB8NNNC
C_NRST = "100n"       # mcu/supply/Cnrst, CC0603KRX7R9BB104
V3V3 = 3.3            # AP2112K-3.3 output (±1.5 %)

# ---- Limits, with their source -----------------------------------------------------------------
RPU = ("25k", "55k")                 # NRST weak pull-up RPU min/max (DS14720 Table 53)
VIL = 0.3 * V3V3                     # NRST VIL max = 0.3 × VDD (Table 53)
VIH = 0.7 * V3V3                     # NRST VIH min = 0.7 × VDD (Table 53)
MIN_PULSE_MS = 1.0                   # we want ≥ 1 ms; the pin needs only 350 ns (VNF(NRST), Table 53)
MAX_RECOVER_MS = 100.0               # NRST must be back above VIH within this, with DTR still low
MAX_INJ_MA = 5.0                     # negative injection, any pin (Table 22 / Table 49)
MAX_NRST_V = V3V3 + 4.0              # VIN max = VDDIO1 + 4.0 V (Table 21)
VOH = (3.3, 5.0)                     # 3.3 V and 5 V FTDI cables
RSRC = ("20", "300")                 # DTR driver output resistance: stiff and weak (assumption)

T_FALL, T_RISE, T_END = 0.5, 1.5, 2.2


def netlist(voh, rsrc, rpu, clamp=True):
    clamp_lines = """Vsd1 0 a1 0
Dc1 a1 nrst DBAT
Dc2 nrst v3 DBAT
Hd1 id1 0 Vsd1 1000""" if clamp else "Rnoclamp id1 0 1"
    return f"""* DTR auto-reset on NRST
{diode('DBAT', 'BAT54')}
{diode('DSI', '1N4148')}
V3 v3 0 {V3V3}
Vdtr src 0 PWL(0 0 1m 0 1.0001m {voh} {T_FALL} {voh} {T_FALL + 1e-7} 0 {T_RISE} 0 {T_RISE + 1e-7} {voh} {T_END} {voh})
Rsrc src dtr {rsrc}
Cdtr dtr nrst {C_DTR}
Cnrst nrst 0 {C_NRST}
Rpu v3 nrst {rpu}
* MCU-internal ESD diode to VSS (generic silicon stand-in); current into the pin from GND is
* measured as mA. FT/RST pins have no diode to VDD (positive injection is not possible, Table 22).
Vsi 0 ai 0
Dint1 ai nrst DSI
Hi1 ii 0 Vsi 1000
{clamp_lines}
.options method=gear
.tran 10u {T_END} 0 5u
.end
"""


NODES = ["nrst", "dtr", "ii", "id1"]


def window(tr, node, a, b):
    return [v for t, v in zip(tr.time, tr[node]) if a <= t <= b]


def scenario_all(sim, clamp):
    def build(voh, rsrc, rpu):
        return netlist(voh, rsrc, rpu, clamp)

    def check(tr, c):
        fall = window(tr, "nrst", T_FALL, T_RISE)
        tfall = [(t, v) for t, v in zip(tr.time, tr["nrst"]) if T_FALL <= t <= T_RISE]
        low_ms = sum(t1 - t0 for (t0, v0), (t1, v1) in zip(tfall, tfall[1:]) if v0 < VIL and v1 < VIL) * 1e3
        back = next((t for t, v in tfall if t > T_FALL + 1e-4 and v > VIH), None)
        recover_ms = (back - T_FALL) * 1e3 if back else float("inf")
        vmin = min(fall)
        inj_ma = max(window(tr, "ii", 0, T_END))            # mA into the MCU's own clamp from GND
        vmax = max(window(tr, "nrst", 0, T_END))              # plug-in edge and port-close edge
        held = min(window(tr, "nrst", T_RISE - 0.2, T_RISE))  # DTR still low: not stuck in reset
        ok = (low_ms >= MIN_PULSE_MS and recover_ms <= MAX_RECOVER_MS and inj_ma <= MAX_INJ_MA
              and vmax <= MAX_NRST_V and held > VIH)
        return ok, (f"low {low_ms:.1f} ms (min {vmin:+.2f} V), back >VIH {recover_ms:.0f} ms, "
                    f"MCU clamp {inj_ma:.2f} mA, peak {vmax:.2f} V, held-low NRST {held:.2f} V")

    return run_matrix(sim, "dtr", build, corners(voh=VOH, rsrc=RSRC, rpu=RPU), NODES, check)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-clamp", action="store_true", help="remove the BAT54S")
    a = p.parse_args(argv)
    return report(scenario_all(NgSpice(), clamp=not a.no_clamp))


if __name__ == "__main__":
    sys.exit(main())
