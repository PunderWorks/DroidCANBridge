# 3D models

Models for parts whose stock KiCad model is missing. Footprints in `../DroidCANAdapter.pretty`
reference them as `${KIPRJMOD}/libraries/3dmodels/...`.

Some manufacturer models can't be committed: their terms of use forbid redistributing them. Those are
gitignored, and each one's download steps are listed below. Without the file, KiCad shows no body for
that part; the board, DRC and fab outputs are unaffected.

| File | Part | Source | In git | Alignment notes |
|---|---|---|---|---|
| `TS-1187A-B-A-B.step` | XKB TS-1187A-B-A-B (SW_BOOT) | SnapEDA (SnapMagic), STEP AP214 exported from SolidWorks | No: SnapEDA's terms allow use in your designs but not redistributing the models | Used by `DroidCANAdapter:XKB_TS-1187A-B-A-B` (KiCad's footprint, renamed so the Stackup sync picks it up). Rotate (90, 0, 0), no offset. The model is Y-up with its base on y = 0; body 0-1.55 mm, terminals at x = ±3.25 mm over pads at ±3.0 mm |
| `WAGO_2601-1102.stp` | WAGO 2601-1102 (J_PWR_IN, J_PWR_OUT) | WAGO via CADENAS PARTcommunity / 3Dfindit, STEP AP214 | No: [CADENAS terms](https://www.cadenas.de/terms-of-use-3d-cad-models) §8 bar passing models to third parties or making them public | Used by `DroidCANAdapter:WAGO_2601-1102_Horizontal` (copied from PowerBoards, pads identical to KiCad's stock footprint). Rotate (270, 0, 90), offset X +4.56 mm. The model is Y-up with its origin at an entry-side pin; this puts its pins on pads 1 and 2 |

## Getting the WAGO 2601-1102 model

1. Open the [WAGO 2601-1102 product page](https://www.wago.com/global/pcb-terminal-blocks-and-pluggable-connectors/pcb-terminal-block/p/2601-1102)
   and sign in.
2. Under **Downloads**, choose the CAD data and download **STEP AP214**.
3. Extract `2601-1102.stp` from the zip and save it here as `WAGO_2601-1102.stp`.

## Getting the TS-1187A-B-A-B model

1. Search SnapEDA (snapeda.com) for **TS-1187A-B-A-B** (XKB Connectivity) and sign in.
2. Download the 3D model as **STEP**.
3. Save it here as `TS-1187A-B-A-B.step`.

## Getting the WAGO model from PowerBoards

If you have the PowerBoards repo checked out, its `PCB/libraries/3dmodels/WAGO_2601-1102.stp` is the
same file.
