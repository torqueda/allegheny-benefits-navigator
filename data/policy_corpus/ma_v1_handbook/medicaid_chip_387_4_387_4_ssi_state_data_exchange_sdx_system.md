---
program: Medicaid/CHIP
source_type: official_handbook
title: 387.4 SSIâState Data Exchange (SDX) System
chapter: 387.4
source_url: http://services.dpw.state.pa.us/oimpolicymanuals/ma/387_SSI/387_4_SSI—State_Data_Exchange_SDX_System.htm
accessed_date: 2026-04-19
jurisdiction: Pennsylvania
---

# 387.4 SSIâState Data Exchange (SDX) System

TheÂ SSI Â State Data Exchange (SDX) Â System providesÂ DHSÂ Â with case data on SSI applicants and recipients Â via the â8036 PendâÂ files on Exchange 6 . SSA sends DHS a new or updated â8036 Pendâ file when an individual initiates an SSI claim or there is a change in the individualâs SSI case. When the CAO initiates an Exchange 6 request for an individual, SSA responds with the latest â8036 Pendâ file they have, as long as the state of jurisdiction is assigned to PA. Â See Using IEVS, Exchange 6, SDX information and Exchange 6: SSA SDX- State Data Exchange f or details on the information provided by SSA on the SDX files .

When the CAO receives information from the SDX, the CAO must review the information and decide what action to take for MA eligibility.

Â Â Â Â Â Â NOTE: The CAO should contact SSA for more information if the SDX Exchange 6 information is unclear or incomplete.

Reminder: Â If an Exchange 6 hit or an alert is received, t he CAO must review the hit dispositionÂ reason code or alert description , as well as the SDX payment status code and the MA eligibility code. In addition, the CAO should review any new information that will be displayed in bolded font on the SDX file . These codes , descriptions, and bolded text will help determine what actions are required on the SSI MA record. SeeÂ Section 387.53, End of SSI MA Benefits for instructions on reviewing other MA benefits when codes indicate that MA should no longer continue in the SSIÂ category .

## 387.41 Disposition Reason Codes

This code appears in the âReasonâ column of the SDX Match Summary Screen as well as in the upper right hand side of the SDX Match Detail s screen of Exchange 6 . It tells why a disposition was set.Â The following codes are used:

- 01â Non-payment of SSI benefits to a Disabled Adult Child (DAC) .

- 02â Active on SDX, not found or active in the appropriate SSI category in e CIS .

- 03â Incorrect category in e CIS.

- 04â Active A, J, M in e CIS. Not found on SDX master file.

Important: The individual is not currently on SDX. This lets the CAO know that the SDX master file could not find an SSI payment for an individual in Pennsylvania. The individual may not be eligible to continue MA in the A, J, or M category.

- 05â Interstate move. The individual has moved to another state. Â

NOTE: Â SDX will process a request to get the out-of-state address.

- 06â Payment amount change.

- 08â Intrastate move. The individual has moved to another address in Pennsylvania, or the payment name has changed.

- 09â Intrastate move. The individual has moved to another address within Pennsylvania or the payment name has changed and there is a change in the payment amount.

- 10â The record was sent for an SSI opening and failed MCI file clearance.

## 387.42 SDX Payment Status Codes

The first position of the payment status code shows the status of SSI payment eligibility. The second and third positions show the reason for the status. The following codes are used for the first position:

- Câ The individual is eligible for SSI, a state supplement (SS) payment, or both.

- Eâ The individual is eligible for federal or state benefits (or both) under the eligibility computation, but (a) no payment is due under the payment computation or (b) the benefit is not payable in that month because of a new application date.

- Hâ âHoldâ status, final decision pending.

- Mâ Under manual control, called a âforced payment,â although a payment may not be involved.

- Nâ Non-pay. The applicant is not eligible for SSI or SS payments, or a previously eligible recipient is no longer eligible.

- Sâ Suspended. The recipient may still be eligible for SSI or SS but is not getting payments.

- Tâ SSI or SS eligibility is terminated . In certain cases, an SSI case record may be terminated and a new case record opened.

