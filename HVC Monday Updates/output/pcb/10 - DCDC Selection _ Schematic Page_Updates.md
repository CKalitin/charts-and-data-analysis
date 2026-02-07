# or RDK-85SLR to your specifications.

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

