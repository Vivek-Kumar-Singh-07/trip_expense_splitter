import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from datetime import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Trip Splitter 🧳", page_icon="✈️", layout="wide")

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; }
.hero { text-align:center; padding:2.5rem 1rem 1.5rem; margin-bottom:2rem; }
.hero h1 { font-size:3rem; font-weight:800; background:linear-gradient(90deg,#f7971e,#ffd200,#f7971e); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-1px; }
.hero p { color:#a9a9c8; font-size:1.05rem; font-weight:300; }
.expense-card { background:rgba(247,151,30,0.08); border:1px solid rgba(247,151,30,0.25); border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.7rem; }
.owe-card { background:rgba(255,90,90,0.08); border:1px solid rgba(255,90,90,0.25); border-radius:12px; padding:0.9rem 1.2rem; margin-bottom:0.6rem; display:flex; justify-content:space-between; align-items:center; }
.settled { background:rgba(90,255,130,0.08); border:1px solid rgba(90,255,130,0.25); border-radius:12px; padding:1.2rem; text-align:center; color:#90f3a5; font-family:'Syne',sans-serif; font-weight:600; font-size:1.1rem; }
.section-label { font-family:'Syne',sans-serif; font-size:0.75rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#a9a9c8; margin-bottom:0.8rem; }
.total-box { background:rgba(255,210,0,0.07); border:1px solid rgba(255,210,0,0.2); border-radius:12px; padding:1rem 1.3rem; margin-bottom:0.6rem; }
.fancy-divider { border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(255,210,0,0.4),transparent); margin:1.5rem 0; }
.stButton > button { background:linear-gradient(90deg,#f7971e,#ffd200); color:#1a1a2e; font-family:'Syne',sans-serif; font-weight:700; border:none; border-radius:10px; padding:0.6rem 2rem; font-size:1rem; width:100%; }
.count-badge { background:rgba(247,151,30,0.2); border:1px solid rgba(247,151,30,0.4); border-radius:50px; padding:0.15rem 0.6rem; font-size:0.75rem; color:#ffd200; font-family:'Syne',sans-serif; font-weight:700; margin-left:0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Config ────────────────────────────────────────────────────────────────────
FRIENDS = ["Sanjeet", "Kundan", "Nayan", "Sanjay", "Govind", "Vivek"]
SHEET_NAME = "TripExpenseSplitter"
HEADERS = ["timestamp", "paid_by", "description", "amount", "split_with", "all_involved", "per_head"]

# ─── Google Sheets — only cache the CLIENT, never the data ────────────────────
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def get_sheet():
    """Always fetch a fresh sheet object — never cached."""
    client = get_client()
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
        sheet = spreadsheet.sheet1
        sheet.append_row(HEADERS)
        return sheet
    # Ensure headers exist
    if sheet.row_values(1) != HEADERS:
        sheet.insert_row(HEADERS, 1)
    return sheet

def load_expenses(sheet):
    """Always reads fresh data from Google Sheets."""
    expenses = []
    for r in sheet.get_all_records():
        try:
            expenses.append({
                "timestamp":   r["timestamp"],
                "paid_by":     r["paid_by"],
                "description": r["description"],
                "amount":      float(r["amount"]),
                "split_with":  r["split_with"].split(","),
                "all_involved":r["all_involved"].split(","),
                "per_head":    float(r["per_head"]),
            })
        except Exception:
            continue
    return expenses

def save_expense(sheet, exp):
    sheet.append_row([
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ])

def render_expense_card(exp, idx):
    st.markdown(f"""
    <div class="expense-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:600;color:#ffd200;">#{idx} {exp['description']}</div>
                <div style="font-size:0.82rem;color:#a9a9c8;">Paid by <b style="color:#d0d0e8">{exp['paid_by']}</b> · {exp['timestamp']}</div>
                <div style="font-size:0.82rem;color:#a9a9c8;">Split with: {', '.join(exp['split_with'])}</div>
                <div style="font-size:0.82rem;color:#a9a9c8;">₹{exp['amount']:,.2f} ÷ {len(exp['all_involved'])} = <b style="color:#d0d0e8">₹{exp['per_head']:,.2f} each</b></div>
            </div>
            <div style="font-size:1.3rem;font-weight:700;color:#f7971e;font-family:'Syne',sans-serif;">₹{exp['amount']:,.2f}</div>
        </div>
    </div>""", unsafe_allow_html=True)

# ─── Connect & Load fresh data every page load ─────────────────────────────────
try:
    sheet    = get_sheet()
    expenses = load_expenses(sheet)
    connected = True
except Exception as e:
    st.error(f"❌ Google Sheets connection failed: {e}")
    expenses  = []
    connected = False

# ─── Session State for Show All toggle ─────────────────────────────────────────
if "show_all" not in st.session_state:
    st.session_state.show_all = False

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero"><h1>✈️ Trip Expense Splitter</h1><h2>🐯🌴 PENCH</h2></div>', unsafe_allow_html=True)
if connected:
    st.success("🟢 Connected to Google Sheets — all data is saved permanently!")

col_left, col_right = st.columns([1, 1.1], gap="large")

# ── LEFT: Add Expense ──────────────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="section-label">💳 Add Expense</div>', unsafe_allow_html=True)

    paid_by     = st.selectbox("Who paid?", FRIENDS)
    description = st.text_input("What was it for?", placeholder="e.g. Dinner, Hotel, Petrol…")
    amount      = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")

    st.markdown("**Split with:**")
    select_all = st.checkbox("Select All Friends", value=True)
    if select_all:
        split_with = [f for f in FRIENDS if f != paid_by]
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.5rem;">' +
            "".join(f'<span style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:50px;padding:0.25rem 0.75rem;font-size:0.8rem;color:#d0d0e8;">{f}</span>' for f in split_with) +
            "</div>", unsafe_allow_html=True)
    else:
        split_with = st.multiselect(
            "Choose friends", [f for f in FRIENDS if f != paid_by],
            default=[f for f in FRIENDS if f != paid_by]
        )

    if st.button("➕ Add Expense"):
        if not description.strip():
            st.error("Please enter a description.")
        elif amount <= 0:
            st.error("Amount must be greater than 0.")
        elif not split_with:
            st.error("Select at least one friend.")
        elif not connected:
            st.error("Not connected to Google Sheets.")
        else:
            all_involved = list(set([paid_by] + split_with))
            per_head     = round(amount / len(all_involved), 2)
            save_expense(sheet, {
                "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                "paid_by":      paid_by,
                "description":  description.strip(),
                "amount":       amount,
                "split_with":   split_with,
                "all_involved": all_involved,
                "per_head":     per_head,
            })
            st.success(f"✅ Saved ₹{amount:,.2f} for '{description.strip()}'")
            st.session_state.show_all = False  # reset to compact view on new entry
            st.rerun()

    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

    # ── Expense Log ────────────────────────────────────────────────────────────
    if not expenses:
        st.markdown('<div class="section-label">🧾 Expense Log</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.5rem;color:#a9a9c8;text-align:center;">No expenses yet!</div>', unsafe_allow_html=True)
    else:
        # Filter + Show All row
        filter_col, toggle_col = st.columns([2, 1])
        with filter_col:
            filter_person = st.selectbox("🔍 Filter by person", ["All"] + FRIENDS, key="filter_person")
        with toggle_col:
            st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
            if st.button("👁 " + ("Show Less" if st.session_state.show_all else "Show All")):
                st.session_state.show_all = not st.session_state.show_all
                st.rerun()

        # Apply filter
        if filter_person == "All":
            filtered = expenses
        else:
            filtered = [e for e in expenses if e["paid_by"] == filter_person or filter_person in e["all_involved"]]

        total_filtered = len(filtered)
        showing = list(reversed(filtered if st.session_state.show_all else filtered[-5:]))

        # Section label with badge
        label_suffix = f" · {filter_person}" if filter_person != "All" else ""
        badge_text   = f"All {total_filtered}" if st.session_state.show_all else f"Last 5 of {total_filtered}"
        st.markdown(
            f'<div class="section-label">🧾 Expense Log{label_suffix} <span class="count-badge">{badge_text}</span></div>',
            unsafe_allow_html=True
        )

        if not filtered:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.2rem;color:#a9a9c8;text-align:center;">No expenses found for {filter_person}.</div>', unsafe_allow_html=True)
        else:
            for exp in showing:
                idx = expenses.index(exp) + 1
                render_expense_card(exp, idx)

            if not st.session_state.show_all and total_filtered > 5:
                st.markdown(f'<div style="text-align:center;color:#a9a9c8;font-size:0.82rem;margin-bottom:0.5rem;">+ {total_filtered - 5} more hidden · click "Show All" to see</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear ALL Expenses (cannot undo)"):
            sheet.clear()
            sheet.append_row(HEADERS)
            st.session_state.show_all = False
            st.rerun()

# ── RIGHT: Balances ────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="section-label">📊 Who Owes What</div>', unsafe_allow_html=True)

    if not expenses:
        st.markdown('<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.5rem;color:#a9a9c8;text-align:center;">Add expenses to see balances.</div>', unsafe_allow_html=True)
    else:
        balance, total_paid, total_share = defaultdict(float), defaultdict(float), defaultdict(float)
        for exp in expenses:
            total_paid[exp["paid_by"]] += exp["amount"]
            for person in exp["all_involved"]:
                total_share[person] += exp["per_head"]
                if person == exp["paid_by"]:
                    balance[exp["paid_by"]] += exp["per_head"] * (len(exp["all_involved"]) - 1)
                else:
                    balance[person] -= exp["per_head"]

        st.markdown('<div class="section-label" style="margin-top:0.3rem;">💰 Individual Summary</div>', unsafe_allow_html=True)
        for f in FRIENDS:
            net = balance.get(f, 0)
            if net > 0.5:    net_str, net_color = f"+₹{net:,.2f} (gets back)", "#90f3a5"
            elif net < -0.5: net_str, net_color = f"-₹{abs(net):,.2f} (owes)", "#ff9a9a"
            else:            net_str, net_color = "✔ Settled", "#a9a9c8"
            st.markdown(f"""
            <div class="total-box">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div><b style="color:#ffd200">{f}</b></div>
                        <div style="font-size:0.8rem;color:#a9a9c8;">Paid ₹{total_paid.get(f,0):,.2f} · Share ₹{total_share.get(f,0):,.2f}</div>
                    </div>
                    <div style="color:{net_color};font-family:'Syne',sans-serif;font-weight:700;">{net_str}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🔁 Settlement Plan</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a9a9c8;font-size:0.82rem;margin-bottom:0.8rem;">Minimum transactions to settle all debts</div>', unsafe_allow_html=True)

        creditors = sorted([(k, v) for k, v in balance.items() if v > 0.5], key=lambda x: -x[1])
        debtors   = sorted([(k, -v) for k, v in balance.items() if v < -0.5], key=lambda x: -x[1])
        transactions, i, j = [], 0, 0
        while i < len(creditors) and j < len(debtors):
            cname, camount = creditors[i]
            dname, damount = debtors[j]
            settled = min(camount, damount)
            transactions.append((dname, cname, settled))
            creditors[i] = (cname, camount - settled)
            debtors[j]   = (dname, damount - settled)
            if creditors[i][1] < 0.01: i += 1
            if debtors[j][1]   < 0.01: j += 1

        if not transactions:
            st.markdown('<div class="settled">🎉 Everyone is settled up!</div>', unsafe_allow_html=True)
        else:
            for debtor, creditor, amt in transactions:
                st.markdown(f"""
                <div class="owe-card">
                    <div>
                        <span style="color:#ff9a9a;font-weight:600;font-family:'Syne',sans-serif;">{debtor}</span>
                        <span style="color:#a9a9c8;margin:0 0.5rem;">→ pays →</span>
                        <span style="color:#90f3a5;font-weight:600;font-family:'Syne',sans-serif;">{creditor}</span>
                    </div>
                    <div style="color:#ffd200;font-weight:700;font-family:'Syne',sans-serif;font-size:1.1rem;">₹{amt:,.2f}</div>
                </div>""", unsafe_allow_html=True)

        grand = sum(e["amount"] for e in expenses)
        st.markdown(f'<div style="margin-top:1.2rem;text-align:right;color:#a9a9c8;font-size:0.9rem;">Total trip spend: <b style="color:#ffd200;font-family:\'Syne\',sans-serif;">₹{grand:,.2f}</b></div>', unsafe_allow_html=True)
