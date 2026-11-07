"""Entity type definitions for the PHI de-identification task.

The 13 entity types below cover the identifier families required by the
assessment brief (HIPAA Safe Harbor categories A-R relevant to free-text
clinical notes):

    NAME        - Safe Harbor (A): patients, relatives, clinicians
    LOCATION    - Safe Harbor (B): street, city, ZIP, facility (sub-state)
    DATE        - Safe Harbor (C): all calendar dates except year-only mentions
    AGE         - Safe Harbor (C): ages over 89 (younger ages are kept)
    PHONE       - Safe Harbor (D)+(E): telephone and fax numbers
    EMAIL       - Safe Harbor (F)
    SSN         - Safe Harbor (G)
    MRN         - Safe Harbor (H): medical record numbers
    HEALTHPLAN  - Safe Harbor (I): health plan beneficiary / member / policy IDs
    ACCOUNT     - Safe Harbor (J): account / billing numbers
    LICENSE     - Safe Harbor (K): certificate and licence numbers (incl. DEA)
    URL         - Safe Harbor (N)
    IP          - Safe Harbor (O)

Intentionally NOT covered (documented in README.md):
    vehicle IDs (L), device IDs (M), biometrics (P), photos (Q),
    free-text unique characteristics (R).
"""

# Canonical entity type order (used everywhere: labels, metrics, placeholders).
ENTITY_TYPES = [
    "NAME",
    "LOCATION",
    "DATE",
    "AGE",
    "PHONE",
    "EMAIL",
    "SSN",
    "MRN",
    "HEALTHPLAN",
    "ACCOUNT",
    "LICENSE",
    "URL",
    "IP",
]

# BIO tag set for token classification: O + B-/I- for each type.
LABEL_LIST = ["O"] + [f"{prefix}-{t}" for t in ENTITY_TYPES for prefix in ("B", "I")]
LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

# Types that the deterministic rule layer handles almost perfectly.  The rule
# layer runs in addition to the neural model (union of spans) because the brief
# prioritises recall: a missed identifier is a data leak, an extra mask is only
# an inconvenience.
RULE_TYPES = {"SSN", "PHONE", "EMAIL", "URL", "IP", "DATE", "MRN", "LICENSE"}

# Surnames that are also eponymous disease names.  A standalone occurrence of
# one of these is far more likely to be the disease ("Parkinson's disease")
# than the person, so the surname-recall pass only masks them when a title
# (Dr./Mr./Mrs....) is attached.
EPONYM_SURNAMES = {
    "parkinson", "huntington", "bell", "crohn", "graves", "hodgkin",
    "alzheimer", "lynch", "addison", "cushing", "meniere", "raynaud",
    "turner", "marfan", "barrett", "down", "kaposi", "hashimoto",
    "sjogren", "wernicke", "broca",
}

# Placeholder display names (bracketed in masked text, e.g. [NAME_1]).
PLACEHOLDER_PREFIX = {t: t for t in ENTITY_TYPES}
