"""Synthetic clinical note generator for PHI de-identification training data.

All values are synthetic (Faker + hand-written pools); no real patient data is
used anywhere.  Notes are composed from clinical-note templates (H&P, SOAP,
discharge summary, referral letter, radiology, ED, psych, telehealth, op note,
pathology, billing, voicemail).  Entity spans are tracked during construction,
so gold labels are correct by construction (no post-hoc matching).

Deliberate variation:
  * date formats (MM/DD/YYYY, "March 5, 2024", 2024-03-05, 05-Mar-2024, ...)
  * name styles (Dr. X, LAST-FIRST headers, misspellings, hyphens, suffixes)
  * ages mostly <= 89 (kept) with ~15% over 89 (masked AGE entities)
  * adversarial traps: clinicians named after diseases, place-like person
    names, state names that must be kept, relative dates that must be kept.

Usage:  python -m phi_gateway.data_gen [--n-train 3000] [--n-dev 300]
Output: data/train.jsonl, data/dev.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --------------------------------------------------------------------------
# Pools
# --------------------------------------------------------------------------

EponYM_SURNAMES = [  # clinicians with these surnames -> disease mentions are O
    "Parkinson", "Huntington", "Bell", "Crohn", "Graves", "Hodgkin",
    "Alzheimer", "Lynch", "Addison", "Cushing", "Meniere", "Raynaud",
    "Turner", "Marfan", "Barrett",
]
EponYM_DISEASES = {
    "Parkinson": ["Parkinson's disease", "Parkinson disease", "PD"],
    "Huntington": ["Huntington's disease", "Huntington disease"],
    "Bell": ["Bell's palsy"],
    "Crohn": ["Crohn's disease", "Crohn disease"],
    "Graves": ["Graves' disease", "Graves disease"],
    "Hodgkin": ["Hodgkin's lymphoma"],
    "Alzheimer": ["Alzheimer's dementia", "Alzheimer disease"],
    "Lynch": ["Lynch syndrome"],
    "Addison": ["Addison's disease"],
    "Cushing": ["Cushing's syndrome"],
    "Meniere": ["Meniere's disease"],
    "Raynaud": ["Raynaud's phenomenon"],
    "Turner": ["Turner syndrome"],
    "Marfan": ["Marfan syndrome"],
    "Barrett": ["Barrett's esophagus"],
}

# First names that collide with US places (person NAME vs place NAME traps)
PLACE_FIRST_NAMES = ["Austin", "Charlotte", "Jackson", "Lincoln", "Madison",
                     "Houston", "Brooklyn", "Georgia", "Virginia", "Orlando",
                     "Denver", "Phoenix", "Dallas", "Trevor"]

STATE_ABBRS = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
               "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
               "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
               "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
               "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

FACILITIES = [
    "St. Vincent Medical Center", "Riverside General Hospital",
    "Mercy West Hospital", "Lakeview Regional Medical Center",
    "Northgate Family Clinic", "Summit Health Pavilion",
    "Pinegrove Community Hospital", "Eastside Surgical Center",
    "Harborview Urgent Care", "Cedar Hills Psychiatric Center",
    "Maplewood Rehabilitation and Nursing Center",
    "Bright Path Behavioral Health", "Copperfield Dialysis Center",
    "Two Rivers Imaging Center", "Meadowbrook Women's Health",
    "Silver Springs Assisted Living", "Fairhaven Hospice Center",
    "Grandview Orthopedic Associates", "Downtown Health Alliance",
    "Willow Creek Pediatrics", "Redstone VA Clinic",
]
CLINICS = ["Cardiology Associates", "Family Medicine of Fairview",
           "Lakeshore Internal Medicine", "Westside Neurology Group",
           "Ironwood Orthopedics", "Bluebird Pediatrics",
           "Stonebridge Behavioral Health", "Cornerstone Urology"]

CONDITIONS = ["type 2 diabetes mellitus", "hypertension", "congestive heart failure",
              "COPD", "atrial fibrillation", "chronic kidney disease stage 3",
              "coronary artery disease s/p PCI", "hyperlipidemia",
              "hypothyroidism", "osteoarthritis", "major depressive disorder",
              "generalized anxiety disorder", "asthma", "GERD",
              "obstructive sleep apnea", "ischemic stroke", "seizure disorder",
              "peripheral vascular disease", "iron deficiency anemia"]

SYMPTOMS = ["chest pain", "shortness of breath", "fever", "productive cough",
            "abdominal pain", "headache", "dizziness", "fatigue",
            "palpitations", "bilateral leg swelling", "acute confusion",
            "low back pain", "nausea and vomiting", "diarrhea", "dysuria",
            "polyarticular joint pain", "left-hand numbness",
            "word-finding difficulty", "syncope", "unintentional weight loss"]

MEDS = [
    "metformin 1000 mg BID", "lisinopril 20 mg daily", "atorvastatin 40 mg QHS",
    "apixaban 5 mg BID", "metoprolol succinate 25 mg daily",
    "gabapentin 300 mg TID", "omeprazole 20 mg daily", "sertraline 50 mg daily",
    "insulin glargine 24 units QHS", "albuterol MDI PRN",
    "hydrochlorothiazide 25 mg daily", "amlodipine 5 mg daily",
    "warfarin 5 mg daily (INR monitored)", "levothyroxine 75 mcg daily",
    "pantoprazole 40 mg daily", "furosemide 40 mg daily",
    "carvedilol 6.25 mg BID", "spironolactone 25 mg daily",
    "clopidogrel 75 mg daily", "prednisone taper per protocol",
]

RELATIVES = ["husband", "wife", "mother", "father", "son", "daughter",
             "brother", "sister", "granddaughter", "grandson", "niece",
             "nephew", "cousin", "neighbor", "friend", "caregiver"]

DEPARTMENTS = ["Internal Medicine", "Family Medicine", "Cardiology",
               "Emergency Department", "General Surgery", "Neurology",
               "Psychiatry", "Orthopedics", "ICU", "Telemetry Unit",
               "Laboratory", "Radiology"]

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTHS_ABBR = [m[:3] for m in MONTHS]

RELATIVE_TIMES = [
    "3 days post-op", "two weeks ago", "five days ago", "over the last month",
    "since last visit", "POD #2", "post-op day 5", "for 3 weeks",
    "the day before admission", "several months", "six hours",
    "two days prior", "3 weeks s/p catheterization", "overnight",
    "this morning", "yesterday evening", "for the past 48 hours",
]


# --------------------------------------------------------------------------
# NoteBuilder: accumulates (text, label) parts and tracks entity offsets
# --------------------------------------------------------------------------

class NoteBuilder:
    def __init__(self):
        self.parts: list[str] = []
        self.entities: list[dict] = []
        self._pos = 0

    def t(self, text: str) -> "NoteBuilder":
        """Add plain (non-PHI) text."""
        self.parts.append(text)
        self._pos += len(text)
        return self

    def e(self, text: str, label: str) -> "NoteBuilder":
        """Add an entity span with its label."""
        start = self._pos
        self.parts.append(text)
        self._pos += len(text)
        self.entities.append(
            {"start": start, "end": self._pos, "label": label, "value": text})
        return self

    def line(self, *chunks, sep: str = " ") -> "NoteBuilder":
        """Add chunks (str or (text,label)) separated by sep, then newline."""
        for i, c in enumerate(chunks):
            if i:
                self.t(sep)
            if isinstance(c, tuple):
                self.e(c[0], c[1])
            else:
                self.t(c)
        return self.t("\n")

    def mixed(self, parts: list) -> "NoteBuilder":
        """Add a list of str or (text, label-or-None) chunks."""
        for c in parts:
            if isinstance(c, tuple):
                if c[1]:
                    self.e(c[0], c[1])
                else:
                    self.t(c[0])
            else:
                self.t(c)
        return self

    def build(self, template: str) -> dict:
        return {
            "text": "".join(self.parts),
            "entities": sorted(self.entities, key=lambda e: e["start"]),
            "template": template,
        }


# --------------------------------------------------------------------------
# Value makers (each returns str or (text, label) tuples)
# --------------------------------------------------------------------------

class ValueFactory:
    def __init__(self, fk: Faker, rng: random.Random):
        self.fk = fk
        self.rng = rng

    # ---- names ----------------------------------------------------------

    def _misspell(self, name: str) -> str:
        if self.rng.random() > 0.10 or len(name) < 4:
            return name
        i = self.rng.randrange(1, len(name) - 1)
        kind = self.rng.random()
        if kind < 0.4:      # swap two adjacent letters
            name = name[:i] + name[i + 1] + name[i] + name[i + 2:]
        elif kind < 0.7:    # double a letter
            name = name[:i] + name[i] + name[i:]
        else:               # drop a letter
            name = name[:i] + name[i + 1:]
        return name

    def person_name(self, style: str | None = None) -> str:
        """Full personal name, optionally place-flavored or eponym-flavored."""
        first = self.fk.first_name()
        last = self.fk.last_name()
        if style == "place" and self.rng.random() < 0.8:
            first = self.rng.choice(PLACE_FIRST_NAMES)
        if style == "eponym" and self.rng.random() < 0.8:
            last = self.rng.choice(EponYM_SURNAMES)
        return f"{first} {last}"

    def patient_name(self) -> tuple[str, str]:
        """(display_name, surname_for_prose)"""
        n = self.person_name()
        r = self.rng.random()
        if r < 0.08:
            n += f" {self.rng.choice(['Jr.', 'Sr.', 'II', 'III'])}"
        elif r < 0.14:
            first, last = n.split(" ", 1)
            n = f"{first} {self.rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}. {last}"
        elif r < 0.18:
            first, last = n.split(" ", 1)
            n = f"{first}-{self.fk.first_name()} {last}"
        return self._misspell_punct(n)

    def _misspell_punct(self, n: str) -> tuple[str, str]:
        # occasionally misspell one word (keep label on the misspelled form)
        words = n.split(" ")
        idx = self.rng.randrange(len(words))
        words[idx] = self._misspell(words[idx])
        n = " ".join(words)
        surname = words[-1]
        return n, surname

    def clinician(self) -> tuple[str, str]:
        """(entity_text, surname) — 'Dr. F Last' or 'F Last' (creds separate)."""
        n = self.person_name()
        first, last = n.split(" ", 1)
        style = self.rng.random()
        if style < 0.45:
            text = f"Dr. {first} {last}"
        elif style < 0.6:
            text = f"Dr. {first[0]}. {last}"
        else:
            text = f"{first} {last}"
        return self._misspell_punct(text)

    def header_name(self, full: str) -> str:
        """'LAST, FIRST' style for headers (suffixes like 'II' dropped)."""
        parts = [p for p in full.split(" ")
                 if p.rstrip(".").upper() not in ("JR", "SR", "II", "III", "IV")]
        first, last = parts[0], parts[-1]
        return f"{last.upper()}, {first.upper()}"

    # ---- locations ------------------------------------------------------

    def facility(self) -> str:
        if self.rng.random() < 0.65:
            return self.rng.choice(FACILITIES)
        city = self.fk.city()
        kind = self.rng.choice(
            ["General Hospital", "Regional Medical Center", "Health Center",
             "Community Hospital", "Medical Group", "Memorial Hospital"])
        saint = self.rng.choice(["St. ", ""])
        base = city.replace(" ", "")
        return f"{saint}{base} {kind}"

    def street(self) -> str:
        n = self.rng.randint(10, 9999)
        name = self.fk.street_name()
        suffix = self.rng.choice(
            ["St", "St.", "Ave", "Ave.", "Rd", "Rd.", "Blvd", "Blvd.",
             "Ln", "Dr", "Dr.", "Ct", "Way", "Ter", "Pl"])
        s = f"{n} {name} {suffix}"
        if self.rng.random() < 0.3:
            unit = self.rng.choice(["Apt", "Apt.", "Suite", "Ste", "Unit", "#"])
            s += f" {unit} {self.rng.randint(1, 999)}"
            if self.rng.random() < 0.3:
                s += self.rng.choice("ABCDEFG")
        return s

    def city_state_zip(self) -> list:
        """[city-entity, ', ' plain, state plain, ' ' plain, zip-entity] parts."""
        city = self.fk.city()
        state = self.rng.choice(STATE_ABBRS)
        if self.rng.random() < 0.2:
            state = self.fk.state()  # full state name, still kept
        zipc = (self.fk.zipcode_plus4() if self.rng.random() < 0.25
                else self.fk.zipcode())
        return [(city, "LOCATION"), f", {state} ", (zipc, "LOCATION")]

    # ---- dates ----------------------------------------------------------

    def rand_date(self, y0: int = 2014, y1: int = 2026) -> date:
        d0 = date(y0, 1, 1)
        return d0 + timedelta(days=self.rng.randint(0, (date(y1, 6, 1) - d0).days))

    def date_entity(self) -> tuple[str, str]:
        d = self.rand_date()
        fmt = self.rng.random()
        if fmt < 0.22:
            text = f"{d.month:02d}/{d.day:02d}/{d.year}"
        elif fmt < 0.36:
            text = f"{d.month}/{d.day}/{d.year}"
        elif fmt < 0.46:
            text = f"{d.year}-{d.month:02d}-{d.day:02d}"
        elif fmt < 0.58:
            text = f"{MONTHS[d.month-1]} {d.day}, {d.year}"
        elif fmt < 0.68:
            text = f"{d.day}-{MONTHS_ABBR[d.month-1]}-{d.year}"
        elif fmt < 0.76:
            text = f"{d.day} {MONTHS[d.month-1]} {d.year}"
        elif fmt < 0.82:
            text = f"{MONTHS_ABBR[d.month-1]} {d.day}, {d.year}"
        elif fmt < 0.88:
            text = f"{d.month:02d}/{d.day:02d}/{str(d.year)[2:]}"
        elif fmt < 0.93:
            text = f"{MONTHS[d.month-1]} {d.year}"       # month+year
        elif fmt < 0.97:
            text = f"{d.month:02d}/{d.day:02d}"           # no year
        else:
            text = f"{d.day} {MONTHS[d.month-1]}"         # day+month
        return (text, "DATE")

    def year_only(self) -> str:
        return str(self.rng.randint(2012, 2026))

    def relative_time(self) -> str:
        return self.rng.choice(RELATIVE_TIMES)

    # ---- ages -----------------------------------------------------------

    def age_chunks(self, force_old: bool = False) -> list:
        """Age mention as parts; only >89 becomes an AGE entity."""
        old = force_old or self.rng.random() < 0.15
        n = self.rng.randint(90, 103) if old else self.rng.randint(18, 89)
        form = self.rng.random()
        if form < 0.45:
            parts = [(str(n), "AGE" if n > 89 else None), "-year-old"]
        elif form < 0.60:
            parts = [(str(n), "AGE" if n > 89 else None), " y.o."]
        elif form <0.72:
            parts = ["age ", (str(n), "AGE" if n > 89 else None)]
        elif form < 0.84:
            parts = ["aged ", (str(n), "AGE" if n > 89 else None)]
        elif form < 0.92:
            parts = [(str(n), "AGE" if n > 89 else None), " years of age"]
        else:
            parts = ["age of ", (str(n), "AGE" if n > 89 else None)]
        return parts

    # ---- contact --------------------------------------------------------

    def phone(self) -> tuple[str, str]:
        a, b, c = (self.fk.random_int(100, 999), self.fk.random_int(100, 999),
                   self.fk.random_int(1000, 9999))
        fmt = self.rng.random()
        if fmt < 0.22:
            text = f"({a}) {b}-{c}"
        elif fmt < 0.42:
            text = f"{a}-{b}-{c}"
        elif fmt < 0.58:
            text = f"{a}.{b}.{c}"
        elif fmt < 0.70:
            text = f"{a} {b} {c}"
        elif fmt < 0.80:
            text = f"+1-{a}-{b}-{c}"
        elif fmt < 0.90:
            text = f"{a}{b}{c}"
        else:
            ext = self.fk.random_int(1000, 9999)
            text = f"({a}) {b}-{c} x{ext}"
        return (text, "PHONE")

    def email(self, person: str | None = None) -> tuple[str, str]:
        if person and self.rng.random() < 0.5:
            handle = person.lower().replace(" ", ".").replace("..", ".")
            handle = "".join(ch for ch in handle if ch.isalnum() or ch == ".")
        else:
            handle = self.fk.user_name()
        domain = self.rng.choice(
            ["gmail.com", "yahoo.com", "outlook.com", "aol.com",
             "example-health.org", "mail.example-med.net", "comcast.net"])
        return (f"{handle}@{domain}", "EMAIL")

    # ---- identifiers ----------------------------------------------------

    def ssn(self) -> tuple[str, str]:
        if self.rng.random() < 0.75:
            text = f"{self.fk.random_int(100,899)}-{self.fk.random_int(10,99)}-{self.fk.random_int(1000,9999)}"
        else:
            text = f"{self.fk.random_int(100,899)} {self.fk.random_int(10,99)} {self.fk.random_int(1000,9999)}"
        return (text, "SSN")

    def mrn(self) -> tuple[str, str]:
        n = self.fk.random_int(100000, 99999999)
        if self.rng.random() < 0.2:
            return (f"{self.rng.choice('ABCDEFGH')}{n}", "MRN")
        return (str(n), "MRN")

    def healthplan(self) -> tuple[str, str]:
        style = self.rng.random()
        if style < 0.35:
            letters = "".join(self.rng.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
            text = f"{letters}{self.fk.random_int(100000, 999999)}"
        elif style < 0.6:
            text = f"{self.fk.random_int(100,999)}-{self.fk.random_int(100000,999999)}-{self.fk.random_int(10,99)}"
        elif style < 0.8:
            letters = "".join(self.rng.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
            text = f"{letters}-{self.fk.random_int(1000000, 9999999)}"
        else:
            text = f"{self.fk.random_int(10,99)}{self.rng.choice('ABCDEFGH')}{self.fk.random_int(100000, 999999)}"
        return (text, "HEALTHPLAN")

    def account(self) -> tuple[str, str]:
        style = self.rng.random()
        if style < 0.4:
            text = f"{self.fk.random_int(10000,99999)}-{self.fk.random_int(1000,9999)}"
        elif style < 0.7:
            text = str(self.fk.random_int(100000000, 999999999))
        else:
            text = f"AC{self.fk.random_int(1000000, 9999999)}"
        return (text, "ACCOUNT")

    def license(self, kind: str | None = None) -> tuple[str, str]:
        kind = kind or self.rng.choice(["dl", "dea", "npi"])
        if kind == "dea":
            letters = "".join(self.rng.choices("ABCDEFGHJKLM", k=2))
            text = f"{letters}{self.fk.random_int(1000000, 9999999)}"
        elif kind == "npi":
            text = str(self.fk.random_int(1000000000, 1999999999))
        else:
            text = f"{self.rng.choice('ABCDEFGH')}{self.fk.random_int(1000000, 9999999)}"
        return (text, "LICENSE")

    def url(self) -> tuple[str, str]:
        host = self.rng.choice(
            ["www.example-health.com", "portal.carelink-example.net",
             "mychart.example-med.org", "results.labexample.com",
             "www.southside-imaging-example.com"])
        if self.rng.random() < 0.35:
            return (f"https://{host}/login", "URL")
        if self.rng.random() < 0.3:
            return (f"{host}/appointments", "URL")
        return (host, "URL")

    def ip(self) -> tuple[str, str]:
        octets = [self.rng.choice(["192", "10", "172", "68", "76", "104", "209"])]
        octets += [str(self.fk.random_int(0, 254)) for _ in range(3)]
        return (".".join(octets), "IP")


# --------------------------------------------------------------------------
# Trap sentences (ambiguous eponyms, place-names, kept states)
# --------------------------------------------------------------------------

def trap_sentence(vf: ValueFactory) -> list | None:
    r = vf.rng.random()
    if r < 0.35:  # eponym clinician vs disease
        surname = vf.rng.choice(EponYM_SURNAMES)
        first = vf.fk.first_name()
        disease = vf.rng.choice(EponYM_DISEASES[surname])
        verb = vf.rng.choice(["diagnosed", "evaluated for", "manages",
                              "suspected", "ruled out"])
        if vf.rng.random() < 0.5:
            return [f"Dr. ", (f"{first} {surname}", "NAME"), f" {verb} ", disease, "."]
        return [f"Dr. {surname} ", (f"({first})", "NAME") if False else f"", disease, f" was reviewed."]
    if r < 0.55:  # person with place-like name + real state mention
        name = vf.person_name(style="place")
        state = vf.fk.state()
        city = vf.fk.city()
        return [
            (name.split(" ")[0], "NAME"), "'s family lives in ", state,
            ", though the patient resides in ", (city, "LOCATION"), " county.",
        ]
    if r < 0.7:  # state names kept, cities masked
        state = vf.rng.choice(STATE_ABBRS)
        city = vf.fk.city()
        return ["Transferred from ", (city, "LOCATION"), f", {state}, for higher-level care."]
    if r < 0.85:  # relative time kept next to calendar date
        return ["Symptoms began ", vf.relative_time(),
                " before the encounter of ", vf.date_entity(), "."]
    # year-only kept
    return ["First diagnosed in ", vf.year_only(),
            " and monitored annually since."]


def add_traps(b: NoteBuilder, vf: ValueFactory, p: float = 0.55) -> None:
    """Sprinkle 0-2 trap sentences into a note as their own paragraph."""
    if vf.rng.random() > p:
        return
    for _ in range(vf.rng.randint(1, 2)):
        parts = trap_sentence(vf)
        if parts is None:
            continue
        for c in parts:
            if isinstance(c, tuple):
                b.e(*c)
            else:
                b.t(c)
        b.t(" ")


# --------------------------------------------------------------------------
# Note templates
# --------------------------------------------------------------------------

def tpl_hp_note(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, surname = vf.patient_name()
    dr, _ = vf.clinician()
    age_parts = vf.age_chunks()
    b.line((vf.facility(), "LOCATION"))
    b.line(vf.rng.choice(DEPARTMENTS), "-", "History and Physical")
    b.t("\n")
    b.line("Date:", vf.date_entity(), "   Attending:", (dr, "NAME"))
    b.line("Patient:", (pname, "NAME"), "   MRN:", vf.mrn())
    b.line("DOB:", vf.date_entity(), "   Sex:", vf.rng.choice(["M", "F"]))
    b.t("\nChief Complaint: ")
    b.line(f'"{vf.rng.choice(SYMPTOMS)} x {vf.rng.choice(["2 days", "1 week", "3 days", "several hours"])}".')
    b.t("\nHPI: ")
    honor = "Mr." if vf.rng.random() < 0.5 else "Ms."
    b.t(f"{honor} {surname} is a ")
    b.mixed(age_parts)
    b.line(f" {vf.rng.choice(['male','female'])} with a history of",
           vf.rng.choice(CONDITIONS), f"who presents with {vf.rng.choice(SYMPTOMS)}.")
    b.line("Symptoms began", vf.relative_time() + ".")
    add_traps(b, vf)
    b.t("\nPMH:")
    for c in vf.rng.sample(CONDITIONS, vf.rng.randint(1, 3)):
        b.t(f" {c};")
    b.t("\nMedications:")
    for m in vf.rng.sample(MEDS, vf.rng.randint(3, 6)):
        b.t(f" {m};")
    b.t("\nAllergies: " + vf.rng.choice(["NKDA", "penicillin (rash)", "sulfa (hives)", "latex"]))
    b.t("\nSocial Hx: Lives at ")
    b.e(vf.street(), "LOCATION")
    b.t(" in ")
    city = vf.fk.city()
    b.e(city, "LOCATION")
    state = vf.rng.choice(STATE_ABBRS)
    b.t(f", {state} ")
    b.e(vf.fk.zipcode(), "LOCATION")
    rel = vf.rng.choice(RELATIVES)
    relname, _ = vf.patient_name()
    b.t(f" with {rel} ")
    b.e(relname, "NAME")
    b.t(". ")
    b.line(vf.rng.choice(
        ["Former smoker, quit 2019.", "Denies tobacco or alcohol use.",
         "Smokes half a pack daily.", "Works as a teacher."]))
    b.t("\nPhysical Exam: BP ")
    b.t(f"{vf.fk.random_int(90,180)}/{vf.fk.random_int(55,110)}, HR ")
    b.t(f"{vf.fk.random_int(50,120)}, RR {vf.fk.random_int(10,24)}, T ")
    b.t(f"{vf.fk.random_int(965, 1020)/10}. General: no acute distress.")
    b.t("\nAssessment/Plan: ")
    b.line(f"{vf.rng.choice(CONDITIONS)}; ", "start",
           f" {vf.rng.choice(['metoprolol', 'losartan', 'amlodipine'])},",
           " follow up in", vf.rng.choice(["2 weeks", "1 month", "3 days"]) + ".")
    if vf.rng.random() < 0.5:
        b.t("Contact office at ")
        b.e(*vf.phone())
        b.t(" or fax ")
        b.e(*vf.phone())
        b.t(".\n")
    if vf.rng.random() < 0.4:
        b.line("Patient portal:", vf.url())
    b.t("\nElectronically signed by ")
    sig, _ = vf.clinician()
    b.e(sig, "NAME")
    b.t(", MD, ")
    b.e(*vf.date_entity())
    b.t(" at ")
    b.t(f"{vf.fk.random_int(0,23):02d}:{vf.fk.random_int(0,59):02d}.")


def tpl_progress_note(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, surname = vf.patient_name()
    dr, _ = vf.clinician()
    b.line("PROGRESS NOTE - ICU")
    b.line("Hospital day:", str(vf.fk.random_int(1, 21)))
    b.line("Date:", vf.date_entity(), " Patient:", (pname, "NAME"),
           " MRN:", vf.mrn())
    b.t("\nS: Patient remains ")
    b.line(vf.rng.choice(["stable", "improved", "guarded", "critical"]) + ".",
           f"Endorses {vf.rng.choice(SYMPTOMS)}", vf.relative_time() + ".")
    b.line("Family updated by phone with", (vf.patient_name()[0], "NAME"), ".")
    b.t("\nO: T ")
    b.t(f"{vf.fk.random_int(965,1020)/10} C, HR {vf.fk.random_int(50,130)},")
    b.line(f"BP {vf.fk.random_int(85,180)}/{vf.fk.random_int(50,110)},")
    b.line(f"SpO2 {vf.fk.random_int(88,100)}% on", vf.rng.choice(["RA", "2L NC", "40% HFNC"]) + ".")
    b.t("Labs: WBC ")
    b.t(f"{vf.fk.random_int(2,19)}.{vf.fk.random_int(0,9)}, Hgb ")
    b.t(f"{vf.fk.random_int(6,16)}.{vf.fk.random_int(0,9)}, accession ")
    b.e(*vf.account())
    b.t(" drawn ")
    b.e(*vf.date_entity())
    b.t(".\n")
    add_traps(b, vf)
    b.t("\nA/P: Continue current antibiotics; assess for extubation")
    b.line(vf.rng.choice(["tomorrow", "in 48 hours", "today"]) + ".")
    if vf.rng.random() < 0.5:
        b.line("Wound culture from", vf.date_entity(), "grew",
               vf.rng.choice(["MSSA", "E. coli", "Klebsiella", "Pseudomonas"]) + ".")
    b.t("\nPager: ")
    b.e(*vf.phone())
    b.t("\n--- ")
    b.e(dr, "NAME")
    b.t(", MD, ")
    b.e(*vf.date_entity())


def tpl_discharge_summary(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    pcp, _ = vf.clinician()
    b.line("DISCHARGE SUMMARY")
    b.line("Patient:", (pname, "NAME"), "  MRN:", vf.mrn())
    b.line("Admitted:", vf.date_entity(), " Discharged:", vf.date_entity())
    b.line("Attending:", (vf.clinician()[0], "NAME"))
    b.t("\nHospital Course:\nPatient admitted for ")
    b.line(f"{vf.rng.choice(SYMPTOMS)}; treated supportively.",
           "Improved", vf.rng.choice(["over 3 days", "over the week", "by day 4"]) + ".")
    add_traps(b, vf)
    b.t("\nDischarge Medications:\n")
    b.t("Medication             | Start date\n")
    for m in vf.rng.sample(MEDS, vf.rng.randint(3, 5)):
        b.t(f"{m:<22}| ")
        b.e(*vf.date_entity())
        b.t("\n")
    b.t("\nDisposition: Discharged to ")
    b.e(vf.facility(), "LOCATION")
    b.t(" with home health. Follow-up with ")
    b.e(pcp, "NAME")
    b.t(" on ")
    b.e(*vf.date_entity())
    b.t(" at ")
    b.e(vf.rng.choice(CLINICS), "LOCATION")
    b.t(". Office ")
    b.e(*vf.phone())
    b.t(".\nInsurance on file: member ID ")
    b.e(*vf.healthplan())
    b.t(", account ")
    b.e(*vf.account())
    b.t(".\n")


def tpl_referral_letter(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    sender, _ = vf.clinician()
    b.line("RE: Referral -", (pname, "NAME"))
    b.line("DOB:", vf.date_entity(), " MRN:", vf.mrn())
    b.t("\nDear ")
    to_dr, _ = vf.clinician()
    b.e(to_dr, "NAME")
    b.t(":\n\nThank you for seeing this ")
    b.mixed(vf.age_chunks())
    b.line(f"-year-old patient with {vf.rng.choice(CONDITIONS)}.")
    b.line("I evaluated the patient on", vf.date_entity(), "at",
           (vf.rng.choice(CLINICS), "LOCATION"), ".")
    add_traps(b, vf)
    b.line("Assessment concerns:", vf.rng.choice(SYMPTOMS) + ".")
    b.t("\nPlease contact my office at ")
    b.e(*vf.phone())
    b.t(", fax ")
    b.e(*vf.phone())
    b.t(", or ")
    b.e(*vf.email(sender))
    b.t(".\n\nSincerely,\n\n")
    b.e(sender, "NAME")
    b.t(", MD\n")
    b.e(vf.rng.choice(CLINICS), "LOCATION")
    b.t("\n")
    b.e(vf.street(), "LOCATION")
    b.t("\n")
    for c in vf.city_state_zip():
        (b.e(*c) if isinstance(c, tuple) else b.t(c))
    b.t("\nOffice: ")
    b.e(*vf.phone())


def tpl_radiology(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    ref, _ = vf.clinician()
    rad, _ = vf.clinician()
    b.line((vf.facility(), "LOCATION"))
    b.line("RADIOLOGY REPORT")
    b.line("Exam:", vf.rng.choice(
        ["CT abdomen/pelvis with contrast", "Chest X-ray, 2 views",
         "MRI brain without contrast", "Ultrasound right lower extremity",
         "CT head without contrast", "Echocardiogram"]))
    b.line("Date:", vf.date_entity(), " Referring:", (ref, "NAME"))
    b.line("Patient:", (pname, "NAME"), " MRN:", vf.mrn(),
           " DOB:", vf.date_entity())
    b.t("\nHistory: ")
    b.mixed(vf.age_chunks())
    b.line(f"-year-old with {vf.rng.choice(SYMPTOMS)}.")
    b.t("\nFindings: ")
    b.line(vf.rng.choice([
        "No acute cardiopulmonary abnormality.",
        "Small right pleural effusion. No pneumothorax.",
        "1.2 cm hypoechoic focus in the right lobe; recommend follow-up imaging in 3 months.",
        "Mild diffuse cerebral volume loss. No acute infarct or hemorrhage.",
        "Noncompressible left popliteal vein, consistent with DVT."]))
    b.t("\nImpression: ")
    b.line(vf.rng.choice([
        "1. See findings. 2. Clinical correlation recommended.",
        "1. Negative study. 2. No further imaging indicated.",
        "1. Findings as above; recommend outpatient follow-up."]))
    add_traps(b, vf)
    b.t("\nElectronically signed by ")
    b.e(rad, "NAME")
    b.t(", MD on ")
    b.e(*vf.date_entity())
    b.t(". Results released via ")
    b.e(*vf.url())
    b.t(". Report ID ")
    b.e(*vf.account())
    b.t(".\n")


def tpl_ed_note(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, surname = vf.patient_name()
    b.line("EMERGENCY DEPARTMENT NOTE")
    b.line("Arrival:", vf.date_entity(),
           f" {vf.fk.random_int(0,23):02d}:{vf.fk.random_int(0,59):02d}")
    b.line("Patient:", (vf.header_name(pname), "NAME"))
    b.line("Mode of arrival: brought by EMS from ")
    b.e(vf.street(), "LOCATION")
    b.t(", ")
    b.e(vf.fk.city(), "LOCATION")
    b.t(".\n")
    b.t("Triage complaint: ")
    b.line(f"{vf.rng.choice(SYMPTOMS)} for {vf.rng.choice(['2 hours','1 day','3 days'])}.")
    add_traps(b, vf)
    b.t("\nED course: IV access obtained; labs (accession ")
    b.e(*vf.account())
    b.t(") and imaging ordered. Attending ")
    eddr, _ = vf.clinician()
    b.e(eddr, "NAME")
    b.t(", MD at bedside.\nNext of kin: ")
    kin, _ = vf.patient_name()
    b.e(kin, "NAME")
    b.t(" (")
    b.t(vf.rng.choice(["daughter", "son", "spouse", "brother", "sister"]))
    b.t(") reachable at ")
    b.e(*vf.phone())
    b.t(".\nDisposition: ")
    b.line(vf.rng.choice(["admitted to observation", "discharged home",
                          "admitted to medicine", "transferred to psychiatry"]) + ".")
    if vf.rng.random() < 0.5:
        b.line("Registration verified SSN on file:", vf.ssn())
    b.t("\nSigned: ")
    b.e(vf.clinician()[0], "NAME")
    b.t(", MD, ")
    b.e(*vf.date_entity())


def tpl_psych_note(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    clin, _ = vf.clinician()
    b.line("BEHAVIORAL HEALTH PROGRESS NOTE")
    b.line("Session date:", vf.date_entity())
    b.line("Client:", (pname, "NAME"), " Clinician:", (clin, "NAME"))
    b.t("\nThe client is a ")
    b.mixed(vf.age_chunks())
    b.line("-year-old who reports",
           vf.rng.choice(["persistent worry", "low mood", "panic episodes",
                          "sleep disturbance", "intrusive thoughts"]) + ".")
    b.line("Symptoms have persisted", vf.relative_time() + ".")
    add_traps(b, vf)
    b.line("PHQ-9:", str(vf.fk.random_int(4, 22)), "GAD-7:",
           str(vf.fk.random_int(3, 20)))
    b.t("\nPlan: weekly therapy; medication management with ")
    presc, _ = vf.clinician()
    b.e(presc, "NAME")
    b.t(". Client consented to email updates at ")
    b.e(*vf.email())
    b.t(". Telehealth sessions via ")
    b.e(*vf.url())
    b.t("; last login from IP ")
    b.e(*vf.ip())
    b.t(".\nCrisis line: ")
    b.e(*vf.phone())
    b.t(".\n")


def tpl_telehealth(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    dr, _ = vf.clinician()
    b.line("TELEHEALTH VISIT NOTE")
    b.line("Visit date:", vf.date_entity(), " Platform:", vf.url())
    b.line("Patient:", (pname, "NAME"), " Provider:", (dr, "NAME"))
    b.line("Patient location during visit: home in", (vf.fk.city(), "LOCATION"))
    b.line("Device IP verified:", vf.ip(), " Account email:", vf.email())
    b.t("\nPatient reports ")
    b.line(f"{vf.rng.choice(SYMPTOMS)}, ongoing {vf.rng.choice(['3 days','2 weeks','1 month'])}.")
    add_traps(b, vf)
    b.line("Plan: prescription sent to", (vf.facility() if vf.rng.random() < 0.3 else vf.fk.city() + " Pharmacy", "LOCATION"), ".")
    b.line("Follow-up video visit", vf.date_entity(), "; scheduler:",
           vf.phone())
    b.t("\nEscalation contact: ")
    b.e(*vf.phone())
    b.t(" (")
    b.t("answering service). Message portal: ")
    b.e(*vf.url())
    b.t(".\n")


def tpl_op_note(vf: ValueFactory, b: NoteBuilder) -> None:
    surgeon, _ = vf.clinician()
    assist, _ = vf.clinician()
    anes, _ = vf.clinician()
    b.line("OPERATIVE REPORT")
    b.line("Date of procedure:", vf.date_entity())
    b.line("Surgeon:", (surgeon, "NAME"), " Assistant:", (assist, "NAME"),
           " Anesthesiologist:", (anes, "NAME"))
    b.line("Facility:", (vf.facility(), "LOCATION"))
    b.line("Preoperative diagnosis:", vf.rng.choice(CONDITIONS))
    b.line("Procedure:", vf.rng.choice(
        ["laparoscopic cholecystectomy", "right total knee arthroplasty",
         "carpal tunnel release", "inguinal hernia repair",
         "coronary artery bypass grafting"]))
    b.t("\nESTIMATED BLOOD LOSS: ")
    b.line(f"{vf.rng.choice(['minimal','50 mL','100 mL','200 mL'])}.")
    b.t("SPECIMENS: sent to pathology, accession ")
    b.e(*vf.account())
    b.t(".\n")
    add_traps(b, vf)
    b.t("\nThe patient was identified and the site marked. Procedure begun at ")
    b.t(f"{vf.fk.random_int(7,19):02d}:{vf.fk.random_int(0,59):02d}. ")
    b.t("Details of the procedure are documented in the dictated record (ref ")
    b.e(*vf.account())
    b.t("). Surgeon DEA on file: ")
    b.e(*vf.license(kind="dea"))
    b.t(".\nElectronically signed: ")
    b.e(surgeon, "NAME")
    b.t(", MD, ")
    b.e(*vf.date_entity())


def tpl_path_lab(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    path, _ = vf.clinician()
    b.line("PATHOLOGY REPORT")
    b.line("Specimen collected:", vf.date_entity(), " Received:",
           vf.date_entity())
    b.line("Patient:", (pname, "NAME"), " DOB:", vf.date_entity(),
           " MRN:", vf.mrn())
    b.line("Accession:", vf.account(), " Patient account:", vf.account())
    b.t("\nSpecimen: ")
    b.line(vf.rng.choice(
        ["skin lesion, left shoulder", "core needle biopsy, right breast",
         "gallbladder", "colon polyps (2)", "thyroid lobe"]))
    b.t("\nMicroscopic: Sections show ")
    b.line(vf.rng.choice([
        "benign keratosis.", "fibroadenoma with no atypia.",
        "chronic cholecystitis.", "tubular adenoma with low-grade dysplasia.",
        "nodular hyperplasia."]))
    add_traps(b, vf)
    b.t("\nDiagnosis: ")
    b.line(vf.rng.choice([
        "1. Benign. 2. Recommend routine follow-up.",
        "1. See diagnosis. 2. No evidence of malignancy."]))
    b.t("\nFinal report issued ")
    b.e(*vf.date_entity())
    b.t(" by ")
    b.e(path, "NAME")
    b.t(", MD. Results delivered to patient portal ")
    b.e(*vf.url())
    b.t(" and email ")
    b.e(*vf.email())
    b.t(".\n")


def tpl_billing(vf: ValueFactory, b: NoteBuilder) -> None:
    pname, _ = vf.patient_name()
    b.line("REGISTRATION / BILLING SUMMARY")
    b.line("Guarantor:", (pname, "NAME"), " Account:", vf.account())
    b.line("Statement date:", vf.date_entity())
    b.line("Address on file:")
    b.e(vf.street(), "LOCATION")
    b.t("\n")
    for c in vf.city_state_zip():
        (b.e(*c) if isinstance(c, tuple) else b.t(c))
    b.t("\nDay phone: ")
    b.e(*vf.phone())
    b.t("  Evening: ")
    b.e(*vf.phone())
    b.t("\nEmail: ")
    b.e(*vf.email())
    b.t("\nCoverage: policy ")
    b.e(*vf.healthplan())
    b.t(", group ")
    b.e(*vf.account())
    b.t(". SSN on file for verification: ")
    b.e(*vf.ssn())
    b.t(".\nStatements available online: ")
    b.e(*vf.url())
    b.t("\nQuestions: billing office ")
    b.e(*vf.phone())
    b.t(", fax ")
    b.e(*vf.phone())
    b.t(". Driver license no. ")
    b.e(*vf.license(kind="dl"))
    b.t(".\n")


def tpl_voicemail(vf: ValueFactory, b: NoteBuilder) -> None:
    caller, _ = vf.patient_name()
    pname, _ = vf.patient_name()
    b.line("VOICEMAIL TRANSCRIPTION (automated)")
    b.line("Received:", vf.date_entity(),
           f" {vf.fk.random_int(6,21):02d}:{vf.fk.random_int(0,59):02d}")
    b.t("\n\"Hi, this is ")
    b.e(caller, "NAME")
    b.t(". I'm calling about my ")
    b.t(vf.rng.choice(["father", "mother", "wife", "husband", "son", "daughter"]))
    b.t(", ")
    b.e(pname, "NAME")
    b.t(". We have an appointment on ")
    b.e(*vf.date_entity())
    b.t(" and I need to confirm transportation. Please call me back at ")
    b.e(*vf.phone())
    b.t(". Thank you.\"\n")


def tpl_trap_dense(vf: ValueFactory, b: NoteBuilder) -> None:
    """A note densely packed with ambiguity traps."""
    pname, _ = vf.patient_name()
    b.line("NEUROLOGY CONSULT NOTE")
    b.line("Date:", vf.date_entity(), " Patient:", (pname, "NAME"))
    b.t("\nReason: evaluation of ")
    epon = vf.rng.choice(EponYM_SURNAMES)
    disease = vf.rng.choice(EponYM_DISEASES[epon])
    b.t(f"{disease} ")
    first = vf.fk.first_name()
    b.t(".\nOf note, ")
    b.t(f"Dr. {epon}" if vf.rng.random() < 0.5 else f"Dr. {first} {epon}")
    if vf.rng.random() < 0.5:
        b.t(f" (first name {first}")
        b.t(")")
    b.t(" previously followed this family for ")
    b.t(vf.rng.choice(EponYM_DISEASES[epon]))
    b.t(".\n")
    add_traps(b, vf, p=0.95)
    add_traps(b, vf, p=0.95)
    b.t("The patient's grandmother, ")
    gname, _ = vf.patient_name()
    b.e(gname, "NAME")
    b.t(", had ")
    b.t(vf.rng.choice(["Huntington disease", "Parkinson's disease", "Alzheimer dementia"]))
    b.t(" diagnosed in ")
    b.t(str(vf.rng.randint(1985, 2015)))
    b.t(".\nExam today (")
    b.e(*vf.date_entity())
    b.t("): tremor noted. Patient is ")
    b.mixed(vf.age_chunks(force_old=vf.rng.random() < 0.5))
    b.t(" years of age. Recommend follow-up ")
    b.e(*vf.date_entity())
    b.t(". Contact: ")
    b.e(*vf.phone())
    b.t(".\n")


TEMPLATES = [
    ("hp_note", tpl_hp_note, 0.18),
    ("progress_note", tpl_progress_note, 0.10),
    ("discharge_summary", tpl_discharge_summary, 0.10),
    ("referral_letter", tpl_referral_letter, 0.10),
    ("radiology", tpl_radiology, 0.10),
    ("ed_note", tpl_ed_note, 0.08),
    ("psych_note", tpl_psych_note, 0.07),
    ("telehealth", tpl_telehealth, 0.07),
    ("op_note", tpl_op_note, 0.06),
    ("path_lab", tpl_path_lab, 0.05),
    ("billing", tpl_billing, 0.05),
    ("voicemail", tpl_voicemail, 0.02),
    ("trap_dense", tpl_trap_dense, 0.02),
]


def make_note(vf: ValueFactory) -> dict:
    r = vf.rng.random()
    acc = 0.0
    for name, fn, weight in TEMPLATES:
        acc += weight
        if r <= acc:
            b = NoteBuilder()
            fn(vf, b)
            return b.build(name)
    b = NoteBuilder()
    tpl_hp_note(vf, b)
    return b.build("hp_note")


def validate(note: dict) -> bool:
    text = note["text"]
    prev_end = -1
    for ent in note["entities"]:
        if text[ent["start"]:ent["end"]] != ent["value"]:
            return False
        if ent["start"] < prev_end:
            return False  # overlap
        prev_end = ent["end"]
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-train", type=int, default=3000)
    ap.add_argument("--n-dev", type=int, default=300)
    ap.add_argument("--seed-train", type=int, default=42)
    ap.add_argument("--seed-dev", type=int, default=1337)
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {}
    for split, n, seed in (("train", args.n_train, args.seed_train),
                           ("dev", args.n_dev, args.seed_dev)):
        fk = Faker()
        fk.seed_instance(seed)
        rng = random.Random(seed)
        vf = ValueFactory(fk, rng)
        out = []
        for _ in range(n):
            note = make_note(vf)
            assert validate(note), f"invalid note in {split}: {note}"
            out.append(note)
            stats.clear()
            for e in note["entities"]:
                stats[e["label"]] = stats.get(e["label"], 0) + 1
        path = DATA_DIR / f"{split}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for note in out:
                f.write(json.dumps(note, ensure_ascii=False) + "\n")
        print(f"{split}: wrote {n} notes -> {path}")
        print(f"  entity counts (last-note running totals reset; full counts below)")
        # recompute over full split
        counts: dict[str, int] = {}
        for note in out:
            for e in note["entities"]:
                counts[e["label"]] = counts.get(e["label"], 0) + 1
        for k in sorted(counts):
            print(f"    {k:12s} {counts[k]}")
        words = sum(len(n["text"].split()) for n in out)
        print(f"  avg words/note: {words/len(out):.0f}")


if __name__ == "__main__":
    main()
