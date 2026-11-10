# DroidCANBridge — Claude Notes

## Design principles

This device makes CANBus much easier for droid builders: a very small, cheap CAN-to-UART bridge that gives a
device without CAN support its own CANBus endpoint, translating CAN to a plain UART and back.

Requirements and the decisions behind them are recorded in [PCB/README.md](PCB/README.md). Read it
before changing the hardware, and add to it rather than re-deciding something already settled there.

## Repository layout

- `PCB/` — hardware. `PCB/stackup/` holds the Stackup design, `PCB/datasheets/` the manufacturer
  datasheets (fetched with the `pcb-design` skill's `datasheet.py`), and the KiCad project
  (`DroidCANBridge.*`) lives beside them.
- `ci/` — the Cargo-locked Stackup CLI (`ci/stackup/`) and the PCB sync check (`check_pcb_sync.py`).
- `src/`, `include/`, `test/` — firmware (PlatformIO, STM32C092). Not started yet.

## Git workflow

**All changes go through pull requests — never push directly to `main`.** History is linear: rebase,
never merge. Land PRs with `gh pr merge --rebase`. The remote is `thePunderWoman`.

Because PRs land by rebase, `git branch -d` and `--merged` won't recognize a landed branch. Confirm
via `git log --oneline` or `gh pr view <branch> --json state`, then `git branch -D <branch>`.

## Hardware design (Stackup)

The electrical design is Stackup KDL — `PCB/stackup/board.kdl` and `PCB/stackup/parts.kdl` — not
KiCad schematics (there are none). Hardware work follows the `pcb-design` skill.

- Check the design with `stackup check PCB/stackup/board.kdl --locked` (CLI 0.3.0; the Cargo-locked
  copy in `ci/stackup/` is the reference version). The parts library is pinned by commit in
  `manifest.kdl`.
- After any change to the KDL, sync `PCB/DroidCANBridge.kicad_pcb` from it with the Stackup KiCad
  plugin (never edit footprint nets by hand) and commit the PCB with the KDL. Footprints record their
  `board.kdl` line, so even reordering lines needs a resync.
- Logos are KiCad `board_only` footprints; the sync leaves them alone. Mounting holes are KDL
  placements whose stock footprint already excludes itself from the BOM and position files.
- SMD parts (including the boot button) are assembled by JLCPCB; connectors, WAGO terminals and
  headers are through-hole and hand-soldered. Give every hand-soldered part `hand=#true` in
  `board.kdl`: the sync then sets its *Exclude from position files* and *Exclude from BOM*
  attributes, so the KiCad exports leave it out. Don't set those attributes by hand.
- CI (`.github/workflows/ci.yml`) runs the Stackup check and the PCB sync check on PCB changes. The
  only required check on `main` should be `CI Result`; add any new job to its `needs` list.

## Firmware (once it exists)

**Test coverage**
- All new logic gets unit tests in `test/`, running on the native PlatformIO environment
  (`pio test -e native`) with no hardware. Do not add test dependencies that need Arduino or
  physical hardware.
- Keep hardware-touching code (FDCAN/UART HAL wrappers) thin; put the bridging and framing logic in
  plain, hardware-agnostic code that is compiled and covered natively.
- Every bug fix gets a regression test that would have caught it.

**Build verification**
- Verify the real firmware build locally (`pio run`) before pushing. Fix a broken build before
  opening or merging a PR.
