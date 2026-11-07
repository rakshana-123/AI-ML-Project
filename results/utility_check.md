# Utility check - LLM answers on original vs masked notes

LLM: **local:Qwen2.5-0.5B-Instruct (CPU)**  |  notes: test_01, test_02, test_05, test_12, test_23  |  3 questions each

Average ROUGE-L F1 between answers: **0.33** (raw masked), **0.34** after rehydration restores identifiers (1.0 = identical content).

| Note | Question | ROUGE-L masked | ROUGE-L rehydrated |
|---|---|---|---|
| test_01 | Summarise this clinical note in ... | 0.47 | 0.47 |
| test_01 | What is the working diagnosis an... | 0.44 | 0.44 |
| test_01 | What follow-up is arranged and w... | 0.18 | 0.19 |
| test_02 | Summarise this clinical note in ... | 0.23 | 0.26 |
| test_02 | What is the working diagnosis an... | 0.36 | 0.36 |
| test_02 | What follow-up is arranged and w... | 0.27 | 0.27 |
| test_05 | Summarise this clinical note in ... | 0.62 | 0.62 |
| test_05 | What is the working diagnosis an... | 0.28 | 0.28 |
| test_05 | What follow-up is arranged and w... | 0.17 | 0.21 |
| test_12 | Summarise this clinical note in ... | 0.40 | 0.41 |
| test_12 | What is the working diagnosis an... | 0.45 | 0.45 |
| test_12 | What follow-up is arranged and w... | 0.35 | 0.35 |
| test_23 | Summarise this clinical note in ... | 0.19 | 0.20 |
| test_23 | What is the working diagnosis an... | 0.28 | 0.28 |
| test_23 | What follow-up is arranged and w... | 0.33 | 0.36 |

## test_01 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

The patient presents with bilateral leg swelling and worsening dyspnea after running out of furosemide. The chief complaint is that the patient's legs are swollen. The patient denies chest pain and has a history of CHF and AFib. The patient was previously diagnosed with hypertension, coronary artery disease, and diabetes mellitus type 2. The patient underwent an acute-on-chronic diastolic heart failure episode and restarted furosemide. The patient is currently being evaluated by Dr. Wallace at Wexford Heart Institute.

**Masked:**

The patient presented with bilateral leg swelling and worsening dyspnea after running out of furosemide two weeks prior. The chief complaint is the swelling of both legs, which has persisted for three days. The patient denies chest pain and has no history of previous episodes. The patient's medical history includes a history of CHF (ejection fraction <35%) and AFib, as well as hypertension (BP 148/86 mmHg). The patient also has diabetes mellitus stage 3, kidney disease stage 3, and a retired school teacher who lives with her daughter in Ohio. The patient was admitted with acute-on-chronic heart failure, where she was prescribed furosemide 40 mg daily. The patient underwent an electrocardiogram (

## test_01 - What is the working diagnosis and the key supporting findings?

**Original:**

The working diagnosis for this patient is acute-on-chronic heart failure (ACHF). The key supporting findings include:

1. **Acute On Chronic Diastolic Heart Failure**: This indicates that the patient's heart failure has progressed from an acute phase to a chronic one. The use of furosemide as prescribed suggests that the heart failure was initially acute but now requires long-term management.

2. **Bilateral Leg Swelling**: The presence of bilateral leg swelling is a common symptom of heart failure, especially when it progresses to more severe forms like ACHF. This could be due to fluid retention or increased cardiac load.

3. **Worsening Dyspnea on Exertion**: The patient's dyspnea on exertion is a hallmark sign of heart failure. It indicates

**Masked:**

The working diagnosis for this patient is acute-on-chronic heart failure (ACHF). The key supporting findings include:

1. **Acute On Chronic Heart Failure (ACHF)**: This indicates that the patient's heart failure has progressed from an acute exacerbation to a chronic condition.

