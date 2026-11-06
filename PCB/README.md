# DroidCANAdapter hardware

The electrical design is Stackup KDL in [`stackup/`](stackup/); the KiCad project
(`DroidCANAdapter.*`) is laid out from it. Manufacturer datasheets are in [`datasheets/`](datasheets/)
with their source URLs in `datasheets/manifest.json`.

## Requirements

| Area | Requirement |
|---|---|
| Size | As small as possible. M3 mounting holes. No target outline. |
| Assembly | SMD parts assembled by JLCPCB. Connectors, terminals, headers and button through-hole, hand-soldered. |
| MCU | Inexpensive STM32 with a CAN FD controller. |
| CAN | Two JST-XH connectors (daisy-chain in/out), pinout `GND, CANL, CANH`. Jumper-selectable 120 Ω termination. No ESD protection. |
| UART | One JST-XH connector, pinout `GND, RX, TX` (named from this board's side). Works with 3.3 V and 5 V devices, selected by a pin jumper. |
| Power | 5 V in on a through-hole WAGO terminal, with reverse-polarity protection. A second WAGO terminal passes the 5 V input through to the connected device. No fuse. |
| Programming | Standard 6-pin FTDI header (`GND, CTS, VCC, TX, RX, DTR`) on the STM32 system-bootloader UART. The board can run from the FTDI header's VCC on the bench. DTR drives reset. A small boot button (not a jumper) selects the bootloader. |
| Indicators | None (status is reported over serial). |

## Decisions

- **STM32C092FCP6 (TSSOP-20).** The cheapest STM32 with FDCAN (the C091 has none). No STM32 comes in a
  through-hole package, so the MCU is SMD; once JLCPCB is assembling it, the other small parts are SMD
  too to keep the board compact. FDCAN1 is available on the TSSOP-20 pins 1/2 (PB8 RX / PC14 TX) and
  16/17 (PA11[PA9] RX / PA12[PA10] TX) per the pin table in DS14720 pp. 33–37; the final choice is made
  together with the bootloader UART pins. JLCPCB stock is low (C44847704, 6 pcs on 2026-11-05;
  Mouser 3,314), so recheck before ordering and plan on global sourcing or consigned parts.
- **CAN FD hardware, classic CAN firmware first.** The bus mixes CAN FD and classic nodes. A classic
  node does not slow the others down, since every node already shares the nominal (arbitration) bit
  rate. But a strictly classic controller (e.g. MCP2515) answers FD frames with error frames. The
  STM32 FDCAN can run in classic mode and ignore FD frames (protocol exception handling), so this
  board stays safe on a mixed bus and can move to FD in firmware later. Messages addressed to the
  adapter must be sent as classic frames while it runs in classic mode.
- **Firmware platform: PlatformIO + STM32duino.** `platform-ststm32` v20.0.0 has a `nucleo_c092rc`
  board (Arduino, STM32Cube, Zephyr), and STM32duino 3.0.0 has the TSSOP-20 variant
  `STM32C0xx/C092ECY_C092F(B-C)P`, so a small custom board JSON is enough. FDCAN is used through the
  bundled HAL; STM32duino has no CAN library.
- **UART level shifting without a shifter IC.** STM32 RX is a 5 V-tolerant (FT) input. TX is driven
  open-drain with a pull-up to a jumper-selected 3.3 V / 5 V rail. Pin choice must confirm FT on both
  pins.
- **JST-XH** for CAN and UART (the community's preferred connector).
