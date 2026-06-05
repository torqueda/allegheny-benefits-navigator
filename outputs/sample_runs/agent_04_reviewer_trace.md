# Reviewer Trace

- Trace ID: `027e2ffd-b407-4ea3-9088-ca76743d0efb`
- Case ID: `AGENT_04`
- LLM mode: `offline_or_rule_only_fallback`

## Raw Input
```json
{
  "user_description": "I live in Pittsburgh with my daughter. We got a shutoff notice but I did not say how much income we have yet.\n\nFollow-up: I am not working right now. We get about $950 a month from unemployment and child support combined."
}
```

## Intake Object
```json
{
  "normalized_profile": {
    "user_description": "I live in Pittsburgh with my daughter. We got a shutoff notice but I did not say how much income we have yet.\n\nFollow-up: I am not working right now. We get about $950 a month from unemployment and child support combined.",
    "county": "Allegheny",
    "zip_code": null,
    "num_adults": 1,
    "num_children": 1,
    "child_under_5": null,
    "pregnant_household_member": null,
    "elderly_or_disabled_member": null,
    "employment_status": null,
    "monthly_earned_income": null,
    "monthly_unearned_income": null,
    "household_income_total": 950.0,
    "housing_cost": null,
    "utility_burden": "high",
    "heating_assistance_need": true,
    "insurance_status": null,
    "recent_job_loss": null,
    "food_insecurity_signal": null,
    "language_or_stress_notes": null
  },
  "missing_fields": [],
  "contradictory_fields": [],
  "extracted_signals": [
    "free_text_description_received",
    "energy_need_detected"
  ],
  "intake_status": "complete",
  "geography_status": "in_scope_geography",
  "validation_reasons": [
    "Core screening fields are complete enough to continue."
  ],
  "intake_summary": "User described the household as: I live in Pittsburgh with my daughter. We got a shutoff notice but I did not say how much income we have yet.\n\nFollow-up: I am not working right now. We get about $950 a month from unemployment and child support combined. Household: 1 adult(s), 1 child(ren) in Allegheny. Reported household income: $950 per month. Utility or heating strain is present in the intake.",
  "clarification_questions": []
}
```

