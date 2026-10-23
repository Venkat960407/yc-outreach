"""Batch 2 research data (2026-10-23). Same rules as batch 1.

Every observation came from the company's public site or YC page on 2026-10-23 and was picked
to be checkable by reading the page text (no "this button is broken" claims, which a text
scraper can't confirm). Still glance at the site before sending.

`reply_to` = the Gmail message id of Venkat's Aug 15 email to that company; those drafts are
replies in that thread, written out in full in `body`.
Emails marked "guess" are first@domain until finder.py runs on the new rows.
"""

VEX = ("I write the autonomous code for my VEX robotics team (C++, PID, odometry, IMU and rotation sensors), "
       "and we're ranked 12th in the world in Robot Skills.")
STOCK = ("I built a stock research tool where a verifier checks every number an LLM writes against real "
         "market data. In testing it caught 18 of 18 injected errors with zero false positives: "
         "github.com/Venkat960407/stock-research-assistant.")
PROOF = {"VEX": VEX, "STOCK": STOCK, "": ""}

FISH = "https://github.com/Venkat960407/fish-measure"
PADS = "https://github.com/Venkat960407/pad-planner"


def reply(first, text):
    return f"Hi {first},\n\n{text}\n\nThanks,\nVenkat"


COMPANIES = [
    dict(slug="cerulion", name="Cerulion", tier="B", yc="S24", size=2, loc="San Francisco",
         what="Open-source robot middleware: Flashback rolling recorder (MCAP), Studio viewer, native replay with --verify for CI, shared-memory transport.",
         contact="Lakshay Sharma", role="Co-founder & CEO", first="Lakshay",
         email="founders@cerulion.com", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://www.cerulion.com", proof="", reply_to="1a00607e967b4bc3",
         subject="Re: Not your average intern candidate",
         value="Homepage has no install steps or quickstart (CTAs are only 'Talk to us' and 'Star on GitHub'), and Flashback/Hindsight/Studio aren't defined. Offer: write a 5-minute quickstart from a fresh install.",
         opener="", why="", build=None,
         body=reply("Lakshay", "Following up on my note from August with something concrete I could do. Your homepage goes "
                    "straight from the features to \"Talk to us\" and \"Star on GitHub,\" and the only way to setup "
                    "instructions is the Docs link in the footer, so a robotics student landing there can't try it in "
                    "five minutes. I'd be "
                    "happy to install Cerulion fresh, record a run from a simple robot sim, and write up the "
                    "quickstart I wish I'd had, including every place I got stuck.\n\nI write the autonomous code "
                    "for my VEX team (C++, PID, odometry), so replaying a run to see why the robot drifted is a "
                    "problem I deal with every week. Would that be useful?"),
         notes="Aug 15 thread. Founding Middleware Lead role is senior."),

    dict(slug="verne-robotics", name="Verne Robotics", tier="B", yc="S25", size=7, loc="San Francisco",
         what="Nemo3 bimanual arms that learn a task from ~30 min of teleop (diffusion policies), priced hourly. Packaging vials for ABClonal.",
         contact="Neil Nie", role="Co-founder & CEO", first="Neil",
         email="neil@vernerobotics.com", email_status="guess",
         website="https://vernerobotics.com", proof="VEX",
         subject="Nemo3 specs aren't on vernerobotics.com",
         value="Site shows no specs, pricing or tasks; the YC page has them (2.5 ft reach, 4 lb payload, ~30 min of teleop per task, hourly pricing). Also hiring a Robotics Operator, new grads welcome.",
         opener=("Your YC page has the numbers a buyer wants (2.5 ft reach, 4 lb payload, a new task from about "
                 "30 minutes of teleop, hourly pricing), but vernerobotics.com doesn't show any of them yet. "
                 "Moving those onto the homepage would answer the first questions a factory lead asks."),
         why=("I also saw the Robotics Operator opening. Teleoperating arms to collect clean demos is close to "
              "how I tune our robot's autonomous routines, and I'd love to learn how you turn 30 minutes of "
              "data into a working skill."),
         build=None, notes="Robotics Operator role ($20-30/hr, new grads welcome)."),

    dict(slug="pivot-robotics", name="Pivot Robotics", tier="C", yc="W24", size=8, loc="San Francisco",
         what="Camera-driven robot finishing (grinding, cutting, sanding) and inspection for foundries and aerospace. 10+ robots at a cast-iron foundry.",
         contact="Siddharth Girdhar", role="Founder & CEO", first="Siddharth",
         email="siddharth@pivotrobotics.com", email_status="guess (public: sales@pivotrobotics.com)",
         website="https://pivotrobotics.com", proof="VEX",
         subject="Your '100x Faster' stat might get misread",
         value="'100x Faster' stat refers to adding a new part without programming (small caption), but the big number reads like grinding speed (verified).",
         opener=("On pivotrobotics.com, the big \"100x Faster\" stat is about adding a new part without "
                 "programming, but at a glance it reads like grinding speed, and a skeptical foundry manager "
                 "might discount it. Something like \"100x faster to add a new part\" would keep the claim and "
                 "avoid the misread."),
         why=("Handling part-to-part variation without fixed toolpaths is the hard version of what I do with "
              "odometry and PID on a much smaller robot, and I'd love to see how you do it on real castings."),
         build=None, notes="SWE roles need 1+ yr."),

    dict(slug="relari", name="Relari", tier="B", yc="W24", size=4, loc="San Francisco",
         what="Learning dexterous manipulation from humans: video plus EMG armband, motion, force and touch, to train a manipulation foundation model.",
         contact="Yi Zhang", role="Co-founder & CEO", first="Yi",
         email="yi@relari.ai", email_status="guess",
         website="https://www.relari.ai", proof="VEX",
         subject="Software Engineering Intern (and your YC profile)",
         value="Has a Software Engineering Intern posting. YC profile's launches still show the old GenAI testing product (and Nuvi), which doesn't match the robotics story.",
         opener=("I saw your Software Engineering Intern posting. While reading up on Relari, I noticed your YC "
                 "company page still lists the older GenAI testing launch, so someone landing there first gets "
                 "a different story than relari.ai tells about EMG and dexterous robots."),
         why=("Pairing an EMG armband with video to capture the force behind a grasp is a clever answer to a "
              "problem I hit constantly: our robot knows where it is, but not how hard it's pushing."),
         build=None, notes="SWE Intern ($40-60/hr). Strong fit."),

    dict(slug="tuesday-labs", name="Tuesday Labs", tier="C", yc="W24", size=7, loc="New York",
         what="Voxel Series-1, a home robot that tidies. Founder ex-Boston Dynamics Spot manipulation.",
         contact="Rosalind Shinkle", role="Founder & CEO", first="Rosalind",
         email="rosalind@tuesdaylabs.com", email_status="guess",
         website="https://www.tuesdaylabs.com", proof="VEX",
         subject="How do I get a Voxel?",
         value="Homepage has 'Shop' and 'How Do I Get a Robot?' (goes to reserve) but no price, deposit, or availability date (verified).",
         opener=("I was looking at Voxel on tuesdaylabs.com and couldn't tell whether I can buy one now or only "
                 "reserve one. There's a \"Shop\" link and a \"How Do I Get a Robot?\" link, but no price, date, "
                 "or deposit on the page. A single line on that would help anyone who's excited to sign up."),
         why=("A robot that actually tidies a real home is the kind of messy, unstructured problem I want to "
              "work on after years of VEX fields where everything is in a known place."),
         build=None, notes="Only an open call in NYC."),

    dict(slug="waddle-labs", name="Waddle Labs", tier="B", yc="S26", size=2, loc="San Francisco",
         what="LLM agents that write robot control code from a prompt ('Claude Code for robotics'). Preview API by sign-up.",
         contact="Yiding (Vincent) Song", role="Founder", first="Vincent",
         email="founders@waddlelabs.ai", email_status="public (founders@ on site, for people who want to work with them)",
         website="https://www.waddlelabs.ai", proof="VEX",
         subject="Would love to stress-test Waddle on a real robot",
         value="Offer to be an early preview user on a real (VEX/hobby) robot and send a written log of where the agent's control code fails.",
         opener=("Your site says to email founders@ if I'm interested in working with you, so here I am. I'd love "
                 "to get preview access and try Waddle on real hardware, then send you a written log of every "
                 "task where the agent's control code worked, nearly worked, or failed, and why."),
         why=("Writing reliable control code by hand is most of what I do, so I have a good sense of where an "
              "agent would trip up: sensor noise, tuning, and recovering when the robot gets bumped."),
         build=None, notes="Founding Research Engineer open to new grads ($175-350K) is a stretch, but they invite emails."),

    dict(slug="one-robot", name="One Robot", tier="B", yc="W26", size=2, loc="San Francisco",
         what="World-model simulators of hard manipulation tasks (folding, assembly) to train and evaluate robot policies without robot time.",
         contact="Hemanth Sarabu", role="Founder & CEO", first="Hemanth",
         email="founders@onerobot.io", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://www.onerobot.io", proof="", reply_to="1a00609952185015",
         subject="Re: Not your average intern candidate",
         value="Machine Learning Intern posting. Site's demo link shows as a raw path ('/viz/index.html') instead of a label.",
         opener="", why="", build=None,
         body=reply("Hemanth", "Following up on my note from August now that I've seen your Machine Learning Intern "
                    "posting. Your point that evaluating a policy can take longer than training it really stuck "
                    "with me; testing autonomous routines on our VEX robot is the slowest part of our week too.\n\n"
                    "Small thing on onerobot.io: the link to your demo shows up as the raw path \"/viz/index.html\" "
                    "instead of a label like \"Try the folding demo,\" which undersells the coolest thing on the "
                    "page.\n\nIs the intern role open to a high school sophomore who'd work hard on whatever's "
                    "most useful?"),
         notes="Aug 15 thread. ML Intern ($6-8K/mo, junior and above)."),

    dict(slug="runtimesi", name="Runtime.si", tier="C", yc="F26", size=5, loc="San Francisco",
         what="Evaluation infrastructure for robotics: test policies in thousands of simulated environments. LIBERO work, upcoming SimInfinity benchmark.",
         contact="Chen Peng", role="Founder & CEO", first="Chen",
         email="chen@runtime.si", email_status="guess",
         website="https://runtime.si", proof="VEX",
         subject="runtime.si says 'research lab', YC says 'eval platform'",
         value="Homepage headline calls Runtime a research lab while the YC page calls it a simulation and evaluation platform; a buyer can't tell if there's a product to try.",
         opener=("Your homepage headline calls Runtime a research lab, while your YC page describes a simulation "
                 "and evaluation platform for robot policies. Someone with a policy to test can't tell from the "
                 "site whether there's something to try today beyond the waitlist."),
         why=("Testing a routine in sim before it hits the field is something I wish we did more in VEX, and "
              "thousands of varied environments is exactly what our 'works on the practice field, fails at "
              "the tournament' problem needs."),
         build=None, notes="Founding roles are full-time."),

    dict(slug="deepaware", name="DeepAware AI (Robotics Center of Silicon Valley)", tier="B", yc="S25", size=4,
         loc="San Francisco",
         what="Sells and leases robots and parts with fast delivery, plus teleop data collection, RL environments and an eval stack.",
         contact="Jerry Huang", role="Founder & CEO", first="Jerry",
         email="jerry@deepawareai.com", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://roboticscenter.ai", proof="", reply_to="1a006094bb5191a0",
         to=["jerry@deepawareai.com"], bcc=["contact@roboticscenter.ai"],
         subject="Re: Not your average intern candidate",
         value="roboticscenter.ai body text gives three platform counts (30+ stats bar, 60+ how-it-works, 90+ store card; verified) and its headline promises 48-hour delivery while the YC page says 72. Robotics Engineer Intern posting.",
         opener="", why="", build=None,
         body=reply("Jerry", "Following up on my note from August; I saw you're hiring a Robotics Engineer Intern.\n\n"
                    "While looking through roboticscenter.ai I noticed the platform count changes depending on "
                    "where you look (30+ in the stats bar, 60+ in how-it-works, 90+ on the store card), and the "
                    "headline promises 48-hour delivery while your YC page says 72. Small, but a buyer comparing "
                    "suppliers notices those.\n\nI write the autonomous code for my VEX team and I'd love to help "
                    "with setup guides, testing kits before they ship, or anything else small. Would you be open "
                    "to a quick call?"),
         notes="Aug 15 thread (jerry@deepawareai.com). Robotics Engineer Intern."),

    dict(slug="voltair", name="Voltair", tier="A", yc="W26", size=5, loc="San Francisco",
         what="Long-range drones (Faraday-1: 85 mi, 135 min) that recharge on pads at substations/poles to inspect power lines. ~1,000 sq mi per pad.",
         contact="Hayden Gosch", role="Co-founder & CTO", first="Hayden",
         email="hayden@voltairlabs.com", email_status="guess (public: info@voltairlabs.com)",
         to=["hayden@voltairlabs.com"], bcc=["info@voltairlabs.com"],
         website="https://voltairlabs.com", proof="VEX",
         subject="Pad placement planner for Faraday-1",
         value="BUILD (done): pad-planner, greedy set cover choosing substations for pads so every line-mile is in round-trip reach. With 85 mi range and 20% reserve, 1,000 sq mi per pad matches ~30 mi of line inspected per sortie.",
         opener=(f"I wrote a small planner that picks which substations should host charging pads so every mile of "
                 f"line is within Faraday-1's round trip: {PADS}. With an 85-mile range and a 20% reserve, your "
                 f"\"about 1,000 square miles per pad\" works out to roughly 30 miles of line per sortie. Is that "
                 f"how you budget it? I built it with Claude's help on a synthetic grid, and the README explains it."),
         why=("I saw you studied at UW and worked at Seattle City Light, which is part of why Voltair caught "
              "my eye, and I noticed the Electrical Engineering Intern opening too."),
         build="DONE: github.com/Venkat960407/pad-planner (set cover, sweep, GeoJSON input; synthetic demo)",
         notes="Tier A. CTO UW + Seattle City Light. EE Intern ($1-2K/mo)."),

    dict(slug="arlo-industries", name="Arlo Industries", tier="C", yc="Sp26", size=3, loc="New York",
         what="Passive mesh sensor network (Mentat) that tracks drones and missiles in 3D without radar. Field tests in Ukraine.",
         contact="Deo Arlo", role="Founder & CEO", first="Deo",
         email="deo@arlo1.com", email_status="guess",
         website="https://arlo1.com", proof="VEX",
         subject="Robotics student interested in Mentat",
         value="Little to offer; hook is interest in 3D tracking from passive sensors (geometric CV). Site's only contact path is a LinkedIn link.",
         opener=("Tracking a target in 3D from cheap passive nodes is the kind of geometry problem I love, and "
                 "Mentat is the most interesting use of it I've seen. I also noticed arlo1.com's only contact "
                 "option is a LinkedIn link, so I'm guessing at your address here."),
         why=("Most of my robotics work is estimating where something is from noisy sensors, just on a robot "
              "instead of a drone."),
         build=None, notes="Defense; roles need 3+ yrs. Low priority."),

    dict(slug="octapulse", name="OctaPulse", tier="A", yc="W26", size=2, loc="Frisco, TX",
         what="Computer vision and robotics for fish farms: phenotyping (size, shape, condition), digital twin, planned processing-line robots. Contract with Riverence.",
         contact="Rohan Singh", role="Co-founder & CTO", first="Rohan",
         email="rohan@tryoctapulse.com", email_status="guess",
         website="https://www.tryoctapulse.com", proof="VEX",
         subject="Built a one-photo fish measurer",
         value="BUILD (done): fish-measure, one photo + printed ArUco marker gives total length, fork length, body depth and area. On 60 synthetic photos: TL 0.32% mean error, FL 1.21%, depth 1.29%.",
         opener=(f"I built a small tool that measures a fish from one phone photo using a printed marker for scale: "
                 f"length, fork length, body depth, and area: {FISH}. On 60 synthetic test photos it's within about 1% "
                 f"on length and 2% on depth. I built it with Claude's help, and the README explains how it works."),
         why=("I'm really interested in geometric computer vision, and I'd love to see how far this gets on "
              "real, wet, shiny fish."),
         build="DONE: github.com/Venkat960407/fish-measure (OpenCV, synthetic accuracy test)",
         notes="Tier A. Roles in Dallas need 2+ yrs."),

    dict(slug="eden-robotics", name="Eden Robotics", tier="C", yc="Sp26", size=4, loc="San Francisco",
         what="Semi-humanoid robots for manufacturing and logistics, rented by the hour ('from $10/hour', $0 setup).",
         contact="Joseph Humphreys", role="Co-founder & CTO", first="Joseph",
         email="founders@edenrobotics.ai", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://www.edenrobotics.ai", proof="", reply_to="1a006070bd08d6a4",
         subject="Re: Not your average intern candidate",
         value="Homepage '$10/hour' has no note on what's included, what counts as an hour, or minimum commitment.",
         opener="", why="", build=None,
         body=reply("Joseph", "Following up on my note from August with one small thing. edenrobotics.ai leads with "
                    "\"Starting at $10/hour\" and \"$0 setup,\" which is a great hook, but it doesn't say what the "
                    "hour includes or whether there's a minimum. A factory manager doing the math will want that "
                    "line before booking a call.\n\nI'd still love to help with anything small, part-time now or "
                    "this summer. Would you be open to a quick 15-minute call?"),
         notes="Aug 15 thread. Founding Communications Engineer open to new grads."),

    dict(slug="dalus", name="Dalus", tier="B", yc="W25", size=3, loc="San Francisco / Munich",
         what="AI systems-engineering (SysML v2 MBSE) software: requirements, architecture, analysis, V&V, safety. Free Pro plan for students.",
         contact="Sebastian Völkl", role="Founder & CEO", first="Sebastian",
         email="sebastian@dalus.io", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://dalus.io", proof="", reply_to="1a0060875c5b6cc3",
         subject="Re: Not your average intern candidate",
         value="Free Pro plan for students needs a .edu email (Venkat is in high school, so the email asks). Offer: model the VEX robot in Dalus and send a write-up of where a student gets stuck. Pricing page 'Try for free' buttons lead to the demo form.",
         opener="", why="", build=None,
         body=reply("Sebastian", "Following up on my note from August with an offer. I'd like to model our VEX "
                    "competition robot in Dalus (requirements, subsystems, and the tests we actually run before a "
                    "tournament) and send you an honest write-up of where a first-time student user gets stuck.\n\n"
                    "The catch: the free student Pro plan asks for a .edu email, and I'm in high school. Would you "
                    "be open to setting me up anyway? I also noticed the \"Try for free\" buttons on the pricing "
                    "page go to the demo form rather than a trial, which might lose people who just want to start."
                    "\n\nWould that write-up be useful?"),
         notes="Aug 15 thread. GTM Intern any level."),

    dict(slug="adam", name="Adam", tier="B", yc="W25", size=4, loc="San Francisco",
         what="AI mechanical engineer / CAD copilot that works inside Fusion, Onshape, SOLIDWORKS etc. Open-source CADAM. Summer 2027 Residency (any experience).",
         contact="Zach Dive", role="Founder & CEO", first="Zach",
         email="founders@adam.new", email_status="public (founders@adam.new on site; Aug email went to founders@adamcad.com)",
         to=["founders@adam.new"], website="https://adam.new", proof="", reply_to="1a006086c0806848",
         subject="Re: Not your average intern candidate",
         value="Summer 2027 Residency open to any experience. Offer: run Adam on real VEX parts in Fusion and send a test log. Pricing copy: Pro called 'for trying things out' while the FAQ says Pro fits most engineers.",
         opener="", why="", build=None,
         body=reply("Zach", "Following up on my note from August (I sent it to your old adamcad.com address). I saw "
                    "the Summer 2027 Residency is open to any experience level, and I'd love to be considered.\n\n"
                    "In the meantime, I CAD parts for our VEX robot every season, so I could run Adam on real "
                    "parts we've already built (gussets, gear mounts, intake brackets) and send you a log of what "
                    "it got right and where it went wrong. Small copy note too: the pricing section calls Pro "
                    "\"for trying things out,\" while the FAQ says Pro fits most individual engineers.\n\nWould "
                    "that kind of test log help?"),
         notes="Aug 15 thread (adamcad.com). Residency Summer 2027."),

    dict(slug="outerport", name="Outerport", tier="C", yc="S24", size=4, loc="San Francisco / Tokyo",
         what="AI agents that turn specs and drawings into electrical/control designs (single-lines, P&IDs, BOMs), export DWG/DEXPI/JSON. Daikin customer.",
         contact="Towaki Takikawa", role="Founder & CEO", first="Towaki",
         email="towaki@outerport.com", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://outerport.com", proof="", reply_to="1a00607e3895e502",
         subject="Re: Not your average intern candidate",
         value="No site issue used (checked: P-1/MP-1 is pump vs motor tag, P-101 is the sheet, so not an error). Hook: MTS Computer Vision / Graphics role open to any experience; Towaki's NVIDIA neural-fields background.",
         opener="", why="", build=None,
         body=reply("Towaki", "Following up on my note from August. I saw the Member of Technical Staff role in "
                    "computer vision and graphics is open to any experience level, and that's the area I'm most "
                    "drawn to: 3D and geometric vision. Parsing scanned drawings into a graph of components and "
                    "connections is a really interesting version of that problem.\n\nI'd love to help with "
                    "anything small, like labeling or checking parsed drawings, part-time now or this summer. "
                    "Would you be open to a quick call?"),
         notes="Aug 15 thread. MTS CV/Graphics open to any level."),

    dict(slug="simantic", name="Simantic", tier="B", yc="F26", size=4, loc="Waterloo, ON",
         what="Runs real firmware on simulated MCUs (Cloud Sim) for CI and AI agents. HTTP API + TypeScript SDK; Python and CLI 'coming soon'.",
         contact="Seungmin Hong", role="Founder & CEO", first="Seungmin",
         email="seungmin@simantic.com", email_status="guess",
         website="https://simantic.com", proof="VEX",
         subject="Python client for Cloud Sim?",
         value="Python SDK and CLI are 'coming soon' while the HTTP API is documented. Offer: write an unofficial Python client against the HTTP API.",
         opener=("I saw that Cloud Sim has an HTTP API and a TypeScript SDK, with Python and a CLI marked "
                 "\"coming soon.\" If it would help, I'd be glad to write an unofficial Python client against "
                 "the HTTP API, with a couple of examples, so you can see whether it's worth shipping."),
         why=("Our VEX code only ever runs on the real robot, so every test means charging batteries and "
              "clearing the field. Running firmware against a simulated board is exactly what I wish we had."),
         build=None, notes="Could upgrade to Tier A if they give an API key."),

    dict(slug="charge-robotics", name="Charge Robotics", tier="C", yc="S21", size=25, loc="San Leandro, CA",
         what="Portable 'Sunrise' factories where robots assemble solar array bays on site (0.5-1 MW per shift).",
         contact="Max Justicz", role="Co-founder & CTO", first="Max",
         email="max@chargerobotics.com", email_status="guess",
         website="https://chargerobotics.com", proof="VEX",
         subject="The Charge vs. EPC columns on your homepage",
         value="Homepage responsibility list has three unlabeled columns, so readers infer that pile driving stays with the EPC (verified). Mechanical Engineer role open to new grads.",
         opener=("I was reading the Charge vs. EPC responsibility split on chargerobotics.com. The three columns "
                 "aren't labeled, so I had to work out from the sentence above them that pile driving stays with "
                 "the EPC. Column headers would make that obvious to an EPC skimming the page."),
         why=("Building a robot that works outdoors, in wind and heat, is the opposite of a VEX field, and "
              "that's what makes Charge interesting to me."),
         build=None, notes="Bigger team (25), full-time roles."),

    dict(slug="copycat-ai", name="CopyCat AI", tier="B", yc="W25", size=2, loc="Seattle (local)",
         what="AI for insurance brokers: turns carrier quotes into proposals, compares quotes, flags discrepancies with source references.",
         contact="Abhi Balijepalli", role="Co-founder", first="Abhi",
         email="abhi@runcopycat.com", email_status="guess (public: hello@runcopycat.com)",
         to=["abhi@runcopycat.com"], bcc=["hello@runcopycat.com"],
         website="https://runcopycat.com", proof="STOCK",
         subject="Seattle student who built an LLM number-checker",
         value="Proof match: Venkat's verifier checks every number an LLM writes against source data, same problem as CopyCat's quote comparisons. Site: testimonial 'Output is never invented' vs FAQ 'AI can make mistakes'.",
         opener=("CopyCat pulling numbers out of carrier PDFs and citing the source page is the same problem I "
                 "spent my last project on."),
         why=("I'm in Redmond, and since you're in Seattle I'd love to help in person with anything small, "
              "like testing proposals against tricky quotes to find where numbers slip."),
         build=None, notes="Seattle local. Only role is a Founding AE."),

    dict(slug="asimov", name="Asimov", tier="C", yc="W26", size=3, loc="San Francisco / remote",
         what="Pays people to record everyday activities (egocentric video, 3D pose, depth) to train humanoid robots.",
         contact="Lyem Ningthou", role="Founder", first="Lyem",
         email="founders@tryasimov.ai", email_status="emailed Aug 15, no bounce (reply in that thread)",
         website="https://tryasimov.ai", proof="", reply_to="1a006099dc305e03",
         subject="Re: Not your average intern candidate",
         value="Remote Data Collection Specialist and Strategic Ops Intern roles. Offer to collect in the Seattle area. Copy: 'We make your labor free' while the section says Asimov pays workers.",
         opener="", why="", build=None,
         body=reply("Lyem", "Following up on my note from August. I saw the remote Data Collection Specialist "
                    "and Strategic Operations Intern roles, and I'd be glad to do either from the Seattle area, "
                    "including recording tasks myself and helping recruit local collectors.\n\nOne copy note: the "
                    "business section says \"We make your labor free\" right before explaining that Asimov pays "
                    "the workers, which reads a little oddly to a business owner.\n\nWould you be open to a "
                    "quick call?"),
         notes="Aug 15 thread."),
]

for _c in COMPANIES:
    _c.setdefault("to", [_c["email"]])
    _c.setdefault("bcc", [])
    _c.setdefault("proof", "")
