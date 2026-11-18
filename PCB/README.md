# DroidCANBridge hardware

The electrical design is Stackup KDL in [`stackup/`](stackup/) (`board.kdl`, plus the local parts in
`parts.kdl`). The KiCad board `DroidCANBridge.kicad_pcb` is synced from it through
`DroidCANBridge.stackup_sch`. Manufacturer datasheets are in [`datasheets/`](datasheets/), with
their source URLs and hashes in `datasheets/manifest.json`.

```sh
stackup check PCB/stackup/board.kdl --locked     # check the design
```

After changing the KDL, use **Sync PCB from stackup** in KiCad's PCB editor, or sync headless with
the board closed:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
  <stackup checkout>/kicad-plugin/sync_headless.py PCB/DroidCANBridge.kicad_pcb
```

Commit the synced PCB with the KDL. CI fails if syncing would change the committed PCB.

## Requirements

| Area | Requirement |
|---|---|
| Size | As small as possible. M3 mounting holes. No target outline. |
| Assembly | SMD parts assembled by JLCPCB. Connectors, terminals and headers are through-hole, hand-soldered. |
| MCU | Inexpensive STM32 with a CAN FD controller. |
| CAN | PunderWorks CAN standard (reference design DroidPowerSense v1): two 3-pin JST-XH connectors (daisy-chain in/out), pinout `1 CAN_GND, 2 CANL, 3 CANH`, printed on the silkscreen. CAN_GND to board GND through a PTC. Jumper-selectable 120 Ω termination. No power on the CAN connector. No ESD protection beyond the transceiver's own. |
| UART | One 2-pin JST-XH connector, pinout `RX, TX` (named from this board's side). Works with 3.3 V and 5 V devices, selected by a pin jumper. |
| Power | 5 V in on a through-hole WAGO terminal, with reverse-polarity protection. A second WAGO terminal passes the 5 V input through to the connected device. No fuse. |
| Programming | Standard 6-pin FTDI header (`GND, CTS, VCC, TX, RX, DTR`) on the STM32 system-bootloader UART. The board can run from the FTDI header's VCC on the bench. DTR drives reset. A small boot button selects the bootloader. |
| Indicators | None (status is reported over serial). |

## Circuit

| Block | Parts | Notes |
|---|---|---|
| Power in | J_PWR_IN, J_PWR_OUT (WAGO 2601-1102), D_IN, D_FTDI (SS14), C_VSYS | The two SS14s OR the WAGO input and the FTDI VCC onto VSYS. D_IN is the reverse-polarity protection. Each diode stops one source back-feeding the other, so the FTDI never powers the passthrough terminal. |
| 3.3 V | ldo (AP2112K-3.3) | VSYS → +3V3 for everything on the board. |
| MCU | mcu (STM32C092FCP6, TSSOP-20) | 100 nF + 4.7 µF on VDD; 100 nF NRST filter. |
| CAN | can_xcvr (TCAN334GDR), J_CAN1/J_CAN2, F_CAN_GND, R_TERM + J_TERM | STB/SHDN left on their internal pull-downs (normal mode). Connectors: pin 1 CAN_GND, 2 CANL, 3 CANH. CAN_GND runs straight from J_CAN1 to J_CAN2 (the bus ground daisy-chains) and reaches board GND through F_CAN_GND (Bourns MF-MSMF014/60X-2). Fit the TERM shunt at the ends of the bus. |
| Device UART | J_UART, J_VIO, R_TXPU, Q_RX (BSS138), R_RXPU | TX: open-drain with a 1 kΩ pull-up to the jumper-selected level. RX: BSS138 level shifter. |
| FTDI | J_FTDI, C_DTR, D_NRST (BAT54S) | DTR is AC-coupled to NRST (Arduino-style auto-reset); the BAT54S clamps NRST between GND and +3V3. CTS is tied to GND. |
| Boot | SW_BOOT (TS-1187A), R_BOOT | Hold SW_BOOT through a reset to enter the bootloader. No SWD pads: the FTDI header is the only programming path. |

Jumpers: **J_VIO** shunt on 1-2 = 3.3 V UART, 2-3 = 5 V UART (VSYS). **J_TERM** shunt fitted = 120 Ω
terminator in. The two shunts (SH_VIO, SH_TERM: Würth 60900213421) are BOM-only parts with
outline-only footprints, so they are on the BOM but not in the placement file.

## Layout

The board is 50 x 40 mm, two layers, laid out for how it sits in a droid harness, with
power and signals flowing left to right:

| Edge | Connectors |
|---|---|
| Left (in) | J_PWR_IN (WAGO, wires enter from the left), J_CAN1 |
| Right (out) | J_PWR_OUT (WAGO, wires leave to the right), J_CAN2, J_UART |
| Bottom | J_FTDI, lying along the edge, pin 1 (GND) on the left |

- Both WAGOs have **+5V on the top pole and GND on the bottom**. J_PWR_OUT is turned the opposite
  way from J_PWR_IN, which reverses its pin order, so its +5V is pin 2 (see `board.kdl`). Mark + and
  − on the silkscreen beside both.
- The CAN connectors are turned opposite ways: J_CAN1 reads CANH, CANL, CAN_GND from the top
  (pin 1 at the bottom) and J_CAN2 reads CAN_GND, CANL, CANH (pin 1 at the top). Each pin has an
  edge label (H, L, G) beside it. J_UART has pin 1 (RX) at the top.
- J_CAN2 sits between the 5V OUT WAGO and J_UART, with 1.1 mm and 1.4 mm between the bodies, so its
  "CAN OUT" label runs vertically to its left (0.8 mm-wide characters, as on the FTDI pins).
- CAN_GND: J_CAN1 pin 1 to F_CAN_GND (beside TERM) on the top, and a 0.5 mm track on the bottom
  from J_CAN1 pin 1, under the FTDI header, up to J_CAN2 pin 1. F_CAN_GND's other pad joins the
  top GND pour.
- The +5V passthrough runs straight across the top edge between the WAGOs, above the OR diodes and
  LDO. Size it for the passthrough current, not the board's own < 100 mA.
- The WAGO levers overhang the side edges by about 2 mm (WAGO drawing: 16.58 mm with the lever
  against the 14.5 mm body).
- Two M3 holes in opposite corners: H1 bottom-left, H2 top-right (above J_PWR_OUT). Each has a
  3.5 mm-radius copper keep-out on both layers (rule areas `Keepout H1/H2`), so screw heads,
  washers and standoffs sit on bare board, not on the GND pour.
- GND pours fill both layers. The bottom one gives the passthrough's return a solid path under the
  3 mm +5V_IN track. Pads join them through thermal reliefs with 0.5 mm spokes, wide enough for the
  WAGO GND pins and still easy to hand-solder. 26 GND stitching vias (0.8/0.4 mm) around the
  perimeter and through open areas tie the two pours together, plus vias joining top-pour pockets
  that tracks enclose.
- Silkscreen: reference designators and values are hidden (they remain on the Fab layer for
  assembly drawings). The top labels each connector, jumper setting and the boot button, and the
  FTDI pins from the cable's side (GND, CTS, VCC, RXI, TXO, DTR). The back carries the PunderWorks
  logo (`PunderWorks_Logo_14mm`, a board-only footprint in `libraries/DroidCANBridge.pretty`,
  copied from DroidPowerSense with its source image in `libraries/logos/`), the board name and
  version, the repo URL, and a 6.2 mm QR code to github.com/PunderWorks/DroidCANBridge.
- `scripts/pcb/place.py` produced the starting placement. Once the board is edited in KiCad, the
  board file is the source of truth.

## GPIO table (STM32C092FCP6, TSSOP-20)

From DS14720 Rev 2, Figure 3 and Table 12. Pads marked "shared" bond several die pins together;
firmware must leave the unused ones in their reset (analog) state.

| Pad | Pin (shared) | Net | Function | Notes |
|---|---|---|---|---|
| 1 | PB7 (PB8) | UART_RX_3V3 | USART1_RX | From Q_RX; 1 kΩ pull-up on board. |
| 2 | PC14 | — | spare | |
| 3 | PC15 | — | spare | |
| 4 | VDD/VDDA | +3V3 | supply | |
| 5 | VSS/VSSA | GND | supply | |
| 6 | PF2-NRST | NRST | reset | Bidirectional reset (factory NRST_MODE = 11). DTR auto-reset. |
| 7, 8 | PA0, PA1 | — | spare | |
| 9 | PA2 | FTDI_RXD | USART2_TX | Bootloader USART (AN2606 Table 19). |
| 10 | PA3 | FTDI_TXD | USART2_RX | Bootloader USART. |
| 11-14 | PA4-PA7 | — | spare | Bootloader SPI1 pins (pulled down in bootloader mode); unused here. |
| 15 | PA8 (PB0, PB1, PB2) | — | spare | |
| 16 | PA11 (PA9) | CAN_RX | FDCAN1_RX | Bootloader remaps USART1_TX here but holds it in reset state until 0x7F arrives on pad 17. |
| 17 | PA12 (PA10) | CAN_TX | FDCAN1_TX | Bootloader remaps USART1_RX here (input, pull-up). Only the transceiver's TXD input is on it. |
| 18 | PA13 | — | spare (SWDIO) | Not brought out; no SWD on this board. |
| 19 | PA14-BOOT0 (PA15) | BOOT0 | BOOT0 | 10 kΩ pull-down + SW_BOOT to +3V3. BOOT0 only once nBOOT_SEL is cleared (see Firmware). |
| 20 | PB6 (PB3, PB4, PB5) | UART_TX | USART1_TX | Open-drain, internal pull off (pin sees up to 5.25 V). Bootloader I2C1_SCL. |

## DC operating points

Supply states: WAGO only, FTDI only, both, and the bridge unpowered with the UART device powered.

| Node | Value | Limit (source) | OK |
|---|---|---|---|
| +5V_IN | 4.75-5.25 V (stated ±5%) | SS14 VRRM 40 V | ✓ |
| FTDI_VCC | 4.4-5.25 V (USB at the device) | SS14 VRRM 40 V | ✓ |
| VSYS | 3.85-5.25 V (input less ≤ 0.55 V, SS14 VF at 1 A; < 0.4 V typical at this current) | AP2112 VIN 2.5-6 V; needs ≥ 3.5 V (3.3 V + 200 mV max dropout at 300 mA, AP2112 table p. 8) | ✓ |
| +3V3 | 3.25-3.35 V (±1.5%) | STM32 2.0-3.6 V; TCAN334 3.0-3.6 V | ✓ |
| +3V3 load | ≤ 85 mA (TCAN334 70 mA dominant + MCU budget 15 mA) | AP2112 600 mA | ✓ |
| LDO dissipation | ≤ (5.25 - 3.25) V × 85 mA = 0.17 W | SOT-23-5; check the board temperature on the bench | ✓ |
| UART_TX low | sinking ≤ 5.25 mA (VIO / 1 kΩ) | VOL ≤ 0.4 V at 8 mA (DS14720 Table 51) | ✓ |
| UART_TX high, 5 V setting | 3.85-5.25 V | ATmega VIH 0.6 × VCC = 3.0 V at 5 V (from memory, typical AVR); PB6 FT max VDD + 4.0 V = 7.25 V (Table 21) | ✓ |
| Q_RX on (device TX low ≤ 0.8 V) | VGS ≥ 3.25 - 0.8 = 2.45 V | BSS138 VGS(th) max 1.5 V (onsemi, electrical characteristics) | ✓ |
| UART_RX_3V3, device low | ≤ 0.8 V + 3.3 mA × RDS(on) (≤ 6 Ω at 4.5 V; more at 2.45 V) ≈ 0.85 V | VIL 0.3 × VDD = 0.98 V (Table 50) | ✓ (assumes device VOL ≤ 0.8 V; typical ≤ 0.4 V) |
| UART_RX_3V3, device high | 3.25 V via R_RXPU | VIH 0.7 × VDD = 2.31 V | ✓ |
| UART_RX_3V3, bridge unpowered | ≈ 0 V (FET off, body diode reverse-biased) | FT pin max 4.0 V with VDD = 0 (Table 21) | ✓ |
| BOOT0 at rest / pressed | 0 V / 3.3 V (0.33 mA) | VIL 0.98 V / VIH 2.31 V | ✓ |
| NRST on DTR fall, 3.3 V cable | 3.3 - 3.3 × 1 µF/1.1 µF = 0.3 V, below VIL for 7-16 ms (τ = 1.1 µF × RPU 25-55 kΩ) | VIL(NRST) 0.3 × VDD = 0.98 V; filter 70 ns (Table 53) | ✓ |
| NRST on DTR fall, 5 V cable | clamped by BAT54S to -0.35 to -0.52 V, below VIL for 12-27 ms (SPICE) | MCU negative injection ≤ 5 mA (Table 22): simulated ≤ 0.25 mA; without the BAT54S, 26 mA | ✓ |
| NRST on DTR rise (port close) | ≤ 4.32 V with the BAT54S (SPICE); 7.9 V without it | VIN ≤ VDD + 4.0 V = 7.3 V (Table 21) | ✓ |
| CAN terminator | 2-3 V differential across 120 Ω → ≤ 75 mW | 0805 125 mW | ✓ |
| CAN_GND to GND, normal | ~0 A (no load returns through it), ≤ 6 Ω (R1max) | Ihold 0.14 A (MF-MSMF p. 1) | ✓ |
| CAN_GND to GND, fault | WAGO GND lost with a CAN cable fitted: the downstream load's return (≤ 10 A, the WAGO rating) through the PTC until it trips; then ~0.8 W tripped at ≤ 5.25 V | Vmax 60 V, Imax 40 A, trips in ≤ 0.15 s at 1.5 A (p. 1) | ✓ |

## Firmware requirements from the hardware

- **First flash: clear nBOOT_SEL over the UART before writing any firmware.** Factory option bytes
  are nBOOT_SEL = 1, nBOOT0 = 1 (RM0490 p. 66), so a fresh part ignores the BOOT0 pin and reaches
  the bootloader only through the empty-flash check (RM0490 Table 9, §3.1.4). There are no SWD pads,
  so if firmware were written first with nBOOT_SEL still set, the chip would always boot from flash
  and only that firmware could get back to the bootloader. On the blank chip, connect the FTDI
  and run `STM32_Programmer_CLI -c port=<tty> -ob nBOOT_SEL=0` (STM32CubeProgrammer talks to the ROM
  bootloader over UART and can write option bytes). From then on, holding SW_BOOT through a reset
  always reaches the bootloader, whatever the firmware does. Firmware should also check the bit at
  startup and clear it if a board somehow skipped the step.
- **PB6 (UART TX):** open-drain alternate function, internal pull-up and pull-down off (required to
  sustain more than 4 V, DS14720 Table 21 note 2).
- **PB7 (UART RX):** no internal pull needed (R_RXPU).
- **FDCAN (PunderWorks CAN standard):** classic CAN 2.0 frame format with FD mode off, not just a
  matching data rate, and payloads of at most 8 bytes. One bit rate across the bus, set by the
  motor controllers, with the sample point at ~87.5% (match it on every node). Enable protocol
  exception handling too, so a stray FD frame is ignored instead of answered with error frames.
  The hardware stays FD-capable, so a later move to FD is firmware and segmenting only.
- **Shared pads:** leave PB8, PB0-PB2, PA9, PA10, PA15, PB3-PB5 untouched (analog). Use the SYSCFG
  remap only if the pad assignment changes.
- **Flashing:** the ROM bootloader on USART2 (8 data bits, even parity, 1 stop bit; AN2606 Table 19).
  Hold SW_BOOT, let the flasher pulse DTR, release after it connects.

## Decisions

- **STM32C092FCP6 (TSSOP-20).** The cheapest STM32 with FDCAN (the C091 has none). No STM32 comes in a
  through-hole package, so the MCU is SMD; once JLCPCB is assembling it, the other small parts are SMD
  too to keep the board compact. The library part only has LQFP packages, so `parts.kdl` carries a
  TSSOP-20 copy (candidate to upstream). JLCPCB stock is low (C44847704, 6 pcs on 2026-11-05;
  Mouser 3,314), so recheck before ordering and plan on global sourcing or consigned parts.
- **Pin plan.** FTDI on USART2 PA2/PA3 because that is a bootloader USART bonded on TSSOP-20 (the other,
  USART1 on PA9/PA10, is remapped onto pads 16/17 there). CAN on pads 16/17. Device UART on USART1
  PB6/PB7 (pads 20/1). The bootloader's I2C1 on PB6/PB7 cannot trigger: SCL (PB6) never toggles with
  the MCU in the bootloader. Its FDCAN bootloader is not available on TSSOP-20 (AN2606 Table 19 note 2).
- **PunderWorks CAN standard (2026-11-17).** All PunderWorks CAN boards match DroidPowerSense v1:
  3-pin JST-XH (1 CAN_GND, 2 CANL, 3 CANH), TCAN334GDR, CAN_GND daisy-chained between the two
  connectors and tied to GND through a Bourns MF-MSMF014/60X-2, 120 Ω on a TERM jumper with a Würth
  60900213421 shunt, and no power on the CAN connector. This board was brought into line before
  it was ever made, so it stays V1.0. It replaces the earlier 2-pin connectors with no ground,
  which relied on every board sharing ground through the power wiring. A bus ground wire keeps
  nodes within the transceiver's common-mode range when they are powered separately. Without the
  PTC, losing this board's WAGO GND with a CAN cable still fitted would send the downstream
  device's return current through a 3 A JST contact and signal wire. The PTC, part, footprint
  (`DroidCANBridge:Bourns_MF-MSMF_1812_Style2`, Bourns p. 7 land pattern: 1.68 × 2.95 mm pads,
  3.1 mm gap) and shunt are DroidPowerSense's. The builder may leave out the CAN_GND wire.
- **CAN FD hardware, classic CAN firmware first.** The bus mixes CAN FD and classic nodes. A classic
  node does not slow the others down, since every node already shares the nominal (arbitration) bit
  rate. But a strictly classic controller (e.g. MCP2515) answers FD frames with error frames. The
  STM32 FDCAN can run in classic mode and ignore FD frames (protocol exception handling), so this
  board stays safe on a mixed bus and can move to FD in firmware later. Messages addressed to the
  bridge must be sent as classic frames while it runs in classic mode.
- **TCAN334G, 3.3 V transceiver.** Running everything from 3.3 V lets the power path use plain
  Schottky diodes for OR-ing and reverse protection: a 5 V-only transceiver (MCP2562FD, VDD ≥ 4.5 V)
  would not tolerate the diode drop. This replaced the P-MOSFET reverse protection discussed earlier:
  with no 5 V load, the diode's drop costs nothing and it also does the OR-ing.
- **Firmware platform: PlatformIO + STM32duino.** `platform-ststm32` v20.0.0 has a `nucleo_c092rc`
  board (Arduino, STM32Cube, Zephyr), and STM32duino 3.0.0 has the TSSOP-20 variant
  `STM32C0xx/C092ECY_C092F(B-C)P`, so a small custom board JSON is enough. FDCAN is used through the
  bundled HAL; STM32duino has no CAN library.
- **UART level shifting.** TX: open-drain with a pull-up to the J_VIO rail, no extra parts. RX: a
  BSS138, because the FT pin's limit drops to 4.0 V with the bridge unpowered and positive injection
  is not allowed (DS14720 Tables 21-22), so a series resistor can't protect it from a separately
  powered 5 V device.
- **JST-XH** for CAN and UART (the community's preferred connector). CAN follows the PunderWorks
  standard above. The UART stays **2-pin with no ground**: the UART device is powered from this
  board's passthrough, so its ground return is short. **WAGO 2601-1102** (10 A, lever push-in,
  horizontal entry) for power.

## Accepted risks and known gaps

- **Passthrough is unprotected.** J_PWR_OUT is wired to the input terminal, so reversed input reaches
  the downstream device. D_IN protects only this board.
- **Reversed power with other grounds connected.** If the input is reversed while the UART device's
  ground is tied to the system ground, current flows through the board's ground copper; no series
  part can stop that. Through a CAN ground wire, F_CAN_GND trips and limits it to tens of mA.
- **F_CAN_GND is not stocked at LCSC** (MF-MSMF014/60X-2; Mouser 3,538, DigiKey 3,608 on
  2026-11-17). JLCPCB places it from global sourcing or consigned parts, like the STM32. Without
  one, it is an 1812 that hand-solders easily.
- **FTDI adapters with 3.3 V on VCC.** Some adapters supply 3.3 V instead of 5 V on the VCC pin.
  VSYS is then about 3.0 V, the LDO drops out to about 2.8 V, and the TCAN334G (3.0 V minimum)
  is out of spec. Flashing still works (the STM32 runs from 2.0 V); CAN needs the WAGO input.
- **FTDI adapter without VCC wired.** If an adapter drives 5 V TX into PA3 without supplying VCC and
  nothing else powers the board, PA3 exceeds its 4.0 V unpowered limit. Normal FTDI cables supply
  VCC.
- **UART ground shares the power wiring.** If the UART device's ground also carries heavy load
  current (a motor controller, say), the offset appears in the UART signal levels. Fine for a device
  powered from J_PWR_OUT; worth checking for anything else.
- **J_VIO with no shunt** leaves UART TX without a pull-up (the device's RX floats). Always fit a shunt.
- **`stackup bom` reports 2 parts without an MPN:** the two mounting holes, which are drill only
  with nothing to buy.
- **No SWD access.** Programming and recovery go through the FTDI header and the ROM bootloader
  only, which relies on nBOOT_SEL being cleared at the first flash (see Firmware requirements).
- **AP2112 θJA for SOT-23-5** was not found in the datasheet text; 0.17 W worst case is small but the
  LDO temperature is on the bench checklist.

## Final review (2026-11-05)

Pre-fab review of the routed board at `ede7f2c`. Clean: `stackup check` (0/0/0), PCB sync check,
DRC with zones refilled (0 violations, 0 unconnected), footprint pad numbers against every IC
and diode datasheet pin table, silkscreen labels against the nets they name, the saved zone fill
(identical to a refill), JLC trace/space, via, annular-ring and hole-spacing limits
(`datasheets/JLC-PCB-capabilities.txt`), and the DTR reset simulation (`scripts/spice/`).

Fixed in the review: hole keep-outs, 26 stitching vias, back silkscreen "rev A" → "V1.0" (the
board's version, matching the front), UART label "SERIAL IN" → "SERIAL". U3 moved up and C7 (its
100 nF) moved beside it: 3.0 mm of track to VCC (was 6.2 mm) and 2.8 mm to GND, with the supply
reaching C7 before U3, per TI's "as close to the VCC supply pins as possible" (TCAN334 §7.4).

Decoupling arrangement, traced along the copper: C4 (MCU VDD) and C7 (TCAN VCC) are in line
between the supply and the pin; C1 (VSYS bulk) sits where both OR diodes meet; C6 is 3.0 mm from
NRST; the BAT54S clamp sits at C8 where the DTR surge enters. The regulator's own caps hang off
short branches: C3 (output) 6.9 mm from VOUT and C2 (input) 8.7 mm from VIN. Accepted: the
AP2112 is stable with 1 µF ceramics and C1's 4.7 µF is in line on the input.

Silkscreen: every board text is at least 1.0 mm tall (JLC's minimum, "characters height less than
40 mil (1.0 mm) will be unidentifiable"), and the board setup's minimum text height is 1.0 mm so
DRC enforces it. The FTDI pin names are 1.0 mm tall by 0.8 mm wide to fit the 2.54 mm pitch. The
edge labels beside the WAGO and JST pins are one text per pin, placed at that pin.

Accepted findings:
- `bom_check.py` flags H1/H2 for no MPN or LCSC: they are drill-only, nothing to buy.
- The WAGO "5V / G" edge labels sit between each terminal and the board edge, under the
  overhanging levers: hidden from directly above, visible at an angle and with the levers open.
  The back pinout legend that repeated the polarity was replaced by the logo and QR code
  (2026-11-08), so the edge labels are now the only polarity marking.
- KiCad's stock footprints draw silkscreen at 0.12 mm, under JLC's 0.15 mm line minimum. Common
  practice; outlines may print faint. Not changed.

## CAN standard update (2026-11-17)

Brought in line with the PunderWorks CAN standard (see Decisions): J_CAN1/J_CAN2 to 3-pin, F_CAN_GND
added, SH_TERM/SH_VIO in the BOM. Re-checked after the change: `stackup check` 0/0/0 (33 parts,
20 nets), PCB sync check clean, DRC with zones refilled 0 violations and 0 unconnected, F1 pads
against Bourns p. 7. To make room, two GND stitching vias moved off F1's pads and two off the new
edge labels. Fab files and the renders in `assets/` regenerated.

## Fab files

[`production/`](production/) holds the Gerbers and job file (2 layers, 1.6 mm) and the PTH/NPTH
drills with maps in `production/gerbers/`, and the purchasing BOM (`stackup bom`, with LCSC numbers
for JLCPCB) and the placement file in `production/bom/`. The placement file lists only the 21
JLCPCB-placed parts: the hand-soldered connectors and headers (J1-J8) and the loose jumper shunts
(SH1, SH2) are `hand=#true` in the KDL,
which marks them Hand/DNP in the BOM and, from Stackup 0.3.0, makes the PCB sync give their
footprints KiCad's *Exclude from position files* and *Exclude from BOM* attributes. The mounting
holes' stock footprint carries both attributes itself. Check JLCPCB's placement preview for rotation and pin 1 on U1-U3, Q1, D1-D3 and SW1.
F1 has no LCSC number (see Accepted risks): order it through global sourcing or consign it.