## Retrieved Chunks
```json
[
  {
    "program_name": "LIHEAP",
    "document_id": "liheap_678_3_678_3_acceptable_forms_of_verification",
    "title": "678.3 Acceptable Forms of Verification",
    "section_title": "678.3 Acceptable Forms of Verification",
    "score": 14.132,
    "text": "The CAO has the discretion to use all available resources to establish verification of required information. - SSN's are verified through e-CIS directly with the Social Security Administration - Household members who do not provide a SSN must sign an Energy Assistance Affidavit ( HS EA-4 ) , or complete question #2 of the Certification section on the LIHEAP application ( HSEA-1) - Earned/Unearned Income- - Pay stubs, benefit award letters or photocopies of these documents - A letter from a person paying voluntary support that includes the person's address and telephone number, the amount of support paid and how often it is paid. - Automated sources such as CIS , e-CIS and exchanges 1,2,3, and 6 of the Income Eligibility Verification System (IEVS) . - Deliverable-fuel bills from January of the previous heating season and forward, utility bills dated two months or less from the date of application to verify heating responsibility, or a landlord statement (HSEA-36) to verify heat is included in the rent. NOTE : In certain situations, such as the death of a spouse or credit problems, the heating bill may be in the name of someone other than the applicant. The applicant must give written proof of address other than the heating bill and explain why the bill is in another person's name. If the landlordâs name is on the heating bill, the applicant must show the lease or a statement from the landlord saying that the applicant is responsible for paying heating costs directly to the fuel supplier. - A utility termination notice showing that service has been shut off or will be shut off within 60 days or a statement from the applicant that his or her deliverable fuel supply will run out within 15 days."
  },
  {
    "program_name": "LIHEAP",
    "document_id": "liheap_677_677_appendix_a",
    "title": "677 Appendix A",
    "section_title": "677 Appendix A",
    "score": 12.204,
    "text": "Application entered in error. - No notice generated for this rejection reason. Duplicate application rejection. All household members are ineligible aliens . LIHEAP State Plan, Appendix B § 601.31(4); § 601.109; 42 U.S.C. § 8624 ( c ); 8 U.S.C § 1611 Your household can only get one LIHEAP Cash payment for each program year. 55 Pa. Code § 601.43 All household members already received a LIHEAP Crisis benefit as part of another LIHEAP household. 55 Pa. Code § 601.63 The total amount of the Cash and Crisis payment will not take care of your heating emergency. 55 Pa. Code § 601.32(3); § 601.61; § 601.32(2) The Crisis amount needed is less than $25 LIHEAP State Plan, Appendix B § 601.63 Household does not meet the definition of Crisis LIHEAP State Plan, Appendix B § 601.32, 601.62(2) Your household did not send a signed application. 55 Pa. Code § 601.21; § 601.23 Your household is not responsible for paying the heating costs. 55 Pa. Code § 601.31(2) Your household income is more than the program limit. 55 Pa. Code § 601.31(1) You did not send the income information we asked for. 55 Pa. Code § 601.81; § 601.82; § 601.83; § 601.102 Your household's rent payment is based on a percentage of household income and includes heating costs. 55 Pa. Code § 601.31(2)(b) You did not send proof that you live in Pennsylvania. 55 Pa. Code § 601.31(3) We got your application after the program was closed. You did not send proof that you are a legal alien or refugee . LIHEAP State Plan, Appendix B § 601.31(4); § 601.109; 42 U.S.C. § 8624 (c) Amount of Crisis payment will not resolve heating emergency"
  },
  {
    "program_name": "LIHEAP",
    "document_id": "liheap_677_2_677_2_eligible_notice",
    "title": "677.2 Eligible Notice",
    "section_title": "677.2 Eligible Notice",
    "score": 12.198,
    "text": "When DHS approves an application, it must send the applicant a notice with the following information: 55 PA. Code § 601.22 LIHEAP State Plan § 601.22 - The amount of the benefit. - The householdâs reported income. - The yearly amount of reported income compared with the LIHEAP income limit based on household size. - A detailed explanation of the right to an appeal , how to ask for a hearing, how to prepare for a hearing and what happens at a hearing, and a fair hearing request form. Eligible notices for the cash program include the following text: - For benefits payable to utilities and deliverable fuel companies: âYou qualify for LIHEAP Cash Benefit: $______ will be sent to [vendor name]. This is a one-time only payment for the [program year] heating season.â - For benefits payable directly to LIHEAP applicants: âYou qualify for LIHEAP Cash Benefit: $______ will be sent to YOU. This is a one-time only payment for the [program year] heating season.â Eligible notices for the crisis program have the following text: âYou qualify for 20 xx -20 xx C risis energy assistance. On [ mm/dd/yy ] we approved $_____ to resolve your crisis. Your energy provider is [ name of utility or deliverable company ] for this benefit.â âYou qualify for 20 xx -20 xx Crisis energy assistance. On [ mm/dd/yy ] we approved $_____ to resolve your crisis. The payment for this benefit was sent to YOU. Please be aware that this money is to help you with your home heating cost and should be used to pay your heating bills.â Approval notices are generated on the weekend after the LIHEAP system processes the payments."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_312_1_312_1_general_policy",
    "title": "312.1 General Policy",
    "section_title": "312.12 Pregnant Women and Children under Age One",
    "score": 15.149,
    "text": "A pregnant woman or a qualified child up to age 1 can get MAGI-related MA if household income is equal to or less than 215 percent of the Federal Poverty Income Guideline (FPIG ) for the household size (See Appendix A ) . The pregnant woman, once approved, continues to be eligible for MA coverage through the end of the 12 th month when the12-month postpartum period ends, regardless of her income or a change in circumstances . ( See Chapter 338.42 ) The newborn whose mother was getting MA or CHIP at the time of birth can get MA coverage up to age one, regardless of the parentsâ income, per the Children's Health Insurance Program Reauthorization Act of 2009 (CHIPRA). Children under one who were not born to a mother on MA or CHIP at the time of birth are eligible for a 12-month continuous eligibility period (See Section 312.131 ). NOTE: If the CAO did not know about the pregnancy and learns that MA or SSI benefits were closed during the pregnancy, it must approve MA coverage from the date of the closing through the last day of the month in which the 12-month postpartum period ends. Newborns and pregnant/postpartum individuals can only be closed during their periods of continuous eligibility for the following reasons: - Permanent Move Out of State - If the CAO determines that the opening of benefits was incorrect due to fraud or abuse or agency error. When a provider or other outside source asks for MA benefits for a child under age one, the CAO must review the familyâs case record to see if MA , SSI, or CHIP benefits were open for the mother at any time during the pregnancy. If so, the CAO must authorize MA benefits for the child from the date of birth until the first birthday."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_338_2_338_2_third_party_resources",
    "title": "338.2 Third-Party Resources",
    "section_title": "338.225 Failure to Cooperate with HIPP",
    "score": 10.199,
    "text": "338.231 MEC and Children aged 6-18 Children aged 6-18 with household income between 100 and 133 percent of the Federal Poverty Limit (FPL) and who meet all other eligibility factors will also use an indication of MEC to determine category of eligibility under Modified Adjusted Gross Income (MAGI-related MA). Additionally, any child aged 18 and under with an indication of MEC is not eligible to be reviewed for the Childrenâs Health Insurance Program (CHIP). A âMinimal Essential Coverage?â check box on the Individual Attributes screen must be completed when health insurance is indicated for the child. Category placement will be determined in the following way: - If the âMinimal Essential Coverage?â box is checked, children age 6-18 with household income between 100 and 133 percent FPL will be opened in the MG 00 category. - If the box âMinimal Essential Coverage?â box is not checked, children age 6-18 with household income between 100 and 133 percent FPL will be opened in the MG 19 category. NOTE: MG 00 will continue to be assigned to children age 6-18 with household income at or below 100 percent FPL regardless of health insurance. County Assistance Office (CAO) Action Health insurance may be reported and available to the CAO on applications, renewals, through client reported changes, or Third-Party Liability (TPL) screens in the case record, etc. If the reported health insurance is considered MEC, the CAO will check the âMinimal Essential Coverage?â box on the Individual Attributes screen when information is available that shows a child, age 18 and under, has MEC health insurance."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_315_5_315_5_determining_eligibility",
    "title": "315.5 Determining Eligibility",
    "section_title": "315.5 Determining Eligibility",
    "score": 10.161,
    "text": "Reminder: The child should not be referred to SSA to apply for SSI benefits (unless the family wants to apply for SSI benefits) in the PH 95 category since it is assumed by the childâs eligibility in that category that the child does not qualify for SSI. If the child qualifies for any other MA category (based on income eligibility), an SSA DAP referral should be initiated to encourage the pursuit of Federal benefits and the disability determination since it is beneficial to the child. The CAO should not use SSAâs parental deeming or Federal Benefit Rate charts to determine which type of DAP referral to make. NOTE: The issuance of the PA Access card is authorized upon the completed transaction of the MA authorization. The CAO will ensure that the authorization and data entry process is completed timely to meet the medical needs of the eligible child. See Chapter 380, Issuing the ACCESS Card . - Deny eligibility for the Children with Special Needs Category i f the total net countable income of the child exceeds 100 percent of the FPIG. Generate a notice of ineligibility per Chapter 377, Notices . If the CAO determines the child is not eligible for any MA category, including the Children with Special Needs category due to financial reasons or because the child is determined not to be disabled, then the child will be reviewed for the Childrenâs Health Insurance Program (CHIP) . NOTE: If the child is within their 12-month certification period, the child will be transitioned to MG 18 target type âCâ until their next renewal . If the child is not eligible for the Children with Special Needs category because their family did not provide the pending medical documentation for the MRT review process (including if it was needed to provide presumptive eligibility), the CAO will update the Disability screen as follows in order to capture the reported disability:"
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_550_550_appendix_a",
    "title": "550_Appendix A",
    "section_title": "550_Appendix A",
    "score": 11.141,
    "text": "The Support Pass-Through (SPT) system compiles monthly support collection information and issues SPT checks to appropriate Temporary Assistance for Needy Families (TANF) recipients through the electronic Client Information System ( e CIS). After the initial month of TANF eligibility, an SPT check, not to exceed $50, is issued by e CIS based on the amount of support collected in the current support month and the percentage of that support payment that is determined to be the stateâs share. The stateâs share is calculated each September using a formula based on the stateâs Medical Assistance matching rates. Effective October 1, 2008, the SPT check is paid based on current support collections and increases for TANF families, up to $100 for a family with one child or up to $200 for a family with two or more children. The federal share is no longer deducted from current support to determine the SPT amount. eCIS determines whether the SPT payment is to be treated as income or a resource for Supplemental Nutrition Assistance Program (SNAP) purposes and generates two alerts to help County Assistance Office ( CAO) workers: - If the SPT is income and is a different amount than was received in the previous calendar month, alert 37 is set. - If the SPT is a resource and for the calendar month is greater than $99, alert 36 is set. Workers will review their alerts and take appropriate action to assure the household receives the proper SNAP allotments. Reminder: Workers should check the Pennsylvania Child Support Enforcement System (PACSES) for child support or alimony, even if listed as voluntary on the application."
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_568_7_568_7_deletion_of_a_household_member",
    "title": "568.7 Deletion of a Household Member",
    "section_title": "568.7 Deletion of a Household Member",
    "score": 10.176,
    "text": "To remove a household member, the CAO must determine the eligibility of the remaining household members prospectively. When deleting a member of a household, the CAO must prospectively determine the household's eligibility and benefit amount without the member or the member's income and expenses for the next month that the deadline can be met. If the deletion results in a decrease or termination of benefits, the CAO must: - Send an Advance Notice of Adverse Action advising the household of the action; and - Decrease or terminate benefits for the first month following the expiration of the Advance Notice of Adverse Action. NOTE: For Extended SNAP households, if the deletion of the household member causes a decrease in SNAP benefits, the CAO must not decrease benefits. If the deletion results in a benefit increase , the CAO must: - Send a Confirming Notice explaining the change; and - Remove the household member for the month after the month the household reported the change. If the deadline cannot be met, the CAO must authorize a supplemental benefit using reason code 157. Example: Mr. and Mrs. Wilson and their three children receive SNAP benefits. The FPIG limit for a family of five is $2,295. Mr. and Mrs. Wilson are both working part-time. Mr. Wilson moves out of the household. Mrs. Wilson does not report this change. To determine the householdâs gross monthly income, Mrs. Wilson totals the remaining household membersâ income and compares this with the $2,295 FPIG limit. Since Mr. Wilson left the household, Mrs. Wilson is not required to determine his monthly income for the 130% comparison. The SNAP benefit and the 130% FPIG limit remain the same until Mrs. Wilson reports the change at the six-month review or renewal , whichever comes first. If Mr. Wilson applies for SNAP for himself, he must be removed from Mrs. Wilsonâs SNAP benefits, as no duplication of SNAP benefits can occur."
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_510_2_510_2_household_members",
    "title": "510.2 Household Members",
    "section_title": "510.22 Mandatory Household Members",
    "score": 10.141,
    "text": "NOTE: Ineligible students, ineligible household members, and persons who are disqualified because they did not comply with work requirements are not included as mandatory household members. - Spouses (including common-law) must always be included in the same household. Exception: When a spouse is not living at home due to active military service, the individual would not be considered part of the SNAP household but their income may still be counted when determining the household's SNAP benefit amount. See Section 550.535 to determine how the income should be counted. NOTE: A common-law marriage is legally recognized only if it existed before January 1, 2005. In a common-law marriage, the individuals are legally free to marry, are known to the community as spouses , and state that they both agree to live together as a married couple . A person claiming to be a common-law spouse must show proof that the couple was presenting itself to the community as a married couple before January 1, 2005. Acceptable proof includes the deed to their residence, leases, income tax records, bank records, utility bills, or statements from knowledgeable persons. If the record shows that the recipients have been presenting themselves as married under common law since before January 1, 2005, the marriage is legally recognized and can be dissolved only through the legal process. - Parents and a child (natural, adopted, or stepchild), age 21 or younger, and a child's own child or spouse are included in the same household unless one parent is elderly and disabled. (See Section 510.21 and Section 510.41 .) - Shared custody situations require the child or children to be included in the applicant household regardless of where the child or children eat the majority of meals in any given month."
  }
]
```

