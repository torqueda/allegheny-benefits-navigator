---
program: Medicaid/CHIP
source_type: official_handbook
title: 388.6 Authorizing Buy-In
chapter: 388.6
source_url: http://services.dpw.state.pa.us/oimpolicymanuals/ma/388_Buy-In/388_6_Approving_Buy-In.htm
accessed_date: 2026-04-19
jurisdiction: Pennsylvania
---

# 388.6 Authorizing Buy-In

Medicare Buy-In Reimbursement Inquiries , PMA18784-388 (Published January 3, 2018)

There are three ways to enroll an individual in Buy-In :

1. CMS Auto-Accrete â SSI recipients are enrolled automatically by the CMS at the directive of the SSA and Pennsylvania is billed for the premiums.

2. Exchange 7 Auto-Accrete â The Buy-In system automatically processes a Part A and/or Part B accrete through an exchange between eCIS and Data Exchange #7 . (See 388.61, Exchange 7 Auto-Accrete Process ).

3. Manual Accrete â The CAO processes a manual Part A and/or Part B accrete on the Exchange 7 Buy-In Action Request screen .

388.61 Exchange 7 Auto-Accrete Process

The CAO will authorize Buy-In as follows:

- Authorize the appropriate Buy-In budget in e CIS and send notice to the client .

NOTE: Â A system-generated notice will tell the recipient that DHS made an enrollment request for Buy-In of Medicare premiums. The notice reason code is 408, option 1. (See Chapter 377, Notices .)

The Buy-In system will automatically process a Part A and/or Part B accrete if the individual is authorized in one of the following category and program status code combinations; AND, Exchange 3 (BENDEX) shows the individual is entitled to Medicare and the Payer is SELF.

A, J, M â any PSC

PH â 80

PM â 81, 84

TAN â 66, 80

B â 80

PI â 66, 80

PM â 86, Part A ONLY

TAW â 66, 80

PA â 81, 84

PJ â 81, 84

PMN â 66, 80

TB â 66, 80

PA â 86, Part A ONLY

PJ â 86, Part A ONLY

PMW â 66, 80

TJ â 65, 66, 67, 80

PAN â 66, 80

PJN â 66, 80

PMW â 81, 84

TJN â 66, 80

PAW â 66, 80

PJW â 66, 80

PW â 66, 80

TJW â 66, 80

PG â 00

PJW â 81, 84

TA â 65, 66, 67, 80

Important: If the individual does not meet both conditions, the Buy-In system cannot auto-accrete, and the CAO will need to process a manual accrete to enroll the individual in Buy-In. For other situations that require the CAO to process a manual accrete, see Section 388.62, Manual Accrete Process .

- Check the Exchange 7 Buy-In Match Results screen in the middle of the next month to make sure that the individual was enrolled in Buy-In. If the auto-accrete was not accepted, enter a manual accrete on the Exchange 7 Buy-In Action Request screen. Contact the CIS Hotline if you need assistance.

Â Â

Â Â Â Â Â Â NOTE: See Using IEVS, Chapter 10, Exchange 7, Glossary for a description of Buy-In transaction codes.

- Review eligibility for Buy-In at renewal and when changes take place that require an eligibility review. These changes include, but are not limited to, the following:

- A change in income

- New persona l property or an increase in value of personal property

- A change in living arrangements

388.611 Special Part A Auto-Accrete for Uninsured Clients

Individuals whose claim number ends in âMâ or âTâ indicates that they do not have a work history and are considered âuninsuredâ by SSA. The Department of Human Services (DHS) is obligated to pay the Part A premiums for these clients if they qualify for Buy-In as a Qualified Medicare Beneficiary (QMB). If an individual is receiving Part B and is considered uninsured by SSA, DHS can authorize them for Part A at any time after Part B has been approved by CMS.

The Buy-In system automatically checks eCIS, BENDEX and SDX to see if a client is eligible for SSI and Medicare. If it can determine the client is active for Part B it will automatically send a request to CMS to open the clientâs Part A back to either their Medicaid start date or their Medicare start date, whichever is later (the start date is limited to no more than two years back).