See Using IEVS, Exchange 6, SDX information, Payment Codes for detailed information on SDX payment status codes.

NOTE: Certain SDX payment status codes will create a disposition reason code Exchange 6 hit that must be reviewed and cleared by the CAO.

## 387.43 MA Eligibility Codes

The following MA eligibility codes show that MA eligibility continues:

- Bâ Deeming waived. Child is under a state home care plan. Child was in an institution and covered by MA. Child is now home and enrolled in an MA waiver program. SSA does not use deeming rules to establish eligibility for these children. SSA continues to pay the personal needs allowance.

- Câ Federally granted MA coverage should be continued no matter what the payment status is. Wages make it not possible for the individual to get any SSI cash benefit, but they are eligible for MA under SSA rules (1619b) .

- Gâ Goldberg/Kelly payment continuation ( appeal status). The payment status code may show a reason why the individual is not eligible for SSI benefits. Because the individual appealed the decision, they are still considered eligible for MA under SSA rules.

- Yâ Eligible for MA

The following MA eligibility codes indicate that the state must review the individualâs case for continued MA eligibility:

- Aâ Refused third-party liability assignment - referred to State , F ederal determination not possible. The individual answered ânoâ to the following question on the SSI application: Do you agree to assign your rights (or the rights of anyone for whom you can legally assign rights) to payments for medical support and other medical care to the State MA agency?

Important: Most SSI applicants and recipients answer âyesâ to this question. When the CAO gets an SSI record with MA eligibility code A, the CAO must contact the individual and the SSA office to make sure of the answer. The CAO must tell the individual that SSI recipients in Pennsylvania automatically get MA benefits. If the individual answered ânoâ to the question, the CAO and the SSA must make sure the individual does not want MA. In most cases, the individual will want MA. The CAO should tell SSA that the individual wants to change their answer to the question. If an individual tells the CAO that âNoâ is the answer they meant, the CAO should submit a policy clarification request, which is to include the case record and recipient identification numbers .

- Dâ Disabled adult child. (See Section 387.62, Title IIâSocial Security Disabled Adult Child (DAC) benefits .)

- FâTitle VIII Recipient. Individual is receiving Special Veterans Benefits (SVB) which are paid to certain World War II veterans who reside outside the USA. SVB is not the same as SSI.

- Qâ Medicaid Qualifying Trusts may exist . If the SSA applicant or recipient uses assets to set up a trust, the trust is counted as a resource for SSI eligibility. Some trusts and trust payments that are not counted as resources for SSI purposes can affect MA eligibility. The DHS must refer SSI trust cases to the following mailing or email address:

TPL Special Needs Trust Depository Attn: Manager TPL Section P.O. Box 8486 Harrisburg, Pennsylvania 17105

RA-PWSNTREPSTRY@pa.gov

- Ensure a full copy of the trust policy and the individualâs eCIS recipient identification number is included in the referral.

Cases should stay open as category A, J, or M until the review is completed by the TPL Special Needs Trust Depository. The CAO will be notified when the review is finished and of its outcome.

Â Â Â Â Â Â Â NOTE: Â The law does not apply to the following trusts, and MA must continue in the SSI category:

- Special-needs trustsâThe state gets whatever is left in the trust when the individual dies.

- Â Pooled trustsâThe money goes back to the individuals who are part of the trust.

- Râ Referred to state; a Federal determination is not possible. (See Section 387.53, End of SSI MA benefits .)

- Sâ State determination; not SSAâs responsibility. The state makes the MA decision for SSI recipients.

Exception: Essential persons are coded S. In Pennsylvania, these individuals can get MA benefits. (See Section 387.3, SSI Benefits .) No determination for MA is needed.

- Wâ Widow or widower. (See Section 387.64, Disabled Widows and Widowers .)

The SSI MA case must stay open until the eligibility review for other MA benefits is finished. The review may lead to one of the following decisions:

- Â Keep MA open in the A, J, or M category.

- Â Close the A, J, or M benefits and open MA in another category.

- Â Close MA. (See Section 387.53, End of SSI MA benefits .)

Updated May 14, 2024, Replacing February 14, 2012
