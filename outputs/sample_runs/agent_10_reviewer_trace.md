# Reviewer Trace

- Trace ID: `20d71705-c095-4aee-92fe-a8de875b4a80`
- Case ID: `AGENT_10`
- LLM mode: `offline_or_rule_only_fallback`

## Raw Input
```json
{
  "user_description": "I live in Philadelphia with my daughter. I have no insurance, my income is about $900 a month, and I am behind on my gas bill."
}
```

## Intake Object
```json
{
  "normalized_profile": {
    "user_description": "I live in Philadelphia with my daughter. I have no insurance, my income is about $900 a month, and I am behind on my gas bill.",
    "county": "Philadelphia",
    "zip_code": null,
    "num_adults": 1,
    "num_children": 1,
    "child_under_5": null,
    "pregnant_household_member": null,
    "elderly_or_disabled_member": null,
    "employment_status": null,
    "monthly_earned_income": null,
    "monthly_unearned_income": null,
    "household_income_total": 900.0,
    "housing_cost": null,
    "utility_burden": "high",
    "heating_assistance_need": true,
    "insurance_status": "uninsured",
    "recent_job_loss": null,
    "food_insecurity_signal": null,
    "language_or_stress_notes": null
  },
  "missing_fields": [],
  "contradictory_fields": [],
  "extracted_signals": [
    "free_text_description_received",
    "energy_need_detected",
    "coverage_need_detected",
    "out_of_scope_geography_detected"
  ],
  "intake_status": "insufficient_data",
  "geography_status": "out_of_scope_geography",
  "validation_reasons": [
    "Household appears to be outside Allegheny County."
  ],
  "intake_summary": "User described the household as: I live in Philadelphia with my daughter. I have no insurance, my income is about $900 a month, and I am behind on my gas bill. Household: 1 adult(s), 1 child(ren) in Philadelphia. Reported household income: $900 per month. Utility or heating strain is present in the intake. Insurance status is reported as uninsured. The household appears to be outside the Allegheny County scope supported by this prototype.",
  "clarification_questions": [
    "This prescreen is limited to Allegheny County. If the household is outside Allegheny County, please use local county resources or a human caseworker."
  ]
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
    "score": 10.104,
    "text": "The CAO has the discretion to use all available resources to establish verification of required information. - SSN's are verified through e-CIS directly with the Social Security Administration - Household members who do not provide a SSN must sign an Energy Assistance Affidavit ( HS EA-4 ) , or complete question #2 of the Certification section on the LIHEAP application ( HSEA-1) - Earned/Unearned Income- - Pay stubs, benefit award letters or photocopies of these documents - A letter from a person paying voluntary support that includes the person's address and telephone number, the amount of support paid and how often it is paid. - Automated sources such as CIS , e-CIS and exchanges 1,2,3, and 6 of the Income Eligibility Verification System (IEVS) . - Deliverable-fuel bills from January of the previous heating season and forward, utility bills dated two months or less from the date of application to verify heating responsibility, or a landlord statement (HSEA-36) to verify heat is included in the rent. NOTE : In certain situations, such as the death of a spouse or credit problems, the heating bill may be in the name of someone other than the applicant. The applicant must give written proof of address other than the heating bill and explain why the bill is in another person's name. If the landlordâs name is on the heating bill, the applicant must show the lease or a statement from the landlord saying that the applicant is responsible for paying heating costs directly to the fuel supplier. - A utility termination notice showing that service has been shut off or will be shut off within 60 days or a statement from the applicant that his or her deliverable fuel supply will run out within 15 days."
  },
  {
    "program_name": "LIHEAP",
    "document_id": "liheap_677_2_677_2_eligible_notice",
    "title": "677.2 Eligible Notice",
    "section_title": "677.2 Eligible Notice",
    "score": 9.174,
    "text": "When DHS approves an application, it must send the applicant a notice with the following information: 55 PA. Code § 601.22 LIHEAP State Plan § 601.22 - The amount of the benefit. - The householdâs reported income. - The yearly amount of reported income compared with the LIHEAP income limit based on household size. - A detailed explanation of the right to an appeal , how to ask for a hearing, how to prepare for a hearing and what happens at a hearing, and a fair hearing request form. Eligible notices for the cash program include the following text: - For benefits payable to utilities and deliverable fuel companies: âYou qualify for LIHEAP Cash Benefit: $______ will be sent to [vendor name]. This is a one-time only payment for the [program year] heating season.â - For benefits payable directly to LIHEAP applicants: âYou qualify for LIHEAP Cash Benefit: $______ will be sent to YOU. This is a one-time only payment for the [program year] heating season.â Eligible notices for the crisis program have the following text: âYou qualify for 20 xx -20 xx C risis energy assistance. On [ mm/dd/yy ] we approved $_____ to resolve your crisis. Your energy provider is [ name of utility or deliverable company ] for this benefit.â âYou qualify for 20 xx -20 xx Crisis energy assistance. On [ mm/dd/yy ] we approved $_____ to resolve your crisis. The payment for this benefit was sent to YOU. Please be aware that this money is to help you with your home heating cost and should be used to pay your heating bills.â Approval notices are generated on the weekend after the LIHEAP system processes the payments."
  },
  {
    "program_name": "LIHEAP",
    "document_id": "liheap_614_1_614_1_eligible_students",
    "title": "614.1 Eligible Students",
    "section_title": "614.1 Eligible Students",
    "score": 8.166,
    "text": "College students who already got LIHEAP Cash or Crisis benefits during the current heating season as part of another household, such as a parent or guardianâs household, are not eligible for LIHEAP Cash or Crisis benefits in the county where they go to school. College students who receive LIHEAP Cash or Crisis benefits in the county where they attend school are not eligible for LIHEAP Cash or Crisis benefits as part of the parent or guardian household. College students can qualify for LIHEAP if their heat is included in their rent, unless they live in subsidized housing, a dormitory, a boarding home, or a fraternity or sorority house. A student must prove that they are responsible for heating costs by providing a copy of the lease or a statement from the landlord. College students who are unrelated roommates must be considered together as one LIHEAP household ; if a roommate is not a resident of Pennsylvania, they and their income would be excluded from eligibility Unrelated roommates who have separate leases but are responsible for paying one heating bill in the name of one roommate must all be considered together as one LIHEAP household. Example: Two unrelated college roommates share a house off-campus and have separate leases. Heat is included in the rent, and the students pay the rent to the landlord separately each month. The students meet the definition of a household and must be considered for LIHEAP together. The students cannot apply for LIHEAP separately. The CAO must count both roommates in the household size and include each studentâs income in the determination. Example: Two unrelated college roommates, Joe and John, share a house off-campus and have separate leases. Heat is not included in the rent, and only Joeâs name appears on the heating bill. John gives Joe money each month to pay for half of the heating bill. The CAO must count Joe and John together as one LIHEAP household and include each studentâs income in the determination."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_312_1_312_1_general_policy",
    "title": "312.1 General Policy",
    "section_title": "312.12 Pregnant Women and Children under Age One",
    "score": 12.124,
    "text": "A pregnant woman or a qualified child up to age 1 can get MAGI-related MA if household income is equal to or less than 215 percent of the Federal Poverty Income Guideline (FPIG ) for the household size (See Appendix A ) . The pregnant woman, once approved, continues to be eligible for MA coverage through the end of the 12 th month when the12-month postpartum period ends, regardless of her income or a change in circumstances . ( See Chapter 338.42 ) The newborn whose mother was getting MA or CHIP at the time of birth can get MA coverage up to age one, regardless of the parentsâ income, per the Children's Health Insurance Program Reauthorization Act of 2009 (CHIPRA). Children under one who were not born to a mother on MA or CHIP at the time of birth are eligible for a 12-month continuous eligibility period (See Section 312.131 ). NOTE: If the CAO did not know about the pregnancy and learns that MA or SSI benefits were closed during the pregnancy, it must approve MA coverage from the date of the closing through the last day of the month in which the 12-month postpartum period ends. Newborns and pregnant/postpartum individuals can only be closed during their periods of continuous eligibility for the following reasons: - Permanent Move Out of State - If the CAO determines that the opening of benefits was incorrect due to fraud or abuse or agency error. When a provider or other outside source asks for MA benefits for a child under age one, the CAO must review the familyâs case record to see if MA , SSI, or CHIP benefits were open for the mother at any time during the pregnancy. If so, the CAO must authorize MA benefits for the child from the date of birth until the first birthday."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_305_5_305_5_td_ga_related_category_mno",
    "title": "305.5 Modified Adjusted Gross Income (MAGI)-Related Categories",
    "section_title": "305.5 Modified Adjusted Gross Income (MAGI)-Related Categories",
    "score": 10.105,
    "text": "- Families with income at or below 33 percent of the Federal Poverty Income Guideline (FPIG) - Transitional Medical Assistance (TMA) For more information about MAGI-related groups and eligibility criteria, see Chapter 312, Affordable Care Act/Modified Adjusted Gross Income . NOTE: Individuals eligible for Home and Community Based Services (HCBS) should NOT be enrolled in MAGI-related categories. Exception: I ndividuals eligible for the Adult Community Autism Program (ACAP) waiver can continue to be authorized in MAGI budgets as they were previously. They are currently the only waiver program allowed to use MAGI methodologies to determine eligibility. See the HCBS Procedural Desk Guide for details about authorizing the ACAP waiver. 305.51 Children Aged 18 and Under Income 100-133% - Age 6-18 Children aged 18 and under are assigned category MG with program status code (PSC) 00 if they have household income between 33% of the FPIG and the applicable limit for their age group: - Under Age 1 (Target Type I ): 215 percent FPIG - Age 1-5 (Target Type C ): 157 percent FPIG - Age 6-18 (Target Type Y ): 133 percent FPIG Children aged 6-18 who have household income between 100 percent and 133 percent FPIG and who do not have other health insurance are assigned category MG with PSC 19 and a Target Type of â Y â. If a child aged 18 and under becomes ineligible for MA during their 12-month continuous eligibility (CE) period, category/PSCs are assigned to designate CE: - Children under the age of 1 born to a parent receiving MA or CHIP at birth and who become income ineligible for MA are assigned category MG , PSC 18 , and Target Type of â N â. - Children aged 0-18 who become ineligible for MA are assigned category MG , PSC 18 , and Target Type of â C â."
  },
  {
    "program_name": "Medicaid/CHIP",
    "document_id": "medicaid_chip_309_5_309_6_children_s_health_insurance_program_chip",
    "title": "309.5 Children's Health Insurance Program (CHIP)",
    "section_title": "309.5 Children's Health Insurance Program (CHIP)",
    "score": 9.31,
    "text": "The Childrenâs Health Insurance Program (CHIP) is available statewide and provides free or low cost insurance for uninsured children who do not qualify for MA. Children must have no other health insurance to qualify for CHIP. CHIP provides preventative and primary care services, inpatient and outpatient services, dental and orthodontia services, vision services and prescriptions. Free CHIP is available to children up to age 19 whose family income is 208% or less of the Federal Poverty Income Guidelines (FPIG). Low-cost CHIP is available to children up to age 19 whose family income is 208% to 314% of the FPIG. Full-cost CHIP is available for families with income over 314% FPIG. For detailed information about CHIP please see the CHIP Handbook."
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_550_5_550_5_income_excluded_in_computing_eligibility",
    "title": "550.5 Income Excluded in Computing Eligibility",
    "section_title": "550.59 Lump Sum Payments",
    "score": 9.143,
    "text": "NOTE: A one-time Chafee lump sum payment is excluded from income but will be considered a resource in subsequent months. Any recurring payments made to the household will be counted as income. The CAO should assist in verifying the income by contacting the appropriate Children and Youth Agency. At least one Children and Youth Agency has issued Chafee funds spread out over two payments. This is still considered a non-recurring lump sum payment and must be excluded as income but considered a resource in subsequent months. If the household is provided the benefit as a direct payment to a vendor, the payment must be excluded from income. - Energy assistance payments received from a third party on a one-time, non-recurring basis, such as money provided by Catholic Charities toward the payment of an electric bill NOTE: If utility assistance from a third party is ongoing, the CAO will treat the payments as unearned income. For households without an elderly or disabled member, the income will be counted when determining Supplemental Nutrition Assistance Program (SNAP) eligibility (see Section 550.3 )."
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_506_3_506_3_determining_entitlement_to_expedited_service",
    "title": "506.3 Determining Entitlement to Expedited Service",
    "section_title": "506.3 Determining Entitlement to Expedited Service",
    "score": 9.134,
    "text": "A household is entitled to expedited service if it meets any of the following criteria in the month of application: - All members are migrant or seasonal farm workers who are destitute as defined in Chapter 516, Migrant or Seasonal Farm Workers, have $100 or less in liquid resources and nothing else to live on. NOTE: The CAO must use actual income received or expected to be received in the month to determine entitlement. - The value of total liquid resources is $100 or less, and countable monthly gross income is less than $150. - The householdâs combined monthly gross income and liquid resources are less than its monthly shelter expenses. Shelter expenses include rent or mortgage, property taxes, homeowner's insurance, and the appropriate Standard Utility Allowance (SUA) based on the obligation to pay utility bills. When determining entitlement, the County Assitance Office (CAO) must apply the appropriate SUA. To know what SUA is appropriate, the CAO must consider whether the household: - Incurs a heating or cooling cost, - Received assistance under the Low Income Home Energy Assistance Program (LIHEAP) and has an elderly (age 60 or older) or disabled household member. - Receives the Heat and Eat (H&E) Benefit or is going to receive the Heat and Eat Benefit. NOTE: A household must have an elderly or disabled household member to be eligible to receive the H&E benefit."
  },
  {
    "program_name": "SNAP",
    "document_id": "snap_540_5_540_5_excluded_resources",
    "title": "540.5 Excluded Resources",
    "section_title": "540.510 Energy Assistance",
    "score": 8.179,
    "text": "- Payments or allowances for energy assistance made under any federal law and excluded as income subject to Food and Nutrition Service approval - Payments, allowances, or tax credits for energy assistance made under state or local law that are excluded as income - One-time, non-recurring energy assistance payments received from a third party, such as money provided by Catholic Charities toward the payment of an electric bill NOTE: If utility assistance from a third party is ongoing, the CAO will treat the payments as unearned income. For households without an elderly or disabled member, the income will be counted when determining Supplemental Nutrition Assistance Program (SNAP) eligibility (see Section 550.3 )."
  }
]
```

