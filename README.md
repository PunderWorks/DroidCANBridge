# Droid CANBus Adapter

A very small, inexpensive adapter board that bridges CANBus to a standard UART and back, so droid
components without CAN support can join a CAN network.

- **MCU:** STM32C092 (TSSOP-20), with a built-in CAN FD controller
- **CAN:** CAN FD-capable transceiver; two JST-XH connectors for daisy-chaining and a jumper for the
  120 Ω termination resistor
- **UART:** JST-XH connector with a jumper that sets the logic level to 3.3 V or 5 V
- **Power:** 5 V in on a WAGO terminal (reverse-polarity protected), with a WAGO passthrough output
- **Programming:** standard 6-pin FTDI header using the STM32's built-in serial bootloader, with a
  boot button

Status: design in progress. Hardware is in [`PCB/`](PCB/) (see [PCB/README.md](PCB/README.md) for
requirements and design decisions); firmware will live in `src/`.