## Program Scores
```json
[
  {
    "program_name": "LIHEAP",
    "status": "strong_match",
    "decision_state": "likely_eligible",
    "match_score": 9.5,
    "priority_score": 16.5,
    "rule_match_score": 9.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "LLM cross-check was unavailable or skipped, so deterministic screening produced the final result.",
    "suppression_reason": null,
    "priority_boost_reason": null
  },
  {
    "program_name": "Medicaid/CHIP",
    "status": "possible_match",
    "decision_state": "possibly_eligible",
    "match_score": 4.5,
    "priority_score": 4.5,
    "rule_match_score": 4.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "LLM cross-check was unavailable or skipped, so deterministic screening produced the final result.",
    "suppression_reason": null,
    "priority_boost_reason": null
  },
  {
    "program_name": "SNAP",
    "status": "possible_match",
    "decision_state": "possibly_eligible",
    "match_score": 3.5,
    "priority_score": 3.5,
    "rule_match_score": 3.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "LLM cross-check was unavailable or skipped, so deterministic screening produced the final result.",
    "suppression_reason": null,
    "priority_boost_reason": null
  }
]
```

## Final Decision
```json
{
  "intake_status": "complete",
  "geography_status": "in_scope_geography",
  "decision_status": "ambiguous",
  "final_status": "delivered_with_uncertainty"
}
```

