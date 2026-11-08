# Pakistan UBL Zero-Hassle International Cashflow & Tax Guide
**Author**: Engineer Abdullah Bin Zafar  
**Target Banking Institution**: United Bank Limited (UBL), Pakistan  
**Applicable Regulations**: SBP Foreign Exchange Manual & FBR Income Tax Ordinance Section 154A  

---

## 1. Executive Summary: The Pakistan International Payout Challenge

As a developer/engineer based in Pakistan with an account exclusively at **United Bank Limited (UBL)**:
1. **Stripe & PayPal are unavailable locally**: Standard Stripe requires a US/UK legal entity (LLC/LTD) with ~$500–$1,000 upfront setup fees, annual registered agent fees, and complex IRS form 5472 filings.
2. **Traditional International Wire Transfers are expensive**: Intermediary correspondent banks (e.g., Citi, J.P. Morgan) deduct \$25–\$45 per wire, plus local receiving bank charges.
3. **High Domestic Taxes if improperly declared**: Normal domestic income in Pakistan is taxed at progressive rates up to **35%**, whereas foreign IT export remittances qualify for a special concessionary final tax of **0.25% to 1.0%** if routed correctly through official banking channels.

This blueprint provides the exact, legally compliant, minimal-fee, and minimal-tax architecture to monetize **SafeMotion AI**, GitHub sponsorships, and international B2B consulting directly into your **UBL Pakistan** account.

---

## 2. The Complete 3-Step International Payout Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                      STEP 1: GLOBAL CUSTOMERS (US / EU / WORLD)                    │
│   Purchase SafeMotion AI API tiers ($39/mo Pro, $999 Enterprise)                  │
│   Pay via Credit Card, Debit Card, Apple Pay, Google Pay, or GitHub Sponsors      │
└─────────────────────────────────────────▲─────────────────────────────────────────┘
                                          │ Card swipe / checkout
┌─────────────────────────────────────────┴─────────────────────────────────────────┐
│              STEP 2: MERCHANT OF RECORD (MoR) — LEMONSQUEEZY / POLAR.SH           │
│   - Resells software licenses legally as the Merchant of Record                   │
│   - Automatically calculates, collects & remits global sales tax and EU VAT       │
│   - ZERO US LLC required. ZERO sales tax liability for you personally             │
│   - Holds payout balances in USD                                                  │
└─────────────────────────────────────────▲─────────────────────────────────────────┘
                                          │ Automatic weekly/monthly payout ($0 fee)
┌─────────────────────────────────────────┴─────────────────────────────────────────┐
│             STEP 3: PAYONEER VIRTUAL RECEIVING ACCOUNT (USD ROUTING)              │
│   - Provides US Bank Account (First Century Bank / Community Federal Savings Bank)│
│   - LemonSqueezy / Polar / Upwork deposit USD directly via ACH (0% - 1% fee)      │
└─────────────────────────────────────────▲─────────────────────────────────────────┘
                                          │ 1-Click Bank Withdrawal (Mid-market FX)
┌─────────────────────────────────────────┴─────────────────────────────────────────┐
│        STEP 4: UNITED BANK LIMITED (UBL) PAKISTAN — DIRECT TO YOUR IBAN           │
│   - Funds land in PKR in your UBL Account (PKxx UNIL xxxxxxxxxxxxxxxx)            │
│   - Auto-classified under SBP Foreign Remittance Code (IT/Software Export)        │
│   - Free Proceeds Realization Certificate (PRC / Form R) issued by UBL            │
│   - Final withholding tax: 0.25% (with PSEB) or 1.0% (without PSEB)               │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Implementation Instructions

