"""Regenerate per-company files and tracker.xlsx from data/batch*.py.

Usage: python scripts/build.py [output_tracker_path]
Keeps any manual edits in the existing tracker's status columns (Status, Date sent,
Follow-up sent, Response, Notes) by matching on company slug.
"""
import importlib.util, os, sys, re, datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIG = "Thanks,\nVenkat Narayanan\ngithub.com/Venkat960407"
ASK = ("I'm a sophomore, so I know this is unusual, but I'd love to help with something small, "
       "part-time now or this summer. Would you be open to a quick 15-minute call?")


def load_batches():
    out = []
    for f in sorted(os.listdir(os.path.join(ROOT, "data"))):
        m = re.match(r"batch(\d+)\.py$", f)
        if not m:
            continue
        spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(ROOT, "data", f))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for c in mod.COMPANIES:
            c = dict(c); c["batch"] = int(m.group(1)); c["proof_text"] = mod.PROOF[c["proof"]]
            out.append(c)
    return out


def email_body(c):
    intro = "I'm Venkat, a high school programmer" + ("" if "Redmond" in c["opener"] else " in Redmond") + "."
    return (f"Hi {c['first']},\n\n{c['opener']}\n\n{intro} {c['proof_text']} {c['why']}\n\n{ASK}\n\n{SIG}")


def followup(c):
    return (f"Hi {c['first']},\n\nJust bumping this in case it got buried. Still happy to help with anything small "
            f"if it's useful.\n\nThanks,\nVenkat")


def write_company_files(cos):
    d = os.path.join(ROOT, "companies"); os.makedirs(d, exist_ok=True)
    for i, c in enumerate(cos, 1):
        c["file"] = f"companies/{c['batch']:02d}-{i:02d}-{c['slug']}.md"
        body = email_body(c)
        c["words"] = len(re.findall(r"\S+", body.split("Thanks,")[0]))
        verify = "Open the site and confirm this before sending." if c["build"] is None else \
                 "Fill in [BUILD LINK] and [ONE LINE ON WHAT IT DOES] once the build is done and you've read it."
        md = f"""# {c['name']}

| | |
|---|---|
| Tier | {c['tier']} |
| YC batch | {c['yc']} |
| Team size | {c['size']} |
| Location | {c['loc']} |
| Website | {c['website']} |
| YC page | https://www.ycombinator.com/companies/{c['slug']} |
| Contact | {c['contact']}, {c['role']} |
| Email | {c['email']} ({c['email_status']}) |

**What they do:** {c['what']}

**Value item:** {c['value']}

**Build:** {c['build'] or 'None (observation only)'}

**Notes:** {c['notes']}

> Before sending: {verify}

## Email

**Subject:** {c['subject']}

```
{body}
```

## Follow-up (send 5 to 7 days later, same thread)

```
{followup(c)}
```
"""
        open(os.path.join(ROOT, c["file"]), "w").write(md)


COLS = ["#", "Batch", "Company", "Tier", "Contact", "Role", "Email", "Email status", "What they do",
        "Value item", "Build", "Proof used", "Subject", "Status", "Date sent", "Follow-up due",
        "Follow-up sent", "Response", "Notes", "Draft file", "Website", "YC page"]
KEEP = ["Status", "Date sent", "Follow-up sent", "Response", "Notes"]
WIDTH = {"#": 4, "Batch": 6, "Company": 18, "Tier": 5, "Contact": 18, "Role": 18, "Email": 28,
         "Email status": 18, "What they do": 45, "Value item": 55, "Build": 30, "Proof used": 9,
         "Subject": 32, "Status": 16, "Date sent": 11, "Follow-up due": 12, "Follow-up sent": 12,
         "Response": 25, "Notes": 40, "Draft file": 30, "Website": 26, "YC page": 30}
STATUSES = ["Waiting on build", "Ready to review", "Verified", "Sent", "Followed up", "Replied",
            "Call scheduled", "No reply", "Skip"]


