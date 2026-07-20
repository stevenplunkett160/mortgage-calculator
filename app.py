import streamlit as st

# Set page config
st.set_page_config(
    page_title="Easy Mortgage Calculator",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="collapsed",
)



# ----------------- SESSION STATE SETUP -----------------
# We use st.session_state to allow the slider value to be modified programmatically via buttons

# 1. Main slider property value
if "property_value" not in st.session_state:
    st.session_state.property_value = 940000.0

# 2. Debug parameters (defaults)
if "interest_rate" not in st.session_state:
    st.session_state.interest_rate = 6.35

if "mortgage_term" not in st.session_state:
    st.session_state.mortgage_term = 30

if "deposit_amt_input" not in st.session_state:
    st.session_state.deposit_amt_input = 595000.0


if "stamp_duty_pct" not in st.session_state:
    st.session_state.stamp_duty_pct = 4.0

if "stamp_duty_cash" not in st.session_state:
    st.session_state.stamp_duty_cash = 26000.0

if "stamp_duty_mode" not in st.session_state:
    st.session_state.stamp_duty_mode = "Auto (by State)"

if "capitalize_stamp_duty" not in st.session_state:
    st.session_state.capitalize_stamp_duty = False

if "state" not in st.session_state:
    st.session_state.state = "NSW"

if "buyer_type" not in st.session_state:
    st.session_state.buyer_type = "Owner-Occupier (not FHB)"


# Callbacks for Property Value Adjustments
def adjust_property_value(amount):
    new_val = st.session_state.property_value + amount
    # Clamp value within slider min/max limits ($800k - $950k)
    st.session_state.property_value = float(max(800000.0, min(new_val, 950000.0)))

def set_property_value(value):
    st.session_state.property_value = float(value)


# ----------------- STAMP DUTY CALCULATION ENGINE -----------------
def calculate_stamp_duty(value, state, buyer_type):
    """Calculate stamp duty using 2025/26 published bracket formulas for each Australian state/territory."""
    is_fhb = buyer_type == "First Home Buyer"
    is_owner = buyer_type in ("Owner-Occupier (not FHB)", "First Home Buyer")

    def brackets(v, tiers):
        """Apply progressive bracket formula: tiers = [(threshold, base, rate_per_100), ...]"""
        for threshold, base, rate in reversed(tiers):
            if v > threshold:
                return base + (v - threshold) * rate / 100.0
        return 0.0

    if state == "NSW":
        duty = brackets(value, [
            (0,          0,       1.25),
            (17000,      212,     1.50),
            (37000,      512,     1.75),
            (99000,      1597,    3.50),
            (372000,     11152,   4.50),
            (1240000,    50212,   5.50),
        ])
        if is_fhb:
            if value <= 800000:
                duty = 0.0
            elif value <= 1000000:
                # Sliding concession: proportion of full duty
                duty = duty * (value - 800000) / 200000.0

    elif state == "VIC":
        if is_owner and value <= 550000:
            # PPR concessional rates
            duty = brackets(value, [
                (0,       0,      1.4),
                (25000,   350,    2.4),
                (130000,  2870,   5.0),
                (440000,  18370,  6.0),
            ])
        else:
            # General rates
            if value <= 960000:
                duty = brackets(value, [
                    (0,       0,    1.4),
                    (25000,   350,  2.4),
                    (130000,  2870, 6.0),
                ])
            elif value <= 2000000:
                duty = value * 0.055
            else:
                duty = 110000 + (value - 2000000) * 0.065
        if is_fhb:
            if value <= 600000:
                duty = 0.0
            elif value <= 750000:
                # Sliding concession
                duty = duty * (value - 600000) / 150000.0

    elif state == "QLD":
        if is_owner:
            # Home concession rates
            duty = brackets(value, [
                (0,       0,      1.0),
                (350000,  3500,   3.5),
                (540000,  10150,  4.5),
                (1000000, 30850,  5.75),
            ])
        else:
            # Standard/investor rates
            duty = brackets(value, [
                (0,       0,      0.0),
                (5000,    0,      1.5),
                (75000,   1050,   3.5),
                (540000,  17325,  4.5),
                (1000000, 38025,  5.75),
            ])
        if is_fhb and is_owner:
            # Established home concession phases out $700k–$800k
            if value <= 700000:
                duty = 0.0
            elif value <= 800000:
                duty = duty * (value - 700000) / 100000.0

    elif state == "WA":
        duty = brackets(value, [
            (0,       0,      1.90),
            (120000,  2280,   2.85),
            (150000,  3135,   3.80),
            (360000,  11115,  4.75),
            (725000,  28453,  5.15),
        ])

    elif state == "SA":
        duty = brackets(value, [
            (0,       0,      1.0),
            (12000,   120,    2.0),
            (30000,   480,    3.0),
            (50000,   1080,   3.5),
            (100000,  2830,   4.0),
            (200000,  6830,   4.25),
            (250000,  8955,   4.75),
            (300000,  11330,  5.0),
            (500000,  21330,  5.5),
        ])

    elif state == "TAS":
        if value <= 3000:
            duty = 50.0
        else:
            duty = brackets(value, [
                (0,       50,     0.0),
                (3000,    50,     1.75),
                (25000,   435,    2.25),
                (75000,   1560,   3.50),
                (200000,  5935,   4.00),
                (375000,  12935,  4.25),
                (725000,  27810,  4.50),
            ])

    elif state == "ACT":
        if is_owner:
            # Owner-occupier rates (approximate – ACT uses banded flat rates)
            if value <= 260000:    duty = value * 0.0028
            elif value <= 300000:  duty = 728 + (value - 260000) * 0.0232
            elif value <= 500000:  duty = 1656 + (value - 300000) * 0.0390
            elif value <= 750000:  duty = 9456 + (value - 500000) * 0.0490
            elif value <= 1000000: duty = 21706 + (value - 750000) * 0.0497
            elif value <= 1455000: duty = 34131 + (value - 1000000) * 0.0520
            else:                  duty = value * 0.0454
        else:
            # Non-owner/investor rates
            if value <= 200000:    duty = value * 0.0120
            elif value <= 300000:  duty = 2400 + (value - 200000) * 0.0220
            elif value <= 500000:  duty = 4600 + (value - 300000) * 0.0345
            elif value <= 750000:  duty = 11500 + (value - 500000) * 0.0432
            elif value <= 1000000: duty = 22300 + (value - 750000) * 0.0496
            elif value <= 1455000: duty = 34700 + (value - 1000000) * 0.0518
            else:                  duty = value * 0.0454
        if is_fhb and value <= 750000:
            duty = 0.0  # ACT FHB exemption (owner-occupier, up to $750k)

    elif state == "NT":
        # NT formula-based calculation for ≤$525k, flat rate above
        v_thousands = value / 1000.0
        if value <= 525000:
            duty = (0.06571441 * v_thousands ** 2) + (15 * v_thousands)
        else:
            duty = value * 0.0495

    else:
        duty = 0.0

    return max(0.0, duty)