Regenerate everything after any board change. Refill and save the pours first, because the
exporters plot the fills stored in the board file:

```sh
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli; B=PCB/DroidCANBridge.kicad_pcb
$K pcb drc --refill-zones --save-board --severity-all -o /tmp/drc.rpt $B   # refill, save, and check
$K pcb export gerbers --board-plot-params -o PCB/production/gerbers/ $B
$K pcb export drill --excellon-separate-th --generate-map --map-format gerberx2 -o PCB/production/gerbers/ $B
$K pcb export pos --format csv --units mm --side both --exclude-dnp -o PCB/production/bom/DroidCANBridge-pos.csv $B
stackup bom PCB/stackup/board.kdl --locked -o PCB/production/bom/DroidCANBridge-bom.csv
```

`stackup bom` exits 1 because H1/H2 have no MPN (see accepted findings) but still writes the CSV.
The placement file needs no hand editing: the footprint attributes already keep J1-J8, SH1/SH2
and H1/H2 out of it.

## Bench checklist (first board)

1. Before power: inspect U1/U2/U3 orientation, D_IN/D_FTDI bands (cathode toward VSYS), D_NRST and
   Q1 orientation.
2. Current-limited 5 V on J_PWR_IN (limit ~150 mA): VSYS ≈ 4.6-4.8 V, +3V3 = 3.25-3.35 V, idle
   current noted. Reverse the input briefly: no current, board stays dead.
