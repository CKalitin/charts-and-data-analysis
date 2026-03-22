# Untitled

**Author:** Hemat Wander

**Date:** 16h

@Aarjav Jain @Krish D

Going through checklist to finalize PCB:
Before ordering, the last things I want to do are check over all of the notes I've written to ensure nothing was missed.

Some changes:

-
I changed the Vin capacitance to a larger value to better support
switching during scrutineering. if this later isn't desired, we should
be able to revert to a 100nF as before.

![](../../images/image_2845339065.png)

![](../../images/image_2845338967.png)

-
I removed the polygon pours for the top and bottom signal layers from
last time. This is because we want to keep the HV parts of the PCB (on
the top and bottom layers) as isolated as possible.

![](../../images/image_2844608658.png)

- I made all the vias tented, to prepare for ordering.

-
Common mode capacitance, I previously removed the DNP common mode
capacitors due to them adding a stub for possibly no benefit. As Micha
mentions, the presence of the common mode choke makes it kind of
redundant, however it might be helpful later down the line if we are
experiencing noise issues we can't help. Plus we can also try cutting
the trace later down the line if needed. [Related Masterboard Update](https://ubcsolar26.monday.com/boards/9565350285/pulses/18093100406/posts/4770381167)

![](../../images/image_2844634419.png)

I thus added in the capacitors.

![](../../images/image_2845151786.png)

- Added this silkscreen

![](../../images/image_2845233092.png)

Going through the previous reviews

- I addressed everything in this [review](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.7k4z6smstfsq), remaining points:

- I also addressed all of the points / made comments for all the other reviews.

PCB checklist:

I went through this [PCB checklist](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.rawt2gk61hu1), which made me re-evaluate the silkscreens, and vias sizing.

Other points to review:

-
Currently I have the input for the buck converter connected to the
module 16 after it has been connected by the autoconnection circuitry.
Looking at this again, I'm considering if I need to do this, or if I
should connect it to before the autoconnection circuitry? As the PFETs
should only have milliohms of resistance, and we have a 100 ohm
resistance in the buck converter input path anyways, it shouldn't
matter. Also, I'm not sure how VDRIVE will behave when the ADBMS1818 is
not powered. Thus, its best to leave it as after the PFET, thus
everything gets powered at the same time.

![](../../images/image_2845318038.png)

<img src="../../images/image_2845317621.png" width="662" height="175">

- I increased text height to 1.5mm

![](../../images/image_2845319012.png)

I checked that the IC's all have the correct pinnout
- ADBMS1818
- SM91501ALE
- SN74LV4052AQDYYRQ1
- LCC110STR
- SN74LVC1G3157DCKR
- PFETs and NFETS

Added bypass pathways for VREG and VREF, so they don't get cut off at the edge of the board and cause overheating.

![](../../images/image_2845323722.png)

![](../../images/image_2845341477.png)

- Added a ground path under the returning voltage lines here at the cost of being closer to isoSPI.

![](../../images/image_2845326993.png)

-
I realize I accidentally reversed the channel A and B of the isoSPI, so
I needed to reverse them and change the silkscreen accordingly.

![](../../images/image_2845328291.png)

![](../../images/image_2845338320.png)

-
The old altium has a bunch of stitching vias for VREG, not sure why
they added this, or if this is something for me to consider. Currently, I
have all my power routed through traces.

![](../../images/image_2845333126.png)

![](../../images/image_2845334424.png)

Remaining Points (these are not finished in this update):
Bigger changes:
- Should we change how the 16 voltage taps are connected to the ADBMS1818

- Should we connect Vin of the ADBMS1818 to the internal 16th module always (even when scrutineering)

Smaller considerations:

- Discharge timer for the ADBMS1818 (DTEN) -> 0 ohm resistor?

- Should we have fusing on VREG

- Do we need to fuse the main GND of the slaveboards

Minor points:

- Do we need to make the pinnout match that of the module board
- Do we have enough test points?

- Are vias sized and multiplied appropriately for the current they must handle?

- Is this an issue for HV integrity?

![](../../images/image_2845340236.png)

---

# Untitled

**Author:** Hemat Wander

**Date:** 2d

@Aarjav Jain @Krish D
Filling the top and bottom layers with a polygon pour:

As
this slave board iteration is hopefully wrapping up, one last thing I
wanted to add was to fill the top and bottom layers with a polygon pour,
to decrease cost (less area needs to be cut away), and more importantly
to create a neighboring return path, which will increase the speed and
accuracy of the readings, by treating these ADC lines more like a high
speed signal. It should reduce the impedance of the lines which should
improve reading accuracy.

I wasn't able to find any resources
saying if this is a good idea or not, but based on wanting to reduce
inductance, this seems like a good idea?
Resources:
[https://www.analog.com/en/resources/app-notes/an-1142.html](https://www.analog.com/en/resources/app-notes/an-1142.html)

[https://resources.altium.com/p/how-properly-ground-adcs](https://resources.altium.com/p/how-properly-ground-adcs)

**What will it look like?
**

![](../../images/image_2842623638.png)

**Choosing a net:
**There
are a few things I could make these polygon pours, either the filtered
voltage tape (C1 .. C18), or the input voltage (V1), or the
autoconnection voltage (VIN_TOG_1), etc. Furthermore, I could either
make the polygon pours be the return path, or the actual path itself.

For
the first point, I think making it be the fused voltage makes the most
sense (V1) as that will be the raw return path going up to the actual
voltage of the cell (similar to a raw GND). Next, I think making it be
the return path makes more sense to reduce inductance, as we otherwise
wouldn't have a neighboring return path.

I repeated a similar thing on the bottom layer.

![](../../images/image_2842693207.png)

**Important note:
**I am relying on this [HV routing calculator](https://resources.altium.com/p/using-an-ipc-2221-calculator-for-high-voltage-design),
which says that internal conductors (I'm interpreting to mean traces
inside the PCB), only need a distance of 0.1mm, and all of our rule
distances are at least >0.2mm or >0.254 mm. This is why I think
that including this polygon pours for this HV board is okay.

Other Polygons:
There
was some space left over after pouring the return paths for each ADC
layer. Thus, I decided to add a polygon pour for the VREFs. I decided to
note add one for VREG, as I thought it might radiate unnecessarily
radiate switching noise to the ADC lines. However, VREF2 should be safe
to add a polygon pour for.

Other Notes:
I
rerouted isoSPI again, this time avoiding cross over any of the isoSPI
lines, while keeping a <1ps time difference between the adjacent
lines.

![](../../images/image_2842604730.png)

**Important: **I made all stitching vias untented for the sake of reviewing, we need to revert the vias back to being tented afterwards. CC: @Aarjav Jain

![](../../images/image_2842606851.png)

> **Aarjav Jain** (2d)
>
> @Hemat Wander : Sorry, the vias can stay tented I was just wondering if that was the reason I could not see them.
> 
> Otherwise looks good!

---

# Untitled

**Author:** Hemat Wander

**Date:** 3d

Checking things with the Slave board
There are a few important things I need to check with the slave board before ordering.

Organizing cell inputs with 16 inputs going into the 18 input ADBMS1818.
Currently I have it so that we are skipping the input C_12, as is shown in the last pages of the [ADBMS1818 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adbms1818.pdf)
(pg. 87). However, I wrote down in my notes that skipping inputs
like this actually makes open wire checking for those lines worse.
However, I can't remember where I read it, and I unfortunately did
not write down where I read it (should do this next
time).

![](../../images/image_2839288212.png)

After
scouring through the datasheet, I can't find any information about
this, so I will leave it as is. Either way, the most I think we
would loose is open wire checking on just one cell input, which should
be fine. I think its better to leave it as what the part of the
datasheet I could actually find says.

LED input current
I
realized that the warning LEDs we are using for idiot
proofing only have a valid current range of 20mA - 30mA. Meaning
that anything outside this will blow up the LED. I tried looking
for LEDs that accept a wider range of currents, but I couldn't really
find anything greater than a 20mA range. To be clear, we are not sure
exactly what current the LED will experience, as that is dependent on
how poorly we plug in the connectors.

In the future, we could try consider using [this LED](https://www.digikey.ca/en/products/detail/cree-led/CLM2B-REW-CYAZ0AA3/2341882?_gl=1*1g2wsc8*_up*MQ..*_gs*MQ..&gclid=Cj0KCQjwmunNBhDbARIsAOndKpmVOMMjcApvRskGDgWubaplqefIKC0yoKlArk4fcRw5BtawdBZTDzMaAuL_EALw_wcB&gclsrc=aw.ds&gbraid=0AAAAADrbLlir8c3dIIgsyq1p-j1sNEIKb)
which I think has the same footprint. It takes 50mA - 70mA of input
current. I think it would still produce some light below
50mA.

CC: @Krish D @Aarjav Jain

> **Aarjav Jain** (3d)
>
> @Hemat Wander

> **Hemat Wander** (2d)
>
> -
> Again, I couldn't find where it said it was an issue. However, I think
> it is an issue because the open wire checks uses 2 neighboring
> voltage taps (say C11 and C12) to push and pull current
> respectively, to determine if one of the lines is not connected.
> 
> -
> If we increase the series resistance, than it will be harder (or maybe
> impossible) to light up the LED with a lower reverse voltage being
> applied. Depending on how incorrectly we connect the voltage connectors,
> we could have a reverse voltage ranging from 8V to 100V+ (etc.)
> Reasonably, the largest voltage drop we would see is like ~35V
> though.

> **Aarjav Jain** (2d)
>
> @Hemat Wander:
> I see. Consider harness length as a factor for how badly we could
> actually plug in connectors. Use that to guide the resistance value.
> Then avoid the overcurrent situation.

---

# Untitled

**Author:** Hemat Wander

**Date:** 3d

Continuing Checking Slave board + Other Related Tasks:

Kind of interesting change:

It
turns out that this circuitry for reverse voltage protecting the LEDs
doesn't work. Normally, these diodes would be supplied with 4.2V in
reverse, meaning that the LED would be taking 2.6V-4.2V of reverse
voltage.

The LED datasheet says that it normally can
withstand 12V of reverse voltage, meaning that we would normally be
safe, however, if we plug in the wrong connector such that we exceed
12V, the LED will break (In some way, I'm not sure exactly what).

![](../../images/image_2836714318.png)

*As a side note: *The
reason I thought this circuitry would work before, was that the diode
before the LED would block the voltage from passing. However, as a
general principle, the order of series components doesn't matter, as all
you care about is that the current going through them is the same. In
this case, both the diode and LED and diode would experience some split
of the voltage depending on their exact bias curves.

![](../../images/image_2836854381.png)

As
this circuitry is non critical, we can either keep it as it is, or if
we want to avoid the chance of the LED breaking, I'm not entirely sure
what voltage at which this would occur. **To be clear, the problem
statement here is non-critical, meaning we can just leave the circuitry
as is. The diode would protect the cells from anything bad happening
nominally. I also acknowledge that procedural changes to stop plugging
in connectors incorrectly is another solution. **

To
fix this issue, we brainstormed a couple of options, most of which
wouldn't work. We got all of BMS + some of BTM to help brainstorm this
relatively harmless issue(fun stuff):

- One solution @Deev Shah
suggested was using different connectors to avoid needing to idiot
proof all togeather, but I want to avoid using a variety of connectors
for ease of harnessing, + if we have space for these components this
circuity is a somewhat elegant solution in my mind.

-
A common solution you will see online is this one, used to bypass the
LED in the reverse direction. The only issue with this is that the high
quiescent current draw, as this will always be active.

![](../../images/image_2836856781.png)

-
I tried to create this circuit, which uses the 6.8V Zener's we already
had, to make it so there is no quiescent current draw during normal
operation, however this will likely bypass the LED with a lower voltage
drop, meaning that the LED might not have enough of a forward voltage
drop to turn on. ([Zener](https://www.digikey.ca/en/products/detail/diodes-incorporated/BZT52C6V8-7-F/814850)forward voltage is much lower than LED's voltage). This might still be an option, but its riskier.

![](../../images/image_2836877809.png)

-
Another idea was something like the following, where we use a PFET to
protect against the wrong direction voltage. Using a PFET in this case
doesn't work when V15 - V14 > 20V, as we will exceed the VGS of the
PFETs we use (PJAs). *Note the PFET technically is in the wrong place here, but the ideas still applies. *

![](../../images/image_2836798426.png)

-
Then, I found this solution, which I was very convinced would work.
This solution uses an NFET instead of a PFET to get rid of the large
drain source voltage issue. I thought we just need an NFET to withstand
100V drain-to-source. [This was the cheapest one I found on digikey](https://www.digikey.com/en/products/detail/diodes-incorporated/BSS123-7-F/717722).

![](../../images/image_2836907590.png)

The
main issue with this circuit is that it doesn't work. Once again, its
important to note that NFETs do not act like perfect switches, and in
their off state, the would basically once again act like the diode from
the circuit we had originally (meaning the reverse current would travel
through the PFET and cause a reverse voltage across the LED). I confirm
this with the LTspice simulation below, where I got a higher reverse
voltage drop over the LED than the NFET.

![](../../images/image_2836957926.png)

- @Christopher Kalitin
Came up with the following solution, where the  LED is protected from
reverse voltage using a 100 ohm bypass resistor. I think this would work
with any arbitrarily large sized resistor up to a reasonable extent
(ex. 100k).

![](../../images/image_2836913807.png)

-
This is similar to Chris K's idea but uses a diode in reverse instead
to make it so the voltage drop over the LED is capped with a logarithmic
current-voltage relation as opposed to linear.

![](../../images/image_2836930388.png)

I'm
most confident in this solution, and thus I will use it, despite it
adding 8 components per board. I think this is worth it.

*Side Note: *

Analog device article related to [reverse voltage protection on modules](https://www.analog.com/en/resources/design-notes/reversecurrent-circuitry-protection.html)

*Side Note #2: *

It's
obvious we've gotten to the point where there are a lot a lot of
components on the slave boards. Do we actually need most of these
components, probably not. For example, we could just not have this
circuitry, the ESD protection, the buck 0.1 ohm resistor, autoconnection
circuitry etc. I think having all of these things though, at the cost
of more components and more boards space is worth is given us wanting
the slave boards to be very robust and preventative against failure
modes.

I acknowledge the risks this adds in terms of more
components means more possible failure points, however I think thorough
testing will eliminate most of the problems we could see in that regard.
However, I agree there is a point where you are going overboard, so let
me know your thoughts. @Aarjav Jain @Krish D ?

-
Originally the stitching vias Altium's tool was creating were untented,
so I had to add this custom query type rule to make them tented.

![](../../images/image_2835493934.png)

Buck Converter:

-
For future reference, the buck I chose was purely for the sake of using
something we know already works. However there are other options
available:
[Adjustable output bucks with Vin(max) > 70V](https://www.digikey.ca/en/products/filter/power-management-pmic/voltage-regulators-dc-dc-switching-regulators/739?s=N4IgjCBcoKwOwGYqgMZQGYEMA2BnApgDQgD2UA2iAExwAcYtAbCMTQCxhgAML1cMjRjF41atGBFa04jBHF4IuVRnV6MAnIyrrecMAjZJidTTuK02VWmZDq2-Wr25cVk8Gy4XHrKmBhKRNiDBEABdYgAHABcoEABlKIAnAEsAOwBzEABfHKA)

[Bucks with 5V output and Vin(max) > 70V](https://www.digikey.ca/en/products/filter/power-management-pmic/voltage-regulators-dc-dc-switching-regulators/739?s=N4IgjCBcoKwOwGYqgMZQGYEMA2BnApgDQgD2UA2iAExwAcYtAbCMTQCxhgAML1cMjRjF41atGBFa04jBHF4IuVRnV6MAnIyrrecMAjZJidTTuK02VWmZDq2-Wr25cVk8Gy4XHrKmBhKRNiDBEABdYgAHABcoEABlKIAnAEsAOwBzEABfYjA4OB1oEDRILDwiUgpqNnU8iHCQaNiElIzsrKygA)

- I recalculated the buck convert values, and tried to show my work better. @Aarjav Jain
We could go with a 47uF input capacitance (meaning we would need an
alum electrolytic capacitor) however this would delay ordering due to
the size requirement of an alum capacitor, so in our case I think its
battery to go with a smaller ceramic capacitor, which we know from the
past should work. However, I do acknowledge this as an oversight and a
mistake to not include this previously.
(*side note: *I'm not sure if it would have fit vertically speaking)

![](../../images/image_2836669206.png)

- Added pull down resistors for TSEL lines

![](../../images/image_2835796693.png)

-
I reverted the isoSPI back to what it was to optimize for the length of
the paths being the same (< 1ps difference) at the cost of the lines
crossing over one another. Thoughts @Aarjav Jain @Krish D

![](../../images/image_2836669437.png)

BOM:

I created the [BOM](https://docs.google.com/spreadsheets/d/1gjwd6gVp0YLvQOgfCEXVmLvrNoSlmJ6GhuLY-SNHFA8/edit?gid=768663024#gid=768663024).

- I used this [TVS diode](https://www.digikey.ca/en/products/detail/diodes-incorporated/D5V0L1B2WS-7/2918767) for the buck output, as the one listed there is out of stock now

- I calculated around a raw $267 total, $134 per board

- There is $40 of fusing I think I can reduce. Along with some other things.

- I'm still missing adding the male connectors.

Other notes

- It turns out the 6.8V Zener diodes we were [previously using](https://www.digikey.com/en/products/detail/onsemi/MM3Z6V8ST1G/661898) are running out of stock, so I decided to switch them to the [BZT52C6V8-7-F](https://www.digikey.ca/en/products/detail/diodes-incorporated/BZT52C6V8-7-F/814850). This required importing and creating the layout for a slightly longer footprint.

![](../../images/image_2836727851.png)

- Changed resistor divider values from 100k to match that from [previous simulation work](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4941068621).

![](../../images/image_2837071003.png)

- Changed Diode Pad Width

![](../../images/image_2837243705.png)

- I also tried adding text in the middle of the connector names, but I think its getting messy if I do that, so I won't

![](../../images/image_2837258514.png)

CC: @Krish D @Aarjav Jain

> **Aarjav Jain** (3d)
>
> @Hemat Wander:

> **Hemat Wander** (2d)
>
> @Aarjav Jain
> 
> - I have now made the stitching vias untended, did you mean all the vias?
> - I have made a note for the capacitor
> -
> For the isoSPi, good point. I assumed that having the
> isoSPI lines not cross over each other meant that it would be **impossible** to match them to the same time difference. I now have this new routing.
> 
> ![](../../images/image_2842583041.png)
> 
> - Sounds good will update today!

> **Aarjav Jain** (2d)
>
> @Hemat Wander

---

# Untitled

**Author:** Hemat Wander

**Date:** 7d

Continuing layout + Routing based on DR2 feedback

As the last [chunk of work](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4999735636) I did for this was kind of a blur. I want to re-evaluate some of the layout and positioning.

**Buck converter:
**The
requirements for this layout was that the components circled below (2
capacitors and the rectifier diode) had to be placed as close as
possible to the buck IC. Also, the inductor has to be far enough from
the center of the board such that it doesn't interfere mechanically with
slaveboard #2's isoSPI harness. With this in mind, the layout below
makes sense, and we are able to move it down a little if needed

![](../../images/image_2824861584.png)

I cleaned it up a bit to fit into the box as shown below:

![](../../images/image_2824898803.png)

Scrutineering Circuitry:
For
these components, there is no mechanical constraint as the solid state
relays, connector and other scrutineering specific components will not
be needed on slave board #1. Thus, the goal here to place the components
in a sensical way to reduce routing complexity and length for the sake
of shortening lines to reduce noise coupling. Another consideration is
to have the scrutineering test points relatively far from the T_read
lines and the buck converter lines to prevent accidental shorting
during testing.

![](../../images/image_2824942706.png)

I changed the scrutineering connector to be a mirrored version of the B+ footprint, that way we connect a harness easily.

![](../../images/image_2829110534.png)

I
created the following layout, allowing us to easily determine the
scrutineering components required for board #2 and the connections we
can instead use on board #1.

![](../../images/image_2829116293.png)

Schematic addition:
I also
added these bypass 0 ohm resistors for slaveboard #1, which will not
have any of the scrutineering related circuitry (connector, solid state
relays, etc.)

![](../../images/image_2825200233.png)

Debug LED:
I changed the debug LED to be closer to the middle so it is visible through the clear panel.

![](../../images/image_2829128425.png)

Temperature Circuitry + Protection Diode Routing:
The
last thing to finalize the component placement of are these components
between the connectors. Currently they are placed rather
haphazardly.

![](../../images/image_2829128697.png)

Rerouting IsoSPI:
I
decided to reroute the isoSPI line as originally I had this little
cross over section for the common mode. I'm honestly not entirely sure
if this is a bad thing in this case, as it is crossing over a line which
is indirectly connected to the same line through the termination
resistors. However, I found a topology in which we don't need to do
this.

![](../../images/image_2829559584.png)

I
changed it to the following to optimize for having no lines crossing
over one another, at the cost of more bending of the traces and a 4ps
time difference in the differential lines positive and negative.

![](../../images/image_2829562352.png)

@Krish D @Aarjav Jain Please let me know your guys thoughts about this.

I'm
honestly not sure what to do about this routing exactly, as I've heard
that having the return path as closeby as possible is what should be
optimized, but I've also heard that having bends is very bad and should
be avoided at all costs, and I'm not sure how lines crossing over
another another plays into all of this.

To be clear, I know each of these things is bad, but I don't know what is worse.

Currently
I'm looking through these resources to try and see what to do next, but
this is not a big deal and can be changed quickly.
[General Differential Pair Video](https://www.youtube.com/watch?v=Orgi06uotu4)

[Differential Crosstalk article](https://resources.altium.com/p/differential-crosstalk-and-spacing-between-differential-pairs)

[Coplanar routing differential pairs](https://www.youtube.com/watch?v=1LI-ZQaCZrA)

[Mode Conversion](https://resources.altium.com/p/guide-mode-conversion-its-causes-and-solutions)

Other changes:
-
I decided to change the PFETs to the PJAs as I've been kind of
shifting around for a long time. The reason for this is kind of
singular, to improve the chances of success and robustness of the slave
boards at the cost of accuracy of readings during balancing. To this end
I will NOT be populating the parallel 100k resistors unless necessary.
This decision will be justified in the design doc as well.

![](../../images/image_2829457684.png)

To
do so I needed to import the PJAs which didn't have a footprint,
so I needed to take the 2N7002-TP Altium footprint and then morph
it into the PJAs PFET footprint.

- I changed the NFETs to the new standard [NTR4003NT1G](https://www.digikey.ca/en/products/detail/onsemi/NTR4003NT1G/1793060)

- Added a pull up resistor footprint for SPI on the SDO line as shown in this diagram of the datasheet.

![](../../images/image_2829315668.png)

-
Aarjav noticed that the transformer in the schematic was reversed from
the diagram in the datasheet. The choke should be facing towards the
transformer. I have now rectified this in the schematic.

![](../../images/image_2829317364.png)

![](../../images/image_2829318255.png)

-
Removed the DNP capacitors, as they are just creating big stubs in the
circuit for no benefit. I realize the other capacitors are also forming
similar stubs, but we **know **those are going to
be populated for sure. I think its better to just delete these stubs to
avoid these lines serving as antennas.

![](../../images/image_2829555704.png)

- Added mating connector 3D models to the Altium connectors

The (

) for the module-board to slave board and

The (

) for the scrutineering connector.

- I added silkscreen labels for idiot proofing isoSPI connectors.

![](../../images/image_2829565024.png)

- made vias have thermal reliefs

![](../../images/image_2829569411.png)

- added tear drops for all nets

![](../../images/image_2829569683.png)

- Added return vias for the autoconnection circuitry nets

![](../../images/image_2829572282.png)

- Added return vias for the voltage measurements

![](../../images/image_2829573578.png)

-
both of the above benefit from return vias because the transient of the
autoconnection circuitry occurs very fast, and so we need a good return
path to have a proper curve. For the voltage measurements, a good
return path its good for better ADC measurements, and better shielding
from noise.

- Added stitching vias every 5mm to join the GND planes together.

![](../../images/image_2829574120.png)

- Reading up on differential pair resources to find the optimal way to route isoSPI (this is not a priority)

- Recomputing buck converter values -> this should only affect the component values not the routing / layout.

-
I'm considering filling the top and bottom layers with polygons, as
they currently only have traces, however I'm weighing the pros and cons
of doing so, as it might lead to more noise coupling, but on the other
hand could create a closer return path for the analog lines.

let me know your thoughts.

> **Aarjav Jain** (5d)
>
> @Hemat Wande: TL:DR Just small questions. No major concerns. Please read still.
> 
> Otherwise looks good!

> **Hemat Wander** (4d)
>
> @Aarjav Jain
> 
> 1.
> I
> was already using the differential routing tool, do you think I should
> revert the isoSPI routing to what it already was? (I.e the isoSPI
> crosses over itself)
> 
> 2.
> The capacitors might be helpful
> for filtering, but the cost is that they create a stub antennae, what
> are your thoughts on this.

> **Aarjav Jain** (3d)
>
> @Hemat Wander:
> I am skeptical that the antenna like behavior offsets the benefit of
> the filtering. What does the application notes say about the filtering? I
> would say we should add the filtering, test by probing iso spi, and we
> can cut the trace later if we want to test without.
> 
> I
> would use the routing tool and make slight adjustments. Im not
> sure if Altium can accurately calculate the impact of switching layers
> and output that as picosecond difference.

---

# Untitled

**Author:** Hemat Wander

**Date:** 10d

Continuing Routing the Changes from the DR2:
To
make room for the LEDs, when I was routing the buck circuitry, I
realized it might be possible to squish the SMD components together to
make more space.

Before:

<img src="../../images/image_2819144410.png" width="223" height="635">

After:

![](../../images/image_2819154589.png)

Why I would do this:
- Makes room for the reverse connection LEDs without having to resort to 0603 components
- Might even look slightly cleaner
- keeps ADC lines slightly smaller

Any issues:
- No longer any space for the resistance values (not required)
- Silkscreen is kind of squished (not a big issue)

Note:
You
might notice that the silkscreen test is to the left of some
components and to the right of others. This is purely for density so the
text for the components don't overlap with each other.

**I decided not to use the above purely ****because its not a requirement (MVP) and I need to get the other stuff done. **

Changing Connector
Another
decision I decided to make was going down to 6-pos connectors. and this
is purely so we have more space to add the extra components. The only
downside is that we have no backup if the 0 ohm resistor on the module
board doesn't work, however it should work.

![](../../images/image_2819199692.png)

Then, I needed to decide how to place the temperature components + reversing LED. The options were either to
(1) place them between connectors
(2)
have all the connectors together the middle and then place the
components off to the left and right side (like it was
previously).

Or some combination of both. An example of what this could look like is shown below. (I didn't end up going with this).

![](../../images/image_2819268754.png)

Benefits
of (1) is that the routing is in theory simpler as the connector is
more directly closer to the components it is being connected to. It
also makes it easier to separate the modules wires to possibly make it
look cleaner and

The only issue is that the fuse will be a little more difficult to access.

I decided to go with this option for the reasons above.

> **Aarjav Jain** (10d)
>
> @Hemat Wander: What
> is the contingency plan for "The only downside is that we have no
> backup if the 0 ohm resistor on the module board doesn't work, however
> it should work."?

> **Hemat Wander** (7d)
>
> @Aarjav Jain I'm
> not quite sure what you mean. The purpose of adding the 0 ohm resistor
> on the module board was so that we only needed to have 3 wires going
> from each module board to the slave board. Thus, we are just continuing
> with that, as opposed to extra line for GND I had before.
> 
> Does that make sense?

---

# Untitled

**Author:** Hemat Wander

**Date:** 12d

@Krish D @Aarjav Jain
Routing Changes from the DR2:
This update is about the changes I made from the [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4990074680).
It's starting to look like we won't be able to include all of the
components on the board. The option we have is to make all of the
components smaller (such as using 0603 components).

![](../../images/image_2811882800.png)

**Routing the buck converter circuitry:
**To route this section I relied on this snippet from [the datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max5033.pdf)

![](../../images/image_2814514089.png)

We need to:
- Connect the shottky, input capacitor, and output capacitor GNDs to the same point
- Place the rectifier, BST and VD capacitors very close to the device
- Minimize lead length

To
achieve this I layed the components out like this, ensure that the
points above were met as much as possible while also having no test
points or inductor where it would interfere with the isoSPI connector
(as shown below).

![](../../images/image_2814829797.png)

Other notes:
- I'm also looking into tightening the SMD components on the board as follows, to make space for the components we have added.

> **Aarjav Jain** (12d)
>
> @Hemat Wander:
> Go down to 0603 where needed. I would start to do this for
> components we have to buy anyways (Ex: resistors we already have in
> 0805). What about adding ~5mm to the board length.

---

# Untitled

**Author:** Hemat Wander

**Date:** 12d

@Krish D @Aarjav Jain
Revising slaveboard from the DR2 meeting:
This update discusses some of the changes we decided to make from the [previous DR2 meeting](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.rc773p16rt3p).

Is isoSPI high speed? Should we consider adding additional protections / contingencies:
I found this [source](https://www.picotech.com/library/knowledge-bases/oscilloscopes/isospi-serial-protocol-decoding) for isoSPI, and this [source](https://www.analog.com/en/resources/technical-articles/low-cost-isospi-coupling-circuitry-for-high-voltage-high-capacity-battery-systems.html), and this [source](https://www.analog.com/en/resources/technical-articles/isolated-spi-communication-made-easy.html).
From these sources, I learned that we should use CAT5 cable, which has a
characteristic impedance of 100 ohms, to thus match the termination
resistance we choose. Choosing this cabling gives me me more confidence
in our isoSPI line. After doing some reasearch, an alternative common
connector would be the RJ45's (ethernet cables) as used on this LTC6820 [isoSPI demo board](https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/dc1941d.html#eb-relatedhardware).
My conclusion is that connector shouldn't really matter as much as the
characteristic impedance will be defined by the cable not the connector.
Also note, that this demo board has a **very strange**
isoSPI transformer schematic, so in future revisions we could try
testing out this sort of circuitry if we wanted. I think this is
overcomplicating it for now.

The ADBMS1818 datasheet also suggests using CAT5 cable, but doesn't seem to say anything specific about a connector.

I also found this [DC2350B demo board](https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/dc2350b.html#eb-overview) for the LTC6813. They use the [dlw43sh101xk2l](https://www.digikey.ca/en/products/detail/murata-electronics/DLW43SH101XK2L/2590159) common mode chokes and and the [ESMIT-4180](https://www.digikey.ca/en/products/detail/sumida-america-inc/ESMIT-4180-A/5043834)
transformers. We could consider using these if needed in the future,
but I don't think we should follow the actual ADBMS1818 and LTC6813
application notes for now. They also us 100pF capacitors from each line
to GND, which we don't do, but we instead have a capacitor connected to
the transformer center tap which should have a similar effect.

Finally, I found this [DC2792B](https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/dc2792b.html#eb-overview) demo board, which includes this [MMBZ10VAL](https://www.digikey.ca/en/products/detail/nexperia-usa-inc/MMBZ10VAL-QR/17296054),
ESD protection diode setup for lines like this. We can consider adding
something similar (this specific part is out of stock on Digi key).
Interestingly all of these boards seem to have a slit under their
transformer, although I'm not sure why they would do this.

![](../../images/image_2811493419.png)

Routing of LTC6813 demo board:

![](../../images/image_2811492476.png)

Routing of the LTC6820 demo board:

![](../../images/image_2811494557.png)

![](../../images/image_2811493536.png)

![](../../images/image_2811493988.png)

Based on these things, I added the option to include the following TVS diode, however we don't need to include these. [MMBZ10VA-TR](https://www.digikey.ca/en/products/detail/nexperia-usa-inc/MMBZ10VA-TR/21528690?_gl=1*1ogv363*_up*MQ..*_gs*MQ..&gclid=Cj0KCQiA2bTNBhDjARIsAK89wlE9HxZhZEcaU-dKHsM5QtNMUyHg8NzDG7sWZjCXVHCdSAbooTwZNDwaAplOEALw_wcB&gclsrc=aw.ds&gbraid=0AAAAADrbLlhmpApqA1Gu89dptes1ASZp6) (which is somewhat similar to the other TVS diode). I have kept my isoSPI routing the same for now. @Krish D @Michael Lin What do you think?

Temperature Multiplexer Pathway: (@Gurman Khella  read this section)

-
I replaced the t_sense 1k resistors with fuses such that we will have
fuses that break rather than simple current limiting. The failure mode
for these fuses should be easily detectable.

![](../../images/image_2811580180.png)

Other
than that, we discuss in the DR2 if the GND for the multiplexer needs
to be fused. From the reasoning explained below, I decided not to do
this.

![](../../images/image_2811586429.png)

Lets
take a step back for what we are protecting against. The module boards
are being Fed 3 lines (except module 1 and 17 which also have an
additional GND, we can ignore this GND because if that GND shorts we are
screwed anyways). Now there are 3 **black-box **cases of
shorts that can happen, either the B+ and GND short, the B+ and T_sense
short, or the T_sense and GND short. The latter case doesn't matter, as
it will just set the T_sense line voltage to be GND.

If the B+
and GND shorts, we will blow the GND fuse on the slave board. Then, the
voltage on the GND of the thermistor on the module boards will be equal
to B+'s voltage (65V in the worst case). The thermistor, will thus have
65V on its GND side, meaning the T_sense line will form the voltage
divider between the now B+(65V) and VREF2(3V). This will only cause 3mA
to flow, and for T_sense to be ~30V. Although there won't be any
overcurrent directly here, this 30V will break the multiplexers max
input voltage of VREG (5V), meaning the multiplexer will somehow break.
We can't really predict how this would happen, but worst case the
multiplexer shorts internally. In this case you would have 60V across
the thermistor, which would lead to 6mA flowing. This should again
should be non-catastrophic, we just have to make sure to fix any
thermistor issues as soon as we see them.

![](../../images/image_2811589464.png)

In
the other case, B+ will short to T_sense, meaning T_sense will directly
be pulled up to 65V in the worst case. This would break the temperature
readings, and also the multiplexer. From there, its not exactly certain
what would happen, but again in the worst case the multiplexer will
short internally, meaning we will have 65V shorting directly to GND.
meaning we again need a fuse on the line. Which we added. From there, we
will have 65V being shorted to VREF2 or VREF3, meaning we will have
~10mA traveling from T_sense into these lines. From a quick search it
seems fusing on the order of mA would be very expensive, so I will not
add these. We will just have to be serious about fixing temperature
reading issues when they arise, I [made a doc](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.tsn7eeeutawb) I will fill out to make sure we do this.

The
worst worst worst case is the multiplexer somehow shorts through the
ADBMS1818, but we currently have resistors between them + we have all
the fusing shown above, so even this case shouldn't be catastrophic.

What else could the spare GPIO #9 be for?
Previously,
I discussed using the spare GPIO #9 as a debug LED. But I thought it
might be worth considering other possible options for its use.

![](../../images/image_2811598216.png)

The
other main idea that came up was to somehow use this GPIO as an
auxiliary sense line for detecting something we might want to have
information about. For example, being able to detect if a fuse breaks.
-
It doesn't make sense to put it on the GND fused line, as that line is
directly connected to the module boards, and is fused for a reason
-
We could connect it to the IBIAS ICMP line in order to have an analog
reading of the voltage across them (that way we always know what the
threshold voltage we chose was).

- I could connect it to VREG to
see what the exact voltage of VREG is. Although, I don't know if this
will work because VREG is the thing powering the ADC reference.

None of these seem particularly promising, so I will leave this, unless you guys think there are any ideas: @Krish D @Aarjav Jain .

Multiplexing the scrutineering Temperature Sensor:
In
the DR2, we realized that the Tspare line being connected to a seperate
GPIO, probably wouldn't make sense philosophically for scrutineering,
and based on [Dan's last email response, he would probably agree](https://mail.google.com/mail/u/2/?ogbl#inbox/FMfcgzQcpnJldNxDcGrHMcFCkDpQHFTk).
Conclusion from that email is that we are going to be sticking with
multiplexing the voltage into C_17 as opposed to onto C_18.

For
the temperature line, we want to do something similar by having a
multiplexer for the 16th T_sense line, which either connects to the
scrutineering module or the internal module. I found [this 2:1 multiplexer](https://www.digikey.ca/en/products/detail/texas-instruments/SN74LVC1G3157DCKR/562895?_gl=1*z6lns4*_up*MQ..*_gs*MQ..&gclid=Cj0KCQiA2bTNBhDjARIsAK89wlH9zUPz1Z_YLhSQnrsj95bCDbPpPM46RZNtTtQdU-wa82sBzCTH1a0aAhhXEALw_wcB&gclsrc=aw.ds&gbraid=0AAAAADrbLlj3vtiLysXjYEatfPgsuKBJR)
on Digi key which seems to work for this application. The only concern
is if I should include a decoupling capacitor for VCC, as there is
starting to be limited room on the board. I chose to add one.

Wait....
I'm getting flashbacks. I literally had this multiplexer at one point
for this exact purpose, but I deleted it for some reason. Likely because
I realized we had spare GPIOs I could use instead.

![](../../images/image_2811659514.png)

Anyways,
I added this multiplexer, and then fed the output into one of the main
4:1 temperature multiplexers. I found this source that seems to suggest
that cascading multiplexers like this is fine to do. [Cascading Analog Multiplexers](https://www.ti.com/lit/wp/slaa991/slaa991.pdf?ts=1773021216575&ref_url=https%253A%252F%252Fwww.google.com%252F)

![](../../images/image_2811675422.png)

![](../../images/image_2811676265.png)

Should we have RC filtering on the output of the temp multiplexers?
Currently
we have these RC filters on the output of our Tsense lines, and I want
to re-evaluate if we should include these. The general reason for
including these is so that we have some sort of filtering right before
our ADC reading (from the ADBMS1818), such that any noise picked up
between the initial filtering from the thermistor and neighboring 1uF
capacitor (such as from the multiplexing) is filtered out. This 100 ohm -
10nF combination is something directly mentioned in the ADBMS1818
datasheet.

![](../../images/image_2811679324.png)

After a quick search, [this article](https://www.analog.com/en/resources/analog-dialogue/articles/demystifying-data-acquisition-systems.html),
seems to show this configuration but with the addition of a buffering
op-amp. Thus, I will keep these capacitors. (In the future we can
consider adding a buffer for temp sensing, but it is not an MVP right
now). The only thing subject to change is the exact values, but those
can also be changed post ordering.

![](../../images/image_2811684627.png)

Revisiting output capacitor for the buck:
The [MAX5033](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX5033.pdf)
datasheet suggests using a capacitor at the output of the buck
converter, with a ESR between 100 and 250 milliohms to maximize
stability while keeping output ripple low. However, in the application
notes it then recommends using a tantalum capacitor, with an ESR of 1.1
ohms, which doesn't make sense. Thus, I will stick with the setup I have
with a ceramic capacitor

PLUS, I found [this article](https://www.ti.com/document-viewer/lit/html/SSZTBJ1)
that seems to also talk about using a series resistor for the output of
a linear regulator, and so it seems fine for me to do this. The article
also explains characterizing the frequency to determine this value, but
I don't think we need to do that (yet).

![](../../images/image_2811699502.png)

Idiot proofing the connectors

Thinking
about this, It isn't exactly clear what at what level to perform idiot
proofing on. There are two ways of going about this, either through a
hard barrier that makes it impossible to connect the wrong connector, or
by creating some indication for when the incorrect connector is plugged
in. When would we need to do this? Note that we already have some idiot
proofing through the combination of two modules into one connector.

I
should mention my bias, which is that I don't want to make the
connectors different from one another, as that would look uglier, and be
more annoying to bring up harnesses for.

**Why would we need idiot proofing?
**Lets
say we connect a connector in the wrong place. The most likely culprit I
can imagine (depending on how the wiring turns out) is that we swap two
neighboring connectors. Lets say we swapped module 9-10 with module
11-12. The temperature sensing is the same so it wouldn't matter. The
voltage lines of course though, are different. (Lets assume 4V for each
module).

![](../../images/image_2811717219.png)

At
the first stop, we would have the autoconnection circuitry. We would
have the following voltages in black, and assuming the resistance is
high enough to prevent loading, we would continue to have the following
autoconnection circuitry voltages. (black is the module voltages, and
red is the voltages of the resistor divider circuitry).

![](../../images/image_2811721520.png)

This
means that that module 9 would be activated as the PFET is pulled low,
leading to 44V being pushed to C9 while C8 is only 32V. This is a ~12V
difference which would be very bad for the ADBMS1818 (maybe not quite as
bad because of the 6.8V Zener?).

Simulating in LTspice with this situation, we get a similar result.

![](../../images/image_2811725698.png)

At
the end of the day, the only thing we are preventing against by idiot
proofing is the ADBMS1818, there ideally shouldn't be any catastrophic
issues with plugging in the wrong connector (@Krish D what do you think?)

**
Option #1:**
For
this option, we would need to make some of the connectors different
from one another so that it is impossible to plug the wrong connector
into the wrong place. This could vary from having two types of
connectors we alternate every connector, to making every connector
different. The latter option is so ridiculous, but its a question of, if
we have two different types of connectors, why wouldn't we have more?
Again, I don't like the idea of having multiple types of connectors, as
it makes it more difficult to make harnesses post bring up.

Looking at [other teams](https://docs.google.com/document/d/1Vwa5Mix4PpkgyanF9hwTsTV8wRXhdtk6z79yrlHPH5M/edit?tab=t.0), it seems that:
- UC Berkely uses all the same connectors on their slaveboards
- Midnight sun seems to use the same connectors (can't really tell)
- Stanford definitely seems to use the same connector

**Option #2:
**In this case, we would want some circuitry to either protect against or warn against accidentally swapping the connectors.

For
protecting against, we would need a way to make the PFET only turn on
if the voltages are below some max threshold. I'm not knolwedgeable
enough to figure out how to do this, and it seems like a lot of
overhead. MR. GPT says we could have some other bypass switch connected
to the PFET gate which pulls it up if above some voltage threshold, but
that seems like overcomplicating it unnecessarily. -> Something to
consider for future

For warning against, we would need some sort
of LED system for showing when the voltage difference between some
module is above some threshold. There are two options for indicating
this:

(1) [From some searching](https://electronics.stackexchange.com/questions/366658/use-leds-to-indicate-voltage), I found the idea for this voltage indicator circuitry that only requires 3 components.

![](../../images/image_2811798394.png)

In
our case, we need to indicate if the voltage is above some threshold
(the maximum each module can be is 4.2V, meaning that the difference in
voltage would never exceed this). If we swap around a connector by
accident, the voltage would be somewhere from 8V to 12V. We could thus
use the 6.8V Zener diodes we are already using.

(2). The other
option is to rely on the fact that voltage somewhere will get reversed
whenever we swap the connectors (in the example above V_10 is at a
higher voltage than V_11). Thus, we can use diodes facing in that
direction to indicate if the connectors are reversed. The only issue
with this is that LEDs have very poor reverse voltages on average (~5V).
This means, we will have to add another diode in series to deal with
the reverse voltages. We can use the same diodes we used for the
autoconnection circuitry.

I will go with option #2 as it seems
more reliable.  To implement this, we need to include this circuitry
consisting of 3 components between each connector in reverse fashion. I
will use the same red LEDs as are on the HVC.

If we needs to
have MAX 20mA, and the LED has a 2V drop, and the diode will have a
~0.7V drop during at 20mV. The reverse voltage we would see could vary
from 9V in the lowest case to like 20V if we skipped two connectors. In
the worst case, we would have 17V across the resistor, meaning we need a
resistance of ~820 ohms for 20mA in the worst case. This would produce
7mA in the 9V case.

![](../../images/image_2811843722.png)

In
conclusion I chose to go with this warning method, as it will tell us
to connect it in the correct order before the autoconnection circuitry
allows everything to pass.

Next Steps:
- Routing all of these changes
- Adding the mating connector 3D models to the Altium

Other notes:

-
Looking at the DNP capacitors on the other side of the isoSPI
transformer, the routing for them seems to become a big stub
essentially, so maybe we should not have this DNP component. @Michael Lin Where did you write down the purpose of this component again?

![](../../images/image_2811618635.png)

> **Aarjav Jain** (12d)
>
> @Hemat Wander:
> Super awesome update! Keep up the great technical detail as always.
> Your explanations and resource linking is very important to contributing
> to a team's success!

---

# Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** 13d

@Hemat Wander : In the rare case that the B- connection to the B+ module board 1 or 17 is lost then the GND of the SB is lost.

CC: @Gurman Khella @Krish D

> **Hemat Wander** (12d)
>
> @Aarjav Jain
> 1.
> All of the IC's would lose a GND meaning that they would no longer
> function, the exact failure mode for each IC would vary, but the most
> important one would of course be for the ADBMS1818, I think we would
> have to test to determine the effects of this.
> 
> 2. There are not
> explicitly, I think it would be difficult to add a protection mechanism,
> but we could add a warning mechanism of some kind. Once the warning
> occurred it would kind of be too late though.
> 
> Actually, as the
> autoconnection circuitry stands, no GND means this would be floating,
> meaning that the voltage taps should theoretically be isolated from the
> rest of the slave boards, meaning nothing could turn on. This should be
> fine?
> 
> ![](../../images/image_2811815145.png)

> **Aarjav Jain** (12d)
>
> @Hemat Wander
> 
> "meaning
> nothing could turn on." -> Could you elaborate a little more? What
> exactly happens when that connection is floating because the GND is
> lost? If the SB loses comms to MST while battery is on then we could get
> a 'SB COMMS LOST' fault which can be helpful.

---

# Untitled

**Author:** Hemat Wander

**Date:** 15d

I will make the changes mentioned in this [DR2](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.rc773p16rt3p) meeting, by EOD Sunday, March 8th.

---

# Untitled

**Author:** Hemat Wander

**Date:** 16d

Reworking Scrutineering Circuitry:
As from this [update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4977296354), we decided to change the scrutineering circuitry, to make it more **likely **to be possible to use during scrutineering.

I changed the scrutineering topology from looking like this:

![](../../images/image_2807029985.png)

to looking like this:

![](../../images/image_2806467586.png)

For
routing these changes I decided to move these components for the
filtering of module 16s voltage to past the solid state relay.

![](../../images/image_2807031594.png)

This
should give us room to move around buck circuitry as suggested to
make the test points not be so close together. (Safety hazard as they
have a >55V difference at max).

CC:

---

# Untitled

**Author:** Hemat Wander

**Date:** 17d

Debug LED:
I
realize I never made an update on this, but essentially we can use the
spare GPIO #9 for a debug LED, that the masterboard can flash on and
off. Benefit is that we can directly see if isoSPI is working. This
slightly differs from the WDT LED which will always be on if some signal
(possibly invalid) was sent through the isoSPI line. This direrctly
shows us if the isoSPI is working enough to turn on and off the GPIO.
CC: @Michael Lin @Krish D

![](../../images/image_2801607137.png)

Alternatives:
We can set the GPIOs to be seperate to power each SSD seperately. Although I don't know why we would ever need to do this.

![](../../images/image_2801608108.png)

---

# Untitled

**Author:** Hemat Wander

**Date:** 17d

Slave board - Module board Connectors:
After doing a [quick search](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.8u1s39bb89yk),
it seems that 8-pos R/A connectors are cheaper than 6-pos R/A
connectors, meaning I might as well use 8-pos connectors on the slave
boards since they are as big as they are anyways. Thus, on the cell
board we probably no longer need to use the 0 ohm resistor as we can
just connect the ground connection directly to the connector using one
of the spare pins. **However**, we can still use the 0 ohm resistor as well, if we like that solution better.

@Gurman Khella @Krish D

![](../../images/image_2801515443.png)

> **Aarjav Jain** (17d)
>
> @Hemat Wander:
> For connectors like this, price and availability is no problem since we
> can order many many samples. However, it is important that they do not
> occupy significant space. Looking at your board, it are not taking up
> extra space in that there are empty areas of your PCB so that is good.
> 
> Can you explain the exact circuitry changes on the module boards if we go with 8pos? CC: @Gurman Khella
> 
> Additionally, based on your experience should it be 6pos or 8pos (consider how the wiring changes for the MB to SB harness).

> **Gurman Khella** (17d)
>
> We used the 0 ohm resistor in the first place because then we only need
> 3 wires coming from the moduleboard to slaveboard. Initially we had
> started with 4 pins: B-, GND, B+, Tsense; then we simplified using 0ohm
> resistor so we only need the GND pin on the connector and not the B-
> pin. Since we only need B- for the 1st and 17th modules to get GND. This
> got rid of additional wires going between boards and is a simple way to
> have the connection on the moduleboards. Are you suggesting we revert
> to using the 4th pin on the moduleboard?
> 
> I don’t see the point of
> having an extra pin being used and another wire going between boards.
> We have the option to use the extra pin, but I think there are more
> failure points in using the extra pin, than the 0 ohm resistor. It is
> simpler to just have the connection on the moduleboard so all modules
> have 3 wires going between slaveboard and moduleboard for consistency. I
> would like to stick with the 0 ohm resistor, but if there is something I
> am not considering, let me know.

> **Gurman Khella** (17d)
>
> Decision on my part if you decide to use 8pos. We will stick with the 0
> Ohm resistors. I will add a trace from the extra pin on the
> moduleboards to B-, so we have the option to use the wire to make the
> connection between B- to GND on slaveboard side if needed.

---

# Untitled

**Author:** Hemat Wander

**Date:** 17d

Slave board Scrutineering Circuitry:I
In a discussion with @Aarjav Jain
we realized that our current setup of the scrutineering circuitry might
not work for scrutineering because it uses a separate ADC input (C18)
in the chain compared to what the cells normally read (C1 - C17). If we
wanted to change this, we just need to make the solid state relay switch
to C_17 instead of C_18, doing so would require making the changes seen
in the diagram below. Essentially, getting rid of R4.65 and the
capacitor and diode. Then adding a 68 ohm resistor to make C_17 and C_18
always connected to the same voltage. Making this change should likely
not be a big change?

![](../../images/image_2801403831.png)

![](../../images/image_2801408192.png)

My opinion:
Having the circuitry as we have it **right now**,
has one big advantage, where the voltage reading for module 32 can
normally be performed from C17, which provides a clean connection. If we
change the circuitry as proposed, we will now have to read module 32s
voltage through a solid state relay. I don't like this idea because:

1) The routing for the 32nd module reading will be longer and possibly pick up more noise
2)
I'm unsure about the effects of reading a voltage through a solid state
relay, for our normal cell readings. As there might be issues in terms
of noise or some constant offset. I couldn't find any resources online
about this, and I don't think it will be too big of an issue, given that
the [datasheet](https://www.littelfuse.com/assetdocs/littelfuse-integrated-circuits-lcc110-datasheet?assetguid=fef24721-9a57-4423-a6f7-7e12c72ec530)
says there is only pF of capacitance, and since the maximum resistance
is less than that of the 100 ohms needed by the filtering.

In hindsight it might have been a good idea to characterize the noise by testing the circuitry.

Next Steps:
Currently I have not changed the circuitry on the PCB. In waiting for [DAN to respond](https://mail.google.com/mail/u/2/?ogbl#inbox/FMfcgzQcpnJldNxDcGrHMcFCkDpQHFTk).
It seems like Steve at least agrees that the 33rd module solution is
slick (I think slick means good?). I'm not sure what "The only issue can
be that the pack response now is truly lost in the test of the BPS".

@Aarjav Jain
Followed up in the email chain about the idea to change from switching
on the 32nd module line. If we get a response that we should do
something like that I will change it to do so. Currently, I'm not
convinced that doing so is any philosophically better than switching on
the 33rd module line (given that we will have to change firmware either
way) and as we are still using the same BMS measurement chain.

![](../../images/image_2801437524.png)

CC: @Aarjav Jain @Krish D

*Note: *If
none of this works we could revert to a scrutineering version where we
solder 3 wires to these through hole pins and extend them out to the
control board, that way we can choose to enable what scrutineering
circuitry we are connected to with a hardware enable switch outside of
the pack (the idea behind this bypass is connecting a jumper cap to
connect either module 32 or our scrutineering circuitry). This idea can
just be extended to go out to the control board, where we can perform
the switching. The downside of the method is that we can't emulate the
behavior of the second solid state relay for only providing HV when we
need it.

![](../../images/image_2801440496.png)

![](../../images/image_2801444269.png)

> **Aarjav Jain** (17d)
>
> @Hemat Wander
> Thanks for the update. Will need to read it again to understand what
> exactly those 3 wires are doing. Perhaps you can elaborate more on that?
> 
> Regarding
> Steve's message -> I am confused about Slick because he also said
> "The only issue can be that the pack response now is truly lost in the
> test of the BPS." which I agree with. Although "pack" response is
> extreme to say. We will see when they respond.

> **Krish D** (17d)
>
> @Hemat Wander @Aarjav Jain
> 
> I
> think that this scrutineering circuitry should still be feasible, since
> it is still literally in the same chain. <- Although, this is just
> my interpretation, so we should wait until Dan responds.
> 
> @Hemat Wander How
> time consuming would it be to add this circuitry to LT Spice to see
> what reading a voltage through a SSR would do the output signal?
> 
> We aren't expecting the signal to fluctuate much or drawing  excessive current during ADC sampling **unless you are testing balancing**, so I can't imagine there would be many effects as a result of the additional resistance from the SSR.
> 
> I agree, lets wait until Dan responds, and if we have to change the circuitry, lets start with a simulation.
> 
> Regarding
> the 3 wire soldered connection, I'd be hesitant since this provides an
> non-isolated portion of the slaveboard directly exposed on the control
> board (same as you mentioned). If this is sufficiently covered, this may
> still be a feasible option, but we should talk about the exact
> procedure in more detail.

---

# Untitled

**Author:** Hemat Wander

**Date:** 18d

Cleaning up routing in Altium:
Previously,
I completed routing everything in Altium, however I found that the when
running the DRC there were 500+ errors present.

I'm suspicious that most of the errors don't really matter. The errors seem to be:

<img src="../../images/image_2783500319.png" width="632" height="316">

- SMD neck down constraints
This rule is about the ratio of a routed track and the SMD component it enters. I found this [forum](https://electronics.stackexchange.com/questions/218343/the-need-for-smd-neck-down-constraints)that
suggests having these neck down constraints is for the same purpose as
having thermal relief spokes, but also specifically. Although I'm not
entirely convinced this is necessary, this is a reasonable thing to
have, so I will adhere to this design constraint in the cases where I
was directly breaking it.

![](../../images/image_2783503523.png)

before:

![](../../images/image_2783504575.png)

after

![](../../images/image_2783526479.png)

*I did not apply this everywhere, only where the 100% neck down rule was strictly being violated. *

- Minimum allowable angular ring.
This
one I really am not convinced by because this is the generic via we
have set in the design rules (0.4mm hole, 0.8mm diameter), which is used
in plenty of other boards.

![](../../images/image_2783527266.png)

![](../../images/image_2783527642.png)

Again,
I found a forum that says the minimum angular ring constraint for JLC
is 0.13mm. This would make more sense with the generic via size we use.
After some searching around the [JLC capabilities website](https://jlcpcb.com/capabilities/Capabilities),
I found this requirement for the spacing. Given this minimum
constraint, us having 0.254 mm in the rules make some sense. however,
currently our annular rings are 0.25mm which is still above this minimum
requirement. Thus, in the rules I will set it to be 0.24mm, and for
vias to be excluded from the check.

![](../../images/image_2783544214.png)

*I
checked with some other boards including the DRD, and they all seemed
to have this same issue of angular rings smaller than 0.254mm. **So I think this should be fine. *

Minimum solder mask silver clearance:

I
found that the footprint for the temp multiplexers and other ICs had
some issues with the solder mask bridge (AKA the distance between pads
being too big). Essentially I spent a long time trying to figure out why
when I placed a component in the slave board project, it had a
different looking footprint, compared to if I placed it in the DRD or
HVC projects.
**
In slaveboard: **

![](../../images/image_2801327212.png)

\**

In HVC:**

![](../../images/image_2801327653.png)

It
turns out that there is a design rule that makes it so the footprints
can be different in different projects even if you are using the same
component. Thus, I changed the solder mask expansion for my PCB to match
the HVCs of 0.075mm. Note that [JLC](https://jlcpcb.com/capabilities/Capabilities), specifies a minimum solder mask expansion of 0mm. So this is fine.

Despite
changing that setting, there were still some components that broke the
minimum solder mask sliver rule. To solve this issue I did two things as
follows.

1. Set the rule to be at a minimum of 0.2mm instead of 0.254mm. I can do this because [JLC](https://jlcpcb.com/capabilities/Capabilities)only specifies a minimum 0.1mm solder mask bridge for 1oz PCBs (@Aarjav Jain
is this what we use?), and other boards like the HVC had 0 clearance
for this rule and were still able to print ICs with pads really close
together like their MCUs.

(Side note: Were there any issues
with the printing of either of these boards? I'm asking because they
seem to be breaking the solder mask sliver rule since the pads are
closer than the 0.1mm minimum set by [JLC](https://jlcpcb.com/capabilities/Capabilities)?. @Christopher Kalitin @Museok Seo). This [PCBway](https://www.pcbway.com/capabilities.html)page doesn't seem to say anything about this specific rule.

![](../../images/image_2801348845.png)

![](../../images/image_2801337177.png)

2.
For the multiplexer IC I decreased the pad widths greatly and then
decreases the solder mask expansion further to 0mil for this IC
specifically. (I can set it as low as 0 according to JLC + ICs on other
boards already do this). This caused the footprint to go from looking
like this:

![](../../images/image_2801323842.png)

to looking like this:

- Matched lengths (this seems to include nets that I do not care about matching the lengths of for some reason)

Notes on some other stuff I found:
Having a >0.45mm hole-hole clearance is not mentioned in the [wiki](https://wiki.ubcsolar.com/en/tutorials/altium.md), so I added this to my rules with a 0.5mm hole-hole clearance.

![](../../images/image_2783540940.png)

Other routing changes:
-
These 8 temperature sensing traces were previously crossing underneath
the buck converter circuitry (which is going to be very noisy due to
switching), so I decided to move them away from the switching circuitry.
However, there would be two ground planes between them, so this isn't
likely a huge issue.

![](../../images/image_2783627049.png)

Changing polygon pour positions:
I found this [article from AD](https://www.analog.com/en/resources/analog-dialogue/articles/staying-well-grounded.html)
that gives some information on the need for grounding in ADC lines (not
just high speed lines). I don't really have time to go through it in
depth right now, but it seems that we need to treat ADC lines the same
as high-speed analog lines. Based on this I decided to keep two fully
intact GND planes, and then route each of the VREF2 and VREG power nets
on the top layer.

CC: @Krish D

> **Aarjav Jain** (17d)
>
> @Hemat Wander:
> Why were the vias not made with >0.25mm in the first place?
> Where the DRC constraints you put in from the Wiki different?
> 
> Yes we use 1oz.
> 
> There have been no problems regarding silkscreen to pad in the previous boards.
> 
> ![](../../images/image_2801541685.png)
> 
> You missed a picture.
> 
> Why decrease pad width for multiplexor?
> 
> Could you add the pad hole to hole spacing to the Wiki as well? Good find!
> 
> I agree with the GND planes concept. @Museok Seo: Take a read of this update for  regarding DRC and routing ideas and let us know your thoughts as well!

> **Christopher Kalitin** (17d)
>
> @Hemat Wander
> 
> Haven't checked the silkscreen yet, will do that today.
> 
> Micheal and I imported [these design rules](https://github.com/ayberkozgur/jlcpcb-design-rules-stackups/blob/master/design-rules/altium/2layer-1oz.RUL) off for JLCPCB a Github repo, you could do the same to ensure nothing is missed.
> 
> These
> design rules will probably also solve your neck down issue. Also, why
> have larger traces on the inside? Why not make it all the lower width?
> 
> ![](../../images/image_2803093963.png)

> **Museok Seo** (15d)
>
> In
> the Wiki, I believe there isn't a specific section where you include
> the 0.254mm in the rules for DRC. I actually recall when working with
> the DRD, the vias that were placed were very large so I recall changing
> the via sizes to match the previous boards. (I didn't run into this
> issue last year).
> 
> ![](../../images/image_2809757136.png)
> 
> (Two VIA sizes)
> 
> I
> just checked the DRD for your Solder Mask Silver rule, I agree that the
> gap between solder mask openings are smaller than 0.1mm. However, the
> boards were still able to be printed as one large opening rather than
> multiple small openings I believe for the MCU pad. (I can check this in
> more detail on Saturday). I believe if you have a gap larger than 0.1mm,
> JLC will be able to create this bridge of solder masks which we
> currently don't have. I'm curious to see how it will look like for your
> multiplexer IC!
> 
> For the Pad Hole-to-Hole Spacing, you're correct
> with the distance required from holes > 0.45mm, however I believe the
> clearance constraint covers this as well (Prevents copper being too
> close to each other).
> 
> I'll look more into the GND-ing article
> that you have mentioned! It seems to have pretty good information that
> I'll be looking into about proper grounding methods for analog
> signals.
> 
> Out of curiosity, could you explain about the
> analog signals you have on your board? Currently on the DRD there are 2
> analog signals reading the pedal's voltages. I haven't got to testing
> the signals from the DRD yet, but I would like to hear the signals that
> you have on your board so I can implement this for the future revision
> of the DRD.

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 19

Final talks about the auto-connection circuitry (for real this time):
In a [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4907208613), we concluded that we are going to be moving forward with pre-charge circuitry **without **gate
capacitors. Another implicit decision I made was the remove the diodes
in series with resistors, simply because they were taking up extra space
and because they weren't strictly required. The purpose of these
resistors is to explicitly change the time-constant of each PFET so they
close one after another, however this **IS NOT **strictly
necessary (previously I thought it was necessary). The question I want
to evaluate today before I begin routing again is to finalize if these
resistors are required or not.

![](../../images/image_2772058505.png)

There are actually 2 parts to this:
1. Either having those series diode resistors or not.
2.
Changing the values of the resistor ladder to ensure all the PFET
gate-source voltages are at a similar level. (If we didn't do this, some
PFETs activation could vary in the level of entire volts, which could
drastically change how much current can pass through.

I went
through and simulated the 4 possible combinations of these two points.
These can be seen below. The first graph for each shows the gate-source
voltage of all 16 PFETs. The lower this voltage gets to during
activation, the more conductive the PFET becomes. The second graph shows
the charging up of the filtering capacitors right before the ASIC (as
we can see they charge up in order for graphs with a series resistor).

**Removing the series resistors + all ladder resistors are 100k ohms:**

![](../../images/image_2772065984.png)

![](../../images/image_2772075150.png)

**Removing series resistors + ****varied resistance of ladder (not 100ks):
**

![](../../images/image_2772084862.png)

![](../../images/image_2772089817.png)

**Having series resistors + and divider resistors are 100k ohms:
**

****Removing series resistors + ****varied resistance of ladder (not 100ks): **

****Side note:
**By
"varying" the resistances in the ladder, I mean changing the
values from strictly 100k to something else. I got these values by
solving a system of equations for the resistances we need to have equal
gate source voltages.

In the case of no series resistors I used:

100k, 100k, 100k, 100k, 105k, 105k, 105k, 107k, 107k, 110k, 110k, 113k, 113k, 117k, 117k, 117k

In the case of the series resistors I used:
100k, 100k, 103k, 103k, 105k, 105k, 107k, 107k, 107k, 110k, 110k,  107k, 107k, 103k, 107k, 169k**

Conclusion:**

We will (1) be including series resistors, and (2) having a varied series resistance ladder. This is because...

(1)
We see in general that having the series resistors improves the
stability of the charge-up with the filtering, making it so that each
module charges up one after another rather than all at once. This is a
strictly **MMR** feature, and should not affect our ability
to meet our requirements that much, however it provides us more
confidence that the ASIC will not be stressed by the ASICs possibly
varying in how quickly they each turn on. There are some nuances to
this, but it essentially gives us more configurability, as we could
"easily" replace these with 0 ohm resistors if we want to revert to an
earlier design. The only real cost is more space + components to bring
up.

(2) If we compare the PFET gate-source voltages with the
varied resistance ladder, and with all 100ks, we easily see that having
the varied resistance ladder allows for all the PFETs to be more
strongly over the gate-source voltage. This is more important if we ever
have to revert to a PFET like the [PJA3471_R1_00001](https://www.digikey.ca/en/products/detail/panjit-international-inc/PJA3471-R1-00001/14660016) with a high gate-source threshold voltage.

> **Aarjav Jain** (Feb 20)
>
> @Hemat Wander: When/why would we ever: "This is more important if we ever have to revert to a PFET like the [PJA3471_R1_00001](https://www.digikey.ca/en/products/detail/panjit-international-inc/PJA3471-R1-00001/14660016) with a high gate-source threshold voltage."

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 18

Continuing work to complete the Slaveboard V4 Design:

From the past few updates ([#](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4907208613)1 and [#2](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4914735837)),
we made some decisions on what circuitry we are going to keep for the
auto-connection circuitry, so the plan for today is to implement those
changes. Then, there are also a few other changes I need to add.

Auto-Connection Circuitry:

Added auto-connection circuitry alternative components. Also, I made a [subtab in the doc](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.qtg6jv4pf0iy) for information on implementing these alternative pathways.

![](../../images/image_2766168792.png)

Fusing on the GND side:

Currently,
we have all of our fusing in place on the 16 module connectors and for
the VREF input to the temperature circuitry, going to the slave boards.
We also have fusing for the GND of the first module connector, and for
the GND of the temperature circuitry. During the recent DR meeting,
Saman raised a point that the fusing for the GND side seems redundant
and could even be bad because.
1. You now have two places where a fuse could blow for a given short, meaning we have to check multiple places.
2.
If the GND fuse blows, that would lead to a floating GND, which could
be problematic for most ICs as they need their GND reference to be the
lowest voltage.

**Fusing GND: **
First lets
evaluate the temperature GND fuses, why did I consider having this in
the first place? My concern was that, since we are supplying an
"absolute GND" for the sake of temperature sensing to each module board,
we are creating this HV relation on every module board between the
module voltage and GND. Thus, if those two lines shorted then it would
lead to a lot of current surging from the module board through the slave
board to GND. (possible causes could be the thermistor leads contacting
the module voltage, or something small and conductive shorting the
exposed parts together, or degradation of the wires insulation causing
the conductive parts to rub together under the forces from the car
moving around).

TO BE CLEAR: The module fuses would not protect
against a short like this, as it would occur at the module boards and
then flow through the slave board GND wires.

![](../../images/image_2766578630.png)

Normally,
this net would have less than 3mA going through it, meaning this is
only really for protecting against catastrophic shorts far beyond the
nominal current draw. Thus, we shouldn't really ever expect this fuse to
blow or to need to replace it. However, if the fuse does blow, we
should only expect the temperature sensing nets to be pulled up to VREF2
(@Michael Lin
We can do something in firmware to account for this edge case), so this
shouldn't pose a problem for the MUX IC itself, as the MUX itself isn't
connected to that floating GND.

![](../../images/image_2766687903.png)

Conclusion:
We are going to keep this GND fuse, and I will move it to the center
for ease of distribution to each of the modules (as seen below).

<img src="../../images/image_2766692153.png" width="391" height="440">

**What about fusing the mux inputs? **

Based
on the above logic, we are also feeding the T_sense inputs to each
module board, which will be at nominal ~1.5V relative to GND, which
creates a HV difference in respect to the module voltages (which can be
up to ~70V relative to GND). If these two lines did short, it would
raise up the MUX inputs to the module voltages, thereby exceeding the
IC's limits. The IC then breaking could either lead to it just not
working, or it effectively shorting to GND. This logic is sound, however
it doesn't seem feasible to just add a fuse at every Mux input to
prevent against this.

Considering this dilemma, I found [this page](https://www.analog.com/en/resources/technical-articles/fault-protection-saves-multiplexers-switches-and-downstream-circuitry.html),
which among other things suggests adding series resistors with the
multiplexers to prevent against the worst of over-voltage shorts. This
is a good solution I think, and really the only problem is the lack of
space on the slave boards to include these series resistors. Also, I
will use 1k resistors, as they will only lead to 70V/1000 = 70mA of
current draw during a short, and also should have pretty good accuracy. I
will also place these resistors in the corners of the ADBMS1818, as
shown below.

![](../../images/image_2766843027.png)

Conclusion: Use 1k resistors in series with every temperature sensing input.

**Fusing the Absolute GND of the slave board?

**This
other fuse we had connected to the absolute GND of the slave boards
(from the first module board). This fuse was initially kept as a legacy
addition from the previous revision cell-boards which had a fuse at both
their B+ and B- connections.

![](../../images/image_2766851064.png)

However,
re-considering this now, I don't really see a case in which we would
need this fuse, as we already have GND side fusing for the temperature
circuitry, and at every module positive. Thus, we can safely remove this
fuse.

**Fusing VREF2: **Similarly, I also deleted
this fuse because it was no longer being used for anything. (Originally
VREF2 was also going to have a direct connection to the module boards).

![](../../images/image_2766881314.png)

@Krish D Can you please check that all of these make sense for the fusing?

Re-considering iso-SPI transformer and Buck-Converter:

I added justifications for our choices to the [DR doc justifications](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.8u1s39bb89yk) subtab

Next Steps:
- Update the PCB layout with the changes and continue routing

CC: @Krish D

> **Aarjav Jain** (Feb 20)
>
> @Hemat Wander

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 10

Implementing Auto-Connection Circuitry Schematic

From the [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4907208613), we decided to stick with using PFETs to enable the auto-connection circuitry. With that in mind, @Krish D raised
the idea of trying to implement a way to have the balancing somehow
before the auto-connection circuitry, that way we don't have to worry
about the voltage drop over the PFETs during high current draw. However
there are some complexities to this we dive into below.
**
Option #1: **We have the balancing circuitry** before **the auto-connection circuitry

- As mentioned this would remove the high current draw through the auto-connection FETs
- We need some way of pulling up the gate voltage of the PFET to stop balancing current from flowing.
-
If we do something like this, and it doesn't work, it makes it harder
to revert back to circuitry we are more confident will work. In other
words, if we put the balancing circuitry FIRST, then we will **HAVE TO** pull up the balancing gates through some pull-up resistor.  An example of such a pull-up is shown below.

![](../../images/image_2751126118.png)

The
issue with having such a pull-up is that it will passively charge up
the entire ASIC through the balancing pin, meaning we have to rely on
this ability to "charge up" to a high voltage through this high
resistance (100k ohms) working. **We are concerned this might not work because we have never tested this before**.

**Option #2: **We
make the balancing circuitry configurable to either connect BEFORE the
autoconnection circuitry or to connect AFTER the auto-connection
circuitry

- Same benefits as option #1
- Allows for
reconfigurability in case the pre-charging does not work, and we want to
have the balancing circuitry strictly after the auto-connection
circuitry

- Will significantly increase routing complexity
and take more space on board for components we use to choose which nets
to short everything with.

Possible implementation
of this: Using zero-ohm resistors or using 3-pos test pins which we
short either way using jumper caps.

**Option #3: **Balancing circuitry is placed AFTER balancing circuitry.
(this is the way it is placed on the schematic right now).

-
Suffers from some voltage drop depending on the current from balancing.
The specific amount could range from less than 100mV, to 200mV
depending on the PFET's being used.
- Don't have to deal with the above issues.

**Conclusion:
**Considering the options above, I'm going to choose to go with Option #3 (aka keeping what we have). This is because:
1. It reduces complexity
2. It allows us to revert back to having other forms of auto-connection circuitry
3. If needed we can bypass the PFETs with hardware for improved accuracy if we find this is required from testing.

CC: @Krish D @Michael Lin

> **Aarjav Jain** (Feb 11)
>
> @Hemat Wander: Fully agree with continuing with Option 3.

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 9

Coming to a decision on pre-charge circuitry:
In
the past month or so I have been re-evaluating the autoconnection
circuitry a lot due to it being one of the main requirements we wanted
to add for V4, and unfortunately finding that any method I can find of
doing so has somewhat major flaws.

Two sum it up,
we essentially have two main options for satisfying this requirement.
One is what I will call the PFET option, which effectively provides
switches at each ADBMS1818 channel input, and the other is the
pre-charge option, which involves charging up each ADBMS1818 channel
input up to a similar voltage to the cell to protect against transient
spikes when adding each connector.

**
Option #1: PFETs**

pros:

- Have evidence that it works (from Formula E using effectively the same thing)

- Would have a much simpler procedure for use. That being, we plug in the connectors in any order, and then just have **one **jumper cap that we need to plug into activate everything.

cons:

- Lots of space taken up on the board, expanding the board to 120mmx160mm, filled with components
-
tens to hundreds of milliohms of resistance almost guaranteed for any
PFET chosen, making a 20mV-100mV level reading drop during balancing

**Option #2: Pre-charge circuitry**

pros:
- Extremely simple and compact circuitry

- No resistance issues, meaning very little drop in voltage during balancing

cons:

-
A more complicated connecting procedure. First we must connect the
first and last module connectors and attach a jumper-cap for pre-charge.
One that is done, we can connect all other connectors in any order.
Finally, we have to remember to remove the jumper-cap.

- Possibility it might not work (we have to test with an ADBMS1818 chip to confirm it works)

There
is also a secret 3rd option, where we return to the same topology as V3
where we have jumper caps for each module. However, I think there would
be a way to be able to at least connect the jumper caps in any order
(by having a large resistance in parallel with the jumper caps to
pre-charge).

So what should we choose?

Essentially,
choosing between these two options comes down to prioritizing ease and
simplicity of connecting everything, or effectiveness once everything is
connected. Originally, I was leaning towards Option #2 as it would
provide higher accuracy without the voltage drops across the
source-drains of each PFET (especially during balancing). However, after
DR day and discussions with others, **I'm going to conclude that we should stick mostly with Option #1. **(I will get back to the "mostly" part)

My
justification for this is that idiot-proofing the connection process is
the most important thing, more so than having accurate readings during
balancing. This is because, we want to create a procedure for working
with the slave boards, which we can even follow when our brains are
fried (after an all-nighter at competition). Furthermore, we shouldn't
be balancing anyways during competition, so this lack of accuracy will
only be an issue when using the battery outside of comp.

Note
that this comes somewhat directly from the requirements in the DR0. I
mean it was also a requirement to have accurate voltage readings, but
I'm now choosing to prioritize this option.

![](../../images/image_2744664174.png)

That being said...

I
will also include the components on the board for option 2 (and option
3), which will only take up slightly more space on the board (8 more SMD
components), but it will allow us to switch to an option without the
balancing issue.

Some changes to the PFET circuitry

As mentioned in [previous updates](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4901636677),
I realized that the gate capacitors would have rendered the circuitry
completely useless by making the PFET conduct for a significant period
of time when a connector is added. Today, I realized that the resistors
in series with the diodes were effectively useless. I originally added
them to have a more ordered connecting sequence for each module.
However, that is not necessary, as we only need to ensure that the
voltage at each input of the ADBMS1818 stays below 8V, and that there
are no current spikes, both of which are true in this case.

One
big thing is that I realized from looking at the PFET formula E is
using, that there would be a voltage drop of up to 70V across the PFET
when it is charged up. Thus, FE using this [PJA3471_R1_00001](https://www.digikey.ca/en/products/detail/panjit-international-inc/PJA3471-R1-00001/14660016)
PFET, which I can confirm after scouring digikey, is the best of its
high voltage rating kind. The issue with it though, is that it has a
much higher Rds(on) and much high minimum gate-source threshold voltage.
Thus, for the goal of being able to stick with a smaller voltage rating
PFET, I devised the following:

Use an extra 100k resistor in
parallel with the PFET, to essentially charge up the drain of the PFET,
such that the PFET doesn't have to handle taking a large (>70V)
source-drain voltage.  I did some spice simulations, and it seemed to
work (results below). If it doesn't work, we should be able to
substitute FE's PFET in-place of ours as they have relatively the same
footprint (SOT-23-3 vs SOT-23), and we can de-populate the 100k
resistors if needed. The resistor is 100k as to not blow up the
ADBMS1818 during this pre-charge process.

Is this logic sound @Krish D ?

In
the following simulations, we can see that the source-drain voltage of
the PFET (this is for module 15) spikes up to ~15V for an extreme brief
period of time before falling back down. Thus, the drain-source voltage
stays within the limit and falls back down to ~0V extremely quickly.
This is essentially a race for the drain to charge up sufficiently
before the gate charges up, so as to prevent a large drain-source
voltage buildup. There's a concern this might be a race condition, but
if it doesn't work we can always revert to a more stable PFET.

![](../../images/image_2744685390.png)

<img src="../../images/image_2744685847.png" width="353" height="240">

Also, we are going to be switching to the [DMP2045U](https://www.diodes.com/assets/Datasheets/DMP2045U.pdf) for the PFET, as it is seemingly cheaper, has a lower Rds(on) and has ESD gate protection.

Next Steps:
- Finalizing the changes to the auto-connection schematic with this in mind.
- Changing the layout + routing to match these changes.

> **Aarjav Jain** (Feb 11)
>
> @Hemat Wander I like this plan!

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 9

Pre-charge testing circuitry:
The
purpose of this update is to essentially experiment with one of our no
longer in use slave boards and determine if I connected a pre-charge
resistor ladder, what would happen to all of the voltages, or in other
words, how much would the internal resistance of the ADBMS1818 affect
the voltage ladder. ([Test plan here for reference](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.ctq5tud7nag1)). As the test is pretty simple, the plan is pretty bare-bones.

Note although we are testing with the LTC6813, the application is for the ADBMS1818, which should be similar.

From a [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4888364287),
I measured a resistance of 3.5 - 4 Megaohms from each ASIC input to GND
(on one of the spare LTC6813s). Now, I'm going to try creating a test
circuit to pre-charge the ADBMS1818 up to a reasonable voltage using
high value resistors to prevent any current spikes.

I set up a
chain of 100k resistors in series and then connected each one to a cell
input, except for mod16, as the pre-charge relies on their being no
direct connection to module 16. As I'm working with technically HV (60V)
I taped all of the test points to the alligators and will try to only
use one hand as best as possible. I also will set the current limit for
the power supplies very low as we don't need much current. I also have
the reverse voltage protection diodes for the PSUs connected as normal.

![](../../images/image_2744413959.png)

I
started up the PSU and started turning up the voltage of the 1st PSU
while probing the second module. I got a voltage drop of 8V even when
the pack was only at 22.5V. This shows clearly that there is some large
imbalance internally with the resistances of the LTC6813. (At least with
this possibly broken version.)

**Actually, it was a hardware bug:**
I forgot to connect the GND of the slaveboard. Once I did that the
voltage readings started being more normal (2nd module had 1V when the
pack voltage was at 20V.

I increased the total series voltage up
to 63V, and so now I'm ready to probe. Ideally, we would want the
module voltages to be rising from 3.9375 V increments (however, the
resistance of the ASIC might play a role + the ASIC might be damaged).
Interestingly, we get voltage drops of ~0.5V across each module and like
56V across the top resistor. (This is not something I expected, as we
would expect the voltage across each resistor to be essentially the
same). What this means is drawn out below.

![](../../images/image_2744426476.png)

I
then decided to probe the resistance measured across from each module
to GND across the resistor ladder (while it was attached to the
ADBMS1818) and I got essentially increasing resistances from 100k ohms
to 1.6 Megaohms (as would be expected). Thus its extremely strange that
we get such a voltage drop across the initial resistor.

My
best guess is that it has to do with the LTC6813 on the slave board I'm
testing with being broken. Either way, we can regard this setup as a
failure, since it didn't work.

Conclusion:
As this
setup didn't work, we know that we would have to drive a resistor ladder
with a lower resistance, meaning that instead of having the high
resistance be on the ladder, the high resistance would be from the
ladder to the ASIC (as in the drawing below).  Note that the ladder is
only connected to the most positive module and GND (this is different
from the old setup).

![](../../images/image_2744443639.png)

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 6

Autoconnection Circuitry Testing #2: ([previous](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4863725373))

The
purpose of this update is to test the two methods for auto-connection
testing and see some of the behavior I missed last time. Previous update
for context. Specifically I want to:

- Repeating Tests with the fix to the breadboard circuit **with **the PFET gate capacitors. (I had messed up some resistor values previously)

- Try tests with now removing the gate capacitors  (as we are planning to in the main design).

- Probe balancing voltage drop when drawing current across a higher module (say module 5)

Assembling Test Components:
The first thing we need, as in the previous update is diodes to protect the power supplies when connecting them in series.

From the inventory I used the following diodes:

- 2 slave board diodes that were in the proto-crate

- Also used 1 through hole diode that was left over from the testing I was doing

**side note:** I realized that soldering on top of old stencils makes it a lot easier (so we don't damage the desk)

**side note #2: **I probed continuity across the power supplies when they were off (

This gave my the six diodes I needed for all of the power supplies.

For the test plans below, I [refered to this doc](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.ctq5tud7nag1).

![](../../images/image_2740341308.png)

Test Setup #1: Completing the original test from before

This
test entail actually connecting the autoconnection switch and probing
with an oscilloscope to see what happens. Thus, we first connect all of
the power supplies in series, turn them to 4V and connect them to the
breadboard as before. We can then probe the voltages across the 5th and
6th module to start. Below are two photos taken from the modules being
connected, we can see that their voltage seems to spike up to ~8V at the
beginning. (A zoomed out and zoomed in photo are shown). **The red line shows the difference in voltage between input 6 and 5 (which is effectively the voltage of mod 6). **

**Module 5 and Module 6:**

![](../../images/image_2740341586.png)

![](../../images/image_2740341936.png)

This
is unfortunate, because this is the opposite of what I wanted to see. I
was expecting to see the voltage curves be much smoother and more in
order. It seems that changing the resistance values from 100ks to
something else as I simulated should make it better, actually made it
worse in real life. (I re-tested this a few times and got similar
results). Its possible that something with the power supplies transients
is what's causing this, but I'm honestly not sure.

Below
are some of the other modules, they all seem to have better voltage
curves (none of them spike to 8V), but nothing is charging up in order
like I was expecting. I have no idea what's causing this.

**Module 4 and Module 5:**

![](../../images/image_2740341586.png)

**Module 3 and Module 4:**

![](../../images/image_2740344008.png)

**Module 1 and Module 2:**

![](../../images/image_2740344645.png)

**Module 2 and Module 3:
**

![](../../images/image_2740345109.png)

**Interestingly**,
module 1 and 2 and then module 2 and 3 seem to display the exact
behavior I was hoping for where their voltage curves rise up one after
another, where they charge up one after the other. It's very strange
that none of the other ones are working other than the first two.

**Conclusion: **Either
this is an issue with my breadboard (which I could not debug), or
something is stopping the circuit from auto connecting correctly. Either
way, this this output not working is fine due to the outcome of the
test without a capacitor (see below). (from later results I am guessing
this is due to a hardware bug?)

Test Setup #2: Connecting Modules out of order (WITH PFET GATE CAPACITOR)

The
purpose of this task is to simulate plugging in the connectors on the
slave board out of order before we get to the pseudo-steady state of all
the connectors being plugged in.

Before beginning the
test proper, I tried testing what I would see if I connected say module
5's jumper wire without connecting anything else (except GND and module
1). If I probe the other side with the orange multimeter I see that the
voltage spikes up quickly before going back down.

![](../../images/image_2740313044.png)

Now probing with an oscilloscope.

**Connecting Module 1 + GND and then module 5: **

If
we plug in this module, with mod 1 and GND connected, we see that the
voltage spikes up and then falls to around 4V where it seems to
oscillate around for a few seconds before falling back down to 0V. This
oscillation behavior is a bit strange, but the sitting at 4V before
falling down is expected.

![](../../images/image_2740348170.png)

![](../../images/image_2740348793.png)

![](../../images/image_2740349491.png)

(All of the above photos are of the same thing just zoomed differently).

**Connecting module 5 and then module 1 + GND: **

We seem to get the same behaviour as above.

![](../../images/image_2740353472.png)

**Connecting Module 1 + GND and then module 6:**

The
difference between this test and the last two is that module 6 is
connected to the beginning of the gate PFET pull-up chain. So this
simulates connecting the first and last module. We seem to just get an
even bigger spike in voltage.

![](../../images/image_2740351652.png)

I
don't think there is a point testing the other modules with capacitors.
Now, we can test everything else without capacitors, as we decided
based on simulations that we would be removing the capacitors. (The
preliminary tests enforce that).

Removing Gate Capacitors:

As
can be seen from the schematic below, the capacitors I am removing are
the 100nF capacitors on the gate source of the PFETs. These are
currently preventing the gates of the PFETs from being pulled up quickly
when a "connector" is attached.

![](../../images/image_2740358988.png)

Test Setup #3: Connecting Modules out of order (WITHOUT PFET GATE CAPACITORs)

Same
as before, but we now have capacitors removed. We get a similar spike
at the input, but this time the spike is for much less time than it was
for before + we no longer see the oscillatory behavior at 4V. (For mod
3, we see some oscillation but its at a much smaller voltage).

**Module 6:**

![](../../images/image_2740355197.png)

**Module 5:
**

![](../../images/image_2740360332.png)

**Module 4:**

![](../../images/image_2740360606.png)

**Module 3:**

![](../../images/image_2740360923.png)

**Conclusion: **Even
though a voltage spike is still present, it fades to 0 much more
quickly, and is much less pronounced. This voltage spike is caused by
the time it takes to fill up the PFET gate capacitance before it can
stop the flow of current. If we need to, post-bringup we can reduce this
resistance value (along with the others to compensate at the cost of
higher quiescent current). Furthermore, I'm also thinking of using PFET
diodes with builtin TVS ESD protection, that will hopefully allow some
current to flow from source to gate during transients to help flatten
this curve.

Test Setup #4: Same as test Setup #1 but with capacitors removed

When
using 50ms time intervals, module 5 and 6 now seem like they are being
connected at the same time. However, if we zoom in to 250us, then we see
much clearer behavior. The modules seem to be connecting one after the
other!! (this is even better than with a capacitor). **Reminder: **Red is the second module (through math), and yellow is the first module.

**Module 5 and 6:**

![](../../images/image_2740361626.png)

![](../../images/image_2740361889.png)

**Module 4 and 5:**

![](../../images/image_2740362230.png)

**Module 3 and 4:**

![](../../images/image_2740362620.png)

**Module 2 and 3:**

![](../../images/image_2740363116.png)

**Module 1 and 2:**

![](../../images/image_2740363530.png)

**Conclusion: **The
autoconnection circuitry works better without capacitors. However, the
fact that module 3 didn't seem to work, possible points to the fact that
it was indeed a hardware bug that stopped the testing **with **capacitors from working. Regardless, this is good for without capacitors.

Test Setup #5: Testing balancing voltage drop with capacitors removed

The
purpose of this test is to see the drain-source voltage drop across the
PFETS when we are drawing more current due to balancing. I specifically
realized I wanted to test this at higher modules, mod 5 and 6. I also
ensured I was not hitting the current limit of the PSUs for the
following tests.

To give some context, the gate source
voltage and drain source voltage locations for the PFETs are shown
below. If we were to be balancing module two, then the current "I" would
be flowing as shown down through PFET 2 and up through PFET 1.

![](../../images/image_2740367170.png)

**Mod 6 balancing**

We
see a voltage drop of 160mV across the PFET of the 6th input and 60mV
across the PFET of the 5th input. This creates a total drop from 4V to
3.5V across the balancing resistor, however this is likely due to
additional resistances in the breadboard. the voltage drop across the
PFET is the main store, and this level of voltage drop is unacceptable.

![](../../images/image_2740364266.png)

For
reference, the gate-source voltage of the 6th PFET is -3.3V and the
gate-source voltage of the 5th PFET is -3.4V. These should be plenty for
balancing, so it **extremely strange** that we are seeing this level of voltage drop. It could be due to the power supply somehow?

![](../../images/image_2740365013.png)

**Mod 3 balancing
**I
tried to test mod 3 to see if it was an issue with the power supply,
but I got that the voltage drop across PFET 3 was still 50mV. For
reference, the gate source voltage of the 3rd PFET was around -3.4V. The
voltage drop across the PFET of mod 2 was in the 30mV range (as last
time). This is with a -3.57V gate-source voltage drop. It just doesn't
make sense that we would see such a large change from 30mV to 50mV+ just
from the small change in gate-source voltage.

If we do
the same as above, but drop all of the PSU voltages to 3.0V, we get a
gate-source voltage across the 3rd PFET of 2.5V, and then the voltage
drop across the drain-source of the PFET becomes 22mV. This demonstrates
to me that the voltage drop across the PFETs is not an issue of
gate-source voltage not being sufficiently high.

If we try the **Mod 6**
balancing test, but with 3.0V PSUs instead of 4.0V PSUs, we get that
the drain source voltage drop across the 6th PFET is 45mV with a
gate-source voltage of -2.5V. I guess this discrepancy is just caused by
the PFETs having different gate source voltages, however I was not
expecting them to vary **this much**.

**Switching the PFETs and then re-testing. **

The
purpose of this test is to see if the difference in voltage drops is
due to the variation of the PFETs. After switching the 2nd and 6th PFET I
decided to retry the balancing on module 6 (drain-source voltage drop
across the 6th PFET when the PSUs were at 3.0V). I got a drain source
voltage of 35mV compared to 45mV as before.

If I set the PSUs to
4.0V each, then I get a drain-source voltage drop across the 6th PFET
of 39mV compared to the 160mV from before (big difference).

If
I do balancing across the 2nd module and probe the 2nd PFET I still get
a drain-source voltage drop of ~28mV still. So it seems to be a
combination of the module # used and of the PFET specifics. That, or
something is going wrong with my breadboard circuit at these highish
currents (~0.3A).

**Conclusion: **

The
voltage drop across the PFETs seems to vary a lot, and so if we value
retaining voltage information while balancing, it doesn't make sense to
me to use PFETs. If we are fine with only reading voltage information
while balancing, then this is fine. Otherwise, we will likely need to
use the pre-charge circuitry instead (if it works that is).

Overall Thoughts:

Based
on the above results, it seems that although we were able to get very
nice behavior with the PFETs switching on in order (without gate
capacitors), there unfortunately is the issue of the major voltage drop
during balancing. Based on how much it seems to vary, we would likely
have to find some alternative solution to read voltage during balancing
(i.e. PWM balancing). What are your thoughts on this @Michael Lin @Krish D

One
thing is that we are using 10Mega ohm pullups for out PFET gates, while
formula E is using 100k pull-ups (100x difference). This means our
spike might be much longer then theirs would depending on the PFETs they
used. On their schematic I don't think it says the MPN of the PFETs
they used, can we ask @Krish D ?

Another
final note is that the voltage drop probably only varies for forward
current through the PFETs. Backwards current through the PFETs would
always have a similar voltage drop from the body diode.

Next Steps:

-
Test the pre-charge circuitry using the spare slave board and measure
the voltages across each cell input with a 100k resistor divider ladder
for pre-charging.
- From the above, decide what autoconnection method we want to use.

> **Christopher Kalitin** (Feb 6)
>
> @Hemat Wander
> 
> If “PWM Balancing” how much time do you think would be required after stopping balancing to taking the voltage measurement?
> 
> I
> imagine this becomes an issue at very high voltage measuring rate. Eg.
> If you need 1 ms delay to get a good reading, but take readings at 500
> Hz then your effective balancing duty cycle is 50% (each period is 2 ms,
> half of which has the PFET off for you to take a reading).
> 
> Also
> you should ask the people who designed Formula E’s boards directly,
> the equivalent of FE asking Hanlon questions. Or call Hanlon
> or other previous solar Goats!

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 5

The purpose of this update is to document a discussion on slack that happened a while ago.

Slave board Positioning and Accessibility:

The
following drawings show what the wire accessibility for the
scrutineering and isoSPI connectors would be from the pack. As a note,
the scrutineering connector would be tied down somehow using some kind
of removable holder (maybe velcro?).

<img src="../../images/image_2738767273.png" width="503" height="358">

<img src="../../images/image_2738763841.png" width="564" height="256">

![](../../images/image_2738774472.png)

> **Aarjav Jain** (Feb 6)
>
> @Hemat Wander @Deev Shah @Krish D : Hey Velcro is not a bad idea for this application actually.

> **Deev Shah** (Feb 6)
>
> I agree, velcro is a good idea for a quick and easy fix

---

# Untitled

**Author:** Hemat Wander

**Date:** Feb 2

Auto Connection Circuitry Rehaul #2:
Today
I probed the resistance of one of the spare LTC6813s that we had in the
BMS crate, because I wanted to see how much the ASIC was going to
load the circuit, and therefore how low we need to make the resistance
of the resistor divider. Note: I used the big digital
multimeter, as it seems to be much better with larger resistance
values.

Probing Results:
-
When I probed between adjacent pins to try and find the
internal resistance of the ASIC between them (Ex. C18 and C17),
I found that the resistance was in the range of 3.5 - 4 Megaohms,
although the value seemed to shift around.

- When I probed between pins spaced out by 1 (Ex. C18 and C16) I got an internal resistance of 50+ Megaohms.

-
When I probed between each of the pins (C1, C2 ... C18) and V-
(GND), I got an internal resistance of only 3.5-4
Megaohms.

Note these might be dependent on the specifics of
the voltage/current output of the multimeter, and so we will have to
test with a real circuit to determine them.

![](../../images/image_2725121522.png)

Simulating in LTspice
As
from above, it seemed that the 4 Megaohm isolation to GND for every pin
would be the limiting factor in this case of loading the resistor
divider ladder I was making. (loading meaning it would draw current
away from the ladder, making it not have a perfect series of voltages).
Thus, I tried simulating in LTspice with a 4 Megaohm resistance to
GND.

![](../../images/image_2725120508.png)

Essentially,
we first charge up all of the modules using a resistor ladder to GND.
However, since the ASIC itself has a non-negligible resistance, it pulls
every point to GND across this large 3.5Megaohm - 4Megaohm resistance.
See the below simplified diagram for reference. We first connect the top
module to the resistor divider, and then connect all of the modules
once the ASIC has been "charged up". This prevents any current spike
internally in the ADBMS1818.

![](../../images/image_2729234344.png)

The
"issue" is that the internal 4Megaohm insulation to GND at every point,
makes the resistor divider, no longer a perfect resistor divider. Thus,
every voltage (C1, C2... C17) gets charged up to some voltage slightly
below its actual cell voltage. For example, module 17 gets charged up to
~52V while its actual voltage is ~60V when plugged in (if the cells
were at 4.0V).

For these simulations for example, I
switched the C17 switch first AFTER already recharging with the
resistor ladder. The following are the current spikes we see internally
in the zener diodes of the ADBMS1818. As a reminder, the max current
that can go into the ADBMS1818 pins is 10mA.

![](../../images/image_2729219292.png)

However,
these are still smaller then the current spikes I got from FE's
circuitry when connected module connectors out of order (which we
know should work in theory). This leads me to believe it will be
fine.

<img src="../../images/image_2729254130.png" width="600" height="304">

The other point that

made
was discussing the quiescent current draw of this resistor ladder. It
will essentially always be connected, so we can do a worst case
calculation. From simulation, I got a 100 uA - 200 uA draw from
each module. If we assume 3.5Ahper cell, then we get:

(3.5 * 13)/(200 uA) = 227500 hours to drain the battery.

Alternatively, we can view it as the power loss during the race (let's say 3 days non-stop).

72 hours * 3600 seconds * 200 uA * 4.2V = 218 Joules.

I couldn't find from the strategy wikipage what number of laps this would correspond to.

If you can find it.

Note this quiescent current draw is similar to the 100k resistor divider for the PFET autoconnection circuitry as well.

-
I can try playing around with the resistor ladder values, to try
and calculate what resistances will get us closer to the voltage of each
module (so that way it is not that far below).

- We should try
and find the extra slave board to see if we can connect a pre-charge
ladder to it, and see what voltage the modules will rise to. If we find
it, we can conduct tests in the next week.

- I can try
completing the IRL autoconnection circuitry tests with the breadboard
(with and without gate capacitors), which I originally delayed because I
thought the testing wasn't going to be necessary anymore.

Based on the results of the above, I will either add both the PFET and charge up circuitry, or only one of the above.

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 30

Rethinking Auto Connection Circuitry:
When
I was thinking in the shower a few days ago, I realized a problem with
my circuit which I had never considered to actually test in simulation
before. Essentially, all of my simulations (and real life tests so far)
were focused on how the auto connection circuitry would behave when all
the connectors have already been plugged in and it was in a pseudo
steady-state. Thus all my simulations were concerned with if the PFETs
would properly begin conducting in order. However, I never properly
considered what would happen when the module connectors are actually
going to be plugged in to get to that steady state.

I have attached all relevant spice files I used for simulation.

The Problem:
Essentially,
the PFET will begin conducting for a short period of time if we just
plug one of the modules in. This means that if we connect the module
board connectors for modules 8 and 9, the PFET will conduct for a short
while **because** the gate voltage has to charge up to the
drain voltage. I originally thought the 10M resistor would pull up the
gate immediately, but the large resistance in combination with the gate
capacitance + the other capacitance makes it charge up more slowly.
Reminder: We have these large resistances to reduce the quiescent
current draw.

![](../../images/image_2720596420.png)

We
can simulate what happens when the autoconnection switch is open, and
we plug in a random connector, say Module 15's connector. Reminder that
the purpose of this circuitry was to be able to connect the minifit
connectors in any order.

![](../../images/image_2724372447.png)

When
we simulate this, we find that there is a 50mA spike across the
internal Zener diodes of the ASIC when we connect the circuitry, which
could cause the ASIC to break (the limit given in the datasheet is
10mA). This spike is caused by the PFET being in conducting mode for a
long time  (in the seconds) before the gate gets pulled up, when the
PFETs should really be blocking them from the ASIC.

![](../../images/image_2724374091.png)

![](../../images/image_2724407676.png)

What about Formula E's Circuit?
My
first thought after seeing this was wondering if Formula E's circuitry
also had this problem. If we simulate, we see that the voltage across
the filtering capacitors spikes quickly before returning back to zero.
Formula E's circuit is able to do this because the lower resistance gate
pull up resistors are able to more quickly turn off the PFETs. We also
still see the current spike across the internal Zener's go up to 20mA as
well.

![](../../images/image_2724394672.png)

![](../../images/image_2724394037.png)

So
you might be thinking, we can just use Formula E's circuitry, and we
probably could since we know they have tested it and it works. However
I'm weary to do so for a few reasons.
- As they are using PFETs to
connect their voltage taps any time we draw high current (balancing)
there will be some voltage drop in the magnitude of ~50 mV depending on
the PFETs used. (I know this is also true for our, but I address this
later down).
- The spikes I see in simulation for the voltage and
current make me cautious about the chance it has to break the ASIC,
especially in high stress conditions.
- The quiescent current draw
of their circuit in the mA range, means that if the circuit was left
plugged in for about a year, it would discharge 20%. This is perhaps a
lesser reason.
(24 hr * 365days * ~1mA) / (3500 mAh * 13 cells) = 19.3%

<img src="../../images/image_2724397273.png" width="605" height="271">

**NOTE: **These
are pretty small reasons, so we can come back to their circuit if need
be. Also, our original circuit might still work, depending on how wrong
the simulations are. We could test to see if the IRL autoconnection
circuit also faces these problems.
*
Side Note: *[Previously](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4843247753),
I simulated formula E's circuitry, however I know see that I simulated
it wrong because I had included capacitors when there were any. If I
simulate it now, I get the following results with the connection order,
where everything connects in around 0.1 ms. (However, the voltage curves
still seem a bit messy, and according to simulation there is a 20 mA
spike in the internal Zener diodes which should break the chip). Formula
E's circuit probably works however since the the current spike happens
for such a brief duration.

<img src="../../images/image_2724382150.png" width="668" height="207">

![](../../images/image_2724384031.png)

Attempts at solving the problem:
When
I found that this circuitry might not work, it kind of worried me, but
in the spirit of re-thinking BMS from the bottom up, I decided to do
some more brainstorming to try and come up with different solutions than
Formula E. Below are some of the attempts I made.

TWO POSSIBLE SOLUTIONS:
After
about a day and a morning of brainstorming (and some LLM help), I came
up with the following two circuits we can use for pre-charge.

1.
The first idea is to use high-value resistances to pre-charge the
modules before connecting the actual module connections. Essentially,
the requirement is that we connect the first and last modules connector
first (meaning we would have to have to ensure we at least plug in the
last connector first before connecting anything else). Then, the highest
module voltage forms a voltage divider down to the ground of the
circuit through the use of 10Mega ohm resistors. This effectively
pre-charges all of the ASIC inputs up to the correct voltage. After
pre-charge, we can connect the jumper cap and then connect the rest of
the connectors in any order we would want.

<img src="../../images/image_2724440003.png" width="680" height="447">

possible issues:

2.
IFF the above circuit doesn't work, we can try a similar method of
pre-charging, but in this case using PFETs to pre-charge instead of
connecting the pre-charge all of the time. With this method, we could
likely solve most of the issues we **could **have with the
above circuit depending on how testing goes. I'm not exactly sure about
the details of how this circuit would look, but I will look into that if
only necessary.

Conclusion:

By
using a pre-charge approach as opposed to a 1 by 1 connection approach,
we have a better chance of having a functioning circuit and no longer
require PFETs to be constantly connected (meaning we [don't have issues of voltage drops during balancing anymore](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4863725373?reply=reply-4866468947)).
AGAIN, I have no idea of if this will work, other than it seems to fix
the issues of current and voltage being seen by the ASIC (we will need
to test to determine this). The main cost is that we now NEED TO ENSURE
that the first and last modules are plugged in first, however I think
that cost is justified.

The plan is to use the 1st solution, and
only to consider the 2nd solution if we find from testing that the
first solution doesn't work. If the first solution works, we might be
able to remove a lot of the auto connection components we have on the
board.

What do you guys think @Krish D @Michael Lin
(this will probably extend slave board making by a bit, but I think it
is a better solution, and has a better chance at working).

Contingencies:
-
If none of the above options seem good (or we don't have time for them
in our timelines), we can try using the same circuitry we are now,
except with no capacitor. The voltage spikes and current spikes look
about the same as FE's circuit, so it should in theory work.

Next Steps:
-
The first thing I want to do (if I can) is to take the slave boards out
of the pack, and then try pre-charging one using a chain of resistors.
This will consist of using two power supplies in series (60V total), and
then connecting that across a ladder of resistors (we can decide the
value, perhaps 100k ohms - 10 Mega ohms). Then, we can probe the
voltages across the ASIC to see if it is working.

-
Another thing I could do if the first idea isn't an option is to probe
isolation between the LTC6813 pins and GND for some of the spare
LTC6813's. (The LTC6813 will behave similarly to the ADBMS1818).

Reflection:
Before
I begin this reflection, I want to be clear that we have not tested
these pre-charge methods, and so we won't know if they work. That being
said even in terms of just consider this option: This is quite a big
overhaul to the existing work I was doing on the slave board circuitry
and this option probably could have been evaluated earlier in the
process. Why wasn't it? In my mind, I was strictly thinking of the
requirement for the slave board being that we need some method for
connecting each of the ASIC inputs in order. However, that's not what
the requirement was listed as in the DR. (See image).

![](../../images/image_2724544116.png)

Even
in the beginning of the process, I was already thinking about ways of
switching on each connector in order. Instead, I should have been
thinking of how to connect the ASIC without breaking it. Breaking it in
this case means trying to avoid frying the chip via high current spikes
and breaking the voltage thresholds. I could have avoided this simply by
thinking bigger earlier on, and not getting stuck in the details of
trying to solve a problem that wasn't the actual problem.

The
thing is, even before the slave board DR0 happened, even before
competition in 2025, I had already subconsciously made the requirement
in my head that there needs to be some way of connecting the inputs in
order. Then when I saw Formula E's schematic doing that, I got further
locked into this one solution space.

To not have this problem in
the future, I essentially just need to reconsider if what I'm doing is
actually tackling the core of the requirement, or if I made some
assumption about how the requirement needs to be solved. This can be
done by questioning yourself IN THE EARLY STAGES, for if the way your
considering to solve a problem, is the only way that problem can be
solved.

Extras:

In this process of brainstorming, chatGPT told me this... so I probably should have asked chatGPT this question earlier on.

![](../../images/image_2721528180.png)

Also
chat gave me some useful links that could be helpful later on, for some
forums and a datasheet for an application of the LTC6813:

[Where to attach shield of isoSPI](https://ez.analog.com/power/f/q-a/566267/ltc6820-ltc6811-1-isospi-signal-where-to-connect-shield-of-...)
[ADBMS1818 vs LTC6813](https://ez.analog.com/power/battery-management-system/f/qa/582488/adbms1818-vs-ltc6813)

[Mixing ADBMS1818 and LTC6813 in one daisy chain](https://ez.analog.com/power/battery-management-system/f/qa/558455/is-it-possible-to-use-adbms1818-boards-in-daisy-chain-mixed-with-ltc6813-boards)[List of possibly useful threads](https://ez.analog.com/search?engineerzone%5Bquery%5D=LTC681&engineerzone%5Bpage%5D=100)[Other ASIC thing that we might want inspiration from](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17843.pdf)

LTspice Files:
[Auto_Connect_No_Capacitor.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546624/Auto_Connect_No_Capacitor.asc)[Auto_Connect_No_Capacitor_CONNECTING.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546626/Auto_Connect_No_Capacitor_CONNECTING.asc)[Auto_Connect_Input_Capacitor.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546623/Auto_Connect_Input_Capacitor.asc)[Auto_Connect__Capacitors_Gate_Source.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546625/Auto_Connect__Capacitors_Gate_Source.asc)[Auto_Connect_Cascading_Capacitor.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546627/Auto_Connect_Cascading_Capacitor.asc)[Auto_connect_original.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546636/Auto_connect_original.asc)[Passive_Charge_Up.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546637/Passive_Charge_Up.asc)[FE_Circuitry_test_connector.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546638/FE_Circuitry_test_connector.asc)[Hanlon_Simulation_input_capacitor.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2724546639/Hanlon_Simulation_input_capacitor.asc)

> **Krish D** (Feb 1)
>
> @Hemat Wander Amazing
> work analyzing your prospective outcomes and questioning the exact
> nature of your solution against the requirements. This the **exact** mindset you should have during the design stage of a PCB project.
> 
> Regarding your technical points, I have some notes that led to some questions, which I'll present below:
> 
> 1. **The 100k resistor divider ladder:**
> 
> - Balancing issues:
> As mentioned from your points about quiescent current draw, this
> solution is that you will always be balancing your modules. To determine
> the significance of the issue, you should find the absolute highest
> power loss as a result of continuous voltage difference between modules,
> and compare that against the
> 
> - Relying on procedure:
> Original problem of V3 was that it wasn't obvious that too not
> disconnect them in any order, so your previous solutions all relied
> on **a single jumper** to do all the work. This
> solution somewhat fails to address this since it relies on having to
> plug-in and unplug connectors in a defined order. However, this might be
> a reasonable tradeoff since plugging only 2 connectors in/out in a
> particular order is much easier than 16.
> 
> - This solution is
> less bulkier than the existing autoconnection circuitry and can be
> tested with our existing slaveboard, however how feasible is it from our
> timelines perspective to test this and not create an issues with
> existing slaveboard that we want to use for driving day? The largest
> concern with testing this is that we could break the LTC again, and with
> our current limited supply, this could prevent us from having the pack
> in drivable condition, and could also prove to be a major debug time
> sink.
> 
> - You mention that having the PFETs is a cause of concern
> due to voltage drop across the Rds on of the FET during balancing,
> however this is only significant if we are to actually balancing during
> comp.
> 
> 2. **Removing the capacitor before the PFETs:**
> 
> -
> There is no way to test the feasibility of this solution unless you
> bring-up the new slaveboards, as it would be quite difficult to adapt
> your breadboard circuitry to see if this will damage the ADBMS1818 or
> not.
> 
> Conclusion:
> What are your thoughts on the points above?
> 
> The
> priority should be to determine what solution matches all of our
> existing requirements, and to be able to test them for feasibility.
> Below is the suggested course of actions to ensure we can fail fast, and
> achieve an MVP for the slave boards ASAP, without risking the
> integrity of the slave boards currently in the pack.
> 
> 1. Increase
> the size of the V4 Slaveboards as needed to add space for the 100k
> resistor ladder, HOWEVER, leave these as DNP for now.
> 
> 2. Assuming schematic is ready otherwise, order the Slaveboards.
> 
> 3. While waiting for order to arrive, look for our **extra**
> slaveboard, and use a 100k resistor ladder divider on a breadboard to
> test if it is feasible to connect the existing slaveboard in out of
> order in the method your originally proposed.
> 
> **Note:
> For step 3, consider that we currently need more LTC or ADBMS1818 units
> to use in the event that one of them breaks during testing.**
> 
> 4.
> When the slaveboard arrives, if the previous solution hasn't been
> tested on the extra slaveboard, than firstly, test the 100k resistor
> ladder divider solution. <- (Consider what exactly needs to be
> measured and how this going to be done).
> 
> 5. Next, remove the 100k
> resistor divider and test the auto-connection circuitry as is/was. This
> includes removing the capacitor at the gate of the PFET to see if this
> is still feasible (the definition of feasible here means the modules can
> be plugged in any order, the autoconnection circuitry works as is.
> 
> From
> here, feasibility of either of the solutions can be assessed all at
> once. Also consider than you can test the different solutions in
> parallel by bringing-up a second slaveboard in parallel.
> 
> Please let me know your thoughts @Hemat Wander
> 
> CC: @Aarjav Jain

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 26

Testing Auto Connection Circuitry Breadboard Circuit:

First,
I soldered a few diodes to protect the PWS2323 power supplies,
these diodes were connected in parallel with the supplies, with the
anode facing the negative end. There weren't enough diodes to protect
the other supplies, and I don't think right now it is worth it to
look for some diodes ass we are only working with 4V per supply.

I
wired up the supplies as follows, specifically with them being wires in
series, and each positive end for each PSU being connected to a PFET
source. Finally I connected the GND end. All of the exposed connections
were taped up. I did a final check to see that no modules were
continuous to each other to prevent shorts.

![](../../images/image_2708898347.png)

![](../../images/image_2708898949.png)

I
then also checked to confirm nothing on the breadboard was touching
each other that it shouldn't (moved things apart, check by
inspection).

Now I set all the voltages to 4.0V
for each of the supplies with the auto connect switch disconnected.
Probing across the first capacitor, we get 0V for the voltage. (this is
what we expect).

Now we can connect the auto-connection
switch using a yellow jumper wire. And we see that the output capacitor
now reads 3.99 volts (this is good!) Similarly, we can probe the rest of
the output capacitors when the switch is connected and disconnected. We
see that when connected, the output voltage is 3.99V - 4.03V while it
becomes 0V when the switch is disconnected.

Something
strange is for the last 3 voltage sources, I found that the voltages
were a little more unstable (shifting around a lot (by ~0.01V), although
I don't know if this is because of the circuit, or because the
last 3 PSUs were from the XT 30-2 power supplies, which may just be more
unstable).

Since I don't have much time, I will just be testing a few modules with the oscilloscope.

When
I started trying to probe, I found some weird behavior with the
100 ohm resistors for the RC filters having a 2V drop across them, I'm
extremely unsure of what can be causing this.

Ok, I
found the issue, some how the oscilloscope probes were acting as a short
between the capacitor outputs, so I'm unsure on how to fix that.
Currently, it seems like the GNDs of the oscilloscope channels are
connected so I cannot use two channels at the same time. For now,
we can just make the GNDs go to the same place, so the final voltages
will rise at the same time.

OKOK after playing around with
the oscilloscope for a bit, I finally got it to acquire a single shot
waveform, by pressing the single button. (That shouldn't have taken that
long.) We got the following waveform.

![](../../images/image_2708899783.png)

Side
Note: When we disconnect the auto-connection circuitry, it takes
about 5 seconds for the capacitors to become discharged. This is about
what we expected, but is interesting to confirm.

Now we can
compare the voltage charge time of the second and third module. The
captured waveform is shown below. Blue represents the total voltage of
the third module compared to the first module (C3-C1), while yellow
represents the total voltage of the second module (C2-C1). The red line
represents their difference (C3-C2) and therefore the voltage across
module 3. We would expect this to charge up after the second module
(C2-C1), but it charges up at the same time. It seems that the rise
times of the capacitors seem to be exactly the same somehow. This is
quite surprising to me an unfortunately means the capacitors are not
rising one after the other (I was expecting at least a 1ms delay
between charging). However, them rising at the same time will probably
also still work for the connection to the ADBMS1818, so this is not an
issue really. Also it is nice to see that the voltage charge up is so
stable.

![](../../images/image_2708900141.png)

If
we compare the first and third module, we see that the also charge up
at the same time, similar to the second and third modules. It seems that
the charging will occur somewhat simultaneously no matter what.

![](../../images/image_2708900596.png)

Interestingly,
on this third attempt, I tried to probe 3 channels, at module #2,
#3 and #4. I found that if we probe the module voltage curves, we
get this interesting double bump for the voltages charging up. I'm not
entirely sure what's causing this, as we don't see this in
simulation.

![](../../images/image_2708900958.png)

I also
tried recording the falling voltages during module disconnection, and
I found that they again seem to be falling at the same time rather
than one after another. See below.

![](../../images/image_2708901431.png)

Lastly,
I will try to probe the gate source voltages for neighboring FETs.
Now this is very strange, we see that the first module's PFET gate
voltage is going down while the rest of the module PFET gates seem to
be remaining at the same value. I actually am not sure why this is,
and it it probably why we are seeing the output voltages behaving so
strangely.

![](../../images/image_2708902551.png)

To
debug this, I probed voltage across the first diode and found that
there was a positive voltage drop across it. OH WAIT, this is because
the oscilloscope is essentially by passing the 10M resistor as it only
has 1M of isolation. So unfortunately, we cannot really probe the gates
as it stands. Thus this diagram is essentially meaningless.

Final test: current draw.
The
last test I wanted to do does not require the oscilloscope, only a
multimeter to read voltage across the 10 ohm resistor. Across the second
module. Before this "balancing resistor was added, the voltage drop
across the capacitor was 4.04V. After connecting the resistor, the
voltage we are reading becomes ~3.7V however, the voltage drop
(source-drain) across the PFET only goes up from 0.04mV to 26mV as
expected.

I tried decreasing all of the PSU voltages and
repeated this test I got the following PFET drain source voltage
drops.

V (PSU) = 3.5V, V(PFET) = 26 mV.

V (PSU) = 3.0V, V(PFET) = 27 mV.

V(PSU) = 2.8V, V(PFET) = 25 mV.

V(PSU) = 2.3V, V(PFET) = 23 mV.

V(PSU) = 1.5V, V(PFET) = 36 mV.

These
results are much better than I expected, and essentially show that
the voltage drop across the PFET even at low module voltages will be
negligible for balancing.

![](../../images/image_2708903676.png)

Conclusion:
-
Although the transient (when we connect and disconnect) curves did not
behave as we expected in terms of one voltage input turning on after
another (on the scale of milliseconds), we did see that all of the
modules do seem to turn on at essentially the same time, meaning that we
will never see any voltage across the ASIC inputs that would cause it
to break. Thus, this circuitry would work if we use it.

-
The voltage drop across the PFET is even less of a concern than
I thought it was going to be, so it should be completely
fine.

> **Aarjav Jain** (Jan 26)
>
> Excellent work @Hemat Wander.
> Your dedication especially these last weeks have been amazing! Writing
> this update during and right after your testing to inform us what is
> going on is extremely helpful. Some notes regarding the update:
> 
> In
> general one improvement to this update would be clarity. Whether you
> are writing this at 4am dead tired or fully energized, your update
> quality cannot decrease. This is because an update is only as good as
> people understanding it! For example you said "To debug this, I probed
> voltage across the first diode and found that there was a positive
> voltage drop across it". But it was not clear why you decided to probe
> this exactly. Perhaps a diagram in the update showing exactly what is
> where will help (or using Designators from Altium).

> **Hemat Wander** (Jan 26)
>
> I
> will respond to your points later, for now I wanted to note that I
> realized a mistake with the circuit setup that might resolve some of
> the problems I faced.
> 
> - In the circuit, I forgot to
> place 220k resistor and 470k resistors respectively in series with the
> last 2 module's diodes. See [schematic here](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.ctq5tud7nag1).
> This is likely what is causing all of the modules to charge up at the
> same time rather than one after another. Thus, immediate next step is to
> change these resistance values and re-test.
> 
> - I also
> realized I need to test balancing voltage drops on the later
> diodes, as I was only testing with the second module. I.e. I only
> connected a 10 ohm resistor between module 2 and module 1, rather than
> testing between module 6 and module 5 for example.
> 
> - **POSSIBLE ISSUE**: Something
> I just realized is that the auto connection PFETs will have a
> voltage drop of ~30mV across them (from source to drain) when balancing
> is occurring. Originally, I thought this value was fine, as
> I was mostly concerned with the voltage drop across the PFET
> changing the amount of balancing current (by adding the PFETs
> series resistance in series with the 10 ohm resistor).
> 
> However,
> I now realize that a 30mV drop across both PFETs will likely
> represent a 60mV drop in the voltage reading when we are balancing. AKA,
> a module reading 4.03V might become 3.97V when balancing. This
> could be problematic because balancing occurs for differences of
> 50mV. This may or may not be acceptable depending on a few
> points.
> 
> - First of all, formula E must be experiencing a
> similar thing, although I'm unsure what specific PFET they are using, as
> it doesn't say in their schematic.
> - We might be able to find a smaller voltage drop PFET, but I doubt many PFETs will go below a ~10 mV drop.
> - We could have a firmware solution for this (@Michael Lin )
> by compensating for the voltage drop when balancing (based on the
> expected actual module voltage). Although this seems like a band-aid
> solution, I feel like it might be our best bet, as we will be seeing a
> voltage drop across the PFETs no matter what.
> - This depends on
> the characteristics of the cells, but another firmware solution we
> could try something like PWM discharging, where we balance for some 90%
> of the time, and then the other 10% of the time we stop balancing to
> again read the module voltage.

> **Aarjav Jain** (Jan 26)
>
> @Hemat Wander:

---

# Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** Jan 25

**Summary Current Design**

**Goal:**
Confirm that the current status of the auto-connection circuitry is
feasible to manufacture and have confidence the current design will be
able to meet its requirements.

**TL:DR: **We are confident. We have many justifications all coming from distinct sources which support our confidence.

**Requirements: **

**Confirmation: **Below I list **design justifications **for the auto-connection circuitry. These justifications give us confidence that the circuitry **will** meet the above requirements:

CC: @Krish D

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 23

Assembling Auto Connection Circuitry Breadboard:
The plan for today is going to be assembling the slave board's auto-connection circuitry [outlined here](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.ctq5tud7nag1).

Other than the materials outlined in the doc, I also need:

Components used:
- 43 header pins

- 6 SOT-23 breakout boards

- 6 DMP2110U-7 FETs

![](../../images/image_2706888001.png)

Some notes from assembly:
-
The method I used for soldering was quite inefficient and produced
solder blobs on the PFETs. Next time, we can improve the process by
using more flux and using a heat gun to melt all the solder under the
component to flow the component into place.

- I tried
measuring the resistance of the 10M resistors using the orange
multimeter, but when I measured it, it says it was ~4.7M ohms. Now why
can this be? @Gurman Khella However,
when I measured it using the digital multimeters we had, it says it was
9.7M ohms, which seems closer to what we expect. If the multimeter is
around 100M ohms, we can assume the resistors are basically 10M.

Also
side note I measure the resistance of the breadboard and across
12V and GND on the new DRD and I got >>100M ohms on the
breadboard, and 2Mega ohms across the DRD 12V and GND.

The final result:

![](../../images/image_2706887634.png)

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 18

Auto Connection Update #7?
It's
been a while since the last update. I thought I was done looking
at this autoconnection circuitry stuff, but there are two last things
I wanted to do before [testing the circuitry](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.ctq5tud7nag1).
One is that I realized a concern with the continuous gate-source
voltage value of the PFETs, and the other is that I wanted to
simulate formula E's circuitry to see what it behaves like (I never
did this although I should have).

Concern for continuous-on PFET resistance
For
the first point, I realized that in previous updates I was going off of
some assumptions from the datasheet that if we were above the
gate-source threshold voltage, the PFET would be sufficiently conducting
for balancing current to go through it with a small on resistance.
However, I now realize that this threshold voltage is only for a drain
current of -250uA, which is much lower than we need for balancing
(balancing will be at ~400mA max).

<img src="../../images/image_2691336780.png" width="656" height="63">

Thus,
I want to re-evaluate whether we are going to be supplying a
sufficient gate-source voltage to the PFET to have it be "conducting
enough" for balancing current. I will define conducting enough as having
a small on-resistance (or small drain-source voltage drop) when we are
at the minimum gate-source voltage we would be during normal
operation. For reference balancing itself is ~10 ohms, so we want to be
much lower than this.

For reference, the on-resistance of the PFET at VGS = -2.5V is ~0.1 ohms.

<img src="../../images/image_2691343853.png" width="676" height="62">

In
the past I used this image to justify that the gate source voltage we
had was going to conduct enough current for balancing, however I now
realize that I miss the critical equation at the top left which
says this is only true at Vds = -5V. For our case, we can estimate that
if at ~0.1ohms, the Vds will be (0.1 ohms)/(0.1 + 10 ohms)
* 2.5V = 0.025 V or around 20mV.

![](../../images/image_2691345278.png)

This
is confirmed by simulation where if we set a balancing PFET to conduct
by connecting its gate to a lower voltage, the voltage drop will be at
~30mV.

<img src="../../images/image_2691355840.png" width="450" height="175">

![](../../images/image_2691355473.png)

With
that in mind, the datasheet is kind of unhelpful in determining the
minimum gate source voltage we need to supply 400mA. We can try to use
this chart from the datasheet below. Trying to determine what the drain
current at VDS = 40mV will be a fruitless endeavor since that's
like a very small percentage of the box on the bottom left. Instead, we
can compare to something we definitely know works, we know that the PFET
works fine when the VGS is at ~3V just based on the balancing PFET
working when the modules are at 3V.

![](../../images/image_2691365987.png)

Thus,
if we work based on estimation, we see that the behavior of VGS = 2.5
approximately matches VGS = 3.0V, and so if we can get the VGS to around
this range, it will likely work. In other words, since the different
VGS curves become approximately the same at the VDS/Id range we are
thinking about (30mV, 400mA), as long as the VGS is approximately 2V or
greater, the resistance should be fine.

However, instead of
just speculating and saying it should be fine, we will test this with
the autoconnection circuitry breadboard. However, this gives me more
confidence than before.

Based
on the above, I realized I should change the resistance value of the
pull-up resistors to make the VGS value bigger. This is only really an
issue when the modules are at small voltage ranges (2.5V-3V), but
essentially, we want the the voltage value to be higher. If we use 10Meg
ohm  pull-ups, we get VGS = -1.4V at minimum.

<img src="../../images/image_2691390789.png" width="648" height="225">

If we instead use 22 Meg ohms, we get -1.8V VGS, with the only downside being having to wait 2x as long (~5 seconds).

<img src="../../images/image_2691403503.png" width="648" height="174">

Note
for reference, we can also use 33 Mega Ohms to get at VGS of
-2.0V, and so we may switch to using that if necessary. For now, I think
I will switch to 22 Mega Ohms for a balance between speed and
conduction.

We can create this circuitry pretty easily by changing around our old circuitry to roughly match the circuitry they use.

For
the Gate-Source voltage curves, we get something that looks like this.
We see that each gate-source voltage varies ALOT all the way from 2V to
20V.

<img src="../../images/image_2691461105.png" width="652" height="316">

Zooming
in on the beginning (when connection occurs), we see this interesting
effect where the highest voltage modules have the steepest time
constants, before they settle at steady state.

<img src="../../images/image_2691463397.png" width="666" height="320">

Finally,
we can look at the capacitor voltages at the input to the ASIC. We see
that here the voltage curves are a lot more messy (i think), and that
the order of the voltages being connected seems to be a little over the
place. Specifically, I found that some adjacent modules seem to get
connected very close to next to each other, and we see a lot of
noise.

![](../../images/image_2691466878.png)

If
we can get anything from this it is that despite Formula E's circuitry
being much less "stable" as far as I can tell/simulate, we know that it
still works and doesn't fry the LTC6813 based on the fact that they
brought up the board and it worked. Therefore, I think we should
prioritize having a low on-resistance and low-quiescent current for
the FET rather than making sure that the connection and disconnection
curve have a sufficient amount of time between modules. (In the past we
said we wanted at least ~1ms between modules being connected, but
I no longer think this is necessary). As long as the voltage curves
don't spike above 8V or below -0.3V, we are fine.

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 18

PCB Routing Update #2:
After
an afternoon of work, I have completed the routing for the temperature
traces, along with connected the modules on both sides of the board
(connecting module 8 to module 9 for the balancing and autoconnection
circuitry).

Everything seems to be routed, however if its
routed well is starting to seem a little questionable to me. The
mess of routing you see below was my best attempt to get everything to
fit on the top or bottom routing layers. My justification for this being
fine is that the only fast changing traces will be the MUX select
traces (given by the bottom right 2 pins on each IC respectively). As
these traces are routed completely on one layer, and will have a full
ground plane underneath them, I think it will be fine. However,
these traces are decently close to the other temperature traces so there
could be some cross talk.

![](../../images/image_2691182825.png)

-
Another concern is that the temperature lines cross over the area of
the buck converter which will have a lot of changing voltage due to the
buck converter, which might couple to these lines producing some noise.
As before, the only reason I routed like this was because of routing
constraints. If we want to make it not enter this area, we can instead
route the temperature line on the 3rd layer instead of the bottom layer
(as was done on V4). I'm still considering doing this, however it may
not be necessary. Doing so would cut through the ground planes, however
it could be an option. @Krish D What are your thoughts?

![](../../images/image_2691184559.png)

-
Finally, there is the balancing trace I had to route essentially
all the way across the board. Because the resistance of balancing is
only 10 ohms, the resistance of each trace has a much greater percentage
effect on the resistance of the line. In this case, by doubling the
width of the trace, I got the resistance down to ~0.15 ohms, which I
think is sufficiently small (1% difference in the resistance of the
line).

![](../../images/image_2691186893.png)

-
I have a few next step considerations for routing. Mainly, how am
I going to route VREG, VREF2, and ground fused. In V3 this was done
using the 3rd layer, however if we want to keep that as a standard GND
layer for stability, then we may want to route this using a polygon pour
on the bottom and top layers. The main issue is that the fuses for
VREF2 and GND are at the top right of the board (since they fit there),
while the the sources of VREF2 and VREG respectively are in the
center of the board. I'm a little unsure of how to route this.

![](../../images/image_2691191453.png)

-
Final consideration: Based on the last point, I'm considering if
it is better to get rid of the fusing for the GND of
the temperature lines as we already have a GND fuse from the GND
connecting to the board. The purpose of this fuse originally was to
isolate shorts on the temperature circuitry from the rest of the board,
however I'm considering now if this is still necessary. The issue as
I explained above is that the fuse is so far from the source, so
all the modules on the bottom of the board will need to have traces
traveling all the way up and then down again.

![](../../images/image_2691192606.png)

![](../../images/image_2691193506.png)

> **Krish D** (Jan 22)
>
> @Hemat Wander Great progress so far!
> 
> -
> I don't think it is a good idea to have any traces cut into the GND
> plane nor to have them run close to inductor and buck converter for the
> same reasons you mentioned of noise isolation. Given that the two GND
> layers have a larger distance between them, and we are also not
> expecting the dv/dt of the temperature lines to change quickly, is it
> not feasible to run them through the GND plane to reach the MUX?
> 
> -
> For the routing of VREG and VREF2, is it not feasible to add the fuse
> closer to the center of the board near the MCU? It seems less risky to
> me to have it closer to the MCU. I'm also a bit unsure where the polygon
> needs to be routed. Can you make this more clear?
> 
> - Given that
> so many power polygons would be needed to move through the ground plane,
> I'd be a bit concerned about routing any of the sense lines over the
> traces (Of course we don't expect to route high current to travel
> through these traces, however I'm not sure what transients may exist in
> the power lines during startup or when the capacitors are
> powered). This being said, what are your thoughts on making the
> slaveboard **6 layers?**
> 
> CC: @Aarjav Jain

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 15

PCB Routing:
Since
we agree that the connector placements are good to go we can continue
with routing. As a summary of what we expect the module wiring to
be, here are the module numbers

![](../../images/image_2687352651.png)

Schematic Changes:

I
realized there was no resistor in series with the opt isolator, which
means it would have shorted to ground if connected to VREG. To prevent
this I added a resistor to make the current 10mA for the SPDT relay as
recommended [in this datasheet](https://www.littelfuse.com/assetdocs/littelfuse-integrated-circuits-lcc110-datasheet?assetguid=fef24721-9a57-4423-a6f7-7e12c72ec530). and 4mA for the other relay as recommended [in this datasheet](https://www.littelfuse.com/assetdocs/littelfuse-integrated-circuits-cpc1008n-datasheet?assetguid=55b0a818-3bfd-483f-9372-c078b9202476).
To get these currents, we assume a ~1.4V drop across the diode as
explained in the datasheet, and a ~0V drop across the channel of the
NFET.

R1 = (5-1.4)/4mA = 900 ohms -> take 1k ohms

R2 = (5-1.45)/8mA = 450 ohms -> take 470 ohms

![](../../images/image_2687266137.png)

-
I changed the input to the buck converter to be coming from the in pack
module regardless of if we are in scrutineering mode or not.
Previously, this input came from the output of the SPDT solid state
relay used for scrutineering, as that would have changed what the max
voltage was. However, for the buck converter, we don't need to care
about using the external pack module. Furthermore, going through the
solid state relay would add resistance on the line going to the buck
converter.

![](../../images/image_2687269655.png)

Routing:
-
For the voltage lines coming from the connectors, we want to use a
width that can at least take 400mA. For our case we will rate the width
for ~four times this value, as we have enough space to do so. Thus, we
can use 0.635mm width, to get a max current rating of 1.43A. The purpose
of doing this is to reduce the resistance of the line, as we have a 10
ohm resistor for balancing, and thus changes by 0.1 ohm or such will
more drastically change how much current flows (as compared to most of
the other traces)

- I also used similar width lines for all of
the buck converter circuitry, to ensure that all of the high current
draw elements of that circuit has a sufficiently rated trace.

- I
have now completed routing for the analog circuitry, internals of the
buck, scrutineering and temperatures outputs going to the resistor
divider. The bulk of the remaining routing is isospi and the temperature
lines.  After that I have to figure out where the polygon pours will
go.

> **Aarjav Jain** (Jan 25)
>
> @Hemat Wander:
> What is the resistance of the trace if you make it rated for
> 400mA? Or I guess why is the resistance too large? What problem is
> it causing?

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 8

PCB Layout Update #3
I've completed another draft of the [slave board here](https://ubc-solar.365.altium.com/designs/C270EADE-1A51-48A6-9106-53CF561C5068?variant=[No+Variations]&activeView=SCH&activeDocumentId=IsoSPI.SchDoc(6)&location=[1,135.43,-197.91,-105.78]#design).
The dimensions of the slave board are now 120mmx160mm tall, because I
realized that I could increase the height of the slave board while still
ensure the balancing LEDs stay within the viewable window. Thus, the
components are now much less cramped, however the size of the board had
to increase as a result. The two downsides to increasing the size are 1)
the cost will be higher for the PCB, and 2) the wires will have to
reach further across the board to reach modules on the other side.

**Note:
The overlay "boxes" were mostly made for myself in understanding where
the components for each schematic section were, but we can remove them
if needed.

**Viewing Balancing LEDs:
The
polycarbonate for viewing balancing LEDs will be 70mmx200mm which we now
fit within, due to moving the balancing LEDs to the center. This
distance from one side to the other end of the balancing LEDs is
<85mm, meaning that we could have the two slave board next to each
other, with a ~30mm space between the PCBs (based on the 3D printed
holder) and still fit within the window. @Deev Shah @Krish D @Samuel Shin

![](../../images/image_2669487027.png)

Small schematic changes:

- I removed these test points since I don't think we need them (@Krish D if you have any thoguhts)

![](../../images/image_2669464320.png)

-
I changed the Buck converter's inductor back to the previous revisions
220uH as opposed to the new 1mH despite us calculating 1mH based on the
datasheet. The two reasons for this are because we want to reduce flux
leakage leading to EMI on this analog board, and the second reason is
because we already know that having 220uH already works from the
previous slave board. I'm not entirely convinced of the first point
because some sources say shielded inductors have virtually no EMI, but
to the second point if we frame the inductor choice as needing to
justify a **change** from the previous revision, then I can't really do that as we didn't have any reason that changing the inductor was needed.
- I also realized that I was missing a capacitor at the input, which I have now added.

![](../../images/image_2669468342.png)

-
Thus, the only changes from the previous revision buck converter
circuit, is adding a 5.5V breakdown TVS diode at the output, and adding a
0.1 ohm resistor in series to the output capacitor to improve
stability.

Changes to the board layout:
- As
mentioned the main change was a change of dimensions. This allows us to
spread the components more vertically, creating more space between the
SMD components. This also allows us to create more space between the
isoSPI circuitry and the measurement.

![](../../images/image_2669472380.png)

-
I removed the temperature resistors and capacitors from between the
plastic connectors, as I realized they would be very difficult to reach
afterwards with a soldering iron or heat gun.

![](../../images/image_2669473162.png)

- I labeled and added all the test points, meaning all of the components are now on the board (yay!)

- I changed the scrutineering connector to a 4-position to match the module board.

![](../../images/image_2669475859.png)

Concerns:
-
One of my concerns is that the voltage input fuses will be difficult to
desolder and resolder in practice due to the placement close to other
components (including the test points). We likely won't have to do this
often (based on previous experience). If we did want to improve the fuse
positioning, I'm not entirely sure how we could do this, so if you guys
have some thoughts that would be helpful @Krish D.

![](../../images/image_2669477296.png)

Other
than that I don't have many concerns, as the ASIC now has more room in
the middle. The only thing is if we want to decrease the dimensions for
cost savings.

![](../../images/image_2669479509.png)

Room for improvement?

-
There is now some empty space around the board, which is good for
keeping the analog measurements at some distance from the isoSPI,
however it means that we could shrink down the board dimensions if we
wanted to, although its not entirely clear how this would be done in
practice.

> **Krish D** (Jan 9)
>
> @Deev Shah @Samuel Shin Can
> you folks please comment on whether or not the size poses any
> feasibility changes for scrutineering, module access, etc.?

> **Samuel Shin** (Jan 9)
>
> @Krish D Not
> sure which size you are talking about. If you are talking about the 30
> mm gap, I think you guys have much better understanding on how it could
> improve accessibility for scrutineering.
> 
> @Hemat Wander One
> question I had after reading the update. Why does increasing the
> size of the board make wires need to reach further away? Shouldn't it be
> decreasing the length of the wire?

> **Hemat Wander** (Jan 23)
>
> @Krish D
> 
> I found some documents that help give some information on component selection.
> 1. [Selecting Inductors](https://www.ti.com/lit/an/snva038b/snva038b.pdf?ts=1769190319886)
> 2. [General selecting components](https://www.ti.com/lit/an/slva477b/slva477b.pdf?ts=1769134141543#page=2&zoom=100,0,785)
> 
> As from the calculations I found before, it seems that a higher inductance value reduces the current ripple.
> 
> [This random person on the internet](https://electronics.stackexchange.com/questions/32021/why-do-smaller-loads-require-larger-inductors-in-buck-regulators) gives
> an explanation for why HIGHER inductance values are better on LOWER
> loads. He explains that for low-consumption loads, sometimes the output
> capacitor doesn't get discharged fast enough to justify the buck
> converter charging power into the output capacitor. This means that the
> converter will instead "skip a step" essentially meaning it will not
> charge up the output capacitor in this time. This can lead to
> stability.
> 
> In our case, I added a 0.1 ohm series resistor
> and output Zener diode to help with stability and quick large increases
> in the output voltage, however increasing our inductance value might
> further help with stability. If we want to improve stability, a higher
> inductance value seems better.
> 
> **HOWEVER, **the buck [converters datasheet's](https://www.analog.com/media/en/technical-documentation/data-sheets/max5033.pdf) application notes has a recommended inductance value for a 5V output specification (the 220uH we used last time).
> 
> This
> is essentially now a question between, do we want to stray from
> what we know works and what the application notes suggest for the chance
> of increasing stability. If the answer is yes, we can change to a 1 mH
> inductor (or something in-between), otherwise we can keep the 220uH
> inductor.
> 
> @Krish D

> **Krish D** (Jan 24)
>
> @Hemat Wander
> 
> From
> my understanding, having a lower load implies that it will have a
> higher current draw and requires current stability (i.e a lower output
> ripple at the same). Would we consider the V4 revision of the
> slaveboards to have a high enough current draw to require this
> stability?
> 
> It's hard to know this without testing since the
> buck converter datasheet has it's own recommended value, which is why I
> feel it makes more sense to go with the 220uH inductor since it was
> what we used last time (As we should follow what the manufacturers
> suggest for ideal performance).
> 
> To finalized this decision
> and to try and be practical, is it feasible to find higher value
> inductors and lower value one that was used on the previous revision of
> the slaveboard with the same if not similar size footprints so that the
> noise level can be tested?

> **Hemat Wander** (Jan 24)
>
> @Krish D
> Lower
> load in this case means higher resistance not lower resistance
> (AKA lower current draw). I agree with that and will look into how
> similar the footprints will be between 220 uH and 1 mH tomorrow.

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 3

PCB Layout Update #2
I've completed an initial draft of the circuitry for the [slaveboard her](https://ubc-solar.365.altium.com/designs/C270EADE-1A51-48A6-9106-53CF561C5068?activeView=3D&activeDocumentId=PCB1.PcbDoc&variant=[No+Variations]&location=[3,115.15,48.95,3.79,107.79,47.06,-53.17,0.12,0.99,-0.05]#design)e.
For this draft I'm just trying to see generally where everything will
be placed and then I will finalize everything and fix any small mistakes
afterwards. The main thing I'm thinking about is if the number of
components we have means we will have to expand the board size to
greater than 120x120mm for its dimensions. Currently everything seems to
more or less "fit" give or take some of the test points. However I'm
unsure if having the components this close together is a good idea (I
discuss this below).

![](../../images/image_2653711940.png)

Possible Optimizations:
-
Can move some of the autoconnection or balancing/filtering circuitry to
the space between the connectors, as it seems like there will be
-
Possibly could optimize the placement of the autoconnection circuitry +
balancing/filtering SMD components to have them be more cleanly packed,
and thereby save some space.

Concerns:
- All
the SMD components being so close will make bring up more difficult and
also increase the risk of neighboring components shorting together due
to unnoticed solder or wear and tear.

-
The isoSPI line will be too close to the analog measurements, thereby
leading to noise in those voltage readings. Currently I'm thinking I
will surround the voltage measurement (C1, C2, etc.) traces with a pour
of the previous module voltage to create a stable "return path" and
surround the isoSPI with a neutral pour "chassis" that isn't connected
to the main circuitry in anyway.

- The ADMBS1818 will
be too close to the passives. This is just an issue for bringing up the
board and debugging if we have to replace the ADBMS1818 it will be more
difficult.
- There is not enough space for labeling resistance
values. Specifically, I wanted to label the resistance values of the
resistors in the autoconnection circuitry that can change value, however
I doubt there will be enough space as is to do so.

- The
inductor is too close to the analog circuitry. Same idea as the isoSPI
being too close, except more so because inductors have a lot more flux.
Based on how close the inductor is (~7mm) to the nearest voltage
measurement capacitor, I'm currently leaning towards reverting back to a
lower inductance value (as suggested by @Aarjav Jain)
so we can have less flux and thereby reduce the chances of voltage
measurement noise. Furthermore, we want to avoid the catastrophic issue
of isoSPI communication being messed up, as that is a higher priority
than reducing current spikes from the buck converter.

- The
balancing LEDs might be outside the 200mmx70mm dimensions we have set.
Currently they are in the correct height range (They only take ~70mm),
however they seem like they will require ~240mm or more if we want to be
able to see the diodes at the edge. This is because with the circuitry
we have, it seems that the diodes will span the width of the board which
is 120mm across. Thus my next priority will be trying to figure out a
way to get it to fit within this range. CC: @Krish D @Deev Shah @Samuel Shin

-
Also I have a possible concern for the schematic: will the TVS diode
interfere with the algorithm of the buck converter as it serves as
another diode pathway (although it is past the inductor as as opposed to
L5.1). Ideally it shouldn't because VREG should stay ~5V with some
ripple, however this was just a thought I had I thought I should write
down.

![](../../images/image_2653623525.png)

Change to Scrutineering circuitry:
-
I realized we can use one FET for both SSDs as they can easily take
enough current for both SSDs and we will thereby reduce current draw.

![](../../images/image_2653620166.png)

Two options for SMD components:
Note:
The first 8 modules are all connected on one side (top), and the second
8 (9-16) are all connected on the other side (bottom).

For
the first 8 modules I made all the components have the same sort of
layout that looks like the following. This was just based on trying to
optimize the component placements for having all neighboring nets next
to each other.

![](../../images/image_2653715281.png)

For
the 9-16 modules, I used a different layout for the circuitry because I
thought it would have to be different due to the FETs not being
symmetrical when mirrored. I then later realized that I could have just
rotated the components 180 degrees. Before I realized this I already
created a separate layout for the bottom that has a slightly different
organization of the components, and so we can now compare them and
choose one or possibly keep both.

![](../../images/image_2653715764.png)

Next Steps:
-
I want to decide if we want to keep the SMD components as they are or
change how they are placed. That being either we expand the size of the
boards to have them further apart, or we place the SMD components on the
underside.
- I also want to try optimizing the balancing LED placements so I can get them within a 200mmx70mm dimension rectangle.
-
After that I will work on labeling each of the modules so it clear what
module connects to what. For reference, everything is kind of placed
like this.

![](../../images/image_2653716778.png)

> **Aarjav Jain** (Jan 5)
>
> @Hemat Wander
> 
> - The isoSPI line will be too close to the analog measurements, thereby
> leading to noise in those voltage readings. Currently I'm thinking I
> will surround the voltage measurement (C1, C2, etc.) traces with a pour
> of the previous module voltage to create a stable "return path" and
> surround the isoSPI with a neutral pour "chassis" that isn't connected
> to the main circuitry in anyway.
> 
> - Also I have a possible concern for the schematic: will the TVS diode
> interfere with the algorithm of the buck converter as it serves as
> another diode pathway (although it is past the inductor as as opposed to
> L5.1). Ideally it shouldn't because VREG should stay ~5V with some
> ripple, however this was just a thought I had I thought I should write
> down.

> **Hemat Wander** (Jan 6)
>
> @Aarjav Jain
> -
> Your explanation of the neutral pour becoming an antenna makes sense,
> what I was thinking was to ensure that any return path coupling
> would occur on this neutral pour as opposed to one of the analog lines.
> Would the best way to do this be to fill everything with GND? What is
> FR4? @Aarjav Jain
> 
> -
> Sure I can investigate using 0603, however I will use that as a
> space optimization if required, as using 0805 components seems much more
> preferable for bring up.
> 
> - 120mmx120mm was a requirement
> we made based on the balancing LEDs needing to fit within the 70mmx200mm
> polycarbonate sheet on the control board, so 70x200 for both boards
> balancing LEDs is the absolute requirement. However I'm still figuring
> out how to best meet this requirement.
> 
> - Currently the TVS
> diode is rated for beginning breakdown at 5.5V and clamping at 14V.
> So the the leakage current at 5V-5.5V is max 10nA, so
> I think we should be fine in terms of leakage power.
> 
> ![](../../images/image_2661206276.png)
> 
> - The order of module connectors can entirely be based on the position of modules in the pack. ([See this update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4786943441)).
> However, I found that regardless of which order we place the
> module connectors, we have issues of wires going to modules on the other
> side of the board, and so it makes more sense to prioritize sensical
> ordering of the modules for clean routing and debugging, as opposed
> to for reducing wiring length. Does that make sense? @Aarjav Jain

> **Aarjav Jain** (Jan 12)
>
> @Hemat Wander yes makes sense. I had seen your update as well!

---

# Untitled

**Author:** Hemat Wander

**Date:** Jan 1

Begining PCB Layout:
I had to do some work cleaning up the footprints for each of the components.

- For the [SN74LV4052AQDYYRQ1](https://www.digikey.com/en/products/detail/texas-instruments/SN74LV4052AQDYYRQ1/25324537), I had to use the footprint + 3D model from [SN3257QDYYRQ1](https://www.digikey.ca/en/products/detail/texas-instruments/SN3257QDYYRQ1/12342989?s=N4IgTCBcDaIMoDkDMYCsB2AigEQJq4CVMBGEAXQF8g), as they have the exact same package (16-SOT-23 THIN) and the former did not have a 3D model/footprint available.

-
For the connector positions, I decided to have all of the first 8
modules on one side and the last 8 on another. This is just to simplify
routing for the autoconnection and balancing circuitry. I can justify
doing this as it is already quite impossible to have perfectly clean
wiring ([as discussed in this update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4786943441)).

-
I tried creating a layout with the autoconnection components that
would allow us to work without switching layers, however I got to a
point where doing so was no longer geometrically feasible. My concern
with the autoconnection circuitry, is that if we switch layers, there
will be some added inductance or capacitance of the lines that will stop
the circuitry from functioning as intended.

However as the
capacitance values are 10nF or greater, and the resistances are only up
to 10Megohms, the effects of routing changes should theoretically be
insignificant. The risetimes are on the order of milliseconds, and
therefore the frequencies should be fine. Thereby, the priority should
be ensuring that the analog signals (the voltage measurements) are as
straight and short as possible.

- Also need to keep in mind
we want to label the resistor values for the resistors in series with
the autoconnection circuitry diodes. As those resistor values will
change over time.

- I'm beginning to get concerned if it
will be possible to fit all the SMD components on one side of the board.
Everything right now is looking very tight. If we moved all the SMD
components to the other side of the board, and only kept the LEDs and
ICs on the top, it might work better. However, I will only look
into doing that if necessary.

- Also possible concern, will balancing current exceed the limits of the FET for the VGS we are operating at? [It says that](https://www.diodes.com/_files/datasheets/DMP2110U.pdf)
at 2.5V VGS voltage the max current is 2.5A, so we might have to look
into if at our min cell voltage, we are still in a good current
threshold.

> **Aarjav Jain** (Jan 5)
>
> @Hemat Wander Pack will fault at > 2.5V. Does this change the concern mentioned at the bottom?
> 
> "I'm
> beginning to get concerned if it will be possible to fit all the SMD
> components on one side of the board" -> As you found out, correct!
> 
> What do you mean by change the resistor values? And why will they change over time?
> 
> If 4 layers is genuinely not doable with our board size requirement we may consider a 6 layer PCB.

> **Hemat Wander** (Jan 6)
>
> 1.
> Ideally the current through the PFET will be fine, however it is kind
> of hard to tell from the datasheet, if the on-resistance of the PFETs
> will be significant at lower cell voltages. The concern here is that the
> on resistance is significant enough to affect balancing current
> noticeably or even the voltage readings. Since we are ideally only going
> to be balancing at higher voltages, it should be fine, but I haven
> noted this down as something to test with the in person testing
> circuitry.
> 
> [https://www.diodes.com/assets/Datasheets/DMP2110U.pdf](https://www.diodes.com/assets/Datasheets/DMP2110U.pdf)
> 
> ![](../../images/image_2661419786.png)
> 
> 2. The resistor values will change between each autoconnection **module**, and they vary gradually between 100k ohms and 4.32M ohms
> 
> 3.
> The layering of the PCB is not an issue, there is ample space for
> routing I think, the issue is fitting all SMD components on one side of
> the board.

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Connector Placement on Slave board:
Due
to the non-mirrored layout of the modules within the pack, it isn't
exactly obvious how we should place the moduleboard-slaveboard
connectors. There are a few different options we have, and none seems
particularly clean or ideal. We had a [brainstorming session previously](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.thxesxah3e4),
where we came up with some ideas of how to place the connectors. The
three types of board layouts we came up with is either

1. 4 connectors on the top and bottom

![](../../images/image_2648185868.png)

2. Connectors all towards the edge of the board, with the second board then having to be rotated.

![](../../images/image_2648187106.png)

3. A skinny PCB, with all of the connectors on one side.

![](../../images/image_2648188138.png)

If
we went with option #1, because there is no symmetry between the first
16 and last 16 modules, the wiring would have to be a little messy. That
means that we would have some wires crossing underneath the slave
board, and over from one side to another. I came up with one
possible option of placing the connectors below, however other options
would work as regardless of what we choose, it is going to be messy.

The
main benefit of this option is that the slave boards will be facing the
same way, meaning the balancing LEDs and other things we need to check
will also be facing the same way. I.e. its less confusing.

![](../../images/image_2648190997.png)

In
the above drawing, the numbers represent the module positions, and the
1/2 represents that connector connecting to module 1 and module 2.

Note: We
could further make this option "simpler" by having the first 8 modules
connect to one side of the PCB or on the other side. Doing this however,
would make the wiring more slightly messy and increase the overall
average length of wiring.

If
we went with option #2 we would be prioritizing lower overall wiring
length and slightly cleaner wiring. The main downside is that the PCBs
have to be rotated from one another, meaning it might be slightly more
confusing to look out (figure out where balancing LEDs are for), etc.
The other downside is that it's not exactly clear where we should plug
in each connector to the module boards as they are extremely out of
order. This just means we would need to label very well or used coloured
connectors.

Note that regardless of if we choose option #1
or option #2, we would have wires crossing over each other and under
the slave board. However this option will have slightly less so.

![](../../images/image_2648195550.png)

Finally,
if we chose option #3, I think we would simply have all the
connectors placed in order from module 1/2, module 3/4, etc. down the
length of the board. Again, the second PCB would have to be rotated
180 degrees from the first one, meaning it would again be confusing
when we are trying to figure out where to probe/which balancing LED goes
to what, etc.

Also there might be more wasted space on a
skinny PCB in terms of placing components, however I'm not entirely sure
about this.

I currently think we
should just go for option #1, with perhaps a change in the ordering of
the modules for each connector (but still having 4 connectors on top and
4 on the bottom). This would sacrifice wire cleanliness, but make the
board simpler to connect to the battery (as the connectors will connect
to the modules in order).

CC:

> **Krish D** (Dec 2025)
>
> There are two ideas that come to mind here:
> 
> 1. Is there a reason we should place heavy emphasis on the wires being in a mess?
> 
> -
> Of course elegance is partly the goal here, but practically, we won't
> need to be accessing the module boards often, since there there will
> only be passive components and connectors. Therefore regardless of
> if the wires are arranged well or not, we will have to interact with
> them the same amount in both cases.
> 
> - Increased length means a
> higher likely hood of snagging cables, however this can be mitigated by
> better wire management (ziptie-ing wires for example to the modules or
> in labelled bundles). Also, the same problem was present in the V3 pack
> when it came to the length of the harnesses having enough slack to get
> caught on things).
> 
> 2. Convenience of debuggability:
> 
> -
> Having longer wires at the expense of ensuring LEDs are aligned
> intuitively for debugging seems like a no-brainer to me. Since it is
> unlikely that the connectors will have to be taken off multiple
> times  (since we will have the SBTPCB to perform tests), the
> priority should be visibility.
> 
> For these reasons I agree that connector layout option 1 makes more sense to go with.

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Slaveboard Schematic Cleanup:
-
I added bypass headers for the autoconnection circuitry, so that we can
always use these if the autoconnection circuitry ends up not working.
These will work in the same way as they did on the previous slave board.
However, these headers can also serve as test points, meaning we can
remove the test points we already had for those two nets at each module.

![](../../images/image_2647935651.png)

![](../../images/image_2647941989.png)

-
For the Temperature circuitry, I only included test points for the MUX
selecting and MUX outputs. This is because I expect us to be able to
probe each individual temperature using the SBT (slaveboard testing
PCB).

![](../../images/image_2647942490.png)

- I also found an explanation for why we skip C_12 in the datasheet of the ADBMS1818 when measuring 16 cells. It explains on [page 86. of this datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adbms1818.pdf)
that we can either have all the unpopulated cells be at the end of the
last MUX (skip C_17 and C_18), or we can choose to skip C_12 and C_18.
Skipping C_12 allows us to "optimize measurement synchronization" by
equally distributing the skipped cells among ADC2 and ADC3. I'm not
entirely sure what this means, but since it was effective last time, and
I don't think it is that messy to skip C_12, I will keep it as it is.
Just note that we could skip C_17 if we wanted to. CC: @Aarjav Jain @Krish D

![](../../images/image_2647950836.png)

![](../../images/image_2647992690.png)

- I also added numbers for all of the components based on the schematic page (R2.5, etc.)

Next Steps:
- Auto-connection testing BOM/procedure
- Connector placement on the slaveboard

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Testing Auto-Connection Circuitry Plan:

During
the slave board schematic check-in we decided it would be a good idea
to perform a real-life test for the autoconnection circuitry, to see if
it is likely to be effective. The circuitry we will test with looks
something like the schematic below, where we will have 6 modules each
attached to a capacitor and resistor in parallel to simulate the
internals of the ASIC draining power. The overall goal is to be able to
see a >1ms time difference in the voltage charge-up between each
module.

<img src="../../images/image_2642837914.png" width="658" height="418">

How will we construct this:
As
mentioned, we will use a solderable breadboard with all of the passive
components seen (resistors, capacitors, diodes and PFETs) being SMD
components. For the cells, we will use power supply's to effectively act
as separate voltage sources. For this reason, we would need at least 6
separate power supply outputs for this to work. If not, we would have to
use a fewer number of modules (I put 6 because I remember us
having 6). How many power supply's do we have @Aarjav Jain @Krish D ?

What is the point of this test?

As
this circuitry is a little complex, and relies on very extreme values
of resistances and currents (megaohms and microamps), along with the
variable threshold voltage of the PFETs, we want to test that this
circuitry behaves as we expect from the simulations.

In general,
we will bring up this circuitry (all of the components seen) on a
solderable breadboard, and then test using an oscilloscope to compare
the voltage across each adjacent capacitor, to see if they charge up one
after another. Specifically, we will perform at least 5 different
tests, where we either compare module 1 and 2, module 2 and 3, module 3
and 4, etc. On top of that, we would also likely want to compare
gate-source voltage waveforms for neighboring modules. Note that I'm
saying we can only compare two voltages at a time, because the
oscilloscope only has 2 input channels.

To make it crystal
clear, we would be having each oscilloscope channel across one of the
capacitors, that we would normally have connected right before the
ADBMS1818 (the 10nF capacitor).

As I haven't really
tested such a small time-scale transient before, we will have to figure
out how to properly trigger and capture waveforms of this sort. I wrote [a doc](https://docs.google.com/document/d/1MV-YpjvpVpQkrTj-ODzY-dOq-oSJA0L8ceQa_oe5DN4/edit?tab=t.0) that may help with this.

In general there are only a few things that we could imagine being different between the simulations and real world behavior:

Thus,
on top of getting waveforms for the voltage across the capacitors, we
would be on the lookout for seeing in what range the values are off from
expected simulations (if it works at all). Furthermore we would also
want to test some of the extremes mentioned in the [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4780498486), so changing some of the power supply voltages, and seeing how the waveform behavior changes (time wise and voltage wise).

Change to Timelines:
Doing
these tests doesn't necessarily mean we have to delay the design
process (since I can't test since I'm back in January), however we would
have to delay ordering the PCBs by necessity, to have the tests inform
if the circuitry works. Thus, when we come back on the week of Jan 5th,
if we could ideally get started testing and complete by the 20th. Then,
if everything works as expected, we can order the PCB now by the 20th.
This is of course later than we were expecting before.

However
regardless, the PCB should ideally be routed by the time we start doing
all this testing, so that we are good to order if everything works. How
would this sound @Krish D @Aarjav Jain

> **Krish D** (Dec 2025)
>
> @Hemat Wander
> 
> **Technical questions/notes:**
> 
> -
> We have a 6 power total power supplies that we can use. Keep in mind
> though that this would make the wiring of your setup quite tedious and a
> pain to deal with safely. Is using the resistor ladder divider not
> a feasible option?
> 
> - For the setup itself, how many points need
> to be probed at any given instance? Did you plan out where the test
> points would need to go in this case? A circuit diagram on the
> breadboard itself (similar to what @Christopher De Lazzari has made the pre-charge check circuitry would be ideal).
> 
> -
> I don't think we should have any issues with looking for the transient
> since it will be on the order of <1ms, so the procedure you outlined
> in the ISO-SPI test plan doc seems reasonable to work with.
> 
> - I'd
> like to see a more specific test plan and bring-up plan that outlines
> what points are going to be probed and in what order (since timing
> between capacitors charging is of great importance here).
> 
> **Timeline:**
> 
> -
> I don't see this impeding slaveboard-masterboard testing timelines,
> however I do believe the testing will not take longer than 3 work
> sessions (you've specified a total of 5 @Hemat Wander)
> Unless you for see some failure modes that prevent you from obtaining
> the ~1ms gate-source voltage becoming <= -1.0V AND have a plan for
> how to remedy this (replacing specific resistor or capacitor values),
> than I can't imagine that probing and iteration will take much longer.
> 
> - @Aarjav Jain I'm
> ok pushing timelines for ordering the slaveboard by around 5 days if
> you don't for see any challenges that come with this.

> **Hemat Wander** (Dec 2025)
>
> @Krish D
> -
> Using a resistor divider ladder will absolutely not work, as the
> voltages will changes based on current draw (which doesn't emulate a the
> real circuit being cells in series)
> - I could imagine wanting to
> probe everywhere around the circuit to see voltage drops across the
> various components. However, if we want to have test points for places
> where we will be probing often, then I think we should have test
> points at the gate, source, and drains of the PFETs
> - Sounds good,
> I think it would be better to make the test plan after we order the
> components because we should order ASAP.
> - I'm putting 5 work sessions as a safety net, as in person testing usually always has some complications related to it.

> **Krish D** (Dec 2025)
>
> @Hemat Wander
> 
> Sounds good. Please add a small diagram showing where the test points should be placed then on a perf board for greater clarity.
> 
> Can you please make a BOM for the autoconnection circuit as your next steps? In the meantime, @Aarjav Jain please note I've changed the SB bring-up timeline to account for testing time.

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Auto-connection circuitry Update #6

After a [check-in meeting on Sunday](https://docs.google.com/document/d/1pZTixNz-3UK0dogTyN2dd9UEFnAjusMHCIIedliVVPU/edit?tab=t.i0w8rp6cxwn2),
we realized that we only performed simulations for the scrutineering
circuitry under the condition that the cells were at 4V. Thus, we should
test the simulation under different voltage conditions.

First
I tested under the cells all being at a minimum voltage we can
expect plus some safety threshold of 0.1V, giving us 2.4V. This is
based on the cells having a minimum of 2.5V, so its likely we won't go
under 2.6V. Under these conditions I found that the gate-source
voltages of the PFETs were at -1.4V and below while the PFETs are closed
(conducting). In comparison, I found that if the cells were all at 4.3V
(0.1V safety threshold over maximum voltage), then the gate source
voltages hover at around -2.7V and below.  (Both charts are shown
below).

<img src="../../images/image_2642812551.png" width="680" height="312">

<img src="../../images/image_2642812946.png" width="678" height="314">

As
the max threshold voltage is only -1V (with -0.4V being the minimum),
we find that even in the worst case for all cell voltages, we are still
over the gate source threshold (so it will theoretically still work
then).

Testing with a lower voltage unbalanced cells:
Other
than testing with all of the cells being at different voltages, we
should also test for there being a reasonable imbalance between the
cells and how that would affect this circuitry. Lets begin at an extreme
to see the behavior. To begin, we can try testing module 5 being
at a lower voltage than the rest of the cells (mod 5 = 2.5V, and mod
1-4,6-16 = 4.0V).

If we look at the gate-source
voltage curves, then we see that the first 4 voltages behave as
expected, but then every voltage after module 5 is much higher (less
negative), meaning that the rest of the PFET gate-source voltages are
pushed upwards because of the one faulty cell. Furthermore, we find that
instead of the first module settling at the lowest (most negative) gate
source voltage, and the rest of the modules being at slightly higher
(less negative) gate-source voltages, we actually see the opposite
pattern, due to module 5 being at a lower voltage.

<img src="../../images/image_2642816620.png" width="673" height="313">

If
we look to the input capacitor voltages (to see the order they fill up
in), we see that again, the first 4 modules fill up in order, but then
after that it gets a bit sketchy. Namely, we see a long delay between
module 4 and 5, and then after that, a lot of the modules seem to fill
in right after one another, and then we finally see the last few modules
filling up with a proper space between them.

<img src="../../images/image_2642819586.png" width="626" height="287">

If
we zoom in, we find that modules 5-10 fill in in a slight reverse
order, meaning that module 10 fills in before module 9, and so on down
to module 5.

<img src="../../images/image_2642820876.png" width="641" height="308">

I
originally assumed this was bad because the modules are filling in out
of order (meaning for example module 7 will be filled slightly before
module 6). However, we need to back up for a second. From first
principles, what we are looking for is that nothing breaks the max
thresholds of the ADBMS1818 (in terms of max voltage between inputs or
max current through the internal ESD diodes). In terms of the current,
we find that the internal EDS diodes current stay around 22uA max, which
is well below the threshold of 10mA. This is because the capacitors
fill up so close to one another, that they are practically filling up at
the same time.

<img src="../../images/image_2642821636.png" width="647" height="298">

For
reference, if we plug module 5 in first without plugging in the
previous modules first, we get a 81mA drop across the internal ESD
diodes (way over the threshold). This would be an example of what it
would look like for us to break the ADBMS1818 from a simulation
perspective.

<img src="../../images/image_2642823170.png" width="668" height="318">

If
we now test the opposite case were module 5 is overfilled to 4.1V,
while the rest of the modules are at 2.7V, we get some more sketchy
behavior. This time the gate source voltages of the first few modules
are relatively low because of the 2.7V cells, however the 4.1V cell
makes the 5th module gate-source voltage drop way down to -3.0V, meaning
that all of the modules passed it overlap with the initial 4
modules.

<img src="../../images/image_2642823644.png" width="682" height="317">

I was
expecting that this would mess the timing of everything up for the
connecting stage, but surprisingly, everything seems to still connect in
order. likely due to the behavior very early into the gate-source
voltage curve.  Furthermore, if we look at the current at the
internal ESD diodes, we see that it says in the nA range (well below the
threshold).

Finally,
if we look at the disconnecting stage for this unbalanced case, we
somehow miraculously see that the modules still disconnect in the
correct order (last->first). I'm honestly not sure how this is
working, but it does seem to be working.

We
find that for the simulation, even under different voltage conditions
for the cells (with the cells being in the 2.5V-4.1V range) or with
there being an imbalance with some cell at a radically different
voltage, we still find that even if the charge up behavior is a little
sketchy, we find that the order of the connections is expected, or
otherwise the current of the internal ESD diodes stays well within
the thresholds. Thus, the circuitry still looks safe from this
perspective.

> **Krish D** (Dec 2025)
>
> @Hemat Wander Amazing
> update! I'm glad you considered every edge case and defined from first
> principles if the discontinuities in proposed behavior is significant
> for causing damage to the ADBMS1818.
> 
> Can we finalize the design of the autoconnection circuitry as it stands and begin testing?

> **Hemat Wander** (Dec 2025)
>
> Yes,
> everything seems good for this being the finalized design for the
> autoconnection circuitry, and so we can test accordingly.

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Auto-connection circuitry Update #5

Going on from [this update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4682578880).

Context:
To
give some clarification of what the circuitry looks like, we have the
following circuitry at each module (3 modules interconnected are shown).
The PFET is what controls the switching from cell to the ASIC.

![](../../images/image_2635212753.png)

The
top resistance is 100k for every module, but the resistance in series
with the diode is different for each module. The first 8 modules
all use 100k ohm resistors, but after that I found we have to
steadily increase the resistance (220k, 470k, 680k, 1Meg, 1.5Meg,
2.2Meg, 3.3Meg, 4.32Meg). (@Krish D ,
adding these different resistance values is what I found to have
"fixed" the simulation to get it working). I'm not entirely sure why
these values work, but they seem to work based on the simulation.

SPICE simulations
Now
we can return to the spice simulations. The chart we see below compares
the gate-source voltages for each of the 16 module PFETs. At t=1
seconds we connect the jumper and at t=2 seconds we disconnect the
jumper. We expect that when we connect the jumper module 1 is the first
to connect and module 16 is the last to connect. When we disconnect the
jumper we expect that module 16 would be the first to disconnect and
module 1 would be the last to disconnect. This does in fact seem to be
the behavior we get. Note that we also get that the gate source voltages
for the PFETs differ a bit between each module (-2.4V -> -4V),
however they are all under the gate-source threshold in the datasheet of
-1V.

<img src="../../images/image_2635176755.png" width="675" height="162">

<img src="../../images/image_2635107523.png" width="626" height="67">

We
can also plot the voltages across each of the input differential
capacitors. This now directly shows the voltages being input to the ASIC
across each of the capacitors directly attached to the LTC inputs. The
first image shows them being connected, and we see that they turn on in
order, but the time difference between voltage rises is anywhere from
0.01ms - 1ms. The second image shows them disconnecting, and we find
that they disconnect in exactly the order we want (last-first). In other
words, this means it technically works.

<img src="../../images/image_2635121349.png" width="676" height="161">

<img src="../../images/image_2635120131.png" width="667" height="153">

Increasing Capacitance
As suggested by @Krish D and @Michael Lin,
I tried increasing the capacitance value of the capacitors to
increase the time between connections, and by switching from 10nF
capacitors to 1uF, we get the following results. The connecting part
looked very promising, with us getting at least 4ms between connections,
even with the bunch of modules connecting one after another in the
middle.

<img src="../../images/image_2635129115.png" width="601" height="143">

However,
the disconnecting part is less great, as we are using 10Meg ohm
resistors for pullups (to try and not disrupt the circuitry), we get
that with 1uF capacitors, the time constant is much longer (1uF
* 10Meg = 10 seconds), meaning we would have to wait at least 30
between disconnecting the jumper and unplugging the connectors, which
might be tedious in a time-crunch scenario. What are your guys thoughts
on this @Krish D @Michael Lin ?

The
voltages here again represent the capacitor voltages input to the ASIC.
We connect the jumper and see the voltages rise up fairly quickly,
however if we disconnect the jumper (at t=10 seconds), we see it takes
until t=40 seconds for everything to fully disconnect.

<img src="../../images/image_2635144903.png" width="660" height="147">

So
in general we see that increasing the capacitance, doesn't majorly
effect the connecting stage (as it is already in the ms range), however
it will affect the disconnecting stage in that we will have to have an
additional step in the procedure to wait longer before doing anything.
Note that we can also have any other resistance value in the 10nF-1uF
range. Calculating the time constant for the disconnecting would just be
from t  = 10^7 Ohms * capacitance. So a 100nF capacitor would
have a 1 second disconnecting time constant. This currently seems like
the best option so we only have to wait a few seconds (less chance for
error). I will stick with using 100nF for now. This gives us at
least 1ms between each connection occurring, and we only have to wait
~3seconds for the FETs to discharge when disconnected.

<img src="../../images/image_2635181166.png" width="681" height="168">

Something
to note here is that we technically have no idea how long it will take
for the capacitors connected to the ASIC (not the FET capacitors) to
discharge, because we don't know the shunt resistance internal to the
ASIC. However, this information shouldn't affect us, such as for our
current slave boards, where once we disconnect the module jumpers, we
technically don't know how long it takes for those capacitors to
discharge.

Components used in simulation:
Also
I should specify the components used in simulation, and how well
they match real components. For the diode I used a 1N4148 model in
LTspice, and for the actual schematic I am using
the 1N4148WX-TP, so it should be similar. For the PFET I'm using a
default model with a 20V gate source max voltage and a 0.8V threshold
voltage, so essentially something in the same range as our PFETs.
I don't think its necessary to find an exact PFET model, as this
design should work for a variety of PFETs.

<img src="../../images/image_2635191076.png" width="682" height="335">

Next Steps for auto-connection circuitry:
We
discussed in person if performing tests for this circuitry is a good
idea before ordering the PCB. Originally I was not sure
because of how much time it might take to perform these tests. However I
think that performing these tests might be helpful if the behavior is
just completely off of what we expect. We would have to make a mock
breadboard to see if the voltages for the PFETs are within the
correct range, and each adjacent group of modules are activated at least
1ms after each other. The other issue is that it would require 16
voltage inputs to plug into the PFETs, which is what the slaveboard
testing PCB was originally for. For the last reason alone, I don't think
we can perform the test. I considered performing a test with only a
few modules and seeing if it works, but in simulation I found the
timing is highly dependent on the number of modules used.

Currently
it seems the most feasible option is to just order the board and see if
it works, by first only soldering in the autoconnection stuff, and
testing using the testing PCB. Then if it doesn't work, we have to order
another PCB. @Aarjav Jain  @Krish D what are your thoughts on this?

Also, me and @Krish D
discussed implementing FEs autoconnection circuitry in SPICE and
testing it. Should we do that? I don't know what the solar standard
for this scenario is, because it doesn't feel right to just use what
they use? What are your thoughts on this @Aarjav Jain

Next Steps before schematic check-in:
- Schematic cleanup, including net names and note colors, other standards, etc.
- Modify buck converter circuitry including inductor and adding proper TVS diode
- Check datasheets for integration points between components
(ensure multiplexers are properly pulled up / down, and are analog not digital)
- Add DNP common-mode choke capacitor.

> **Hemat Wander** (Dec 2025)
>
> Here is the LTspice file, for everyone else to check out. [Auto_connect_experimenting.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2635219958/Auto_connect_experimenting.asc)

> **Michael Lin** (Dec 2025)
>
> I
> think the 30s delay constraint might make operation more complex
> similar to how the "connecting in-order" constraint makes V3's board
> complex to operate. (If someone forgets to wait 30s before starting to
> disconnect the modules out-of-order, they'll cook the board, right?)
> 
> Maybe
> as a remedy to this, we can add one indicator LED at each module (or
> maybe just at the last module to disconnect?) so that we have light(s)
> that slowly fade away after disconnecting. This can indicate when it's
> safe to unplug stuff

> **Hemat Wander** (Dec 2025)
>
> @Michael Lin
> The
> issue with LEDs is that the circuit is going to be plugged in all the
> time, so we don't want to have a high quiescent draw source (LED) always
> lit up due to the circuitry.

> **Krish D** (Dec 2025)
>
> @Hemat Wander
> 
> Is it not feasible to test with 4-6 modules on modules on a breadboard?
> 
> I don't see the need to make all 16. We are looking for a general behavior since they are more or less functioning the same.
> 
> What are your thoughts though?
> 
> CC: @Aarjav Jain

> **Hemat Wander** (Dec 2025)
>
> @Krish D
> 
> In
> the past, when I tried simulating with 8 modules, I found that the
> timing behavior was very different, in that the first 4 modules had
> increasing time constants, while the last 4 modules had decreasing time
> constants. Essentially meaning that how close the module is to the
> beginning or end will decrease its time constant. Therefore,
> behavior with a different number of modules will behave very
> differently.
> 
> I can try simulating in SPICE what it
> would look like to use say 4-6 modules (what resistance values we would
> have to use), but just note it would be different.
> 
> Does that make sense?

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Space taken up by LEDs on the slave board:

One of the requirements for the control board (@Samuel Shin ) is
deciding how much space will be taken up by the LEDs on the slave
board, and therefore how much room on the control board needs to be
reserved for polycarbonate.

Going from [this update chain](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4710587125),
we know that the slave board will be approximately 120mm x 120 mm (max
dimensions). This increase in size is both because we are increasing the
number of passive components, and also because we are trying to ensure
all the passive components are on one side of the PCB. This is mostly
for ease of soldering, so we can reflow-solder all of the components on
one side.

With that in mind, the circuitry for the the new
slave board revision has a few more components being added in the chain
of going from connector to ASIC. Approximately we have. The fuses and
autoconnection circuitry is a new addition.

Connector -> Fuse -> Autoconnection Circuitry ->  Balancing -> RC filter -> ASIC.

Note
that the last 3 stages are the same as previously. This indicates that
the space taken up by this circuitry will be approximately the same as
previously. Although we will no longer have module jumpers, we will
still have HV test points (for each module) and on-top of that we will
have additional autoconnection circuitry between the connectors and
balancing.

All of this is to say that the width taken up by
the balancing LEDs and other resistors will be approximately the same
as before. However, the height may differ based on how much additional
space is required for the auto-connection FETs. Based on this, if we
want to keep all of the components on one side of the PCB, we might need
to further increase the width of the PCB to 130mm x 120 mm.

Regardless,
the space maximum for the LEDs will be 100mmx100mm. This is to give
space for whatever additional height we will need. Note that the width
across is technically only 70mm between balancing LEDs, however
I think that based on how the routing changes, additional width may
be required.

![](../../images/image_2602699713.png)

> **Hemat Wander** (Dec 2025)
>
> From the [last DR1 meeting for the control board](https://docs.google.com/document/d/1nH0ZoBw_3RXaa47jVCRjyzZTOelWsJcVV9dLKlmtVYE/edit?tab=t.iod93ixo74hc),
> we decided that we are going to be having the polycarbonate panel be as
> small as possible. Thus, we are going to be using a width of
> 70mmx200mm. As mentioned, the minimum width for the slave board LEDs was
> ~70mm. And then we would have ~100mm per slave board in the window,
> meaning that the LEDs will likely be more centered toward one side of
> the board (as they are ~120mm each).

---

# Untitled

**Author:** Hemat Wander

**Date:** Dec 2025

Auto-connection circuitry Implementation #4
Going on from the [previous updates](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4682578880),
I realized that the resistance values we were using was much too
low for our application, and so the quiescent current would be too high.
I originally was thinking that I could increasing all of the
resistances (say by a factor x100) and then call it a day, however, I'm
weary about increasing the resistances so high all the way to 100
Megaohms, as there could be parasitic resistance effects from the PCB
itself + other components. I'm somewhat arbitrarily going to say
that have 10Megaohms is a good maximum resistance value for us before we
have to consider extremely strange parasitic behaviour.

With
that in mind, I had to play around with the resistance values
again. The goal was to get 100 kohm resistors between each module, which
would get us to microamps of quiescent draw. After playing around with
the resistor values for a while, I got to a point where all of the
voltage values in the input to the ADBMS1818 are safe (don't spike to a
high value), and the FETS.

I have attatched the file here: [Auto_connect_circuitry_test.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2594065879/Auto_connect_circuitry_test.asc)

I have also changed the schematic accordingly.

> **Aarjav Jain** (Dec 2025)
>
> @Hemat Wander

---

# Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** Nov 2025

@Michael Lin Great list to keep up with! Thank you for creating this!

@Hemat Wander Please
be mindful of this doc as you finalize the schematic and begin
layout/routing for the slaveboard. It would be useful to consider which
tests need to be done and justify them to this doc, while also
considering where you could add test points on the slaveboard to achieve
them.

The update was originally posted on subitem Slaveboard-Masterboard Testing on 12-01-2025 at 02:04 by

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Deciding on Max Dimensions of Slave board:
We
wanted to decide on a max dimension for both of the slave boards, and
also the general layout within the slave boards. There are two options
we have for the layout. Either the vertical option (seen below, which is
what we have in our current pack) or the horizontal option (seen on the
right).

<img src="../../images/image_2586401258.png" width="302" height="282">

<img src="../../images/image_2586401626.png" width="301" height="281">

In
terms of determining the max slave boards dimensions, the connectors
are the limiting factor. Lets assume we are using 4-pos connectors, as
I think this will take more space than the other option of using
8-pos connectors, (thus giving us a bigger MAX dimension).

<img src="../../images/image_2586406755.png" width="273" height="297">

Thus,
if we assume that the space taken up by all of the connectors is 9.6mm
+ 2.5mm for width between, then we have ~12 mm per connector.
Assuming we have 8 connectors on two sides of the slave board, the width
taken up by connectors would be 8x1.2=9.6 cm.

We then, would
also have 1 extra centimeter on either side of the control board due to
the mounting holes (assuming we use the same size). The total width is
9.6cm + 1cm  + 1cm = 11.6 cm -> take 12 cm.

![](../../images/image_2586406608.png)

If
we take a square area the approximate dimensions of the slave
board would be 120mm x 120mm which is compared to the original
100mm x 100mm. This is a a 44% area increase.

However, we
can just make the slave boards slightly rectangular to save area, as on
the current slave board we still have enough space for the other
connectors we would need (isoSPI, mock-scrutineering,
etc.).  Thus, we can take 120mm x 100 mm. (20% area increase
from previous revision).

![](../../images/image_2586413775.png)

In
terms of placement in the pack, having an horizontal orientation would
be preferable for minimizing the distance between the modules and the
slave board (decreasing wire length).  The limiting factor for
this is that the current iteration of the control board has more
empty space in general towards the center, so doing something like below
would be slightly problematic (this again depends on the exact
dimensions, so we will confirm when we get those).

![](../../images/image_2586416417.png)

CC:

> **Krish D** (Dec 2025)
>
> @Hemat Wander Below is my thought process for assessing the feasibility of your chosen position for the slaveboards:
> 
> -
> I originally believed that it will be difficult routing wise to
> ensure that all LEDs can be kept in one block/grouped together. This
> will involve many vias and could become quite annoying to deal
> with, ***assuming you don't want to route across any of the power layers.*** This
> is why I'd suggest keeping the LEDs where they are currently with
> regard to being next to each connector, and instead moving closer
> towards the center of the slaveboard (think a narrow column of LEDs that
> are on both sides of the ADBMS1818). However, this assumed that from [Sam's latest update](https://ubcsolar26.monday.com/boards/7524367617/pulses/7524367914/posts/4710656665), that you are choosing layout #2 referenced in my last reply.
> 
> ![](../../images/image_2587747538.png)
> 
> -
> The other option is to route across the power layer, as currently on
> Brightside slaveboards, there are no traces on it! This would be an easy
> solution, I can believe this wouldn't contribute highly to
> EMI since the slave board has such low current draw, and having
> such a large GND plane will keep the continuous analog signals stable,
> as long as none of the balancing traces are being routed below the
> ADBMS1818.
> 
> ![](../../images/image_2587747343.png)
> 
> Please let me know your thoughts
> 
> !

> **Aarjav Jain** (Dec 2025)
>
> @Hemat Wander
> 
> CC: @Krish D

> **Gurman Khella** (Dec 2025)
>
> @Aarjav Jain The
> chosen Minifit Sigma connectors are tin plated, so they are rated for a
> mating cycle of 30. The gold plated sigma connectors have a mating
> cycle of 250. For the gold plated connectors, I will have to find the
> specific combination of specific parts of the sigma series for this
> rating. Sometimes the datasheets for the gold-plated specific components
> also says 30, which is misleading with the initial datasheets, so I
> will have to confirm the specific components. Also, a note,
> gold-plated is more cost than tin-plated

> **Krish D** (Dec 2025)
>
> @Aarjav Jain I
> expect with our more recent changes (moving passive components to
> slaveboard), we shouldn't be messing with the module boards as often as
> we thought. The only times we needed to remove the connector from the
> cell boards on V3 was for pack disassembles and mod 32 for
> scrutineering, however this shouldn't exceed more than 30 times over the
> pack's expected 2 year life cycle.

> **Aarjav Jain** (Dec 2025)
>
> @Krish D That is true. Although I would like to see the cost and part number that @Gurman Khella is mentioning for higher mating cycles.

---

# Untitled

**Author:** Aarjav Jain - Electrical Director

**Date:** Nov 2025

**I have start a doc**
to list potential tests that we'd like to do. We can also add the
actual test procedures to this doc in the future (under different
document tabs)

**[https://docs.google.com/document/d/1R-2-kh3UOMEi8B_aRGCaqyDrYEIhD4hJOsgBoEB7tsM/edit?tab=t.0](https://docs.google.com/document/d/1R-2-kh3UOMEi8B_aRGCaqyDrYEIhD4hJOsgBoEB7tsM/edit?tab=t.0)**

**There are current 2 tests listed**: measuring voltage amplitude & noise on the IsoSPI line, and testing the newly-added selfchecks

**Next steps**
are to continue adding more tests to this doc as needed. We should also
specify a date when we should finalize all tests to carry out (and
write their procedures) before we finish bringing up the master and
slave boards.

The update was originally posted on subitem Slaveboard-Masterboard Testing on 11-29-2025 at 19:27 by

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Scrutineering Test Circuitry:
Going on from [this update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4693728576):

The
purpose of this update is to flesh out everything a little more by
deciding on what connectors we will be using. Some initial notes:
- We can use this component for the HV switches: [LCC110](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/LCC110/203121), but its quite expensive for the other switch, thus we can use a lower voltage switch
- I also noticed when looking on Altium that SPST HV switches are much cheaper ($2) compared to the SPDT HV switches ($8).

Context:

I found this helpful link for comparing the types of relay options and their uses: [https://www.ni.com/en/shop/electronic-test-instrumentation/switches/what-are-switches/how-to-choose-...](https://www.ni.com/en/shop/electronic-test-instrumentation/switches/what-are-switches/how-to-choose-the-right-relay.html?srsltid=AfmBOordm7XDt2c3-Vl7vdlsFEA5voivAnfCYn-E7SGv4DCl80mvb6FS)
-
Electromechanical relays are less expensive on average, ($2) for SPDT
compared to SSD which is ($8) for SPDT. However, they are bulkier,
meaning bigger size and more coil current required.

- Reed switches are used for high speed switching applications, and are generally less robust, which we don't really need.

-
SSD relays seems to be the go-to choice for the HV switches we are
going to be using, the only downside is that they are a little expensive
(especially for SPDT compared to SPST).

- For the LV Tense switch we can also look at analog FET switching options, that essentially serve as Muxes.

Goals:
- We want switches that are safe in that they provide high isolation resistance when not on.
- Want them to be relatively cheap
- Want them to not take up too much space on the slave board

Required Switches:
-
We need a HV SPDT switch for connecting the B+ of the C18 input to
either the in-pack module, or to the external scrutineering module
voltage
- We need a LV SPDT swithc for connecting the T_sense line of the last module to the external module or in-pack module
-
We need a HV SPST (or SPDT if cheaper) for connecting the B+ of the
31st module (B- of the 32nd), to either be floating or to be charged.
Purpose is for connection to scrutineering outside of the pack.

Some Options:

- [J1031C5VDC.15S](https://www.digikey.ca/en/products/detail/cit-relay-and-switch/J1031C5VDC-15S/14002065),
this SPDT electromechanical relay is $2 and rated for 60V, meaning it
is a possible option for the Tsense line. The only downsides are that it
is quite big (1.2cm x 0.7cm and 1cm tall), and that it draws a high
amount of coil current (30mA)

- [1462042-8](https://www.digikey.ca/en/products/detail/te-connectivity-potter-brumfield-relays/1462042-8/2126945),
this SPDT electromechanical relay is $7.11 and rated for a 200V load.
It would be a good option for the B+ SPDT switch if we want a high off
insulation-resistance solution.

- [EE2-5NU,](https://www.digikey.ca/en/products/detail/kemet/EE2-5NU/4291122) DPDT electromechanical relay, costs $3.06 and takes 28mA of supply current. Could be used for both the B+ and B- connections.

- [EE2-5SNU](https://www.digikey.ca/en/products/detail/kemet/EE2-5SNU/4291123) DPDT relay similar to previous one, but is latching relay (meaning doesn't require continuous current draw, and costs $3.62

- [LCC110](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/LCC110/203121),
high voltage SPDT switch, costs $7.40. Only draws 2mA of control
current. Could technically be used for all 3 switches, but will not due
to the price. Because it is SPDT, we can connect both the normally open
and normally close pin for our purposes, without needing to rely on
using more switching circuitry.

- [SN74LVC1G3157DCKR](https://www.digikey.ca/en/products/detail/texas-instruments/SN74LVC1G3157DCKR/562895),
2:1 MUX (SPDT) which we should use for the T_sense line. Costs $0.43,
so I think it is the best option for this LV application.

- [CPC1008NTR](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/CPC1008NTR/655286)(SPST-
NO), a single throw SSD switch that costs $2.49 and has 2mA of supply
current. Could be used by itself for the B- connection. If being used
for B+ connection, needs to be used in conjunction with another relay
since it is SPST. Has 8 ohms of resistance (note that this is quite high
in reference to the 10 ohm balancing resistance).

- [CPC1125NTR](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/CPC1125NTR/4971412)
(SPST-NC), a single throw SSD switch. Costs ($2.45), and has 2mA supply
current. Could be used in conjunction with the above switch for the B+
connection to reduce cost.

So what should we use?:
For the T_sense line, we should definetly use the [SN74LVC1G3157DCKR](https://www.digikey.ca/en/products/detail/texas-instruments/SN74LVC1G3157DCKR/562895) mux since its cheap and small.

For the B+ and B- lines we have a few options.

If we prefer a more compact but cheap solution, we can use the [CPC1008NTR](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/CPC1008NTR/655286) SSD relay for the B- connection and [LCC110](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/LCC110/203121)
for the B+ connection. However, this will be a little expensive
($9.50), and will have some additional contact resistance (15-50 ohms on
each side) meaning balancing will be off, at least for the B+
connection. These would only draw 2mA, and that too only during
scrutineering.

If we want a bulkier solution, we can use electromechanical relays. Either with the [EE2-5NU](https://www.digikey.ca/en/products/detail/kemet/EE2-5NU/4291122) non-latching relay, or with the [EE2-5SNU](https://www.digikey.ca/en/products/detail/kemet/EE2-5SNU/4291123) latching relay. Both of these would cost ($3-$4) **for both **switches
together, but would draw 20-28mA at peak (during scrutineering), and
take up more space on the slave board. One benefit is that the switching
resistance would be smaller than in the SSD case. An issue with this is
that it will generate some EMI during switching, however this should
only be an issue during scrutineering?

**Important note.
These currents (2mA-20mA) would be drawn directly from the VREG line
through a mosfet that we would control from a GPIO. The GPIOs themselves
cannot support that much current draw. **

CC: @Krish D @Michael Lin **What are your thoughts?

> **Hemat Wander** (Nov 2025)
>
> I was
> initially going to go with the most compact solution of the Solid State
> Relays. However, for the case of the B+ connection, the solid state
> relay would introduce too much resistance in the circuit for the
> normally closed (NC) connection (35 ohms), which is way too high
> considering balancing is 10 ohms.
> 
> Thus, for now I'm going
> to implement the circuit with the DPDT electromechanical relay. However,
> we might want to reconsider this in the future, given the higher
> EMI.

> **Hemat Wander** (Nov 2025)
>
> After discussing with @Krish D
> , we realized that we can just put the solid state relay after the
> balancing setup, as scrutineering doesn't have to worry about balancing.
> Then, if we set the RCfilter to be 68 ohms, the accuracy won't be
> harmed by much.
> 
> Thus, for now, we can stick with using solid state relays for both the B- and B+ connections.

> **Michael Lin** (Nov 2025)
>
> After
> discussing with these guys, we'll email the scrutineers again to
> confirm this. We're pretty certain this will be an okay implementation,
> but it wouldn't hurt to ask.
> 
> See original email chain:
> 
> [https://mail.google.com/mail/u/1/?ogbl#search/fwd+scrutineer/FMfcgzQcpnJldNxDcGrHMcFCkDpQHFTk](https://mail.google.com/mail/u/1/?ogbl#search/fwd+scrutineer/FMfcgzQcpnJldNxDcGrHMcFCkDpQHFTk)

> **Michael Lin** (Nov 2025)
>
> The draft email is now saved in battery email drafts. Please have a look @Hemat Wander @Krish D @Aarjav Jain !

> **Krish D** (Nov 2025)
>
> Hey
> folks, I just made a large lapse in judgement since I forgot we have 2
> other cell inputs (ADBMS1818 has 18 cell inputs, not 16). Please take a
> look at [this](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4693728576?reply=reply-4703170274)update for a revised implementation strategy.

---

# Untitled

**Author:** Michael Lin

**Date:** Nov 2025

**Component selection** for IsoSPI connectors and Mux

**Note that these components are not added to BOM**. I will do so after finalizing these choices

**IsoSPI line**

PCB Header: [Digikey page](https://www.digikey.ca/en/products/detail/molex/1726480102/9352770)

Connector receptacle: [Digikey page](https://www.digikey.ca/en/products/detail/molex/0039014020/6822885)

Female crimp: [Digikey page](https://www.digikey.ca/en/products/detail/molex/0039000039/61448)

**Multiplexer: **[TI’s SN74LV4052AQDYYRQ1](https://www.digikey.ca/en/products/detail/texas-instruments/SN74LV4052AQDYYRQ1/25324537)

**Related changes**

The required firmware changes to implement the new mux config should be pretty straight forward:

> **Hemat Wander** (Nov 2025)
>
> @Michael Lin
> Looks good for the multiplexer.
> 
> For
> the iso-SPI connector, I think we should use a vertical header as it
> will be going up through the control board. However this entirely
> depends on the pack geometry @Deev Shah. Either way, the male connector and crimps can stay the same

> **Aarjav Jain** (Nov 2025)
>
> @Krish D @Michael Lin: Please check the wire in the ELEC inventory. Ensure twisted pairs are used where needed.

> **Krish D** (Nov 2025)
>
> @Michael Lin I
> remember you drew out the connections of the 8:2 MUX. Adding this
> diagram here would make it more clear what you are refering to, since it
> isn't clear what factors (the connections from the ADBMS1818 GPIOs
> in particular) are being used to determine the proper input/output
> ratio <- also the logic for them as well.

---

# Untitled

**Author:** Krish D

**Date:** Nov 2025

[@Hemat Wander](https://ubcsolar26.monday.com/users/66767094-hemat-wander) [@Aarjav Jain](https://ubcsolar26.monday.com/users/66722948-aarjav-jain) [@Michael Lin](https://ubcsolar26.monday.com/users/66710609-michael-lin) @Deev Shah

**Context**

Me
and Hemat had an in person ideation session where we thought of a way
to route an connector from the slaveboard to the control board for
scrutineering access.

The point of this circuitry is to ensure that we can access **all**
of our relevant voltage-checking circuitry current circuitry from the
control board. This will enable scrutineering process to be more
accessible, less complex/procedural , less-HV exposure and more timely
(considering we took ~2 hours during FSGP 2025).

**Design requirements**

**Proposed design Concept**

<img src="../../images/image_2573062490.png" width="622" height="310">

Anything
in the diagram above that is in white or green represents circuitry
that will exist on the slaveboard. Yellow connections literally show the
wire.

You may be curious as **when the switches will be toggled.**
This can be done by reflashing the system to toggle the switch before
the BMASIC polls the voltage values, or by using  a physical switch
(when pressed will tell the MCU on masterboard to send an ISO-SPI
message to toggle the GPIO DURING idle operation) to effectively MUX
between the real mod 32 and the external mod 32.

**What isn't included in the circuit diagram?**

-
There isn't any fuses, ESD protection, or by-pass jumpers caps
included, since the purpose of the diagram was to make the accessibility
circuit more clear. Fuses would be added where the external circuitry
connector interacts with the slaveboard (yellow-white nodes).

-
There is no connections to show what net/signal will actuate the
switches. The signal responsible for doing this would be anyone of the 9
controllable GPIOs on the ADBMS1818.

**What implications are there for the rest of the slaveboard?**

-
The current mux layout (3x 6->3 MUXs for multiplexing temperature
inputs) has to be changed since this implementation utilizes the 9 total
available GPIOs. This can mitigated choosing 1x16->4 MUX which would
use 4 GPIOs for controlling the MUX, 4 GPIOS for reading the
temperatures, and would leave 1 GPIO available for toggling the
switches. This would also change the current firmware we have for toggling specific outputs of the MUX.

-
Generally, one other connection + relevant jumpers for bypassing the
switches need too be added as redundancy, increasing layout complexity.

- [HV SPDT switches](https://www.digikey.ca/en/products/detail/ixys-integrated-circuits-division/LCC110/203121) are a tad expensive (~7.40 on Digikey). However only 2 would be required

**Failure points of the mechanisms + mitigations**

@Hemat Wander @Michael Lin @Aarjav Jain Please
let me know your thoughts on complexity, feasibility, however I believe
the gains would create a much more elegant & scrutineering process.
Do note that currently the slaveboard dimensions are mostly up to us,
meaning size of the board can change. A larger board = less routing complexity.

@Deev Shah Note
that this may result in an extra cutout, so other methods for routing
this external connector the top of the pack in w ay that makes it
secured, is most ideal. If this idea gains more popularity and
implantation, lets discuss how we can do this in more detail.

> **Hemat Wander** (Dec 2025)
>
> @Krish D
> 
> I think that the C17 connection needs a **SPST, not ****a ****SPDT. **This
> is because C17 always connects to the 32nd module (+) which we will
> toggle to connect to the 33rd module (-) outside of the pack.
> 
> THEN, for C18, we will need a **SPDT, **which
> will either connect it to the internal pack 32nd module (+), or to the
> external 33rd module (+). Note if C18 is connected to the internal
> 32nd module (+) then BOTH C17 and C18 will be connected to the
> internal 32nd module (+). This will be normal operation mode as shown in
> the image in this [reply](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4693728576?reply=reply-4704928671). On the other hand, if we connect C18 to the external 33rd module (+), then we will be in scrutineering mode.
> 
> We can  now get rid of the thermistor MUX, and just connect one of the pins to a spare GPIO.
> 
> Does this make sense/agree with what you were saying? @Krish D

> **Aarjav Jain** (Dec 2025)
>
> @Krish D @Hemat Wander how does this IC work exactly?
> 
> ![](../../images/image_2589921150.png)
> 
> *Note: *We
> cannot change our FW for scutineering so we are always reading and
> faulting on C18. This is why I do not understand why we are using more
> than 16 cell inputs. That means the scrutineering cell input which is
> C18 would be 0V which would cause a fault.
> 
> So, why are we not lets say switching what we input **into **the slaveboard?

> **Hemat Wander** (Dec 2025)
>
> @Aarjav Jain
> 
> That's
> a good point, I didn't realize we wouldn't be able to change our
> firmware. Would it be possible to have a scrutineering mode selectable
> on the master board, via a jumper that we connect for scrutineering mode
> (monitor C18 voltage) vs not (do not monitor C18).
> 
> I say this for two reasons:
> 1 - Nothing in the scrutineers email mentions if we can / can't do this.
> 2 - The scrutineers email mentions attaching a spare module to the same measurement **CHAIN **as
> the rest of the actual modules. Given this, they must mean that we have
> a spare module connected to a SPARE measurement input. Thus, during
> normal operation (normal operation = **NOT **scrutineering) that
> SPARE measurement input couldn't have anything connected to it, simply
> due to the fact that it is a SPARE. If nothing is connected to it during
> normal operation, then there is no way that it wouldn't cause a
> FAULT **unless** we are meant to "de-activate" that input.
> 
> Thus, we should be able to de-activate that input.
> 
> **However: **
> If we **cannot** deactivate that input, we will need to revert back to the [original scrutineering setup](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4693728576).

> **Krish D** (Dec 2025)
>
> @Aarjav Jain I agree with @Hemat Wander idea
> to add some form of toggling through the masterboard, this would be the
> most feasible option to activate the switch before the masterboard
> begins requesting voltage and temp data from the slaveboards.

> **Aarjav Jain** (Dec 2025)
>
> Toggling idea is great idea @Hemat Wander! Can you draft a reply to Dan? Use the previous email chain to him as inspiration as needed.

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Notes on Fusing for Slaveboard:
As previously discussed in [this update](https://support.analog.com/en-US/my-cases/edit-my-case/?id=c3358223-a4c5-f011-aa43-000d3a7a511a),
I think that we should add additional fusing to help protect the ASIC
as it is connected to high voltage. Previously I mentioned adding
additional fuses going to GND from the ASIC to help protect against ESD
shorts that cause a high overcurrent internally leading to GND.

However, after discussing with @Michael Lin,
we realized that it doesn't make much sense to include this as we have
no justification that any overcurrent scenario through the ASIC would go
to GND (which is where we would be fusing it). Thus, we will no longer
be adding this fuse. The original purpose of adding this fusing was to
protect against spikes in current caused from the HV connections to the
cell-boards, so we can **instead** take a look at the fusing on that line.

**Cell board fuses:**
Currently we have 750 mA [C1Q 750](https://www.digikey.ca/en/products/detail/bel-fuse-inc/C1Q-750/615161?_gl=1*12fb0m9*_up*MQ..*_gs*MQ..&gclid=CjwKCAiA8vXIBhAtEiwAf3B-gxocOPnkrqC0grODoPrCgsoA_qD5GA2pHdg3acpuPM0vHyHSgoP_8hoClOsQAvD_BwE&gclsrc=aw.ds&gbraid=0AAAAADrbLlj_7uZ07vFABVVBZeqPQr6WF)
fuses connected on every module input from the cell-boards, however we
found that these fuses didn't stop high current (>5A) ESD scenarios.
For reference, we have no ways of knowing if those overcurrent scenarios
actually were above 750 mA (all the way to >5A), however [previous LTspice simulations](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4673264479) make us believe this.

We
discussed increasing the speed of the fuses, however on Digikey it
seems like the C1Q750 model is the fastest SMD fuse that is over 600mA.
Specifically, it has the smallest I2T value (melting time) for all fuses
on Digikey in the 600mA-800mA range. In order to get a faster fuse we
would need to get the 500 mA [C1Q 500](https://www.digikey.ca/en/products/detail/bel-fuse-inc/C1Q-500/615155?_gl=1*7rpufv*_up*MQ..*_gs*MQ..&gclid=CjwKCAiA8vXIBhAtEiwAf3B-gxocOPnkrqC0grODoPrCgsoA_qD5GA2pHdg3acpuPM0vHyHSgoP_8hoClOsQAvD_BwE&gclsrc=aw.ds&gbraid=0AAAAADrbLlj_7uZ07vFABVVBZeqPQr6WF),
which is only 4x faster than the current fuse we use. I honestly don't
think anything on the ADBMS1818 datasheet gives information about fusing
time would be sufficient to protect the chip against over-currents, so I
think we should just go with the smallest fuse time that makes sense.
As balancing only takes 420mA at max, I think a 500mA fuse would
suffice. Thoughts @Krish D @Michael Lin ?

**Temperature Circuitry Fuses:
**The
idea behind fusing the temperature circuitry is that on a given
cell-board, the cell voltage can be very high relative to the voltage of
the temperature circuitry. The temperature circuitry is always 0V-3V
above the voltage of the slave boards first module, meaning the voltage
of the cell board can be >60V above the temperature circuitry. Thus,
in the case we accidentally short something on the cell-board side,
especially given that our thermistors will be more involved this time
around (through-holes, which are epoxied to the cells). I think there is
enough risk where we should include a fuse.  To simplify things, the
fusing should look like the following, where we only have one fuse for
all of the VREF2 and GNDs going to the cell-board.

![](../../images/image_2566873487.png)

The
issue with this, is that if a cell-board shorts we won't know which one
it was (slightly longer to find it and fix it), and that we have no
fusing on the Tsense line, so if it shorts to the Batt(+) or BATT(-) for
some of the other modules, the voltage will go outside the max voltage
range of the MUxes (causing them to break or short, I'm not sure). -
> If we did add fusing for each Tsense line it would add 16
additional fuses, which seems like overkill. Thoughts @Krish D

![](../../images/image_2566875626.png)

Other
than that, we would have NO additional fusing. All other overcurrents
would be protected (hopefully) by the Zener diodes we add between cell
inputs.

**Side Note: **
Also I contacted AD about using Zeners and ESD protection circuitry [here](https://support.analog.com/en-US/my-cases/edit-my-case/?id=c3358223-a4c5-f011-aa43-000d3a7a511a).

This update took ~30-45 minutes? (I didn't time it)

> **Krish D** (Nov 2025)
>
> @Hemat Wander
> 
> 1. A 500mA fuse would suffice. Can you define what the maximum expected current draw is to reference why this is the case?
> 
> 2. For reference, we aren't sure yet if the thermistors will be epoxied to the cells or not.
> 
> 3.
> Great job on condensing the fuses for the temperature lines. I think
> this is a much more efficient solution. Given the number of fuses being
> added (cell board -> SB and Tsense + GND fuse), I thought adding LED
> indicators for the larger fuses would be a good idea, however this just
> seems like unnecessary current draw. This being said, debugging the
> slaveboards will be a more involved procedure since more of the failure
> modes are being accounted for through our protection circuitry. Consider
> adding items like this to a "Slaveboard Debugging" guide, since
> checking continuity across fuses is a bit more implicit.
> 
> 4. Please remember that the B+ and B- fuses will be on the slaveboard now to increase accessibility.

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Simulating Auto-Connection Circuitry #2:
As mentioned in the [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4682515840),
I wanted to confirm that the time delay between circuitry connections
was sufficient by testing using the equivalent circuitry going to the
ASIC. This includes both the resistors and capacitors leading up the
ASIC (seen below) and the ESD protection circuitry within the ASIC (also
seen below).

![](../../images/image_2564211675.png)

![](../../images/image_2564211842.png)

To
implement this in LTspice I used the following circuitry. Note that the
balancing FET behavior is an approximation that the gate voltage would
be pulled up to the next module positive voltage. I should note that
this isn't exactly as it would be connected to the ADBMS1818, as the
chip has 18 cell inputs, and we only have 16 cells. However the goal of
this simulation is just a quick check that the autoconnection circuitry
works, which this essentially confirms.

![](../../images/image_2564216649.png)

We
can now simulate and look at the currents through the ESD protection
diodes. We see that the currents stay below 2uA in magnitude, which is
within the regular amount we would expect in operation. This shows that
the current limit is safe during connection. (For reference, if we
connect wires out of order, we can see spikes up to ~8A.

![](../../images/image_2564222519.png)

We
can also look at the voltages across each capacitor over time, and we
see that the voltages stay well under 8V, even during the spike when we
connect the switch.

![](../../images/image_2564231700.png)

**Conclusion**
The
above two pieces of data are justification that the connection
circuitry we have chosen is sufficient in that they will not blow up the
ASIC (hopefully). I will continue with this circuitry for the
schematic!

**Next steps for slave board:
- **Justify fuse timing values from [this update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4641933290).
- Send email to Analog Devices about if there is a specification for what Zener diodes we use
- Start work on schematic.

The complete LTspice file is attached below (it's pretty messy, my excuse is I did this quickly).
[Auto_connect_experimenting.asc](https://ubcsolar26.monday.com/protected_static/25620279/resources/2564267462/Auto_connect_experimenting.asc)

This Update took 50 minutes.

> **Krish D** (Nov 2025)
>
> Hi @Hemat Wander, great job finding out what the problem was!
> 
> Can you make it more clear what exactly what you changed from the previous circuitry and what made it work?

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Simulating Auto-Connection Circuitry:
After
performing some simulations for the auto-connection circuitry, I'm more
confused than I was before. The goal is that the Gate Source voltage
curves for each module should have curves that have steeper slope than
the module AFTER it. That way, each PFET would only close after all of
the previous PFETs for the previous modules have already closed.

![](../../images/image_2557456578.png)

For
the first few modules, we see that the gate source voltage curves look
like what we want, meaning that the first module has the steepest curve
(green), the second module curve (blue) is in the middle, and the third
module curve is the least steep (orange).

![](../../images/image_2557458402.png)

However,
for the last two modules, for some reason the gate-source voltage
curves has a different behavior. The 7th module had a less-steep curve
than the 8th module. (The 7th module is in red and the 8th module is in
grey).

![](../../images/image_2557458546.png)

So
in short, the issue is that as we get the higher modules, for some
reason the time constant for the capacitors begins to decrease again,
although I'm not entirely sure why. To try and learn more about what's
happening I decided I should try and focus on the transient conditions
as soon as you flick the switch.

We know that the voltage of a
capacitor cannot change instantaneously, meaning that the voltage it
holds from before the switch gets closed will remain. In this case, the
voltage of the PFET is initially pulled up to the cell positive voltage,
meaning we can assume each capacitor begins with 4V. We can now
simulate with each capacitor now replaced with a 4V source, and then
measure the current after the switch gets flipped. We get the following
results.

<img src="../../images/image_2563996868.png" width="646" height="282">

(

Zoomed in photo:

![](../../images/image_2563997207.png)

The
current through the last two "capacitors" (which are now replaced with
voltage sources) can be seen as the following during startup.

![](../../images/image_2563998655.png)

The
current seems to jump to around 3 mA for the last capacitor while the
current through the second last capacitor settles to something much
smaller. This shows why the voltage of the last capacitor was dropping
so quickly (since the current draw was so high). The reason this current
draw is so high is due to the "D8" diode which has a lower on
resistance than the 1k capacitor, meaning we get more current flowing
from the capacitor, as opposed to from the positive of the V8 voltage
source. This tells me that the current flow is so high because of the
R16 resistor pulling everything up to V8's positive. So I want to try
two things next (both in isolation and together).

1. Try adding a resistor on the diode paths to try and increase the resistance there and even out the current draws.
2. Remove the R16 pullup resistor to the positive voltage of the cells.

For
point 1, adding 1k resistors on the discharge line didn't seem to solve
the main issue of the discharge curve for some of the higher modules
being faster than the previous modules. Such as for module 8 (blue) and 7
(green) down below.

<img src="../../images/image_2564068010.png" width="604" height="277">

![](../../images/image_2564068382.png)

For
point 2, if we remove the R16 pulling everything up to the V+, then all
of the voltages will fall to GND (0V), which will then exceed some of
the PFETs max gate-source source undervoltage thresholds.

I also
tried increasing the number of cells to 16 to try and see how a circuit
of increased size would behave. Interestingly, the first 8-9 cells seem
to behave correctly in that the gate voltage drops fastest for the
first cell, and then slightly slower for the second cell and so on.
(This is seen with the gate-source voltage curves in the below chart,
where the fastest drop occurs for the 1st module, and the second fastest
is with the 2nd module, etc.)

![](../../images/image_2564114705.png)

**Final Product:
**I
last thing I tried was increasing the resistance values of the
resistors on the line of the diode for the last 8 modules (modules
8-16), meaning that we would now need 8 additional resistor types (2.2k,
6.8k, 10k, 15k, 22k, 33k, 47k, 66k). However, this shouldn't affect the
price, so this is fine - only downside is a little more annoying to
bring up, so we can include resistance values on the silkscreen.

<img src="../../images/image_2564142735.png" width="639" height="357">

<img src="../../images/image_2564156404.png" width="488" height="498">

The
gate-source voltage curves for all of the module PFETs look as follows:
Each module has a slower voltage drop time than the previous module,
meaning that the circuit seems to work!!

![](../../images/image_2564157496.png)

*Note
that I'm assuming that the time between each of the PFETs turning on is
sufficient for our application. I don't think the datasheet would
specify this, however I can check by simulating with the equivalent ESD
circuitry of the ASIC (that the current through each diode doesn't spike
past the 10mA limit).

**Next Steps:
**1. As
mentioned I want to try simulating with the rest of the ASIC equivalent
circuitry to confirm the voltage input won't shock the internal ESD
protection diodes. (Confirming that the difference between time
constants is sufficient).
2. Although this circuitry seems to work,
we might want to compare with options that require fewer components or
fewer types of resistors, so I will simulate that next.

(This update took 3 days, 4 hours, and 18 minutes - beating Chris K's record)

> **Aarjav Jain** (Nov 2025)
>
> @Hemat Wander:

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Simulating ESD protection circuitry:
From the last [update last night](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4673264479),
I was getting confused why the current through the internal 24V
Zener diodes, stayed so high regardless of us using smaller voltage
clamping voltage Zener diodes. I found the reason for this is
likely due to the 24V Zener diode internal to the LTC having a very
small on resistance, compared to the other clamping voltage Zener
diodes.
(Rs in the picture below).

<img src="../../images/image_2557385633.png" width="651" height="81">

If
we instead use a 33V Zener diode between each 3 inputs, then we will
see that the current through the 24V Zener only spikes to around 5A, and
most of the current goes through the 33V Zener (at least
initially).

<img src="../../images/image_2557386772.png" width="583" height="373">

<img src="../../images/image_2557376120.png" width="587" height="177">

The
conclusion from this is that the Zener's we choose will only be able to
save the LTC based on if they have a smaller on resistance than the
ASIC's internal ESD diodes. As this information is not available on the
datasheet, we have no way of knowing if this will work.

However,
the datasheet recommends using 6.8V zeners between inputs anyways for
the grounded capacitor system (we are using differential capacitors), so
we might want to consider 6.8V zeners anyways.

![](../../images/image_2557387571.png)

> **Aarjav Jain** (Nov 2025)
>
> @Hemat Wander Good
> points. Could you email AD and ask about this? If you found that adding
> the zener is actually doing nothing because the path into the chip is a
> lower resistance then its **odd **that they still suggest adding a zener. *Correct me if that is wrong. *
> 
> So, lets ask them if there is a particular spec that these zeners need to have other than 6.8V Zener Voltage.

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

More slaveboard Circuitry
To create the slave board schematic there were a couple of systems we needed to finalize.

**Scrutineering Available Cellboard**

For
one, we need some method of easily being able to complete scrutineering
without having to disconnect the 32nd module connector and reconnect a
new one. Doing so requires us going into the pack and removing one of
the cellboard-slaveboard connectors, which takes a little while. To
streamline this process for scrutineering, we should have another method
for being able to connect a slave board for testing, without having to
disconnect the connections within the pack.

One possible idea is
that we have two separate cellboard-slaveboard connectors for module
32, with one actually connecting to the 32nd module, and one going to an
extra connector that extends out of the slave board region into the
control board area. Then for the part that connects to the ASIC for the
voltage tap line and TSENSE lines (circled below), we will have a jumper
cap selection system where you can either choose to use the actual 32nd
module input, or the input from scrutineering.

![](../../images/image_2556956562.png)

The
main problem with this system is that changing the jumper caps will
still require taking off the control board to access the modules, which
will take a while and slow down the scrutineering process. Thus, it
wouldn't really make sense to include this jumper cap option, as the
main time-consuming process would be removing the control board. Once we
do that, either switching the module connector from a short harness to a
spare long harness, or removing the jumper cap would take around the
same amount of time.

With that in mind, I think creating a
separate path for connecting a cell-board for scrutineering is only
worth it if we can do so while the control-board stays in the pack.
Doing so would require a HV connection extending outside of the slave
board to an area on the control board where we could choose between
either connecting the actual module to the ASIC, or a separate external
cell board. To clarify, we would be adding an additional harness with
two wires going to the ASIC (for the voltage & temperature
circuitry) and with wires going to the 32nd module cell board (for
voltage & temperature circuitry). From there, we can now switch
between connecting the ASIC to either the actual pack cellboard or some
external cellboard for scrutineering. The downside is we are introducing
a HV connection to the controlboard that will always be live with 130V,
meaning we would have to keep it well-isolated. For now this seems a
little risky so I suggest we continue without it, however it is a
possible option to consider. [@Krish D](https://ubcsolar26.monday.com/users/66710612-krish-d) Thoughts?

**Testing the ESD protection circuitry
**I
ran some tests in SPICE and got the following outputs. Note that this
EDS protection circuity is only for the purpose of clamping voltages
outside of the range of the cell inputs. This is because we have
directly seen failures before where the INTERNAL ESD protection
circuitry for the cell inputs (voltage taps) has failed (when connecting
a module out of order), while we have not seen the ESD circuitry for
the other pins fail before.

Unfortunately, the simulations showed the my circuitry doesn't seem to work, although I can't quite tell why.

Without the ESD protection circuitry

![](../../images/image_2556970961.png)

![](../../images/image_2556970934.png)

With the ESD protection circuitry:

![](../../images/image_2556969007.png)

![](../../images/image_2556975840.png)

**Note
I completed these simulations with a 6V Zener diode instead of a TVS
diode (since LTspice had no 6V TVS diodes). However from my research, we
can assume the behavior to be pretty similar.

As we can see, in
both of the cases, the current through the internal Zener diodes of the
LTC spikes past 7A during the startup phase, regardless of if we
include external ESD protection. My thought process was that including
additional external protection diodes with a smaller breakdown voltage
would allow them to draw the current instead of the internal Zener, by
clamping the voltage, however, this is not the behavior we observe.
Instead, we observe that the current through the large 24V zener diodes
(D7 & D8) still spikes to around 8A.

I also tried adding
smaller voltage Zener diodes in parallel with the 24V zener diodes to
see if they would draw some of the current instead, however the 24V
zener diodes seem to be taking most of the current no matter what. This
is really confusing to me.

![](../../images/image_2556977840.png)

![](../../images/image_2556978136.png)

I
also tried using TVS diodes and got the same results, (current spiking
to 8A in the 24V zener diodes). You can see the results for that below.

![](../../images/image_2556979324.png)

![](../../images/image_2556979378.png)

I'm
honestly not sure how to move forward with creating the ESD protection
circuity as it seems like there isn't anyway to get it to work in this
simulation. We might want to consider putting on external zeners/TVS
diodes regardless to serve  as additional protection that might work,
but if the simulations are set up correctly it seems like the ASIC will
experience a current spike either way. I'm not entirely sure what's
causing this, any thoughts @Krish D? @Michael Lin ?

We
might have to continue without this circuit if we can't figure out how
to get it to work correctly? Now that we have auto-connection circuitry,
the issue of the voltage taps experiencing a spike in current likely
wont be an issue anyways.

**Auto Connection Circuitry**
I
also tried simulating the auto-connection circuitry, by using a switch
and checking analyzing the voltage drop curves at the gate of each FET.
The goal is that the time constant for each FET should be greater than
the FET before it, that way they turn on in sequence. However, for some
reason we see that the time constant drops for the last two FETs,
meaning that they close at the same speed as the first two FETs. I don't
really know why this is happening, but I will investigate tomorrow.

![](../../images/image_2556989793.png)

![](../../images/image_2556989768.png)

**Side Note: **
- Also as a note for fusing the GND of the ASIC from the [previous update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4641933290),
it seems that VREG will draw a max of ~35 mA, which will be the same as
the current going through GND (because of continuity of current). So,
we can fuse the GND line with a 50 mA fuse, such that if a current spike
occurs somewhere shorting internally to ground for an extended period
of time we can save the ASIC by blowing the fuse.

![](../../images/image_2556926820.png)

> **Krish D** (Nov 2025)
>
> Hmm.
> A lot to unpack regarding functionality of TVS diodes. Does AD not have
> any Spice models for TVS diodes with a 6V rating? Is it worth reaching
> out to ask for a Spice model?
> 
> Doesn't the behavior for the
> why the ESD protection not working make sense, since the other TVS
> diodes (the path the high spike should take when clamped) not have a
> reference? Perhaps probing the voltages between each TVS diode would
> help make it more obvious if they are floating or not. Since they are
> floating, it makes sense why they wouldn't be functioning.
> 
> It
> would make more sense to connect all the modules in order (in the
> simulation itself) and then try to vary the input signal to a high
> voltage very quickly (to simulate noise), and then look at the
> voltage/current behavior across the internal zener diodes and across
> each TVS diode. This will protect against transient events that occur
> when the board is powered on properly, however it will not act as a
> failsafe against protecting modules out of order UNLESS they are
> connected to gnd instead of the previous module. This would mean that
> every TVS diodes clamp rating would change, but we can talk about this
> more and analyze how they should change.
> 
> Does this make sense @Hemat Wander ?

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Determining necessary protection circuitry for Rev 2.0
The
purpose of this update is to discuss some of the research I will
do into determining how we will protect the next slave board from small
overcurrent events and ESD.

**Purpose:
**The
previous slave board suffered from issues with the LTC6813 consistently
breaking due to a spike in the voltage or current, meaning we would
have to replace it. For example, you connect a random module jumper
without connect the previous modules in order, it will create a spike of
voltage at that input (say C5), thereby causing a spike in current due
to the internal ESD protection in the IC -> which causes an
overcurrent that breaks the IC. Furthermore, we've also experienced
behavior with the IC something just not working even if we connect
everything properly -> thus we suspect that ESD spikes from us
working with the PCB and chip caused it to break -> we want to
prevent this for the next pack.

Furthermore, we also want
to add some fuse protection to protect the ASIC we use from any
overcurrent situations we might experience. Both in general from
connecting modules, but also in terms of adding protection on the
temperature line.

**Goals: **

1. We
want to determine what type of protection diodes we want to use (TVS,
ESD, part number, etc.) and where they should be placed.
2. For
fusing, we want to determine where the current will go in an
overcurrent case, and also what type of fuses we should use (fast
acting?, part number?)

**Protection Diode Research:
**The
datasheet says that the maximum limit for adjacent Cell inputs is
positive 8V, and -0.3V. Ideally, we should include protection against
both of these limits, to protect against either a module being connected
out of order (ignoring our auto-connection circuitry), and to protect
against a module being plugged in reverse. However, it doesn't really
make sense to account for the latter with a diode as we would
essentially be shorting the module positive and negative if it was
connected backwards (not a good idea).

![](../../images/image_2533272673.png)

With
this in mind, we should use some sort of voltage protection in the
range of 5V-7V between each module, the idea being that if a module has a
spike in voltage, the current will flow down to the other modules
instead of flowing through the ASIC and breaking it. Also, the only
application note related to using diode protection in the ADBMS1818
datasheet is this. It makes sense to include the diode protection like
this, to protect against overvoltage's between modules, so we will do
that as well.

![](../../images/image_2533288148.png)

What
type of diode should we use (TVS diodes or ESD diodes)? From a quick
search it seems that TVS diodes are predominantly for power supply
surges which can be for a higher amount of power for a
(slightly) extended period of time, while ESD diodes are for
protecting against a smaller electrostatic discharge but with a faster
time. For our purposes, I think that we want to worry about accounting
for a higher amount of power for an extended time, caused by module
voltages being connected in the wrong order (TVS diodes). This should
also provide some ESD protection as well though.  Furthermore
Zener diodes are used to consistently regulate a voltage at some higher
level, meaning they don't really apply to our use case as our input
should usually be lower than the diode breakdown voltage.

After
looking on Digi-key, it seemed like there weren't many results with a
5V breakdown voltage, however I found some options with a 6V
breakdown voltage. Specifically the [ESD7481MUT5G](https://www.digikey.ca/en/products/detail/onsemi/ESD7481MUT5G/4847670),
which we will connect between each of the cell inputs. However, I want
to confirm that these diodes will remain as an open circuit for voltages
below 4.2V.

Note that we still need to find some way of
protecting against modules being plugged in reverse (however we can
solve that issue with other methods).

**Additional Fuse Protection:
**On top of the cell-tapping fuses we already have on the cell board, I think that it would be good to add additional fuses to

1. Protect the ASIC from extended current spikes that would stress the diode protection
2. Protect the temperature lines from overcurrent caused by shorting with the module voltages.

For
point 1, I don't think we need to do anything overkill, this
simply accounts for the difference in the maximum current we can draw
through the ASIC (10mA according to the above table), and the fuse
rating of the cell board fuses (> 400 mA). We could add one fast
acting fuse on the GND connection of the ASIC, with a current rating
slightly above that of the max expected current draw from all of the
chip systems.  -> I still need to determine how to calculate
this.

For protecting the temperature lines, we should
consider the possibility of the module voltage shorting through the
temperature line based on however we choose to implement the thermistor.
The circuitry seems like it will be more involved than last time, so I
think the severity x likelihood of the risk is large enough to consider
adding fusing. The shorts can either occur on the module voltage to the
3V ref, or from the module voltage to GND, or directly shorting the 3V
ref to GND somewhere in the temperature circuitry. If an overcurrent
occurred, the current draw would be very high, meaning it might suffice
to have one fuse on both the GND and VREF (3V) for all of the thermistor
circuitries combined (2 fuses total).

The main benefit to
have multiple fuses is that we can use the fuses to determine at which
module exactly the short occurred. Because the fuses are relatively
expensive (~>$1), but it would be very helpful to know which module
shorted, this is a bit of a tough problem.

My conclusion is
that we should fuse once on the VREF side and once on the GND side of
the thermistor circuit as it would be cheaper, while still achieving the
larger goal of having
fuse protection for extreme short cases.
Each of these fuses will be 28mA-50mA, as the expected current draw
from the VREF line is only 16 *(3V/20000 ohms) = 2.4 mA. They will be
fast-acting SMD fuses.

> **Aarjav Jain** (Nov 2025)
>
> @Hemat Wander

> **Hemat Wander** (Nov 2025)
>
> To add some more detail and answer your questions:
> 
> For
> the fusing, we know that the ADBMS pins for the temperature circuitry
> (VREF2, GPIO1-9 if we use them) have an absolute limit at 10mA,
> meaning that our rating for the fusing has to be below that to protect
> the ADBMS. However the issue is that when looking on Digi-key for SMD
> fuses, they are all rated at 28mA or over.
> 
> ![](../../images/image_2541865338.png)
> 
> If looking at non-SMD fuses with the ratings we would want, they seem to be way too-expensive. ($44).
> 
> ![](../../images/image_2541869097.png)
> 
> It
> seems like there is no feasible way to 100% protect the ADBMS in the
> case that high voltage shorts to Tense or VREF2. However, in the case
> that high voltage does somehow short to one of the temperature sensing
> lines, we still need fusing, as even if it cannot protect the ASIC it
> will stop an extended overcurrent situation caused by the short, which
> would otherwise draw an insane amount of current from the cells and
> light the cells on fire. (Ex. Module 23(+) = ~92V gets shorted to VREF =
> ~3V).
> 
> With this in mind, we know that the maximum current
> the ADBMS will be able to draw from each pin is 10 mA, meaning the
> expected current draw by definition has to be less than 10mA. From
> there, Digi-key has a few options, but in general we can assume that
> whatever shorts happen would be over 1 A (if a short happens).
> Regardless, if we want to use the smallest available fuse that is still
> above the expected current draw, we can just use a 28 mA fuse, like
> here
> 
> To answer your questions:
> 
> 1.   The
> current flowing down to the other modules is intended. What this means
> is that whenever we connect a higher voltage module without connecting
> the previous ones, the TVS diode will act as a path to first fill up the
> capacitors of the previous modules with voltages decrementing in 6V
> between modules down until it reaches 0V, after which all of the
> modules before that would have 0V. This essentially protects the IC from
> the 8V limit between cells by filling up the previous module capacitors
> to the correct voltage. Once the capacitors are filled, current will
> stop flowing. Note that this protection is for voltage threshold between
> cell inputs, which is different from ESD caused by static
> electricity.
> 
> ![](../../images/image_2541884340.png)
> 
> 2.
> The case of a higher amount of power is what I explained before,
> with the voltage protection for the cell inputs from the previous
> question using Zener's. Essentially, if we connect modules with the
> incorrect voltage, the ASIC will experience an extended period of
> overvoltage between cell inputs -> which we should account for.
> 
> 3.
> It is not the only solution, we can instead use two fuses (one on VREF2
> and one on GND), which will only cost us ~$3, as opposed to fusing on
> each line. That just means we wont know at which module the short
> happened exactly.
> 
> 4. Let me know if this explanation
> doesn't suffice and I will draw it out: If we short one of the
> higher voltages to the GND of the temperature sensing circuitry on the
> cell-board, then we will have a lot of current flowing through the GND
> wires of the slaveboard-cellboard harnesses, which then feed into the
> GND on the slaveboard, which connects to the first module of the
> respective slaveboard. If we fuse this line, we can stop the current
> draw on that line.

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Voltage Tapping Auto-Connection Circuitry Update #3:

Going on from the previous [update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4632505281):

It's
beginning to seem like the only method we have for automatically
connecting the voltage taps in order is the PFET circuitry given at the
end of the [first update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4632220538).
However, before we confirm this I wanted to do some more thinking on
possible alternatives, or getting the method from the previous update to
work.

For context of the previous method, it
currently looks something like this. The idea is that the voltage from
the previous cell should feed into controlling the very next cells FET
(which  connects the cell to the LTC). The issue with this design
is that the voltage from the next cells in the series feed backwards
into the previous cell and so on forming a voltage divider ladder down
to ground voltage. The issue with this is that plugging in any cell
later in the chain (say cell 4 with 16V) will cause the voltage of
the previous cells inputs to immediately become some fraction of that,
despite that cell being missing (cell 3 will read 12V despite the
voltage tap not being connected to the actual cell).

![](../../images/image_2530099358.png)

How
can we fix this? We tried thinking of ways of integrating diodes into
this circuit, but the issue is that this doesn't really work. We need to
somehow pass a lower voltage from the left side to the right side
without passing a higher voltage from the right side to the left side. A
diode works by passing a higher voltage to the other side or in other
words passing a lower voltage through backwards.

![](../../images/image_2530136720.png)

I
also considered passing the voltage from the LTC input of the previous
module, instead of the cell voltage directly. The idea being that the
PMOS wouldn't have the voltage at the source of a given
module passed back through the previous modules source
affecting the previous modules. Also, this makes more sense in terms of
working like an "AND" gate, where the voltage only passes through if all
the previous voltages are

![](../../images/image_2530274104.png)

This
concept seemed promising as I thought the PMOS would act as an
open circuit when the connection is floating, thus not allowing the cell
voltage to pass through, or propagate backwards. However, after
simulating in LTspice, it became clear to me that this wouldn't be a
viable option due to the body diode of the PFET. the body diode of the
PFET allows for current to flow backwards from drain to source when the
drain voltage is higher than the source voltage. This is essentially
always true in our setup, due to the next cell connection increasing the
voltage of the previous LTC input.

For example, Cell 2(+)
increases the voltage of C1 in comparison to Cell 1(+), thus allowing
current to flow through the PFET in reverse bias.

![](../../images/image_2530344889.png)

When
simulating, I got that C1 was essentially always slightly higher than
4V despite the input to cell 1 (+) being floating (as opposed to being.
Note that the drain and source are flipped in the SPICE model.

After
simulations and thinking about more configurations, it doesn't seem
like there's any promising way to get this circuitry to work the way we
want.

As a reminder our goals are:

- Only connect each PFET when all of the previous modules are connected

- To not propagate voltage of the each modules backwards to fill in the previous module voltage inputs.

The
second goal is important for completing open wire checking (as
otherwise the previous modules will make it seem like a cell is
connected even though it is not).

HOWEVER, I should
mention that all of these circuitries should in theory NOT fry the ASIC,
thanks to the voltage resistor ladder present in some form or
another.

It seems like the conclusion from all of this is
to continue with circuitry similar to FEs. The next steps are to discuss
this in the slave board check in meeting (I will set this for Tuesday
(tomorrow)).

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

Going on from the previous [Update](https://ubcsolar26.monday.com/boards/9565350285/pulses/9692467519/posts/4632220538):

After
doing some more research, I think there are a few other promising
methods for being able to connect the voltage taps automatically in
order.

One method would be to use this timer block debounce
IC (LTC6994), that would allow us to specify an amount of delay time
between each of the gates activating. The idea with using this IC
is that would would have it separately connected to each MOSFET, and
then drive the signal to the gate of each MOSFET using one switch
with each IC having different delays.

[https://www.analog.com/en/products/ltc6994-1.html](https://www.analog.com/en/products/ltc6994-1.html)The
ONLY problem I can see with this solution, would be that each IC
is so expensive, meaning it would cost ~$160 per slave board (that's not
gonna work for us).

Another method I was thinking
of was using some sort of OPAMP circuitry to connect the voltage taps,
such that we wouldn't require any FETs. The idea would be that we only
power the rails of the MOSFET (turn it on) using one GND connection for
each MOSFET, to act as another sort of switch.

![](../../images/image_2526075151.png)

However,

had
an idea that we can take the finalized RC circuitry from the previous
update, and remove the need for a switch. The idea is that each module
connection requires a voltage from the previous cell in order to
activate the PFET. This would be a nice solution, the only problem is
that it doesn't work.

![](../../images/image_2526096205.png)

The
issue, is that we essentially form a voltage divider going from the
higher cell voltages to ground, meaning that each cell would get
automatically connected.

> **Krish D** (Nov 2025)
>
> @Hemat Wander @Michael Lin Some notes & questions on your ideas:
> 
> - Regarding your implementation idea for the [LTC6994](https://www.analog.com/en/products/ltc6994-1.html),
> I think there is much more complexity involved since you are coupling
> together a MOSFET and this IC (essentially doubling the number of ICs
> needed to drive the gates). I'm unsure of how you thought to connect
> with these ICs but I'd also assume there is issues with high voltage
> isolation since the IC will be reference ground (0V or 60V - depending
> on the slaveboard you are connected to) and the gate of the FET has a
> risk of being connected to much larger voltages.
> 
> - I'm not
> too sure what the issue is that you are describing. A different issue I
> see however is that if a module is connected out of order, it will
> activate the FETs at multiple other points, which may be unwanted. Could
> diodes not prevent the current from flowing unwantedly? Additionally,
> you are losing the ability to toggle on and off the connection since the
> connection is now dependent on if a connector is in or not. Do we need
> the connection to be togglable (with a jumper for example)?

---

# Untitled

**Author:** Hemat Wander

**Date:** Nov 2025

**Determining auto-connection circuitry: **

The Problem:
With
the LTC6813, it was necessary to plug the voltage tap connections in
order. The voltage taps refer to the "cell inputs" in the datasheet,
which are used to connect the module positives to the LTC and measure
the voltage across each module. "Connecting in order", meant that we had
to connect each of these voltage taps beginning at the lowest module
and going up (module #1, then #2, etc. -> with voltages ~4V, ~8V,
~12V, etc..)

To achieve this on the previous slave board
iteration, we had to use the module jumpers (module 13's is shown), such
that every time we would connect the slaveboard in the pack we would
connect the jumper cap going on each of the module jumpers in order. The
process was slow and prone to human error -> thus we want some way
to automate this process.

![](../../images/image_2525787953.png)

![](../../images/image_2525788436.png)

The Solution

The
idea in general should be something similar to what formula electric
does, such that we have some sort of timing system to connect the
voltage taps in order. Using some sort of RC timer circuitry should fit
this purpose. I couldn’t find any sort of mechanical solution that could
do this for us (@Krish any thoughts?), but I think using an electrical solution would be less prone to error -> similar to what formula E uses.

We need two things to achieve this:

1. An electronically controlled switch

2. Some timing / ordering circuitry for when to control those switches.

Electronic Switch:

Currently
a MOSFET seems like the best option, my only concern is that a FET is
not exactly like a switch when its on. Specifically, it might behave
weirdly when we try to push current in the opposite direction, such as
for open wire checking, or depending on how the ADC reading operates.

This
is the more complicated part, as we need to find some way of activating
the MOSFETs in order for all of the different voltage inputs, just
using one switch. From FE, we figured out we can do this using RC
"timers" where we use a certain resistance and capacitance to determine
how long the gate voltage takes to reach the Vgs threshold.

-
Note: I considered having the RC timers connect to comparators that
trigger a digital signal (high or low) to the MOSFET to have a specific
digital cutoff time, as opposed to a continuous analog increase, however
I think as long as the time constant calculations are done correctly,
the analog solution will be much cleaner than adding comparators.

My
first guess was to use NMOSs and have their gates connected through a
resistor ladder to the max voltage, however this would invert all of the
time constants (meaning we would have the maximum time constant for the
first module, and the minimum time constant for the last module). ->
This solution doesn't work

![](../../images/image_2525831397.png)

One
simple solution would be to have each FET wired separately to the
switch with a varying resistance voltage divider, or a varying
capacitance to change the output current. Two possible configurations of
this kind are shown below. In the first one we have a ladder of
resistors connecting to the voltage divider circuitry for each. One
issue with both of these is that they require a large variety of
different resistor values, and they seem a little bit more messy.

Also, note that with the resistance values written they would have quiescent current draws of approximately.

(4V)/(16000 * 3 + 5000 ohms) = 6.35 8 10^-5 A between each module

and

(64V)/(16000 * 3) = 1.3 mA between module 1 and 16

![](../../images/image_2525831454.png)

![](../../images/image_2525831625.png)

To
try and make a cleaner solution, I used PFETs to invert the logic of
the first solution. This time we switch the GND connection as opposed to
the Vmax connection. However, the issue with this circuitry, is that in
the off state (switch disconnected) the 100ks will have a much higher
resistance than the 1k ohm ladder chain, meaning that the voltage at
each gate will be heavily influenced by the other module voltages.

![](../../images/image_2525845532.png)

To
fix this final issue, we can add diodes at the gate of the MOSFETs
essentially like how Formula E does there's. These diodes stop the
current from flowing from the other modules to the gate of each given
module.

![](../../images/image_2525852339.png)

We
basically ended up with what Formula E has, but I wanted to derive what
they had from first principles, as opposed to blindly copying it.

Next Steps:
Before moving forward implementing in the schematic we might consider:
1) Making a spice simulation to ensure it works the way I think
2)
Trying to consider other circuit topologies. Essentially just continue
brainstorming concepts like I did here to see if any other solution is
cleaner.

> **Krish D** (Nov 2025)
>
> Great
> job on breaking down your thought process. I appreciate that you took
> the time to break this down since I was considering these ideas as well.
> 
> I
> think doing any form of a mechanical solution would be quite space
> intensive and more prone to failure, so using semiconductors as switches
> would likely be the best bet for a robust solution.
> 
> I
> believe both of your solutions (images 6,-7) are feasible to do. You
> mentioned that the there would be a larger quiescent current draw,
> however if diodes are put in place, this could be avoided. While diodes
> would make your two solutions work, there is still many more resistors
> associated with them, so ultimately going with the last solution seems
> like a better idea to me.
> 
> @Hemat Wander @Michael Lin Did
> you folks manage to come up with another solution yesterday? If so,
> please document it here when you can, but otherwise this justification
> for choosing the circuitry makes sense.

> **Aarjav Jain** (Nov 2025)
>
> "We basically ended up with what Formula E has, but I wanted to derive
> what
> they had from first principles, as opposed to blindly copying it."
> -> Haha. This is beautiful though and exactly how our engineering
> work should be done. So, as Krish said, this is great that you derived
> it. Every circuit and component** needs **a justification at Solar.

---
