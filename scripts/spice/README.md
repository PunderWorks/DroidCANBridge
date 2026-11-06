# SPICE checks

ngspice through KiCad's bundled `libngspice` (no CLI needed). `ngspice_harness.py` and `spice_lib.py`
are copied from the `pcb-design` skill so these run without it installed.

```sh
python3 scripts/spice/ngspice_harness.py --selftest   # proves the library and harness work
python3 scripts/spice/dtr_reset.py                     # exit 1 on any failing corner
python3 scripts/spice/dtr_reset.py --no-clamp          # the same without the BAT54S
```

## dtr_reset.py: FTDI DTR auto-reset on NRST

Circuit: DTR → C_DTR 1 µF → NRST, with the STM32's internal pull-up, the 100 nF Cnrst and the
BAT54S clamp (D_NRST) to GND and +3V3. Corners: 3.3 V and 5 V cables, DTR driver resistance 20 Ω
and 300 Ω, internal pull-up 25 kΩ and 55 kΩ (DS14720 Table 53).

| Assertion | Limit (source) | Result with BAT54S (2026-11-05) |
|---|---|---|
| NRST below VIL after DTR falls | ≥ 1 ms (pin needs 350 ns, Table 53) | 7.0-26.9 ms |
| NRST back above VIH with DTR still low | ≤ 100 ms | 30-78 ms |
| Port held open (DTR low) | NRST must not stay in reset | NRST at 3.30 V |
| Current into the MCU's own clamp | ≤ 5 mA negative injection (Table 22) | ≤ 0.25 mA |
| NRST peak when DTR rises (port close) | ≤ VDD + 4.0 V = 7.3 V (Table 21) | ≤ 4.32 V |

Without the BAT54S, the 5 V-cable corners fail: NRST reaches 7.9 V on port close and 26 mA flows
into the MCU's clamp on the falling edge. The 3.3 V-cable corners pass either way.

Not modelled: the real FTDI/CH340/CP2102 driver (a resistor stands in, an assumption), the
MCU's internal ESD diode (a generic 1N4148 model), the BAT54S (the library's generic BAT54 model,
which matches MDD's VF ≤ 0.32 V at 1 mA), cable inductance, and temperature. Confirm on the bench:
scope NRST on DTR fall and rise with a 5 V adapter.

## Keeping it in sync

The netlist mirrors `PCB/stackup/board.kdl` by hand. Update `dtr_reset.py` whenever C_DTR, Cnrst,
D_NRST or the reset topology changes.
