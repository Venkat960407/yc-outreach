"""Batch 1 research data. Source of truth for the tracker and the per-company files.

Every "observation" was found on the company's public website on 2026-10-16.
Venkat must open the site and confirm it before sending.
Emails marked "guess" follow the common first@domain pattern and are NOT verified.
"""

VEX = ("I write the autonomous code for my VEX robotics team (C++, PID, odometry, IMU fusion), "
       "and we're ranked 12th in the world in Robot Skills.")
AUDIO = ("I recently built a real-time spatial audio engine in Python that makes any sound on my PC "
         "seem to come from a point in 3D space, with webcam head tracking: github.com/Venkat960407/spatial-audio-hrtf.")
STOCK = ("I built a stock research tool where a verifier checks every number an LLM writes against real "
         "market data. In testing it caught 18 of 18 injected errors with zero false positives: "
         "github.com/Venkat960407/stock-research-assistant.")

B = "https://github.com/Venkat960407/robotics-builds/tree/main/"

PROOF = {"VEX": VEX, "AUDIO": AUDIO, "STOCK": STOCK}

COMPANIES = [
    dict(slug="theseus", name="Theseus", tier="B", yc="S24", size=7, loc="San Francisco",
         what="Camera-based drone navigation that works without GPS (Cyclops). Customers include US Special Forces.",
         contact="Sacha Levy", role="Co-founder & CTO", first="Sacha",
         email="sacha@theseus.us", email_status="guess (public: inbound@theseus.us)",
         website="https://theseus.us", proof="VEX",
         subject="Small thing on the Cyclops page",
         value="Site naming: the USSOCOM testimonial calls the product \"VizNav\" while the rest of the site says \"Cyclops\". Hero stats (1.1 km, 104 km, <50 m) have no context on test conditions.",
         opener=("I was reading about Cyclops and noticed the USSOCOM quote on your homepage calls it \"VizNav\" "
                 "while the rest of the site says Cyclops, which could trip up a buyer skimming the page. "
                 "The hero stats (1.1 km, 104 km, <50 m) could also use one line on how they were measured."),
         why=("Estimating where a robot is without GPS is the exact problem I deal with on a small scale, "
              "so camera-based positioning on drones is really interesting to me."),
         build=None, notes="Defense customer. Some roles may need US-person status (Venkat is US-born, so fine)."),

    dict(slug="polymath-robotics", name="Polymath Robotics", tier="B", yc="S22", size=25, loc="San Francisco",
         what="Autonomy software for industrial vehicles (tractors, mining trucks) controlled through a REST API. Free simulator called Caladan.",
         contact="Ilia Baranov", role="Co-founder & CTO", first="Ilia",
         email="ilia@polymathrobotics.com", email_status="guess",
         website="https://www.polymathrobotics.com", proof="VEX",
         subject="Two small things in the Synapse API docs",
         value="API reference pages for /v2/relative-waypoints and /v2/polymath-feedback show no request or response fields (VERIFY in a browser: synapse.docs.polymathrobotics.dev/docs/api/relative-waypoints). Homepage tab title shows \"Autonomy &amp; Safety\". Planned Caladan build was blocked: the API needs credentials from Polymath support.",
         opener=("I was reading the Synapse API docs to write a small Caladan behavior, and the pages for /v2/relative-waypoints and /v2/polymath-feedback "
                 "don't list any request or response fields, so there's no way to see what a waypoint looks like before getting credentials. "
                 "Also, the browser tab on your homepage reads \"Autonomy &amp; Safety\" instead of \"&\"."),
         why=("If you'd ever give a student Caladan access, I'd love to build something with it."),
         build=None, notes="Was Tier A. API needs credentials from Polymath support, so no build. Could become Tier A if they grant Caladan access."),

    dict(slug="innate", name="Innate", tier="A", yc="F24", size=7, loc="San Francisco / Palo Alto",
         what="Personal AI robot (MARS, $995) you teach with code, language, and demonstrations. Open-source Innate OS plus a browser simulator.",
         contact="Vignesh Anand", role="Co-founder & CTO", first="Vignesh",
         email="vignesh@innate.bot", email_status="guess",
         website="https://innate.bot", proof="VEX",
         subject="Wrote an odometry-drift check skill for MARS",
         value="BUILD (done): odometry-drift check skill for Innate OS. Bonus: site says \"Teach MARS a task with one example\" in one section and \"Teach with a few examples\" in another.",
         opener=("I wrote a MARS skill that drives a square on wheel odometry, then checks against the lidar map how far the wheels drifted, "
                 "so an owner knows when a new floor is throwing off navigation: "
                 f"{B}innate-odom-check. I tested it against a simulated robot with known wheel errors, but not on MARS yet. "
                 "I built it with Claude's help, and the README explains how it works."),
         why=("Your careers section says skill matters more than degrees, which is exactly why I'm writing."),
         build="DONE: builds/innate-odom-check (odometry vs lidar drift check skill, tested on a fake robot, not on MARS/sim yet)",
         notes="Careers page says degrees don't matter. Strong fit."),

    dict(slug="almond", name="Almond", tier="A", yc="Sp25", size=6, loc="San Francisco",
         what="Axol, a dual-arm robot for physical AI ($9,499) with an open-source Python SDK, IK, and VR teleop.",
         contact="Saba Khalilnaji", role="Co-founder & CEO", first="Saba",
         email="saba@almond.bot", email_status="guess (public: hello@almond.bot)",
         website="https://almond.bot", proof="VEX",
         subject="Mapped Axol's two-arm workspace from your URDF",
         value="BUILD (done): two-arm workspace map from the Axol URDF. Bonus: FAQ says two arms give \"double the cycle time\" of one arm, which reads like the opposite of what's meant (half the cycle time).",
         opener=("I used the URDF from your open-source SDK to map where Axol's two arms can both reach, and at which table heights: "
                 f"{B}almond-axol-workspace. One thing I'd love to check with you: I get 781 mm of reach to the gripper mount vs 860 mm on "
                 "the spec sheet, which I'm guessing is the fingers. I built it with Claude's help, and the README explains how it works."),
         why=("Tuning motion on our VEX robot is my favorite part of robotics, so a dual-arm platform with an open SDK is right up my alley."),
         build="DONE: builds/almond-axol-workspace (bimanual reachability map from the SDK's URDF)",
         notes="Hiring Founding Robotics SWE. Ships from SF."),

    dict(slug="morphoai", name="MorphoAI", tier="A", yc="Sp25", size=7, loc="New York / London",
         what="AI tool that generates, checks, and refines manufacturable designs for robots and machines. Backed by a 2.5M GBP ARIA grant.",
         contact="Andrew Spielberg", role="Co-founder & CTO", first="Andrew",
         email="andrew@morpho.ai", email_status="guess (public: hello@morpho.ai)",
         website="https://morpho.ai", proof="VEX",
         subject="Drafted a homepage for morpho.ai",
         value="BUILD (done): morpho.ai currently shows only the company name, no product description. Draft a one-page landing page from their YC launch description.",
         opener=("I noticed morpho.ai only shows the company name right now, so I drafted a one-page homepage from your YC launch post: "
                 f"{B}morphoai-homepage-draft (there's a screenshot in the README). I made it with Claude's help, and it's yours to use or toss."),
         why=("Designing and iterating on robot mechanisms every season is a big part of VEX, so a tool that generates and checks designs is something I'd genuinely use."),
         build="DONE: builds/morphoai-homepage-draft (one-page HTML, labeled unofficial)",
         notes="Hiring is London-based. Site is a near-empty Squarespace page."),

    dict(slug="os3", name="OS3", tier="B", yc="S26", size=2, loc="San Francisco",
         what="Low-cost semi-humanoid robots (HALE 1.0). Developer units $14,995. First deployments in hotels.",
         contact="Rishabh Chanana", role="Founder", first="Rishabh",
         email="rishabh@os3robotics.com", email_status="guess",
         website="https://os3robotics.com", proof="VEX",
         subject="Spec sheet idea for HALE developer units",
         value="Developer units are $14,995 but the site lists no payload, reach, runtime, weight, or compute. Offer to draft a spec table. Also meta description says \"hospitality laundry\" while the page just says \"Hospitality\".",
         opener=("I was looking at the HALE developer units and noticed the site has pricing but no payload, reach, runtime, or compute specs, "
                 "which are the first things a developer spending $15K would look for. Happy to draft a clean spec table if you send me the numbers."),
         why=("Your bio says you built your first robot at 17. I'm earlier on that same path and would love to learn from a team building humanoids from scratch."),
         build=None, notes="2-person team, very early. Contract mechanical role open."),

    dict(slug="darwin", name="Darwin", tier="C", yc="F25", size=4, loc="San Francisco",
         what="General-purpose robots that learn by demonstration to assemble and maintain AI infrastructure. First deployments planned early 2027.",
         contact="Sergio Charles", role="Founder & CEO", first="Sergio",
         email="sergio@darwinrobotics.ai", email_status="guess",
         website="https://darwinrobotics.ai", proof="VEX",
         subject="\"See it work\" button on darwinrobotics.ai",
         value="The \"See it work\" button points to #work but there doesn't seem to be a section with that id (VERIFY: click it).",
         opener=("Quick heads up: the \"See it work\" button on your homepage didn't seem to jump anywhere when I clicked it. "
                 "It looks like it points to a section that isn't on the page."),
         why=("Robots learning tasks from demonstration instead of explicit programming is the opposite of how I've built autonomous routines so far, "
              "and I'm really curious how you make that reliable."),
         build=None, notes="Weak value item. Verify the button before sending, or skip."),

    dict(slug="lightberry", name="Lightberry", tier="B", yc="F25", size=3, loc="San Francisco",
         what="AI \"social brain\" for robots so they can listen, speak, and act. Runs on Unitree, Booster, Fourier humanoids. Robot named Lumi.",
         contact="Stephan Koenigstorfer", role="Co-founder & CTO", first="Stephan",
         email="stephan@lightberry.com", email_status="guess",
         website="https://lightberry.com", proof="AUDIO",
         subject="Spatial audio guy, interested in robots that listen",
         value="Idea: use sound direction-of-arrival so the robot turns toward whoever is speaking. Venkat's HRTF engine is the reverse of that problem. Site note: homepage has one line about Lumi and no specs or details.",
         opener=("For a robot that's meant to feel social, turning toward whoever is talking matters a lot. I've been working on the reverse of that problem: "
                 "making a sound seem to come from a specific direction."),
         why=("I'd love to try building direction-of-arrival detection for one of your robots so it can face the person speaking."),
         build=None, notes="Hiring Voice AI SWE. Good match for the audio project."),

    dict(slug="bucket-robotics", name="Bucket Robotics", tier="C", yc="S24", size=8, loc="San Francisco",
         what="Defect detection for manufacturing: CAD files in, vision model out, runs on edge devices like Jetson Orin Nano.",
         contact="Matt Puchalski", role="Founder & CEO", first="Matt",
         email="matt@bucket.bot", email_status="guess",
         website="https://bucket.bot", proof="VEX",
         subject="Link previews for bucket.bot",
         value="Homepage sets a large-image social card but has no preview image, so links shared on X/Slack/LinkedIn show up blank (VERIFY with a link preview checker like opengraph.xyz).",
         opener=("Small thing I noticed: when bucket.bot gets shared on X or Slack, the preview has no image even though the page asks for a large image card. "
                 "Adding an og:image would fix it."),
         why=("Generating vision models straight from CAD without labeling is a really clever way around the data problem, and I'd love to see how it works on the factory floor."),
         build=None, notes="Hiring ML, full stack, forward deploy."),

    dict(slug="saphira-ai", name="Saphira AI", tier="C", yc="S24", size=7, loc="San Francisco",
         what="AI agents that help hardware and robot companies get safety certified (ISO 10218, ISO 26262, UL, CE).",
         contact="Akshay Chalana", role="Co-founder & CEO", first="Akshay",
         email="akshay@saphira.ai", email_status="guess (public: contact@saphira.ai)",
         website="https://saphira.ai", proof="VEX",
         subject="Robotics student curious about safety certification",
         value="Customer quote from RobCo has no named speaker or title, which weakens it (VERIFY).",
         opener=("I was reading through the case studies on your site and noticed the RobCo quote doesn't have a name or title attached, "
                 "which makes it easier for a skeptical buyer to skim past."),
         why=("Safety is something we deal with in VEX at a tiny scale, and I've never seen how it works for real industrial robots. Saphira seems like the best place to learn that."),
         build=None, notes="Weaker fit. Lower priority."),

    dict(slug="yondu", name="Yondu", tier="B", yc="W24", size=7, loc="Los Angeles",
         what="Warehouse robots for order picking at 3PLs: teleop first (ULTRON), then autonomy (YGM). Has a Fall 2026 Mechatronics Intern posting.",
         contact="Michael Chen", role="Founder & CEO", first="Michael",
         email="michael@yondu.ai", email_status="guess (public: hello@yonduai.com)",
         website="https://yondu.ai", proof="VEX",
         subject="Mechatronics intern question (and a small site note)",
         value="Site is yondu.ai but the contact email is hello@yonduai.com (different domain). Copy also switches between \"bin-picking\" and \"warehouse tasks\" as the first thing you fully automate.",
         opener=("I saw your Fall 2026 Mechatronics Intern posting. While looking around the site, I noticed the contact email uses yonduai.com "
                 "even though the site is yondu.ai, which might make some buyers think it's a different company."),
         why=("Starting with teleop and handing more over to autonomy over time is a really practical approach, and it's close to how we build up our autonomous routines in VEX."),
         build=None, notes="Has an intern posting. Michael helped build an open-source bipedal robot at MIT."),

    dict(slug="ultra", name="Ultra", tier="B", yc="S24", size=4, loc="New York",
         what="OP1 stationary robots that pack and sort orders in warehouses. Raised $62M on Oct 9, 2026 and partnered with Physical Intelligence.",
         contact="Oliver Ortlieb", role="Co-founder & CTO", first="Oliver",
         email="oliver@ultra.tech", email_status="guess",
         website="https://ultra.tech", proof="VEX",
         subject="Placeholder text showing on ultra.tech",
         value="The \"Introducing\" section shows leftover CMS text: \"No frames yet. Paste a manifest URL...\" (VERIFY).",
         opener=("Congrats on the raise. Quick heads up: the \"Introducing\" section on ultra.tech is showing leftover placeholder text "
                 "(\"No frames yet. Paste a manifest URL...\") where I think an animation is supposed to be."),
         why=("A robot that just plugs into a standard outlet and starts working is the kind of practical robotics I want to build."),
         build=None, notes="Fresh $62M raise, 19 open roles. Bigger hiring process, lower odds of cold reply but worth one shot."),

    dict(slug="proception", name="Proception", tier="C", yc="W25", size=10, loc="Mountain View",
         what="Dexterous robot hands (ProHand, 22 DOF, tactile skin) and a data glove (ProGlove). $11M seed led by First Round.",
         contact="Jay Li", role="Founder & CEO", first="Jay",
         email="jay@proception.ai", email_status="guess",
         website="https://proception.ai", proof="VEX",
         subject="\"Explore products\" button on proception.ai",
         value="\"Explore products\" button points to #products but there's no products section on the homepage. Nav says \"Product\", footer says \"Products\". (VERIFY)",
         opener=("Quick heads up: the \"Explore products\" button on your homepage doesn't seem to lead to a products section, "
                 "so a visitor can't find ProHand specs from there."),
         why=("A hand with tactile skin is the kind of sensor problem I find fascinating, since most of my robotics so far has been about getting reliable data from IMUs and encoders."),
         build=None, notes="Only role open is a technician in Palo Alto."),

    dict(slug="mbodi-ai", name="Mbodi AI", tier="B", yc="Sp25", size=6, loc="New York",
         what="Teach industrial robots new skills with plain language and demos. ABB partnership. Open-source embodied-agents library.",
         contact="Sebastian Peralta", role="Founder & CEO", first="Sebastian",
         email="sebastian@mbodi.ai", email_status="guess",
         website="https://www.mbodi.ai", proof="VEX",
         subject="Press links on mbodi.ai all go to one article",
         value="Every item in the press carousel links to the same TechInAsia article, including the TechCrunch and ABB headlines (VERIFY by clicking 3-4).",
         opener=("I was reading through your press section and noticed every item links to the same TechInAsia article, "
                 "including the TechCrunch and ABB ones, so visitors can't actually reach that coverage."),
         why=("Congrats on winning the Automate Startup Challenge. Teaching robots with language and demos instead of code is a big shift from how I program our VEX robot, and I'd love to learn how you make it reliable in production."),
         build=None, notes="Could upgrade to a build later with their open-source embodied-agents library."),

    dict(slug="orangewood-labs", name="Orangewood Labs", tier="C", yc="W18", size=8, loc="San Francisco / Noida",
         what="Affordable AI robot arms for small manufacturers (RoboGPT). Most of the team is in India.",
         contact="Abhinav Das", role="Founder", first="Abhinav",
         email="abhinav@orangewood.co", email_status="guess (public: hellorobot@orangewood.co)",
         website="https://www.orangewood.co", proof="VEX",
         subject="Missing numbers in \"Tasks Done by Orangewood Robots\"",
         value="The \"Tasks Done by Orangewood Robots\" section has the \"rough estimates\" disclaimer but no actual numbers showing (VERIFY).",
         opener=("I noticed the \"Tasks Done by Orangewood Robots\" section on your homepage shows the disclaimer about rough estimates, "
                 "but the numbers themselves aren't showing up."),
         why=("Making robot arms cheap enough for small shops is a mission I really like, and RoboGPT sounds like a great way to make them easier to program."),
         build=None, notes="Open roles are all in Noida. Lower priority."),

    dict(slug="revise-robotics", name="Revise Robotics", tier="A", yc="W25", size=3, loc="New York",
         what="Robots that test, wipe, photograph, and list used laptops for resale. Posting Engineering Intern (Summer/Fall 2026).",
         contact="Rupesh Jeyaram", role="Founder & CEO", first="Rupesh",
         email="rupesh@reviserobotics.com", email_status="guess",
         website="https://www.reviserobotics.com", proof="VEX",
         subject="Built a laptop health-check script for refurbishing",
         value="BUILD (done): a Python script that pulls a laptop's battery wear, disk health, RAM, and CPU into a one-page resale grade report.",
         opener=("I saw you're automating laptop testing, so I built a small script that pulls a laptop's battery wear, disk health, RAM, and CPU "
                 f"into a one-page resale grade: {B}revise-laptop-grader. I built it with Claude's help, and the README explains how it works."),
         why=("I also saw the Engineering Intern posting. Automated testing and making robots reliable are exactly what I like working on."),
         build="DONE: builds/revise-laptop-grader (Windows/macOS/Linux, tested grading rules)",
         notes="Has an Engineering Intern posting. Site didn't render for research; verify it loads."),

    dict(slug="aktoria-robotics", name="Aktoria Robotics", tier="B", yc="S26", size=2, loc="San Francisco",
         what="24/7 remote robot operators plus low-latency teleop software. Also sells teleop training data.",
         contact="Shreenabh Agrawal", role="Founder", first="Shreenabh",
         email="founders@aktoria.com", email_status="public (founders@ shown on site)",
         website="https://aktoria.com", proof="VEX",
         subject="Question about R1 Teleop",
         value="Site names \"R1 Teleop\" as a product but never explains it, and \"works with any robot\" has no list of supported platforms.",
         opener=("I was reading about your teleop setup and noticed \"R1 Teleop\" is named on the site but never explained, and there's no list of which robots it supports. "
                 "Those would be the first two things I'd want to know as a robotics lab."),
         why=("I've spent a lot of time on the line between driver control and autonomy in VEX, so a teleop layer that helps robots get deployed sooner makes a lot of sense to me."),
         build=None, notes="Brand new (S26), 2 people. Public founders@ email."),

    dict(slug="starcloud", name="Starcloud", tier="B", yc="S24", size=12, loc="Redmond, WA (local)",
         what="Data centers in space. Launched Starcloud-1 with an Nvidia H100 in Nov 2025. $170M Series A in Mar 2026.",
         contact="Adi Oltean", role="Founder & Chief Engineer", first="Adi",
         email="adi@starcloud.com", email_status="guess",
         website="https://www.starcloud.com", proof="VEX",
         subject="Redmond student who'd love to help in person",
         value="LOCAL: Venkat is in Redmond, same as Starcloud's hiring location, so he can help in person. Site footer still says (c) 2024 (VERIFY).",
         opener=("I live in Redmond, a few minutes from your team, and I'd love to help out in person. Small thing I noticed: the footer on starcloud.com still says 2024."),
         why=("Training an LLM in orbit was one of the coolest things I read about last year, and being local means I could help in person with anything hands-on."),
         build=None, notes="Local in Redmond. Big company now ($1.1B), so lower cold-email odds, but the local angle is strong."),

    dict(slug="feather", name="Feather", tier="C", yc="S22", size=8, loc="Seattle (local)",
         what="Voice AI platform for natural-sounding AI phone calls.",
         contact="Aahan Sawhney", role="Co-founder", first="Aahan",
         email="aahan@featherhq.com", email_status="guess",
         website="https://www.featherhq.com", proof="AUDIO",
         subject="Typo in Feather's Google/link preview text",
         value="Site description used in Google results and link previews reads \"Feather is helps enterprises build and deploy AI agents\" (VERIFY by searching featherhq).",
         opener=("Small thing: the description that shows up in Google and link previews for featherhq.com says \"Feather is helps enterprises\", "
                 "which is an easy fix in the page's meta description."),
         why=("I'm into audio and real-time processing, and natural-sounding voice is one of the hardest audio problems out there. Being in the Seattle area, I'd love to help locally."),
         build=None, notes="Only open role is India-based. Lower priority."),

    dict(slug="silurian", name="Silurian", tier="C", yc="S24", size=6, loc="Seattle (local)",
         what="Foundation models that simulate Earth, starting with weather (GFT, 1.5B params). API for energy, insurance, agriculture.",
         contact="Nikhil Shankar", role="Co-founder & Chief Engineer", first="Nikhil",
         email="nikhil@silurian.ai", email_status="guess",
         website="https://silurian.ai", proof="STOCK",
         subject="Footer \"API\" link on silurian.ai",
         value="Footer \"API\" link goes to the weather product page, not API docs (VERIFY).",
         opener=("Small thing I noticed: the \"API\" link in your site footer goes to the weather product page instead of API docs, "
                 "which might lose a developer who's ready to try it."),
         why=("I'm interested in forecasting and in making sure model outputs can be trusted, which is what my last project was about. Being in the Seattle area, I'd love to help locally."),
         build=None, notes="ML research role is senior. Lower priority."),
]
