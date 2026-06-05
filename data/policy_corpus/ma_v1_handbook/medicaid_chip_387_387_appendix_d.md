---
program: Medicaid/CHIP
source_type: official_handbook
title: 387 Appendix D
chapter: 387
source_url: http://services.dpw.state.pa.us/oimpolicymanuals/ma/387_SSI/387_Appendix_D.htm
accessed_date: 2026-04-19
jurisdiction: Pennsylvania
---

# 387 Appendix D

Whenever a State Data Exchange (SDX) file comes in from SSA , it is matched against e CIS by Social Security number , name, and date of birth. The SDX file has information on new SSI cases and on changes to current SSI records.

If the individual is not known to e CIS or is inactive, then the process assumes that this is a new SSI recipient and opens a new case in the SDX county of residence in the correct SSI category . The case is given a new record number and individual number. The system uses the SDX individual name for the case and budget payment name . Defaults are provided by county/district for caseload, worker, unit, civil subdivision, and school district.

Â Â Â Â Â Â NOTE: Â If the individual is known to e CIS but is inactive, the old individual number is used. CAOs can access the TSCR Schedule Cross Reference Table for default values. CAOs must distribute new cases to correct caseloads. The CAO will reassign records to workers to equal their caseload and also to assign the records to the correct unit, i.e. LTC , SSI, etc.

If the individual is found on the Application Processing (AP) database and the application is registered (an individual number is assigned), the case is opened using the AP county code, no matter whether there is an AP/SDX county mismatch. The system uses the AP case record number, if one is available, or assigns a new record number in the AP county.

Â Â Â Â Â Â NOTE: Â The AP case record number could be different from the record number of the closed case. If the individual is found in AP and the application is not registered, the system uses the SDX federal county code to open the case with a new record number.

If the individual is currently active in e CIS, the system uses existing information for a budget opening. This includes existing record number, caseload, worker ID, and unit. New elements will be populated to the individual's case records. (For example, an ETP code of 22 is set if the SSI individual is age 60 or older.)

## Effective Date of Medicaid Eligibility on CIS

In all cases of automated openings, the open effective date for category A, J, or M is theÂ Medicaid Â Eligibility Begin date on the MA/FS tab of the â8036 Pendâ SDX file (Exchange 6 ). If a currently active budget is closed because of an automated SSI opening, the closing date is the day before the next payment day that can be met. WheneverÂ SNAP or multiple individuals on a single MA budget group Â is involved in the case, the automated process creates anÂ alert .

## SSI Medicaid Openings

The process uses the following rules to handle SSI openings:

- The individual is active in a one-individual MA case.

Action: The system closes the budget and opens an SSI budget.

- The individual is open with other household members in the same MA budget .

Action: The system processes an individual delete and opens an SSI Â budget. e CIS SSI Alert 118 is set. Alert SSI 119 is set when there is a related SNAP budget.

- The individual is active for SNAP only.

Action: The system opens an SSI MA budget. e CIS SSI Alert 119 is set for the SNAP budget (unless the individual is open in extended SNAP (FS 43) ) . If the individual is open in FS 43, the system does not generate an alert for the SNAP.

When the process has trouble identifying the individual, it uses the following rules:

- There is a match on the Social Security Number, but the date of birth and the name do not match.

Action: The SSI MA case is not auto opened in e CIS. Exchange 6 disposition reason code 10 is set.

- There is a match on the Social Security Number and the name, but the SDX date of birth differs from the eCIS date of birth and the case status is active.

Action: The SSI MA case is not auto opened in eCIS. Exchange 6 disposition reason code 10 is set.

- There is a match on the Social Security Number and the date of birth, but there is no match on the name and the case status is active.

NOTE: In the above three cases, the discrepancy in the date of birth indicated on the SDX file and eCIS must be by 15 or more days.

In these situations, the CAO must determine whether the individual is currently active in e CIS and open the SSI MA budget manually.

In the following situations where cash and multiple MA budgets are included in the case, the SSI MA budget must not be auto opened :

- If a C ,D or U budget is included in the case

- If the case contains multiple cash and MA budgets.

Action: An SSI MA budget is not opened. eCIS alert SSI 115 is set.

- A multiple-individual MA case has a future delete action set for processing.

Action: An SSI budget is not opened. e CIS alert SS I 141 is set.

The CAO must open the SSI MA budget manually when there is cash assistance and multiple MA budget activity in these cases or when a future delete action is pending.

## Automated SSI Closing Process

Daily, weekly, and monthly , the SDX â8036 Pendâ file sent by SSA is matched against e CIS by Social Security number, name, and date of birth. SSI records on which the SDX payment status code equals T 0 I (termination due to death) or the Medicaid Eligibility Code is set to âD- Disabled Adult Childâ are looked at for possible processing. If the process closes the SSI case, the closing date for the A, J, and M budget is the day before the next payment day that can be met. The system must process the case or budget closing for the following:

- One-person SSI cases

- One-person SSI budgets

