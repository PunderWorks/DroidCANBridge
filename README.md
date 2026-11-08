# DroidCANBridge

<p align="center">
  <img src="PCB/assets/DroidCANBridge-v1-front.png" alt="DroidCANBridge v1.0, front: WAGO 5 V in and out terminals, the STM32 and CAN transceiver in the middle, JST-XH CAN and serial connectors along the edges, and the FTDI header along the bottom" width="49%">
  <img src="PCB/assets/DroidCANBridge-v1-rear.png" alt="DroidCANBridge v1.0, back: the PunderWorks logo, board name and version, and a QR code linking to this repository" width="49%">
</p>

A very small, inexpensive CAN-to-UART bridge for droid builders: it translates CAN bus frames to a
standard UART and back, so droid components without CAN support can join a CAN network.

- **MCU:** STM32C092 (TSSOP-20), with a built-in CAN FD controller
- **CAN:** CAN FD-capable transceiver; two 2-pin JST-XH connectors (CANL, CANH) for daisy-chaining and a jumper for the
  120 Ω termination resistor
- **UART:** 2-pin JST-XH connector (RX, TX) with a jumper that sets the logic level to 3.3 V or 5 V
- **Power:** 5 V in on a WAGO terminal (reverse-polarity protected), with a WAGO passthrough output
- **Programming:** standard 6-pin FTDI header using the STM32's built-in serial bootloader, with
  DTR auto-reset and a boot button

Status: PCB complete (50 x 40 mm, two layers): routed, silkscreen and graphics done (PunderWorks
logo and a QR code to this repo on the back); not yet ordered. Gerbers, drills, BOM and placement
are in [`PCB/production/`](PCB/production/). Hardware is in [`PCB/`](PCB/) (see
[PCB/README.md](PCB/README.md) for requirements and design decisions); firmware will live in `src/`.
