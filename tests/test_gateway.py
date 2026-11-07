"""Focused tests for the gateway's core invariants.

Run:  python -m pytest tests/ -q
(uses the rules-only gateway by default so tests run in seconds; set
PHI_GATEWAY_TEST_MODEL=1 to include the trained model in round trips)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from phi_gateway.masker import PHIGateway
from phi_gateway.rules import find_ages, rule_spans


@pytest.fixture(scope="module")
def gw():
    return PHIGateway(use_model=False)


def spans_of(text, label):
    return [s for s in rule_spans(text) if s["label"] == label]


# ---- the required interface ------------------------------------------

def test_deidentify_signature(gw):
    masked, mapping = gw.deidentify("Call John Smith at 555-018-2244.")
    assert isinstance(masked, str) and isinstance(mapping, dict)
    assert "555-018-2244" not in masked
    assert "[PHONE_1]" in masked
    assert mapping["[PHONE_1]"] == "555-018-2244"


def test_rehydrate_round_trip_identity(gw):
    text = "Visit on 03/04/2024; MRN: 88-4471; fax (555) 123-9876."
    masked, mapping = gw.deidentify(text)
    assert gw.rehydrate(masked, mapping) == text


def test_same_value_same_placeholder(gw):
    text = "Appt 01/02/2024. Again 01/02/2024, not 01/03/2024."
    masked, mapping = gw.deidentify(text)
    assert masked.count("[DATE_1]") == 2
    assert "[DATE_2]" in masked and len(mapping) == 2


def test_unknown_placeholder_left_alone(gw):
    _, mapping = gw.deidentify("Meeting 04/05/2024.")
    out = gw.rehydrate("He met [NAME_99] and [DATE_42].", mapping)
    assert "[NAME_99]" in out and "[DATE_42]" in out
    assert gw.last_report["unknown_placeholders"] == ["[NAME_99]", "[DATE_42]"]


def test_placeholder_no_prefix_collision(gw):
    # 10+ entities of one type: [DATE_10] must not be eaten by [DATE_1]
    dates = ". ".join(f"d{i:02d}/01/2024" for i in range(1, 12))
    dates = " ".join(
        f"visit {(i):02d}/01/2024" for i in range(1, 12))
    masked, mapping = gw.deidentify(dates)
    assert "[DATE_10]" in masked and "[DATE_11]" in masked
    assert gw.rehydrate(masked, mapping) == dates


# ---- the brief's edge cases -----------------------------------------

def test_age_over_89_only():
    text = ("a 45-year-old, an 88 yo M, aged 89, a 90-year-old, a 94 y.o., "
            "102 years of age, and age 96.")
    ages = [int(text[s["start"]:s["end"]]) for s in find_ages(text)]
    assert ages == [90, 94, 102, 96]


def test_relative_time_not_masked(gw):
    text = "3 days post-op, two weeks ago, POD #3, x 48 hours."
    masked, _ = gw.deidentify(text)
    assert masked == text          # nothing calendar-like -> untouched


def test_year_only_not_masked(gw):
    masked, _ = gw.deidentify("Diagnosed in 2019 and seen annually since.")
    assert masked.startswith("Diagnosed in 2019")


def test_month_year_masked(gw):
    masked, _ = gw.deidentify("Admitted 04/2025 for observation.")
    assert "[DATE_1]" in masked


def test_vitals_not_dates(gw):
    text = "BP 148/86, HR 92, SpO2 96%, 1/2 tablet furosemide."
    masked, _ = gw.deidentify(text)
    assert masked == text


def test_eponym_doctor_masked_by_model_path():
    # rules never touch names; this guards the rule layer does not
    # accidentally mask diseases while hunting identifiers
    text = "Dr. Parkinson diagnosed Parkinson's disease; Bell's palsy noted."
    masked = text
    for s in spans_of(text, "DATE"):
        masked = masked.replace(text[s["start"]:s["end"]], "[DATE]")
    assert "Parkinson's disease" in masked


def test_ssn_span_text():
    for ssn in ("123-45-6789", "123 45 6789"):
        text = f"SSN on file: {ssn}."
        s = spans_of(text, "SSN")
        assert len(s) == 1, ssn
        assert text[s[0]["start"]:s[0]["end"]] == ssn
