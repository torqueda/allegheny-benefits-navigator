# Evaluation Failures

Processed cases: 10
Full matches: 5
Mismatches: 5
Exceptions: 0

## TC01
Scenario: Single adult in Pittsburgh working limited part-time hours. She is uninsured, struggling to afford groceries, and has a past-due gas bill after a cold spell.

- Failure category: priority_mismatch
- Expected: LIHEAP > SNAP > Medicaid/CHIP
- Actual: LIHEAP > Medicaid/CHIP > SNAP
- Diagnostic note: Priority order comparison uses the current 3-program prototype scope only.

## TC03
Scenario: Single parent with two children ages 3 and 8. Parent recently lost one side job, the family is skipping meals, and the heating bill is overdue.

- Failure category: priority_mismatch
- Expected: SNAP > LIHEAP > Medicaid/CHIP
- Actual: LIHEAP > SNAP > Medicaid/CHIP
- Diagnostic note: Priority order comparison uses the current 3-program prototype scope only.

## TC05
Scenario: Two adults and two children (ages 4 and 9) are living on one paycheck. Their income appears just under SNAP and LIHEAP cutoffs, and the younger child may still fall within Medicaid limits while the older child may not.

- Failure category: priority_mismatch
- Expected: LIHEAP > SNAP > Medicaid/CHIP
- Actual: LIHEAP > Medicaid/CHIP > SNAP
- Diagnostic note: Priority order comparison uses the current 3-program prototype scope only.

## TC06
Scenario: Applicant says she is employed full time and has not recently lost work, but the intake form shows zero earned income. The household is also reporting food and utility hardship.

- Failure category: priority_mismatch
- Expected: SNAP > LIHEAP > Medicaid/CHIP
- Actual: LIHEAP > Medicaid/CHIP > SNAP
- Diagnostic note: Priority order comparison uses the current 3-program prototype scope only.

## TC08
Scenario: Two adults and three children report a mix of part-time wages, cash babysitting, and a very recent layoff. The intake is messy, the household is behind on bills, and the applicant is more comfortable in Spanish.

- Failure category: priority_mismatch
- Expected: SNAP > LIHEAP > Medicaid/CHIP
- Actual: LIHEAP > SNAP > Medicaid/CHIP
- Diagnostic note: Priority order comparison uses the current 3-program prototype scope only.
