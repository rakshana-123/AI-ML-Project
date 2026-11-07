"""Deterministic regex rule layer (recall safety net).

The neural model handles context-dependent identifiers (names, ambiguous
words, locations); these rules nail down format-regular ones where a regex
is near-perfect: SSN, phone/fax, email, URL, IP, dates, ZIP-in-address,
labelled ID numbers (MRN / health plan / account / licence) and the
age > 89 rule (which requires arithmetic a classifier can't do reliably).

Every rule returns spans as dicts {start, end, label}.  The masker takes
the UNION of model spans and rule spans (recall-first: a missed identifier
is a data leak, an extra mask is only an inconvenience).
"""

from __future__ import annotations

import re

MONTHS = {
    "january": "jan", "february": "feb", "march": "mar", "april": "apr",
    "may": "may", "june": "jun", "july": "jul", "august": "aug",
    "september": "sep", "october": "oct", "november": "nov",
    "december": "dec",
}
MONTH_RE = (r"(?:January|February|March|April|May|June|July|August|September|"
            r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|"
            r"Oct|Nov|Dec)\.?")
ORDINAL = r"(?:st|nd|rd|th)"
STATE_ABBR = (r"(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|"
              r"MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|"
              r"SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)")

RX_SSN = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b|\b\d{9}\b(?=[\s,.;)]|$)")
# bare 9 digits only when a label says so (see labelled rules below)

RX_PHONE = re.compile(
    r"(?:\+?1[\s./-])?(?:\(\d{3}\)[\s.]?|\d{3}[\s./-])\d{3}[\s./-]\d{4}"
    r"(?:\s*[x#]\d{1,5})?")

RX_PHONE_CONTEXT = re.compile(  # bare 10-digit numbers near phone words
    r"(?i)\b(?:phone|tel|telephone|fax|call|pager|beeper|mobile|cell|contact|"
    r"office|reachable|reached|callback|direct|day|evening|home|scheduler?|nurse line|"
    r"crisis line|billing office|after[\s-]?hours pager)\b[^.\n]{0,40}?"
    r"\b(\d{10})\b")

RX_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

RX_URL = re.compile(
    r"https?://[^\s<>\"')\]]+"
    r"|\bwww\.[\w-]+(?:\.[\w-]+)+(?:/[^\s<>\"')\]]*)?"
    r"|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|edu|gov|io|co|info)\b"
    r"(?:/[^\s<>\"')\]]*)?")

RX_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
RX_IPV6 = re.compile(r"\b(?:[A-Fa-f0-9]{1,4}:){3,7}[A-Fa-f0-9]{1,4}\b"
                     r"|\b(?:[A-Fa-f0-9]{1,4}:){1,7}:(?::[A-Fa-f0-9]{1,4}){1,7}\b")

