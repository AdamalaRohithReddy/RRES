"""Script to generate authentic official Atal Pension Yojana guidelines PDF for testing."""
from pathlib import Path
import pymupdf


def create_apy_official_pdf(output_path: Path):
    doc = pymupdf.open()

    # --- Page 1: Overview, Objectives, Target Beneficiaries, State Availability ---
    p1 = doc.new_page()
    p1_text = (
        "GOVERNMENT OF INDIA\n"
        "MINISTRY OF FINANCE - DEPARTMENT OF FINANCIAL SERVICES\n"
        "PENSION FUND REGULATORY AND DEVELOPMENT AUTHORITY (PFRDA)\n\n"
        "ATAL PENSION YOJANA (APY) - OFFICIAL SCHEME GUIDELINES\n\n"
        "1. Overview and Objective\n"
        "Atal Pension Yojana (APY) is a flagship social security initiative launched by the Government of India on 9th May 2015. "
        "The primary objective of the scheme is to provide universal social security to all Indian citizens, with particular focus on workers "
        "in the unorganised sector who lack formal pension and retirement provisions. The scheme is administered by PFRDA through the National Pension System (NPS) architecture.\n\n"
        "2. State Availability and Geographic Scope\n"
        "The Atal Pension Yojana is a Central Government scheme applicable across all States and Union Territories of India. "
        "Any eligible citizen residing in any State or UT in India can enroll through public sector banks, private sector banks, regional rural banks, or post offices.\n\n"
        "3. Target Beneficiaries\n"
        "The scheme is designed for workers in the unorganised sector, daily wage earners, self-employed persons, agricultural workers, and gig economy workers "
        "who are not covered by any statutory social security scheme like EPF or EPS."
    )
    p1.insert_text((50, 60), p1_text, fontsize=10)

    # --- Page 2: Eligibility Criteria, Age Requirement, Income Limit ---
    p2 = doc.new_page()
    p2_text = (
        "ATAL PENSION YOJANA (APY) - OFFICIAL SCHEME GUIDELINES (PAGE 2)\n\n"
        "4. Eligibility Criteria\n"
        "To enroll in Atal Pension Yojana, an applicant must satisfy the following mandatory conditions:\n"
        "a) The applicant must be a citizen of India.\n"
        "b) The applicant must possess an active Savings Bank account or Post Office Savings Bank account.\n"
        "c) The applicant must have an Aadhaar number and a valid mobile number for transaction notifications.\n"
        "d) The applicant must provide nominee details at the time of subscription.\n\n"
        "5. Age Requirement\n"
        "The minimum entry age for joining APY is 18 years, and the maximum entry age is 40 years. "
        "The minimum contribution period under APY is 20 years (from age 40 to 60), or up to 42 years (if entering at age 18). "
        "No person below 18 years or above 40 years of age can enroll in the scheme.\n\n"
        "6. Income Limit and Taxpayer Restriction\n"
        "In accordance with Ministry of Finance Gazette notification w.e.f. 1st October 2022, any citizen who is or has been an Income Tax Payer under the Income Tax Act is NOT eligible to join APY. "
        "If a subscriber who joined on or after 1st October 2022 is subsequently found to be an income tax payer on or before the date of application, "
        "their APY account shall be closed immediately, and the accumulated pension wealth will be refunded to the subscriber after deducting account maintenance charges."
    )
    p2.insert_text((50, 60), p2_text, fontsize=10)

    # --- Page 3: Benefits, Pension Amounts, Spousal and Nominee Protection ---
    p3 = doc.new_page()
    p3_text = (
        "ATAL PENSION YOJANA (APY) - OFFICIAL SCHEME GUIDELINES (PAGE 3)\n\n"
        "7. Benefits and Pension Entitlements\n"
        "Subscribers enrolled in APY are entitled to the following guaranteed benefits:\n"
        "a) Guaranteed Minimum Monthly Pension: Subscribers receive a fixed monthly pension of Rs. 1,000, Rs. 2,000, Rs. 3,000, Rs. 4,000, or Rs. 5,000 per month upon attaining the age of 60 years, depending on their contribution schedule.\n"
        "b) Central Government Guarantee: The minimum pension is guaranteed by the Government of India. If the actual returns on the pension fund are lower than the guaranteed rate, the shortfall is fully funded by the Central Government.\n"
        "c) Spousal Pension: In the event of the subscriber's demise after age 60, the exact same monthly pension amount is paid to the surviving spouse for the rest of their life.\n"
        "d) Return of Pension Corpus to Nominee: After the demise of both the subscriber and the spouse, the complete accumulated pension corpus (e.g. Rs. 8.5 Lakh for the Rs. 5,000 monthly pension tier) is handed over to the designated nominee.\n"
        "e) Tax Benefit: Contributions made to APY are eligible for additional tax deductions under Section 80CCD(1B) of the Income Tax Act up to Rs. 50,000."
    )
    p3.insert_text((50, 60), p3_text, fontsize=10)

    # --- Page 4: Required Documents & Application Process ---
    p4 = doc.new_page()
    p4_text = (
        "ATAL PENSION YOJANA (APY) - OFFICIAL SCHEME GUIDELINES (PAGE 4)\n\n"
        "8. Required Documents\n"
        "Applicants must submit the following verified official documents for enrolment:\n"
        "a) Aadhaar Card: Mandatory identity document and demographic KYC proof.\n"
        "b) Savings Bank Account passbook or account statement showing Account Number, IFSC, and Branch details.\n"
        "c) Active Mobile Number registered with the savings bank account for receiving PRAN and debit SMS alerts.\n"
        "d) APY Subscriber Registration Form, duly filled and signed.\n"
        "e) Nominee Identification Details (Nominee Aadhaar copy and date of birth proof).\n\n"
        "9. Application Process and How to Apply\n"
        "Citizens can apply through either offline or online channels:\n"
        "a) Offline Branch Application:\n"
        "Step 1: Visit the bank branch or post office where your savings bank account is maintained.\n"
        "Step 2: Collect and complete the APY Subscriber Registration Form.\n"
        "Step 3: Choose your monthly pension slab (Rs. 1,000 to Rs. 5,000) and contribution frequency (monthly, quarterly, or half-yearly).\n"
        "Step 4: Authorize auto-debit of the contribution from your bank account.\n"
        "Step 5: Receive an acknowledgement receipt and PRAN (Permanent Retirement Account Number) card.\n"
        "b) Online Net Banking Mode:\n"
        "Log in to internet banking or mobile banking app of your bank. Navigate to 'Government Social Security Schemes', select 'Atal Pension Yojana', verify details, select pension amount, and authenticate via OTP."
    )
    p4.insert_text((50, 60), p4_text, fontsize=10)

    # --- Page 5: Important Conditions, Defaults, Penalties, Exit Rules, FAQs ---
    p5 = doc.new_page()
    p5_text = (
        "ATAL PENSION YOJANA (APY) - OFFICIAL SCHEME GUIDELINES (PAGE 5)\n\n"
        "10. Important Conditions and Rules\n"
        "a) Auto-Debit Mandate: Contributions are debited automatically from the linked savings account. Subscribers must maintain sufficient balance on the due date.\n"
        "b) Default and Delayed Payment Penalty: In case of overdue contributions, banks levy nominal charges: Rs. 1 per month for contribution up to Rs. 100/month, Rs. 2/month up to Rs. 500/month, and Rs. 10/month for contribution above Rs. 1,000/month.\n"
        "c) Voluntary Exit before Age 60: Premature withdrawal is strictly restricted and permitted only under exceptional circumstances such as terminal illness or death of the subscriber before age 60.\n"
        "d) Change in Pension Amount: Subscribers can upgrade or downgrade their pension amount once per financial year during April.\n\n"
        "11. FAQs and Grievance Redressal\n"
        "Subscribers can check their APY account status, download APY e-PRAN, and view transaction statements via the Protean CRA (NSDL) portal (npscra.nsdl.co.in). "
        "Grievances can be registered through the Central Grievance Management System (CGMS) or directly with the PFRDA Ombudsman."
    )
    p5.insert_text((50, 60), p5_text, fontsize=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"Created official scheme PDF at: {output_path}")


if __name__ == "__main__":
    out = Path("data/raw/atal_pension_yojana_guidelines.pdf")
    create_apy_official_pdf(out)
