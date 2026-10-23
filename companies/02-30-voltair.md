# Voltair

| | |
|---|---|
| Tier | A |
| YC batch | W26 |
| Team size | 5 |
| Location | San Francisco |
| Website | https://voltairlabs.com |
| YC page | https://www.ycombinator.com/companies/voltair |
| Contact | Hayden Gosch, Co-founder & CTO |
| Email | hayden@voltairlabs.com (guess (public: info@voltairlabs.com)) |

**What they do:** Long-range drones (Faraday-1: 85 mi, 135 min) that recharge on pads at substations/poles to inspect power lines. ~1,000 sq mi per pad.

**Value item:** BUILD (done): pad-planner, greedy set cover choosing substations for pads so every line-mile is in round-trip reach. With 85 mi range and 20% reserve, 1,000 sq mi per pad matches ~30 mi of line inspected per sortie.

**Build:** DONE: github.com/Venkat960407/pad-planner (set cover, sweep, GeoJSON input; synthetic demo)

**Notes:** Tier A. CTO UW + Seattle City Light. EE Intern ($1-2K/mo).

> Before sending: Read the build's README so you can talk about it, and make sure the link works.

## Email

**Subject:** Pad placement planner for Faraday-1

```
Hi Hayden,

I wrote a small planner that picks which substations should host charging pads so every mile of line is within Faraday-1's round trip: https://github.com/Venkat960407/pad-planner. With an 85-mile range and a 20% reserve, your "about 1,000 square miles per pad" works out to roughly 30 miles of line per sortie. Is that how you budget it? I built it with Claude's help on a synthetic grid, and the README explains it.

I'm Venkat, a high school programmer in Redmond. I write the autonomous code for my VEX robotics team (C++, PID, odometry, IMU and rotation sensors), and we're ranked 12th in the world in Robot Skills. I saw you studied at UW and worked at Seattle City Light, which is part of why Voltair caught my eye, and I noticed the Electrical Engineering Intern opening too.

I'm a sophomore, so I know this is unusual, but I'd love to help with something small, part-time now or this summer. Would you be open to a quick 15-minute call?

Thanks,
Venkat Narayanan
```

## Follow-up (send 5 to 7 days later, same thread)

```
Hi Hayden,

Just bumping this in case it got buried. Still happy to help with anything small if it's useful.

Thanks,
Venkat
```