# -----------------  CALCULATION ENGINE -----------------
property_val = st.session_state.property_value

# 1. Total cash the buyer has available (input by user)
total_cash = st.session_state.deposit_amt_input

# 2. Determine Stamp Duty
if st.session_state.stamp_duty_mode == "Auto (by State)":
    stamp_duty_amt = calculate_stamp_duty(
        property_val,
        st.session_state.state,
        st.session_state.buyer_type
    )
elif st.session_state.stamp_duty_mode == "Custom Cash Amount":
    stamp_duty_amt = st.session_state.stamp_duty_cash
else:
    stamp_duty_amt = 0.0

# 3. Calculate Down Payment & Loan Amount
if st.session_state.capitalize_stamp_duty:
    # Stamp duty rolled into loan
    cash_for_house = min(property_val, max(0.0, total_cash))
    realtor_deposit_amt = min(property_val * 0.10, cash_for_house)
    settlement_cash = max(0.0, cash_for_house - realtor_deposit_amt)
    deposit_amt = cash_for_house
    loan_amount = max(0.0, property_val - deposit_amt + stamp_duty_amt)
    upfront_cash = deposit_amt
else:
    # Stamp duty paid upfront out of available cash
    cash_for_house = min(property_val, max(0.0, total_cash - stamp_duty_amt))
    realtor_deposit_amt = min(property_val * 0.10, cash_for_house)
    settlement_cash = max(0.0, cash_for_house - realtor_deposit_amt)
    deposit_amt = cash_for_house
    loan_amount = max(0.0, property_val - deposit_amt)
    upfront_cash = min(total_cash, deposit_amt + stamp_duty_amt)

# 4. Standard Amortization Formula
# Monthly interest rate r, total number of months n
r = (st.session_state.interest_rate / 100.0) / 12.0
n = st.session_state.mortgage_term * 12

if loan_amount <= 0:
    monthly_repayment = 0.0
elif r == 0:
    monthly_repayment = loan_amount / n
else:
    monthly_repayment = loan_amount * (r * (1 + r)**n) / ((1 + r)**n - 1)

