"""PHI De-identification Gateway.

A small fine-tuned transformer (DistilBERT, ~67M parameters) detects
identifiers in clinical notes; a deterministic rule layer adds high-precision
regex coverage.  ``deidentify`` replaces each identifier with a stable
placeholder such as ``[NAME_1]`` and returns the private mapping;
``rehydrate`` restores the original values into the LLM's answer.
"""

__version__ = "1.0.0"