2. **Chronic Diastolic Heart Failure**: The patient's heart function is classified as chronic, which means it has been ongoing for more than 6 months but not yet severe enough to be considered chronic heart failure.

3. **Acute On Chronic Heart Failure (ACHF)**: The patient's heart failure has worsened over time, indicating that their condition is now more severe than it was before.

4. **Heart Rate (HR) 92 irregular**: The patient's heart rate is

## test_01 - What follow-up is arranged and with whom?

**Original:**

The follow-up appointment arranged for Gloria M. Castellanos was with Dr. Erin Wallace, the internal medicine physician at Wexford Hospital. The appointment was scheduled for April 9, 2025, and included an examination of her condition, including her symptoms of bilateral leg swelling and worsening dyspnea on exertion. The patient also mentioned that she had run out of furosemide two weeks ago and denied chest pain. Additionally, she noted similar symptoms previously, which led to the diagnosis of acute-on-chronic heart failure. The appointment was followed up by Dr. Wallace at Wexford Heart Institute on April 21, 2025.

**Masked:**

The follow-up is arranged for the patient Wexford Memorial Hospital Internal Medicine Department admission history and physical examination. The primary follow-up involves the appointment with Dr. [NAME_2] who was the PCP (primary care physician) for the patient's previous visit. This appointment likely included reviewing the patient's medical history, conducting a physical examination, and discussing any relevant medications or treatments that were prescribed during their previous visit. The appointment also involved noting any changes in the patient's condition since their last visit, such as new symptoms or improvements in their current health status.

## test_02 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

**Clinical Note Summary:**

**Patient:** Robert Fenwick  
**MRN:** 0038471  
**Hospital Day 3:**  
**Date:** April 11, 2025  
**Progress:** The patient is reporting improved health with no chest pain since his previous cardiac procedure. He has been able to ambulate in the hall three times today. His temperature remains stable at 36.8°C, heart rate is 68 beats per minute, blood pressure is 124/74 mmHg, and respiratory rate is 14 breaths per minute. Laboratory results show a troponin level of 0.02, indicating no signs of myocardial infarction. The patient's oxygen saturation is

**Masked:**

**Clinical Note Summary**

**Patient:** [NAME_1]
**MRN:** [MRN_1]
**Status:** Feeling much better after hospitalization with complications from previous myocardial infarction (MI) post-PCI. 

**Progress Notes:**
- **Triage Status:** 
  - Progress noted as 4 West (TElemetry).
  - Hospital day 3.
  - Date: [DATE_1].

- **Current Condition:**
  - Patient is reporting good sleep through the night.
  - No chest pain since PCI.
  - Ambulated to Hall 3 three times since today.
  - Nurse reported eating most of breakfast.