# Calendar dates (year-only mentions deliberately NOT matched)
RX_DATE_NUM = re.compile(  # M/D/Y, M/D/YY, M-D-Y, M/D
    r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b")
RX_DATE_ISO = re.compile(r"\b(\d{4})[.\/-](\d{1,2})[.\/-](\d{1,2})\b")
RX_DATE_MON_Y_NUM = re.compile(r"\b(\d{1,2})/(\d{4})\b")   # MM/YYYY
RX_DATE_MON_D = re.compile(  # March 5, 2024 / Mar. 5 2024 / February 3rd
    rf"\b({MONTH_RE})\.?\s+(\d{{1,2}}){ORDINAL}?(?:,)?(?:\s+(\d{{4}}))?\b")
RX_DATE_MON_Y = re.compile(rf"\b({MONTH_RE}),?\s+(\d{{4}})\b")
RX_DATE_D_MON = re.compile(  # 5 March 2024 / 19-Apr-2016 / 29.Oct.2025
    rf"\b(\d{{1,2}}){ORDINAL}?[\s.-]({MONTH_RE})\.?(?:[\s.,-]+\s*(\d{{4}}))?\b")
RX_DATE_MON_CTX = re.compile(  # bare month anchored by a time preposition
    rf"(?i)\b(?:in|on|of|since|during|until|before|after|arrived|admitted|"
    rf"discharged|moved to|move to)\s+({MONTH_RE})\b")

RX_ZIP = re.compile(  # ZIP+4 always; 5-digit ZIP only after state abbr
    rf"\b\d{{5}}-\d{{4}}\b|(?:(?:,|^)\s*{STATE_ABBR}\s+)(\d{{5}})\b"
    rf"|\bZIP\s*#?\s*(\d{{5}}(?:-\d{{4}})?)\b")

RX_AGE = re.compile(  # number-as-age; caller checks > 89
    r"(?i)(?:\bage[ds]?(?:\s+of)?\s*[:#=]?\s*|\baged\s+|\bis\s+|\bturn(?:ed|ing)?\s+"
    r"|\bpatient(?:'s)?\s+age\s*[:#=]?\s*|\bat\s+age\s+)?"
    r"(\d{1,3})"
    r"(?=\s*-?\s*(?:year|yr|y)\.?[\s-]*old\b|\s*y\.?\s?o\.?\b|\s*yo\b"
    r"|\s*years?\s+of\s+age\b|[\s,.])")

RX_AGE_SUFFIX = re.compile(  # evidence that the number is an age (after it)
    r"(?i)^\s*-?\s*(?:year|yr|y)\.?[\s-]*old\b|^\s*y\.?\s?o\.?\b|^\s*yo\b"
    r"|^\s*years?\s+of\s+age\b")
AGE_CTX_REQUIRED = re.compile(  # when no suffix, need an age cue before it
    r"(?i)\bage[ds]?(?:\s+of)?|aged|\bis\b|turn(?:ed|ing)?|at\s+age")

# Labelled identifier numbers --------------------------------------------
# Order matters: at equal spans the earlier entry wins, so specific multi-
# word labels (ACCOUNT's "contact id") beat the generic "id" fallback in MRN.
_ID_VALUE = r"([A-Za-z0-9][A-Za-z0-9.\-]*(?:[ -][A-Za-z0-9][A-Za-z0-9.\-]*){0,2})"
LABELLED = [
    ("ACCOUNT", re.compile(
        r"(?i)\b(?:account|acct|accession|patient\s+account|group"
        r"|incident\s*id|report\s*id|document\s*id|case\s*id|dictation\s*id"
        r"|contact\s*id|specimen\s*id|auth(?:orization)?\s*(?:number|no|#)"
        r"|reference|ref\b|ticket|tracking)\s*(?:#|no\.?|number)?\s*[:=]?\s*"
        + _ID_VALUE)),
    ("LICENSE", re.compile(
        r"(?i)\b(?:licen[sc]e|lic\.?|lic#|dea|npi|driver'?s?\s*licen[sc]e"
        r"|serial)\s*(?:#|no\.?|number)?\s*[:=]?\s*" + _ID_VALUE)),
    ("HEALTHPLAN", re.compile(
        r"(?i)\b(?:health\s*plan|member\s*id|member(?:ship)?|policy(?:\s*holder)?"
        r"|policy\s*(?:no|number|#)|insurance\s*id|plan\s*id|coverage\s*id"
        r"|beneficiary)\s*(?:#|no\.?|number)?\s*[:=]?\s*" + _ID_VALUE)),
    ("SSN", re.compile(
        r"(?i)\b(?:ssn|social\s*security(?:\s*number)?)\s*(?:#|no\.?|number)?"
        r"\s*[:=]?\s*" + _ID_VALUE)),
    ("MRN", re.compile(
        r"(?i)\b(?:MRN|MR\b|medical\s+record(?:\s+number)?|chart(?:\s*#)?"
        r"|clinic\s*#|id)\s*(?:#|no\.?|number)?\s*[:=]?\s*" + _ID_VALUE)),
]


def _span(m, group=0, label=None):
    s, e = m.start(group), m.end(group)
    return {"start": s, "end": e, "label": label}


def _valid_ipv4(m) -> bool:
    parts = m.group(0).split("/")[0].split(".")
    return all(0 <= int(p) <= 255 for p in parts)


def _plausible_md(mon: int, day: int, year: str | None) -> bool:
    if not (1 <= mon <= 12 and 1 <= day <= 31):
        return False
    if year is None:
        return True
    return len(year) in (2, 4)


def find_dates(text: str) -> list[dict]:
    out = []
    for m in RX_DATE_ISO.finditer(text):
        y, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1900 <= y <= 2099 and _plausible_md(mon, day, m.group(3)):
            out.append(_span(m, label="DATE"))
    for m in RX_DATE_MON_Y_NUM.finditer(text):   # MM/YYYY
        mon, y = int(m.group(1)), int(m.group(2))
        if 1 <= mon <= 12 and 1900 <= y <= 2099:
            out.append(_span(m, label="DATE"))
    for m in RX_DATE_NUM.finditer(text):
        a, b, yr = m.group(1), m.group(2), m.group(3)
        # guard against doses ("1/2 tablet") and vitals ("120/74")
        tail = text[m.end():m.end() + 12].lower()
        if re.match(r"\s*(?:tablet|tab\b|dose|mg|ml|unit|percent)", tail):
            continue
        mon_a = int(a) <= 12
        mon_b = int(b) <= 12
        if yr is not None:
            if not (mon_a or mon_b):     # neither <=12 -> not a date
                continue
            if mon_a and int(b) > 31:
                continue
            if not mon_a and mon_b and int(a) > 31:
                continue
        else:
            if not (mon_a and 1 <= int(b) <= 31):
                continue
            # month/day without year needs some date flavour around it
            ctx = text[max(0, m.start() - 30):m.start()].lower()
            if not re.search(r"(?:date|on|of|appt|appointment|visit|admit|"
                             r"discharge|start|stop|follow|covered|seen|from|"
                             r"to|due|dob|drawn|collected|issued|booked)", ctx):
                continue
        out.append(_span(m, label="DATE"))
    for m in RX_DATE_MON_D.finditer(text):
        out.append(_span(m, label="DATE"))
    for m in RX_DATE_MON_Y.finditer(text):
        out.append(_span(m, label="DATE"))
    for m in RX_DATE_D_MON.finditer(text):
        out.append(_span(m, label="DATE"))
    for m in RX_DATE_MON_CTX.finditer(text):
        # mask only the month itself (the preposition stays)
        out.append({"start": m.start(1), "end": m.end(1), "label": "DATE"})
    return out


def find_ages(text: str) -> list[dict]:
    out = []
    for m in RX_AGE.finditer(text):
        n = int(m.group(1))
        if n <= 89:
            continue
        after = text[m.end(1):m.end(1) + 20]
        has_suffix = RX_AGE_SUFFIX.match(after)
        if not has_suffix:
            # bare big number: require an explicit age cue before it
            prefix_len = m.start(1) - m.start()
            cue = m.group(0)[:prefix_len] if prefix_len else ""
            before = text[max(0, m.start() - 15):m.start()]
            if not AGE_CTX_REQUIRED.search(cue + " " + before):
                continue
        out.append({"start": m.start(1), "end": m.end(1), "label": "AGE"})
    return out


def find_zips(text: str) -> list[dict]:
    out = []
    for m in RX_ZIP.finditer(text):
        # choose the captured group when present
        g = next((i for i in (1, 2) if m.group(i)), 0)
        out.append({"start": m.start(g), "end": m.end(g), "label": "LOCATION"})
    return out


def find_labelled_ids(text: str) -> list[dict]:
    hits = []
    for label, rx in LABELLED:
        for m in rx.finditer(text):
            val = m.group(1)
            if not any(ch.isdigit() for ch in val):
                continue
            hits.append({"start": m.start(1), "end": m.end(1), "label": label})
    # resolve cross-type overlaps: prefer longer spans, then LABELLED order
    hits.sort(key=lambda h: (h["start"], -(h["end"] - h["start"])))
    out, last_end = [], -1
    for h in hits:
        if h["start"] < last_end:
            continue
        out.append(h)
        last_end = h["end"]
    return out


RX_PHONE_WORDS = re.compile(
    r"(?i)\b(?:phone|tel|telephone|fax|call|pager|beeper|mobile|cell|contact"
    r"|office|reachable|reached|callback|direct|line|home|day|evening)"
    r"(?:ed|s)?\b")

RX_ID_WORDS_BEFORE = re.compile(
    r"(?i)\b(?:mrn|mr|id|account|acct|accession|policy|member|group|license"
    r"|lic|dea|npi|ssn|chart|clinic|reference|ref|ticket|auth)\s*[:#.]?\s*$")


def find_phones(text: str) -> list[dict]:
    out = [_span(m, label="PHONE") for m in RX_PHONE.finditer(text)]
    for m in re.finditer(r"\b\d{10}\b", text):
        window = text[max(0, m.start() - 60):m.start()]
        between = window[window.rfind("\n") + 1:]  # current line so far
        if not between.strip():                     # number starts its line:
            prev = window[:window.rfind("\n")] if "\n" in window else window
            between = prev[prev.rfind("\n") + 1:] + " " + between
        if RX_PHONE_WORDS.search(between) and not RX_ID_WORDS_BEFORE.search(between):
            out.append({"start": m.start(), "end": m.end(), "label": "PHONE"})
    return out


def find_ips(text: str) -> list[dict]:
    out = [{"start": m.start(), "end": m.end(), "label": "IP"}
           for m in RX_IPV4.finditer(text) if _valid_ipv4(m)]
    out += [{"start": m.start(), "end": m.end(), "label": "IP"}
             for m in RX_IPV6.finditer(text)]
    return out


# Explicit name clarifications ("first name Austin", "named Denver") and the
# Washington-DC special case (a city, unlike the state of Washington).
RX_NAME_CLARIFY = re.compile(
    r"(?i)\b(?:first|middle|last|given|family|maiden)\s+name\b\s*[:\-]?\s*"
    r"([A-Z][a-z'\u2019-]{1,20})\b"
    r"|\bsurname\b\s*[:\-]?\s*([A-Z][a-z'\u2019-]{1,20})\b"
    r"|\bnamed\s+([A-Z][a-z'\u2019-]{1,20})\b")
RX_WASHINGTON_DC = re.compile(r"\bWashington\s*,\s*D\.?C\.?\b")

from .labels import EPONYM_SURNAMES  # noqa: E402  (used below)


def find_name_clarifications(text: str) -> list[dict]:
    out = []
    for m in RX_NAME_CLARIFY.finditer(text):
        gi = next((i for i, g in enumerate(m.groups(), 1) if g), None)
        if gi is None:
            continue
        if m.group(gi).lower() in EPONYM_SURNAMES:
            continue            # "named Parkinson" -> the disease
        out.append({"start": m.start(gi), "end": m.end(gi), "label": "NAME"})
    for m in RX_WASHINGTON_DC.finditer(text):
        out.append({"start": m.start(), "end": m.start() + len("Washington"),
                    "label": "LOCATION"})
    return out


def rule_spans(text: str) -> list[dict]:
    """All rule-layer identifier spans for one note (deduped, sorted)."""
    spans = []
    spans += [_span(m, label="SSN") for m in RX_SSN.finditer(text)
              if "-" in m.group(0) or " " in m.group(0)]
    spans += find_phones(text)
    spans += [_span(m, label="EMAIL") for m in RX_EMAIL.finditer(text)]
    spans += [_span(m, label="URL") for m in RX_URL.finditer(text)]
    spans += find_ips(text)
    spans += find_dates(text)
    spans += find_zips(text)
    spans += find_ages(text)
    spans += find_labelled_ids(text)
    spans += find_name_clarifications(text)
    # drop spans fully contained in an earlier (wider) span of any type,
    # e.g. the sub-match "09/2025" inside "04/09/2025"
    spans.sort(key=lambda s: (s["start"], -s["end"]))
    out: list[dict] = []
    for s in spans:
        if out and s["end"] <= out[-1]["end"]:
            continue
        out.append(s)
    return out
