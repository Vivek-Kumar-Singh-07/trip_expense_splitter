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

/* Hero */
.hero { text-align:center; padding:1.5rem 1rem 1rem; margin-bottom:1rem; }
.hero h1 { font-size:2.2rem; font-weight:800; background:linear-gradient(90deg,#f7971e,#ffd200,#f7971e); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-1px; margin-bottom:0; }
.hero h2 { font-size:1.1rem; color:#a9a9c8; font-weight:400; margin-top:0.2rem; }

/* Expense cards — compact */
.expense-card { background:rgba(247,151,30,0.07); border:1px solid rgba(247,151,30,0.2); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.5rem; }

/* Owe cards — compact */
.owe-card { background:rgba(255,90,90,0.07); border:1px solid rgba(255,90,90,0.2); border-radius:10px; padding:0.55rem 0.9rem; margin-bottom:0.45rem; display:flex; justify-content:space-between; align-items:center; }

.settled { background:rgba(90,255,130,0.08); border:1px solid rgba(90,255,130,0.25); border-radius:10px; padding:0.9rem; text-align:center; color:#90f3a5; font-family:'Syne',sans-serif; font-weight:600; font-size:1rem; }

.section-label { font-family:'Syne',sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#a9a9c8; margin-bottom:0.6rem; }

/* Total boxes — compact */
.total-box { background:rgba(255,210,0,0.06); border:1px solid rgba(255,210,0,0.18); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.45rem; }

.fancy-divider { border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(255,210,0,0.4),transparent); margin:1rem 0; }

.count-badge { background:rgba(247,151,30,0.2); border:1px solid rgba(247,151,30,0.4); border-radius:50px; padding:0.1rem 0.5rem; font-size:0.7rem; color:#ffd200; font-family:'Syne',sans-serif; font-weight:700; margin-left:0.4rem; }

/* Primary button */
.stButton > button { background:linear-gradient(90deg,#f7971e,#ffd200); color:#1a1a2e; font-family:'Syne',sans-serif; font-weight:700; border:none; border-radius:10px; padding:0.5rem 1.2rem; font-size:0.95rem; width:100%; }

/* Edit/Delete small buttons */
div[data-testid="column"] .stButton > button {
    padding: 0.3rem 0.6rem;
    font-size: 0.78rem;
    border-radius: 8px;
}

/* Mobile friendly */
@media (max-width: 768px) {
    .hero h1 { font-size: 1.8rem; }
    .hero h2 { font-size: 0.95rem; }
    .expense-card { padding: 0.5rem 0.7rem; }
    .total-box { padding: 0.5rem 0.7rem; }
    .owe-card { padding: 0.5rem 0.7rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── Config ────────────────────────────────────────────────────────────────────
FRIENDS   = ["Sanjeet", "Kundan", "Naya", "Sanjay", "Govind", "Vivek"]
SHEET_NAME = "TripExpenseSplitter"
HEADERS    = ["timestamp", "paid_by", "description", "amount", "split_with", "all_involved", "per_head"]

# ─── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def get_sheet():
    client = get_client()
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
        sheet = spreadsheet.sheet1
        sheet.append_row(HEADERS)
        return sheet
    if sheet.row_values(1) != HEADERS:
        sheet.insert_row(HEADERS, 1)
    return sheet

def load_expenses(sheet):
    expenses = []
    for r in sheet.get_all_records():
        try:
            expenses.append({
                "timestamp":    r["timestamp"],
                "paid_by":      r["paid_by"],
                "description":  r["description"],
                "amount":       float(r["amount"]),
                "split_with":   r["split_with"].split(","),
                "all_involved": r["all_involved"].split(","),
                "per_head":     float(r["per_head"]),
            })
        except Exception:
            continue
    return expenses

def save_expense(sheet, exp):
    sheet.append_row([
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ])

def update_expense_in_sheet(sheet, row_index, exp):
    """row_index is 1-based, +1 for header row"""
    sheet.update(f"A{row_index}:G{row_index}", [[
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ]])

def delete_expense_from_sheet(sheet, row_index):
    """row_index is 1-based, +1 for header row"""
    sheet.delete_rows(row_index)

# ─── Connect & Load ────────────────────────────────────────────────────────────
try:
    sheet     = get_sheet()
    expenses  = load_expenses(sheet)
    connected = True
except Exception as e:
    st.error(f"❌ Google Sheets connection failed: {e}")
    expenses  = []
    connected = False

# ─── Session State ─────────────────────────────────────────────────────────────
if "show_all"    not in st.session_state: st.session_state.show_all    = False
if "editing_idx" not in st.session_state: st.session_state.editing_idx = None

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero"><h1>✈️ Trip Splitter</h1><h2>🐯🌴 PENCH</h2></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.1], gap="large")

# ══════════════════════════════════════════════════
# LEFT — Add / Edit Expense + Log
# ══════════════════════════════════════════════════
with col_left:

    # ── Add / Edit Form ────────────────────────────────────────────────────────
    is_editing = st.session_state.editing_idx is not None
    edit_exp   = expenses[st.session_state.editing_idx] if is_editing else None

    st.markdown(
        f'<div class="section-label">{"✏️ Edit Expense" if is_editing else "💳 Add Expense"}</div>',
        unsafe_allow_html=True
    )

    paid_by = st.selectbox(
        "Who paid?", FRIENDS,
        index=FRIENDS.index(edit_exp["paid_by"]) if is_editing else 0
    )
    description = st.text_input(
        "What was it for?",
        value=edit_exp["description"] if is_editing else "",
        placeholder="e.g. Dinner, Hotel, Petrol…"
    )
    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0, step=10.0, format="%.2f",
        value=edit_exp["amount"] if is_editing else 0.0
    )

    st.markdown("<div style='font-size:0.85rem;font-weight:600;color:#e0e0f0;margin-bottom:0.3rem;'>Split with:</div>", unsafe_allow_html=True)
    select_all = st.checkbox(
        "Select All Friends", 
        value=True if not is_editing else set(edit_exp["split_with"]) == set(f for f in FRIENDS if f != edit_exp["paid_by"])
    )
    if select_all:
        split_with = [f for f in FRIENDS if f != paid_by]
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:0.35rem;margin-bottom:0.4rem;">' +
            "".join(f'<span style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:0.2rem 0.65rem;font-size:0.75rem;color:#d0d0e8;">{f}</span>' for f in split_with) +
            "</div>", unsafe_allow_html=True)
    else:
        default_split = edit_exp["split_with"] if is_editing else [f for f in FRIENDS if f != paid_by]
        split_with = st.multiselect(
            "Choose friends",
            [f for f in FRIENDS if f != paid_by],
            default=[f for f in default_split if f != paid_by]
        )

    # Buttons
    if is_editing:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 Save Changes"):
                if not description.strip():
                    st.error("Enter a description.")
                elif amount <= 0:
                    st.error("Amount must be > 0.")
                elif not split_with:
                    st.error("Select at least one friend.")
                else:
                    all_involved = list(set([paid_by] + split_with))
                    per_head     = round(amount / len(all_involved), 2)
                    updated = {
                        "timestamp":    edit_exp["timestamp"],
                        "paid_by":      paid_by,
                        "description":  description.strip(),
                        "amount":       amount,
                        "split_with":   split_with,
                        "all_involved": all_involved,
                        "per_head":     per_head,
                    }
                    row_index = st.session_state.editing_idx + 2  # +1 header, +1 1-based
                    update_expense_in_sheet(sheet, row_index, updated)
                    st.session_state.editing_idx = None
                    st.success("✅ Expense updated!")
                    st.rerun()
        with b2:
            if st.button("✖ Cancel"):
                st.session_state.editing_idx = None
                st.rerun()
    else:
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
                st.session_state.show_all = False
                st.rerun()

    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

    # ── Expense Log ────────────────────────────────────────────────────────────
    if not expenses:
        st.markdown('<div class="section-label">🧾 Expense Log</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.2rem;color:#a9a9c8;text-align:center;font-size:0.9rem;">No expenses yet!</div>', unsafe_allow_html=True)
    else:
        filter_col, toggle_col = st.columns([2, 1])
        with filter_col:
            filter_person = st.selectbox("🔍 Filter by person", ["All"] + FRIENDS, key="filter_person")
        with toggle_col:
            st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
            if st.button("👁 " + ("Less" if st.session_state.show_all else "Show All")):
                st.session_state.show_all = not st.session_state.show_all
                st.rerun()

        if filter_person == "All":
            filtered = list(enumerate(expenses))  # (original_idx, exp)
        else:
            filtered = [(i, e) for i, e in enumerate(expenses)
                        if e["paid_by"] == filter_person or filter_person in e["all_involved"]]

        total_filtered = len(filtered)
        showing = list(reversed(filtered if st.session_state.show_all else filtered[-5:]))

        label_suffix = f" · {filter_person}" if filter_person != "All" else ""
        badge_text   = f"All {total_filtered}" if st.session_state.show_all else f"Last 5 of {total_filtered}"
        st.markdown(
            f'<div class="section-label">🧾 Expense Log{label_suffix} <span class="count-badge">{badge_text}</span></div>',
            unsafe_allow_html=True
        )

        if not filtered:
            st.markdown(f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1rem;color:#a9a9c8;text-align:center;font-size:0.9rem;">No expenses for {filter_person}.</div>', unsafe_allow_html=True)
        else:
            for orig_idx, exp in showing:
                # Card display
                st.markdown(f"""
                <div class="expense-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="flex:1;min-width:0;">
                            <div style="font-family:'Syne',sans-serif;font-weight:600;color:#ffd200;font-size:0.9rem;">#{orig_idx+1} {exp['description']}</div>
                            <div style="font-size:0.75rem;color:#a9a9c8;">Paid by <b style="color:#d0d0e8">{exp['paid_by']}</b> · {exp['timestamp']}</div>
                            <div style="font-size:0.75rem;color:#a9a9c8;">Split: {', '.join(exp['split_with'])}</div>
                            <div style="font-size:0.75rem;color:#a9a9c8;">₹{exp['amount']:,.2f} ÷ {len(exp['all_involved'])} = <b style="color:#d0d0e8">₹{exp['per_head']:,.2f} each</b></div>
                        </div>
                        <div style="font-size:1.1rem;font-weight:700;color:#f7971e;font-family:'Syne',sans-serif;white-space:nowrap;margin-left:0.5rem;">₹{exp['amount']:,.2f}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Edit / Delete buttons per card
                btn_edit, btn_del = st.columns(2)
                with btn_edit:
                    if st.button(f"✏️ Edit", key=f"edit_{orig_idx}"):
                        st.session_state.editing_idx = orig_idx
                        st.rerun()
                with btn_del:
                    if st.button(f"🗑 Delete", key=f"del_{orig_idx}"):
                        delete_expense_from_sheet(sheet, orig_idx + 2)  # +1 header +1 1-based
                        st.session_state.editing_idx = None
                        st.success("Expense deleted.")
                        st.rerun()

            if not st.session_state.show_all and total_filtered > 5:
                st.markdown(f'<div style="text-align:center;color:#a9a9c8;font-size:0.78rem;margin-bottom:0.4rem;">+ {total_filtered - 5} more hidden · click "Show All"</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# RIGHT — Balances & Settlements
# ══════════════════════════════════════════════════
with col_right:
    st.markdown('<div class="section-label">📊 Who Owes What</div>', unsafe_allow_html=True)

    if not expenses:
        st.markdown('<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.2rem;color:#a9a9c8;text-align:center;font-size:0.9rem;">Add expenses to see balances.</div>', unsafe_allow_html=True)
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

        st.markdown('<div class="section-label" style="margin-top:0.2rem;">💰 Individual Summary</div>', unsafe_allow_html=True)
        for f in FRIENDS:
            net = balance.get(f, 0)
            if net > 0.5:    net_str, net_color = f"+₹{net:,.2f} gets back", "#90f3a5"
            elif net < -0.5: net_str, net_color = f"-₹{abs(net):,.2f} owes", "#ff9a9a"
            else:            net_str, net_color = "✔ Settled", "#a9a9c8"
            st.markdown(f"""
            <div class="total-box">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:0.88rem;"><b style="color:#ffd200">{f}</b></div>
                        <div style="font-size:0.72rem;color:#a9a9c8;">Paid ₹{total_paid.get(f,0):,.2f} · Share ₹{total_share.get(f,0):,.2f}</div>
                    </div>
                    <div style="color:{net_color};font-family:'Syne',sans-serif;font-weight:700;font-size:0.85rem;">{net_str}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🔁 Settlement Plan</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#a9a9c8;font-size:0.75rem;margin-bottom:0.6rem;">Minimum transactions to settle all debts</div>', unsafe_allow_html=True)

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
                        <span style="color:#ff9a9a;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{debtor}</span>
                        <span style="color:#a9a9c8;margin:0 0.4rem;font-size:0.8rem;">→ pays →</span>
                        <span style="color:#90f3a5;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{creditor}</span>
                    </div>
                    <div style="color:#ffd200;font-weight:700;font-family:'Syne',sans-serif;font-size:1rem;">₹{amt:,.2f}</div>
                </div>""", unsafe_allow_html=True)

        grand = sum(e["amount"] for e in expenses)
        st.markdown(f'<div style="margin-top:1rem;text-align:right;color:#a9a9c8;font-size:0.82rem;">Total trip spend: <b style="color:#ffd200;font-family:\'Syne\',sans-serif;">₹{grand:,.2f}</b></div>', unsafe_allow_html=True)