## Program Scores
```json
[
  {
    "program_name": "LIHEAP",
    "status": "no_clear_match",
    "decision_state": "suppressed_out_of_scope",
    "match_score": 9.5,
    "priority_score": 9.5,
    "rule_match_score": 9.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "This prototype currently supports Allegheny County households only.",
    "suppression_reason": "out_of_scope_geography",
    "priority_boost_reason": null
  },
  {
    "program_name": "Medicaid/CHIP",
    "status": "no_clear_match",
    "decision_state": "suppressed_out_of_scope",
    "match_score": 8.5,
    "priority_score": 8.5,
    "rule_match_score": 8.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "This prototype currently supports Allegheny County households only.",
    "suppression_reason": "out_of_scope_geography",
    "priority_boost_reason": null
  },
  {
    "program_name": "SNAP",
    "status": "no_clear_match",
    "decision_state": "suppressed_out_of_scope",
    "match_score": 3.5,
    "priority_score": 3.5,
    "rule_match_score": 3.5,
    "llm_match_score": null,
    "cross_check_status": "rule_only_fallback",
    "cross_check_summary": "This prototype currently supports Allegheny County households only.",
    "suppression_reason": "out_of_scope_geography",
    "priority_boost_reason": null
  }
]
```

## Final Decision
```json
{
  "intake_status": "insufficient_data",
  "geography_status": "out_of_scope_geography",
  "decision_status": "ambiguous",
  "final_status": "needs_human_followup"
}
```

## Final Explanation
This prototype currently supports Allegheny County households only. The household appears to be outside that supported geography, so the system is stopping before normal recommendations. Use county-specific official resources or a human caseworker before relying on any benefits prescreen.

## Caveats
- This is prescreening only.
- This is not an official determination.
- SNAP: This prototype currently supports Allegheny County households only..
- Medicaid/CHIP: This prototype currently supports Allegheny County households only..
- LIHEAP: This prototype currently supports Allegheny County households only..
- This prototype currently supports Allegheny County households only.