3. FTDI only: board powers, J_PWR_IN/J_PWR_OUT stay at 0 V (no back-feed).
4. Blank chip: confirm it enters the bootloader (empty check) and `stm32flash` talks on USART2.
   Confirm DTR produces a reset (scope NRST: a ~10-20 ms low pulse, no excursion beyond -0.4 V or
   +3.7 V with a 5 V cable).
5. Clear nBOOT_SEL with STM32CubeProgrammer over the FTDI; then confirm hold-SW_BOOT + DTR reset
   enters the bootloader, before and after flashing firmware.
6. CAN: CANH/CANL recessive ≈ 2.5 V, 120 Ω between them with J_TERM fitted (60 Ω with both ends
   terminated). Exchange classic frames with a known node (DroidPowerSense) at the motor
   controllers' bit rate and an 87.5% sample point; confirm no error frames when an FD node
   transmits FD frames. Confirm the pinout against DroidPowerSense with one cable: pin 1 GND on
   both ends.
7. CAN_GND: continuity J_CAN1.1 to J_CAN2.1 (direct), and to GND through F_CAN_GND (≤ 6 Ω). With
   the WAGO GND disconnected and a load returning through a CAN cable's ground, F_CAN_GND trips and
   the current falls to mA.
8. UART: loopback at 3.3 V and 5 V settings; scope TX rise time at the target baud rate; with the
   bridge unpowered and a powered 5 V device on J_UART, confirm PB7 stays ≈ 0 V.
9. LDO temperature with the CAN bus heavily loaded.
