# Utility check - LLM answers on original vs masked notes

LLM: **mock (offline deterministic)**  |  notes: test_01, test_02, test_05, test_12, test_23  |  3 questions each

Average ROUGE-L F1 between answers: **0.95** (1.0 = identical content)

| Note | Question | ROUGE-L |
|---|---|---|
| test_01 | Summarise this clinical note in ... | 0.91 |
| test_01 | What is the working diagnosis an... | 0.91 |
| test_01 | What follow-up is arranged and w... | 0.91 |
| test_02 | Summarise this clinical note in ... | 0.95 |
| test_02 | What is the working diagnosis an... | 0.95 |
| test_02 | What follow-up is arranged and w... | 0.95 |
| test_05 | Summarise this clinical note in ... | 0.96 |
| test_05 | What is the working diagnosis an... | 0.96 |
| test_05 | What follow-up is arranged and w... | 0.96 |
| test_12 | Summarise this clinical note in ... | 0.99 |
| test_12 | What is the working diagnosis an... | 0.99 |
| test_12 | What follow-up is arranged and w... | 0.99 |
| test_23 | Summarise this clinical note in ... | 0.95 |
| test_23 | What is the working diagnosis an... | 0.95 |
| test_23 | What follow-up is arranged and w... | 0.95 |

## test_01 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

Summary: Notes similar symptoms last year. Cardiology follow-up 04/21/2025 with Dr.

**Masked:**

Summary: Notes similar symptoms last year. Cardiology follow-up [DATE_3] with Dr.

## test_01 - What is the working diagnosis and the key supporting findings?

**Original:**

Summary: Notes similar symptoms last year. Cardiology follow-up 04/21/2025 with Dr.

**Masked:**

Summary: Notes similar symptoms last year. Cardiology follow-up [DATE_3] with Dr.

## test_01 - What follow-up is arranged and with whom?

**Original:**

Summary: Notes similar symptoms last year. Cardiology follow-up 04/21/2025 with Dr.

**Masked:**

Summary: Notes similar symptoms last year. Cardiology follow-up [DATE_3] with Dr.

## test_02 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: 2025-04-11

Patient: Robert Fenwick   MRN: 0038471

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

**Masked:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: [DATE_1]

Patient: Robert Fenwick   MRN: [MRN_1]

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

## test_02 - What is the working diagnosis and the key supporting findings?

**Original:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: 2025-04-11

Patient: Robert Fenwick   MRN: 0038471

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

**Masked:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: [DATE_1]

Patient: Robert Fenwick   MRN: [MRN_1]

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

## test_02 - What follow-up is arranged and with whom?

**Original:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: 2025-04-11

Patient: Robert Fenwick   MRN: 0038471

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

**Masked:**

Summary: PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: [DATE_1]

Patient: Robert Fenwick   MRN: [MRN_1]

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.

## test_05 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at portal.cascadevalley-example.com.

**Masked:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at [URL_1].

## test_05 - What is the working diagnosis and the key supporting findings?

**Original:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at portal.cascadevalley-example.com.

**Masked:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at [URL_1].

## test_05 - What follow-up is arranged and with whom?

**Original:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at portal.cascadevalley-example.com.

**Masked:**

Summary: TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast. IMPRESSION:
1. Recommend orthopaedic consultation; report available in the patient
portal at [URL_1].

## test_12 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks (02/06/26).

**Masked:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks ([DATE_2]).

## test_12 - What is the working diagnosis and the key supporting findings?

**Original:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks (02/06/26).

**Masked:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks ([DATE_2]).

## test_12 - What follow-up is arranged and with whom?

**Original:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks (02/06/26).

**Masked:**

Summary: Huntington wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother Ray Parkinson carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged. Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2). Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks ([DATE_2]).

## test_23 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

Summary: PRIMARY CARE VISIT - 10/10/2025

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

**Masked:**

Summary: PRIMARY CARE VISIT - [DATE_1]

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

## test_23 - What is the working diagnosis and the key supporting findings?

**Original:**

Summary: PRIMARY CARE VISIT - 10/10/2025

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

**Masked:**

Summary: PRIMARY CARE VISIT - [DATE_1]

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

## test_23 - What follow-up is arranged and with whom?

**Original:**

Summary: PRIMARY CARE VISIT - 10/10/2025

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

**Masked:**

Summary: PRIMARY CARE VISIT - [DATE_1]

Simonbar Sinistaj (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.