# Convert monthly repayment to weekly repayment
# (Standard banking practice is converting monthly payment to annual, then dividing by 52)
weekly_repayment = (monthly_repayment * 12.0) / 52.0

# Inject CSS with dynamic theme based on weekly repayment threshold
_over_threshold = weekly_repayment > 550

# Green theme (normal)
_c_primary   = "#10b981" if not _over_threshold else "#ef4444"
_c_light     = "#34d399" if not _over_threshold else "#f87171"
_c_dark      = "#059669" if not _over_threshold else "#dc2626"
_c_rgb       = "16, 185, 129" if not _over_threshold else "239, 68, 68"
_c_rgb_dark  = "5, 150, 105"  if not _over_threshold else "185, 28, 28"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0f172a !important;
    }}

    div[data-testid="stAppViewBlockContainer"] {{
        max-width: 600px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}

    .app-title {{
        text-align: center;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(to right, {_c_primary}, {_c_light});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    .app-subtitle {{
        text-align: center;
        color: #94a3b8;
        font-weight: 400;
        font-size: 1rem;
        margin-bottom: 2rem;
    }}

    .repayment-card {{
        background: linear-gradient(135deg, rgba({_c_rgb}, 0.12) 0%, rgba({_c_rgb_dark}, 0.03) 100%);
        border: 1px solid rgba({_c_rgb}, 0.25);
        border-radius: 24px;
        padding: 32px 24px;
        text-align: center;
        box-shadow: 0 10px 30px -10px rgba({_c_rgb}, 0.15);
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}

    .repayment-card:hover {{
        transform: translateY(-2px);
        border-color: rgba({_c_rgb}, 0.4);
        box-shadow: 0 15px 40px -10px rgba({_c_rgb}, 0.25);
    }}

    .repayment-label {{
        font-size: 12px;
        font-weight: 700;
        color: {_c_primary};
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }}

    .repayment-value {{
        font-size: 3.5rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
        text-shadow: 0 0 20px rgba({_c_rgb}, 0.3);
    }}

    .repayment-period {{
        font-size: 15px;
        color: #94a3b8;
        margin-top: 10px;
        font-weight: 500;
    }}

    .stats-container {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 28px;
    }}

    .stat-box {{
        flex: 1 1 18%;
        min-width: 90px;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 10px 4px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        transition: all 0.2s ease;
    }}

    .stat-box:hover {{
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(255, 255, 255, 0.1);
    }}

    .stat-title {{
        font-size: 10px;
        color: #94a3b8;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        font-weight: 600;
    }}

    .stat-val {{
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
    }}

    div[data-baseweb="slider"] > div {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        height: 10px !important;
        border-radius: 5px !important;
    }}

    div[data-baseweb="slider"] > div > div {{
        background-color: {_c_primary} !important;
    }}

    div[role="slider"] {{
        background-color: #ffffff !important;
        border: 4px solid {_c_primary} !important;
        box-shadow: 0 0 8px rgba({_c_rgb}, 0.3) !important;
        width: 22px !important;
        height: 22px !important;
        cursor: grab !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
    }}

    div[role="slider"]:hover {{
        border-color: {_c_light} !important;
        background-color: {_c_primary} !important;
        box-shadow: 0 0 16px rgba({_c_rgb}, 0.7) !important;
    }}

    div[role="slider"]:active {{
        cursor: grabbing !important;
        background-color: {_c_dark} !important;
        border-color: {_c_light} !important;
        box-shadow: 0 0 12px rgba({_c_rgb}, 0.9) !important;
    }}

    div[data-testid="stWidgetLabel"] p {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }}

    div[data-testid="stButton"] button {{
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
    }}

    div[data-testid="stButton"] button:hover {{
        background-color: {_c_primary} !important;
        color: #0f172a !important;
        border-color: {_c_primary} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba({_c_rgb}, 0.25) !important;
    }}

    div[data-testid="stButton"] button:active {{
        transform: translateY(1px) !important;
    }}

    div[data-testid="stExpander"] {{
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        overflow: visible !important;
        margin-top: 2rem !important;
    }}

    div[data-testid="stExpander"] > details {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stExpander"] summary {{
        font-size: 0.65rem !important;
        font-weight: 400 !important;
        color: rgba(100, 116, 139, 0.35) !important;
        padding: 4px 0 !important;
        background: transparent !important;
        transition: color 0.3s ease !important;
        letter-spacing: 6px !important;
        list-style: none !important;
    }}

    div[data-testid="stExpander"] summary:hover {{
        color: rgba(100, 116, 139, 0.6) !important;
    }}

    div[data-testid="stExpander"] summary::marker,
    div[data-testid="stExpander"] summary::-webkit-details-marker {{
        display: none !important;
        color: transparent !important;
    }}

    .footer {{
        text-align: center;
        color: #475569;
        font-size: 0.8rem;
        margin-top: 3rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- MAIN MOTHER'S VIEW -----------------
# Header
st.markdown("<h1 class='app-title'>🏡 Quick Repayment Calculator</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Drag the slider below to see how much your property will cost per week.</p>", unsafe_allow_html=True)

# Big Repayment Display Card
st.markdown(
    f"""
    <div class='repayment-card'>
        <div class='repayment-label'>Estimated Weekly Repayment</div>
        <div class='repayment-value'>${weekly_repayment:,.2f}</div>
        <div class='repayment-period'>calculated at {st.session_state.interest_rate:.2f}% interest over {st.session_state.mortgage_term} years</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Stats Breakdown Card Row
st.markdown(
    f"""
    <div class='stats-container'>
        <div class='stat-box'>
            <span class='stat-title'>Property Price</span>
            <span class='stat-val'>${property_val:,.0f}</span>
        </div>
        <div class='stat-box'>
            <span class='stat-title'>Initial Deposit</span>
            <span class='stat-val'>${realtor_deposit_amt:,.0f}</span>
        </div>
        <div class='stat-box'>
            <span class='stat-title'>Stamp Duty (Est.)</span>
            <span class='stat-val'>${stamp_duty_amt:,.0f}</span>
        </div>
        <div class='stat-box'>
            <span class='stat-title'>Settlement Deposit</span>
            <span class='stat-val'>${settlement_cash:,.0f}</span>
        </div>
        <div class='stat-box'>
            <span class='stat-title'>Loan Amount</span>
            <span class='stat-val'>${loan_amount:,.0f}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Property Slider (The main input for Mother)
st.slider(
    "Choose Property Price",
    min_value=800000.0,
    max_value=950000.0,
    value=st.session_state.property_value,
    step=5000.0,
    key="property_value",
    format="$%,d"
)

# Helper Buttons to fine-tune or jump to presets
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Tweak Buttons
tweak_col1, tweak_col2, tweak_col3, tweak_col4 = st.columns(4)
with tweak_col1:
    st.button("- $50k", on_click=adjust_property_value, args=(-50000.0,))
with tweak_col2:
    st.button("- $10k", on_click=adjust_property_value, args=(-10000.0,))
with tweak_col3:
    st.button("+ $10k", on_click=adjust_property_value, args=(10000.0,))
with tweak_col4:
    st.button("+ $50k", on_click=adjust_property_value, args=(50000.0,))


# Footer
st.markdown(
    """
    <div class='footer'>
        Designed with ❤️ for Mum • Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- DEBUG / DEVELOPER MENU (COLLAPSED BY DEFAULT) -----------------
# Located in a collapsible expander at the bottom. This keeps the main view simple for the mother,
# but lets the user tweak calculations behind the scenes.
with st.expander("· · ·", expanded=False):
    st.markdown("<h4 style='color: #10b981; margin-top:0;'>Developer Control Panel (not for you mum 😁)</h4>", unsafe_allow_html=True)
    st.markdown("Use these settings to change interest rates, terms, deposits, and duties. The main view will adjust automatically.", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Interest Rate
        st.session_state.interest_rate = st.slider(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=st.session_state.interest_rate,
            step=0.05,
            format="%.2f%%"
        )

        # Available Funds dollar amount text box
        st.session_state.deposit_amt_input = st.number_input(
            "Available Funds ($)",
            min_value=0.0,
            max_value=5000000.0,
            value=st.session_state.deposit_amt_input,
            step=5000.0,
            format="%.0f"
        )

    with col2:
        # Mortgage Term
        st.session_state.mortgage_term = st.slider(
            "Mortgage Term (Years)",
            min_value=5,
            max_value=40,
            value=int(st.session_state.mortgage_term),
            step=1,
            format="%d Years"
        )

        # Stamp Duty controls
        st.session_state.stamp_duty_mode = st.radio(
            "Stamp Duty Mode",
            ["Auto (by State)", "Custom Cash Amount", "None / Exempt"],
            index=["Auto (by State)", "Custom Cash Amount", "None / Exempt"].index(
                st.session_state.stamp_duty_mode
            ) if st.session_state.stamp_duty_mode in ["Auto (by State)", "Custom Cash Amount", "None / Exempt"] else 0
        )

        if st.session_state.stamp_duty_mode == "Auto (by State)":
            st.session_state.state = st.selectbox(
                "State / Territory",
                ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
                index=["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"].index(st.session_state.state)
            )
            st.session_state.buyer_type = st.radio(
                "Buyer Type",
                ["Owner-Occupier (not FHB)", "First Home Buyer", "Investor"],
                index=["Owner-Occupier (not FHB)", "First Home Buyer", "Investor"].index(
                    st.session_state.buyer_type
                ) if st.session_state.buyer_type in ["Owner-Occupier (not FHB)", "First Home Buyer", "Investor"] else 0
            )
        elif st.session_state.stamp_duty_mode == "Custom Cash Amount":
            st.session_state.stamp_duty_cash = st.number_input(
                "Custom Stamp Duty ($)",
                min_value=0.0,
                max_value=500000.0,
                value=st.session_state.stamp_duty_cash,
                step=1000.0,
                format="%.2f"
            )

    # Capitalize Stamp Duty Toggle
    st.session_state.capitalize_stamp_duty = st.checkbox(
        "Capitalize Stamp Duty (Add stamp duty to the loan amount instead of paying upfront)",
        value=st.session_state.capitalize_stamp_duty
    )

    # Upfront Cash Required + Stamp Duty breakdown (read-only, calculated)
    st.divider()
    stamp_pct_effective = (stamp_duty_amt / property_val * 100) if property_val > 0 else 0
    state_label = f"{st.session_state.state} · {st.session_state.buyer_type}" if st.session_state.stamp_duty_mode == "Auto (by State)" else st.session_state.stamp_duty_mode
    capitalize_label = "Deposit only (stamp duty added to loan)" if st.session_state.capitalize_stamp_duty else "Total cash contributed to house purchase"
    st.markdown(
        f"""
        <div style='display:flex; flex-direction:column; gap:10px; margin-top:4px;'>
          <div style='display:flex; align-items:center; justify-content:space-between;
                      background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
                      border-radius: 12px; padding: 14px 18px;'>
              <div>
                  <div style='font-size:11px; color:#10b981; font-weight:700;
                              letter-spacing:1.5px; text-transform:uppercase;'>Total Available Funds</div>
                  <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>Total cash provided</div>
              </div>
              <div style='font-size:1.4rem; font-weight:800; color:#f8fafc;'>${total_cash:,.0f}</div>
          </div>
          <div style='display:flex; align-items:center; justify-content:space-between;
                      background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
                      border-radius: 12px; padding: 14px 18px;'>
              <div>
                  <div style='font-size:11px; color:#10b981; font-weight:700;
                              letter-spacing:1.5px; text-transform:uppercase;'>10% Realtor Deposit (Exchange)</div>
                  <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>Paid upfront to holding trust</div>
              </div>
              <div style='font-size:1.4rem; font-weight:800; color:#f8fafc;'>-${realtor_deposit_amt:,.0f}</div>
          </div>
          <div style='display:flex; align-items:center; justify-content:space-between;
                      background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
                      border-radius: 12px; padding: 14px 18px;'>
              <div>
                  <div style='font-size:11px; color:#10b981; font-weight:700;
                              letter-spacing:1.5px; text-transform:uppercase;'>Stamp Duty (Settlement)</div>
                  <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>{state_label} · {stamp_pct_effective:.2f}%</div>
              </div>
              <div style='font-size:1.4rem; font-weight:800; color:#f8fafc;'>-${stamp_duty_amt:,.0f}</div>
          </div>
          <div style='display:flex; align-items:center; justify-content:space-between;
                      background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
                      border-radius: 12px; padding: 14px 18px;'>
              <div>
                  <div style='font-size:11px; color:#10b981; font-weight:700;
                              letter-spacing:1.5px; text-transform:uppercase;'>Remaining Cash at Settlement</div>
                  <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>Paid towards remaining house balance</div>
              </div>
              <div style='font-size:1.4rem; font-weight:800; color:#f8fafc;'>${settlement_cash:,.0f}</div>
          </div>
          <div style='display:flex; align-items:center; justify-content:space-between;
                      background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2);
                      border-radius: 12px; padding: 14px 18px;'>
              <div>
                  <div style='font-size:11px; color:#10b981; font-weight:700;
                              letter-spacing:1.5px; text-transform:uppercase;'>Net Down Payment (Total Cash to House)</div>
                  <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>{capitalize_label}</div>
              </div>
              <div style='font-size:1.4rem; font-weight:800; color:#f8fafc;'>${deposit_amt:,.0f}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
