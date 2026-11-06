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
W, H = 46.0, 32.0         # board outline, mm

# Signal and power flow left to right, the way the board sits in a droid harness: power and CAN
# come in on the left edge; the power passthrough, CAN out and the device UART leave on the right.
#
# ref: (x, y, rotation°) — x/y are the courtyard centre from the board's top-left corner.
# Edge-aligned parts are given by an edge rule instead (see EDGE below).
PLACE = {
    # Top middle, between the two WAGOs: power OR diodes, VSYS bulk, LDO. The +5V_IN passthrough
    # runs straight across above them.
    "D1": (19.6, 2.3, 180),     # SS14, WAGO in; anode left toward J_PWR_IN, band right
    "D2": (19.6, 6.5, 180),     # SS14, FTDI VCC; band right
    "C1": (24.3, 4.4, 90),      # VSYS bulk
    "U1": (27.6, 3.5, 0),       # AP2112K
    "C2": (26.3, 7.6, 0),       # LDO in
    "C3": (29.0, 7.8, 90),      # LDO out

    # CAN: terminator beside CAN in, transceiver between it and the MCU.
    "J5": (8.8, 13.5, 0),       # TERM jumper
    "R1": (8.8, 18.5, 90),      # 120 Ω terminator
    "U3": (14.8, 16.0, 180),    # TCAN334G; CANH/CANL face J_CAN1, TXD/RXD face the MCU
    "C7": (14.8, 20.5, 0),      # TCAN VCC 100 nF

    # MCU and its local parts.
    "U2": (24.5, 17.0, 180),    # STM32C092; CAN pins face U3
    "C6": (29.6, 15.5, 90),     # NRST filter, beside pad 6
    "C4": (29.6, 18.8, 90),     # VDD 100 nF, beside pad 4
    "C5": (31.3, 18.8, 90),     # VDD 4.7 µF
    "C8": (31.3, 15.5, 90),     # DTR coupling
    "D3": (34.2, 15.5, 0),      # BAT54S NRST clamp
    "SW1": (16.5, 24.5, 0),     # boot button
    "R4": (22.0, 23.0, 90),     # BOOT0 pull-down

    # Device UART parts beside J_UART on the right edge.
    "J7": (34.5, 22.3, 90),     # VIO jumper (pin 1 = 3V3 on the left)
    "R2": (35.0, 25.6, 0),      # TX pull-up
    "Q1": (36.6, 28.2, 0),      # BSS138 RX shifter
    "R3": (36.6, 31.0, 0),      # RX pull-up
}

# Edge-aligned parts: (ref, rotation°, edge, offset along the edge from the left/top corner, inset)
# The courtyard's outer side sits `inset` mm inside the named edge (negative = overhang).
EDGE = [
    # In, on the left edge: power (wire entry facing left) and CAN in. JSTs are turned so pin 1
    # (GND) is at the top on both sides.
    ("J1", 270, "left", 0.0, 0.0),     # J_PWR_IN
    ("J3", 270, "left", 10.5, 0.0),    # J_CAN1 (in)
    # Out, on the right edge: power passthrough (wire entry facing right), CAN out, device UART.
    ("J2", 90, "right", 0.0, 0.0),     # J_PWR_OUT
    ("J4", 270, "right", 10.0, 0.0),   # J_CAN2 (out)
    ("J6", 270, "right", 21.1, 0.0),   # J_UART
    # FTDI header along the bottom edge, pin 1 (GND, black wire) on the left.
    ("J8", 90, "bottom", 9.5, 0.0),
]

HOLES = {"H1": (4.0, H - 4.0), "H2": (29.5, H - 3.5)}


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