NOTE: SNAP is not closed if there are two or more individuals in the SNAP budget. e CIS alert SSI 122 is set.

- A case with m ultiple A, J, or M budgets or a case which includes A, J, or M budget(s) and other MA budgets.

Action: e CIS alert SSI 147 is set. If applicable, CAOs must review the case and update the payment name orÂ head of household for the case record .

The automated closing process does not close SSI cases that meet the following conditions:

- There is no exact match on the Social Security number, name (excluding the âMrs.,â Ms.,â or âMr.â title and the middle initial), and date of birth.

Action: The individual is not included in the file for closing. The CAO must follow existing Exchange 6 hit disposition reason code processes , such as RC01 and RC04, for closing the SSI MA budget in e CIS.

- There is a match on the Social Security number, name, and date of birth, but the e CIS category is not A, J, or M.

Action: The system does not close the case or SSI MA budget. e CIS alert SSI 121 is set.

- There is a match on the Social Security number, name, and date of birth and the category equals A, J, or M, but there is a related cash budget.

Action: The system does not close the case or SSI MA budget. e CIS alert 120 SSI is set.

## Description of Alerts

The following alerts are used in the Automated SSI process. Alerts must be created and made available for review the day the case is processed. CAOs can look at the WLD Alert Types Reference Table (R00417) under CAO Utilities in the eCIS Standalone Module for more information.

- Exchange 6 hit Disposition Reason Code 10 âNotifies the case worker that there is a demographic mismatch and the SSI MA budget must be opened manually. The worker must determine whether the SSI individual is currently active in e CIS.

- Alert SSI 115â Notifies the case worker that there is cash assistance activity or multiple MA budgets in the case and the SSI MA budget must be opened manually. The alert is cleared by the worker after the SSI budget is opened. The alert remains in completed status and will be purged from the system after 365 days.

- Alert SSI 116â Instructs the case worker to compare SDX demographic information with e CIS and enter correct e CIS codes in the appropriate data fields, if applicable . The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 365 days.

- Alert SSI 117â Notifies the case worker of a Personal Care or Domiciliary Care case (facility code 75 or 76). The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 365 days.

- Alert SSI 118â Instructs the case worker to check who is in the household, as SSI was opened in a multiple-individual single MA budget . The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 125 days .

- Alert SSI 119â Instructs the case worker to review and adjust SSI income to the SNAP budget and run case eligibility . SSI is opened automatically. The alert is cleared by the worker after case eligibility is run. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 120â Instructs the case worker to stop individual benefits because the individual is no longer receiving SSI (because of the death of the SSI individual) and make other appropriate case benefit changes. The case includes multiple cash, MA , or other A, J, or M budgets. The alert is cleared by the system after eligibility is run in e CIS. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 121â Instructs the case worker to stop the individualâs SSI MA benefits and make any income adjustments to the SNAP budget . The SDX file shows the individual is no longer receiving SSI (because of the death of an individual ) , but the category is not A, J, or M. The alert is cleared by the system after eligibility is run in e CIS. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 122â Instructs the case worker to check who is in the household , make any income adjustments to the SNAP budget, and run eligibility . SSI is closed automatically. The alert is cleared by the worker after eligibility is run. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 130â Lets the case worker know that the SSI individual is aÂ refugee Â and to review the nonfinancial citizenship screen and data fields for any require d updates. The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 136â Informs the case worker that the SSI individual was aÂ GA Â individual sharing aÂ family size allowance (FSA) Â with another GA budget and that the FSA should be checked . The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 141â Instructs the case worker to open the SSI MA budget for an individual with a future delete action pending on the MA . The alert is cleared by the system after the individual is opened for SSI. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 146â Instructs the case worker to reviewÂ third-party liability (TPL) Â information and update the TPL.Â The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 125 days.

- Alert SSI 147â Instructs the case worker to review who is in the household and who is the payment name and make any applicable updates . The SSI MA budget is closed automatically. The alert is cleared by the worker. The alert remains in completed status and will be purged from the system after 125 days

## Notices

The Automated SSI process will create the following notices when it takes action on a case.

NOTE: Â No stop notice is created if an MA case or budget is closed and SSI is opened for one individual.

- For all automated openings, the system generates an Automated Notice of Eligibility (162M). The notice code and option are not set. The notice indicator is set to N. This notice is created with a copying process and does not run through the notice module.

- For an SSI closing due to death, the system creates an Automated Stop Notice (162C). The notice code is set to 490 Option 1. A separate notice using the same code and option is sent if the SNAP budget is closed by the process.

## Reporting

The Openings/Closings by Category/Reason Code-Monthly Report (ARM240) found in Docushare under the Mainframe Reports folder, includes the number of SSI budgets that are opened/closed on a monthly basis and by reason code. There is a statewide and a CAO specific report. The following data is included on the report:

- County and District Code

- SSI category

- SSI opening or closing reason code

- Subtotals for the SSI budgets that are opened and closed

CAOs can use the report to review trends from month to month and to identify and study problems.

Updated May 14, 2024, Replacing February 14, 2012
