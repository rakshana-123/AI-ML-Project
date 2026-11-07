"""Hand-written, hand-labelled test set (25 notes).

These notes are deliberately written in a style DIFFERENT from the synthetic
training templates: fresh vocabulary, hand-invented names/numbers, adversarial
phrasings, and edge cases from the brief (ambiguous eponyms, relative vs
calendar dates, age 88/89/90 boundaries, misspellings, tables, signature
blocks, DC vs state, ZIP+4 ...).

Each identifier is annotated inline as  [[TYPE::value]]  and converted to
exact character spans by build_testset.py.  Nothing here is generated from
the training generator; every note and label was written by hand.
"""

# (id, focus, note-with-inline-markup)
TEST_NOTES = [

("test_01", "classic H&P header + body",
"""WEXFORD MEMORIAL HOSPITAL
Internal Medicine - Admission History & Physical

Visit date: 04/09/2025
Name: [[NAME::Gloria M. Castellanos]]    MR: [[MRN::77-40219]]
DOB: [[DATE::July 23, 1951]]    Sex: F    PCP: [[NAME::Dr. Erin Wallace]]

Chief Complaint: "My legs are swelling."
HPI: 73-year-old female, history of CHF and AFib, presenting with 3 days of
bilateral leg swelling and worsening dyspnea on exertion. She ran out of
furosemide two weeks ago. Denies chest pain. Notes similar symptoms last year.
PMH: CHF (EF 35%), AFib on apixaban, HTN, CKD stage 3.
SH: Retired schoolteacher. Lives with her daughter [[NAME::Pilar]] at
[[LOCATION::118 Bonnyview Road, Apt 9C]] in [[LOCATION::Millhaven]], Ohio
[[LOCATION::44872]]. Former smoker 20 pack-years, quit 1998.
Exam: BP 148/86, HR 92 irregular, RR 18, SpO2 94% RA. 2+ pitting edema to
mid-shin, bibasilar crackles.
A/P: Acute on chronic diastolic heart failure. Restart furosemide 40 mg daily,
check BMP in 3 days. Cardiology follow-up 04/21/2025 with [[NAME::Dr. Wallace]]
at [[LOCATION::Wexford Heart Institute]]; office [[PHONE::(814) 555-0173]],
fax [[PHONE::814.555.0186]].

Electronically signed by [[NAME::Dr. Marcus Okafor]], MD on [[DATE::04/09/2025]]
at 21:47."""),

("test_02", "SOAP progress note, relative vs calendar dates",
"""PROGRESS NOTE - 4 West (Telemetry)
Hospital day 3
Date: [[DATE::2025-04-11]]

Patient: [[NAME::Robert Fenwick]]   MRN: [[MRN::0038471]]

S: Patient reports feeling "much better". Sleeping through the night. No
chest pain since PCI. Ambulating in hall 3 times since this morning.
Nurse states he ate most of breakfast.

O: T 36.8, HR 68 regular, BP 124/74, RR 14, SpO2 97% on room air.
Labs this morning: troponin 0.02 (down from 0.11 at admission), creatinine
1.1. Accession [[ACCOUNT::L-99284-33]].

A/P: NSTEMI, day 3 post-PCI, uncomplicated. Continue dual antiplatelet
therapy. Monitor for groin hematoma x 24 hours. Discharge anticipated
tomorrow-pending cardiology clearance. Discharge teaching started
POD 3; wife [[NAME::Doris Fenwick]] present and verbalized understanding.

Paging: [[PHONE::(603) 555-0142 x2774]]

[[NAME::Anjali Rao]], DO
[[DATE::11 April 2025]] 09:12"""),

("test_03", "discharge summary with medication table",
"""DISCHARGE SUMMARY
Patient: [[NAME::Yolanda Becerra]]          MRN: [[MRN::MR5882094]]
Admitted: [[DATE::03/02/25]] through ED      Discharged: [[DATE::March 8, 2025]]
Attending physician: [[NAME::Dr. Simon Petrov]], Hospitalist

Brief hospital course:
Ms. Becerra is a 66 year-old female admitted with community-acquired
pneumonia, right lower lobe. Treated with IV ceftriaxone and azithromycin,
transitioned to oral levofloxacin after 72 hours. Afebrile for 48 hours
prior to discharge. Chest X-ray improved compared to admission study.

DISCHARGE MEDICATIONS
Medication                  Directions            Started
1. levofloxacin 500 mg      one tablet daily      [[DATE::03/07/25]]
2. guaifenesin 100 mg/5mL   10 mL QID PRN cough   [[DATE::03/07/25]]
3. metformin 500 mg         twice daily with meals [[DATE::01/14/25]]
4. lisinopril 10 mg         once daily            [[DATE::01/14/25]]

Follow-up: primary care within 7 days with [[NAME::Dr. Alice Nkemdirim]] at
[[LOCATION:Brightwater Family Practice]], [[LOCATION::402 Kestrel Lane, Suite 210]].
Appointment already booked for [[DATE::03/14/2025]]. Clinic phone
[[PHONE:555-019-8874]].

Discharged home with daughter [[NAME::Marisol Becerra-Trent]].
Insurance: MetroHealth Plan member [[HEALTHPLAN::MH-4077215-B]],
account [[ACCOUNT::99310-447]].

Signed: [[NAME::S. Petrov]], MD   [[DATE::3/8/25]] 14:05"""),

("test_04", "referral letter with letterhead and address block",
"""[[LOCATION:Northfield Orthopaedic Associates]]
[[LOCATION:88 Cadogan Court, Building C]]
[[LOCATION:Rosemont]], Vermont [[LOCATION:05760]]
Phone [[PHONE:(802) 555-0139]] / Fax [[PHONE:(802) 555-0140]]

Re: [[NAME::Douglas Whitfield]]    DOB [[DATE:11/28/1962]]    ID [[MRN::447-0291]]

Dear [[NAME::Dr. Priya Raghavan]],

Thank you for seeing this 62-year-old gentleman for evaluation of right knee
pain, present for six weeks after a fall from a ladder. X-rays from
[[DATE:February 3rd]] show medial compartment narrowing. He has had no
locking but reports intermittent swelling after activity.

I have started NSAIDs and physical therapy. Given persistent symptoms, I
would appreciate your opinion regarding candidacy for unicompartmental
replacement.

My direct line is [[PHONE:802-555-0162]] and I can also be reached at
[[EMAIL:d.whitfield-ortho@northfieldortho-example.org]].

With thanks,

[[NAME::Gregory Lin]], MD, FACS
Northfield Orthopaedic Associates"""),

("test_05", "radiology report",
"""[[LOCATION::Cascade Valley Imaging Center]]
RADIOLOGY CONSULTATION REPORT

Examination: MRI left knee without contrast
Exam date: [[DATE::26-Feb-2025]]
Referring physician: [[NAME::Dr. Helen Osei]]
Patient: [[NAME::Marcus Dewilde]]    DOB: [[DATE::09/09/1978]]    Accession:
[[ACCOUNT::CVI-778204]]

CLINICAL HISTORY: 46-year-old male, acute lateral knee pain after pivoting
injury 4 days ago.

TECHNIQUE: Multiplanar multisequence MR images of the left knee were
obtained without intravenous contrast.

FINDINGS: There is increased signal within the anterior horn of the lateral
meniscus extending to the free edge, consistent with an oblique tear. No
displaced fragment. Ligaments intact. Moderate joint effusion. No fracture
or osteonecrosis.

IMPRESSION:
1. Oblique tear, lateral meniscus anterior horn.
2. Moderate effusion.
3. Recommend orthopaedic consultation; report available in the patient
portal at [[URL:portal.cascadevalley-example.com]].

Dictated by [[NAME::Dr. Helen Osei]], MD; electronically signed
[[DATE::02/26/2025]] at 16:03. Report ID [[ACCOUNT::R-2025-118442]]."""),

("test_06", "ED note with SSN and next of kin",
"""EMERGENCY DEPARTMENT RECORD - Bay Ridge Campus
Arrival: [[DATE::08/17/2025]] 02:19    Triaged: 02:24    Room 14
Patient: [[NAME::KEATON, RAMON]]    MRN [[MRN::2277-88301]]    DOB [[DATE:4/3/1966]]

Brought in by private vehicle. Complaint: severe lower back pain beginning
yesterday morning after lifting boxes, now radiating down the left leg.

Triage vitals: BP 152/90, HR 88, RR 18, T 98.4F, SpO2 96%.

ED course: IV placed, given ketorolac and valium with partial relief. Low-dose
CT performed showing L4-L5 disc protrusion without cauda equina. Attending
[[NAME::Dr. Farrah Siddiqui]] at bedside 02:45. Registration confirmed
identity via SSN [[SSN::521-88-9012]] on file.

Next of kin: brother [[NAME::Victor Keaton]] contacted at [[PHONE:5550172398]],
aware of disposition.

Disposition: discharge home with instructions, follow-up Monday
with [[NAME::Dr. Siddiqui]] or PCP [[NAME::Angela Flores-Whitman]] within
3 days. Work note provided.

[[NAME:F. Siddiqui]], MD    [[DATE:17 Aug 2025]] 04:10"""),

("test_07", "psych note, age > 89, email, portal URL",
"""BEHAVIORAL HEALTH INTAKE NOTE
Session date: [[DATE::10/06/2025]]
Client: [[NAME::Harriet Blum]] (she/her)    Chart: [[MRN::BH-330118]]
Clinician: [[NAME::Jordan Mercer]], LCSW

Harriet is a [[AGE::93]]-year-old widow self-referred for anxiety and
adjustment difficulties following her move to [[LOCATION:Sunrise Assisted
Living of Dutton County]] in [[DATE:June]]. She reports poor sleep, worry
about "being a burden", and tearfulness most days for the past two months.
No SI/HI. Cognitively intact per collateral from son [[NAME::Alan Blum]],
who joined the first 10 minutes by phone.

Daughter [[NAME::Ruth Cullinan]] is listed as emergency contact,
[[PHONE:555.017.2280]].

PHQ-9 = 11, GAD-7 = 14.

Plan: weekly CBT sessions; psychiatry referral for medication evaluation
with [[NAME::Dr. Naomi Feld]]. Client prefers appointment reminders by
email at [[EMAIL:hblum1932@example-mail.com]]. Telehealth option via
[[URL:https://secure.counselconnect-example.net/hblum]]; last session
joined from IP [[IP::172.20.14.88]].

Crisis resources reviewed; client verbalized the safety plan. Follow-up
session scheduled for [[DATE::10/13/2025]]."""),

("test_08", "telehealth visit with IP, URL, email",
"""VIRTUAL CARE VISIT NOTE
Date of service: [[DATE::9/29/2025]]    Platform: [[URL::www.virtuwell-example.com/visit]]
Patient: [[NAME::Devon Marsh]]    DOB [[DATE::12/02/1994]]
Provider: [[NAME::Dr. Ijeoma Uzoma]], Family Medicine

Video visit conducted with patient at home in [[LOCATION:Kelso]]. Device
authenticated from IP [[IP::68.203.11.5]]. Patient confirmed identity via
portal email [[EMAIL:dmarsh.94@mail-example.org]].

HPI: 30-year-old male with 5 days of sore throat, rhinorrhea, no fever.
Rapid strep at [[LOCATION:Kelso MinuteClinic]] on [[DATE:09/26/25]]
negative. Symptoms improving; no antibiotic indicated per CENTOR criteria.

Plan: supportive care; return if fever > 101F or symptoms persist beyond
10 days total. Prescription sent to [[Location::Greenfield Pharmacy on
Mulberry Street]]. Follow-up message thread in portal
[[URL::virtuwell-example.com/messages]]; nurse line [[PHONE:(800) 555-0199]].

Total visit time 14 minutes, of which 9 minutes counseling.

[[NAME::I. Uzoma]], MD"""),

("test_09", "operative report with DEA and licenses",
"""OPERATIVE REPORT

Date: [[DATE::2025.05.14]]
Facility: [[LOCATION::Saint Aurelia Surgical Pavilion]]
Patient: [[NAME::Teresa Giannopoulos]]    MRN: [[MRN::SA-112098]]
Surgeon: [[NAME::Dr. Colin Marsden]]    NPI [[LICENSE::1730288475]]
Assistant: [[NAME::Ben Osei-Atta]], PA-C
Anesthesia: [[NAME::Dr. Weiran Sun]], MD
Anesthesiologist DEA [[LICENSE::BS9482013]]

PREOPERATIVE DIAGNOSIS: Right inguinal hernia, reducible.
POSTOPERATIVE DIAGNOSIS: Same.
PROCEDURE: Laparoscopic right inguinal hernia repair, mesh.

EBL: 25 mL. Complications: none. Specimen: none. Counts correct.
Tourniquet time: none. Procedure began 07:52, completed 08:41.

The patient was identified in the preoperative area, site marked and
confirmed with the time-out. After induction of general anesthesia the
abdomen was prepped and draped in standard fashion. Details of mesh
placement are recorded in the dictated operative log, reference
[[ACCOUNT::OR-5566-4421]].

Postop condition stable, extubated in OR, to PACU in stable condition.
Follow-up in clinic [[DATE::05/28/2025]]; surgeon contact via office
[[PHONE:555-488-2200]], fax [[PHONE:555-488-2201]].

Electronically signed: [[NAME::C. Marsden]], MD, FACS  [[DATE:14 May 2025]]"""),

("test_10", "pathology report with accession and delivery email",
"""ANATOMIC PATHOLOGY REPORT - [[LOCATION:Harrowgate Laboratories, plc]]
Specimen received: [[DATE::11/03/2025]]    Reported: [[DATE::11/07/2025]]
Patient: [[NAME::Fumiko Tanaka-Ishii]]    DOB [[DATE:03/17/1958]]
MRN: [[MRN::887123]]    Accession: [[ACCOUNT::S25-0993871]]
Patient account: [[ACCOUNT::77-2091-44]]

SPECIMEN: shave biopsy, left scapular skin lesion, 5 mm.

GROSS: Tan-brown shave, 5 x 4 x 1 mm. Entirely submitted in cassette A1.

MICROSCOPIC: Sections show a symmetric, well-circumscribed proliferation
of basaloid cells with melanin pigment, maturing at the base. No atypia.
Pigmented basal cell carcinoma is not present. Findings favor a
seborrheic keratosis with irritation changes.

DIAGNOSIS: Skin, left scapula, shave biopsy - irritated seborrheic
keratosis; margins negative for atypia.

Note: results discussed with referring dermatologist [[NAME::Dr. Callie
Moreau]] on [[DATE::11/06/25]] and released to the patient portal
[[URL:results.harrowgate-example.com/patient]]. Copies emailed to
[[EMAIL:f.tanaka.ishii@example-mail.net]] at the patient's request.

[[NAME::Percival Odum]], MD, FCAP    Staff pathologist"""),

("test_11", "billing/registration summary",
"""PATIENT ACCOUNT STATEMENT - [[LOCATION::Lakeshore Health System]]
Statement date: [[DATE::10/31/2025]]

Guarantor: [[NAME::Eleanora Vasquez-Doyle]]
Account number: [[ACCOUNT::4400-918-72]]
Service dates: [[DATE::10/03/25]] - [[DATE::10/06/25]]

Address on file:
[[LOCATION::74 Windward Passage]]
[[LOCATION:Eastport]], Maine [[LOCATION::04631]]

Primary coverage: PineTree Health Cooperative
Member: [[HEALTHPLAN::PTC-9-8871204]]    Group: [[ACCOUNT::G-1174]]
Secondary: none on file.

Home phone: [[PHONE:(207) 555-0163]]    Mobile: [[PHONE:207-990-0163]]
Statements delivered to [[EMAIL:nora.vd@examplebox.com]].
Identity on file: SSN [[SSN::013-62-4471]], driver license
[[LICENSE::D-5546-3390-8871]] (state ME).

Patient responsibility after adjudication: $312.40. Payment plans and
paperless billing via [[URL:pay.lakeshorehealth-example.org/440091872]].
Questions: billing office [[PHONE:800-555-0144]], fax [[PHONE:800-555-0145]]."""),

("test_12", "eponym ambiguity torture",
"""NEUROLOGY CLINIC NOTE
[[DATE::12/12/2025]]

Patient: [[NAME::Olive Parkinson]], 71F, seen with her husband
[[NAME::Gerald Parkinson]]. Referred by [[NAME::Dr. Felicity Huntington]]
for tremor evaluation.

History: Over the past 8 months the patient has developed a resting tremor
of the right hand. Her mother reportedly had Parkinson's disease.
[[NAME::Dr. Huntington]] wondered whether this represents early
Parkinson disease versus essential tremor. Of note, the family also has a
history of Huntington disease on the paternal side, and the patient's
brother [[NAME::Ray Parkinson]] carries the diagnosis of Huntington's
disease, so genetic counseling has been arranged.

Exam: cogwheel rigidity right > left, asymmetric tremor, postural
instability on pull test.

Assessment: Clinical picture most consistent with idiopathic
Parkinson's disease (Hoehn & Yahr stage 2).

Plan: begin carbidopa/levodopa trial, refer to physical therapy, reassess
in 8 weeks ([[DATE:02/06/26]]). [[NAME::Dr. Malcolm Graves]] will address
possible Graves disease overlap given her thyroid history; endocrine
follow-up is separate.

Contact: movement disorders scheduler [[PHONE:555-013-7700]],
portal [[URL:neuro.example-health.org/movement-disorders]].

[[NAME::A. Whitcomb]], MD, PhD - Neurology"""),

("test_13", "date format torture; relative time kept",
"""DIABETES CLINIC FLOW SHEET - visit of [[DATE::13 Jan 2026]]

Patient: [[NAME::Cyrus Njoku]]    MRN [[MRN::D-99-44021]]
Type 1 diabetes since 2003 (diagnosed age 11).

Recent visits: [[DATE:10/14/2025]], [[DATE:July 2025]], [[DATE:04/2025]]*,
[[DATE:22 December 2025]] (nutrition), [[DATE:1/6/26]] (endocrine NP).
*telehealth

CGM downloaded today; data cover the last 14 days. Time in range 62%,
up from 48% last quarter. No severe hypoglycemia in 6 months.
Insulin pump site changed every 3 days as recommended.

Lab: A1c today 7.4% (previous 8.1% on [[DATE::Oct 14, 2025]]).
Urine microalbumin pending from sample dropped 2 days ago.

Plan: continue current basal-bolus via pump. Recheck A1c in 3 months,
i.e. [[DATE:April 2026]]. Next pump supply shipment arrives in 1 week.
Contact diabetes educator [[NAME::Rebecca Lomax, RN]] at
[[PHONE:555.662.0188]] or [[EMAIL:r.lomax@diabetes-care-example.org]]."""),

("test_14", "age boundary torture",
"""GERIATRIC ASSESSMENT CLINIC
Consultation date: [[DATE:06/06/2026]]

Referral source: [[NAME::Dr. Beatrice Anand]], PCP.

1. [[NAME::Agnes Kowalczyk]], aged [[AGE::101]], community-dwelling,
   being assessed for memory decline. Husband died at 88. Daughter
   [[NAME::Marta Kowalczyk]] is primary caregiver.
2. Her sister, [[NAME::Sophie Renard]], is a [[AGE::94]]-year-old living
   at [[LOCATION:Foxglove Manor Nursing Home]], [[LOCATION::12 Thistle
   Way]], [[LOCATION:Brambleton]], Iowa [[LOCATION::51004]].

Today's index patient is a 88-year-old male, [[NAME::Walter Chase]] (not
present today). Also on panel: [[NAME::Ida Bloom]], who is 89, and
[[NAME::Salvatore Ferraro]], who will be 90 this fall - both stable.

Cognitive screening: MoCA 22/30. Functional status: independent ADLs.
Advanced care planning discussed with [[AGE::97]]-year-old matriarch
[[NAME::Ginevra Ferraro]] by phone at [[PHONE:555-014-9922]].

Most patients tolerate assessment batteries well; the 45-minute format
suits adults up to age 89; beyond age 89 we shorten sessions, and for
anyone over 93 we offer home visits. A separate cohort of 65-70 year-olds
serves as controls.

Follow-up: [[DATE:07/08/2026]]. Clinic director
[[NAME::Dr. H. Okonkwo-Bello]], contact [[EMAIL:gaitclinic@university-example.edu]]."""),

("test_15", "misspellings, casing, punctuation variants",
"""AFTER-HOURS TRIAGE NOTE
Caller identifies as patient "jonathon smythe" (spelled J-O-N-A-T-H-O-N).
Chart search matches [[NAME::Jonathon Smythe]], DOB [[DATE:2/29/1984]].
Verify: no, DOB does not match chart; chart shows [[DATE:02/29/1984]] and
caller gave a different year. Second match found: [[NAME::Jonathan Smythe]]
(pronounced "smith"), DOB [[DATE:2/28/1984]] - likely correct party.

Caller states 4 days of vomiting; unable to keep down oral intake since
Tuesday. Advised ED evaluation. Caller declined, will call PCP
[[NAME::Dr. Marisol Quant]] in the morning at [[PHONE:(513) 555-0110]].

Callback number provided: [[PHONE:513.555.0117]] (caller's mother,
[[NAME::delia smythe]]). Alternate contact listed in chart:
[[NAME::D. SMYTHE]] [[PHONE:5135550118]].

Note entered by RN [[NAME::K. Oyelaran]] on [[DATE:29.Oct.2025]] 23:58.
Supervisor notified: [[NAME::R. Tremblay]], RN. Incident ID
[[ACCOUNT::IR-2025-77314]]."""),

("test_16", "fixed-width table",
"""AMBULATORY CARE NOTE                                    [[DATE::11/14/2025]]
------------------------------------------------------------
Patient   : [[NAME::Priya Venkataramanan]]
Clinic #  : [[MRN::AC-77-2291]]        Pharm on file : [[LOCATION:Corner Druggist, 5 Elm Row]]
Home      : [[LOCATION:1620 Marlow Heights Dr. NW]]            City/Zip : [[LOCATION:Arborview]] [[LOCATION::20877-4412]]
Employer  : Arborview Public Schools (school nurse [[NAME:Colleen Bray]])
------------------------------------------------------------
DATE         WEIGHT    BP      NOTE
[[DATE::09/12/25]]   72.1 kg   118/76   Annual PE, well
[[DATE::10/03/25]]   71.8 kg   122/78   BP recheck, NL
[[DATE::11/14/25]]   71.4 kg   120/74   Ortho eval L ankle
------------------------------------------------------------
Plan: RICE protocol 1 week, recheck 7 days post injury.
Return sooner if unable to bear weight. Portal:
[[URL:arborview-health-example.org/me]]    Helpdesk
[[PHONE:301-555-0190]] (ask for IT, ext 4). Home IP for the patient
portal session logged as [[IP::192.168.1.117]].

Signed: [[NAME::Dr. T. Halvorsen]], MD [[DATE::14 Nov 2025]]"""),

("test_17", "signature-block heavy consult letter",
"""PULMONOLOGY CONSULTATION

To: [[NAME::Dr. Yolande Pritchard]], [[Location:Chest Medicine of the
Riverbend]]   Fax [[PHONE:503-555-0166]]
From: [[NAME::Dr. Omar Suleyman]], [[LOCATION:Riverbend University
Hospital]], Pulmonary & Critical Care
Re: [[NAME::Bernard Toft]]   DOB [[DATE:6/6/1950]]   MRN [[MRN:RB-4420913]]
Date of consult: [[DATE::2026/01/09]]

Dear Yolande,

Thank you for asking me to see this 75-year-old gentleman with a 9-month
history of progressive exertional dyspnea and a dry cough. He stopped
working as a stonemason in 2018. He has never smoked. Spirometry last
month shows restriction; HRCT obtained [[DATE:12/18/2025]] demonstrates
lower-lobe predominant reticulation with traction bronchiectasis,
consistent with usual interstitial pneumonia.

I have started antifibrotic therapy and arranged pulmonary rehab at
[[Location:Riverbend Pulmonary Rehab]]. I will see him again in 6 weeks.

Please do not hesitate to call my office [[PHONE:503.555.0190]] or email
[[EMAIL:o.suleyman@riverbend-u-example.edu]].

Yours sincerely,

______________________________
[[NAME::Omar Suleyman]], MD, MRCP
Associate Professor of Medicine
[[LOCATION:3211 Riverbend Parkway, Floor 4]] | [[PHONE:503-555-0192]]
Attending of record for this encounter: [[NAME::Dr. Nasrin Alamy]],
covered [[DATE::01/09]]-[[DATE::01/11]] while I was away.

cc: [[NAME::B. Toft]] via patient portal [[URL:my.riverbend-u-example.org]],
    phone [[PHONE:5035550171]]
Dictation ID [[ACCOUNT::D-2601-33097]]"""),

("test_18", "address variants incl. DC and ZIP+4",
"""PUBLIC HEALTH CONTACT TRACING FORM (synthetic practice exercise)
Form completed: [[DATE:07/22/2025]]

Subject: [[NAME::Marisol Quintero-Avila]]    Contact ID
[[ACCOUNT::CT-772-019]]    Phone [[PHONE:(202) 555-0188]]
Email [[EMAIL:marisol.qa@example-mail.com]]

Residence: [[LOCATION:1200 Independence Ave SE]], [[LOCATION:Washington]],
DC [[LOCATION:20003-1234]]
Employer: [[LOCATION:Capitol Hill Dental Group]], [[LOCATION:415 Duddington
St SE]] (works 3 days weekly on site)
School: none

Visited during infectious period:
- [[LOCATION:Northeast Market]], [[LOCATION:1400 H Street NE]] on [[DATE:07/15/25]]
- [[LOCATION:Anacostia Park]] (outdoor) on [[DATE:July 16th]]
- [[LOCATION:Union Station]] pharmacy counter on [[DATE:07/18/2025]]
Trip out of state: flew to [[LOCATION::Atlanta]], Georgia on [[DATE:07/19/25]], returned
[[DATE::07/21/25]] (airline seat 14C, flight not tracked).

Household contacts: partner [[NAME::Devon Alvarado]] (age 41), daughter
[[NAME:Luz Alvarado]] (age 7), grandmother [[NAME::Abuela Rosa Quintero]],
aged [[AGE::96]], all advised to test 5 days after exposure.

Case investigator: [[NAME::R. Etienne]]    Field office
[[LOCATION:409 C Street SW]]    Direct [[PHONE:202-555-0176]]"""),

("test_19", "phone format torture",
"""HEMATOLOGY/ONCOLOGY - TREATMENT COORDINATION NOTE
Patient: [[NAME::Aisha Bellamy-Ruiz]]    MRN [[MRN::HOT-99126]]
Cycle 3 of R-CHOP scheduled for [[DATE:09/09/2025]]; arrive 08:00.

Coordination calls this morning:
- Patient home: [[PHONE:555-017-9088]] (left voicemail)
- Patient mobile: [[PHONE:+1-555-017-9089]] (spoke with patient)
- Work (florist, [[LOCATION:Verdant & Vine Flowers, 902 Longview Ave]]):
  [[PHONE:555.017.9090]] (message left with manager)
- Ride service confirmed from [[LOCATION:Longview Apartments, Bldg 7]]:
  pickup [[DATE:09/09/2025]] 07:15
- Infusion center fax: [[PHONE:1-800-555-0131]] / direct fax
  [[PHONE:555-013-1200]]
- Insurance prior auth: member [[HEALTHPLAN::ZQ-88-J41927]], auth number
  [[ACCOUNT::PA-2025-88214-9]], coordinator [[NAME:Dana Kerr]] at
  [[PHONE:(800) 555-0155 x3341]]

Note: patient's cousin [[NAME:Rosa Ruiz]] (next of kin) reached at
[[PHONE:5550179911]] regarding transportation backup.

Pharmacy specialty line for rituximab sourcing: [[PHONE:800-555-0162]],
after-hours pager [[PHONE:555-016-4000]].

Entered by [[NAME::Cheryl-Ann Douglas]], RN on [[DATE:09/02/2025]]."""),

("test_20", "URL and IP torture",
"""eHEALTH TECHNICAL SUPPORT NOTE
Ticket [[ACCOUNT::SUP-2025-55129]] opened [[DATE::08/08/2025]] 11:04 by
patient [[NAME:Ernest Caldwell]] (verified via portal username
e.caldwell1957, email [[EMAIL:ernie.c1957@oldmail-example.com]]).

Issue: cannot load lab results on the portal
[[URL:https://portal.metrocare-example.org/results]] - error 502.

Troubleshooting:
1. Asked patient to try [[URL:http://portal.metrocare-example.org]] (HTTP)
   and the mobile app (works). Classic ISP routing issue.
2. Patient IP at time of fault: [[IP::76.183.44.201]].
3. Backend node healthy at [[IP::10.14.2.77]]; CDN edge for the region
   (see [[URL:status.metrocare-example.org/edge-nodes]]) shows elevated
   latency from [[IP::68.183.44.0/24]] ranges.
4. Workaround: patient set device DNS manually; internal resolver
   [[IP::192.168.0.1]] responds fine. Video guide at
   [[URL:www.youtube.com/watch?v=dQw4w9WgXcQ]] sent to patient
   (standard guide; no PHI).
5. Escalated to network on-call [[NAME:Padma Rangan]] (cell
   [[PHONE:555-018-4400]]); ticket linked to [[URL:status.metrocare-example.org/incidents/8823]].

Resolution: CDN cache purge. Patient confirmed working at 12:31 from
IP [[IP::76.183.44.201]]. Appointment portal unaffected; next visit
[[DATE:08/29/2025]] with [[NAME::Dr. L. Bramble]].

Closed by support agent [[NAME:T. Nguyen]] [[DATE::08/08/25]] 12:40."""),

("test_21", "place-name persons vs states",
"""AMBULATORY SURGERY PRE-OP NOTE - [[DATE::05/05/2026]]

Patient: [[NAME::Austin Houston]] (first name [[NAME::Austin]], surname [[NAME::Houston]] -
verified twice because of the matching Texas cities). DOB
[[DATE:05/05/1971]] - 55th birthday today.

Emergency contact: sister [[NAME::Charlotte Houston]], reachable in
[[LOCATION:Charlotte]] but traveling to [[LOCATION:Atlanta]] this week;
best number [[PHONE:555-014-7788]].

Procedure: right carpal tunnel release, 20 minutes, local with sedation.
Surgeon [[NAME::Dr. Denver Jauregui]] (yes, named [[NAME::Denver]], practices in
[[LOCATION:Denver]], Colorado).

Insurance: Employers Health Fund, member [[HEALTHPLAN::EHF-3355-8890]],
group [[ACCOUNT::SE-77]].

Home address: [[LOCATION:909 Madison Avenue]], [[LOCATION:Madison]],
Wisconsin [[LOCATION::53703]]. Note the street and city share the name
Madison; both are identifiers; the state (Wisconsin) is not.

Companion for discharge: neighbor [[NAME:Georgia O'Rourke]] (no relation
to the state of Georgia), phone [[PHONE:608-555-0173]].

Time-out performed. Consent signed [[DATE::05/05/2026]] 06:58.
Anesthesia: [[NAME::Dr. Frank Osei]], time 07:15. Patient tolerating
procedure well; to recovery 07:52.

[[NAME::D. Jauregui]], MD"""),

("test_22", "sparse note",
"""Nurse visit note - suture removal.
[[NAME::Wendell Aske]] doing well; wound clean, no signs of infection.
Sutures out; Steri-Strips applied. RTC if redness or drainage.
Done 09:15 by [[NAME::N. Tamas]]."""),

("test_23", "repeated values -> same placeholder expected",
"""PRIMARY CARE VISIT - [[DATE::10/10/2025]]

[[NAME::Simonbar Sinistaj]] (that spelling is correct; chart annotation
says "pronounced see-mon-BAHR") presents for follow-up of hypertension.

[[NAME::Simonbar Sinistaj]] reports home readings 130s/80s since starting
lisinopril 3 months ago. No side effects. walked 30 min, 5 days weekly.

BP today 132/82. Continue current dose; recheck in 6 months at annual
visit ([[DATE:04/2026]]) or sooner if readings exceed 150/90.

If pharmacy questions arise, contact [[LOCATION:Stapid Pharmacy]] where
[[NAME::Simonbar Sinistaj]] fills prescriptions, or call me at
[[PHONE:555-016-2099]] / fax [[PHONE:555-016-2100]].

Interpreting for the visit: his son [[NAME::Endrit Sinistaj]].

[[NAME::Dr. Mira Halimi]], MD"""),

("test_24", "mixed identifiers, IDs in unlikely places",
"""SLEEP MEDICINE CONSULT
Date: [[DATE::02/02/2026]]

Patient: [[NAME::Orrin Blackwater]], 58M, referred by
[[NAME::Dr. Cassia Villanueva]] (license [[LICENSE::V-9082-114-K]]).
MRN [[MRN::Z-44-991-2]] (older clinic format).

Fibromyalgia score 14. Snoring, witnessed apneas; Epworth 12. Boss at
[[LOCATION:Blackwater & Sons Machine Shop]] supportive of schedule change.
CPAP supplies shipped to [[LOCATION:31 Quarry Road]] in [[LOCATION:Stone
Creek]] on [[DATE:01/28/26]]; tracking not clinical, billing account
[[ACCOUNT::SM-772-9014]].

Insurance: Northern Health Plan, policy holder same patient, member ID
[[HEALTHPLAN::NHP 889-4471-02]], SSN on the old card he brought in:
[[SSN::588 44 2219]]. Advised not to carry the card.

Research consent offered - study "SLEEP-WELL-2", coordinator
[[NAME:Dr. Priscilla Mott]], data use agreement in the portal
[[URL:research.sleepmed-example.org/consent/88213]]; queries to
[[EMAIL:p.mott@sleepmed-example.org]] or [[PHONE:555-019-4400]].

Remote oximetry loaner kit serial [[LICENSE::OX-918823]] issued; return
visit [[DATE:16 Feb 2026]].

[[NAME:C. Villanueva]], MD"""),

("test_25", "everything note (final boss)",
"""INTERDISCIPLINARY CASE CONFERENCE SUMMARY
Conference date: [[DATE::03/17/2026]], 13:00-14:30
Held at [[LOCATION:Kestrel Point Medical Center, Dempsey Pavilion, 3rd
floor conference room B]] and by video ([[URL:meet.kpmed-example.org/j/882-991-441]];
host IP logged [[IP::10.88.4.21]])

PATIENT: [[NAME::Ramona Ellsworth-Diaz]], DOB [[DATE::April 4, 1931]],
i.e. she will turn [[AGE::95]] next month. MRN [[MRN::KP-77-402-9]].
Admitted [[DATE::03/09/26]] after a fall at [[LOCATION:22 Pilgrim Court,
Unit 2]] in [[LOCATION:Ossining]], New York [[LOCATION:10562-4433]].
Prior admissions: [[DATE:11/2025]] (syncope), [[DATE:06/2024]] (CHF).

FAMILY PRESENT: daughters [[NAME::Celia Ellsworth]] and
[[NAME:Marisol Ellsworth-Diaz]] (zoom), grandson [[NAME:Theo Marsh]]
(phone, [[PHONE:914-555-0188]]).

TEAM: Hospitalist [[NAME::Dr. Amara Nwosu]]; cardiology
[[NAME::Dr. Sun-Wook Bae]] (queried by fax [[PHONE:914.555.0177]]);
palliative care fellow [[NAME::Dr. Lucia Ferreira]]; case manager
[[NAME:Deb Zero]] ([[PHONE:914-555-0165]], [[EMAIL:d.zero@kpmed-example.org]]);
pharmacy reviewed anticoagulation (periprocedural plan of
[[DATE::March 20th]], i.e. 3 days from now).

ISSUES: 1) HF with preserved ejection fraction, 2) delirium improving,
resolved 2 days ago, 3) fall risk, 4) goals of care. Notes from
[[NAME::Dr. Bae]] mention he trained under [[NAME::Dr. Felicity
Huntington]] (no relation to the family's history of Huntington
disease, which is not present in this patient).

FINANCE: insurance member [[HEALTHPLAN::EX-99-441-72]]; hospital account
[[ACCOUNT::77-9923881]]; financial counsel contacted at
[[PHONE:800-555-0140]].

PLAN: discharge to [[LOCATION:Pilgrim Court Assisted Living]] expected
[[DATE::03/20/2026]]; PCP [[NAME::Dr. R. Anand]] to see her within
5 days of discharge; patient prefers email updates at
[[EMAIL:ramona.diaz.1931@silvermail-example.com]] but NOT the old
address [[EMAIL:mona.ellsworth@oldbox-example.net]].

Minutes recorded by [[NAME::Lucia Ferreira]], reviewed by
[[NAME::A. Nwosu]] on [[DATE::18 Mar 2026]]. Document ID
[[ACCOUNT::CONF-2026-0317-9]]. System of record:
[[URL:kpmed-example.org/emr/conf/2026/03/17/8891]]."""),
]