## Final Explanation
This upgraded navigator turns the household description into structured intake fields, then ranks programs using retrieved local policy evidence. Based on the intake handoff and the retrieved policy chunks, the strongest current matches are LIHEAP, Medicaid/CHIP, SNAP. For LIHEAP, the main reason is: A direct heating-assistance need strongly supports LIHEAP review. Retrieved evidence for LIHEAP highlights the section '678.3 Acceptable Forms of Verification': The CAO has the discretion to use all available resources to establish verification of required information. - SSN's are verified through e-CIS directly with the Social Security Administration - Household members who do not provide a SSN must sign an Energy Assistance Affidavit ( HS EA-4 ) , or complete question #2 of the Certification section on the LIHEAP application ( HSEA-1) - Earned/Unearned Income- - Pay stubs, benefit award letters or photocopies of these documents - A letter from a person paying voluntary support that includes the person's address and telephone number, the amount of support paid and how often it is paid. - Automated sources such as CIS , e-CIS and exchanges 1,2,3, and 6 of the Income Eligibility Verification System (IEVS) . - Deliverable-fuel bills from January of the previous heating season and forward, utility bills dated two months or less from the date of application to verify heating responsibility, or a landlord statement (HSEA-36) to verify heat is included in the rent. NOTE : In certain situations, such as the death of a spouse or credit problems, the heating bill may be in the name of someone other than the applicant. The applicant must give written proof of address other than the heating bill and explain why the bill is in another person's name. If the landlordâs name is on the heating bill, the applicant must show the lease or a statement from the landlord saying that the applicant is responsible for paying heating costs directly to the fuel supplier. - A utility termination notice showing that service has been shut off or will be shut off within 60 days or a statement from the applicant that his or her deliverable fuel supply will run out within 15 days. For Medicaid/CHIP, the main reason is: Children increase the relevance of Medicaid or CHIP review. Retrieved evidence for Medicaid/CHIP highlights the section '312.12 Pregnant Women and Children under Age One': A pregnant woman or a qualified child up to age 1 can get MAGI-related MA if household income is equal to or less than 215 percent of the Federal Poverty Income Guideline (FPIG ) for the household size (See Appendix A ) . The pregnant woman, once approved, continues to be eligible for MA coverage through the end of the 12 th month when the12-month postpartum period ends, regardless of her income or a change in circumstances . ( See Chapter 338.42 ) The newborn whose mother was getting MA or CHIP at the time of birth can get MA coverage up to age one, regardless of the parentsâ income, per the Children's Health Insurance Program Reauthorization Act of 2009 (CHIPRA). Children under one who were not born to a mother on MA or CHIP at the time of birth are eligible for a 12-month continuous eligibility period (See Section 312.131 ). NOTE: If the CAO did not know about the pregnancy and learns that MA or SSI benefits were closed during the pregnancy, it must approve MA coverage from the date of the closing through the last day of the month in which the 12-month postpartum period ends. Newborns and pregnant/postpartum individuals can only be closed during their periods of continuous eligibility for the following reasons: - Permanent Move Out of State - If the CAO determines that the opening of benefits was incorrect due to fraud or abuse or agency error. When a provider or other outside source asks for MA benefits for a child under age one, the CAO must review the familyâs case record to see if MA , SSI, or CHIP benefits were open for the mother at any time during the pregnancy. If so, the CAO must authorize MA benefits for the child from the date of birth until the first birthday. For SNAP, the main reason is: Households with children may benefit from early SNAP review. Retrieved evidence for SNAP highlights the section '550_Appendix A': The Support Pass-Through (SPT) system compiles monthly support collection information and issues SPT checks to appropriate Temporary Assistance for Needy Families (TANF) recipients through the electronic Client Information System ( e CIS). After the initial month of TANF eligibility, an SPT check, not to exceed $50, is issued by e CIS based on the amount of support collected in the current support month and the percentage of that support payment that is determined to be the stateâs share. The stateâs share is calculated each September using a formula based on the stateâs Medical Assistance matching rates. Effective October 1, 2008, the SPT check is paid based on current support collections and increases for TANF families, up to $100 for a family with one child or up to $200 for a family with two or more children. The federal share is no longer deducted from current support to determine the SPT amount. eCIS determines whether the SPT payment is to be treated as income or a resource for Supplemental Nutrition Assistance Program (SNAP) purposes and generates two alerts to help County Assistance Office ( CAO) workers: - If the SPT is income and is a different amount than was received in the previous calendar month, alert 37 is set. - If the SPT is a resource and for the calendar month is greater than $99, alert 36 is set. Workers will review their alerts and take appropriate action to assure the household receives the proper SNAP allotments. Reminder: Workers should check the Pennsylvania Child Support Enforcement System (PACSES) for child support or alimony, even if listed as voluntary on the application. Treat this as a guided prescreen and next-step summary, not a final eligibility decision.

## Caveats
- This is prescreening only.
- This is not an official determination.
- Heating-cost details and seasonal program rules may affect the result.
- Some applicants may need extra documentation depending on rent and citizenship details.
- Pregnancy, age bands, and current coverage details can change the result.
- Household-composition details may affect Medicaid or CHIP pathways.
- SNAP prescreening can change if income details are incomplete or inconsistent.
- Work-related or exemption rules may require follow-up.