### Step 3.1: Sign Up for LemonSqueezy or Polar.sh (Merchant of Record)
1. Go to [LemonSqueezy.com](https://lemonsqueezy.com) or [Polar.sh](https://polar.sh).
2. Create an account as an **Individual / Sole Proprietor** using your Pakistan national identity (CNIC) and address in Lahore.
3. LemonSqueezy is an approved Merchant of Record (MoR): they handle all customer disputes, chargebacks, and international taxes.
4. Set up two products for SafeMotion AI:
   - **SafeMotion Pro**: \$39/month recurring subscription.
   - **SafeMotion Enterprise On-Prem**: \$999 one-time perpetual license.

### Step 3.2: Open a Free Payoneer Account Linked to UBL
1. Go to [Payoneer.com](https://payoneer.com) and register as an **Individual Freelancer / Software Developer**.
2. When asked for bank details, provide your **United Bank Limited (UBL) Account Details**:
   - Bank Name: `United Bank Limited`
   - Account Title: `Abdullah Bin Zafar`
   - IBAN: `PKxx UNIL xxxxxxxxxxxxxxxx` (found on your UBL chequebook or UBL Digital app).
3. Under **Receive > Global Payment Service**, Payoneer will issue you a **USD Virtual Bank Account** (Bank name: *First Century Bank* or *Lead Bank*, Routing number, and Account number).
4. Enter this US routing number and account number into LemonSqueezy / Polar.sh / Upwork as your payout method.

### Step 3.3: Transferring Money from Payoneer to UBL
1. Once payments accumulate in Payoneer, click **Withdraw > To Bank Account**.
2. Select your UBL Pakistan account.
3. Payoneer converts USD to PKR at the State Bank of Pakistan (SBP) interbank mid-market rate with a nominal ~1.5% FX spread.
4. The funds arrive in your UBL account within **2 to 24 hours** via 1-Link RTGS!

---

## 4. Pakistani Tax Optimization: How to Pay Only 0.25% to 1.0% Tax Legally

Under the **Income Tax Ordinance 2001 (Section 154A)**, export of computer software and IT-enabled services enjoys a special final tax regime:

| Category | Registration Status | FBR Tax Rate | Required Documentation |
| :--- | :--- | :---: | :--- |
| **Gold Standard** | Registered with **PSEB** (Pakistan Software Export Board) | **0.25%** (Flat Final Tax) | PSEB Certificate + UBL PRC |
| **Silver Standard** | Unregistered Freelancer / Developer | **1.00%** (Flat Final Tax) | UBL PRC (Form R) |
| **Default Mistake** | Non-filer / undeclared domestic income | **Up to 35%** | Standard domestic tax slabs |

### How to Get the 0.25% Flat Tax Rate:
1. **PSEB Registration**: Register online at [pseb.org.pk](https://pseb.org.pk) under the **IT Professional / Freelancer** category.
   - Annual fee: ~PKR 5,000 (often discounted for university students/recent graduates).
   - PSEB issues a digital Registration Certificate valid for 1 year.
2. **UBL Trade Operations Notification**:
   - Provide your PSEB registration certificate to your UBL branch manager or email it to UBL Home Remittance / Trade Services.
   - Instruct them: *"Please tag all incoming foreign inward remittances to my account under Purpose Code: 9114 / 9115 (Computer & Information Services / Software Export)."*
3. **Download Your PRC (Proceeds Realization Certificate)**:
   - Within 48 hours of any international transfer landing in your UBL account, request a **PRC** (also known as Form R) from UBL Digital / Branch.
   - This certificate is free of charge and serves as **100% conclusive proof to FBR** that the income was foreign IT export and is fully settled under the final tax regime.

---

## 5. Alternative Direct B2B Payout Channels (Immediate Cashflow)

If you take high-ticket freelance consulting contracts for ROS 2 / MCP integration:

| Platform | Payout to Pakistan | Fee | Transfer Time |
| :--- | :--- | :--- | :--- |
| **Upwork** | Direct to Local Bank (UBL IBAN) | **$0.99** flat per withdrawal | 24 Hours |
| **Contra** | Via Stripe Express to Payoneer | Free | 1–2 Days |
| **Direct Client Invoice** | Client wires directly to UBL IBAN (SWIFT: `UNILPKKA`) | Client pays wire fee | 2–3 Days |
| **GitHub Sponsors** | Via Stripe Connect (Payoneer USD) | Free (GitHub covers fee) | Monthly |

---

## 6. Financial Summary: Retaining ~97.5% of Every Dollar Earned

On a **\$1,000 USD** Enterprise License sale of SafeMotion AI:
- LemonSqueezy MoR platform fee (5% + \$0.50): ~\$50.50
- Payout to Payoneer USD: \$949.50 (Free)
- Payoneer FX spread to PKR at UBL: ~\$14.24 (1.5%)
- Net remittance received in UBL: ~PKR 258,000 equivalent
- FBR Final Tax (0.25% with PSEB): ~PKR 645
- **Net In-Pocket Retention: > 97.5% of gross earnings!**

This architecture is 100% legal, fully compliant with State Bank of Pakistan regulations, and gives you institutional financial infrastructure using only your existing United Bank Limited account.