- **Laboratory Results:**
  - Troponin levels remain stable at 0.02 (down from

## test_02 - What is the working diagnosis and the key supporting findings?

**Original:**

The working diagnosis for this patient is likely to be an acute coronary syndrome (ACS) with possible secondary thrombosis or embolism due to the presence of ST-segment elevation myocardial infarction (STEMI). The patient's symptoms, including chest pain, sleep disturbances, and lack of appetite, suggest that there may be underlying heart disease contributing to these symptoms.

Key Supporting Findings:

1. **Acute Coronary Syndrome (ACS)**: The patient has been diagnosed with an acute coronary syndrome, which indicates that there is a risk of a heart attack occurring within the next few days.

2. **Secondary Thrombosis**: Given the presence of STEMI, it is reasonable to consider that the patient may have developed a secondary thrombus or embolic event. This could be

**Masked:**

The working diagnosis for this patient is likely to be an acute coronary syndrome (ACS) with possible secondary thromboembolism due to the presence of a troponin elevation and other clinical signs suggestive of ACS. The key supporting findings include:

1. **Troponin Levels**: Elevated troponin levels (e.g., 0.02 ng/mL) suggest myocardial injury or necrosis, which is consistent with an acute coronary syndrome.

2. **Chest Pain**: The patient reported chest pain, which could indicate angina or another type of chest discomfort that may be related to the underlying condition.

3. **Ambulation**: The patient has been ambulating frequently since the morning, indicating some degree of exertion and possibly exacerbation of the condition.

4. **Tach

## test_02 - What follow-up is arranged and with whom?

**Original:**

The follow-up is arranged by Anjali Rao, DO, who is the attending physician and nurse practitioner overseeing the patient's care. The follow-up includes:

1. **Patient Information**: The patient's medical history, current symptoms, and any relevant medications or treatments.
2. **Current Status**: The patient's current condition, including their sleep patterns, appetite, and physical activity levels.
3. **Lab Results**: Recent laboratory tests performed to monitor the patient's health status.
4. **Follow-Up Plan**: A detailed plan for the patient's care, including ongoing monitoring and treatment as needed.
5. **Communication**: Regular updates between the patient and the healthcare team, ensuring that all aspects of the patient's care are being managed effectively.

This follow-up process ensures that the patient receives comprehensive care

**Masked:**

The follow-up is scheduled to be conducted by Dr. A/P, who is the nurse providing care to patient [NAME_1]. The follow-up will involve monitoring the patient's condition, reviewing any recent laboratory results, and discussing potential next steps based on the patient's current status. Additionally, the nursing team will continue to monitor the patient's progress and provide guidance as needed.

## test_05 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

### Clinical Note Summary:

A 46-year-old male presented with acute lateral knee pain following a pivoting injury four days ago. The MRI examination revealed an oblique tear in the anterior horn of the lateral meniscus, which was not displaced and had moderate joint effusion. A recommendation for an orthopaedic consultation was made, and the findings were reported on the patient's portal website.

**Masked:**

### Summary of Clinical Note

**Clinical History:** A 46-year-old male presented with acute lateral knee pain following a pivoting injury four days ago. The examination revealed an oblique tear in the anterior horn of the lateral meniscus extending to the free edge, with no displaced fragments and moderate joint effusion. The findings were reported as "Moderate tear" and "Moderate effusion." The patient was referred for further evaluation and has been advised to consult an orthopedic specialist via the portal site provided.

## test_05 - What is the working diagnosis and the key supporting findings?

**Original:**

The working diagnosis for Marcus Dewilde's MRI left knee examination was:

1. **Oblique Tear** - The imaging showed increased signal within the anterior horn of the lateral meniscus extending to the free edge, which is consistent with an oblique tear. No displaced fragments were detected, and ligament integrity remained intact.

2. **Moderate Effusion** - The presence of moderate joint effusion suggests that there may be some fluid accumulation around the knee joint, but it does not indicate any specific type of injury or pathology.

3. **Recommendation for Orthopaedic Consultation** - Given the findings, the patient should be referred for further evaluation as part of his ongoing medical care. This recommendation is based on the clinical presentation described.

The key supporting findings from this MRI report include:

**Masked:**

The working diagnosis for this case is:

**Oblique Tear, Left Meniscus Anterior Horn**

Key Supporting Findings:

1. **Increased Signal Within the Anterior Horn of the Lateral Meniscus**: This indicates that there is an abnormal increase in the signal intensity within the anterior horn of the lateral meniscus. The presence of this signal suggests that there may be an injury or tear in the meniscus.

2. **No Displaced Fragment**: The absence of any displaced fragments further supports the diagnosis as it indicates no significant damage to the meniscus during the injury.

3. **Ligaments Intact**: The integrity of the ligaments surrounding the meniscus is also noted, which is important for understanding the stability of the meniscus.

4. **

## test_05 - What follow-up is arranged and with whom?

**Original:**

The follow-up for this MRI report is scheduled with Dr. Helen Osei, who referred Marcus Dewilde to the Cascade Valley Imaging Center (CVC). The follow-up will be conducted via email at the provided portal URL, which is `portal.cascadevalley-example.com`. This indicates that the next step involves reviewing the imaging findings and discussing any relevant clinical information with Dr. Osei.

**Masked:**

The follow-up is arranged as follows:

1. **Follow-Up Date**: The follow-up was scheduled for [DATE_3].
2. **Follow-Up Physician**: The follow-up was conducted by [NAME_1][NAME_2], who is a doctor.
3. **Follow-Up Content**: The content of the follow-up includes:
   - A multi-planar multitechnique (MPM) MRI of the left knee without contrast.
   - An examination that did not include intravenous contrast.
   - The findings indicate an oblique tear of the lateral meniscus, with no displaced fragments or fractures noted.
   - The patient reports moderate effusion.
   - The patient's information is available on the portal site at [URL_1].

## test_12 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

**Clinical Note Summary**

Olive Parkinson, a 71-year-old woman, presented with a resting tremor of the right hand over the past 8 months. Her father, Gerald, was diagnosed with Parkinson's disease, while her brother, Ray, also carried the diagnosis of Huntington's disease. The patient's family history of Huntington's disease suggests a potential genetic component. A neuromuscular examination revealed cogwheel rigidity and asymmetric tremor, along with postural instability during the pull test. Based on these findings, the patient's condition is most consistent with idiopathic Parkinson's disease (Hoehn & Yahr stage 2), and she should be referred for physical therapy. Dr. Malcolm Graves will address any possible genetic overlap between the patient's family history and her thyroid history

**Masked:**

**Clinical Note Summary**

- **Patient:** [NAME_1], 71F, seen with her husband [NAME_2].
- **Date:** [DATE_1]
- **Date:** [DATE_2]

**History:**
- Patient has developed a resting tremor of the right hand over the past 8 months.
- Family history includes Parkinson's disease (mother), Huntington's disease (paternal side), and a brother with Huntington's disease (brother).
- The patient's mother reportedly had Parkinson's disease.

**Exam:**
- Cogwheel rigidity right > left, asymmetric tremor, and postural instability on pull test.

**Assessment:**
- Clinically, the patient's symptoms most closely align with idiopathic Parkinson's disease Stage 2

## test_12 - What is the working diagnosis and the key supporting findings?

**Original:**

The working diagnosis for Olive Parkinson is idiopathic Parkinson's disease (Hoehn & Yahr stage 2), which is consistent with the clinical presentation described. The key supporting findings include:

1. **Resting Tremor**: The patient reports a resting tremor in the right hand, which is characteristic of Parkinson's disease.
2. **Cogwheel Rigidity**: This is a hallmark feature of Parkinson's disease, characterized by stiffening of the muscles around the joints, particularly in the hands and legs.
3. **Asymmetric Tremor**: The tremor is asymmetrical, meaning it affects one side more than the other.
4. **Postural Instability**: The patient experiences postural instability when trying to sit or stand up, which is common in Parkinson's disease.
5

**Masked:**

The working diagnosis for this case is **Idiopathic Parkinson's Disease Stage 2**. The key supporting findings include:

1. **Resting Tremor**: The patient reports a resting tremor in the right hand that has persisted over the past 8 months.
2. **Cogwheel Rigidity**: There is a significant increase in the frequency and severity of cogwheel rigidity (right > left) in the right hand.
3. **Asymmetric Tremor**: The tremor pattern is asymmetrical, which is characteristic of Parkinsonian tremors.
4. **Postural Instability**: Posture instability during activities such as pulling or standing up can be observed.
5. **Clinical Symptomatology**: The patient’s symptoms align with those typically associated with Parkinson's disease, including

## test_12 - What follow-up is arranged and with whom?

**Original:**

The follow-up plan for Olive Parkinson includes:

1. **Clinical Assessment**: The primary focus is on evaluating the current clinical picture, which is most consistent with idiopathic Parkinson's disease (Hoehn & Yahr stage 2).
   
2. **Initial Treatment Plan**: The patient will be referred to physical therapy as part of the initial treatment plan. This is because the symptoms described (cogwheel rigidity, asymmetric tremor, and postural instability) are characteristic of Parkinson's disease.

3. **Follow-Up**: The patient will be scheduled for a follow-up appointment in 8 weeks (February 6, 2026), at which time Dr. Malcolm Graves will address any possible overlap between Graves' disease and the patient's condition. This follow-up visit is separate from

**Masked:**

The follow-up plan for the patient is as follows:

1. **Initial Assessment**: The patient is scheduled for a clinical assessment at Neurology Clinic (DATE_1) to evaluate the presence of idiopathic Parkinson's disease (PD) and its progression stage.

2. **Carbidopa/Levodopa Trial**: If the initial assessment indicates that the patient may have PD or if there are signs of worsening symptoms, she will be referred to Physical Therapy (DATE_2). This referral is necessary because the patient's tremor pattern suggests an underlying issue beyond just PD.

3. **Follow-Up**: After the initial assessment and referral, the patient will undergo a comprehensive follow-up appointment at Neurology Clinic (DATE_3), where they will continue to monitor the patient's condition and adjust treatment plans

## test_23 - Summarise this clinical note in 3 sentences for a handover.

**Original:**

The patient Simonbar Sinistaj has been following up on his hypertension treatment with lisinopril. His home readings have remained within the target range of 130/80 since starting the medication three months ago. He reports no side effects and maintains a daily walking routine of 30 minutes, five times per week. The patient's blood pressure has recently risen to 132/82 mmHg, which he continues to take as prescribed. If any pharmacy-related issues arise, Dr. Mira Halimi should be contacted for assistance, or he can reach out via phone at 555-016-2099 or email at 555-016-2100.

**Masked:**

The patient has been experiencing high blood pressure (hypertension) for three months and has not taken any medication. His BP is currently 132/82 mmHg, which is within the target range but still needs to be monitored closely. The patient's son is also being followed up as part of the same visit. Dr. [NAME_3]'s primary responsibility is to interpret the patient's condition and provide appropriate treatment recommendations.

## test_23 - What is the working diagnosis and the key supporting findings?

**Original:**

The primary care visit for Simonbar Sinistaj was scheduled on October 10, 2025. The patient presented with hypertension, which has been managed with lisinopril for three months. His home readings have remained within the normal range of 130/80 mmHg since starting the medication. There were no reported side effects from the lisinopril treatment.

The patient's blood pressure today is 132/82 mmHg, which falls within the therapeutic range. He continues to take his prescribed dose of lisinopril. The next step would be to review his BP readings every six months at an annual visit (April 2026). If the readings exceed 150/90 mmHg,

**Masked:**

The primary care visit details provided indicate that Dr. [NAME_3]'s office has been contacted regarding the patient's hypertension management. The patient, [NAME_1], has reported home readings of 130/80 systolic and 132/82 diastolic pressures over the past three months, with no significant side effects from lisinopril. His blood pressure has recently reached 132/82 mmHg, which he plans to continue on his current medication regimen.

Given this information, the key supporting findings include:

1. **Home Reading Data**: The patient's home readings have consistently shown high blood pressure levels, indicating ongoing hypertension.
   
2. **Medication Compliance**: The patient has continued taking lisinopril as prescribed

## test_23 - What follow-up is arranged and with whom?

**Original:**

The follow-up appointment scheduled for October 10, 2025 involves Simonbar Sinistaj presenting to address hypertension. The primary care physician will be Dr. Mira Halimi, MD. This appointment is part of a routine check-up that includes monitoring blood pressure levels over time. If there are any concerns about the patient's health, such as changes in BP readings exceeding 150/90 mmHg, the doctor will likely discuss these issues further during the visit.

**Masked:**

The follow-up appointment is scheduled to be conducted on **[DATE_2]**. The primary care physician will be Dr. [NAME_3], MD, who will address the patient's hypertension and provide guidance on medication management. The doctor will also inquire about any concerns related to the patient's son [NAME_2].
