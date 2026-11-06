"""Proposed starting placement for PCB/DroidCANAdapter.kicad_pcb.

Run with KiCad's bundled Python, with the board closed in KiCad:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        scripts/pcb/place.py PCB/DroidCANAdapter.kicad_pcb

It moves footprints and redraws the Edge.Cuts outline; it never touches nets (those come from the
Stackup sync). Positions are the centre of each footprint's courtyard, in mm from the board's
top-left corner, so the table reads like the board. This is a starting point for hand layout:
once the board is edited in KiCad, the board file is the source of truth and this script is
not rerun.
"""

import sys

import pcbnew

ORIGIN = (100.0, 100.0)  # board top-left corner in KiCad page coordinates
W, H = 46.0, 35.0         # board outline, mm

# ref: (x, y, rotation°) — x/y are the courtyard centre from the board's top-left corner.
# Edge-aligned parts are given by an edge rule instead (see EDGE below).
PLACE = {
    # Left band: CAN transceiver under the CAN connectors, terminator beside them.
    "J5": (3.6, 9.6, 90),       # TERM jumper
    "R1": (9.0, 9.6, 0),        # 120 Ω terminator
    "U3": (8.5, 15.5, 180),     # TCAN334G; TXD/RXD side faces the MCU
    "C7": (14.0, 15.5, 90),     # TCAN VCC 100 nF

    # Middle band: device-UART parts under J_UART, MCU in the centre.
    "R2": (24.0, 9.5, 0),       # TX pull-up
    "Q1": (28.5, 9.8, 0),       # BSS138 RX shifter
    "R3": (32.5, 9.5, 0),       # RX pull-up
    "U2": (24.5, 16.5, 180),    # STM32C092; CAN pins face U3, FTDI pins face J8
    "C6": (29.6, 14.5, 90),     # NRST filter, beside pad 6
    "C4": (29.6, 18.0, 90),     # VDD 100 nF, beside pad 4
    "C5": (31.3, 18.0, 90),     # VDD 4.7 µF
    "C8": (31.3, 14.5, 90),     # DTR coupling
    "D3": (34.0, 14.5, 0),      # BAT54S NRST clamp
    "R4": (33.0, 21.0, 90),     # BOOT0 pull-down

    # Middle band, bottom: power OR diodes and LDO beside the WAGOs.
    "D1": (24.3, 22.8, 180),    # SS14, WAGO in; cathode (band) toward VSYS on the right
    "D2": (24.3, 26.6, 180),    # SS14, FTDI VCC; cathode toward VSYS
    "C1": (29.2, 23.5, 90),     # VSYS bulk
    "U1": (31.6, 27.5, 0),      # AP2112K
    "C2": (29.8, 31.0, 0),      # LDO in
    "C3": (33.3, 31.0, 0),      # LDO out

    # Right band: VIO jumper, boot button, test pads.
    "J7": (38.5, 12.0, 0),      # VIO jumper (1 = 3V3 at top)
    "SW1": (38.5, 21.0, 0),     # boot button

}

# Edge-aligned parts: (ref, rotation°, edge, offset along the edge from the left/top corner, inset)
# The courtyard's outer side sits `inset` mm inside the named edge (negative = overhang).
EDGE = [
    # CAN in/out on the left of the top edge, UART in the middle; wires plug in from above.
    ("J3", 0, "top", 0.5, 0.0),        # J_CAN1
    ("J4", 0, "top", 11.5, 0.0),       # J_CAN2
    ("J6", 0, "top", 24.5, 0.0),       # J_UART
    # Power terminals at the bottom-left, wire entry facing down (footprint +y), side by side so
    # the passthrough copper between them is short and wide.
    ("J1", 0, "bottom", 0.5, 0.0),     # J_PWR_IN
    ("J2", 0, "bottom", 10.6, 0.0),    # J_PWR_OUT
    # FTDI header on the right edge, pin 1 (GND, black wire) at the top.
    ("J8", 0, "right", 9.0, 0.0),
]

HOLES = {"H1": (42.0, 4.0), "H2": (42.0, H - 4.0)}


def mm(v):
    return pcbnew.FromMM(v)


def courtyard_bbox(fp):
    bbox = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if bbox.GetWidth() == 0:
        bbox = fp.GetBoundingBox(False, False)
    return bbox


def move_centre_to(fp, x, y):
    bbox = courtyard_bbox(fp)
    cx, cy = bbox.GetCenter().x, bbox.GetCenter().y
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(ORIGIN[0] + x) - cx, pos.y + mm(ORIGIN[1] + y) - cy))


def place_on_edge(fp, edge, offset, inset):
    bbox = courtyard_bbox(fp)
    w, h = pcbnew.ToMM(bbox.GetWidth()), pcbnew.ToMM(bbox.GetHeight())
    if edge == "top":
        x, y = offset + w / 2, inset + h / 2
    elif edge == "bottom":
        x, y = offset + w / 2, H - inset - h / 2
    elif edge == "left":
        x, y = inset + w / 2, offset + h / 2
    else:  # right
        x, y = W - inset - w / 2, offset + h / 2
    move_centre_to(fp, x, y)


def draw_outline(board):
    for item in list(board.GetDrawings()):
        if item.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(item)
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(mm(ORIGIN[0]), mm(ORIGIN[1])))
    rect.SetEnd(pcbnew.VECTOR2I(mm(ORIGIN[0] + W), mm(ORIGIN[1] + H)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(mm(0.1))
    board.Add(rect)


def main(path):
    board = pcbnew.LoadBoard(path)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    for ref, (x, y, rot) in PLACE.items():
        fps[ref].SetOrientationDegrees(rot)
        move_centre_to(fps[ref], x, y)
    for ref, rot, edge, offset, inset in EDGE:
        fps[ref].SetOrientationDegrees(rot)
        place_on_edge(fps[ref], edge, offset, inset)
    for ref, (x, y) in HOLES.items():
        fps[ref].SetPosition(pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y)))

    missing = set(fps) - set(PLACE) - {e[0] for e in EDGE} - set(HOLES)
    if missing:
        sys.exit(f"not placed: {sorted(missing)}")

    draw_outline(board)
    pcbnew.SaveBoard(path, board)
    print(f"placed {len(fps)} footprints on a {W} x {H} mm board")


if __name__ == "__main__":
    main(sys.argv[1])