def build_tracker(cos, path):
    prev = {}
    if os.path.exists(path):
        wb0 = load_workbook(path); ws0 = wb0["Tracker"]
        hdr = [c.value for c in ws0[1]]
        for row in ws0.iter_rows(min_row=2, values_only=True):
            r = dict(zip(hdr, row))
            if r.get("Company"):
                prev[r["Company"]] = {k: r.get(k) for k in KEEP}

    wb = Workbook(); ws = wb.active; ws.title = "Tracker"
    f = Font(name="Arial", size=10); fb = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="1F3A5F")
    edit_fill = PatternFill("solid", fgColor="FFF4CC")
    thin = Side(style="thin", color="D0D0D0")
    for j, h in enumerate(COLS, 1):
        cell = ws.cell(row=1, column=j, value=h); cell.font = fb; cell.fill = hdr_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = WIDTH[h]
    ci = {h: j for j, h in enumerate(COLS, 1)}
    for i, c in enumerate(cos, 2):
        old = prev.get(c["name"], {})
        status = old.get("Status") or ("Waiting on build" if c["build"] else "Ready to review")
        vals = {"#": i - 1, "Batch": c["batch"], "Company": c["name"], "Tier": c["tier"],
                "Contact": c["contact"], "Role": c["role"], "Email": c["email"],
                "Email status": c["email_status"], "What they do": c["what"], "Value item": c["value"],
                "Build": c["build"] or "", "Proof used": c["proof"], "Subject": c["subject"],
                "Status": status, "Date sent": old.get("Date sent"),
                "Follow-up sent": old.get("Follow-up sent"), "Response": old.get("Response"),
                "Notes": old.get("Notes") if old.get("Notes") is not None else c["notes"],
                "Draft file": c["file"], "Website": c["website"],
                "YC page": f"https://www.ycombinator.com/companies/{c['slug']}"}
        for h, v in vals.items():
            cell = ws.cell(row=i, column=ci[h], value=v)
            cell.font = f; cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=thin)
            if h in KEEP:
                cell.fill = edit_fill
        ds = get_column_letter(ci["Date sent"]); fs = get_column_letter(ci["Follow-up sent"])
        fu = ws.cell(row=i, column=ci["Follow-up due"],
                     value=f'=IF({ds}{i}="","",IF({fs}{i}<>"","done",{ds}{i}+6))')
        fu.font = f; fu.number_format = "mmm d"; fu.alignment = Alignment(vertical="top")
        for h in ["Date sent", "Follow-up sent"]:
            ws.cell(row=i, column=ci[h]).number_format = "mmm d"
        for h in ["Website", "YC page"]:
            cell = ws.cell(row=i, column=ci[h]); cell.hyperlink = cell.value
            cell.font = Font(name="Arial", size=10, color="1155CC", underline="single")
    n = len(cos) + 1
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f"{get_column_letter(ci['Status'])}2:{get_column_letter(ci['Status'])}{n}")
    ws.freeze_panes = "D2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{n}"

    sm = wb.create_sheet("Summary")
    st = get_column_letter(ci["Status"]); tr = get_column_letter(ci["Tier"])
    rows = [("Companies", f"=COUNTA(Tracker!C2:C{n})")]
    rows += [(s, f'=COUNTIF(Tracker!{st}2:{st}{n},"{s}")') for s in STATUSES]
    rows += [("", None), ("Tier A (build)", f'=COUNTIF(Tracker!{tr}2:{tr}{n},"A")'),
             ("Tier B", f'=COUNTIF(Tracker!{tr}2:{tr}{n},"B")'), ("Tier C", f'=COUNTIF(Tracker!{tr}2:{tr}{n},"C")'),
             ("", None), ("Reply rate (of sent)",
              f'=IFERROR((B{2+STATUSES.index("Replied")+1}+B{2+STATUSES.index("Call scheduled")+1})/'
              f'(B{2+STATUSES.index("Sent")+1}+B{2+STATUSES.index("Followed up")+1}+B{2+STATUSES.index("Replied")+1}'
              f'+B{2+STATUSES.index("Call scheduled")+1}+B{2+STATUSES.index("No reply")+1}),"-")')]
    sm.cell(row=1, column=1, value="Metric").font = fb; sm.cell(row=1, column=1).fill = hdr_fill
    sm.cell(row=1, column=2, value="Count").font = fb; sm.cell(row=1, column=2).fill = hdr_fill
    for r, (k, v) in enumerate(rows, 2):
        sm.cell(row=r, column=1, value=k).font = f
        c2 = sm.cell(row=r, column=2, value=v); c2.font = f
        if k.startswith("Reply rate"):
            c2.number_format = "0%"
    sm.column_dimensions["A"].width = 22; sm.column_dimensions["B"].width = 10

    lg = wb.create_sheet("How to use")
    notes = [
        "Yellow columns on Tracker are yours to edit: Status, Date sent, Follow-up sent, Response, Notes.",
        "Claude regenerates everything else each batch and keeps what you typed in the yellow columns.",
        "Follow-up due fills in 6 days after Date sent, and says 'done' once Follow-up sent has a date.",
        "Emails marked 'guess' in Email status are unverified. Check with Hunter.io or Apollo before sending.",
        "Every value item needs a quick check on the live site before you send.",
        "Tier A = Claude builds something for them. Tier B = strong observation. Tier C = lighter fit.",
        "Full drafts and follow-ups are in the repo under companies/ (path in Draft file).",
        "Close this file before asking Claude for the next batch, so it can be saved over.",
    ]
    for r, t in enumerate(notes, 1):
        c3 = lg.cell(row=r, column=1, value=t); c3.font = f
    lg.column_dimensions["A"].width = 110
    wb.save(path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tracker.xlsx")
    cos = load_batches()
    write_company_files(cos)
    build_tracker(cos, out)
    for c in cos:
        print(f"{c['name']:<20} words={c['words']}")
