# PCB

## Automatically Naming Schematic Symbols

**Author:** Christopher Kalitin

**Date:** Dec 2025

**Automatically Naming Schematic Symbols**

This is a simple guide on getting Altium to automatically annotate schematics in a hierarchically designed PCB by adding designators to all symbols. Eg. "C1.1" or "U6.3".

The goal is to have designators of the form "R1.2" where:
- R is the reference designator for the given part
- 1 is the sheet number (eg. if MCU is sheet 1, all parts on that sheet get "X1.Y"
- 2 is the index of a given part on its sheet (eg. if you have 5 resistors, you'll get "RX.5")

I'll show you:
1. How to automatically rename components according to position in the "R102" format
2. Tell you to add the dot between 1 and 2 manually "R1.2"
3. Give you an AutoHotKey script to accelerate adding the dot

**1. Suboptimal Altium Naming**

1.1. From the top tool bar, select Tools > Annotation > Annotate Schematics

1.2. Configure symbol naming

Next, you should see this screen:

![](images/image_2590827726.png)

In the box in the bottom left, you must set the start index of each part on a given schematic sheet. Ensure the check mark to the left of start index is checked for all entries.

In my screenshot above, the first part on the MCU page will be "201". The next part will be "202", then "203", "204", etc. Later, we will simplify these designators so they are "2.1".

The parts of labelled using the Order of Processing shown in the top left, which increments across then down by default. Ie. Top left is counted first (eg. "201"), then top right (eg. "202"), then bottom left (eg. "203"), finally bottom right (eg. "204").

1.3.

Click "Update Changes List" then "Eccept Changes (Create ECO)" then "Execute Changes" and your schematic should be updated.

**2. Making Altium's Naming Slightly Nicer

**

![](images/image_2590831451.png)

Now we're left with part names like "C1201" which was not the format we were going for ("C12.1" would be nicer!).

After 3 hours of effort at ~1500 PPM CO2 in my room (I beg you to buy a CO2 monitor) I couldn't find an automated way to do this. Altium has no inherent support for this naming scheme, and it has checks against you manually editting the binary .SchDoc files.

Either live with "C1201" or manually add the dot to every schematic symbol designator in your project. Live with the relief that you didn't pursue elegant designators to the extent that you had to do this on the HVC (many hundreds of components).

**3. Adding The Dot Faster With AutoHotKey
**
I'll now give you a script that will automatically add the dot to each schematic designator when you double click it and then click F2.

[AutoHotKey](https://www.autohotkey.com/) is a tool that allows binding a given key stroke to a more complex key stroke. Eg. you can map "F10" to "We should rename the DRD to Driver User Interface (DUI)" if you happen to type out that particular phrase very often.

[Tom Scott made a great video](https://youtu.be/lIFE7h3m40U?si=aQNVYeyPkmQXd-Tf&t=170) a decade ago in which he describes using AutoHotKey to automatically deploy a skydrivers parachute.

3.1.
[Install AutoHotKey at this link](https://www.autohotkey.com/) and once installed click "New script"

![](images/image_2590847587.png)

Take note of where your script will be saved, here it's in Documents/AutoHotKey.

![](images/image_2590848289.png)

3.2.

Copy and paste this script into the script.

```
; Script: Right, Left, Shift+Left, Period Sequence
; Trigger: Press F2
; Action: Sends {Right}, {Left}, {Shift Down}+{Left Arrow}, {.}

F2::
Send {Right}
Send {Left}
Send {Backspace}
Send .
return
F4::
Send {Right}
Send {Left 2} ; Move left twice
Send .
return
```

If AutoHotKey doesn't open the script for you in your editor of choice automatically, right click the script, select "open with", select "choose another app", select Notepad. I'm on Windows 10 maybe this changed for you.

3.3.

Double click your script in the file explorer (or manually open with AutoHotKey) and it's now active.

3.4.

To use the script:
1. Double click a symbol designator (eg. "U301") so it's highlighted in green

<img src="images/image_2590852649.png" width="120" height="87">

2A. If the part index (in this case "1") is one digit, click F2
2B. If the part infex (in the case below "10") is two digits, click F4

<img src="images/image_2590857870.png" width="117" height="81">

3. Click in any empty space on the schematic to save the change
4. Repeat

This script simply clicks the right arrow, to select move the text cursor all the way right. Then, it either replaces the 0 in the schematic designator with a period, or inserts a period if the schematic designator is 2 digits.

Note that if you want to do this process (starting from step 1) over again, you probably have to click "Reset All" in the annotation screen and redo step 3 manually.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

The update will cover project organization and timelines.

For IMD Mischa attempted to implment a standard on Solar for schematic block numbering, where the first page is the title of the board ("HVC"), page 2 is power, page 3 is MCU, and all successive pages cover various board functionality. I'll follow this for HVC.

There are a few schematic blocks that I can tackle immediately:
3. MCU
4. Contactor Control
5. LV System Control
6. LVS Current Sensor
7. ESTOP Level Shifting (12V -> 3.3V)
8. CAN Transceiver

There are three schematic blocks that are dependent on other projects:
- Pre/discharge relays (control board design / routing)
- Wires outputting to Junction Board (need to perfectly define wires PAS wants out of the pack, and Junction board functionality)
- Precharge Checking circuitry (Christopher Lazzari's project)

Other items require a good amount of research but can be worked on immediately (in this order):
- Current Sensor
- Swap Relay vs. Power Prioritizer
- Overcurrent faulting circuitry
- DCDC Selection & Mounting
- Startup Circuitry + Supp Low Relay
- Connector Selection

Over the next 2 weeks I'll complete the basic schematic blocks and do component selection. After this, I'll tackle each item that requires a non-trivial amount of research. Finally, when blocking items are complete, I'll integrate / complete schematic block of those items.

> **Aarjav Jain** (Oct 2025)
>
> Nice! As you complete each separate schematic dont forget to make an update and link the Altium. This will let us review it in parallel to you working on it for peak efficiency.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

For the HVC we'll use hierarchical design where we begin with the microcontroller as the source node, and every non-trivial circuit / IC gets its own schematic block branching off of the core MCU block.

<img src="images/image_2459686980.png" width="581" height="378">

*Formula E's BMS Core Schematic*

[Schematic PDF__No Variations_-5.pdf](https://ubcsolar26.monday.com/protected_static/25620279/resources/2459693297/Schematic%20PDF__No%20Variations_-5.pdf)

We'll base the schematic styling / organization roughly off the Formula E schematic above. Notice each connector is defined on the primary highest-level page of the schematic, schematic blocks don't have physical connector schematic elements inside them. Exceptions can be made for test points, as these aren't fundamental to the operation of the PCB ("test" is in the name).

UBC Solar has our

page on Altium that covers hierarchical design.

As a general principle, each IC should get its own schematic block.

New list of schematic blocks:

1. MCU

2. Power

3. Contactor Control

4. LV System Control

5. Startup

6. Pre/discharge Relays

7. HV Current Sensor

8. Overcurrent faulting

9. LVS Current Sensor

10. ESTOP Level Shifting (12V -> 3.3V)
1.1 CAN Transceiver
12. Indication (Additional LEDs)

Some additional schematic pages (not schematic page != schematic block) can be used, eg. mechanical page for screw holes.

Schematic Block connectors:
MCU:
- SWD / JTAG
- BMS Comms
Fans

- Power / PWM Connector
CAN:

- 1 or 2 CAN connectors (not decided which connector yet
ESTOP:
- ESTOP In / Out
Pre/discharge relays:
- Connector for each relay coil power wire
Startup:
- Startup Switch / Motor Discharge
Contactor Control:
- Coil power wires
Current sensor:
- Vref / Vout / GND wiring harness

> **Krish D** (Oct 2025)
>
> I'm assuming when you refer to BMS comms, that this is electrical connections between BMS and ECU (GPIOs)?

> **Christopher Kalitin** (Oct 2025)
>
> @Krish D Yes

> **Aarjav Jain** (Oct 2025)
>
> Looks good @Christopher Kalitin!

---

## Untitled

**Author:** Krish D

**Date:** Sep 2025

This step involves designing the circuitry of each divided section of the HVC's schematic (referred to as schematic blocks).

The current list of schematic blocks to go through are as follows:

1. Startup

2. Power

3. MDU discharge

4. In-pack contactors

5. MCU

6. LV control

7. HV Contactors
8. Estop

9. Fans

10. Hardware over-current faulting

**Note: ** Many sections mentioned will have their circuitry taken from the previous ECU, and changes to that circuitry should be documented on Monday.

> **Aarjav Jain** (Sep 2025)
>
> CC:@Christopher Kalitin.

> **Samuel Shin** (Sep 2025)
>
> Just a reminder @Christopher Kalitin @Hemat Wander We will be using hierarchical design for the new schematics; I know slaveboard testing PCB was a small board as well as distribution board, so I have no problems with them. I'm mentioning this on here as I think the blocks can be each page and the schematic can be designed with more clarity this time!

> **Krish D** (Sep 2025)
>
> Adding on to Sam's point, a good example of hierarchical design is FEEDBACK slaveboard schematic. It is insult the V4 BMS Google drive for reference!

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** Nov 2025

PAS chose a standard DCDC to use, so I replaced the buck + LDO circuitry with it.

Also, the ISO_3V3 DCDC was moved to the power page from the current sense amplifier schematic page, as ISO_3V3 is required both for precharge check and current sense.

See Museok's update about the DCDC:
[https://ubcsolar26.monday.com/boards/9565348340/pulses/9650915685/posts/4645974720](https://ubcsolar26.monday.com/boards/9565348340/pulses/9650915685/posts/4645974720)

![](images/image_2573987555.png)

> **Krish D** (Nov 2025)
>
> @Christopher Kalitin Great to see standardization between PAS and BMS circuitry. Good catch!

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

Options for step downs:

DCDC:
[TSR 1-2450](https://www.digikey.ca/en/products/detail/traco-power/TSR-1-2450/9383780) (92% efficient) - $9
[VR20S05](https://www.digikey.ca/en/products/detail/xp-power/VR20S05/13147720) (92% efficient) - Out of stock

Buck:[AP63205](https://www.digikey.ca/en/products/detail/diodes-incorporated/AP63205WU-7/9858424) (3.8V - 32V input, 90% +/- 5% efficient) - $1.15

LDO:[AP2114H-3.3](https://www.digikey.ca/en/products/detail/diodes-incorporated/AP2114H-3-3TRG1/4470756) (~70% efficient) - $0.41

PAS has been using DCDCs for their 12V -> 5V step down. On ECU rev 2.0 we used a buck converter.

The buck converter requires a few passive components (caps and inductors) that cost an additional ~$1.

The buck converter had models that output either 3.3 V or 5 V. On ECU rev 2.0 we used the 5 V output with a 12 V input.

We need 5 V and 3.3 V on the HVC, the 3.3 V is used for all logic (eg. STM32) and 5 V is used by our CAN transceiver.

To determine whether we should use DCDCs, Bucks, or LDOs, we can consider the costs and efficiencies of each option.

With the current ECU design we use a buck, then LDO for 12 V -> 5 V -> 3.3 V. Multiplying efficiencies, we get 0.92 * 0.7 = 0.644 = 64.4%.

If we used a DCDC or a Buck converter to do 12 to 3.3 V directly, we could get 90% efficiency.

The difference between a DCDC and Buck is mainly cost and passive components. DCDC is ~$9, Buck is ~$2 total (including passives). Buck requires some more routing for the passive components.

I've come to the conclusion that using two buck converters for 12 to 5 and 12 to 3.3 V is optimal. This uses slightly more space (maybe a square centimeter), costs ~$4 total, and gets us ~90% efficiency.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin another consideration I would like to see is noise from the components you chose (2 bucks) and see how it affects your board. Consider what benefits there are to using an LDO for 5 to 3.3V. Another thing to explain here is also the expected power loss due to the inefficiency. A 65% efficiency on an extremely small power draw may be more effective than higher efficiency with other drawbacks (name these).
> 
> Great start to comparing options and its good that you explained reasoning and came to a decision! Another thing, these chains of reasoning are perfect to **link **in a PCB design notes doc so you can say "U1.1: See monday update explaining why".

> **Christopher Kalitin** (Oct 2025)
>
> Looking online, STM32s can tolerate ~50 mV of ripple voltage, and a buck will give ~ +/- 30 mV.
> 
> Using a buck down to 5 V than an LDO seems to be a very standard design to get a low-ish noise supply for microcontrollers.
> 
> Another note is that STM32s have internal LDOs for all logic, to ensure power is even steadier. The reason for all the decoupling capacitors around a chip is that lots of current is consumed on each clock edge, and no LDO or buck can respond fast enough without the smaller caps.
> 
> Given this is a fairly industry standard design decision, I’ll go with buck to LDO. The alternative is including both LDO and Buck to get down to 3.3 V and testing if buck can be used, though this is getting too in the weeds for this project.
> 
> With 100mA on 3.3 V, were loosing an extra 0.19 W at 64.4% efficiency. Over the entire car we’re losing about 1 W.
> 
> To save ~1 W over the entire car we could use DCDCs for 12->3.3 V on every board at the expense of ~$50. We should consider something like this.
> 
> https://community.st.com/t5/stm32-mcus-products/how-much-current-ripple-is-allowable-in-a-vdd-and-or-vdda-3-3v/td-p/233819
> 
> https://www.reddit.com/r/AskElectronics/comments/1ex00nl/is_powering_a_microcontroller_off_a_buck/

> **Aarjav Jain** (Oct 2025)
>
> Sounds good @Christopher Kalitin . Ensure that the LDO you use has a sufficiently low output ripple (< 50mV).

---


---

## IMD Interface

**Author:** Christopher Kalitin

**Date:** 17d

**IMD Interface**

We luckily realized during the meeting last Saturday that we forgot to include functionality for powering or getting a GPIO from the IMD on the HVC.

Adding circuitry to toggle power to it was farily simple

<img src="images/image_2697627600.png" width="291" height="203">

![](images/image_2697629307.png)

The image above shows the topology of the IMD and HVC.

Because the IMD is safety critical, it will have a GPIO going directly to the HVC that goes low if it ever detects the chassis is shorted to POS or NEG.

This GPIO will be read by the HVC's MCU.

Note that this GPIO is pulled low on the HVC to protect against the case in which the IMD is not connected. The IMD must pull the GPIO high for the HVC to allow closing of the contactors.

The GPIO and toggled ground are the extent of the IMDs connection to the HVC. The rest of the connections to the IMD do not involve the HVC (12V, CAN, Chassis connection).

> **Hemat Wander** (16d)
>
> @Christopher Kalitin
> Is the IMD output going to trigger faulting, and if so why not have a hardware connection instead of reading from the HVC MCU? For example, connecting to contactor enable through an NFET similar to the master board will have?
> 
> Is an GPIO connection to the HVC MCU sufficient?

> **Christopher Kalitin** (15d)
>
> @Hemat Wander
> 
> Good idea.
> 
> We could replace IMD_GPIO_IN with an open-drain active-low line that goes directly to the contactors.
> 
> One issue is that if we wanted to include a GPIO as well, the pin count for the junction board connector would have to increase to 24 from 20 (no 22 pin version exists), and we'd have 3 unused pins.
> 
> This is solved by only reading IMD status over a CAN message.
> 
> At this point I'm slightly skeptical of all this hardware-focused faulting. I believe MCUs are mostly trustworthy, especially in our case, and that I've over corrected in the direction of hardware faulting.

> **Krish D** (14d)
>
> @Christopher Kalitin Please CC this in the IMD thread for posterity and to ensure who is designing the IMD is aware of this topology!

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

Currently the only LV system we have to control from the HVC is MPPT power.

Another system we could toggle is masterboard ground, I can think of two reasons we shouldn't do this:
1. If we are debugging we would still see masterboard CAN messages but not HVC CAN messages. This could be useful for knowing the battery is in a safe state.
2. If the give the masterboard hardware control of the contactors, it will be able to provide an override to keep them closed even if we get erroneous behaviour out of the HVC. (Eg. put another NMOS on the coil power line).

Very small lonely schematic page:

![](images/image_2475625804.png)

Previously all of our LEDs were 0603s, to make assembly slightly easier I'm switching it all to 0805s (Mischa suggested this a year ago iirc).

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin
> 
> 1. Could you explain how point **1 **justifies not powering the MPPT and masterboard through HVC? For point 2 I agree why not to **toggle** power masterboard from HVC. *Toggle being different from using a part of the HVC to provide power to the masterboard. * *Toggle implies MCU control.*
> 
> 2. I did not understand why MPPTs should not be powered by HVC? Why not and what will power the MPPTs 12V instead?
> 
> 3. Fully agree for the LEDs. Please do 0805s.

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> MPPT power should be toggled by HVC, masterboard should not be.
> 
> Masterboard power should not be toggled because there are cases when you want it to be active even if there is an issue with the HVC's MCU. Eg. to get battery info on memorator (we should make provisions to keep memorator powered if HVC is not active). Or, so we have redundacy for battery faults opening contactors.

> **Samuel Shin** (Oct 2025)
>
> @Christopher Kalitin
> 
> 1. I agree, but why not see HVC messages? Is it because it's going to stay at fault anyways?
> 
> 2. Not sure I understand. You are saying that if we give masterboard the control of contactors, it's going to be better in a case where HVC is acting weird?
> 
> 3. I **love **that we are switching the LEDs.

> **Christopher Kalitin** (Oct 2025)
>
> 1.
> 
> If HVC microcontroller is fried, we should keep masterboard on to get data on battery health.
> 
> 2.
> 
> Giving masterboard hardware control over contractors is a further safety feature we can discuss. Not 100% sure but that’s the general idea. I’d be interested in consulting Mischa / Ezzat.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin thanks for clearing that up. I agree with powering masterboard separately. Feel free to reach out and come to a conclusion about contactor control via the masterboard **and **HVC and propose the solution on monday!

---


---

## Untitled

**Author:** Krish D

**Date:** 9d

![](images/image_2718186373.png)

@Christopher Kalitin

If you are testing the HVC on bench, LLIM_EN and HLIM_EN must be pulled low, otherwise you won't be able to actuate the contactors. Is this a problem?

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Jan 11

After speaking with @Hemat Wander, I've redesigned the CONTACTOR_ENABLE circuitry.

**Previous Issue
**

The previous iteration was described in [this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080995210/posts/4770869948) and included series diodes on the inputs to the CONTACTOR_EN trace.

These series diodes posed some issues when CONTACTOR_EN is 3.3V but the input itself is supposed to be GND. The forward voltage of the diode meant the input could be pulled up to CONTACTOR_EN - 0.3 V, which poses issues with the MCU identifying which input is controlling CONTACTOR_EN.

**Solution: MOSFETs
**
Inspired by internal GPIO logic in microcontrollers, the new solution toggles a MOSFET to pull CONTACTOR_EN low, and otherwise keeps the NMOS open so the output is in a high-impedance state (not pulled to any voltage, ie. floating).

![](images/image_2673190182.png)

STM32 microcontrollers have two MOSFETs that pull a GPIO to VDD or VSS, depending on if it's a 1 or 0.

This follows the functionality I want, either pull the output down, or leave it floating (so we don't use the PMOS for pull-up).

This greatly simplifies the required mental model to understand the circuitry, and doesn't use any more components

**Schematics

**Note that a truth table has been added to every input to CONTACTOR_EN to make functionality clear.

Diagrams beat paragraphs every time.

![](images/image_2673242145.png)

![](images/image_2673242241.png)

> **Krish D** (Jan 12)
>
> @Christopher Kalitin Can you provide more clarity on what this new FET circuitry protects against, and how the previous design did not account for this? (Adding a diagram would be preferred here).

> **Christopher Kalitin** (Jan 12)
>
> @Krish D
> 
> At a high level, there are many edge cases in which the diodes (described in the previous update under this card) would start conducting and pull the MCU sense line up.
> 
> Here's an example:
> 
> First, note that ESTOP_OUT, ALERT_OUT, and MASTER_BOARD_FAULT_OUT are all connected to CONTACTOR_EN. These nets are all equivalent.
> 
> ESTOP_MCU and ALERT_MCU are tra
> 
> ces that the MCU uses to determine which source is pulling CONTACTOR_EN low.
> 
> If CONTACTOR_EN is pulled to 3V3, then the ESTOP_MCU line will be pulled to 3V because of the series schottky diode. See the image below for a previous iteration of the design.
> 
> ![](images/image_2676333313.png)
> 
> I've actually just realized this is fine, as a logic level high is a nominal state and GND is a fault state, so if the optocoupler is pulling the net to 3V3 or the diode is, it doesn't matter as both are nominal states. We'll still be able to pull to GND in a fault state.
> 
> Either way, the circuitry took way too much thought and is an order of magnitude easier to explain if it's MOSFETs, meaning it's also easier to debug (especially for the poor soul who may have to fix this at 5 am at comp).

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Dec 2025

**1. Contactor Enable NFET**

![](images/image_2634845966.png)

To give the INA228 shunt current sense amplifier control over the
contactors, I added an NFET in series with Contactor Ground, so that
when the INA228 Fault pin goes low (it's open-drain active-low) this FET
opens and none of the contactors have power.

**2. INA228 Current Sense Amplifier Alert Pin**

![](images/image_2634857622.png)

Above you can see how the open-drain active-low ALERT_OUT pin functionality is implemented.

When ALERT_ISO is pulled low (signifying an INA228 detected current fault), the ALERT_OUT pin is pulled to GND.

ALERT_OUT is connected directly to CONTACTOR_EN, which has a 10k pull-up resistor. So when the optocoupler is conducting, CONTACTOR_EN is pulled to GND.

**3. ESTOP Optocoupler**

![](images/image_2634864857.png)

ESTOP_12V_IN is default 12V and becomes floating when ESTOP is pressed.

Hence, the output of the optocoupler is 3V3 by default and pulled to GND when ESTOP is pressed.

To ensure the 3V3 here can't directly short to the INA228 optocoupler Ground, a schottky diode is used. This ensures the output is in fact active-low open-drain and never goes high.

We do still need to have a method of the STM32 reading the value of ESTOP_3V3, so we create a separate port before the schottky diode that does go between 3V3 and GND instead of floating and GND.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin Can you explain how the output of the INA228's OC (ALERT OUT) and ESTOPS OC (ESTOP 3v3)interact with each other, and through which net?
> 
> I'm a bit confused with which logic levels constitute a fault and idle state respectively.
> 
> Also, isn't the fault condition here supposed to be that alert_iso goes high?
> 
> ![](images/image_2634905037.png)

> **Christopher Kalitin** (Dec 2025)
>
> ![](images/image_2637149397.png)
> 
> CONTACTOR_EN is meant to be powered by active-low open-drain inputs. Ie. inputs that are usually floating, but are pulled to ground in a fault condition.
> 
> So, if any net is pulled to GND, it's a fault state. (This is the meaning of "active-low")
> 
> INA228 ALERT_OUT and ESTOP_3V3_OPEN_DRAIN connect directly to that CONTACTOR_EN trace.

> **Krish D** (Dec 2025)
>
> Sounds good. I see you redid the HVC schematic homepage. This is more clear now for showing how these signals converge to contactor_en.

> **Hemat Wander** (Dec 2025)
>
> @Christopher Kalitin  Looks good. A few questions:
> 
> 1. Why is the contactor enable net being set to the master board? Are we also going to give the master board contactor control as well? So its either E-STOP OR current sense OR master board connected to this net?
> 
> ![](images/image_2637624494.png)
> 
> Side note: Why don't you use the input/output symbols for ports?
> 
> 2. Why do we need a pull-up at all if E-STOP normally pulls up the contactors? The reason I say this is because the NFET should normally be pulled to GND (open) so that the contactors are open, UNLESS everything is safe. Or alternatively make it pulled to GND normally.
> 
> ![](images/image_2637628203.png)
> 
> ![](images/image_2637628551.png)
> 
> 3. Is ALERT_ISO pulled up internally?
> 
> ![](images/image_2637631939.png)

> **Hemat Wander** (Dec 2025)
>
> Nevermind you already answered first question here:
> 
> ![](images/image_2637634838.png)

> **Christopher Kalitin** (Dec 2025)
>
> @Hemat Wander
> 
> 1.
> Will make all ports inputs / outputs for clarity.
> 
> 2.
> ESTOP_3V3_Open_Drain never pulls it up.
> 
> ![](images/image_2639325668.png)
> 
> The purpose of the CONTACTOR_EN NFET is to give faulting control to a couple of circuits. This is similar functionality to our ESTOP Relay on the ECU, where it should always be closed, unless ESTOP occurs. So, we pull it up.
> 
> 3.
> Good catch, added a pull-up.
> 
> <img src="images/image_2639335627.png" width="243" height="221">

> **Hemat Wander** (Dec 2025)
>
> @Christopher Kalitin
> Is the ESTOP_3V3_OPEN_DRAIN normally floating and not pulled high because of the diode? Otherwise the opt isolator would be pulling it up to 3.3V right?
> 
> Why not remove the diode and replace it with a resistor, so the e-stop opt isolator normally pulls the CONTACTOR_EN pin high unless e-stop is pressed?

> **Christopher Kalitin** (Dec 2025)
>
> @Hemat Wander
> 
> Yes floating because of the diode.
> 
> I think your design would work and it does remove a part from the overall system, I can think of only 2 suboptimal points:
> 1. The pull-up resistor is farther from the gate of the MOSFET
> 2. It doesn't follow the standard open-drain active-low topology
> 
> So, if we think there are no fundamental issues with my implementation I'm going to keep it.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Nov 2025

![](images/image_2577241363.png)

Above is the standard block for contactor / precharge relay control.

It contains:
- An NMOS to toggle current flow controlled by an STM32 pin
- A flyback schottky diode for the reverse voltage spike when current stops flowing through the contactor/relay coil
- An LED to show the contactor is active

Improvements over ECU rev 2.0:
- Using a schottky diode instead of a standard 0.7 V Vf diode
- LED not powered by STM32, instead directly from 3.3 V

![](images/image_2577242588.png)

Note that all contactor/relay coil currents go through this NMOS. This way, the current sensor can manually open all contactors if it detects an overcurrent fault.

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

![](images/image_2478878695.png)

This is the final of the initial 8 schematic pages that are essentially copy and pasted from ECU rev 2.0.

This one has a few minor changes:
1. Flyback diode for fans instead of series diode
2. 1uF decoupling capacitors go to board GND instead of FAN_GND (differing from previous ECU design)

The use of a flyback instead of series diode increases the voltage the fans see (now 12 V instead of 12 V - forward voltage drop of the diode).

The 1uF capacitors used to go to FAN GND, which if the fans are disable (NMOS open), would have one end connected to positive 12 V and the other would be floating. This means the voltage across the capacitors would be undefined and could float to any given value.

The NMOS used is the same as the one on ECU rev 2.0, it has an 8.3 A current limit so should be sufficient. The current V3 pack has 4 1.25 A fans.

> **Samuel Shin** (Oct 2025)
>
> 1. Do you know why we had series diodes before? I am wondering what was the reason behind it.
> 
> 2. What problems could be caused if the capacitor's voltage is undefined and be floating?
> 
> 3. Have you looked into using a different NMOS? From slack @Deev Shah mentioned that each fans take around 1.25A. 4 in parallel means 5A.

> **Christopher Kalitin** (Oct 2025)
>
> @Samuel Shin
> 
> 1. Mischa said this was an incorrect design decision, they just didn't think enough about it.
> 
> [https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0](https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0)
> 
> ![](images/image_2479104516.png)
> 
> 2.
> If it's floating it could go to any given value due to EMI, potentially something dangerous. It's just a good design practice to not let this happen.
> 
> 3.
> 8.3 A > 5 A so we should be fine.

> **Samuel Shin** (Oct 2025)
>
> @Christopher Kalitin
> 
> 1. I understand. From what he is saying, however, is tht there is already a flyback or series diodes inside the fans, why do we need to add more?
> 
> 3. I understand that we are fine, I meant as in lower performance from 8.3 A to something closer to 5A which will save a little bit (probably not sufficient) cost.

> **Christopher Kalitin** (Oct 2025)
>
> @Samuel Shin
> 
> 1.
> Some fans BTM could choose have internal flyback diodes. When they decide on one we'll have to reevaluate this circuitry. Or, keep the diodes in (~$1) for good measure in case we want to swap out the fans in the future.
> 
> 3.
> The cost difference would be tens of cents per FET, a few dollars for the whole board. So, I didn't put too much effort into finding another option. We've also got good margins with this FET.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin @Samuel Shin good to check if the fans have an internal flyback. If you can show this then lets add it to an update. Additionally consider using a **Schottky **diode. See the [Driver Fan Board](https://ubc-solar.365.altium.com/designs/1D270496-DEEE-4245-8B1E-CFA33C9CBAB5?variant=[No+Variations]&activeView=SCH&activeDocumentId=E_PAS_DFB1.1.SchDoc&location=[1,95.68,26.62,35.19]#design) as an example.

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> I replaced it with a Schottky diode. Contractor control also didn't have any flyback diodes so I've added those in.
> 
> I was using the same diode as ECU rev 2.0, so none of the flyback diodes on ECU were schottky's. I'll attribute this to Mischa's most common answer in such cases, that they were junior designers (but Nic Ricci too? Come on!).

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** 11h

**Simulating Optocoupler DCH_ON Circuit**

LTSpice sims saved [in the Drive](https://drive.google.com/drive/folders/1d_N84UDBGEXQGZUtdiL4UZMFQ7Z3tRlc?usp=drive_link).

**Problem Background**

![](images/image_2743899550.png)

I
was concerned the circuit above wouldn't work due to R11.8, the emitter
pull-down / load resistor. I simulated pretty much the same circuit
shown above, where it's very important for emitter voltage to rise high
enough to close the MOSFETs.

**Problem Description**

As described in the [previous update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18134735438/posts/4850567476),
I used an RC circuit to extend the pulse of DISCHARGE_GND_IN by ~10x to
ensure that even a pulse as short as 2 ms will extend to be long enough
to latch the discharge relay.

<img src="images/image_2743899543.png" width="169" height="121">

![](images/image_2743899536.png)

During
the team-wide DR yesterday, Saman pointed out I used a few
Optocoupler's incorrectly with common collectors instead of common
emitters.

Notice in the images above that an Optocoupler contains
an NPN BJT on the output-side. NPNs require V_BE > 0.7 to conduct.
If, for example, the emitter was at 3.3 V and the base was at 3.3 V,
then the NPN wouldn't conduct.

For an optocoupler, base voltage
is proportional to LED input voltage (Pin 1 in the first image of this
update). So, if LED voltage input is 3.3 V, base will be around 3.3 V.

This
could occur if the load-resistor is placed low-side (on the emitter)
instead of high-side (on the collector). My LTSpice sims below show this
topology.

In this case, voltage will drop over the low-side
resistor, meaning the emitter will be at GND + V_Resistor. There are
only two places in this circuit where voltage drops, the NPN (V_CE ~=
0.2 V) and the resistor. So, the resistor will drop most of the voltage,
and hence V_E ~= 3.3 V - 0.2 V = 3.1 V.

If anything is unclear, look at the circuit below and remember 2nd year circuit analysis.

**Theory As To Why The Circuit Would Work**

I had a theory that output voltage will converge to around V_CC - V_CE (3.3 V - 0.2 V) because the NPN wants to conduct.

Example of states:
1. V_LED = 3.3 V, V_C = 3.3V, V_E = 0 V -> NPN conducts (V_BE > 0.2 V)
2. V_LED = 3.3 V, V_C = 3.3 V, V_E = 3.1 V -> NPN reaches equilibrium

This however will only occur if the emitter resistor (R1 & R3 in the sim below) is of great enough resistance.

Important points:
1. NPNs are current sources
2. In optocouplers, their current is dependent on LED current and Current Transfer Ratio (~100% In:Out)
3. V=IR

Because we're limited in how much current can be produced, the emitter voltage is limited (V=IR, I is limited, R is a constant).

My
worry was that if the ratio of the input to output resistor (LED to NPN
resistor) was too small, the emitter voltage wouldn't rise high enough
to close a MOSFET (shown at the top of this update.

**Simulation**

![](images/image_2743899559.png)

I
simulated an optocoupler circuit in LTSpice and took a sweep of input
voltages. The green line in both graphs is input voltage, blue/red is
output voltage (emitter), and teal/pink is current through the NPN load
resistor.

Above you see two cases of the circuit:
1. Both have LED resistors of 100 ohms.
2. The first circuit (left circuit, top graph), has an NPN load resistor of 1000 ohms.
2. The second circuit (right circuit, bottom graph) has an NPN load resistor of 100 ohms.

Notice that when the NPN load resistor of 1000 ohms, the emitter voltage goes to ~3.1 V very quickly.

However,
if the NPN load resistor of 100 ohms, we saturated NPN current and it
only increases at LED input voltage increases. Hence, the NPN resistor
is current-limiting component, instead of the resistor being the
current-limiting component.

This results in emitter voltage slowly climbing, instead of quickly converging to 3.3V.

These
results simply tell us that using a 100 ohm LED resistor and 1000 ohm
NPN resistor is a valid circuit to get output voltage (at the emitter)
high enough for our purposes.

Hence, the circuit I showed at the beginning will work:

![](images/image_2743899556.png)

Note:

Yesterday R11.5 was a 1k resistor, which wouldn't have worked! Very good that Saman scrutinized my design days before ordering!

> **Christopher Kalitin** (11h)
>
> My original question to Saman:
> 
> ![](images/image_2743899651.png)
> 
> ![](images/image_2743899659.png)

---

## Differential + Common Mode Capacitors

**Author:** Christopher Kalitin

**Date:** Dec 2025

**Differential + Common Mode Capacitors**

![](images/image_2634711417.png)

First, I'll give some background on differential vs. common-mode noise. Differential noise is between two sense lines, and common-mode noise is between a sense line and ground. Both are protected against by using capacitors / RC filters, with the filter either between both sense lines or an individual sense line and ground. Read [this article](https://www.allaboutcircuits.com/industry-white-papers/emc-basics-common-mode-vs-differential-noise/) for more info.

![](images/image_2634708820.png)

I've added differential and common mode capacitors the shunt resistor sense lines. These are meant to eliminate noise of a particular frequency.

Here are the formula for finding differential / common-mode capacitor values as a function of series sense line resistance (10 ohms in our case) and cutoff frequency.

![](images/image_2634710360.png)

![](images/image_2634710293.png)

![](images/image_2634710581.png)

I chose a 10 ohm series resistance (R_IN) on each input line because such a small resistor will have a very low voltage drop over it. The INA228 shunt current sense amplifier has a 2.5 nA max bias current (ADC pin input current). V=IR, 2.5 nA * 10 ohm = 25 nV.

Our shunt resistor will have a 6 mV max voltage drop across it, so 25 nV error is fairly insignificant. Also note this is max bias current, the nominal value is 0.1 nA, 25x lower.

The internet tells me selecting common mode cutoff frequency higher than differential cutoff frequency is best practice.

So, I selected:
Differential Cutoff Frequency = 10 kHz
Common-mode Cutoff Frequency = 1 MHz

This gives these capacitors:
Diff Cap: 0.796 nF
CC Cap: 15.9 nF

I chose to use the closest standard values to these capacitances, 1 nF and 10 nF.

Note that adding capacitors will increase the amount of time it takes for a measurement to settle. This is an issue if we want to detect a fault current extremely quickly.

![](images/image_2634714042.png)

The time constant of our RC filter is a function of its cutoff frequency. At 10 kHz, the time constant is 15 us. To get to 5 tau will take us 75 us. This is still fast enough that we'll likely detect a short before the fuse blows, but if I chose a 10x lower cutoff frequency, this may not be true.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin The justification for the addition of common mode **and **differential noise filters makes sense. I also agree with your reasoning of choosing a 10ohm  One question I have as well is why are you choosing a differential cutoff frequency as 10khz? I'd suggest referencing other circuits across the car to check what their cutoff frequency as a point of comparison.
> 
> Also, note that the capacitors you spec-ed out for the common mode noise rejection are **50V tolerant**. I'd suggest using the 200V tolerant ceramic capacitors on digikey as an alternative.

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> Most of the reason for choosing a cutoff frequency of 10 kHz is that if we get lower we increase response time. Are there any other circuits in the car that are filtered in a similar way?
> 
> I think the 50V tolerant capacitors should suffice because the shunt is on the low-side of the battery. This is the same principle as the current sense amplifier IC only being rated for 80 V.
> 
> It also simplifies the BOM to use a standard capacitor.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> I agree with using 10khz given your tau calculation. I gave you a bad tip, I originally thought the PVA (since it has a differential pair output that is susceptible to common mode noise & differential noise) might have this filtering, however since it is a line that sends a quick changing (dv/dt >= 1v/s) signal (can treat this effectively as data), adding caps would be counter intuitive. I can't think of any other parts on the car that use this type of filtering, but I agree with your calculations.
> 
> Ah, thanks for correcting me with mentioning that the shunt is on the low side. You are correct, the 50V tolerant capacitors will suffice.
> 
> Well done on catching these details!

---

## System Overview

**Author:** Christopher Kalitin

**Date:** Oct 2025

[Altium page link](https://ubc-solar.365.altium.com/designs/39582840-6999-40D9-89D8-9774BDE86C17?activeView=SCH&activeDocumentId=CURRENT_SENSING.SchDoc(9)&variant=[No+Variations]&location=[1,94.16,28.36,35.59]#design)

![](images/image_2525419557.png)

@Aarjav Jain @Krish D @Hemat Wander Please look over this schematic for any issues or mistakes.

For future reference, find current sensor research under [this Monday card](https://ubcsolar26.monday.com/boards/9565350285/pulses/18164045278). This update is a high-level overview. All competent selection notes are in the research card.

Shunt Current Sensor Datasheet:
[https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074](https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074)

**System Overview**

**1. INA228 - Current Sense Amplifier**

[Datasheet](https://www.ti.com/lit/ds/symlink/ina228.pdf?ts=1761932938428&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FINA228)

The INA228 is a current sense amplifier which senses the voltage over our 100 micro ohm [shunt resistor](https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074), then amplifies this voltage before reading it through an internal differential delta-sigma ADC.

Because V=IR, any voltage reading can be translated into a current reading by using the resistance as a conversion factor.

The INA228 communicates over I2C and must be configured every time it turns on. So, a configuration packet consisting of full-scale range, current fault thresholds, etc. will be sent during the startup sequence of the HVC.

We use the fault pin on the INA228 in case I2C or our STM32 fails (eg. bus hangs due to misconfigured peripheral, pull-up resistor improperly soldered, infinite while loop in firmware, etc). This pin can be configured to be pulled low (it's default high with a 10k external resistor) whenever we get an out of range current fault.

We can wire this fault pin[like we currently wire the DOC_COC pin on ECU rev 2.0](https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0#heading=h.ga3334jxacjk), where it disables power to all contactors if a fault occurs. The INA228 has a latching mode for faults ([see section 7.6.1.12 bit 15](http://7.6.1.12)), so we don't need external CMOS latch circuitry (like is present for over current faulting currently).

**2. NEK0303SC - Isolated DCDC**

[Datasheet](https://www.digikey.ca/en/products/detail/murata-power-solutions-inc/nke0303sc/1926989)

Because the INA228 differential inputs touch the shunt resistor, it is in contact with high voltage and must be isolated from the rest of the HVC.

To isolate power, we use the NEK0303SC DCDC converter which takes in a 3.3 V input and outputs isolated 3.3 V.

Note that this component doesn't exist in Altium Manufacturer Part Search so I had to make it manually, while triple checking footprints.

**3. ISO1541**** - I2C Isolator**
[Datasheet](https://www.ti.com/lit/ds/symlink/iso1540-q1.pdf?HQS=dis-dk-null-digikeymode-dsf-pf-null-wwe&ts=1761945132950&ref_url=https%253A%252F%252Fwww.ti.com%252Fgeneral%252Fdocs%252Fsuppproductinfo.tsp%253FdistId%253D10%2526gotoUrl%253Dhttps%253A%252F%252Fwww.ti.com%252Flit%252Fgpn%252Fiso1540-q1)

![](images/image_2525458564.png)

In the same vain as the NEK0303SC, we need to isolate the I2C output of the INA228. TI makes the ISO1541 for this purpose, and it seems like a relatively plug and play chip.

The typical application circuit shows an isolated power source (like our DCDC), 100 nF capacitors on each power pin, and 1.5k pull up resistors.

I only differed from this by using 10k pull up resistors. If this

**4. LTV-817S - Optoisolater for Fault Pin
**[Datasheet](https://www.digikey.ca/en/products/detail/liteon/LTV-817S-TA1/388451)

I am using the same optoisolater for the fault pin as for ESTOP on HVC. 10k current limiting resistor for the LED side, pull down for STM32 side.

> **Aarjav Jain** (Nov 2025)
>
> @Christopher Kalitin:

> **Christopher Kalitin** (Nov 2025)
>
> @Aarjav Jain
> 
> 1.
> Good point. I've just checked over the INA228 datasheet again and confirmed that all values are reset to 0 or default values on power cycles. Ie. it's all volatile memory.
> 
> ![](images/image_2532764332.png)
> 
> ![](images/image_2532763969.png)

> **Hemat Wander** (Nov 2025)
>
> Some notes about the schematic:
> 
> - For the LV control schematic, I think we should include an extra control for the low voltage going to the distribution board on the other side of the car. i.e. the GND we feed them is not actually directly GND, but rather a GND controlled through a MOSFET. I'm not sure if you got to that yet.
> - Is the e-stop LED supposed to have have 100 ohms of resistance? Some of the other ones have 1000 ohms?
> -  I'm not entirely sure how this works, but you might want to check the current transfer ratio of the current alert isolator, because the datasheet it can be anywhere from 50%-300%. If you want saturation at the output of the isolator (3.3V) you need a roughly 200% CTR as the input resistance is double the output resistance?
> - How did you select 10K for the pull-resistances for the I2C lines? In the datasheet there's an example going as low as 1K, which allows for a faster communication rate. Again I'm not sure how fast the communication rate is going to be set to be, but you might want to check if that's fine.
> Also, I'm not sure exactly how you were going to connect this to the STM32, but if you also use pull-up resistors on the STM32 side, make sure that the resistor values is parallel are under the current limit of each component?
> 
> Otherwise looks really pretty kind of sort of maybe good

> **Krish D** (Nov 2025)
>
> @Christopher Kalitin  @Aarjav Jain Some notes for feedback from your current sensor schematic:
> 
> - I don't see scrutineering circuitry incorporated into this. I came up with a general concept and would love to see if you can make this better and improve on it. Note that the net's aren't labelled and usage of separated polygons could be minimized if routed well. Please let me know what you think.
> 
> ![](images/image_2541849556.png)
> 
> - Can we include a 2 position connector to use the hall effect as a backup? This would be our first time using the shunt. Wiring and control board integration **may** show that it is not feasible. Including this back up 2 pos connector and 1.8V reference circuitry doesn't seem like a bad idea in the case the shunt current sensor circuitry is rendered ineffective. Thoughts here.

> **Christopher Kalitin** (Nov 2025)
>
> @Krish D
> 
> 1.
> Added the voltage divider for scrutineering, it's about the same circuit as what you drew just formatted for Altium.
> 
> ![](images/image_2541851926.png)
> 
> 2.
> I'll be breaking out unused GPIO pins on the HVC (like a Nucleo does) so we'll have the ability to add in a hall effect if shunt doesn't work.

> **Krish D** (Nov 2025)
>
> Sounds good. Thanks Chris!
> 
> Also if you are planning to do 100 and 100k, your expected voltage to mimic 60A would be 6.006V. Do you think is important to use a larger voltage range in the case the voltage source used at comp has a smaller voltage-toggling precision, thereby limiting it's ability to show incremental steps?
> 
> Please justify this when choosing the resistor values.

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** 3d

**Resolving LTC4421 Shutdown Issues**

Two issues, one critical:
1. INTVCC is near its current max
2. INTVCC is 0 V when the shutdown (SHDN) pin is low

**Issue 1:**

<img src="images/image_2732651084.png" width="339" height="137">

<img src="images/image_2732652838.png" width="293" height="157">

Reading the datasheet, I found that the INTVCC pin can only supply up to 500 uA of current. The current design uses INTVCC on the output of an optocoupler with 10k resistor providing the current through the transistor.

3.9 V (INT_VCC voltage) / 10,000 ohms = 390 uA

This would likely work, but I doubt its how INT_VCC is meant to be used. It's likely only a method of specifying a logic level, and not meant to provide any current.

**Issue 2:**

As described [in this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080990623/posts/4773895719), the current plan for startup of the car is to wake up the LTC4421 power path prioritizer, and then it'll start supplying 12V_Supp to the HVC, which then goes through the usual startup sequence.

The previous plan was to tie INT_VCC to the SHDN pin of the LTC4421. This way, when the optocoupler shown in the previous section conducts, the SHDN pin is pulled up to INT_VCC and the LTC4421 turns on.

However, when SHDN is low the LTC4421 is in a low-power state meant to minimize quiescent current (~6 uA), so the LDO that provides INT_VCC is disabled.

Hence, there is no source of voltage to pull SHDN high, and the LTC4421 can't turn on, so the car won't turn on.

**Solution
**
Connect SHDN to 12V_SUPP_TOGGLED (after checking voltage tolerance of the pins) instead of INT_VCC.

Functionality is the same, SHDN goes to >1 V while the startup switch it toggled on.

![](images/image_2732711213.png)

![](images/image_2732710657.png)

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Jan 5

I found out what the RC Snubber circuit is for from this [Monday Update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080990623/posts/4654467464).

Essentially, the purpose of an RC Snubber circuit is to reduce the voltage spike due to parasitic inductance of traces and wires. A capacitor is added to reduce the spike, and a resistor is added to reduce the amplitude of the oscillations of the RLC circuit that results.

<img src="images/image_2657876281.png" width="305" height="236">

All our traces and wires have parasitic inductance. [Gemini estimates](https://gemini.google.com/share/6ff3db138302) 150 nH for 15 cm of PCB trace + wire going to our DCDC, using a rule of thumb of 1 nH per millimeter.

Our [SIJA58DP MOSFETs](https://www.vishay.com/docs/76203/sija58dp.pdf) used with the Power Path Prioritizer have a fall time of ~25 ns.

Using
the fundamental equation of an inductor, we can find what kind of
voltage is induced when the MOSFET open (eg. swapping to Supp from
DCDC).

Assuming current is 5 A:
V = L * di/dt
150 nH * 5 A / 25 ns = 30 V

30 V is a high voltage spike which we should avoid to not stress the MOSFET or DCDC.

I'm
skeptical that this is actually an issue because our MOSFETs are rated
for 40 V and the DCDC must have some protection circuitry, but if the
datasheet recommends it I'll listen. We'll follow industry standards
here.

![](images/image_2657898565.png)

If we just add a capacitor, we get an oscillating LC circuit without any damping (aside from trace resistance). This means the spikes are slightly smaller and stay around for a while.

The frequency of this oscillation is determined by:

![](images/image_2657915045.png)

The Snubber Capacitor on the HVC is current 1 uF, this results in an oscillation frequency of 411 kHz.

To ensure this noise doesn't stay around too long, we add a 1 ohm resistor in series to damp the system.

The resistor is sized so that the system is critically damped, using the usual equations we all certainly remember from PHYS 158.

[This video](https://www.youtube.com/watch?v=wgNMepGIrTk) (very good video) shows a method for sizing the capacitor and resistor:
1. Determine inductance and current
2. Equate inductor energy to capacitor energy and solve for capacitance given a chosen V_capacitor_max value.
3. Solve for resistance using R = V/I where V = V_cap_max

1.
Inductance = 150 nH
Current = 5 A (Fine value to use for our LV system)

2.
E_ind = 1/2 * L * I^2 = 0.5 * 0.00000015 * 5^2 = 1.875 uJ (yes, micro joule)

V_cap_max = 12 V (arbitrary value that feels nice as our LV system operates at 12 V)

E_cap = 1/2 * C * V^2
E_cap = E_ind

E_ind * 2 / V^2 = C

C = 0.000001875 * 2 / 12^2 = 26 nF

3.
R = V/I = 12/5 = 2.4 Ohms

This capaitance and resistor of 26 nF and 2.4 ohms is much lower than what the LTC4421 datasheet recommends, 1 uF and 1.21 ohms. They must have assumed a far higher parasitic trace/wire inductance value.

I'll update Altium with 100 nF and 1 ohm, this seems to meet our expected inductance value better than 1 uF and 1 ohm.

> **Aarjav Jain** (2d)
>
> @Christopher Kalitin what about considering that Gemini suggested values that do not apply in our case and the datasheet was tailored based on their own testing? So your method of choosing 100nF if the range is 26nF to 1uF is mostly arbitrary and I couldn't see a reason not to continue with what the datasheet recommends (which again comes from their engineers actually testing this out).
> 
> Also, I cannot view your Gemini link to scrutinize what Gemini proposed.

> **Christopher Kalitin** (2d)
>
> @Aarjav Jain
> 
> Fixed the link.
> 
> Here's an [inductance calculator](https://www.allaboutcircuits.com/tools/wire-self-inductance-calculator/) that gives a similar result of 170 nH for 1mm diameter wire (18 AWG) and 15 cm.
> 
> ![](images/image_2735763782.png)
> 
> 100 nF is chosen not because it's in that range, but because it's far closer to 26 nF. The 150 nH number could be off by an order, and we'd still be at 260 nH which is closer to 100 nF than 1000 nF.
> 
> So, the rule of thumb 1nH/mm could be way off and we're still closer to being right than with a 1 uF cap.
> 
> I'd argue that using a rule of thumb and doing the calculations yourself to justify a part choice is far closer to being a competent engineer than *blindly* trusting the datasheet.
> 
> I found an [application note](https://assets.nexperia.com/documents/application-note/AN11160.pdf) that details the process of RC Snubber component selection in some more detail. On page 4 it gives a few conditions to check to ensure peak voltage is kept low enough (among other points), and my selected components meet these conditions.
> 
> Eg.
> (This is derived from equating the capacitors energy to the inductors energy)
> 
> ![](images/image_2735824665.png)
> 
> 100 nF > 150 nH * 5^2 / 12^2
> 1e-7 > 2.6e-8

---

## Redesigning Startup Circuitry

**Author:** Christopher Kalitin

**Date:** Dec 2025

**Redesigning Startup Circuitry**

**DCDC Power Path Prioritizer Design Flaw**

![](images/image_2637189271.png)

While in the shower yesterday I discovered a design flaw in my implementation of the LTC4421 Power Path Prioritizer.

The LTC4421 has two inputs and it sources current from the highest priority input that is at a valid voltage.

We set the DCDC as the highest priority voltage, and only use the Supplemental before we've connected the POS and NEG contactors, after which point the DCDC 12V output enters its nominal range (12V instead of 0V) and the LTC4421 switches to it.

Notice that our startup relay in the hand drawn schematic shown above is on the supplemental battery input. So, when the car is off the LTC4421 is unpowered, then the supplemental is connected, then we switch to DCDC.

After we've swapped to DCDC, it will remain a valid source of voltage until POS and NEG are closed. However, POS and NEG will not close when the Startup Relay open, and the DCDC will stay a valid source of LV power.

So, after the startup switch is turned off, the car will continue running off the DCDC.

Pretty major design flaw, we have no way of turning off the car.

**Solution: SHDN Pin**

![](images/image_2637197056.png)

The LTC4421 must be commanded to stop supplying DCDC 12V after the startup switch is turned off.

It has a Shutdown (SHDN) pin that will turn off the IC if the voltage on the SHDN pin is below ~1 V.

So, the solution to the design flaw is to connect the Startup Switch to the SHDN pin.

![](images/image_2637228800.png)

I achieved this by using an optocoupler to translate the STARTUP_IN_GND net (floating while car is off, shorted to GND while car is on) into the STARTUP_INT_VCC net which is pulled to GND when the car is off, and connected to INT_VCC when the car is on.

INT_VCC is generated by the LTC4421 and is meant as the input to the SHDN pin.

**Deleting The Startup Relay**

While the Power Path Prioritizer is turned off, the car will have no 12V source.

This is the same purpose as our startup relay, to ensure the car has no 12 V source while the car is off.

So, we can delete the startup relay and use the Power Path Prioritizer in place of it, as it serves the same exact purpose.

Effectively, the startup relay is now replaced by the startup optocoupler.

**Supplemental Battery Quiescent Current**

One possible issue with not having a start up relay, is that SUPP_12V will always be connected to a few circuits on the HVC.

While the car is off, 12V is disconnected from everything, but raw 12V_Supp voltage is used by a few systems.

These circuits are:
1. Discharge Relay Control
2. Startup Optocoupler
3. Supp Voltage Sense
4. Power Path Prioritizer Voltage Dividers

The discharge relay always has 12V_Supp connected but has ground disconnected, so no current can flow.

The Startup Optocoupler high-side is always connected to 12V_Supp, but current only flows when STARTUP_IN_GND is shorted to GND, ie. the car is on.

<img src="images/image_2637232054.png" width="285" height="129">

<img src="images/image_2637232400.png" width="146" height="141">

Supp Voltage Sense and the Power Path Prioritizer voltage dividers are a more complicated case. They are always connected to 12V_Supp, and their negatives would always be connected to GND, allowing current to flow even if the car is off.

To solve this problem, we add a a net for STARTUP_TOGGLED_GND. This is controlled by an NFET so that it is disconnected from GND while the car is off, and connected to GND when the car is on.

This way, we've eliminated all sources of quiescent current on 12V_Supp.

**Deleting ESTOP Relay**

ESTOP and contactor disconnection circuitry is explained in more detail in [this Monday Update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080995210/posts/4770869948).

After I removed the Startup Relay, I reevaluated whether we need the ESTOP Relay.

The purpose of the ESTOP Relay is to disconnect 12V from the contactors when ESTOP occurs. This is a hardware redundancy to ensure the HV battery is disconnected from the car when ESTOP is pressed

![](images/image_2637240833.png)

I realized that I had already implemented this functionality with the Contactor Enable NFET. This NFET disconnects all Contactors Grounds when CONTACTOR_EN is pulled to GND, disconnecting the HV batteries from the car.

![](images/image_2637247977.png)

I made slight changes to the ESTOP Optocoupler so that it would be compatible with the CONTACTOR_EN pin.

Now, by tying the ESTOP_3V3_OPEN_DRAIN pin to CONTACTOR_EN, we give ESTOP direct hardware control to open all contactors when its pressed.

By extension, we can delete the ESTOP relay because it's now redundant.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> This is a great summary of your changes, it makes a lot of sense!
> 
> Is there any reason you didn't want to simply replace the startup relay with a double-pole single-throw relay to toggle both the supp and the DCDC as inputs to the LTC4421? This would effectively do the same thing, and to me this seems as the most direct way to ensure there is no power coming into the car. Your circuit optocoupler circuit is still serving the same purpose as the startup relay.
> 
> I'm a bit confused regarding the implementation of the STARTUP_TOGGLED_GND. What is the purpose of the NFET to connect this to GND? The startup switch itself is already acting to toggle if the supp's GND is connected to the rest of the HVC, so is this FET not redundant?
> 
> If there is an edge case here that I didn't see, please let me know!

> **Hemat Wander** (Dec 2025)
>
> @Christopher Kalitin  Everything seems to make sense, but adding onto @Krish D 's point, I don't see why an optocoupler is required for the startup? Why not just have the startup switch short INT_VCC and STARTUP_INT_VCC?
> 
> If startup_GND is being used somewhere else and so is required anyways, why not have this be an NMOS instead of an optocoupler.
> 
> ![](images/image_2637644296.png)
> 
> Also why not just have STARTUP_TOGGLED_GND just be STARTUP_IN_GND?

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> Have a DPDT Relay would be redundant as we've already got the back-to-back MOSFETs serving the same purpose.
> 
> Back-to-back MOSFETs are a farily standard design in industry, so I'm not too worried about it.
> 
> Here's a link to the E-Bike BMS I posted in Slack a while ago that uses back-to-back NFETs:
> [https://github.com/nhallsny/faraday-rescue](https://github.com/nhallsny/faraday-rescue)
> 
> @Krish D @Hemat Wander
> 
> Using an optocoupler for STARTUP_IN_GND follows the same logic as ESTOP_12V_IN. It's a wire that's going all over the car, so is susceptible to EMI.
> 
> To prevent potential issues with the stability this ground, I use it to toggle STARTUP_TOGGLED_GND, which only lives on the HVC and doesn't go all over the car.
> 
> This is the same reason why I don't want to be INT_VCC on the driver startup switch line.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> Isolating grounds makes sense, but note that the stability should be negligible since the GND polygon on the ECU is literally the entire board (except for the discharge relay), and therefore is less of an issue. The principle of toggling grounds here makes sense as a design principle, however I don't believe it is necessary. I'll let you decide whether this is still a requirement or not. Please justify this with a small note on the HVC as you've done with the described signals aswell!
> 
> I more so meant that the DPST can be used for toggling off both the DCDC converter and the supp as inputs to the LTC4421. This to me serves as the most direct way to ensure there is no power inputs (If startup switch is turned off, LTC4421 can not switch to either of the inputs).

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> In the case of STARTUP_IN_GND, the ground is not the entire PCB. The ground is sourced from the PCB, but then goes on a long path all around the car and picks up noise along the way.
> 
> Will add a note.
> 
> Yep DPST is a way to be certain that both supp and DCDC can't provide power, but back-to-back NFETs are also an industry standard way to achieve this.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> I see your point. This was never an issue on V3, since the GND plane was considered highly stable, but this is definetly a more robust way to prevent any form of noise from distributing through the HVC.
> 
> I meant using the DPST to ensure that the car turns off after being turned on. The double NFET doesn't prevent the DCDC from still being a valid source (as you mentioned in your update).  I think that using a DPST relay avoids the need to use the SHDN functionality as well.

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> 1.
> 
> Slight correction to your wording:
> 
> The PCB ground plane isn't an issue, it is highly stable!
> 
> The issue is that STARTUP_GND_IN is not the ground plane, and has gone all over the car before it's gotten back to the HVC, hence why we put it through an optocoupler and toggle an NFET instead of using it directly.
> 
> 2.
> 
> Put another way, using the SHDN pin avoids the need to use a DPST. I'm biased towards the solution that uses fewer components.
> 
> Note that the DPST also doesn't prevent the DCDC from being a valid source, but opening it means the contactor coils have no power, hence the DCDC has no HV source. Same principle as the NFETs.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> Sounds good. I'm a bit confused with the exact purpose of the back to back NFETs, if you could clear this up that would be appreciated!
> 
> Do you think it is also worth reading from startup gnd from the MCU? (This way if the car if startup switch us turned off, the MCU can also toggle POS and NEG, alongside the power path pritoizer toggling the SHDN pin. This makes of firmware and hardware as redundancies. Since keeping the car off when it is supposed to be is safety critical, I think this would be fair to implement.
> 
> CC: @Aarjav Jain @Hemat Wander

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> 1.
> 
> ![](images/image_2639659594.png)
> 
> Ah, the back-to-back NFETs serve exactly the same purpose as a DPST relay would. Literally exactly the same outcome (no current flow in both directions), just a different method. Should've made this clearer.
> 
> In the typical application above you can see how we have a pair of back-to-back NFETs on each LV input.
> 
> This is functionally identical to having an SPST on both inputs, except that because they're semiconductors their switching time is far faster than a mechanical relay.
> 
> 2.
> 
> Reading STARTUP_GND_IN is an interesting idea, I'll think about it.
> 
> If STARTUP_GND_IN is floating, there will be no power so the MCU will be off. But as a redundancy there's some merit.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> I see, this makes more sense now. Your justification for a relay vs the back to back NFETs is clear.
> 
> I'll point out that this logic only works if the SHDN pin of the LTC4421 functions as expected. <- I know this sounds obvious, but I'd like you to consider if there any other failure modes of the circuit that are accounted for with a relay.
> 
> Otherwise, this makes sense.

---

## Reading The Supplemental Valid Pin

**Author:** Christopher Kalitin

**Date:** Nov 2025

[@Museok Seo](https://ubcsolar26.monday.com/users/66935094-museok-seo) [@Michelle Hu](https://ubcsolar26.monday.com/users/66782803-michelle-hu) [@Aarjav Jain](https://ubcsolar26.monday.com/users/66722948-aarjav-jain) [@Krish D](https://ubcsolar26.monday.com/users/66710612-krish-d)

An LED and GPIO input needs to be added to the DRD because of changes to the startup circuitry. This updates describes required changes.

**Reading The Supplemental Valid Pin**

As discussed in the final section of [this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080990623/posts/4654467464), there is a pin on the LTC4421 Power Path Prioritizer that tells us if the supplemental is in its nominal voltage range.

If the LTC4421 is outside of its nominal voltage range, it will not be connected to the output. In this case, even after the driver has flipped the startup switch the car will not turn on because the supplemental is at too low a voltage.

For this contingency, we need to connect the valid pin of the supplemental to an LED so we are aware it is outside its nominal range. This LED must be present both on the HVC for debugging and on the DRD so the driver knows the status of the car.

The supp valid pin of the LTC4421 is pulled low if it is outside its nominal range. So, a PMOS can be used on the HVC to invert the signal to activate an LED.

For labelling, we can call this LED Supp Invalid.

Next Steps:
1. Implement PMOS on HVC to invert the GPIO

2. Implement Supp Valid LED on HVC
2. Output inverted Supp Invalid pin to DRD (Through the junction board, across the car)
3. Implement Supp InvalidLED on DRD

What will change on DRD:
1. Instead of reading one GPIO from HVC, read two (Fault and Supp Invalid)
2. Add another LED for Supp Invalid

Note that this Supp Invalid is not like our previous Supp Low LED. Supp Low was a warning when the Supplemental was below 10.5 V, but we would still run the car. Supp Invalid means the car will not start up, and we're turning on this LED so it's clear why we're not turning on, making debugging simpler.

@Museok Seo
Furthermore, because the DRD will not be powered in the Supp Invalid case, the connector supplying the LED power needs to include a ground wire.

If the car doesn't startup, the DRD will not be on but we still need to activate the Supp Invalid LED. So, we need to supply both power and ground in a separate wiring harness.

Ie. the current schematic for the FLT LED would not work for this. The Supp Invalid LED input must power the LED, and the ground must not be board ground, but a ground specific to the Supp Invalid LED.

![](images/image_2573134745.png)

---

## Startup Circuitry Relays

**Author:** Christopher Kalitin

**Date:** Nov 2025

**Startup Circuitry Relays**

![](images/image_2557456236.png)

With the power prioritizer schematic block done, now we need to find the relays involved in the startup circuitry.

Relay requirements:
- >10 A current rating

- Low coil current (30mA or less, going off current ECU relays)
- 12 V coil voltage

I put these requirements into Digikey part search and found this relay:
[PR9-12V-200-1A](https://www.digikey.ca/en/products/detail/same-sky-formerly-cui-devices/PR9-12V-200-1A/16752656)

Current rating: 16 A
Coil current: 16 mA
Coil voltage: 12 V

It's also relatively cheap ($1.61) and has a 10 ms operating time and 5 ms release time.

In the [HVC DR0](https://docs.google.com/document/d/1IN_0Pcg9eEbxtUkUSTO_Nc7S2LKmDKqyU20G1GsCJE0/edit?tab=t.0#heading=h.jhe8s63mkmtz) I arbitrarily set a requirement that we respond to ESTOP within 10 ms,  which is being met.

I imported the Altium component and got this schematic component:

<img src="images/image_2557457221.png" width="217" height="122">

It's not entirely clear what A1, A2, COM, and NO (normally open pin) are.

I found this source that specifies how to connect each pin:

![](images/image_2557458503.png)

[Image Source](https://er.yuvayana.org/relay-logic-circuit-rlc-relay-contactor-switch-and-timer/)

Now I just need to translate my sketch to Altium.

8 minute monday update speedrun.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Nov 2025

![](images/image_2553065728.png)

Schematic is complete: [link](https://ubc-solar.365.altium.com/designs/39582840-6999-40D9-89D8-9774BDE86C17?variant=[No+Variations]&activeDocumentId=STARTUP.SchDoc(10)&activeView=SCH&location=[1,165.1,-367.02,-213.65]#design)

Notes:
- Tying retry pin to INT_VCC makes it retry connecting a source after it has had an over current fault. We have no current sensing shunt resistor, so this is mostly useless for us. If there is an edge case where it detects current, in this case we'll be able to keep driving the car.
- Tying Disable to INT_VCC means both sources are enabled
- SHDN tied to INT_VCC means we never shut down
- CASIN tied to INT_VCC means we're not stringing many LTC4421's together (we're only using one).

I used the [SIJA22DP-T1-GE3](https://www.digikey.com/en/products/detail/vishay-siliconix/SIJA22DP-T1-GE3/13540658?curr=usd&utm_campaign=buynow&utm_medium=aggregator&utm_source=octopart) as the NMOS instead of the one the datasheet suggested, because I didn't want to make a footprint and this one had one on Altium.

Also used the [SMAJ30A-TR](https://www.digikey.com/en/products/detail/stmicroelectronics/SMAJ30A-TR/2873847?curr=usd&utm_campaign=buynow&utm_medium=aggregator&utm_source=octopart) TVS diode because I could find an Altium model for it, this was was pretty difficult to find a model for was pretty annoying.

---

## Designing LTC4421 Power Path Prioritizer Circuitry

**Author:** Christopher Kalitin

**Date:** Nov 2025

**Designing LTC4421 Power Path Prioritizer Circuitry**
[LTC4421 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4421.pdf)

Essentially what I'm doing in this update is taking this typical application circuit and tailoring it for our purposes.

![](images/image_2542417482.png)

Sections:
1. Choose Supp/DCDC UVR, UVF, OV resistors

2. TMR Capacitors
3. Cout selection

4. NMOS Selection
5. Snubber Circuit Exploraton
6. Zener Diode
7. Reading GPIO outputs

**UVR, UVF, OV Threshold Voltages & Voltage Dividers**

![](images/image_2542405883.png)

The LTC4421 has three pins that manage the overvoltage (OV) and undervoltage (UV) threshold voltages for each source.

1. UVF (Undervoltage falling): If a source falls below this voltage, it is labelled invalid
2. UVR (Undervoltage rising): Once a source is UV Invalid, it must rise above the UVR voltage threshold to be considered valid again, this provides for some hysteresis.
3. OV (Overvoltage): Simple, if you go above this voltage you are an invalid source.

Notice we're missing an overvoltage falling value, one that a source would have to drop below to be considered valid again (hysteresis). Internal to the IC, the OV falling threshold is set as 10% below the OV rising threshold. Eg. if OV rising threshold is 10 V, the source must return to below 9 V to be considered valid again. See the "Setting Valid Operating Voltage Range" Section of the datasheet.

We configure these voltages with a voltage divider. If any "rising" fault pin goes above 0.5 V, the IC detects a fault. If any "falling" pin goes below 0.5 V, the IC detects a fault. Eg. For a 10 V over voltage fault threshold, we use a 20-to-1 voltage divider, so that if the input is 10 V, the OV pin sees 0.5 V and triggers a fault.

**DCDC Voltage Threshold Values**

The DCDC has a nominal operating voltage of 12 V, and I'll assume +/- 1 V is a tolerable range. So, we set UVF to 11 V, UVR to slightly greater than 11 V (11.5 V), OV to 14 V. Because OV is 14 V, the internal OVF threshold is 12.6 V.

DCDC UVF: 11 V
DCDC UVR: 11.5 V
DCDC OV:   14 V

It's important to consider the overvoltage falling (hysteresis for invalid source) edge case because we want the DCDC to return to operation after an overvoltage event. If I picked 13 V, then the DCDC would have to return to 11.7 V to be operational again, and this is not its nominal value.

**DCDC Resistor Values**

Now with voltage values, we can pick resistors:

V_OV_bus = 14 V (over voltage bus voltage)
V_OV_trigger = 0.5 V (OV trigger voltage)
Voltage divider factor: 14/0.5 = 28x

V_UVF_bus = 11 V
V_UVF_trigger = 0.5 V
Voltage divider factor: 11 / 0.5 = 22x

V_UVR_bus = 11.5 V
V_UVR_trigger = 0.5 V
Voltage divider factor: 11.5 / 0.5 = 23x

Figure 2 of the datasheet (shown above) gives 3 topologies for defining fault voltages, I'll use the first option (farthest left) which is simply three voltage dividers. This is easiest to configure and change.

We notice all options require secondary resistor ~20x smaller than the primary resistor, so I'll baseline use of a 100k resistor and 10k trimmer potentiometer.

Note that we don't purely use a potentiometer because we want precise control of the very low end of the voltage range (ie. 0-1 V, not 0-12 V).

**Supp Voltage Thresholds & Resistors

**The exact voltages can be debated, I'll skip most of the math for now. Note that if supp is outside the nominal range, we'll have no way to startup the car as there'll be no connected 12 V source, so we should give a reasonably wide range.

Supp UVF: 9 V
Supp UVR: 9.5 V
Supp OV:   15 V

Voltage divider factors:
UVF: 18
UVR: 19
OV:   30

Again, a 100k + 10k trimmer pot will work.

**Current Faulting + Fault Time Capacitors**

![](images/image_2542424226.png)

The LTC4421 has the ability to current fault individual sources through using shunt resistors. We'll have an LVS current sensor so don't need to use the LTC4421 for this purpose.

To disable current faulting ability, we'll just tie the sense lines on both sources to output voltage, so voltage drop over them will always be zero and the IC will always be detecting 0 A.

TMR stands for "current fault timer" (see datasheet page 9) and configures how long a source can be in an overcurrent state before being considered invalid, and the chip falls back to a difference source.

Datasheet lists a value of 83ms/uF for fault time, and you'd choose a capacitor accordingly. We'll just put a 1 uF on both TMR1 and TMR2.

**Output Capacitor Selection**

![](images/image_2542420126.png)

Above you can see that there's around a 10 us switching time between sources (notice the time from voltage drop to rise on the left of the chart).

This means we only need to sustain voltage using a capacitor for about 10 microseconds (great improvement from 2-3 ms with a relay!).

"Typically, using 10μF to 50μF of output capacitance
per Ampere of maximum load current achieves a reason-
able trade-off." (datasheet page 16)

Going off this datasheet recommendation and an expected max current draw of 6 A, I'll choose a 100 uF capacitor.

What's also important to optimize for is ESR (Equivalent series resistance) of the capacitor. When a source switches off and we start pulling energy from the capacitor, we're essentially adding a resistor in series with the LV system of the car. This resistor has a voltage drop which we have to consider, and choose a component with low ESR.

Voltage drop due to capacitor ESR:
V_drop = I * R_esr

With I = 6 A as the expected max, we see that an ESR of 100 milliohms would result in a voltage drop of 0.6 V. This is a reasonable value to aim for, [here's a capacitor on Digikey](https://www.digikey.ca/en/products/detail/rubycon/50ZLH100MEFC8X11-5/3563386) with C=100 uF and impedance=74 mohms.

**NMOS Selection**

Requirements:
- >6 A current rating
- Low on-resistance
- Vgs(th) < 5 V (limit of the LTC4421, hopefully we're well below)

The datasheet recommends the PSMN4R0-60YS with a current rating of 74 A and on-resistance of 4 milliohms. It's also out of stock on Digikey.

Note that most FETs at very low on-resistances also have very high current ratings, which is why we're going well above that requirement.

Digikey suggested the [RJK0653DPB](https://www.digikey.ca/en/products/detail/renesas-electronics-corporation/RJK0653DPB-00-J5/2772898) as a replacement at 45 A, 4 milliohms, Vgs(th)=2.5 V, and $5.71 per FET with 3,816 in stock. Good option, if this has an Altium footprint I'll use it.

**Snubber Circuit**

<img src="images/image_2542427190.png" width="207" height="177">

The datasheet reccomends a ~1 ohm resistor and ~1 uF capacitor on the input of both sources as a snubber circuit that dampens oscillations so that peak current is limited in transient events (eg. switching source)>

I don't fully understand this but will trust the datasheet and will go with 1 ohm + 1 uF.

At some point in the next few weeks I'll certainly be nerd snipped into asking the LLMs about this for an hour while on the bus.

**TVS Diode**

You can also see in the image above that a TVS diode is recommended on each input for overvoltage protection (eg. release of inductive energy supply-side). I'll again just trust the datasheet on this one and use the [SMDJ36A](https://www.digikey.ca/en/products/detail/littelfuse-inc/SMDJ36A/1835327) TVS diode with a 58.1 V clamp voltage. This feels pretty high, but it's what's recommended for a 12 V source on the datasheet (page 13).

**What's Next?**

All non-trivial circuit elements are defined with possible parts to use from Digikey, all other circuit elements are simple capacitors. Now just to implement this in Altium, then probably run into some fun trouble routing all of this in a month.

**Which Output Pins Should The STM32 Read?**

![](images/image_2542432275.png)

One last thing, the LTC4421 has 6 output pins (open-drain GPIOs) we can read:
Valid pins: Pulled low if a source is outside it's specified voltage range
Channel pins: Pulled low when a given source is active
Fault pins: Pulled low when an overcurrent fault occurs

Fault pins are useless to use because we're not using the current sensing shunt resistor.

The Supplemental's valid pin is useless because we'd have no way to read it if the supplemental is not powering the PCB.

The DCDCs valid pin could be useful to know if it's voltage isn't where we expect. In practice however, I expect that if we see we aren't switching to DCDC we'll get far more information debugging by probing DCDC voltage manually, so there isn't a case where this pin is very useful.

The channel pins are very useful to us to know if we are in an expected state or not. Eg. while the car is driving we always want to be on DCDC and not Supp so we don't drain it. By observing both channel pins and adding a flag in firmware, we'll know if we're erroneously draining supp while driving. Otherwise, we'd be slowly seeing supp be drained and find out about the problem 30-60 minutes after it started.

> **Krish D** (Nov 2025)
>
> Great update here, @Christopher Kalitin! This is a great in-depth explanation regarding the implementation details of the chip. The sectioning makes it quite easy to follow and the added calculations are easy to follow. Keep it up!
> 
> **Here are some technical notes and questions I thought of while looking more into the chip:**
> 
> - Regarding the Supp voltage thresholds, it's worth noting that our [current supp](https://www.batteryspace.com/NiMH-Battery-Pack-12V-5000mAh-CUJAS155.aspx) will be at a maximum of 14.5V when fully charged, so it's good that you choose 15V at the supp_OV. You also mention that all voltage thresholds "can be debated". What needs to be done to finalize the respective values? An analysis of edge cases should be conducted to make this more concrete/justifiable <- Assuming the values you chose are what you think we should use.
> 
> - In person we also mention adding a secondary current sensor as the full check that determines if supp is being drained? (In the edge case that the PMOS-es conduct despite the logic not functioning as expected?) This may be more advantageous than reading the channel pins don't directly tell you if current is being drawn or not. Is this still necessary?

> **Christopher Kalitin** (Nov 2025)
>
> @Krish D
> 
> 1.
> -15 V max seems like a good value then. All that's left to be determined is the minimum voltage threshold, for which 10 V seems reasonable.
> 
> From datasheet: "Please don't discharging the battery pack below 10V  ( 1.0 V / cell)  Deep discharging may damage NiMH battery pack."
> 
> The only potential issue is that this is a circuit that'll disable the car from starting up, currently without any indication of this, potentially making debugging more annoying for future BMS members.
> 
> We could add an LED on the Supp Valid pin so that we can know if it's outside its nominal range. Otherwise, we'd flip the startup switch and nothing would happen and we'd be left guessing.
> 
> 2.
> If the LTC4421 tried to switch to a different source and it didn't work (and if it didn't fall back to the other source), then the LV system of the car would have no power and it would shut down. So there's no use in taking current measurements in our last 100 ms of operation before an inevitable power cycle.
> 
> For my own future reference: the datasheet recommends pull-downs on the NMOS sources but doesn't show it in the typical application circuit:
> 
> ![](images/image_2547263726.png)

> **Christopher Kalitin** (Nov 2025)
>
> Quick note: The LTC4421 powers itself using an internal LDO that supplies current from either the output voltage, input source 1, or input source 2.
> 
> <img src="images/image_2547318736.png" width="353" height="199">

---

## Supp-DCDC Swap Circuitry

**Author:** Christopher Kalitin

**Date:** Nov 2025

**Supp-DCDC Swap Circuitry**
**
Current ECU Design**

We currently swap between DCDC and Supp with a relay that is driven by the STM32. After the POS and NEG contactors close, we swap the 12 V source from Supp to DCDC.

The issue with this setup is that while the relay is swapping between it's contacts, there is no connection from board 12 V to any 12 V source. While this occurs, we're discharging a 1000 uF capacitor to have a voltage source for the 2-3 ms switching period.

Charging this 1000 uF capacitor at startup induces a current spike, which we'd like to avoid.

There's a section and comments in [this monday update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9721351653/posts/4389304604) on this topic for more info.

**Possible Solution: Power Prioritizer
**
A Power Path Prioritizer is a type of IC that selects from a few input voltage sources to drive an output. This way, we can hook up the DCDC and Supp and let the IC do the switching for us in microseconds, necessitating a much smaller capacitor and hence a smaller current spike.

Most Power Path Prioritizers assign a priority to each input and use the highest priority input that is at a nominal voltage. In our case, this means use the DCDC if it's in the range of 11-13 V, otherwise, use the supplemental if it's in the range of 9 to 15 V, otherwise, do nothing (supp is way outside the nominal range).

![](images/image_2541954364.png)

The nominal voltage ranges are defined by voltage dividers as you can see in the LTC4417 typical application above.

![](images/image_2541958306.png)

Above is the two back-to-back P-channel MOSFETs all power path prioritizers use to toggle current flow. With just one MOSFET, you can always conduct backward through the body diode, including two means current flow back into a source is prevented. [Read this for more info](https://www.homemade-circuits.com/bidirectional-switch/).

**Power Path Prioritizer IC Options**

Our requirements for a power prioritizer are:
- 0 to 15 V input range
- >6 A current max
- Requires relatively small capacitor (eg. not >100 uF)
- Hand solderable (in case pins are shorted, so we can rework it)

IC Options:
- [LTC4417](https://www.analog.com/en/products/ltc4417.html)
- [LTC4418](https://www.analog.com/en/products/ltc4418.html)
- [LM74800](https://www.ti.com/lit/ds/symlink/lm7480-q1.pdf)
- [LTC4421](https://www.analog.com/en/products/ltc4421.html)

The LTC4417 has 3 input channels (we only need two), comes in an SSOP package (reasonably hand solderable), and has GPIO outputs that tell us if each input is in its nominal range of not.

<img src="images/image_2541955318.png" width="147" height="134">

LTC4418 QFN Package

The LTC4418 is what Waterloo uses. It has two input channels (more ideal for us), but only comes in a QFN package which is not hand solderable. Using a QFN means we must reflow / heatgun the IC to remove / place it, and will have more trouble with short. Reworking becomes significantly more difficult, so I'm discounting this option.

@Michelle Hu said Mischa said the LM74800 is what Tesla uses. In her first year on the team she design (didn't bring up) [this board](https://ubc-solar.365.altium.com/designs/9D893F0C-FCB9-49FD-B305-6A68F37502B3?variant=[No+Variations]&activeDocumentId=NMOS_PP_Schematic.SchDoc&activeView=SCH&location=[1,95.43,94.52,66.68]#design) with it. It uses one IC per voltage supply with a nominal voltage range, it's not immediately clear to me how it ensures only supply doesn't feed into another (eg. Supp "Charging" DCDC).

For future reference:

[Michelle_LM74800_Notes.pdf](https://ubcsolar26.monday.com/protected_static/25620279/resources/2541955973/Michelle_LM74800_Notes.pdf)

The LTC4421 is the most feature rich IC of all I checked. It has the ability to disable source in over current conditions (with a 2.5 mohm shunt), it has 2 inputs (ideal for us), valid pins (like LTC4417, that tell us if a source's voltage is in the nominal range).

The big difference with the LTC4421 is that it has pins that tell us which input is currently driving the output (supp or DCDC), these are called CH1 and CH2.

Krish and I spoke and decided that we want a way of knowing which source (Supp or DCDC) is driving the output. If the DCDC isn't driving the output in normal operation, we have a problem and are draining supp when we don't want to be.

Possible solutions:

- Read back-to-back P-channel gate voltage

- Put a current sensor on DCDC and Supp (read by STM32)

- Read valid pins (if source voltage is in specified optimal range), and assume the IC switches

- (For LTC4421) read CH1 (channel 1 active) pin

Reading gate voltage is slightly difficult because for N-channel MOSFETs a charge pump is used to boost gate voltage above source voltage (eg. 12 V -> 17 V). So, we need to also read source voltage to know the delta.

Using another current sensor adds another component, so is suboptimal.

Reading valid pins places complete trust into the power path prioritizer IC, assuming that if a higher-priority source is valid that it'll switch to it. So, this doesn't fully check what's going on (eg. maybe the FETs are broken).

The LTC4421 makes this check extremely easy, we just read a GPIO and know which source is active.

Given all considerations, I have two options:

:

It has all features we need except knowing which source is active, so we'll need to add current sensors in series with each source to know which is active as a redundacy.

:

It foregoes the need for an additional current sensor, but is 32 pins instead of 24 and costs $2 more.

Both have similar stock on Digikey (200-1000, depending on model).

This investigation has shown that using a faster acting swap relay is a far easier solution than a power path prioritizer. I'll look for one of these and if I can't find one I'll use the LTC4421 (for the benefit of knowing which source is active).

> **Christopher Kalitin** (Nov 2025)
>
> ![](images/image_2542294688.png)
> 
> [https://www.digikey.ca/en/products/filter/power-relays-over-2-amps/188?s=N4IgjCBcoGwJxVAYygMwIYBsDOB...](https://www.digikey.ca/en/products/filter/power-relays-over-2-amps/188?s=N4IgjCBcoGwJxVAYygMwIYBsDOBTANCAPZQDaIALGGABxwDsIAuoQA4AuUIAyuwE4BLAHYBzEAF9CMegFZEIFJAw4CxMiADMNAAwaATNuZtOkHv2FjJ4KoegK0WPIRKRyMAAQBBEIXpefIPQAdDL%2BhDRh4NqRYHoxeiExFDGh3oRgHmngflkG-iwgHFwAqkIC7ADyqACyuOjYAK58uBJWeurNmOgAnsziQA)
> 
> No relays exist on Digikey that have an operating time less than the existing swap relay on ECU (EX1-2U1S), and that one is out of stock. Seems Mischa / Nic Ricci already chose the best available relay, there's no room for improvement in this domain.
> 
> Our original goal was to lower the size of the capacitor used while the armature swings by lowering the operating time of the relay, we can't do this with a relay so I'll implement the LTC4421.

---


---

## Finding A Current Sensor

**Author:** Christopher Kalitin

**Date:** Nov 2025

![](images/image_2575980443.png)

**Finding A Current Sensor**

Requirements for LV current sensor:
- 3.3V input
- Can handle >=10 A (to have margin above our expected 3-6 A current draw)
- Voltage output proportional to current (eg. Vout = 100 [mV/A] * current [A])
- Optimize sensitivity (mV/A) for precise readings.

I chose the [TMCS1108A3U](https://www.digikey.ca/en/products/detail/texas-instruments/TMCS1108A3UQDR/13692795), which has these specs:
- 3 to 5.5 V input
- -1.4A to 13.85 A current range
- 200 mV/A sensitivity

Note that with the 200 mV/A sensitivity and an STM32 with voltage sensing precision of 0.8 mV, we get a current sensing precision of 4 mA.

![](images/image_2582096642.png)

The datasheet chart above shows the current sensor IC has a zero current output voltage (ie. reference voltage) of 0.1 * V_supply. This means that at 0 A through the sensor, the output will be 0.1 * 3.3 V = 0.33 V.

We only expect positive current over this current sensor, so we aren't using the usual 0.5x reference voltage (1.65 V). We can bias the sensing range to be inclusive of more positive current, ie. using a 0.1x reference voltage.

Because our sensing range is 0.33 to 3.3 V, we can chose a pretty high sensitivity. We chosen IC has a sensitivity of 200 mV/A. For our ~3 V range this means out max observable current value is 3 [V] / 0.2 [V/A] = 15 A.

**A Note On More Precise Sensing**

Note that the IC generates the zero-current output voltage using a voltage divider internally:
"The TMCS1108 zero-current output voltage is derived from VS using a resistor divider"

This means that the zero-current output voltage is referenced to the supply voltage. Our STM32's ADC is also referenced to its supply voltage (3.3 V, VDDA). This means that our zero-current output voltage can be specified in ADC bits instead of volts.

Ie. use 4095 * 0.1 = 409.5 adc bits as the reference.

In the other case, we'd have to be assuming a zero-current output voltage as a constant in code. Ie. 0.33 V hardcoded. This means that if the supply voltage drifts (eg. to 3.28 V as we've often seen), our 0.33 V hardcoded value would be incorrect (we'd have to make it 0.33 * 3.28/3.3), but using raw ADC bits we're already accounting for supply voltage drift as both the source and sensor are referenced to the same supply voltage.

With this setup, we've eliminated the constant error of having an incorrect reference voltage, but still have gain error:

See gain vs. offset error here:

![](images/image_2576221661.png)

**Is The ADC Range Fine?**

For the [main pack current sensor characterization last year](https://ubcsolar26.monday.com/boards/7524367629/pulses/7524367868/posts/3786316479), I characterized the ECU's STM32s ADC and got this expected vs. experienced value graph (subtract both and you get error):

![](images/image_2575932166.png)

We see that after our 0.3 V reference starting point, we're mostly linear. However, above ~2.5 V our error is non-linear and gets bigger.

We can predict if our sensor will get up to 2.5 V using our expected current and voltage sensitivity to current.

With a max current of 6 A (this value is greater than what we now expect) and a sensitivity of 200 mV/A and a reference of 0.3 V, we get:
Vout(6 A) = 0.3 V + 6 A * 0.2 V/A = 1.5 V

We're not getting to the inaccurate range of the ADC (only up to 1.5 V) so we're fine.

> **Krish D** (Nov 2025)
>
> Hey @Christopher Kalitin,
> 
> One question, where did the 4095 * 0.1 expression come from?
> 
> Also I found[this](https://www.melexis.com/en/product/mlx91231/smart-ivt-shunt-interface-current-sensor)current sensor from Melexis (same brand as the old LV current sensor from the ECU). It has a gain error of 0.2% and communicates over UART. Perhaps worth considering if you think greater accuracy is required.

> **Christopher Kalitin** (Nov 2025)
>
> The 0.1x reference voltage comes from the datasheet, this makes it more optimized for sensing positive currents than negative currents (which is what we want).
> 
> ![](images/image_2582097790.png)
> 
> Greater accuracy than 4 mA isn't required here. That IC is also for a small shunt resistor, would be cool but added complexity isn't worth it (esp. with UART vs. just an ADC).

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** 11h

**Simulating Optocoupler Discharge Pulse Extension Circuitry**

Similar to the [previous Optocoupler update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080991742/posts/4906276781) this morning.

LTSpice sims are [on the drive](https://drive.google.com/drive/folders/1xq5AAaea6qMs2BM9x8qGFx1eYjlmUg9Y?usp=drive_link).

Conclusion:
- Use a 1uF instead of a 10uF for RC circuit (and change 10k to 100k to keep time constant the same)
- Use ~500 ohms on optocoupler input
- This makes the charging time constant 100x lower than the discharge time constant, for optimal pulse extension

**The Concern**

![](images/image_2743922576.png)

As explained in [the previous update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080991742/posts/4906276781), I was concerned about the NPN BJT in the optocouplers being limiting the current in some circuits.

In the case of the RC pulse extender circuit, this could mean not charging the capacitor fast enough, meaning the charging pulse is artificially shortened. In a worst case, this means not latching the discharge relay.

I decided to simulate the circuit in LTSpice to confirm functionality.

**Simulation 1**

![](images/image_2743916863.png)

Parameters:
- Input Pulse: 3 ms
- RC Capacitor: 10 uF
- Input Resistor: 1k

This simulation is a worst-cast scenario for the RC pulse extender circuit with a 3 ms charging time.

We see that with the existing components, the voltage output spends ~50 ms above 1.8 V (Vgs(th) of the NFET), so we successful latch the discharge relay (15 ms required).

This means my concerns over the NPN limiting the charging current to the capacitor weren't too important.

Assuming the Optocoupler has a CTR of ~100%, 12 V and 1k on the input translates to a max current of 12 mA on the output.

Since there's also 12 V and a 1k on the output, this system is well balanced, and the NPN and 1k output resistor both limit current to a similar degree.

However, issues come up with CTR < 100% or if the pulse is even shorter.

**Simulation 2**

![](images/image_2743917832.png)

Parameters:
- Input Pulse: 100 ms
- RC Capacitor: 10 uF
- Input Resistor: 1k

This simulation shows a best case scenario. The output voltage is >1.8 V for ~250 ms for an input charging pulse of 100 ms.

Note that my cursor was at the 1.8 V crossing for all screenshots, and you can see coordinates in the bottom left.

**Simulation 3**

![](images/image_2743922406.png)

Parameters:
- Input Pulse: 4 ms
- RC Capacitor: 10 uF
- Input Resistor: 2k

My next idea was to test if CTR < 100%. I did this by putting a 2k resistor on the input and keeping the 1k resistor on the output of the optocoupler. Now, the NPN will deliver 12V/2k = 6 mA, while the resistor is trying to pull 12V/1k = 12 mA.

We see that the current is limited to a little over 6 mA, as expected.

This results in a minimum pulse length of 4 ms required to latch the relay, which is just on the edge of our requirement of 5ms latching the relay (as discussed in previous updates).

**Simulation 4**

![](images/image_2743924667.png)

Parameters:
- Input Pulse: 100 ms
- RC Capacitor: 1 uF
- Input Resistor: 0.5k
- Low-side RC circuit resistor: 100k

I decided to lower the capacitor to 1 uF so that it would be charged faster. Also, to ensure optimal CTR, I lowered the input resistor to 500 ohms.

I kept the high-side resistor the same, so the charging time constant is now 10x lower. I made the low-side resistor of the RC circuit 100k instead of 10k, so its time constant is equal.

This results in a much faster charging time. Notice the almost instant charging pulse on the left of the graph.

**Simulation 5**

![](images/image_2743933942.png)

Parameters:
- Input Pulse: 1 ms
- RC Capacitor: 1 uF
- Input Resistor: 0.5k
- Low-side RC circuit resistor: 100k

Next I tested the 1 uF RC circuit in a worst case scenario of a 1 ms charging pulse.

Notice that even with the 1 ms charging pulse the pulse is extended to ~130 ms!

> **Aarjav Jain** (3h)
>
> @Christopher Kalitin : Suppose the current components you have chosen do not meet the 5ms charging time requirement. Then can you confirm that you would only need to swap out resistors and caps to find a combination that achieves the 5ms requirement? Or would we be in a situation where the board needs to be reprinted because the circuitry may completely not work (new IC needed)?
> 
> Same logic goes for **all other uses of the Optocoupler.**

> **Christopher Kalitin** (1h)
>
> Yes, it’s all just dependent on component value choice.
> 
> There are 3 things to control for:
> 
> 1. LED input current (input resistor)
> 
> 2. Charging time constant (output high side resistor and capacitor)
> 
> 3. Discharge time constant (output low side resistor and capacitor)
> 
> Unless something is fundamentally wrong with the circuit (unlikely given the LTSpice sim worked), we’ll be able to adjust components in case the current combination doesn’t work.
> 
> My concern after talking to Saman was that a low side resistor is a topology that won’t work and can’t be fixed by changing the resistor value, and the sim in the previous update confirmed this isn’t the case. The topology is fine, just resistor values have to be chosen carefully.
> 
> Previous update:
> 
> https://ubcsolar26.monday.com/boards/9702086049/pulses/18080991742/posts/4906276781

---

## Untitled

**Author:** Christopher Kalitin

**Date:** 20d

As discussed in [this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/11002723643/posts/4850567143), the Discharge Toggle circuitry has to be redesigned to work with a GND input instead of 12 V input.

I also came to the conclusion that because the discharge toggle line is going all the way to the driver (on the other side of the car from the battery), we should use an Optocoupler on it. The reasoning for this is described in [section 5.2 of ECU Rev 2.0 Design Documentation](https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0#heading=h.aqtqd6p6ctx5).

![](images/image_2697513209.png)

This design uses an optocoupler with a togglable ground with an RC circuit to extend the pulse time of DCH_TOGGLE_ON.

The optocoupler isolates DCH_TOGGLE_ON from the rest of the circuitry.

The RC circuit is charged with a 1k resistor and discharged with a 10k resistor. To a first approximation, this extends the pulse of DCH_TOGGLE_ON by 10x.

As shown at the [end of this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/10044512386/posts/4497053922), we could see a pulse as low at 5 ms on DCH_TOGGLE_ON if the driver slams the switch really fast. The Discharge relay requires a 15 ms pulse to latch, 5 < 15 so we need to extend the DCH_TOGGLE_ON pulse.

![](images/image_2697520524.png)

Using the equations we learned in PHYS 158, we can model the charging and discharging of our RC circuit to figure out how long we extend the pulse.

I modelled this in [Desmos](https://www.desmos.com/calculator/w9izcrqo83).

![](images/image_2697522987.png)

The above graph shows the voltage at the gate of the MOSFET for a charging pulse of 10 ms.

Notice that for a 10 ms charging time, the RC circuit discharges to below 1.8 V after 150 ms. Note that 1.8 V is the Vgs(th) of our NFET.

Varying the values in Altium, I found that a charge pulse of 2 ms is required for ~15 ms above 1.8 V.

This means the minimum pulse time is 2 ms, which is less than the 5 ms minimum pulse time we saw during testing.

> **Hemat Wander** (19d)
>
> Just want to note that the Vgs(th) is a voltage at which the NFET would be conducting a very small amount of current (in the microamps) so we need to be "a lot" above that depending on what current the latching relay requires.
> 
> However, "a lot" in this case probably just means something like 2V, since the latching relay only requires milliamps. Given that we only need a 2ms pulse time, this is likely fine.
> 
> ![](images/image_2699849352.png)

---

## The Discharge Relay Problem On Brightside

**Author:** Christopher Kalitin

**Date:** Nov 2025

**The Discharge Relay Problem On Brightside**

[During testing on Brightside](https://ubcsolar26.monday.com/boards/9702086049/pulses/10044512386/posts/4497053922) we found that there's a case in which the startup switch will only pulse the discharge relay's SET coil for 5 ms.

The discharge relay is a latching relay, so requires at least a 15 ms current pulse to change state (once its state is set, it keeps it, see [section 9.2 of ECU rev 2.0 design documentation](https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0#heading=h.xx8u71po48cm)).

This is the primary edge case I considered in designing discharge relay control circuitry for HVC.

**Using An RC Circuit To Extend Latching Time**

<img src="images/image_2577274814.png" width="617" height="183">

For uninitiated members, knowledge of Phys 158 / 2nd year circuit analysis courses may be useful.

To extend the time the latching relay's SET coil (it enables motor discharge) has current flowing through it, I used an RC filter that is charged when the startup switch is in it's middle position (it's a 3pos switch and we use pos1 for off, pos3 for on, hence why we're in pos2 for such little time).

This RC filter has a time constant of 110 ms and is charged up to 12 V directly from the supplemental battery (ie. it'll be charged up even if the HVC is off, we're skipping the startup circuitry and wiring directly into the supplemental battery).

![](images/image_2577255085.png)

Plotting v(t) = 12*e^-(t/0.11s) in desmos we find that we cross Vgs(th)(max) for the MOSFET after 209 ms.

This means that for an arbitrarily short charging time (eg 1 ms), the discharge relay's SET coil will have current going through it for 209 ms.

**Latch Off Circuitry **

![](images/image_2577254483.png)

Since we don't need this circuitry for turning the discharge relay off (which is done by the STM32), we use a more standard NMOS controlled by a GPIO.

**LEDs + SOP**

Note that both the latch on and off control circuits have LEDs that show when they're active. This way, we'll see a ~100 ms flash whenever discharge is enabled or disabled.

This can be worked into the SOP when using the battery, because if you don't see the flash when the car turns off the motor controller is still charged at 134 V, and is dangerous to work on.

---


---

## or RDK-85SLR to your specifications.

**Author:** Christopher Kalitin

**Date:** Nov 2025

Aarjav has been emailing Power Integrations for a little over a month about using their [94% efficiency DCDC](https://pages.power.com/solar-race-car.html). Mischa told us about it after he saw on LinkedIn that Innoptus is using these.

Here's a pdf of the email chain:

[UBC Solar Mail - DCDC Converter Inquiry for Solar Race Car.pdf](https://ubcsolar26.monday.com/protected_static/25620279/resources/2564208179/UBC%20Solar%20Mail%20-%20DCDC%20Converter%20Inquiry%20for%20Solar%20Race%20Car.pdf)

Aarjav's been the one person working on this, so as a sanity check that it's worth talking to Power Integrations about their DCDC in the first place, I put our specifications into Digikey to see if any DCDCs better than Power Integration's showed up.

Specs:

V_in: 85-140

V_out: 12 V

I_max: >6.5 A

207 DCDCs with the above specs exist on Digikey, 60 of which are in stock. See the

.

The max efficiency found is 93%, worse than Power Integrations listed 94%.

Only 2 DCDCs that follow our specifications and have 93% efficiency are in stock on digikey.

There are the:

1.

- $112.80

2.

- $300.85 (in stock on Mouser, not Digikey)

For reference, the Power Integrations DCDC is a kit that costs $50 (

).

The Power Integrations DCDC requires a series of modifications for it to work at our specified current range. This includes replacing minor components like capacitors, but also rewinding the primary inductor. This is detailed in the email chain with Power Integrations, but not in enough detail or with enough certainty to know exactly what actions we must take.

So, I'll reach out to Power Integrations again in the future when our current requirements are more defined.

In the V4 Master BOM

that lists 12 V current consumption of all expected vehicle systems. The current max current is 5.5 A, but includes 3.4 A for 4 pack fans at full power. As BTM refines their requirements, this will likely decrease.

To get a good enough estimate of current consumption to email Power Integrations about their DCDC again, I need BTM to tell me the number of fans and their power draw in our next generation pack.

When will I have this info, it's critical path for the HVC.

In the meantime, I'll look into other DCDCs like the two mentioned above and how to integrate them mechanically (screws and wires) with the HVC.

---


---

## Masterboard Mounting

**Author:** Christopher Kalitin

**Date:** Dec 2025

**Masterboard Mounting**

We've decided to mount the Masterboard onto the HVC this simplifies the connection between the two of them and the next Masterboard will be very small so it won't take up much space on the HVC.

Connection option 1:
[M55-6001242R](https://www.digikey.ca/en/products/detail/harwin-inc/M55-6001242R/8537555)

<img src="images/image_2594014681.png" width="182" height="151">

Connector Option 2:
[Mini-Fit BMI](https://www.molex.com/en-us/products/part-detail/438790027)[438790027](https://www.molex.com/en-us/products/part-detail/438790027)

<img src="images/image_2594014834.png" width="180" height="163">

The Mini-Fit BMI is very similar to the current connector we use for the DCDC.

One issue with the Mini-Fit BMI is that it's soldered through-hole, and that means a significant portion of the masterboard will just be soldered pins. Depending on how small the Masterboard is (currently thinking ~2x6 cm) it could be the majority of the board.

This is mainly due to the wide pin pitch of 4mm. Giving a connector that's ~3-4 cm long in total.

So, for this reason, I'm going with the M55-600 connector. It is surface mount soldered, meaning PCB space on the top layer will not be a concern.

The pins are smaller, but given proper handling when putting the board in and out of its connector socket this is not an issue.

Also, I have confidence that a surface mount soldered connector will be strong. I watched [this video](https://youtu.be/faXiy0wyiH8?si=tKo3LPgQ4EjQly36&t=121) last night of a guy trying to kill a similar connector and it was fine.

**Updated HVC Junction Board Interface**

First, we need to figure out the HVC to Masterboard connections, and then which of these impact the HVC to Junction Board connection.
**
Masterboard Connections:**

- 3.3 V
- GND
- CAN H
- CAN L
- Fan PWM
- FLT
- HLIM
- LLIM
- SWD I/O
- SWD CLK
- UART TX
- UART RX

Of these, the ones that are routed to the junction board are CAN H, CAN L, SWD I/O, SWD CLK, UART TX, UART RX.

A quick note:
HLIM and LLIM have direct override control over the contactors. Ie. if HLIM or LLIM are not high, the contactors cannot be closed. This is implemented in hardware as well.

We already have CAN H, CAN L going from HVC to Junction Board because the HVC MCU's. We just have to add the SWD / UART lines.

The HVC to Junction Board Connector becomes:
1. 12 V
2. 12 V Supp (for supp fuse, making sure it's externally accessible)
3. GND
4. Can H
5. Can L
6. Dist GND (Destination: Distribution board)
7. MPPT GND (Destination: MPPTs)
8. Fault (general) (Destination:DRD)
9. Supp Fault (Destination: DRD)
10. ESTOP 12V In (Destination: ESTOP connectors)
11. Startup (Destination: Driver Startup Switch)
12. Discharge (Destination: Driver Startup Switch)
13. HVC SWD I/O
14. HVC SWD CLK
15. HVC UART TX
16. HVC UART RX
17. Masterboard SWD I/O
18. Masterboard SWD CLK
19. Masterboard UART TX
20. Masterboard UART RX

Exactly 20 pins!

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin Thank you for clarifying the exact connections. This makes the signal topology between masterboard, HVC and the rest of the system quite clear!
> 
> One piece of feedback I'd like you to include for next time is to @ the relevant stakeholders. Deciding on a connector for the masterboard is directly correlated to the work that @Michael Lin needs to do for the layout, and since the DR0 is still being made, it should be made more clear that you are **asking for input** in case your connector choice clashes with a requirement.

> **Aarjav Jain** (Dec 2025)
>
> @Christopher Kalitin: I haven't gone through this with a fine toothed comb yet. However some things that jumped out

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin After re-reading this, I realized some points of confusion.
> 
> It is not immediately clear which connections are going to other parts of the car from the junction board. Can you add a section detailing what are the tentative destinations for each signal?
> 
> CC: @Aarjav Jain

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> Added little notes about wire destinations.
> 
> @Aarjav Jain
> 
> - On JTAG vs. ST-Link:
> 
> - BMS doesn't have too much use for JTAG.
> - JTAG only provides 5 V, which we would need to add an extra Buck / DCDC for
> - If optimizing for a good connector, we can get a nice connector for SWD as well
> - The SW DIO, SW CLK, GND, 3V3 pins are now in the same order as they are on Nucleo's so we'll be able to use a straight 4-pin female jumper wire, minimizing risk of wiring falling out.
> 
> Overall, I don't see too much benefit to using JTAG. Not quite sure why PAS did this in the first place, how useful is hardware verification code anyway? Just so you don't spend 5 minutes manually checking for shorts with a multimeter?
> 
> ![](images/image_2625302462.png)
> 
> - Masterboard will have mounting screws + standoffs.
> 
> - Requirement set as "up to 60x60 mm" in Masterboard DR0.

> **Aarjav Jain** (Dec 2025)
>
> The alternative purpose of using JTAG is that we have devices which support JTAG through a standard connector as opposed to FF wires. Using FF has been a headache for EMD and BMS for the last 3 years. There is a 6pin and a 20 pin option for JTAG.

> **Christopher Kalitin** (Dec 2025)
>
> Is PAS adding a 5 V buck / LDO to all boards just for JTAG?
> 
> Embedded doesn’t need UART if they have JTAG right?

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin This is much more clear. Great job!
> 
> @Aarjav Jain
> 
> Some notes regarding the destination section.
> 
> 1. For the fault & supp fault lines/wires, I believe it makes sense for the line to be directly routed to DIST, and DRD can then access the net from DIST.
> 
> I believe this would be a good idea since these nets being driven high can ensure that all LV systems are turned off immediately by directly driving the FETs/FET low on the dist to toggle off all LV systems.
> 
> Additionally another LED can be driven or blinked on the dist to ensure that if the driver more visibility during debugging.
> 
> Do you have any thoughts here?

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> If were in a fault we shouldn’t turn off all LV systems, eg. TEL should always be telling us what’s going on.
> 
> So, I’m not sure there’s purpose in routing either fault to Dist except for PAS routing reasons.
> 
> Also, if supp fault is high all LV systems are off anyway, no power source for anything.
> 
> For a DRD Supp Fault LED, we could add one but this would increase Supp current draw while it's already extremely low so it might be wise not to include it.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin I meant this should be the case for the supp_lo_fault. If the supp reaches the an extremely low value, it makes sense that we should limit all current consumption as much as possible.
> 
> Depending on what is deemed as an effective form of communication to the team that the supp is low, we could continue to let LEDs draw the current (on DIST, HVC, & DRD) and/or have TEL get direct access to the supp_fault and send this as over radio.
> 
> Would love to hear your thoughts on the tradeoffs here.

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> The definition of SUPP_FAULT is that it occurs when the Power Path Prioritizer can't output anything from Supp because it's voltage is out of the nominal range.
> 
> In such a case, no LV system (eg. TEL) can be active.
> 
> So, our only form of communication of such a fault is the SUPP_FAULT LED on the DRD & HVC.
> 
> While we're debugging we'll be able to see the HVC LED, and if the car is on the track the driver will be able to see the LED on the DRD. So, I don't think it's too useful to have a DIST SUPP_FAULT LED.

---

## Naming Convention

**Author:** Christopher Kalitin

**Date:** Nov 2025

**Naming Convention**

Header: PCB-side connector

Receptacle: Wire-side connector

I've been confused by this in the past and I think the rest of solar has. Above is what the LLMs say is the industry standard naming convention.

Note that "Housing" is reserved for the part that contains the crimps.

Examples:

Header:

<img src="images/image_2586411182.png" width="100" height="86">

Receptacle (also a housing, since it houses the crimps):

<img src="images/image_2586411593.png" width="104" height="95">

**Connector Requirements**

First, how many pins are required for each connectors:
- 2 pins: DCDC, Supp, Current Sensor, MPPT Precharge, Motor Precharge
- 6 pins: Both contactor / relay control harnesses
- 8 pins: Masterboard
- 12 pins: Fans
- 16 pins: Junction Board Harness

Simple things
- Must have reasonable per-pin current ratings (6 A is the max we need)
- Connector must be robust (eg. not too tiny with tiny pins)
- Must have reasonable stock on Digikey

Idiot proofing connectors so they can't be plugged in incorrectly is also a requirement. Having connectors with different pin counts is the easiest way to do it, obviously you won't plug a 12 pin connector into an 8 pin header.

Otherwise, connectors with the same number of pins near each other on the PCB need to have different models (eg. DCDC and Supp connectors should not be able to be plugged into each other).

One thing I'd like is that each connector header (PCB-side) has exposed pins. This way, while testing we'll be able to probe the pins.

![](images/image_2586413218.png)

Standard ATX Power Supply connectors are a great example of this. All of those pins you could probe with a multimeter, without accidentally slipping the probe onto another pin and shorting something.

**12-pin Connectors**

I've spent some time on Digikey and put together a list of suitable 12 pin connectors. I assume most of these are also available in 6, 8, 16 pin variants, this is just a general exploration of connector space.

[Molex 0901 12POS 2.54mm](https://www.digikey.ca/en/products/detail/molex/0901301112/760948)

<img src="images/image_2586409702.png" width="231" height="169">

[Molex 0559 2mm](https://www.digikey.ca/en/products/detail/molex/0559171210/3263360)

![](images/image_2586415053.png)

[Molex 1053 12POS 2.5MM](http://www.digikey.ca/en/products/detail/molex/1053102312/6164168)

![](images/image_2586416915.png)

[Samtec IPL1-106 2.54mm](https://www.digikey.ca/en/products/detail/samtec-inc/IPL1-106-01-L-D-K/4365397)

![](images/image_2586418109.png)

[Molex Mini-fit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)

![](images/image_2586456252.png)

**2-pin Connectors**
[Molex Mini-fit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)

<img src="images/image_2586455883.png" width="100" height="150">

<img src="images/image_2586454699.png" width="164" height="128">

[TE Connectivity 2 pin MATE-N-LOK](https://www.digikey.ca/en/products/detail/te-connectivity-amp-connectors/350986-4/293047) 2 pos 0.25" pin spacing

![](images/image_2586459528.png)

[Molex 00108](https://www.digikey.ca/en/products/detail/molex/0010844022/134541) 2 pos 0.25" pin spacing
(I believe this is the same as the one above, just with a worse datasheet and different manufacturer)

<img src="images/image_2586455376.png" width="129" height="135">

[Wurth Elektronik 66200211122](https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/66200211122/4322246)

![](images/image_2586479419.png)

[Wurth Elektronik 66100211622](https://www.digikey.ca/en/products/detail/w%C3%BCrth-elektronik/66100211622/10239710)

![](images/image_2586479597.png)

**Decision**

Everything will be Molex Minifit Sigma with the required number of pins, except where idiot proofing through disparate connectors is required and for the 16 pin Junction Board connection because no 16 pin Molex Minifit Sigma exists. Also, the 12 pin fan connector will use the Samtec IPL1 because it's slightly smaller and what the ECU currently uses (slightly bad reason, maybe I'll reconsider).

The 16 pin, 12 pin and one of the 6 pin contactor connectors (for idiot proofing) will use the [Samtec IPL1](https://www.samtec.com/products/ipl1) connector.

There are 2 pairs of 2 pin connectors, and a single Shunt resistor 2 pin connector. Each pair of connectors will be next to each other, so they must be different connectors.

2 pin connector pairs: (supp, dcdc), (MPPT PC, Motor PC).

One of the 2 pin connectors in each pair  will be the [Molex 001108](https://www.digikey.ca/en/products/detail/molex/0010844022/134541).

All other 2 pin, 6 pin, 8 pin will be [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002).

To sum up:

1. Junction Board - 16 pin [Samtec IPL1](https://www.samtec.com/products/ipl1)
2. Contactors A - 6 pin [Samtec IPL1](https://www.samtec.com/products/ipl1)
3. Contactors B - 6 pin [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)
4. Current Sensor - 2 pin [Wurth Elektronik](https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/66100211622/10239710)[66200211122](https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/66200211122/4322246)
5. Fans - 12 pin [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)
6. Masterboard - 8 pin [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)
7. Supp - 2 pin [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)
8. DCDC - 2 pin [Molex 001108](https://www.digikey.ca/en/products/detail/molex/0010844022/134541)
9. Motor Precharge - 2 pin [Molex Minifit Sigma](https://www.molex.com/en-us/products/part-detail/1727081002)
10. MPPT Precharge - 2 pin [Molex 001108](https://www.digikey.ca/en/products/detail/molex/0010844022/134541)

Connector Counts:
2 pin Molex Minifit Sigma: 2x
2 pin Molex 001108: 2x
2 pin Wurth Elektronik 66100211622: 1x
6 pin Molex Minifit Sigma: 1x
6 pin Samtec IPL1: 1x
8 pin Molex Minifit Sigma: 1x
12 pin Samtec IPL1: 1x
16 pin Samtec IPL1: 1x

4 connector models with 8 Connector parts (including different pin counts) for 10 total connections, with idiot proofing.

Furthermore, because the Supp/DCDC and Motor PC/MPPT PC pairs of 2pos connectors are on opposite sides of the board, it's possible to idiot proof it by not having long enough wires to reach to the other side of the PCB.

I might change my decisions for Samtec IPL1 vs Minifit Sigma on a few of them. The Samtec IPL1 is lightly smaller than Minifit sigma's (by 1.5mm per horizontal pin, which isn't total pins since they have 2 stacked vertically).

Some points might not be clear, for final HVC documentation I'll probably make a nice diagram when it's all nice and brought up with good images of the PCB actually routed.

I'll just vibe the decision, just touch all connectors in battery and rick rubin the decision. All vibes.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin Below are some points of feedback mixed with technical comments.
> 
> - Can you go into more details how you assigned certain components as 2 pin? Specifically, a justification for why they've been grouped that way would be ideal. It seems that you are referencing previous design choices like how the contactor and pre-charge PCB will have a total of 3 contactors/relays on it, and therefore needs 6 pins (3 x 12V + 3 x GND), therefore referencing that with a picture would make your assignment more clear.
> 
> - Noting how the signals are grouped is something that needs to be documented more clearly since requirements for the junction interface board may change (consider your point from earlier this week to add a supp_lo connection to for the DRD). Additionally, the signals from the master board need to be grouped accordingly in a header that mirrors your choice (since we are focusing on standardizing connectors) and directly influences design for @Michael Lin.
> 
> - "Idiot proofing through disparate connectors.." Just noting this as a typo
> 
> - What is the difference between contactors A and B? (Which one is NEG + DCH board vs POS + LLIM + HLIM + MPPT PC + Motor PC)
> 
> - For idiot proofing why not just make supp and motor PC different? It can be possible to constrain the wire design, but why not just purchase another 2 pos connector?
> 
> - Great job adding connector pictures, embedded links and clarifying the terminology. Good way to start the update!

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> - I'll write another update on rationalizing all choices made in this design, maybe you could tell it was really trailing off towards the end.
> 
> - I'll finalize documentation of all connectors in HVC design documentation, probably over winter break.
> 
> - Disparate is one of my favourite words!
> 
> - I don't know exactly what @Samuel Shin is naming both conntactor boards (I assume primary contactor board (PCB) is comedy Aarjav won't let us keep), so A and B is a placeholder.
> 
> - The idiot proofing can be done by limiting the lengths of the wires going to Supp/DCDC and Motor/MPPT Precharge. This simplifies the BOM, and avoids the need for using potentially suboptimal connectors, I trust the ones chosen to be robust and don't want a repeat of the slaveboard-cellboard harnesses last year.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin Sounds good.
> 
> - I shoudl've google searched disparate first LOL
> 
> - This way of idiot proofing makes sense. Please make sure to note this as integration point that **must be considered during the making of the wire harness**. I'd encourage you to also consider wire routing when the decision is finalized on the placement of the HVC on the control board.

---

## Defining Connectors

**Author:** Christopher Kalitin

**Date:** Nov 2025

**Defining Connectors**

Connectors:
1. Junction Board (16 pin 20 pin)
2. 3x Contactors + 2x Relay (POS, LLIM, HLIM, MPPT PC, Motor PC) (6 pin)
3. 1x Contactor + 1x Relay (NEG, Motor Discharge) (6 pin)
4. Current Sensor (2 pin)
5. Fans (12 pin)
6. Masterboard (8 pin)
7. Supp (2 pin)
8. DCDC (2 pin)

9. Motor Precharge (2 pin)
10. MPPT Precharge (2 pin

Note that the current plan of the contactors is to use Sensata contactors mounted directly to a PCB, this means we have have a single connector going to several contactors. Ie. instead of a 2 pin connector going to each connector we can have a 6 pin connector going to 3 contactors. This applies for relays as well (current plan is for POS, LLIM, HLIM, MPPT PC relay, and Motor PC to be on the same PCB, the primary contactor board (PCB)).

@Samuel Shin This is contingent on using through-hole PCB mounted contactors. If we have the existing control-board mounted contactors, it'll require many more wires. Hopefully Sensata responds soon.

**Wires In Each Connector**

Junction Board:
1. 12 V
2. 12 V Supp
3. GND
4. Can H
5. Can L
6. Dist GND
7. MPPT GND
8. Fault (general)
9. Supp Fault
10. ESTOP 12V In
11. Startup
12. Discharge
13. HVC SWD I/O
14. HVC SWD CLK
15. HVC UART TX
16. HVC UART RX
17. Masterboard SWD I/O
18. Masterboard SWD CLK
19. Masterboard UART TX
20. Masterboard UART RX
Taken from [Battery Interface Options doc](https://docs.google.com/document/d/1ZnLr69jU1ryMSLJ9eH1n_fhDsYKWzfe6zAO6alSrFdw/edit?tab=t.0#heading=h.xz2d9nic3yqc).
Edit: added 12 V supp so we can eliminate Supp connector.
Edit: Added Masterboard connections

Contactors 3x + Relay 2x (POS, HLIM, LLIM, MPPT PC, Motor PC):
- 12V
- POS_GND
- HLIM_GND
- LLIM_GND
- MPPT_PC_GND
- MOTOR_PC_GND

Contactor 1x + Relay 1x (NEG, Motor Discharge):
- NEG GND
- NEG POS
- Toggle Off GND
- Toggle On GND
- Supp 12V

Current Sensor:
- Shunt Pos
- Shunt Neg

Fans:
- Fan Power 4x
- GND 4x
- PWM 4x

Masterboard:
- 3.3 V
- GND
- CAN H
- CAN L
- Fan PWM
- FLT
- HLIM
- LLIM

Supp:
- Pos
- GND
This connection is coming from Junction Board in normal operation. During testing, directly from Supp. So, it has to be the same housing on junction board and HVC.
Edit: Integrated Supp_12V into Junction Board 16 pos connector, so this one is now redundant, but might be useful while debugging so I'm keeping it.

DCDC:
- GND
- 12 V

Motor Precharge:
- Motor Positive
Only one pin required.

MPPT Precharge:
- MPPT Positive
Only one pin required.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin For the junction interface board I have some questions that I'd like you to make more clear since signal choice will affect connectors on both the HVC and the masterboard.
> 
> **Junction interface board:**
> 
> -Why does dist have it's own GND? What edge case is this accounting for?
> 
> - Shouldn't there be a MB SCLK, SWD, UART TX and UART RX?
> 
> - From the battery interface doc, multiple other signals are mentioned, however don't seem continuous with your choices described in this update regarding signal grouping.
> 
> - Where is the dist_set net? Can you point me towards the Monday update that describes if this header to allowing enabling the dch circuitry with the 3 pin header is neccesary for our application?
> 
> ![](images/image_2590767314.png)
> 
> **Masterboard:**
> - I know you had asked in our slack channel about having the HVC handle fan PWM after taking in temperature data from the masterboard. You mention in your update that there should be fan_pwm connection from the masterboard. Does this mean you no longer see a benefit to the HVC handling this operation?
> 
> **Contactors:**
> 
> - Shouldn't there also be 5 signal traces for lowside actuating the contactors? It isn't clear to me where the contactor control interfaces here since you labelled it as "POS" and "GND". I'm assuming you meant to write 12V shared, POS_-, LLIM_-, HLIM_-, MPPT_PC_-, and Motor_PC_- ("-" indicates low side switched line).

> **Christopher Kalitin** (Dec 2025)
>
> @Krish D
> 
> **Junction board:**
> 
> - Distribution board has it's own ground because it's part of the startup sequence to turn it on. This is the same methodology as having every LV board togglable by the ECU in Brightside. This also delays starting boards until after swap to DCDC.
> 
> - I listed only connections going from the HVC to the junction board. So, masterboard connections and external connections (to the rest of the car) were left out. I did this before we considered mounted the master board on the HVC, changes will have to be made if we do this.
> 
> - Dist_Set would only be on HVC, not going to the junction board, because it's just a jumper.
> 
> Also, I didn't include dist_set in the discharge relay circuitry because I cannot think of a case when we don't want the discharge circuitry to be active. The MCU will always disable it during the startup sequence anyway, even if it was never turned on.
> 
> **Masterboard:
> **
> - I came to the conclusion that safety-critical communication between BMS boards shouldn't be done over CAN. Eg. the masterboard may be seeing 80 C and the HVC won't turn on fans if CAN is down. So, I decided to keep fan PWM on Masterboard.
> 
> I'll better document this decision and other Masterboard-ECU interface points in HVC design documentation.
> 
> **Contactors:
> **
> - Fixed the list to make it clearer, your understanding is correct.

> **Krish D** (Dec 2025)
>
> @Christopher Kalitin
> 
> 1. JB: I see, just a different name compared to the startup_gnd. Makes sense.
> 2. JB: Sounds good. I'll make a signal topology document so that elec system-wide signals and their function/use on each board is made more clear. (Will update in a slack message when I make it)
> 
> 3. JB: Hmm, I didn't consider that logic. Is there a time when we need to bypass it for testing purposes? Consider the example of if the trace from the MCU is experiencing an induced voltage due to bad relay/contactor placement, which drives the latching mechanism high. (I don't know if this is actual possible since an super aggressive power source would create this). Can you do a more deeper analysis to justify this and document it?
> 
> 1. MB: That makes sense. Do consider though that @Aarjav Jain has mentioned that we consider CAN being low to be a fault. Therefore, unless their is a discrepancy between the CAN PWM fan value, and the output from the masterboard's GPIO pin. The operation will be treated the same. (If a fault occurs, HVC or masterboard will drive fan PWM ~100%). I still agree that it makes sense at a design level to have the signals and their ""threshold management" being done by the masterboard and HVC is useful since it makes their roles more distinct, so let's keep it on the masterboard for now. <-  However take this as food for thought.
> 
> 1. Contactors: Look good. Let's aim to make the signal labels as clear as possible and **continuous** as possible between pages. Interpretation should be achievable with what is on the page. I'll keep an eye for this as you get closer to finalizing the schematic.
> 
> Great work so far Chris, keep up the stellar documentation!

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** 17d

**12V Issue With The Previous Design**

@Krish D Pointed out that the previous design is incorrect because DCH_TOGGLE_ON would be shorted to 12V during the middle state and bottom state of the switch. Meaning we would be always discharging the motor.

![](images/image_2697487567.png)

Note that if Motor discharge is always on, it's effectively a 50 ohm short between pos and neg of the battery. Schematic taken from [this wiki page](https://wiki.ubcsolar.com/en/subteams/battery/docs/ecu-control-board).

I decided to rework the Discharge Resistor Toggle circuitry so that its input is 0 V instead of 12 V from the startup switch. As described in [this Monday update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18134735438/posts/4850567476).

**Updated Design**

Now that the functionality is the same as the previous car (Default floating, then short DCH to GND, then short Startup to GND), we can use the same wiring as the previous car.

Here's the wiring taken from the [previous update](https://ubcsolar26.monday.com/boards/9702086049/pulses/10044512386?asset_id=2424280792).

![](images/image_2697496399.png)

<img src="images/image_2697498065.png" width="221" height="220">

---

## Untitled

**Author:** Christopher Kalitin

**Date:** 23d

This is a continuation of testing on V3 Brightside's startup switch.

[Monday Update](https://ubcsolar26.monday.com/boards/9702086049/pulses/10044512386/posts/4494653588) describing switch functionality

[Monday Update](https://ubcsolar26.monday.com/boards/9702086049/pulses/10044512386/posts/4497053922) describing switch rewiring & testing

![](images/image_2682682123.png)

Connection diagram

<img src="images/image_2682695723.png" width="254" height="253">

Overlayed connection diagram onto Brightside's Startup switch middle position.

More details are found in the updates above, here's a summary:
- The startup switch is a 3 position switch (3PST) (See connection diagram above)
- It toggles the STARTUP_GND_IN and DISCHARGE_12V_IN lines
- When STARTUP_GND_IN goes from floating to GND, the HVC starts up the car
- When DISCHARGE_12V_IN goes from floating to 12V, we begin discharging the motor controller

Switch Positions:
- Position 1 (Up) => Car off
- Position 2 (Middle) => Toggle Motor Controller Discharge On
- Position 3 (Bottom) => Car on

Trace truth table:

To implement this truth table with the 3 position switch, we'll follow this wiring:

![](images/image_2682761338.png)

Note that the "type" of the switch (Look at the connection diagram at the top of the update again) may be different for the switch we use.

In this case, the middle state is flipped on the vertical axis, so wiring must also be flipped on the vertical axis.

Before connecting wires to the connection, probe it with a multimeter in every state to check which "type" you have.

> **Krish D** (23d)
>
> @Christopher Kalitin  Just want to make this more clear:
> 
> - When the car is on (drawing 3), if Discharge_Toggle_On is connected to 12V, than it will FET controlling the discharge relay will be on. (Capacitor will be fully filled up, and gate voltage = 12V * 10/(10+1) = 10.9V (Vgss(max) = +/-20V and Vth(max) = 1.8, so the FET will definitely be conducting). Therefore as long as the car switch is in the ON position, the SET coil of the relay will be energized.
> 
> - This means that as soon as the car starts, the discharge resistor will be connected with the resistor, however if the MCU asserts the DCH_OFF_GND FET to conduct, than there will be a current return path for BOTH the RST and SET coils in the latching relay. This means that both coils (RST and SET are individual coils with opposing magnetic fields) will be on. The application notes for the relay also explicitly mention that: "You should avoid applying voltages to the SET and RESET coils at the same time. Parallel excitation of both coils can cause maloperation or failure to reliably latch/reset. It’s best to ensure only one coil is energized at a time with a proper pulse before energizing the next." (Got this from Chat GPT by the way)
> 
> TLDR: How can you make sure that the SET and RST coils are not on at the same time?
> 
> CC: @Hemat Wander

> **Krish D** (23d)
>
> [@Christopher Kalitin](https://ubcsolar26.monday.com/users/66779810-christopher-kalitin) A simpler solution You could also use a [SPDT latching relay IC](https://www.digikey.ca/en/products/detail/texas-instruments/SN74LVC1G3157DCKR/562895) (toggled by DCH_TOGGLE_ON) to connect the capacitor to 12V when the switch is moved from OFF-to-MIDDLE-to-ON, and then connected back to the RC circuit when the switch is moved from ON-to-MIDDLE-to-OFF. (refer to image below for where it can be placed)|
> 
> This way, you know that when the car is ON, the SET coil will not be energized, and when the car is turned off, you will still be able to energize the SET coil for long enough using the RC circuitry)
> 
> (Note that the SPDT IC I linked has an decent Rds_on... but we aren't expecting to draw current since it is used for pre-charging a 10uF capacitor)
> 
> CC: [@Hemat Wander](https://ubcsolar26.monday.com/users/66767094-hemat-wander)
> 
> ![](images/image_2683053407.png)
> 
> ![](images/image_2683051483.png)

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** 17d

![](images/image_2697608359.png)

To ensure we don't short Supp while probing its wires directly, we'll buy an inline fuse holder.

This uses the same blade fuses as everything else in the car, so it's interoperable with every other fuse in the car.

Digikey Link:
[https://www.digikey.ca/en/products/detail/mpd-memory-protection-devices/BF353S/8119229?s=N4IgTCBcDaI...](https://www.digikey.ca/en/products/detail/mpd-memory-protection-devices/BF353S/8119229?s=N4IgTCBcDaIEIDEDMBWJBlEBdAvkA)

How I shorted Supp:

![](images/image_2697609221.png)

> **Hemat Wander** (16d)
>
> @Christopher Kalitin
> One thing to note: there are [multiple sizes of fuses](https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-fuses/blade-fuses-shunt) including a larger maxi size and a smaller mini size. We use mostly (if not all) mini's around the car. You might want to check it fits the correct size if you haven't already.

> **Christopher Kalitin** (14d)
>
> @Hemat Wander
> 
> Good point, we need the BF353S, not the standard size BR353
> 
> Correct link:
> 
> [https://www.digikey.ca/en/products/detail/mpd-memory-protection-devices/BF353S/8119229?s=N4IgTCBcDaI...](https://www.digikey.ca/en/products/detail/mpd-memory-protection-devices/BF353S/8119229?s=N4IgTCBcDaIEIDEDMBWJBlEBdAvkA)

> **Krish D** (5d)
>
> @Christopher Kalitin Would you be able to add this to your HVC BOM so we can purchase this alongside the other components?

---


---

# Research

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

We replaced the current sensor IC on the distribution board with a spare of the exact same model.

Initial results:
V_out = 1.679 V
V_ref = 1.724 V
V_delta = -0.045 V

While the Control Board is off, the values float to this:
V_out = 1.170 V
V_ref = 1.184 V
V_delta = 0.014 V

The MLX91221 sensitivity value is 25 mV / A, so a -0.045 V delta means we're registering -1.8 A on the current sensor. This is a strange result, but if it's just a constant offset between the values we can subtract this out in firmware.

ADC readings:
V_out:   1655 mV (2054 adc bits)
V_ref:    1656 mV (2055 adc bits)
V_delta: 0.8 mV (1 adc bit)

I'm writing this update in real time as notes, so I've just found a terrible mistake that gave erroneous multimeter readings before. We were using the multimeter in continuity mode, and the continuity mode was registering a voltage.

Now, multimeter on voltage sensing mode (proper values we can trust):
V_out:   1.647 V
V_ref:     1.648 V
V_delta: 0.001

Now we have replaced the current sensor and confirmed it works while there's no current over it (since we're powered by supp currently).

![](images/image_2409009024.png)

[https://docs.google.com/spreadsheets/d/1cYhZnJEjcnmW1DRI8iqKIOBfocWLhtRU9QVwHDOSeDQ/edit?gid=0#gid=0](https://docs.google.com/spreadsheets/d/1cYhZnJEjcnmW1DRI8iqKIOBfocWLhtRU9QVwHDOSeDQ/edit?gid=0#gid=0)

A few months ago I characterized this current sensor on a breadboard (not on DCDC like it is now) and found that it has a roughly constant 40 mA error (positive error, so it's higher than expected). We can subtract this out in firmware.

Sensitivity = 25 mV / A
Current error = + 0.04 A

Voltage error = 0.025 V/A * 0.04 A = 0.001 V

The voltage reading error is a single millivolt, and one adc bit (Least significant bit) is the equivalent of 0.8 mV. To make it more accurate we need to subtract 1 in firmware.

I actually already did this in this [Monday Update](https://ubcsolar26.monday.com/boards/7524367629/views/162332252/pulses/8628510380) 6 months ago.

![](images/image_2409014888.png)

This is literally linked in the code.

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin What was the mistake "I'm writing this update in real time as notes, so I've just found a terrible mistake that gave erroneous multimeter readings before."? Was it that you were in continuity mode? If so then then why does the next statement say  "Now, multimeter on continuity mode:"?
> 
> When in the flow of the update did you actually replace the current sensor IC?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain
> 
> I've updated that section to remove the line break with the next paragraph to make it clear. Also added "Now, multimeter on voltage sensing mode (proper values we can trust):", there was a typo here earlier where I put "continuity mode" instead of "voltage sensing mode"
> 
> Replaced IC immediately, first line of the update.

> **Aarjav Jain** (Sep 2025)
>
> Thanks!
> 
> @Christopher Kalitin How were you probing the voltage?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain
> Used the orange multimeter we have in the bay.
> 
> The reason I wrote this Monday update in real time is that I think my preivous updates were far too verbose. In project notes for my own projects it's far fewer words, to the point, and continuously written. For a test like the one in the update above this is a far better way or writing an update imo. Slightly overcorrected by not proof reading.

> **Aarjav Jain** (Sep 2025)
>
> Yup thats ok. Just make sure that you during the test you take the time to write the update well while testing. It feels like a burden because you are in the middle of testing but its worth it! I write my updates like this as well.

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin
> 
> When I said how I meant what process and other tools were you using to ensure you do not short 2 pins?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain Forgot to include this in the update, will marginally increase effort next time.
> 
> I soldered a piece of wire to a pin on the DCDC which we wanted to probe. Alligator to the other end. Then, put electrical tape over it for good measure.
> 
> This was the sketchiest pin to probe. Most other times I just used made to female jumper wires or alligators.
> 
> ![](images/image_2411875054.png)

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin: To confirm which pin was probed?
> 
> ![](images/image_2414931210.png)
> 
> And can you confirm that the idea here is that the DCDC is off since there is no HV. Furthermore, can you confirm that supp was disconnected from the ECU and that **its terminals were taped up (the connector)?**
> 
> If thats the case then soldering on the wire is safe. Adding on the electrical tape after for good measure is required as well so great that you did that.

> **Christopher Kalitin** (Sep 2025)
>
> LVS CURR SENSE OFFSET is the one we soldered the little wire onto.
> 
> LVS CURR SENSE has a test pin, which we put an alligator on.
> 
> We had to probe both because the current reading of the sensor is a function of the difference between both voltages. Eg. By default it is 1.65 and 1.65 V. But if the reference voltage (called offset in our schematic) is 1.65 and output is 1.7, we get a 50 mV delta which corresponds with a 2 A current reading.
> 
> The supp was plugged in and ECU on for all tests. The sensor needs 3.3 V somehow, and this was sourced from the ECU (just like regular operation).
> 
> DCDC is disconnected from HV. Our goal was to get a nominal default output (~1.65 V on both pins).
> 
> Soldering directly to pads is just a debugging technique, but through hole soldering wires with connections very close to each other is a common industry technique, so I wasn’t too worried. (See image of Faraday Future e-bike BMS)
> 
> ![](images/image_2414976415.png)

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin Thanks! Great work with setting this up safely and with a concrete goal in mind!
> 
> One thing I am curious about is in the picture below
> 
> ![](images/image_2417183904.png)
> 
> it looks like the white wire is soldered to **12V_DCDC **beside the resistors in the Altium as opposed to LVS_CURRENT_OFFSET. The 2 x 6 row has nothing soldered onto it. Could you explain this? Also could you point out where the electrical tape is?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain
> 
> What looks like a resistor in the image is actually mounting for a DNP through hole resistor. We have two of these resistors forming a voltage divider which outputs to the SC pin on the DCDC.
> 
> Correction: it isn't actually a voltage divider, only one is populated at a time. Read further
> 
> The wire isn't actually connected to a resistor there (there is no resistor), it bends to the right and connects to the back of the DCDC connector to the LVS_CURR_SENSE_OFFSET pin.
> 
> I've labelled both below:
> 
> ![](images/image_2417412225.png)
> 
> ![](images/image_2417411505.png)
> 
> Now why do we have two DNP resistors?
> 
> Vicor datasheet:
> [https://usw.365.altium.com/librarycomponentsapi/api/v1/References/F239870F-ACB6-4292-8F7E-058931B098...](https://usw.365.altium.com/librarycomponentsapi/api/v1/References/F239870F-ACB6-4292-8F7E-058931B0987E)
> 
> ![](images/image_2417385032.png)
> 
> The datasheet and the note on the schematic tells us that we can use either the pull up or pull down resistors as trim resistors to get a different output voltage than 12 V.
> 
> Calculator to determine output voltage to trim resistor value: [http://asp.vicorpower.com/calculators/calculators.asp?calc=1](http://asp.vicorpower.com/calculators/calculators.asp?calc=1)
> 
> These DNP resistors exist in case we want to trim the output of the DCDC to a value slightly different from 12 V (ie. +/- 1 V). I doubt we would ever want to do this, but it's a good design principle to follow the exact implementation the datasheet tells us to.
> 
> The SC pin that can be connected by either (R1.1) or (R1.2), the value of these resistors determines output voltage.
> 
> Also, the DCDC itself has internal faults. The SC pin is pulled low by the DCDC if there is a fault. DCDC internal faults include input undervoltage, input overvoltage, overtemperature, etc.
> 
> When researching the next DCDC I'll look into this.
> 
> ![](images/image_2417418319.png)
> 
> @Krish D @Samuel Shin @Hemat Wander You all might find this interesting as well

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin: Very interesting! Looks like there is some FW logic going on here? In that case can we read this PC pin for a fault potentially. How exactly do we reset PC though if it latches?
> 
> Thanks for clarifying the setup and where the white wire is soldered onto.
> 
> How can we use this feature of a DCDC to our advantage for safety?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain
> 
> Fixed Datasheet Link: [https://www.mouser.com/datasheet/3/1228/1/ds_110vin-maxi-family.pdf](https://www.mouser.com/datasheet/3/1228/1/ds_110vin-maxi-family.pdf)
> 
> Checking the datasheet again, it looks like the faults are all analog and in hardware, the same way we do over current faulting on ECU rev 2.0.
> 
> PC pin can either be pulled low (<2.3 V) by us to disable the DCDC, or it can be observed to know whenever a fault occurs, but not what type of fault has occurred.
> 
> In the case that the DCDC faults and stops outputting voltage, we won't have any need to read the state of PC because we'll have already ran out of power.
> 
> An idea for the HVC is to automatically switch back to Supp if the DCDC ever fails. I'll brainstorm ideas for implementing this.
> 
> ![](images/image_2422934241.png)

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

We did 4 tests, with the LVS Current Sensor:
1. Record ADC Values of LVS_CURR_SENSE and LVS_CURR_SENSE_OFFSET
2. Take DCDC off and record same values (as a control)
3. Put DCDC back on and probe LVS_CURR_SENSE with a multimeter

4. Still with DCDC on, probe LVS_CURR_SENSE_OFFSET

![](images/image_2401233075.png)

*(Figure 1) Notice the while wire we soldered onto the DCDC to probe LVS_CURR_SENSE_OFFSET.*

The LVS_CURR_SENSE_OFFSET trace does not have a test pin and we did not want to probe it directly with a multimeter, because ~6 months ago this is how I shorted 3V3 and GND on the ECU, bricking it.

To record adc values / voltages we added prints in firmware and flashed the ECU.

Results of test 1 (DCDC on, ADC values):
LVS_CURR_SENSE: 8 mV
LVS_CURR_SENSE_OFFSET: 211 mV

The offset voltage should be ~1.8 V (by the [MLX91221 datasheet](https://usw.365.altium.com/librarycomponentsapi/api/v1/References/E27D921F-27F5-4C77-8757-A7F2D2546201)), and we see 211 mV in the case when the DCDC is connected to the ECU. Already, the current sensor is clearly fried.

Results of test 2 (No DCDC):
LVS_CURR_SENSE: 1793 mV
LVS_CURR_SENSE_OFFSET: 1647 mV

We already see that taking off the DCDC results in a very different voltage than with it on.

Note that without the DCDC on, the both pins should be floating (no pull up or down resistors). The only thing on the trace is a 100 nF capacitor.

The image below shows the raw real-time adc voltage readings we saw after turning on the ECU, and a clear ramp is visible (start at 635 mV, end at 992 mV). A few seconds later, the voltage settles to 1793 mV for LVS_CURR_SENSE, and 1647 for the offset.

We confirmed the voltage is actually ramping (not just an ADC issue) by probing it with a multimeter.

We don't expect any kind of voltage ramp on this trace because it should be float. The 100 nF capacitor for some reason is building up a ~1.8 V potential over itself. I'm not sure of the reason for this, but it at least serves as an exercise for why pull up/down resistors are useful.

![](images/image_2401247394.png)

Results of test 3 / 4 (DCDC On, Multimeter on both pins relative to GND):
LVS_CURR_SENSE: ~0 mV
LVS_CURR_SENSE_OFFSET: 170 mV

This test is the same as Test 1, but recording voltages with a multimeter instead of the ADCs. We see the same results, so it's not an issue with the ADCs. Absolute confirmation that the current sensor IC is fried.

Next Steps:

After this analysis, it seems clear that there is no fundamental issue with the implementation of the current sensor on the DCDC. We have used this current sensor on breakboards before so we can narrow down the issue to this specific IC being fried for some reason, and over a year ago (it also wasn't working at 2024 comp).

To regain LVS current sensing on ECU rev 2.0 we can replace the IC (we have extras last I checked ~1 month ago for control board current draw characterization).

It must be decided if this is data we want from the driving day around November. It's not particularly critical to anything except HVC DCDC sizing, for which we have other analogs (our existing assumptions around current draw).

> **Samuel Shin** (Sep 2025)
>
> What happened after TODO? Are we still thinking?

> **Christopher Kalitin** (Sep 2025)
>
> Sorry drunk give me a day didn’t finish in time before class

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin once you get a chance remember to add what TODOs there are.

> **Christopher Kalitin** (Sep 2025)
>
> Did this earlier and mentioned it in a slack comment.
> 
> Most important todo is determining if we want to put effort into replacing the current sensor before the driving day to get good data for HVC design, or if other HVC tasks should be prioritised.
> 
> I don’t expect replacing the current sensor to be particularly difficult, so we should spend an hour or two doing this to get concrete data for DCDC current capacity requirements.
> 
> CC:

> **Krish D** (Sep 2025)
>
> I agree. I realized we just need to take off the DCDC converter and swapping out the IC isn't terribly difficult at all. Worth the time for sure.
> 
> @Aarjav Jain

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin @Krish D @Samuel Shin I agree lets replace the IC. What is the model number of the IC? @Christopher Kalitin you said we have the same current sensor IC in the PVA box?

> **Christopher Kalitin** (Sep 2025)
>
> @Aarjav Jain
> 
> MLX91221
> [https://usw.365.altium.com/librarycomponentsapi/api/v1/References/E27D921F-27F5-4C77-8757-A7F2D25462...](https://usw.365.altium.com/librarycomponentsapi/api/v1/References/E27D921F-27F5-4C77-8757-A7F2D2546201)
> 
> I feel like I remember seeing it in either the PVA box or in another parts box we have. Will check tomorrow evening. If we don't have the exact model, another one with the same footprint can be used.
> 
> If we don't have anything that'll work, I have a ACS711ELCTR-25AB-T which has the same pinout except for the lack of a voltage reference output (internal constant 1.65 V).

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

Test plan:

LVS Current sensing stack:
1. Current sensor outputs two voltage, sense voltage and reference voltage
2. STM32 reads voltage and outputs adc bits (0 to 4095)
3. ADC value converted to voltage reading in firmware
4. Voltage converted to current reading in firmware using formula from the datasheet
5. Current data sent in CAN message to TEL board or PCAN
6. CAN message read by sunlink and outputted to Grafana

The failure mode we saw is that the LV current sensor was always outputting 25 A +/- 1 A. The current reading fluctuated a little bit with time but stayed around 25 A. We noticed this after comp when looking at InfluxDB data.

We don't have any insight as to where in the stack the error is occuring, so we will have to work our way down each step to find where we don't get expected values.

First, we will probe the LVS_CURR_SENSE and LVS_CURR_SENSE_OFFSET lines on the ECU and manually (in google sheets) convert the voltage difference between the two to a current reading value.

Current sensor datasheet: [MLX91221KDC-ABF-050-SP](https://usw.365.altium.com/librarycomponentsapi/api/v1/References/E27D921F-27F5-4C77-8757-A7F2D2546201)

The current sensor has a sensitivity of 25 mV / A.

First, we will need current to be drawn from the DCDC, which requires the control board to be in the pack. Previously we derived the [current vs time graph of the control board](https://ubcsolar26.monday.com/boards/9565350285/pulses/9721351653/posts/4389304604) so we know what current to expect.

Second, to test firmware, we need to print intermediate value at every applicable point in firmware. Eg. ADC value, voltage, and current.

Third, we can check if the UART printed value is the same as what is displayed on Grafana (through PCAN on the bay computer). If this is incorrect, we'll consult with Aarjav (resident Sunlink expert) to track down the issue further.

Previous theory on what is wrong, just for future reference:

My intuition is our firmware is the issue.

The LVS current sensor value on Influx from comp is ~25 amps +/- 1 amp, meaning it changed slightly over time.

With a sensitivity of 25 mV / A, this amounts to a 0.625 V error (if we expect 0 A).

Given that the current on influx changed over time, I think it's a firmware
issue and not hardware (from which I would expect a different failure
mode).

> **Aarjav Jain** (Sep 2025)
>
> Nice. @Christopher Kalitin once you get a chance update with the results!

---

## Untitled

**Author:** Samuel Shin - BTM Member

**Date:** Sep 2025

[Link to previous steps](https://ubcsolar26.monday.com/boards/7524367629/pulses/8628510380); for the new design, we want to implement LVS current sensor, and to make sure we understand how it works and why it wasn't working for Brightside BMS (Failure mode), we are continuing this project.

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

Aarjav and I did a quick 30 minute test to confirm end-to-end discharge relay operation. Our goal was to use a multimeter to probe between ECU GND and ECU Startup Set and only see continuity when we are in the middle state of the startup switch.

This is an end-to-end test using the startup switch, distribution board, and ECU. Before we only used the startup switch.

These were results we got when we were in the middle state of the startup switch (discharge state):

When we probing ECU GND to ECU Startup Set we saw no continuity, but the DMM in continuity mode reported a 1.5 V voltage drop (it automatically went into diode mode).

This result was not what we expected. We wanted continuity between ECU GND and ECU Startup Set when we are in the discharge state (middle state of startup switch). We instead saw no continuity.

Next, we probed ECU GND and ECU Startup Switch relative to the distribution boards GND. We wanted to see that the ECU to Distribution board was not the issue.

*This table shows the state of ECU traces relative to Dist GND (We are probing Dist GND with the black probe of the DMM, and the given ECU trace with the red probe of the DMM).

*From the table above, we see that if we measure relative to Dist GND the state of ECU Startup Switch equals ECU GND when we are in the discharge state (as expected), and is floating when we are in the off state (as expected).

This suggests the ECU GND and ECU Startup Switch are at the same state when we are in the discharge state, as expected. However, as mentioned before, we couldn't get continuity between these two points directly.

This effectively indirectly suggests discharge is working, however we couldn't prove this directly.

A possible next step is to test continuity over the discharge relay itself while the control board is on, getting closer to conditions while driving instead of a very focused test.

A final test we'll do is to check if the motor controller terminals hold 100 V when the car is off, which we'll do when the motor is fixed and back from Mitsuba.

> **Hemat Wander** (Oct 2025)
>
> I'm confused what the purpose of testing the continuity of ECU GND and ECU Startup Switch was. Why not just test the "continuity over the discharge relay itself while the control board is on" first, that seems like the simplest end to end test of if the relay is discharging correctly.
> 
> Also, what do the values in the chart mean? Resistances? Why is there a 6.5 k resistance only?

> **Christopher Kalitin** (Oct 2025)
>
> @Hemat Wander
> 
> Testing continuity over the discharge relay requires the control board being on. We only have ~25 minutes for the test so didn't do this.
> 
> We first used a DMM in *continuity mode* and it reported resistance. Then, with the DMM in resistance mode we got 6.5k ohms from between those two ECU nets and Distribution board GND. This is particularly strange, since we expect all grounds to be shorted to each other.
> 
> ![](images/image_2463792779.png)
> 
> I've looked at the Altium and it's actually not strange.
> 
> We only had the ECU CTRL SIGS connector on the distribution board plugged in, so Dist GND and ECU GND were not connected. The 6.5k ohm path must have been through one of these LV connections.
> 
> Supp Low and Fault Out are pulled to ground on each PCB through 13k ohms of equivalent resistance each. This gives a net equivalent resistance of 6.5k.
> 
> This perfectly explains the behaviour we were seeing.
> 
> The useful conclusion here is that we rushed into this test while not fulling understanding the system. For a 25 minute test, not a bad result.
> 
> Now that the strange result is accounted for, I can confidently come to the conclusion that the circuitry for closing the discharge relay is all functional. @Aarjav Jain
> 
> ECU:
> 
> <img src="images/image_2463793274.png" width="169" height="167">
> 
> Dist:
> 
> <img src="images/image_2463793195.png" width="178" height="121">
> 
> @Hemat Wander Also, you used a 1k for pulldown on Supp Low and Fault Out on the distribution board while the ECU uses 10k's. This means you form a voltage divider and instead of Supp Low's gate being 3.3 V * (10/11) it is 3.3 V * (1/2) <- basic voltage divider math.
> 
> If 1.65 V is not above Vgs(th), the FET wouldn't be well into the conducting regime and the LEDs would not work.
> 
> I made this same mistake on one of my PCBs and asked Mischa about it on Slack a while ago.

> **Hemat Wander** (Oct 2025)
>
> That's a good catch, considering the old distribution board rev also missed this. According to the datasheet, the max VGS(on) is 1.8V, so we just got lucky with the FETs we got being under that VGS(on). I think PCB checklist includes accounting for this.
> 
> ![](images/image_2463835578.png)
> 
> (That or we are running the FETS in resistance mode instead of saturation mode?).
> 
> Also, where did you get the 13k pull down to ground from. Isn't it 11k on the ECU and 2k on the distribution board?

> **Christopher Kalitin** (Oct 2025)
>
> I got 13k between ECU GND and Dist GND. With two of these Req=6.5k.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

Today we rewired the startup switch.

This is the configuration we used:

![](images/image_2424280792.png)

From the previous Monday Update I determined that the middle wiring of the switch was flipped on the vertical axis from what was expected. Ie. instead of top right being shorted, top left was shorted.

This meant that motor discharge did not connect to ground when expected.

While disassembling the connector today I realized that once you take apart the switch and housing portion, if you flip the switch 180 degrees, the middle switch configuration flips as well.

![](images/image_2424293720.png)

The diagram above illustrates the change that occurs, by flipping the switch portion 180 degrees, we change how the middle portion of the switch works and which contacts gets shorted to which.

![](images/image_2424294548.png)

This image shows the housing (left) and switch (right).

This is all to say that when disassembling the switch yesterday I may have put the switch portion (not housing) back in incorrectly (rotated 180 degrees), changing the behaviour of the switch. So, it may have been perfectly fine before and we actually did enter motor discharge (Assuming we were in the middle state for >15 ms, see previous updates).

Regardless, the switch is in a different configuration now so I rewired it (before realized my mistake when reassembling).

These two images show the configuration now

![](images/image_2424297167.png)

![](images/image_2424297374.png)

Once the wiring was completed, we could do the test to see how long we're in the middle state of the switch, and if this is >15 ms for motor discharge to occur.

As mentioned in the testing plan 2 Monday Updates ago (the first one in this thread), we hooked up a PSU to the ground terminal of the switch and probed the motor discharge terminal with a oscilloscope (scope negative to PSU GND).

We attempted to flip the switch very quickly, in a single motion. We found that in this case we are in the middle state of 4-6 ms.

Testing data and visualization scripts are available here:
[https://github.com/UBC-Solar/solar_tools/tree/user/CKalitin/startup-switch/projects/startup-switch](https://github.com/UBC-Solar/solar_tools/tree/user/CKalitin/startup-switch/projects/startup-switch)

![](images/image_2424299712.png)

![](images/image_2424300871.png)

When we did tests while slightly more carefully flipping the startup switch, we saw a 25-50 ms period in the middle state. When flipping the switch this way, we heard two audible clicks for each state change, instead of a single click sound (of the two combined state changes in the 5 ms total time).

So, for further Brightside testing we should get the drivers to carefully flick the startup switch, such that they hear two clicks and not one combined click. In this case the motor discharge relay will have current running through it's coils for long enough to enable motor discharge.

In the future, we either need an RC circuit solution so that the brief current spike can be extended (maybe controlled a FET). Or, we can use a normally closed switch for discharge, that we open whenever we want to drive. These solutions will be explored when designing HVC circuitry.

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin
> 
> 1. Is the first picture your class notes?
> 
> 2. The point about flipping the inside 180 degrees is very important. That is something that could cause serious damage to the motor or injure someone if they are working near a high voltage motor controller when the car is off (expected to be denergized). **What methods can we use to make sure the switch is put back together correctly? Is there a marking that tells us how to put the switch back together correctly? **In addition, lets formally document the internals of the switch by creating a Wiki page on its inside and how we use its wiring. Do this in the BMS wiki and use your explanations (the media and words are great!).
> 
> 3. Excellent attention to detail for documenting! Using solar-tools, and making a README.md with the monday update is extremely important. Great work and keep it up!
> 
> 4. Sounds good for exploring the circuitry for the HVC. Interested to see what you design!

> **Christopher Kalitin** (Sep 2025)
>
> 1.
> 
> Elec 204 was slightly boring so I took a few minutes to figure out the switch problem (this wasnt taught in the class).
> 
> 2.
> 
> Will write a wiki page on startup, great idea.
> 
> No markings on the switch to make this clear, on Brightside the only solution I see is being aware of it. For V4 we could do away with the 3 position switch and use a different circuit for discharge to eliminate this risk.

> **Krish D** (Sep 2025)
>
> @Christopher Kalitin Great job documenting this properly and getting the diagrams up. When you create that wiki page, feel free to also take the note off of the ECU schematic explaining how it works.
> 
> What do you think should be the next course of action? Is there any other tests to consider?

> **Aarjav Jain** (Sep 2025)
>
> @Krish D Why not keep the note on the schematic still? Or what note are you referring to?

> **Christopher Kalitin** (Sep 2025)
>
> @Krish D
> No next steps to do with this. Sam and I validated with a multimeter on the distribution board startup switch connector that startup switch and discharge enable lines in fact get grounded when we want them to.
> 
> All that's left is redesigning this for HVC, which comes later.
> 
> @Aarjav Jain @Krish D
> I don't think there is any note on the ECU schematic explaining how it works! Since I first heard about startup in term 1 last year it remained mostly a mystery and I'm not sure Mischa pointed us towards any good docs.
> 
> Now, all will be documented in detail in PCB design notes / documentation.

> **Krish D** (Sep 2025)
>
> @Christopher Kalitin @Aarjav Jain I thought it may be worth testing when we get back the motor controller if discharge still works or not. It may be stated that it takes 15ms of current flowing from GND for the DCH latch to connect/disconnect the dch resistor, however it's still worth checking if this occurs properly or not.
> 
> Please correct me as I'm unsure about your wording from the monday update, but did you and @Samuel Shin check if their was continuity across the HV side of the latch with the DCH resistor? (not just DCH_EN - which is showing how long the latch is in contact with the GND path from the startup switch)? If this was done, than the team can definitely proceed with caution going into further testing

> **Christopher Kalitin** (Sep 2025)
>
> No pack in car or control board in pack so we couldn’t test it end to end. We just probed the distribution board connector with a multimeter and got the expected result.
> 
> We should absolutely test if the motor actually discharges when it comes back. Extremely important task, possibly can be done with new recruits.
> 
> On whether or not it takes 15 ms, I mostly trust the data sheet here. When doing circuit design for the HVC we’ll use a very different circuit so I’m not sure this is the most useful test we can do during the next meetings.

> **Krish D** (Sep 2025)
>
> @Christopher Kalitin
> 
> Sounds good. Thanks for noting it's importance!
> 
> For now, can you check if the high voltage side of the latch becomes continuous when flick the startup switch fast vs when you slowly flick the switch to ensure it is in the middle pos for longer than 15ms?

> **Christopher Kalitin** (Sep 2025)
>
> @Krish D
> 
> We could do this on Saturday. It would require the distribution board and control board to be near enough to the car for the wires to reach, we can put it on the trolley.

> **Hemat Wander** (Oct 2025)
>
> @Christopher Kalitin Did you guys ever complete this test?

> **Christopher Kalitin** (Oct 2025)
>
> We did not. If anyone is free right now we could do it now in 30 mins.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

On Saturday I was not able to complete the startup switch test detailed below where I would have seen on an oscilloscope how long we stay in the middle state of the switch and toggle the motor discharge relay. This is because I discovered that the startup switch wiring is incorrect and by my assessment, we currently never discharge the motor because the motor discharge line never gets pulled to ground.

Switch Model Number:[2644A APEM2](https://www.digikey.ca/en/products/detail/apem-inc/2644LH-2A212000L0/10447877)

![](images/image_2422846108.png)

Initial wiring of the switch:

<img src="images/image_2422853219.png" width="329" height="359">

<img src="images/image_2422855777.png" width="321" height="366">

<img src="images/image_2422880242.png" width="249" height="332">

I used the distribution board startup switch connector and pinout to cross reference which wire went to what.

After documenting the initial switch setup, I got a multimeter and observed which contact are shorted in each switch position.

**OFF**

<img src="images/image_2422862545.png" width="302" height="301">

**MIDDLE**

<img src="images/image_2422863242.png" width="304" height="303">

**ON**

<img src="images/image_2422863833.png" width="306" height="305">

Note that the white wire in the image shorts the bottom right contact to the left middle contact.

We see that in the OFF state, both motor discharge and startup are disconnected from ground.

In the middle state startup is connected to ground.

In the ON state startups switch remains connected to ground.

Notice that in none of the states does the discharge enable line get connected to ground, meaning we never discharge the motor. We are never discharging the motor and it is holding its high voltage until it self discharged.

To find the root cause of why this mistake occurred, we can examine the rocker switch we are using.

![](images/image_2422887057.png)

Above is a diagram of the standard states of a DP3T Rocker switch. Notice that if in the MIDDLE state you flip the shorted connections on the vertical axis, we now connect GND to Discharge Enable.

(Because GND shorts to the right bottom contact, which is connected to the left middle contact, which shorts to the top left contact, which is discharge enable).

It could have been a simple mistake by the individual who initially set up the motor discharge circuitry where they didn't fully understand which contacts were being shorted in the middle state.

Finally, here are some images of the internals of the switch:

Note it's called a "Rocker" switch because the armature (right, first image below) "rocks" between states, like a rocking chair.

<img src="images/image_2422899555.png" width="334" height="230">

<img src="images/image_2422903485.png" width="324" height="288">

Here's a diagram that might help describe the states of a DP3T rocker switch (bottom left):

<img src="images/image_2422906811.png" width="545" height="313">

> **Hemat Wander** (Sep 2025)
>
> @Christopher Kalitin
> Wait, I'm a little confused on what the correct wiring would be. So the goal is to have DCH_EN connected to GND while in the middle position and have STARTUP connected to GND while in the on position. So when transitioning from the middle position to the on position we would have to both make DCH_EN go floating and connect STARTUP to GND.
> 
> However, it seems that a rockerswitch only switches one "nets" state at a time. "state" in this case means if its connected to GND or floating. So wouldn't it be impossible to make this circuitry work with a rocker switch?

> **Christopher Kalitin** (Sep 2025)
>
> Yes thats the right goal:
> 
> 1. Both floating
> 
> 2. Discharge to GND, Startup floating
> 
> 3. Discharge floating, Startup GND
> 
> In the middle state, if we flip the switches on the vertical axis (mirror horizontally), we’d have discharge shorted to GND while startup switch is still floating.
> 
> By leveraging the “diagonal” switch state in the middle state we can achieve this.
> 
> Does this make sense?

> **Hemat Wander** (Sep 2025)
>
> Ohhh I see, I didn't consider the effect of the white wire shorting the bottom right to the middle left.
> 
> So, that makes it so when startup gets connected to GND, the bottom right gets disconnected from GND, which thereby disconnects the Left from GND.
> 
> Or at least that's what we would want to happen, but we wired it incorrectly.

> **Christopher Kalitin** (Sep 2025)
>
> Yes exactly

> **Christopher Kalitin** (Sep 2025)
>
> Today we will rewrite the startup switch by this diagram and test the time we spend in the middle state as described by the previous test plan.

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Sep 2025

On V3 Brightside we have a 3 position startup switch.

- Position 1: Everything floating

- Position 2: Discharge Enable circuit grounded

- Position 3: Startup Relay Control circuit grounded

Our discharge relay is a latching relay, which means it needs a 15 ms current pulse to change state. Read more in [ECU rev 2.0 design documentation](https://docs.google.com/document/d/1QM3zkZ5lr_cZ472EEUCi2zeDzIvVOQBL3wgIkjYbXAc/edit?tab=t.0) section 9.

This is an issue because the current only flows through the discharge relay while the Discharge Enable trace is grounded, which is in the middle state of the 3 position startup switch (which the driver flips). If the driver flips the switch too quickly, we won't discharge the motor. This is a safety risk because VDX or PAS members may work with the motor or motor controller in this state.

![](images/image_2418098754.png)

To confirm if this is a significant issue, we'll run a test to find out how long we are in the second position of the startup switch.

We'll use a power supply to apply 5 V to one of the terminals. Then, we'll put an oscilloscope between the other terminal of the startup switch and ground. When the terminals are shorted to each other the oscilloscope will read 5 V, and when disconnected it'll be floating.

A possible failure mode is that when the terminals are disconnected from each other the terminal we're probing remains at 5 V instead of being truly floating. If this is the case, we can put a pull down resistor on the terminal.

> **Aarjav Jain** (Sep 2025)
>
> @Christopher Kalitin. Great attention to detail! Have you made an update on the results of this test?

---


---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

The HVC will have a high voltage section of the PCB and pre/discharge resistors increase routing complexity of the control board. So, we can consider mounting high-power resistors on the HVCs high voltage section.

HVC High Voltage section responsibilities
1. Host DCDC
2. (Potentially) host shunt current sensor uV reading IC
3. Host discharge relay (based on ECU rev 2.0)

This HV section is already significant enough that adding high-power resistors to the HVC is not a massive change.

Benefits of Resistors on HVC:
- Fewer bolts through control board (Less metal near cells, so the risk of those bolts falling in is elimiated)
- Cleaner Control Board Routing
- Integrate relays next to resistors directly onto PCB
- Greater control board packaging efficiency

Cons:
- ~$10-20 more expensive PCB
- Heat could sink into the PCB (Relatively minor since pre/discharge resistors aren't active for long and don't sink too much power)

Because under this concept pre/discharge resistors would be directly mounted to the HVC, we can also integrate the pre/discharge relay's onto the HVC, saving every more space and simplifying routing.

Note that the current discharge relay is already integrated onto ECU rev 2.0 because it's a latching relay, dissimilar from the others.

A common theme in all the pro's for this concept is that they are marginal steps in the direct of an ideal design. This isn't a grand idea that will significantly increase performance, but a marginal step in the direction of the ideal perfect battery pack.

![](images/image_2461122467.png)

*(Figure 1) MPPT precharge full current path.*

As an exercise, I decided to illustrate the path current takes while we are precharging the MPPTs. Such a convoluted current path as is shown above should be avoided in the next pack, and integrating precharge resistors / relays onto the HVC solves the majority of the problem.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin did you see my questions for this change? Not sure if it was in a different monday update?
> 
> `1. Why does moving the resistor from CB to HVC increase the amount of room on the CB?
> 
> 2. Draw out a diagram of having the resistor on the CB vs the HVC with all the relevant wiring. I am having trouble imagining if resistor on HVC is better.

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> I did not see the questions and can't find them in 2 minutes of searching, can you point me towards them.
> 
> Because relays and resistors are integrated next to each other and wires are routed as traces instead of physical harnesses, we can shrink distance margins. Relays on a PCB will also be smaller.
> 
> I'll draw a diagram

> **Christopher Kalitin** (Oct 2025)
>
> Here’s a diagram. The bottom half shows my concept where resistors and relays live on the HVC, and we have wires going across the Control Board to the relevant points (Eg, between LLIM, for a parallel resistor across it).
> 
> The big reason I wanted to move resistors and relays to HVC was to simplify routing. Another way to do this is for Control Board design to be very deliberate with selecting where to place components.
> 
> I’ve attached Hemat’s control board circuit diagram. If our physical design matches this schematic, routing will be extremely simple.
> 
> My design would have more HV current paths around the pack (since HV needs to go to HVC for the resistors). If we follow the schematic, then we just need LV connections from the HVC to the relevant relays.
> 
> Routing advantages from my idea are counteracted by having more HV wires across the control board. Note that these aren’t very high current paths, and their resistance isn’t an issue (they go to an resistor anyway).
> 
> I now think the ideal solution is better BTM routing. We should not have routing as an afterthought like the current design.
> 
> This was a useful exercise thanks for suggesting it.
> 
> ![](images/image_2463631273.png)
> 
> ![](images/image_2463634918.png)

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin I have a few comments and questions. These were the ones that were never sent:
> 
> What do you think about first getting the control board dimensions and then planning routing from there. @Deev Shah what general shape can we expect the control board to be. The exact dimensions and even ratio is not important. What is important is that we **start making iterations of the control board layout **similar to how there are iterations of the electrical system. @Christopher Kalitin thoughts on a doc like the Elec system document but for the control board?

> **Krish D** (Oct 2025)
>
> @Christopher Kalitin @Aarjav Jain
> 
> @Deev Shah Will provide the dimensions of the control board by latest Oct 20th (from me asking him in person). From here, whether or not having more components on the control board vs on the HVC will affect wiring complexity can be decided more easily by drawing out potential layouts.
> 
> @Christopher Kalitin Lets keep working on the schematic blocks for now, but continually noting these integration requirements are essential for later stages of your design (routing, layout and connector selection). Therefore, Once the control board dimensions have been given, I agree with [@Aarjav Jain](https://ubcsolar26.monday.com/users/66722948-aarjav-jain) to make a doc that details control board integrations.
> 
> I'll schedule a date to have control board layout DR0 in the next 3 weeks so the requirements for the layout can be decided in further detail.

> **Deev Shah** (Oct 2025)
>
> The shape of the control board should be similar to Brightside (rectangle). For the dimensions I can give you rough dimensions.
> 
> They’ll be in the range of ~w*l= 11*25 inches.
> 
> As
> 
> mentioned, BTM will finalise the pack dimensions by 20th October tentatively.
> 
> Also, I was looking at your ideas for the control board layout. You have placed the batt+ and batt- busbars next to eachother. This might not be the case given the complexity of electrical connections between modules. We can discuss this further during the 25th October meeting.

> **Christopher Kalitin** (Oct 2025)
>
> Here’s the picture of Berkeleys precharge resisotrs mounted on PCB:
> 
> A doc for control board iterations is a very good idea.
> 
> ![](images/image_2465879774.png)

> **Samuel Shin** (Oct 2025)
>
> @Christopher Kalitin This looks like it is solderd on, without any screws. If so, vibration of the pack may become an issue with the solder joint not supporting enough support (Resistor is big and a little heavier than other electrical components that usually go on the board). Just a though looking at the picture you sent.

> **Christopher Kalitin** (Oct 2025)
>
> @Samuel Shin
> 
> Yep, we would want to screw it to the PCB and use a conductor that doesn't take mechanical load through the solder joint (eg. wire instead of solid bit of metal).

> **Samuel Shin** (Oct 2025)
>
> Referencing @Aarjav Jain's question as I believe this hasn't been answered:

> **Christopher Kalitin** (Oct 2025)
>
> @Samuel Shin @Aarjav Jain
> 
> We already lift the PCB off the control board. Also, we could put the nut on top and insert the screw from the bottom so that the screws can be arbitrarily long. Ie. the screw is pointing up not down.

---


---

## Current Sensor Test Plan

**Author:** Christopher Kalitin

**Date:** Oct 2025

This update will be written [in the style of Mischa](https://ubcsolar26.monday.com/boards/7524358047/pulses/7524360025), ie. short and like no one except me will get maximum value out of it.

**Current Sensor Test Plan**

For scrutineering we need to inject voltage to simulate current. We'll do the same for characterizing the majority of the range of the shunt current sense amplifier. Using V=IR we know how to translate an injected voltage into a current reading (R = 100 micro ohms). We'll sweep the full range of the sensor (-6 mV to 6 mV) with the voltage divider that'll already be on the [HVC for scrutineering](https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4600660609).

Maybe ohm's law won't be working the day we do the test, so we can also inject current over the shunt resistor with a PSU to get to the exact conditions the shunt resistor will experience. This gets closer to real world condtions but only works in the range of currents we can inject (+/- 3 A with our current PSUs).

The current injection test really isn't that deep, just put the probes over the shunt (with it disconnected from the cells obv) and compare your reading in firmware / grafana (these values are the same and if they aren't you have another project to do) to PSU current then subtract to find error.

Very simple

If any poor soul is reading this in 5 years, read this blog post thats actually just about writing Monday Updates:
[https://ckalitin.github.io/ideas/2025/10/13/managing-technical-teams.html](https://ckalitin.github.io/ideas/2025/10/13/managing-technical-teams.html)

SNR decreases with word count! If I wrote this for people who understand shunts at my level (+/- a bit) or higher it would've been 3 sentences! Maybe even 2!

> **Aarjav Jain** (Nov 2025)
>
> @Christopher Kalitin why does "HVC for scrutineering" link to Mischa's update btw?

> **Christopher Kalitin** (Nov 2025)
>
> @Aarjav Jain Fixed

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

The issue described in [this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4581850114) is not having enough redundant current fault detection methods. I've found a firmware-independent (mostly) way to current fault, adding another redundancy and eliminating the need for a separate analog amplifier (along with the INA228 current sense amplifier which outputs to I2C.

The INA228 has internal fault modes which can be programmed over I2C. If an overcurrent fault is detected by the INA228, it will pull a fault GPIO high. This fault GPIO can be used to open contactors faster than STM32 firmware would be able to. This provides another redundancy (previously with the INA228 we only have pure firmware with I2C readings, see the [previous update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4581850114)).

This means we can eliminate the separate analog amplifier discussed in the previous update. I would have implemented something very similar to what Emmanuel did on the PVA - see the [voltage sensing section here](https://wiki.ubcsolar.com/en/subteams/power-and-signals/docs/PVA).

Because the redundant fault is a GPIO that the INA228 pulls high, we need a way to read this on the LV side of the HVC, so need some way to isolate. We can use an optoisolator, like we already do with ESTOP on the HVC.

Final part selection:
- [INA228](https://www.ti.com/lit/ds/symlink/ina228.pdf)(current sense amplifier IC)
- [NEK0303SC](https://www.digikey.ca/en/products/detail/murata-power-solutions-inc/NKE0303SC/1926989?s=N4IgTCBcDaIHIGkCiAGAzOgygYRAXQF8g)(DCDC providing isolated 3V3 and GND)
- [Optoisolator](https://www.digikey.ca/en/products/detail/liteon/LTV-817S-TA1/388451)(to use the fault GPIO on the LV side of the HVC, probably the same one as already is on the HVC for ESTOP isolation)
- [ISO1541](https://www.ti.com/lit/ds/symlink/iso1541.pdf?ts=1760166601559)(I2C isolator)

> **Aarjav Jain** (Oct 2025)
>
> Nice!

---

## Scrutineering

**Author:** Christopher Kalitin

**Date:** Oct 2025

This update is about BTM and scrutineering related concerns with the new shunt-resistor based current sensing method.

**Scrutineering**

The input to the current sense amplifier IC is the voltage over the shunt resistor. The maximum value of this is 6 mV. V=IR, Imax = 60 A, R = 100 uOhms, so V = 60*0.0001 = 0.006 = 6 mV.

We can't use our current method of injecting a current into the current sensor because that would require a power supply that can supply 60 A. We currently get around this by wrapping 30 loops around a hall effect sensor, effectively multiplying observed current by 30, but with a shunt resistor this is impossible.

So, we will have to inject a voltage instead (as all other teams that use shunt resistors do). This means we'll have to inject 6 mV. Because power supplies usually aren't accurate to milli or hundreds of micro volts, we'll need a voltage divider.

Our injected voltage input will be divided by 1000, so we'll be injecting 6 V to simulate 6 mV. This requires a 1M to 1k voltage divider.

A potential failure mode is the resistor being a short (eg. poor soldering), but the INA228 IC that currently is planned to be used can tolerate up to +/- 40 V on input pins, so it's robust to this failure mode.

The voltage divider will be integrated onto the HVC and we'll have two header pins that we can connect our power supply to while doing scrutineering.

**Battery Mechanical Integration**
@Deev Shah

3 primary battery mech integration points:
1. Location of shunt resistor on control board
2. Location of HVC related to shunt resistor
3. Accessibility of voltage injection headers for scrutineering

1. Shunt resistor location

The shunt resistor must be on the low-side of the battery (ie. near the negative terminal, not the positive terminal). This is because it can only tolerate up to 80 V on it's inputs and our voltage goes up to 134 V.

2. HVC Location

The distance of the voltage taps from the shunt resistors should be kept as small as possible. The greatest voltage over on these taps is 6 mV, and the amplifier itself can read around 80 nV. So, this is very susceptible to EMI. Contrast this to our hall effect current sensor which has a default output of 1.8 V - much less susceptible to noise than a 6 mV signal!

So, current sense amplifier IC must be located directly next to the shunt resistor. This means either we need the HVC directly next to the shunt resistor, or we need a little board hosting only the IC that's next to the shunt resistor and an I2C wire from this little board to the HVC.

To lower the number of PCBs I'd like to have the HVC directly next to the shunt resistor.

3. Header pin accessibility.

For scrutineering we'll need to connect a power supply to two header pins on the HVC (as mentioned in the section above). So, there's a spot on the HVC we'll need good access to, which is a consideration for control component placement.

> **Deev Shah** (Oct 2025)
>
> Thanks for making this update! For the battery mech integration points:
> 
> 1. Sounds good, we will make this a requirement for the control board project. A quick question: given its a 100uOhm resistor with 60A max expected current, the wattage might be minimal. So will this resistor be mounted on a pcb or is it like the DCH resistor on Brightside’s control board?
> 
> 2. Sounds good, if it does not affect the current sensing capabilities, from a wire management perspective having the HVC next to the shunt might be the better option. Again, this will be added as a requirement to the control board project.
> 
> 3. I believe this is highly dependent on the HVC layout and header pin placement. We should discuss this further after the control board DR0 this Saturday.
> 
> Another question that I had, have you decided on a specific shunt resistor? If yes, can you link the part so that we can estimate its footprint on the board and connection method?
> 
> CC:

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin

> **Christopher Kalitin** (Oct 2025)
>
> Here’s the shunt resistor I’ve currently baselined, and will likely go with:
> 
> https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074
> 
> It’s a relatively large package and takes all of the current in or out of the pack, it’ll be going on the control board, not HVC.
> 
> Another consideration is that it has a good amount of exposed metal, so we should consider 3d printing an enclosure for safety.
> 
> The INA228 has a max common-mode voltage of 85 V, meaning its inputs cannot be 85 V above GND. What GND means here is not clear, since isolated GND on HVC is not referenced to pack GND. Either way, the pack gets up to 134 V so we cannot put the IC on the high side of the battery.
> 
> https://www.ti.com/product/INA228
> 
> An interesting note about this IC is that apart from meausring the differential voltage over the shunt resistor, it also has a bus voltage measurement pin.
> 
> This means we can monitor an additional voltage with this IC, which could be useful for pre charge check.
> 
> The VBUS measurement pin has a max voltage of 85 V and 200 uV of precision. This is another possibility for doing precharge check.

> **Krish D** (Oct 2025)
>
> @Christopher Kalitin Some notes worth mentioning
> 
> - If your update is building off of ideas previously explained in other updates, can you please link to it so it is clear to the reader what you are referring to?
> 
> - Thank you for explaining the context for the hall effect. Makes it quite clear what point you are trying to make as if you are explaining a story. Keep this up! Adding a diagram here would also be quite beneficial.
> -  From my understanding, this voltage divider will be connected to the output side of the shunt resistor. Will it share the same HV trace or be on a separate net that comes after the isolated section? Can you show a circuit diagram of where the resistor divider circuitry will connect too on the INA228?

> **Christopher Kalitin** (Oct 2025)
>
> Which parts that relied on previous updates weren’t clear? The other Monday update from Tuesday linked to previous updates many times!
> 
> The injected voltage would connect to test points that are on the shunt resistor input. We’re essentially plugging in a power supply + voltage divider instead of the shunt resistor.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin when you get a chance can you explain exactly how you will connect the INA228 to ensure the 85V max is met?

> **Aarjav Jain** (Oct 2025)
>
> Also @Christopher Kalitin we can try to get this sponsored or get them to send a sample.
> 
> CC: @Krish D

> **Christopher Kalitin** (Oct 2025)
>
> Will email the company for a sponsorship before buying.
> 
> The 85 V max is the reason we put it on the low side.
> 
> Googling a little, I’ve found that because the HV half of the HVC is effectively floating relative to the battery (through the isolated DCDC), it’s voltage will slowly float to a value dependent on what it’s connected to. So, our isolated ground would float to 85 V so we might be fine with it on the high side.
> 
> I don’t actually understand this mechanism so an easier way to ensure were within the 85 V max is putting the IC on the low side of the battery, so our max voltage is around 0 instead of 134.

> **Krish D** (Oct 2025)
>
> @Christopher Kalitin If you can provide an diagram for how the voltage divider is connected, that would be appreciated.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin could you do some research for typically how are shunt + amplifier methods protected from EMI in a battery or other similar applications? Im worried that the 6mV is going to get destroyed by noise.
> 
> Additionally, what are @Krish and @Christopher Kalitin thoughts on getting a protoype of this current sensing pathway and putting it in our **current pack** to test current reading?

> **Krish D** (Oct 2025)
>
> @Aarjav Jain Prototypes are always beneficial, and we will definitely have to do one since this will be the team's first time use a shunt.
> 
> With our current pack however:
> - I think it will be challenging to get it setup since it will involve us having to cut up some 6AWG wire to solder in series with the shunt.
> 
> - Additionally, if you also mean to integrate this shunt with the ECU, you have to be mindful that there are no pins we can use (please double check for me) on the ECU that can be used for I2C digital communication. This means that @Christopher Kalitin's leading option, INA228, can not be used for prototyping. Therefore unless the shunt current sensor circuitry has an **isolated & analog** output, it becomes more difficult to make edits to our current pack design.
> 
> - What load is going to be used to get ~60A out of the battery and therefore over the shunt resistor? You might think we can just do some voltage injections via a resistor divider on a breadboard, however this wouldn't be testing the amplification circuitry properly (if it is on the analog output).
> 
> I'd suggest that @Christopher Kalitin decides what the process will look like to test this in our current pack. If the integration required for this test isn't time consuming (more than 2 weeks) and is* low risk* for the ECU, than I don't see why not.

> **Aarjav Jain** (Oct 2025)
>
> Also
> 
> : What do you think about having backup ports for hall effect’s to be plugged in in case there are deep issues with using the shunt resistor. Also, other than precision, could you remind me why use a shunt resistor? Cool name does NOT count. Is this used in industry?
> 
> I edited this. I said this before:
> 
> “reconsider using a Hall effect by comparing complexity and price. It doesnt seem very clean that we need isolation for this current sensing and the precharge check. “

> **Christopher Kalitin** (Oct 2025)
>
> [@Aarjav Jain](https://ubcsolar26.monday.com/users/66722948-aarjav-jain)
> 
> 1.
> 
> See this update on hall vs shunt:
> [https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4566779461](https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4566779461)
> 
> In
> short, every single accuracy (Note accuracy != precision!) failure mode of hall effect current
> sensors is felt less by shunt current sensors (eg. resistivity chaging
> as a function of temperature is less extreme than hall voltage changing
> with conductor width which changes with temperature).
> 
> Tesla uses shunt resistors and has since the Model S:
> [https://service.tesla.com/docs/Model3/ServiceManual/en-us/GUID-7597B911-B0D7-4D04-B9A7-8A10938FB237....](https://service.tesla.com/docs/Model3/ServiceManual/en-us/GUID-7597B911-B0D7-4D04-B9A7-8A10938FB237.html)
> [https://www.ebay.com/itm/304520074196](https://www.ebay.com/itm/304520074196)
> 
> Interesting to note that their sensing PCB is directly mounted onto the shunt resistor. If noise ends up being a very big problem for us, we can change the position of the sensing circuitry in a second revision.
> 
> I'll include I2C test point we could solder to for this possibility (now I2C goes from shunt to HVC, instead of raw 6 mV).
> 
> Implementing a shunt current sensor is also the most fun technical problem on HVC, everything else is well known from ECU.
> 
> In case shunt doesn't work, I'll break out from GPIOs with ADCs on HVC.
> 
> 2.
> 
> I found this thread on minimizing shunt resistor noise (not quite for our use case but similar):
> [https://www.eevblog.com/forum/projects/minimizing-noise-when-using-shunt-to-measure-current/](https://www.eevblog.com/forum/projects/minimizing-noise-when-using-shunt-to-measure-current/)
> 
> With small probes it shouldn't be too bad, and RC filters will be on the HVC to prevent AC noise.
> 
> @Krish D @Aarjav Jain
> 3.
> 
> If we were to test the shunt current sensor, we'd use a breadboard + breakouts board for the ICs. HVC schematic should be done by the end of next month so we currently don't have time to do this. If there's a worst case scenario where the circuitry fundamentally doesn't work, we have 2 months of slack in the summer (given current timelines) in which we can test.
> 
> For characterization, we'll inject voltages and could inject up to 3 A to characterize the low range.

> **Aarjav Jain** (Oct 2025)
>
> "Interesting to note that their sensing PCB is directly mounted onto the
> shunt resistor. If noise ends up being a very big problem for us, we can
> change the position of the sensing circuitry in a second revision." What is the sensing PCB in our case and can we follow this as well? @Christopher Kalitin
> 
> Why do we need to inject 3A?

> **Christopher Kalitin** (Oct 2025)
>
> In our current setup there are ~5cm leads from shunt to the circuitry on the HVC
> 
> I believe this is a similar length of leads as Waterloo’s design from what I remember at comp.
> 
> I’m not concerned with noise destroying the signal to the point where we can’t drive given other teams at comp have similar setups. The issue is just with accuracy - with extra time in the summer there’s a fun campaign of characterisation testing to be done here.
> 
> 3 A is the max of our PSUs, ideally we’d inject 60 A but we have no equipment in our bay for this.

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin When you get a chance write an update on how we can completely test the current sensing method. I will let you define 'completely' here. Additionally, define the testing procedure along with the tests.

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> Update: [https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4629141958](https://ubcsolar26.monday.com/boards/9702086049/pulses/18164045278/posts/4629141958)

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

@Aarjav Jain @Krish D
A few major design decisions for the HVC need to be made at this point, this update will detail them so we can discuss the tradeoffs in the comments on Monday so future Solar members will have this extra context.

1.
Using an I2C current sense amplifier eliminates 2 layers of redundacy for current faulting on HVC.

Our current BMS has 3 redundant ways to have a current fault:
1. Firmware sees an ADC reading out of range (essentially what reading an I2C packet would do),

2. Analog watchdog on the STM32 detects an out of range ADC reading (This eliminates our while loop in firmware as an issue, ie. if the chip is stalled we'll still fault)

3. Hardware current faulting circuitry (comparators that check if the voltage output of our current sensor is out of range)

Switching to a purely I2C shunt current sense amplifier would eliminate two of our redundancies because the current sensor output would not be an I2C packet, not a voltage we can put into a hardware current faulting circuit or STM32 ADC.

2.
An option for adding another completely separate faulting circuit is using our existing hardware current faulting circuitry (with minor changes), and supplying it with a voltage amplifier.

This way, we have 2 separate ICs that are giving us a current reading. First, the INA228 sending an I2C packet, and second the amplifier giving us a voltage that is proportional to current over the shunt resistor.

The voltage amplifier output can go both to hardware current faulting circuitry and an ADC pin on the STM32.

The voltage amplifier would also need a voltage reference IC so we can deal with negative currents. Eg. instead of a range of -1 V to 1 V corresponding to -60 A to 60 A, we would get 1 V to 3 V.

3.
I2C current readings are redundant if we have a voltage amplifier + voltage reference. So, we can eliminate the higher precision I2C current readings (800 uA) and go purely with the lower precision amplifier circuitry (est. ~10 mA precision).

800 uA current readings are clearly an MMR not an MVP. So, I think we should go with the voltage amplifier + reference method and use the STM32's ADC for current readings, we won't get as precise readings but strategy will still be happy.

The I2C current sense amplifier circuitry is pretty much already researched and ready for quick implmentation (<2 hours of my work), so I want to keep it on the HVC but make it togglable via a header pin. This way, a minimum viable HVC will not be delayed by an MMR, but we'll have the ability to implement a higher precision current sensing method in the future without redesigning the board.

Note that this solution means we could have 4 redundant current fault mechanisms (not including main pack fuse):
1. I2C current reading
2. STM32 current reading
3. STM32 Analog Watchdog
4. Hardware current faulting

> **Christopher Kalitin** (Oct 2025)
>
> Here's what the circuit would look like:
> (Note the squiggle in the middle showing isolation of the LV from the HV side of the PCB)
> 
> ![](images/image_2488848562.png)

> **Krish D** (Oct 2025)
>
> Great high level analysis Chris.
> 
> Regarding the image you sent, note as well that you would need to create a way to isolate the 3v3 power supply to voltage amplifier and I2C amplifier using an isolated power supply, like is used on the U0.2 of the [PVA](https://ubc-solar.365.altium.com/designs/44197CB3-E292-43B7-A17C-38DABCDCCD9A?variant=[No+Variations]&activeDocumentId=E_PAS_PVA1.1.SchDoc&activeView=SCH&location=[1,91.31,-112.89,123.65]#design), a DC-DC converter IC.
> Additionally, I2C requires pullups on the SD and SCL lines, so there is even more of a need for an isolated power net to act as pull-up before the I2C isolator is also a must.
> 
> Also I highly recommend that if a SPI version of the I2C amplifier exists, to use this instead. In my experience working with both protocols, I2C happens to be more buggy and prone to noise despite the pull ups. This also allows you to use an existing SPI to Iso SPI transformer setup that we've already implemented if you are concerned about complexity in implementing.
> 
> Some feedback:
> 
> - I appreciated the attention to detail with regard to adding a bias voltage to the voltage amplifier since to STM32 can not take in negative voltages. Great catch!
> - Can you add indents and markers for new points you are making? It was a bit difficult to read the update since you had sub-points on parent point 1
> 
> - Characterizing noise of the shunt current sensor due to current spikes is a must for the Cascadia. The only reason the analog watchdog was implemented was due to the fact that sustained current spikes are being read. This is worth noting as an integration test to determine how many out of window measurements will result in a fault.
> 
> I hope to see some more points regarding how this would affect scrutineering and what physical factors (accessibility to certain points of the control board) need to be noted for BTM.

> **Christopher Kalitin** (Oct 2025)
>
> Yep I was baselining the use of the same isolated DCDC used for the INA228 current sense amplifier, the diagram is wrong there.
> 
> Didn’t know PVA did this, I’ll look at the circuit.
> 
> I2C has also been buggy in my experience, but isoSPI would require an LTC6820 to drive a transformer to AC, then a transformer to DC, then another LTC6820. Much more complicated system. I2C is buggy but isoSPI introduces a good amount of complexity. I’ll look further into this maybe there are more elegant implementations.
> 
> Will add indents and better section markings, this update does look worse on mobile than on my PC an hour ago.
> 
> Agreed on noise characterisation, was reading Mischas old update on this earlier.
> 
> Scurtineering update is coming next

---

## Untitled

**Author:** Christopher Kalitin

**Date:** Oct 2025

Currently leaning towards using the INA226 digital current sense amplifier to sense voltage over a 1 milliohm shunt resistor.

Factors to consider include:
- Communication protocol / interface (ie. does it just amplify the voltage or does it have an integrated ADC)
- Voltage sensing range
- Voltage sensing precision (and hence current sense precision)

I considered these ICs:
- MAX17261 (Waterloo uses this)
- INA4290 (amplifier, no internal ADC)
- LTC2946
- INA226

The INA4290 is an amplifier so we would not be properly isolated from the HV shunt resistor without a further IC and we would have to use the STM32s ADC (see previous update for the low precision & accuracy of this). We'd need an IC to isolate I2C signals as well, so extra components for isolation are required in any case.

Since it only amplifies voltage, when current is entering the pack a negative voltage would be returned, which the STM32 can't read. We'd also be limited to around 50x amplification. With a 12 bit ADC with a 3.3 V max value, we get 0.8 mV precision post-amplifciation, which is 16 uV pre-amplification.

V/R = I, so with a 1 milliohm shunt resistor we get 16 mA of current reading precision. Not bad, but we can do about the same with a hall effect current sensor and can do much better with shunts.

The LTC2946 has an adjustable full-scale range (FSR) for its ADC which outputs over I2C. In the +/- 100 mV mode we get a least significant bit (precision) value of 25 uV. This corresponds to 25 mA precision. Even worse!

One of its potential advantages is it has a max input voltage of 100 V and an internal shunt regulator. This means if battery voltage was below 100 V, it could power itself and we wouldn't have to give it an isolated 3V3 supply. Sadly no digital current sense amplifiers with internal shunt regulators and voltage ranges above 134 V exist.

Although we won't be able to use this capability, it means we won't have to worry about transient voltages or voltage spikes. It's rated for ~100 V!

The INA226 also has an adjustable full-scale range (FSR). In its +/- 81.92 mV range we get a precision of 2.5 uV, V/R = I gives us a current precision of 2.5 mA. Amazing value, for reference on ECU rev 2.0 the precision is 140 mA.

The INA226 also has a max input voltage of 40 V, fairly safe from ESR.

We'll need to communicate with this IC over I2C, and will need an additional IC for isolating I2C from the MCU and current sense amplifier, the ISO 154X appears suitable (Waterloo uses the ISO1641).

We'll also need an IC to give it an isolated 3V3 source. Aden - a Waterloo electrical lead I met at comp - said they use an isolated 3V3 converter that sources voltage from their "normal" LV 3V3. The SN6501 looks good for our use case.

I chose a 1 milliohm resistor because of the ADC range of the current sense amplifiers. V / I = R. Our max current is 60 A, and one of the FSR ranges for the INA226 is 81.92 mV. 81.92 mV / 60 A = ~1.3 milli ohms. With a 1 milliohm resistor we get a max current of 81.92 A, which is 25% our expected max current of 60 A.

To do scrutineering with these setup we'll have to inject a voltage of ~60 mV into the current sense line with the current sensor unplugged. To do this I'll add a 1M - 10k voltage divider onto the HVC. This divides voltage by ~100x, so we'll be able to use a standard power supply. Eg. a 10 V input would be seen as 100 mV by the digital current sense amplifier.

ICs I'll likely use:
- Digital current sense amplifier: [INA226](https://www.ti.com/lit/ds/symlink/ina226.pdf?ts=1760167655129&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct-category%252Famplifiers%252Fcurrent-sense%252Fdigital-power-monitors%252Fproducts.html) (now INA228, see comment)

- I2C isolator: [ISO154X](https://www.ti.com/lit/ds/symlink/iso1541.pdf?ts=1760166601559)
- 3V3 isolator: [SN6501](https://www.ti.com/product/SN6501#params) (now NKE0303SC, see comment)

> **Christopher Kalitin** (Oct 2025)
>
> The SN6501 doesn't actually do the job I want, it's meant for use in isolated power supplies, not as an isolator itself.
> 
> The NKE0303SC is ideal for our use case.
> [https://www.digikey.ca/en/products/detail/murata-power-solutions-inc/NKE0303SC/1926989?s=N4IgTCBcDaI...](https://www.digikey.ca/en/products/detail/murata-power-solutions-inc/NKE0303SC/1926989?s=N4IgTCBcDaIHIGkCiAGAzOgygYRAXQF8g)
> 
> It is an isolated DCDC converter with a 3.3V input and 3.3V output, requiring a capacitor and inductor on its output to get low enough ripple (5 mVpp).
> 
> I looked at a few other options, but not many exist below the 1 W class. We'll likely be drawing on the order of a milli amp and the NKE0303SC is sized for 303 mA, so this is slightly not ideal.
> 
> An interesting alternative is the R1SX-3.33.3, which is slightly cheaper and looks like a PCB on top of a plastic interface to the PCB (ie. not a full sealed package), didn't know they made them like this.
> [https://recom-power.com/pdf/Econoline/R1SX.pdf](https://recom-power.com/pdf/Econoline/R1SX.pdf)

> **Christopher Kalitin** (Oct 2025)
>
> My decision in baselining the use of a 1 milli ohm shunt resistor was a mistake. This results in P = I2R = 60^2 * 0.001 = 3.6 W of power loss. Average power during an FSGP lap is 1 kW, so this is increasing power consumption by 0.36%, which is a non-trivial amount.
> 
> The driving factor behind the choice of a 1 milli ohm resistor was that if we went any lower we would not be using the full range of the digital current sense amplifier's ADC and would sacrificing some precision.
> 
> With 2.5 mA precision, even increasing this by 10x isn't a huge concern, but there's a better way.
> 
> The INA228 has a 20 bit ADC with two ranges, +/- 40.96 mV and +/- 163.84 mV, corresponding with precisions of 78.125 nV and 312.5 nV respectively. With a 100 micro ohm resistor, we would have a max voltage of 60 mV, which means either using purely the +/- 163.84 mV range or swapping between both ranges in firmware in real time while current is changing.
> 
> The INA228 allows use of a 100 uOhm instead of a 1000 uOhm shunt resistor while becoming more precise (the beauty of more ADC bits). Power draw is now 0.36 W instead of 3.6 W.
> 
> INA228 datasheet:
> [https://www.ti.com/lit/ds/symlink/ina228.pdf?ts=1760212206725&ref_url=https%253A%252F%252Fwww.ti.com...](https://www.ti.com/lit/ds/symlink/ina228.pdf?ts=1760212206725&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FINA228)
> 
> V/R = I
> V_precision/R_shunt = I_precision
> 78.125 nV / 100 uOhm = I_precision
> 0.000000078125 V / 0.0001 Ohm = 0.00078125 A = 781.25 uA precision
> 
> ECU rev 2.0 current sense precision is 140 mA, this new design gives 0.78125 mA.
> 
> 140 mA / 781.25 uA = 179.2
> 
> With a 100 micro ohm shunt resistor and the INA228, I'll increase current sensing precision by 17,900%.
> 
> Note that decreasing power consumption by 10x and precision by 4x from the previous shunt resistor circuit if merely a function of choosing a different IC with greater precision, this doesn't particularly increase cost (maybe ~$10 for a lower resistance shunt).
> 
> Here's a list of shunt resistors on Digikey:
> [https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074](https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074)
> 
> The 100 micro ohm model costs $66.67:
> [https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074](https://www.digikey.ca/en/products/detail/riedon-products-by-bourns/RSB-500-50/4967074)

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin.
> 
> 1. "The INA226 also has a max input voltage of 40 V" Did you mean ESD?
> 
> 2. Why do we need 2.5mA of precision? What is the precision requirement? What easier options does that open up for us? What about using 2 hall effects? One for higher current one for lower? Were these options considered?
> 
> 3. Could you draw out **clearly **what the path for the connections and ICs looks like? You have a lot of details but lets put those on a 'canvas' so to speak and see how this all connects, what needs isolation and why. This motivates the Control board and HVC drawings.

> **Krish D** (Oct 2025)
>
> @Christopher Kalitin  Great update, here are some notes I took from reading this:
> 
> - I2C isolators exist. Checkout [this](https://www.ti.com/product/ISO1540) one from TI with an rated isolation of 2.5kV!
> -  The attention to detail regarding the negative voltage reading, which is something the STM32 can not read, is a good thing to note. Great job noting this!
> 
> - INA4290: Common mode maximum of 120V, we definitely can't use it. I was able to figure out how you got a 50x amplification factor, however it's not immediately clear from your update. Can you explain this further? (I'm also going to assume 16mA/V is the actual current accuracy we'd be getting with the 500x amplification version of the IC)
> - LTC2946: Justifying calculations?
> - INA226: Isn't this only for 36V common mode input? Can you provide more details on what FSR means here? Since this IC requires a high side and low side shunt, where would this be mounted in the control board?
> - INA228: The maximum current input is 5mA. Why would the NKE not work here if it sized for 303mA? Has an 85V common mode input for the Vin+/- pins. How do you intend to design around this Why was a shunt resistor with a 25W power rating chosen? If P=(I^2)*R =  60^2 * 100^10^-6 = 0.36W. Assuming you are using the full range version, you could also use the calculation of P=IV = 60*(163.84) = 9.83W. Therefore using a shunt resistor that is AT LEAST 10W tolerant + safety factor of 5W is reasonable, right?

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> First, I've realized we can't as easily do hardware current faulting with a shunt. I'll write an update on this later, but since the output to the LV side of the HVC is an I2C packet, we can't use existing circuitry on ECU rev 2.0.
> 
> 1.
> This is common-mode range, not max voltage.
> 
> The INA228 has a common-mode range of -0.3 to 85 V. Common mode range is the max difference between the positive and negative differential sensing lines. We expect V = IR = 60 * 0.0001 = 0.006  V = 6 mV.
> 
> 2.
> Last I checked with Strategy the requirement was ~100 mA.
> 
> With shunt's, it's important to note that the difficulty between 25 mA of precision and 800 uA of precision is not big. It's all about specing the shunt resistor slightly differently and using a different IC of the same series (INA228 vs 226).
> 
> Two hall effects isn't required, as we could just use two ADC sensing different ranges with an amplifier circuit. Such a circuit would be similar precision to a shunt resistor, but with the accuracy issues associated with a hall effect (a shunt is just V=IR, so high accuracy).
> 
> 3.
> At a high level:
> 
> shunt resistor -> digital current sensing amplifier -> I2C Isolator -> MCU
> 
> Because the digital current sense amplifier needs power, we need to use the NKE0303SC DCDC converter to power it.
> 
> @Krish D
> 
> That's the I2C isolator I decided on!
> 
> "Common mode maximum of 120V, we definitely can't use it."
> Common-mode voltage is the difference between each terminal of the shunt resistor, which should be ~6 mV, so we can use it.
> 
> We can't use the 500x amplifier because we'd be attempting to sense 25 V with an STM32! 50x is the greatest amplification option we could use (0 to 2.5 V).
> 
> Vprecision = 25 uV, R = 1 milliohm, V/R = I = 25 uV / 0.001 ohms = 25 mA.
> 
> Common-mode vs full scale range is also something I was confused about. My understanding is common-mode range is max allowable voltage before damaging the IC, full-scale range is the ADC sensing range. I don't think a high-side and low-side shunt are **requirements**, but just a typical application.
> 
> The NKE0303SC does work for us, it's just far bigger than we'll need. There could be a solution that has a lower current rating that is cheaper, but I couldn't find one.
> 
> The shunt was chosen for it's resistance, not power rating. If the power rating of a shunt resistor is greater than 0.36 W, then the only two relevant variables are cost and resistance (100 micro ohms required).
> 
> Your P=IV calculation was incorrect because the voltage in that equation is the drop over the resistor (6 mV), hence why we use P=I2R! We only need to size for 0.36 W, and the smallest power rating I saw was ~5 W, a 15x factor of safety.
> 
> Very good questions

> **Krish D** (Oct 2025)
>
> @Christopher Kalitin Ah. Thanks for clarifying the common mode voltage range as a term, good to know!
> 
> When deciding on shunt, let's look for something cheaper with not as high of a power rating then.
> 
> P=IV : Dumb mistake on my part, thanks for correcting this!

---

## Hall Effect Current Sensor Error

**Author:** Christopher Kalitin

**Date:** Oct 2025

**Hall Effect Current Sensor Error
**

![](images/image_2479655617.png)

I found [this great paper](https://www.iconopower.com/v/lem/coulometry.pdf) which characterized a hall effect current sensor.

The two types of error are gain error and offset error. Gain is the slope of the current error as a function of current. Offset is a constant error.

Because we have roughly equal current flowing into and out of our battery (arrays and motor), the gain error cancels out if we integrate to find total energy. We overestimate current coming out and overestimate current going out, so it nets out to zero.

Offset error is more of an issue because it does not cancel out, it compounds with time and not as a function of input current. So, whether we're drawing 1 A or 100 A for 60 s, the net error is the same.

This is more of an issue at low currents where an error of 0.1 A is a greater proportion of total current (10% vs 0.1% for 1 A or 100 A).

The paper also mentions error as a function of temperature, which we can consider characterizing for our next current sensor.

![](images/image_2479663300.png)

Importantly, the terms of the error are the same as what we found when [characterizing our HASS-100S](https://ubcsolar26.monday.com/boards/7524367629/pulses/7524367868/posts/3902002110) hall effect current sensor a year ago. Notice the graph above has a constant error term and gain error (negative slope, instead of the paper which saw a positive slope).

![](images/image_2479666451.png)

*This graph is also from our [current sensor characterization project](https://ubcsolar26.monday.com/boards/7524367629/pulses/7524367868/posts/3774039039).*

Another type of error is linearity error. ADCs also experience linearity error, which you can see in the graph above. These errors are more difficult to model (it's not a line y=mx+b), and hall effect devices are subject to this error in some proportion. Linearity error is usually minimal, but is a failure mode if we choose a hall effect current sensor.

**Shunt Current Sensor Error**

![](images/image_2479675101.png)

Shunt current sensors use a shunt resistor in series with the main load path, and look at the voltage drop over it (V=IR).

Because shunt resistors are resistors, their resistance varies with temperature.

This should be fairly minor, and we'll be able to adjust for this error with a degree 2 polynomial in firmware using the thermistor output from the cell boards. We just need to adjust for ambient temperature, and don't need extreme precision, so a dedicated thermistor on the shunt resistor is not needed.
[Here's a nice article](https://www.knick-international.com/en/blog/shunt-resistor-versus-hall-effect-technology/) on sources of error for shunts vs hall effect.

Hall effect current sensors also suffer from temperature changes due to the conductor experiencing the hall voltage expanding. Shunt resistors suffer less from temperature than Hall's.

Shunt current sensors don't suffer from:
- temperature as much as Hall's
- EMI of other current paths near it
- reference voltage fluctuations

Overall, it shunt current sensors have fewer precision failure modes than hall effect current sensors.

> **Hemat Wander** (Oct 2025)
>
> @Christopher Kalitin
> 
> I remember we we're discussing how other teams at comp did scrutineering with a shunt resistor, as I assume it would be a little more complicated than with being able to have a separated component for which we can decide the connection.
> 
> I believe we said something like we can just modify the voltage reading of the ADC going to the chip, and so we don't have to actually shove current through the shunt resistor. Either way, just another consideration.

> **Christopher Kalitin** (Oct 2025)
>
> @Hemat Wander
> 
> Yep, scrutineering can't be done in the same way because we would have to put 60 A through the shunt resistor. We'll have to inject a uV voltage with a voltage divider either on an external board or built into the HVC.
> 
> We could easily make a 1M - 1k voltage divider to divide PSU voltage by 1000. Putting this on the HVC with two header pins could be an elegant implementation.
> 
> In contrast, Waterloo has this ugly voltage divider perf board:
> [https://ckalitin.github.io/solar/2025/07/09/fsgp-team-insights.html](https://ckalitin.github.io/solar/2025/07/09/fsgp-team-insights.html)
> 
> ![](images/image_2479735306.png)

> **Aarjav Jain** (Oct 2025)
>
> @Christopher Kalitin
> 
> 1. How will we do scrutineering with a shunt resistor? Can you describe the **exact **implementation and process?
> 
> 2. What is the accuracy of using a shunt resistor?
> 
> 3. Are there certain ratings we need to look for the resistors?
> 
> 4. What *is* linearity error and where does it come from?
> 
> Feedback: You did quite a bit of reading and learning for the 2 different options and came to a conclusion which is great. However, I encourage you to give a summary of the section you wrote. Ex. you mentioned details about the Hall Effect Sensor. Then after, give a summary of what points are important and why are they important (what does this all tie back to and lead to). Additionally, explain the goal of the update. At the end when you say "there are fewer precision errors" it sounds as if that is the sole reason for going with shunt resistor current sensing. Explain *why *you are talking about what you are talking about.

> **Christopher Kalitin** (Oct 2025)
>
> @Aarjav Jain
> 
> 1.
> For scrutineering instead of a current supply and external extra current sensor, we'll unplug the shunt from the HVC and replace it with a power supply + voltage divider (with the divider integrated into the HVC). Then, we show the scrutineers our voltage divider resistance values and fault settings and demonstrate. This is the same as Waterloo.
> 
> 2.
> I found no explicit accuracy value for shunts, but every single accuracy failure mode that hall effect current sensors see impacts shunts far less. Eg. temperature where hall effect sense lines expand more than the resistance the shunt changes.
> 
> Also, with greater precision we have more ability to characterize the accuracy error. One of the issues characterizing Brightside's current sensor was that we reached the limit of precision and couldn't increase accuracy further.
> 
> This is why the accuracy graph looked like this, instead of a more straight line (I could only work in increments of 140 mA):
> [https://ubcsolar26.monday.com/boards/7524367629/pulses/7524367868](https://ubcsolar26.monday.com/boards/7524367629/pulses/7524367868)
> 
> ![](images/image_2482910541.png)
> 
> 3.
> Power (Must be >0.36 W which we dissipate), resistance (100 micro ohms), cost (Hopefully ~$50 each, similar to HASS-100S hall effect we have now).
> 
> 4.
> All error arises from one physics principle or another. When the law causing the error is non-linear, we get linearity error. Eg. resistance changes exponentially with temperature, so this is a non-linear type of error.
> 
> 5.
> Good feedback, these updates were written directly after my research mostly as notes so I can optimize more for the reader and conveying purpose. The best way to fix this I think is a summary section at the top, then all technical details & notes.

---


---

## DCDC

**Author:** Christopher Kalitin

**Date:** Jan 6

**DCDC ****Test Results**

The goals of testing were:
1. Operate at 46 W (nominal power)

2. Record temperature vs time for 10 minutes

3. Derive efficiency for one point

4. Operate at our full HV voltage range

5. Plot Efficiency vs. Current

6. Plot Output Voltage vs. Current

The last 2 goals serve to recreate performance graphs from [the datasheet](https://www.power.com/design-support/design-examples/rdr-85slr-46-w-dc-dc-converter-solar-racing-car-using-innoswitch3-aq-900-v-powigan).

[Testing data spreadsheet](https://docs.google.com/spreadsheets/d/1ppIUuNVFHrE4kxHu8hYvxWLMagOhAPkGQVVrrkbQVtM/edit?gid=20239919#gid=20239919)

**Test Setup**

![](images/image_2660578867.png)

The testing setup follows the description in the [test plan](https://ubcsolar26.monday.com/boards/9702086049/pulses/10794893055/posts/4787142170).

Note all exposed HV Connections were taped to prevent shorts. You can see this on the right side of the DCDC, on the red wire coming off the HV side, and on the purple wire coming off of it.

The pins for the voltage input / output were very small, so male-to-male jumpers were used. These didn't cause any thermal issues.

**Test Data**

25 data points were obtained between 12.8 and 54.5 W output power and 80 to 150 V input. Note the DCDC's nominal ratings at 46 W (80 W max), and 100-150 V.

To vary the load, and hence current, combinations of 3x 10 ohm, 2x 25 ohm, and 1x 3 ohm resistors were used. Note that the exact resistance used never matched what was observed with R=V/I because of contact resistance (maybe alligator clips). This is shown in [columns H to J of the first page in the spreadsheet](https://docs.google.com/spreadsheets/d/1ppIUuNVFHrE4kxHu8hYvxWLMagOhAPkGQVVrrkbQVtM/edit?gid=0#gid=0).

**Goal 1: Operate at 46 W (nominal power)
**
We operated up to 54.5 W, so goal 1 was achieved.

**Goal 2: ****Record temperature vs time for 10 minutes**

![](images/image_2660628230.png)

I tested two cases at different power levels. The terminal temperature of the 4.77 A output 80 V input case (reasonable worst-case for our car) was ~40 C after 10 minutes.

We didn't see far worse thermal performance at greater than nominal current, so we may be able to operate at greater than 46 W (maybe with added cooling).

![](images/image_2660643213.png)

Power Integrations performed a similar test in an enclosed environment and at room temperature (we were in the bay with the bay door open, as maybe ~15 C). After an hour they got 44.4 C on the Switching IC. This appears to align with our values.

<img src="images/image_2660633289.png" width="222" height="295">

The test setup involved pointing our thermal camera towards the IC on the back of the DCDC (the expected hot spot). It was kept in a constant position to ensure we were recording the same point every time.

<img src="images/image_2668180554.png" width="320" height="425">

At the end of the highest power test, the 3 ohm resistor got to 230 C. Pay closer attention to resistor power next time.

Interesting, while monitoring current throughout the entire test, it didn't appreciably increase (resistance decreases with temperature, so this is partly what I expected).

**Goal 4: Operate at our full HV voltage range**

The DCDC outputted 54 W at 80 V input and 150 V input. Success.

**Goal 3/5: Plot Efficiency vs. Current
**
First, I'll show the efficiency graph from the datasheet for what I expected.

Note Load% is output current over 46 W (nominal power).

![](images/image_2660702377.png)

We got this:

![](images/image_2660705057.png)

This graph does not follow the same trend as the efficiency plot from the data sheet at all, and most of the efficiencies we got were above 100%.

![](images/image_2660721404.png)

A clear downward trend in efficiency is seen as input voltage decreases.

Notably, operating below the rated 100 V input minimum gets us far lower efficiency at ~90%. This is expected as it's outside the listed nominal range of the DCDC.

**Why Did The Efficiency Test Fail?
**

I suspect our current measurements were inaccurate.

P_in
= P_out is always true and P=IV is also always true. This leaves us 4
variables, current and voltage on the input and output.

Output
voltage was almost always 11.9 +/- 0.05 V, and input voltage was tested
with 2 different multimeters are returned values +/- 0.3 V (the other
multimeter was not our usual orange handheld DMM, and seems less
trustworthy).

![](images/image_2660760842.png)

The Keithley 2110 DMM ammeter mode appears untrustworthy to me because it gave very different current readings when we manually set the range to the 1 A mode, 3 A mode, or 10 A mode.

This is shown in the table above, with up to a 10% difference.

If we are to repeat this test, the accurate of the DMMs must be investigated.

**Goal 6: Plot Output Voltage vs. Current**

This test matched expected values from the datasheet fairly closely. We were around 11.98 V most of the time, dropping at higher power.

Note that I only tested voltage once at 54 W (for all input voltage values, 80 to 150) instead of 4 individual times like all other power levels.

This means the data declining to 11.9 V at 54 W isn't completely trustworthy because I only got 1 datapoint and copy and pasted it for the rest of the 54 W cases.

![](images/image_2660620235.png)

![](images/image_2660623412.png)

**Next Steps**

1. Email Power Integrations about using the DCDC at 90 V
2. Email PI about how long we can expect to run at >46 W, thermal and efficiency concerns.

I don't believe we should look for another DCDC or repeat this testing as HVC testing is far more important.

> **Aarjav Jain** (Jan 12)
>
> @Christopher Kalitin why would we want to use the DCDC at 90V anyways?
> 
> Overall thanks for the thorough testing!

> **Christopher Kalitin** (Jan 12)
>
> Minimum voltage of the pack is 86.4 V. 2.7*32=86.4

> **Krish D** (20d)
>
> @Christopher Kalitin Just to be clear, what will determine if we are to use this DCDC or not?

> **Aarjav Jain** (14d)
>
> @Christopher Kalitin: In other words: What specifically do you want to ask PI about when you say "Email Power Integrations about using the DCDC at 90 V"?

> **Christopher Kalitin** (13d)
>
> 1. Is it reasonable to use the DCDC at ~90 V and up to 5 A out of the box?
> 
> 2. What changes should be made to get higher efficinecy at 90 V input? (From your email chain with them the immediate path forward on DCDC modifications is not clear)
> 
> 3. Is the max temperature really 50 C? If their test was at 25 C ambient and got to 40 C, I don’t think our DCDC will stay below 50 C during comp (much higher ambient temperature in Kentucky).
> 
> 4. What’s up with these connectors?

> **Christopher Kalitin** (3d)
>
> 5. Heat sink
> 
> Link datasheet in v4 BOM

---

## DCDC Test Plan

**Author:** Christopher Kalitin

**Date:** Dec 2025

**DCDC Test Plan**

**PSU Selection**

First, we need Power Supplies with isolated outputs (so negative isn't shorted to ground) and that have ~150 V isolation voltages (so when wired in series, the input voltage to a given PSU can be higher than 0 V).

From the datasheets

* PSU units means how many independent power supplies are in an individual piece of equipment.

I'll use 3 XT 30-2's in parallel with an additional PS280. I'll start at 120 V (all at max voltage) as 120 V is in the 100-150 V nominal range of the Power Integrations DCDC.

**Parallel Diodes**

I'll also need to connect diodes in parallel with each power supply connection to ensure no PSU will ever have negative voltage over it, damaging the internal polarized capacitors.

For example, imagine we have two power supplies in series at 30 V each but only the first one is on. PSU 1 will try to push current through PSU 2, but PSU 2 is disabled so it's acting as an open circuit. So, PSU 2's positive terminal will stay at 0 V, but its negative terminal will be brought up to 30 V by PSU 1.

To prevent -30 V experienced over the terminals of PSU 2, we add a diode in parallel so the voltage over PSU 2 is limited to the forward voltage of the diode.

We have the [S5JB R5G diode](https://www.digikey.com/en/products/detail/taiwan-semiconductor-corporation/S5JB-R5G/7358544) in stock in the Proto Crate. It has a max voltage of 600 V, max current of 5 A, and forward voltage of 1.1 V. It's suitable for our purposes, but it is an SMD component so I'll have to solder leads to it.
**
Equipment**

- XT 30-2 PSU
- PS280 PSU
- 2x 2110 5 1/2 Digital Multimeter
- Handheld orange multimeter
- Power Integrations DCDC
- Alligator clips
- Electrical Tape
- Thermal Camera
- S5JG R5G Diodes
- Spare wire + wire stripper + soldering iron

**Wiring**

**
Instructions**

1. Wire the equipment as shown in the wiring diagram above. Any open connections should be wrapped with electrical tape.
2. Disconnect the DCDC and probe PSU output voltage, to ensure it's 120 V
3. Disconnect resistors from DCDC, then connect DCDC to HV input. Probe DCDC output to ensure its 12 V.
4. Connector one resistor, record current + input voltage + output voltage.
5. Repeat for 2 and 3 connected resistors (turning everything off in between).
6. While doing the above, watch the DCDC with the thermal camera and note its temperature.

CC: @Krish D @Aarjav Jain @Hemat Wander

> **Christopher Kalitin** (Dec 2025)
>
> I wired up the PSUs in series and got the expected result.
> 
> Note the diode wiring in the first image is incorrect.
> 
> Also, the PS280 PSU (on top) has a series mode built in, so presumably has the parallel diodes built in.
> 
> ![](images/image_2648468581.png)
> 
> ![](images/image_2648468587.png)

> **Hemat Wander** (13d)
>
> @Christopher Kalitin
> 
> I'm a little confused on what the purpose of the diodes was in this case? Why would we expect any power supply to have a negative voltage supplied to it?

> **Christopher Kalitin** (13d)
>
> @Hemat Wander
> 
> The negative voltage is a result of supplying ~30 V into the negative terminal, while the positive terminal is ~0 V (as it's connected to the high-side of your circuit, which has ground supplied by the PSUs).

> **Hemat Wander** (13d)
>
> @Christopher Kalitin
> 
> Ok I see, so if one of the power supplies was off by accident, we would expect the positive terminal to stay at 0V while the negative terminal goes up to whatever supply behind it is at. Why would we expect the positive terminal to stay at 0V and not be at 0V relative to the negative terminal?

> **Christopher Kalitin** (12d)
>
> @Hemat Wander
> 
> Consider the case in which you connected your array of series power supplies to a circuit and the most positive terminal has some positive voltage.
> 
> A power supply turned off can be treated as an open circuit (note this is different from a power supply set to output 0 V, which is a wire).
> 
> Now, if the most positive power supply is off, then the most positive terminal is floating relative to the rest of the power supplies.
> 
> Except, we have a circuit connected between it and GND, which will pull it to GND. Otherwise, you'd have a circuit that is on (eg. a resistor burning power) with no power source, an impossible situation.

---

## DCDC Test Plan Exploration

**Author:** Christopher Kalitin

**Date:** Dec 2025

**DCDC Test Plan Exploration**

Goals:
1. Operate DCDC at 3.83 A (46 W at 12 V, the listed nominal power)
2. Record temperature vs time for 10 minutes while operating at this output current
3. Record input current & voltage and output current & voltage to derive efficiency
4. Operate it at our full HV voltage range

Extras:
1. Plot Efficiency vs. Current
2. Plot Output Voltage vs. Current

At a high-level, the following equipment is required:
1. HV Source (Either out battery or series PSUs)
2. LV Load (Parallel high-power resistors)
3. Temperature measurement (thermal camera)
4. Voltage and Current Measurement on Input and Output (DMMs)

**HV Source**

For the HV Source we can either use some of our 6 power supplies wired in series, or use the Motor Anderson connector to source voltage from our battery.

Pros / Cons of using series PSUs:
1. Must only use isolated output PSUs (check datasheets) (ie. GND can't be tied to negative output)
2. Best to only use PSU of the same model (so we'd be limited to 3 in series, up to 90 V)

[Here's a link](https://electronics.stackexchange.com/questions/735004/can-you-connect-isolated-power-supplies-in-series) on using PSUs in Series.

Pros / Cons of using our pack:
1. May have to charge it
2. Motor Anderson connector will require an alligator to wire connection, and lots of electrical to ensure no short occurs
3. Risk of shorting our pack

Overall, I'd prefer using Power Supplies for the benefit of safety and not potentially risking our pack. This is only possible if we have at least 4 power supplies with isolated outputs.

If a power supply does not have an isolated output, that means it's negative terminal is connected to ground. This means if we connect the positive output of one battery to another, we're just shorting 30 V to ground.

Side note: This is how all PC ATX Power Supplies operate, and is why you can't use PC PSUs to get higher voltage than they're designed for. This is an issue you have to worry about if you need 24 V for stepper motors for your IGEN Capstone Project.

**DMMs for Current / Voltage Measurement**

Voltage measurements can be taken with our orange hand held multimeter in the bay. Extreme care must be taken when working on the HV-side of the DCDC to not short anything.

Current measurements will be taken with our [Keithley 2110 5-1/2 Digital Multimeters](https://assets.testequity.com/te1/Documents/pdf/keithley/2110-ds.pdf), here is the [reference manual](https://download.tek.com/manual/2110-901-01(C-Aug2013)(Ref).pdf).

![](images/image_2643680033.png)

A fun note is that it uses a shunt resistor for current sensing.

Also the DMM has a thermocouple sensing feature, which @Luke Santosham might have found interesting for Motor RTD characterization.

The ammeter mode is rated for AC voltage, so we will have no issue putting ~100 V into it. There are two current sense inputs, one with a 3 A RMS 250 V fuse and the other with a 10 A RMS 250 V fuse.

We will manually be recording values in a spreadsheet and won't be doing any fancy SCPI Python scripting as it's not required here.

Note that even if we use our pack as the HV source, we can't use it's current sensor because it's precision is 140 mA. Our HV-side input current will be ~0.38 A (because P in = P in, and P = IV, and the voltages are different on both sides). So, we'll not nearly have enough precision for any meaningful efficiency number.

**Parallel Load Resistors**

High-Power Resistor Inventory:
- 5x 10 Ohm 50 W
- 3x 25 Ohm 50 W
- 1x 3 Ohm 50 W
- 1x 330 Ohm 50 W
- 3x others with poor labels

Note all power ratings are above our DCDC's power rating, so high current won't be a problem (aside from heating).

Our output voltage is 12 V and V/I = R so we can find the number of parallel resistors we need to achieve a particular output current.

3x 10 Ohm resistors in parallel gets us 3.33 Ohms. 12 V / 3.33 Ohms = 3.6 A.

If we want to get even closer, we can use 2x 10 Ohms and 3x 25 Ohms for an equivalent resistance of 3.125 Ohms and a current of 3.84 A, almost exactly the 3.8333 A rated output of the DCDC.

**Open Items**

Before proceeding, I just need to figure out if our PSUs have isolated outputs.

If so, we'll string PSUs in series. If not, we'll use our pack as the HV source.

> **Aarjav Jain** (Dec 2025)
>
> @Christopher Kalitin: What is the DCDC converter you wanted to use for the HVC previously? We can order that and test it against this one. It will require some extra setup, however.
> 
> CC: @Krish D

> **Christopher Kalitin** (Dec 2025)
>
> Listed in [this update](https://ubcsolar26.monday.com/boards/9702086049/pulses/18080997270/posts/4682602026).
> 
> 1. [0RQB-D0W12LG](https://www.digikey.ca/en/products/detail/bel-power-solutions/0RQB-D0W12LG/7597087) - $112.80
> 2. [TEP 150-7212UIR](https://www.mouser.ca/ProductDetail/TRACO-Power/TEP-150-7212UIR?qs=amGC7iS6iy%2BW5rbcsmqluA%3D%3D&utm_source=OEMSecrets&utm_medium=aggregator&utm_campaign=TEP+150-7212UIR&utm_term=TEP+150-7212UIR&utm_content=TRACO+Power) - $300.85 (in stock on Mouser, not Digikey)
> 
> The cost is non-trivial, so we can compare against our current DCDC if we want something to compare against.

> **Aarjav Jain** (Dec 2025)
>
> Seems expensive because the power rating is super high. No other < 100W options? 6A * 12V = 72W as reference.

> **Christopher Kalitin** (Dec 2025)
>
> @Aarjav Jain
> 
> If I remember the search correctly, there were many options down at ~5 A. Most DCDCs are well oversized for their application.
> 
> Efficiency is more what I was optimising for in the search.

> **Aarjav Jain** (Jan 5)
>
> @Christopher Kalitin would these DCDCs, when operating a much lower than its max power output, still be more efficient than DCDCs operating near their max power output?

> **Christopher Kalitin** (Jan 6)
>
> @Aarjav Jain
> 
> Efficiency approaches a limit as power goes to the nominal power rating.
> 
> So, operating at lower load% results in lower efficiency. This is why we want our DCDC to have a reasonably low nominal power rating, eg. using a 20 A rated DCDC results in far lower efficiency for us.
> 
> Image from [PI datasheet](https://www.power.com/design-support/design-examples/rdr-85slr-46-w-dc-dc-converter-solar-racing-car-using-innoswitch3-aq-900-v-powigan):
> 
> ![](images/image_2660787379.png)

---

## Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** Dec 2025

PI DCDC Converter Tracking Number: [887167298104](https://www.fedex.com/fedextrack/?trknbr=887167298104&trkqual=2461027000~887167298104~FX).

It will arrive at ECE Stores **This Saturday. **Most likely pick-up will be available on Monday Dec 21st.

ECE Stores - MCLD 1032
2356 Main Mall
Vancouver, BC V6T 1Z4
Canada
VANCOUVER, BC, CA
V6T1Z4

CC: @Krish D @Christopher Kalitin

---

## Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** Dec 2025

@Christopher Kalitin : Power Integrations has shipped their DCDC kit. To re-iterate this is the goal of us getting this converter. For more context see [this post](https://forum.digikey.com/t/new-powigan-design-kit-brings-95-efficiency-to-solar-race-cars/59352).

For more information about the sample DCDC see their page [here](https://www.power.com/design-support/design-kits/rdk-85slr-reference-design-kit).

**Next Steps**

CC: @Krish D

![](images/image_2625490826.png)

> **Christopher Kalitin** (Dec 2025)
>
> @Aarjav Jain
> 
> Considering we could have a usable DCDC, the best path forward is to do acceptance testing on it to see if it's suitable. If has a reasonable efficiency (>90%) and a high enough current limit (3 A minimum), I think we should go with it.
> 
> HVC testing seems to be the long-lead item for timelines, so more effort should be dedicated on this versus more thought on a DCDC if we have one that works.
> 
> Assuming it arrives around Janurary, DCDC testing will take place during HVC bringup and HVC firmware work.
> 
> In short:
> - Test the PI DCDC
> - If suitable (>90% efficiency, >3 A), use it and continue HVC testing
> - If not, look for a replacement

> **Aarjav Jain** (Dec 2025)
>
> @Christopher Kalitin sounds good! Lets do testing on the PI DCDC. When you get a chance, could you make an update here that explains those tests and the resources needed so I can order it if necessary.

> **Krish D** (Dec 2025)
>
> @Aarjav Jain Exciting!
> 
> It's worth noting that this DCDC does not come with a metal heat sink. Definitely worth looking into if a heat sink is necessary & how it will be mounted. I'd wager that we *may* need to make a custom PCB to properly mount a heat sink to the PCB and mount it to the HVC.
> 
> @Christopher Kalitin Once you've made an update regarding the testing the DCDC converter, can you please book a check-in meeting with me, @Aarjav Jain, and @Deev Shah  to discuss timelines and integration notes in more detail?

---


---
