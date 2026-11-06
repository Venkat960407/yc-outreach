PROOF = ("I'm Venkat, a high school programmer in Redmond. I write the autonomous code for my VEX "
         "robotics team (C++, PID, odometry, IMU and rotation sensors), and we're ranked 12th in the "
         "world in Robot Skills.")
PROOF_CAD = ("I'm Venkat, a high school programmer in Redmond. I write the autonomous code for my VEX "
             "robotics team (C++, PID, odometry, sensor fusion), we're ranked 12th in the world in Robot "
             "Skills, and I've designed 30+ robots in Fusion 360.")
ASK = ("I'm a sophomore, so I know this is unusual, but I'd love to help with something small, "
       "part-time now or this summer. Would you be open to a quick 15-minute call?")
SIG = "Thanks,\nVenkat Narayanan"

# tier, name, contact, role, to, email_status, website, value, subject, opener, proof, followup(thread,msgid)
C = [
 dict(n="Tekton Dynamics", tier="B", contact="Max Ahrens", role="Founder", to="founders@tekton-dynamics.com", st="guess",
      web="https://www.tekton-dynamics.com", subj="Test cases for seam finding",
      value="Offer: a scored set of messy welding cases (shifted fixtures, warped plates, tacks in the path)",
      body="Tekton's pitch is that welding robots can stop being blind and handle parts that aren't perfectly repeatable. I'd love to help test that: I could put together a small set of messy cases (shifted fixtures, warped plates, tacks in the path), each with the right answer written down, so you can score the vision system against them.",
      proof=PROOF, extra="Getting a robot to hit its target when the field isn't where the code expects is most of what I do."),
 dict(n="Azalea Robotics", tier="C", contact="David Millard", role="Co-founder", to="founders@azalearobotics.com", st="guess",
      web="https://azalearobotics.com", subj="Help with baggage-handling test runs",
      value="Offer: failure logging and scripts that sort runs by failure type",
      body="Bags are a hard manipulation problem: soft, oddly shaped, and never stacked the same way twice. I'd love to help Azalea with the unglamorous side of testing, like logging every failed pick with a short note on why, or writing simple scripts that sort runs by failure type.",
      proof=PROOF, extra="Most of my time goes into figuring out why a run failed and fixing it before the next one."),
 dict(n="Weave Robotics", tier="C", contact="Kaan Dogrusoz", role="Co-founder", to="founders@weaverobotics.com", st="guess",
      web="https://www.weaverobotics.com", subj="Testing help for Isaac",
      value="Offer: failure logs from recorded home runs; no open roles listed",
      body="A robot that tidies a home has to handle everything a demo skips: socks under the couch, a backpack dropped in the hallway, a pet in the way. I'd love to help with testing, whether that's writing up failure logs from recorded runs or building small tools that sort them by what went wrong.",
      proof=PROOF, extra=""),
 dict(n="Vendra", tier="B", contact="Anish Bhardwaj", role="Co-founder", to="founders@vendra.io", st="guess",
      web="https://vendra.io", subj="New-user notes on your RFQ flow",
      value="Offer: run real robot parts through the RFQ flow and report where a first-time user gets stuck",
      body="I design robot parts in Fusion 360 all the time, so I'm close to the engineer who'd use Vendra, just younger. I'd love to take a few real parts from my team's robot through your RFQ process and send you honest notes on where a first-time user gets stuck, from file upload to tolerances to the quote.",
      proof=PROOF_CAD, extra=""),
 dict(n="Loombotic", tier="B", contact="Ethan Breit", role="Co-founder", to="founders@loombotic.com", st="guess",
      web="https://www.loombotic.com", subj="A first-timer's guide to ordering a harness",
      value="Offer: plain-English guide for hardware teams ordering their first harness; hiring in 3 areas",
      body="I saw Loombotic is hiring across marketing, support, and engineering. Wiring is one of the least-loved parts of building a robot, so harnesses in as little as 7 days caught my eye. I'd love to help with something small, like writing a plain-English guide for hardware teams ordering their first harness (what files to send, common mistakes), or testing your ordering flow as a new user.",
      proof=PROOF, extra=""),
 dict(n="Forge Automation", tier="B", contact="Walter Raftus", role="Co-founder", to="founders@forgeautomation.ca", st="guess",
      web="https://www.forgeautomation.ca", subj="New-user report on uploading a part",
      value="Offer: upload real robot parts and write a new-user report on the CAD-to-quote experience",
      body="Giving mechanical engineers the Amazon experience for custom metal parts is exactly what I'd want when I design custom parts. I'd love to upload a few of my team's real parts and write you a short report on the experience as a new user: what was clear, what wasn't, and where I almost gave up.",
      proof=PROOF_CAD, extra=""),
 dict(n="Parametric", tier="C", contact="John Newsom", role="Co-founder", to="founders@parametric.company", st="guess",
      web="https://parametric.company", subj="Help with the boring details",
      value="Offer: test scripts, failure logging, small monitoring tools",
      body="Physical businesses that run themselves is a big idea, and the hard part is usually the boring details: sensors that drift, machines that jam, and edge cases nobody planned for. I'd love to help with any of that, like writing test scripts, logging failures, or building small monitoring tools.",
      proof=PROOF, extra=""),
 dict(n="Allus AI", tier="B", contact="Zhisen An", role="Co-founder", to="founders@allus.ai", st="guess",
      web="https://allus.ai", subj="Help around your vision model",
      value="Offer: label/check sample data, eval scripts, collect hard cases (ties to his 3D vision interest)",
      body="I'm really interested in computer vision, especially 3D and geometric vision, and Allus bringing a vision foundation model to real factory lines is something I'd love to learn from up close. I could help with the work around the model: checking sample data, writing evaluation scripts, or collecting hard cases where it gets things wrong.",
      proof=PROOF, extra=""),
 dict(n="Servo7", tier="C", contact="Pieter Becking", role="Co-founder", to="founders@servo7.com", st="guess",
      web="https://servo7.com", subj="Remote help tagging unload failures",
      value="Offer: remote tagging of failed picks by cause (Amsterdam-based)",
      body="Unloading loose-loaded containers is a great problem because every container is different. I'm in the Seattle area, so I'd love to help remotely with something like going through recorded runs and tagging every failed pick by cause, so your team can see which box situations cost the most time.",
      proof=PROOF, extra=""),
 dict(n="Aseon Labs", tier="B", contact="George Kalligeros", role="Co-founder", to="founders@aseonlabs.com", st="guess",
      web="https://www.aseonlabs.com", subj="Small help on the pod build",
      value="Hiring 4 eng roles; offer: test fixtures, CAD for mounts, cycle logging",
      body="I saw Aseon is hiring for four engineering roles. Robotic pitstops for self-driving fleets mix mechanisms, sensing, and reliability, which is where I spend most of my time. I'd love to help with something small, like test fixtures, CAD for brackets and mounts, or scripts that log every servicing cycle.",
      proof=PROOF_CAD, extra=""),
 dict(n="Yummy Future", tier="B", contact="Jack Cui", role="Co-founder & CEO", to="founders@yummy-future.com", st="guess",
      web="https://www.yummy-future.com", subj="A robotics question, plus an offer",
      value="His YC profile invites robotics questions; hiring robotics engineers in Champaign",
      body="Your YC profile says to send robotics questions your way, so here's one, plus an offer. How do you keep a café arm consistent drink after drink, all day? Keeping a robot reliable over a long run is the problem I care most about. I'd love to help with something small, like logging and sorting arm faults or writing tests for a new drink routine.",
      proof=PROOF, extra=""),
 dict(n="BotBuilt", tier="B", contact="Brent Wadas", role="Co-founder & CEO", to="brent@botbuilt.com", st="guess",
      web="https://www.botbuilt.com", subj="Hoping to be your next high school intern",
      value="Brent mentioned a fast high school intern (Joseph) on a podcast; plan-to-robot-code fit",
      body="In a podcast interview you mentioned a high school intern, Joseph, whose pace caught you off guard. I'd love the chance to do the same. Turning a PDF plan into robot code for framing is exactly the kind of plan-to-motion problem I like working on.",
      proof=PROOF_CAD, extra=""),
 dict(n="JITX", tier="B", contact="Duncan Haldane", role="Co-founder & CEO", to="duncan@jitx.com", st="guess",
      web="https://www.jitx.com", subj="Beginner's write-up of designing a board in JITX",
      value="Offer: design a simple sensor board as a brand-new user and write up where beginners get stuck",
      body="I read that JITX grew out of how painful it was to design the boards for Salto by hand. I'm newer to board design, so I'd love to try designing a simple sensor board in JITX as a brand-new user and send you a write-up of where a beginner gets stuck, from setup through layout.",
      proof=PROOF, extra=""),
 dict(n="Nextera Robotics", tier="B", contact="Alex Rand", role="Co-founder & CTO", to="alex@nexterarobotics.com", st="guess",
      web="https://nexterarobotics.com", subj="Navigation help from a VEX programmer",
      value="Autonomous navigation role open to new grads; offer: replay logs to find localization drift",
      body="I saw your autonomous navigation role is open to new grads. I'm not one yet, but navigation is what I work on: odometry, sensor fusion, and getting a robot to know where it is when the wheels slip. I'd love to help with something small, like replaying logged runs to find where localization drifts.",
      proof=PROOF, extra=""),
 dict(n="PerfectBit", tier="C", contact="Péter Vajda", role="Co-founder", to="founders@perfectbit.ai", st="guess",
      web="https://perfectbit.ai", subj="Policies that hold up outside the lab",
      value="Hiring researchers (senior); offer: eval scripts, failure catalogs",
      body="PerfectBit's focus on policies that hold up outside the lab is the part of robotics I find most interesting. In VEX, a routine that works perfectly at home can fall apart at a tournament because the field is slightly different. I'd love to help with something small, like running evaluation scripts or cataloging failure cases.",
      proof=PROOF, extra=""),
 dict(n="Intelline", tier="C", contact="Kyle Faller", role="Co-founder & CEO", to="kyle@intelline.ca", st="guess",
      web="https://www.intelline.ca", subj="Test-bench data help",
      value="Hiring an ECU engineer; offer: test-data dashboard, scripts to flag odd bench runs",
      body="I saw you're hiring an ECU engineer. Control code is what I write, so an engine that can switch fuels while running is fascinating to me. I'd love to help with something small, like a dashboard for test-bench data or scripts that flag odd runs.",
      proof=PROOF, extra=""),
 dict(n="Vorticity", tier="C", contact="Chirath Neranjena", role="Founder & CEO", to="hello@vorticity.xyz", st="public",
      web="https://vorticity.xyz", subj="Reference tests for simple PDE problems",
      value="New-grad C++/CUDA roles; offer: reference solutions and tests for simple PDEs",
      body="I saw Vorticity's new-grad scientific computing roles. I'm a lot younger than that, but I write C++ every day and I'd love to learn how PDE solvers get mapped onto custom silicon. I could help with something small, like writing reference solutions and tests for simple problems (the heat equation, a basic flow case) to check results against.",
      proof=PROOF, extra=""),
 dict(n="Nine Fives", tier="B", contact="Noah", role="Founder", to="noah@ninefives.com", st="used in Aug, no bounce",
      web="https://ninefives.com", subj="Re: Not your average intern candidate", reply="1a006076301d820f",
      value="Follow-up to Aug 15 email; offer: test-sequence scripts, new-user API notes",
      body="Following up on my note from August with something more concrete. I'd love to help with the unglamorous parts of a test rack: writing scripts that run your gear through a test sequence and log the results, or trying your API as a new user and writing up where I got stuck.\n\nI write the autonomous code for my VEX team (C++, PID, odometry), and we're ranked 12th in the world in Robot Skills. Would you be open to a quick call?",
      proof="", extra=""),
 dict(n="Intelligence Factory", tier="C", contact="Jalaj", role="Founder", to="jalaj@intelligence-factory.com", st="used in Aug, no bounce",
      web="https://intelligence-factory.com", subj="Re: Not your average intern candidate", reply="1a00606ef72168af",
      value="Follow-up to Aug 15 email; offer: record/label demonstrations, sort failed runs",
      body="Following up on my note from August. Your idea of training robots the way people learn, by seeing, doing, and feeling, is a big part of why I wrote. I'd love to help with something small, like recording and labeling demonstrations or sorting failed runs by cause.\n\nI write the autonomous code for my VEX team (C++, PID, odometry), and we're ranked 12th in the world in Robot Skills. Would you be open to a quick call?",
      proof="", extra=""),
]

def first(name):
    return name.split()[0]

def email(c):
    if c.get("reply"):
        return f"Hi {first(c['contact'])},\n\n{c['body']}\n\nThanks,\nVenkat"
    p = c["proof"] + ((" " + c["extra"]) if c["extra"] else "")
    return f"Hi {first(c['contact'])},\n\n{c['body']}\n\n{p}\n\n{ASK}\n\n{SIG}"

if __name__ == "__main__":
    import json
    out = [dict(c, email=email(c)) for c in C]
    bad = [c["n"] for c in out if "\u2014" in c["email"] or "\u2013" in c["email"]]
    print(len(out), "companies; em/en dashes in:", bad)
    for c in out: print(c["n"], len(c["email"].split()), "words")
    json.dump(out, open("/home/claude/batch3.json", "w"), indent=1, ensure_ascii=False)
