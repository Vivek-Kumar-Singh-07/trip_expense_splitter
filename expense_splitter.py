import streamlit as st
from collections import defaultdict

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trip Splitter 🧳",
    page_icon="✈️",
    layout="wide",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3, .big-title {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Hero Header */
.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    margin-bottom: 2rem;
}

.hero h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f7971e, #ffd200, #f7971e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    margin-bottom: 0.3rem;
}

.hero p {
    color: #a9a9c8;
    font-size: 1.05rem;
    font-weight: 300;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(10px);
}

.expense-card {
    background: rgba(247, 151, 30, 0.08);
    border: 1px solid rgba(247, 151, 30, 0.25);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
}

.expense-card .desc {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: #ffd200;
}

.expense-card .meta {
    font-size: 0.82rem;
    color: #a9a9c8;
    margin-top: 0.2rem;
}

.expense-card .amount {
    font-size: 1.3rem;
    font-weight: 700;
    color: #f7971e;
    font-family: 'Syne', sans-serif;
}

/* Owe cards */
.owe-card {
    background: rgba(255, 90, 90, 0.08);
    border: 1px solid rgba(255, 90, 90, 0.25);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.owe-name { color: #ff9a9a; font-weight: 600; font-family: 'Syne', sans-serif; }
.owe-arrow { color: #a9a9c8; font-size: 1.2rem; margin: 0 0.5rem; }
.owe-to { color: #90f3a5; font-weight: 600; font-family: 'Syne', sans-serif; }
.owe-amount { color: #ffd200; font-weight: 700; font-family: 'Syne', sans-serif; font-size: 1.1rem; }

.settled {
    background: rgba(90, 255, 130, 0.08);
    border: 1px solid rgba(90, 255, 130, 0.25);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    color: #90f3a5;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
}

/* Section labels */
.section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #a9a9c8;
    margin-bottom: 0.8rem;
}

/* Friend avatar pills */
.pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.5rem; }
.pill {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 50px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: #d0d0e8;
}

/* Totals */
.total-box {
    background: rgba(255, 210, 0, 0.07);
    border: 1px solid rgba(255, 210, 0, 0.2);
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.6rem;
}
.total-name { color: #e0e0f0; font-size: 0.95rem; }
.total-amt { color: #ffd200; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.15rem; }

/* Override Streamlit button */
.stButton > button {
    background: linear-gradient(90deg, #f7971e, #ffd200);
    color: #1a1a2e;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 2rem;
    font-size: 1rem;
    cursor: pointer;
    width: 100%;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.88; }

/* Divider */
.fancy-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,210,0,0.4), transparent);
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Friends ───────────────────────────────────────────────────────────────────
FRIENDS = ["Sanjeet", "Kundan", "Nayan", "Sanjay", "Govind", "Vivek"]

# ─── State Init ────────────────────────────────────────────────────────────────
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>✈️ Trip Splitter</h1>
    <h2>Pench</h2>
</div>
""", unsafe_allow_html=True)

# ─── Layout: Left (Add Expense) | Right (Summary) ──────────────────────────────
col_left, col_right = st.columns([1, 1.1], gap="large")

# ══════════════════════════════════════════════════
# LEFT COLUMN — Add Expense Form
# ══════════════════════════════════════════════════
with col_left:
    st.markdown('<div class="section-label">💳 Add Expense</div>', unsafe_allow_html=True)

    with st.container():
        paid_by = st.selectbox("Who paid?", FRIENDS, key="paid_by")

        description = st.text_input("What was it for?", placeholder="e.g. Dinner at dhaba, Hotel, Petrol…", key="desc")

        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f", key="amount")

        st.markdown("**Split with:**")
        select_all = st.checkbox("Select All Friends", value=True, key="select_all")

        if select_all:
            split_with = [f for f in FRIENDS if f != paid_by]
            st.markdown(
                '<div class="pill-row">' +
                "".join(f'<span class="pill">{f}</span>' for f in split_with) +
                "</div>",
                unsafe_allow_html=True
            )
        else:
            others = [f for f in FRIENDS if f != paid_by]
            split_with = st.multiselect(
                "Choose friends to split with",
                others,
                default=others,
                key="split_with_multi"
            )

        if st.button("➕ Add Expense"):
            if not description.strip():
                st.error("Please enter a description.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            elif not split_with:
                st.error("Select at least one friend to split with.")
            else:
                all_involved = list(set([paid_by] + split_with))
                per_head = amount / len(all_involved)
                st.session_state.expenses.append({
                    "paid_by": paid_by,
                    "description": description.strip(),
                    "amount": amount,
                    "split_with": split_with,
                    "all_involved": all_involved,
                    "per_head": per_head,
                })
                st.success(f"✅ Added ₹{amount:,.2f} for '{description.strip()}'")
                st.rerun()

    # Expense Log
    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">🧾 Expense Log</div>', unsafe_allow_html=True)

    if not st.session_state.expenses:
        st.markdown('<div class="card" style="color:#a9a9c8;text-align:center;">No expenses yet. Add your first one above!</div>', unsafe_allow_html=True)
    else:
        for i, exp in enumerate(reversed(st.session_state.expenses)):
            idx = len(st.session_state.expenses) - 1 - i
            splitters = ", ".join(exp["split_with"])
            st.markdown(f"""
            <div class="expense-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div class="desc">#{idx+1} {exp['description']}</div>
                        <div class="meta">Paid by <b style="color:#d0d0e8">{exp['paid_by']}</b> · Split with: {splitters}</div>
                        <div class="meta">₹{exp['amount']:,.2f} ÷ {len(exp['all_involved'])} = <b style="color:#d0d0e8">₹{exp['per_head']:,.2f} each</b></div>
                    </div>
                    <div class="amount">₹{exp['amount']:,.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear All Expenses"):
            st.session_state.expenses = []
            st.rerun()

# ══════════════════════════════════════════════════
# RIGHT COLUMN — Balances & Settlements
# ══════════════════════════════════════════════════
with col_right:
    st.markdown('<div class="section-label">📊 Who Owes What</div>', unsafe_allow_html=True)

    if not st.session_state.expenses:
        st.markdown('<div class="card" style="color:#a9a9c8;text-align:center;">Add expenses to see balances here.</div>', unsafe_allow_html=True)
    else:
        # Compute net balance for each person
        # Positive = owed money (paid more), Negative = owes money (paid less)
        balance = defaultdict(float)

        for exp in st.session_state.expenses:
            per_head = exp["per_head"]
            # Payer gets credited for what others owe them
            for person in exp["all_involved"]:
                if person == exp["paid_by"]:
                    balance[exp["paid_by"]] += per_head * (len(exp["all_involved"]) - 1)
                else:
                    balance[person] -= per_head

        # Ensure all friends appear
        for f in FRIENDS:
            if f not in balance:
                balance[f] = 0.0

        # ── Individual Totals ──
        st.markdown('<div class="section-label" style="margin-top:0.3rem;">💰 Total Paid & Share</div>', unsafe_allow_html=True)

        total_paid = defaultdict(float)
        total_share = defaultdict(float)
        for exp in st.session_state.expenses:
            total_paid[exp["paid_by"]] += exp["amount"]
            for person in exp["all_involved"]:
                total_share[person] += exp["per_head"]

        for f in FRIENDS:
            paid = total_paid.get(f, 0)
            share = total_share.get(f, 0)
            net = balance[f]
            net_str = f"+₹{net:,.2f} (gets back)" if net > 0.5 else (f"-₹{abs(net):,.2f} (owes)" if net < -0.5 else "✔ Settled")
            net_color = "#90f3a5" if net > 0.5 else ("#ff9a9a" if net < -0.5 else "#a9a9c8")
            st.markdown(f"""
            <div class="total-box">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="total-name"><b style="color:#ffd200">{f}</b></div>
                        <div style="font-size:0.8rem;color:#a9a9c8">Paid ₹{paid:,.2f} · Share ₹{share:,.2f}</div>
                    </div>
                    <div style="color:{net_color};font-family:'Syne',sans-serif;font-weight:700;">{net_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

        # ── Settlement Plan ──
        st.markdown('<div class="section-label">🔁 Settlement Plan</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a9a9c8;font-size:0.82rem;margin-bottom:0.8rem;">Minimum transactions to settle all debts</div>', unsafe_allow_html=True)

        # Simplified debt settlement algorithm
        pos = {k: v for k, v in balance.items() if v > 0.5}
        neg = {k: -v for k, v in balance.items() if v < -0.5}

        transactions = []
        creditors = sorted(pos.items(), key=lambda x: -x[1])
        debtors = sorted(neg.items(), key=lambda x: -x[1])

        creditors = list(creditors)
        debtors = list(debtors)

        i, j = 0, 0
        while i < len(creditors) and j < len(debtors):
            cname, camount = creditors[i]
            dname, damount = debtors[j]
            settled = min(camount, damount)
            transactions.append((dname, cname, settled))
            creditors[i] = (cname, camount - settled)
            debtors[j] = (dname, damount - settled)
            if creditors[i][1] < 0.01:
                i += 1
            if debtors[j][1] < 0.01:
                j += 1

        if not transactions:
            st.markdown('<div class="settled">🎉 Everyone is settled up! No payments needed.</div>', unsafe_allow_html=True)
        else:
            for (debtor, creditor, amt) in transactions:
                st.markdown(f"""
                <div class="owe-card">
                    <div>
                        <span class="owe-name">{debtor}</span>
                        <span class="owe-arrow">→ pays →</span>
                        <span class="owe-to">{creditor}</span>
                    </div>
                    <div class="owe-amount">₹{amt:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # Grand total
        grand = sum(exp["amount"] for exp in st.session_state.expenses)
        st.markdown(f"""
        <div style="margin-top:1.2rem;text-align:right;color:#a9a9c8;font-size:0.9rem;">
            Total trip spend: <b style="color:#ffd200;font-family:'Syne',sans-serif;">₹{grand:,.2f}</b>
        </div>
        """, unsafe_allow_html=True)