---
program: Medicaid/CHIP
source_type: official_handbook
title: 388 Appendix A
chapter: 388
source_url: http://services.dpw.state.pa.us/oimpolicymanuals/ma/388_Buy-In/388_Appendix_A.htm
accessed_date: 2026-04-19
jurisdiction: Pennsylvania
---

# 388 Appendix A

Transaction code s are used by DHS and Â the Centers for Medicare and Medicaid Services (CMS) to communicate Buy-In actions ( accrete, delete ) , change Buy-In records , or report errors concerning Buy-In individuals.

DHS sends a two-digit transaction code to tell CMS what action the CAO wants taken. The most common DHS transaction codes are:

- Â Â Â Â Â Â 61 â Accrete (Start Buy-In)

- Â Â Â Â Â Â Â Â Â 51 â Delete (Stop Buy-In)

- Â Â Â Â Â Â Â Â 53 â Delete (Death of Recipient)

Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: These codes can be automated or manual.

The following transaction codes are sent together to begin and end an NCE period of eligibility:

- Â Â Â 75 â Begin NCE period for Buy-In

- Â Â 76 â End NCE period for Buy-In

Â Â Â Â Â Â

Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: These are strictly manual transaction codes.

CMS sends either a two-digit or a four-digit code to show what action they have taken, and to alert DHS to changes in an individualâs record. The most common CMS transaction codes are:

- 1161 â CMS has authorized Buy-In

- 1167/1180 â SSA requested Buy-In enrollment for an SSI recipient and CMS approved

- 16 â CMS has closed Buy-In due to death of the recipient

Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: The closing date will be the month/year of the date of death.

- Â Â Â Â 1728 â CMS transferred the Buy-In record to another state because the recipientâs state of residence has changed

- Â Â Â 1751 â CMS has closed Buy-In

- Â Â 2161/2163 â CMS has rejected an accretion request due to demographic mismatch

Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: A rejection code may be further defined by a sub-code, which provides information as to the specific reason for rejection. See Sub-Codes below for more information.

- 41 â Ongoing Buy-In (no issues)

- 4375 â NCE period of eligibility (simultaneous accrete/delete) has been added to CMS file

See Using IEVS, Chapter 10, Exchange 7, Glossary for additional transaction codes and their descriptions .

Sub-Codes

The following sub-codes provide further information as to the specific reason for rejection:

- Â Â Â Â Â Â Â Â Â A â Claim number could not be matched.

- Â Â Â Â Â Â Â Â Â B â Claim number matched but the individualâs demographics did not match.

- Â Â Â Â Â Â Â Â Â C â Claim number matches but SSA does not show Medicare Part A entitlement.

Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: An individual must have Part A entitlement for Buy-In eligibility.

- Â Â Â Â Â Â D â Claim number matches but the individual is a QDWI Â . DHS is requesting Part B Buy-In but DHS only pays Part A premium for a QDWI.

Â Â Â Â Â Â Â Â Â Â Â Â Â NOTE: DHS can only request Part A Buy-In for a QDWI. See Section 388.2, Buy-In of Medicare Part A. Â

- Â Â Â Â Â Â Â Â E â CMS does not show Medicare entitlement for the period requested. If the individual appears eligible for Medicare, contact the local SSA office.

Discrepancy Codes

Discrepancy codes are part of an internal, DHS controlled function within the Buy-In system that compares data from CMS, Exchange 3 (BENDEX), Exchange 6 (SDX) and eCIS.

Most of the codes indicate there is a discrepancy in the data contained in one or more of these systems. Some merely provide information indicating that there is a change, such as a claim account number change. Others, such as discrepancy code 99, mean nothing is wrong and the client is an ongoing Buy-In recipient.

The most common discrepancy codes are:

- Â Â Â Â Â Â Â Â Â 05 â Open in Buy-In but closed in eCIS and not in CP status on SDX.

- Â Â Â Â Â Â Â Â Â 06 â Open in Buy-In but closed in eCIS and in Current Pay (CP) status on SDX.

- Â Â Â Â Â Â Â Â Â 10 â Open in Buy-In but non-Buy-In category open in eCIS and in CP status on SDX.

- Â Â Â Â Â Â Â Â Â 11 â Open in Buy-In but non-Buy-In category open in eCIS and not in CP status on SDX.

- Â Â Â Â Â Â Â Â Â 30 â Individual reported as deceased in Buy-In and case is open in eCIS.

- Â Â Â Â Â Â Â Â Â 35 â Buy-In reports individual moved out of state but case is open in eCIS.

- Â Â Â Â Â Â Â Â Â 95 â Buy-In demographic mismatch.

- Â Â Â Â Â Â Â Â Â 99 â Valid ongoing Buy-In case.

When a discrepancy codes appears on Exchange 7, the CAO will review the corresponding âAction Requiredâ information and take appropriate action to correct the discrepancy.

Updated August 31, 2018, Replacing February 14, 2012