Important: Cases where the clientâs BENDEX record shows a Part A status code other than âRâ, âTâ, âWâ or blank will not be automatically handled by the Buy-In system. In such cases, the CAO is responsible for processing a manual accrete for Part A.

388.62 Manual Accrete Process

The CAO will process a manual accrete on the Exchange 7 Buy-In Action Request screen in the following situations:

- Â Â Â Â Â Â Â Â Â The individual is active in a category/PSC combination not listed above.

- Â Â Â Â Â Â Â Â The Payer on BENDEX shows anything other than SELF (Ex: 390, RRB, another state code, etc.).

- Â Â Â Â Â Â Â Â The individual receives Railroad Retirement Board (RRB) benefits only (does not receive any RSDI or SSI cash benefits).

- Â Â Â Â Â Â Â The individual is an SSI recipient whom SSA has not enrolled in Buy-In after three months of Medicare eligibility.

- Â Â Â Â Â Â The CAO authorizes a Non-Continuous Eligibility (NCE) transaction for retroactive Buy-In, or to correct a past period of eligibility.

Â Example: A Healthy Horizons (PH00) recipient becomes eligible for Medicare in February. ECIS data entry was completed in May to authorize PH80. The auto-accrete process enrolls the recipient in Buy-In as of May.

Â Â Â Â Â Â Â Â Â Â Â Â Â Â The CAO must complete a manual accrete for the months of Buy-In eligibility before May.

- Â Â Â Â Â Â Â Â BENDEX shows more than one claim account number associated with the individual.

- Â Â Â Â Â Â Â BENDEX shows an âRâ, âTâ or âWâ status code under Part A or Part B.

NOTE: These individuals are considered eligible for Buy-In if they pass all other qualifying criteria, and should be accreted using the current month of eligibility only.

- Â Â A uto-accrete cases rejected for demographic mismatch. (See Section 388.63, Resolving Demographic Mismatch.)

The CAO will check the Exchange 7 Buy-In Match Results screen in the middle of the next month to make sure the individual was enrolled in Buy-In. If the manual accrete was not accepted, enter a new manual accrete on the Exchange 7 Buy-In Action Request screen.

388.63 Resolving Demographic Mismatch

When an accretion is rejected because CMS demographic information does not match that in eCIS, a hit is created on Exchange 7 with transaction code â2163B.â The mismatch is to be resolved within 30 days . The CAO will take the following actions to resolve a demographic mismatch:

1. Â Â Â Â Review the demographic information on eCIS, Exchange 3 and Exchange 7 to determine what is causing the mismatch.

2. Â Â Â Â When the cause of the mismatch CAN be identified, correct the information and process a manual accrete to resubmit the request.

3. Â Â Â Â If the cause of the mismatch CANNOT be determined, send an email requesting a review to the Buy-In Mailbox ( RA-buyin@pa.gov ). The email request should include the following information:

- County and case record number

- Name of the individual

- SSN of the individual

- Rejection code on Exchange 7

NOTE: The CAO will receive an email response from the Buy-In Mailbox within 2-3 business days.

4. Â Â Â Â At the same time the email is sent, but no later than 30 days following the date the hit is created, inform the individual that there may be a delay in Buy-In enrollment using a PA 1877 Delay in Buy-In Enrollment form. (See Appendix C, Buy-In Forms .)

5. Â Â Â Â If the discrepancy is not resolved by the 35 th day, the CAO will be advised to contact SSA via fax using a PA 1882 Referral to SSA Due to Buy-In Discrepancy form. (See Appendix C, Buy-In Forms .)

Reminder: The CAO must act (review and adjust benefits as needed, narrate and clear the hit) on new or changed information within 45 calendar days of the system posting the information to Exchange 7. The CAO will utilize the Workload Dashboard to track the number of days a disposition has been pending to ensure prompt resolution. Â

Updated August 31, 2018, Replacing January 3, 2018
