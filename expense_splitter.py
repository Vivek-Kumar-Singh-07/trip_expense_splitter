import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Trip Expense Tracker 🧳", page_icon="🐯", layout="wide")

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }

/* Tiger background on html+body — Streamlit does not override these */
html, body {
    background-color: #050e04 !important;
    background-image:
        linear-gradient(180deg, rgba(2,10,2,0.42) 0%, rgba(3,14,3,0.22) 50%, rgba(2,10,2,0.42) 100%),
        url("https://images.unsplash.com/photo-1545436578-96740d4d5d34?w=1800&q=90&fit=crop&crop=center") !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
}

/* Make Streamlit wrapper divs transparent so body bg shows through */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: transparent !important;
}

/* All content above bg */
.main .block-container { position:relative; z-index:1; }
header { position:relative; z-index:1; }

/* Hero */
.hero {
    text-align:center;
    padding:1rem 1rem 0.6rem;
    margin-bottom:0.6rem;
    position:relative;
    z-index:1;
}
.hero h1 {
    font-size:1.9rem;
    font-weight:800;
    background:linear-gradient(90deg,#ffb347,#ffd200,#ff8c00);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    letter-spacing:-0.5px;
    margin-bottom:0;
    line-height:1.2;
    white-space:normal;
    word-break:keep-all;
}
.hero h2 {
    font-size:0.95rem;
    color:#d4b87a;
    font-weight:400;
    margin-top:0.15rem;
    letter-spacing:1px;
}

/* Expense cards — compact */
.expense-card { background:rgba(180,100,10,0.1); border:1px solid rgba(220,150,50,0.25); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.5rem; backdrop-filter:blur(4px); }

/* Owe cards — compact */
.owe-card { background:rgba(200,60,60,0.08); border:1px solid rgba(220,100,100,0.22); border-radius:10px; padding:0.55rem 0.9rem; margin-bottom:0.45rem; display:flex; justify-content:space-between; align-items:center; backdrop-filter:blur(4px); }

.settled { background:rgba(50,180,100,0.1); border:1px solid rgba(80,220,130,0.3); border-radius:10px; padding:0.9rem; text-align:center; color:#7df5b0; font-family:'Syne',sans-serif; font-weight:600; font-size:1rem; }

.section-label { font-family:'Syne',sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#d4a84b; margin-bottom:0.6rem; }

/* Total boxes — compact */
.total-box { background:rgba(30,50,30,0.35); border:1px solid rgba(180,140,60,0.2); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.45rem; backdrop-filter:blur(4px); }

.fancy-divider { border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(210,160,60,0.5),transparent); margin:1rem 0; }

.count-badge { background:rgba(210,160,60,0.2); border:1px solid rgba(210,160,60,0.4); border-radius:50px; padding:0.1rem 0.5rem; font-size:0.7rem; color:#ffd97d; font-family:'Syne',sans-serif; font-weight:700; margin-left:0.4rem; }

/* Primary button */
.stButton > button { background:linear-gradient(90deg,#b45a00,#e07b00); color:#fff; font-family:'Syne',sans-serif; font-weight:700; border:none; border-radius:10px; padding:0.5rem 1.2rem; font-size:0.95rem; width:100%; }

/* Edit/Delete small icon buttons */
div[data-testid="column"] .stButton > button {
    padding: 0.2rem 0.55rem;
    font-size: 1rem;
    border-radius: 7px;
    background: rgba(255,255,255,0.07);
    color: #e8d5a0;
    border: 1px solid rgba(210,160,60,0.25);
    width: auto;
    min-width: unset;
}

/* Mobile friendly — tighter spacing */
@media (max-width: 768px) {
    .hero { padding: 0.6rem 0.5rem 0.4rem; margin-bottom: 0.4rem; }
    .hero h1 { font-size: 1.3rem; }
    .hero h2 { font-size: 0.78rem; }
    .expense-card { padding: 0.35rem 0.5rem; margin-bottom: 0.2rem; }
    .total-box { padding: 0.35rem 0.5rem; margin-bottom: 0.25rem; }
    .owe-card { padding: 0.35rem 0.5rem; margin-bottom: 0.25rem; }
    .fancy-divider { margin: 0.4rem 0; }
    .section-label { margin-bottom: 0.3rem; font-size:0.62rem; }
    .main .block-container { padding-top: 0.3rem !important; padding-bottom: 0.3rem !important; padding-left: 0.4rem !important; padding-right: 0.4rem !important; }
}

/* Tighten globally */
.main .block-container { padding-top: 0.8rem !important; padding-bottom: 0.8rem !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.25rem !important; }

/* Icon buttons — tiny and perfectly inline */
div[data-testid="column"] .stButton > button {
    padding: 0.05rem 0.3rem !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
    background: rgba(255,255,255,0.07) !important;
    color: #e8d5a0 !important;
    border: 1px solid rgba(210,160,60,0.2) !important;
    width: auto !important;
    min-width: unset !important;
    line-height: 1.4 !important;
    height: auto !important;
    margin-top: 0.3rem !important;
}
/* Settle / Undo buttons — small pill style */
button[kind="secondary"][data-testid*="settle_"],
button[kind="secondary"][data-testid*="undo_"],
div[data-testid="column"] button[data-testid*="settle"],
div[data-testid="column"] button[data-testid*="undo"] {
    padding: 0.12rem 0.45rem !important;
    font-size: 0.72rem !important;
    border-radius: 50px !important;
    background: rgba(255,200,50,0.12) !important;
    color: #ffd97d !important;
    border: 1px solid rgba(210,160,60,0.35) !important;
    width: auto !important;
    min-width: unset !important;
    line-height: 1.5 !important;
    height: auto !important;
    margin-top: 0.55rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Config ────────────────────────────────────────────────────────────────────
FRIENDS    = ["Sanjeet", "Kundan", "Nayan", "Sanjay", "Govind", "Vivek"]
SHEET_NAME = "TripExpenseSplitter"
HEADERS    = ["timestamp", "paid_by", "description", "amount", "split_with", "all_involved", "per_head"]
IST        = timezone(timedelta(hours=5, minutes=30))

# ── UPI IDs: replace with each person's real UPI VPA ──────────────────────────
# Format: phonenumber@upi  OR  name@okaxis  OR  name@ybl  etc.
UPI_IDS = {
    "Sanjeet": "sanjeet@upi",
    "Kundan":  "kundan@upi",
    "Nayan":   "nayan@upi",
    "Sanjay":  "sanjay@upi",
    "Govind":  "govind@upi",
    "Vivek":   "vivek@upi",
}

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
if "show_all"          not in st.session_state: st.session_state.show_all          = False
if "editing_idx"       not in st.session_state: st.session_state.editing_idx       = None
if "form_reset_key"    not in st.session_state: st.session_state.form_reset_key    = 0
# Set of "debtor|creditor" pairs that have been manually settled
if "settled_payments"  not in st.session_state: st.session_state.settled_payments  = set()
# pair_key currently showing UPI picker
if "pending_settle"    not in st.session_state: st.session_state.pending_settle    = None

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero"><h1>Trip Expense Tracker</h1><h2>🐯🌴 PENCH WILDLIFE TRIP</h2></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.1], gap="large")

# ══════════════════════════════════════════════════
# LEFT — Add / Edit Expense + Log
# ══════════════════════════════════════════════════
with col_left:

    # ── Add / Edit Form ────────────────────────────────────────────────────────
    is_editing = st.session_state.editing_idx is not None
    edit_exp   = expenses[st.session_state.editing_idx] if is_editing else None

    # Unique suffix so widgets fully reset after a successful add
    fk = st.session_state.form_reset_key

    st.markdown(
        f'<div class="section-label">{"✏️ Edit Expense" if is_editing else "💳 Add Expense"}</div>',
        unsafe_allow_html=True
    )

    paid_by = st.selectbox(
        "Who paid?", FRIENDS,
        index=FRIENDS.index(edit_exp["paid_by"]) if is_editing else 0,
        key=f"paid_by_{fk}"
    )
    description = st.text_input(
        "What was it for?",
        value=edit_exp["description"] if is_editing else "",
        placeholder="e.g. Dinner, Hotel, Petrol…",
        key=f"description_{fk}"
    )
    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0, step=10.0, format="%.2f",
        value=edit_exp["amount"] if is_editing else 0.0,
        key=f"amount_{fk}"
    )

    st.markdown("<div style='font-size:0.85rem;font-weight:600;color:#e0e0f0;margin-bottom:0.3rem;'>Split with:</div>", unsafe_allow_html=True)
    select_all = st.checkbox(
        "Select All Friends",
        value=True if not is_editing else set(edit_exp["split_with"]) == set(f for f in FRIENDS if f != edit_exp["paid_by"]),
        key=f"select_all_{fk}"
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
            default=[f for f in default_split if f != paid_by],
            key=f"split_with_{fk}"
        )

    # ── Buttons ────────────────────────────────────────────────────────────────
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
                # Use IST for timestamp
                ist_now      = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
                save_expense(sheet, {
                    "timestamp":    ist_now,
                    "paid_by":      paid_by,
                    "description":  description.strip(),
                    "amount":       amount,
                    "split_with":   split_with,
                    "all_involved": all_involved,
                    "per_head":     per_head,
                })
                st.success(f"✅ Saved ₹{amount:,.2f} for '{description.strip()}'")
                st.session_state.show_all    = False
                # ↓ Bump key to reset all form widgets to defaults
                st.session_state.form_reset_key += 1
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
            filtered = list(enumerate(expenses))
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
            st.markdown(f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.7rem;color:#a9a9c8;text-align:center;font-size:0.85rem;">No expenses for {filter_person}.</div>', unsafe_allow_html=True)
        else:
            # Handle edit/delete via query params
            qp = st.query_params
            if "edit" in qp:
                try:
                    st.session_state.editing_idx = int(qp["edit"])
                except: pass
                st.query_params.clear()
                st.rerun()
            if "delete" in qp:
                try:
                    del_idx = int(qp["delete"])
                    delete_expense_from_sheet(sheet, del_idx + 2)
                    st.session_state.editing_idx = None
                    st.success("Expense deleted.")
                except: pass
                st.query_params.clear()
                st.rerun()

            for orig_idx, exp in showing:
                st.markdown(f"""
                <div class="expense-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.4rem;">
                        <div style="flex:1;min-width:0;">
                            <div style="font-family:'Syne',sans-serif;font-weight:600;color:#ffd200;font-size:0.82rem;line-height:1.3;">#{orig_idx+1} {exp['description']}</div>
                            <div style="font-size:0.7rem;color:#a9a9c8;line-height:1.3;">By <b style="color:#d0d0e8">{exp['paid_by']}</b> · {exp['timestamp']}</div>
                            <div style="font-size:0.7rem;color:#a9a9c8;line-height:1.3;">Split: {', '.join(exp['split_with'])}</div>
                            <div style="font-size:0.7rem;color:#a9a9c8;line-height:1.3;">₹{exp['amount']:,.2f} ÷ {len(exp['all_involved'])} = <b style="color:#d0d0e8">₹{exp['per_head']:,.2f}/head</b></div>
                        </div>
                        <div style="display:flex;flex-direction:column;align-items:center;gap:0.3rem;flex-shrink:0;">
                            <div style="font-size:0.95rem;font-weight:700;color:#f7971e;font-family:'Syne',sans-serif;white-space:nowrap;">₹{exp['amount']:,.2f}</div>
                            <div style="display:flex;gap:0.3rem;">
                                <a href="?edit={orig_idx}" target="_self" style="text-decoration:none;background:rgba(255,255,255,0.08);border:1px solid rgba(210,160,60,0.3);border-radius:6px;padding:0.15rem 0.4rem;font-size:0.85rem;cursor:pointer;" title="Edit">✏️</a>
                                <a href="?delete={orig_idx}" target="_self" style="text-decoration:none;background:rgba(255,60,60,0.1);border:1px solid rgba(255,100,100,0.3);border-radius:6px;padding:0.15rem 0.4rem;font-size:0.85rem;cursor:pointer;" title="Delete">🗑️</a>
                            </div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

            if not st.session_state.show_all and total_filtered > 5:
                st.markdown(f'<div style="text-align:center;color:#a9a9c8;font-size:0.75rem;margin-top:0.2rem;">+ {total_filtered - 5} more · click "Show All"</div>', unsafe_allow_html=True)

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

        all_settled = not transactions or all(
            f"{d}|{c}" in st.session_state.settled_payments for d, c, _ in transactions
        )
        if not transactions or all_settled:
            st.markdown('<div class="settled">🎉 Everyone is settled up!</div>', unsafe_allow_html=True)
        else:
            for debtor, creditor, amt in transactions:
                pair_key        = f"{debtor}|{creditor}"
                is_settled      = pair_key in st.session_state.settled_payments
                is_picking_upi  = st.session_state.pending_settle == pair_key

                amt_str    = f"{amt:.2f}"
                upi_note   = f"Trip+settlement"
                payee_upi  = UPI_IDS.get(creditor, "")
                payee_name = creditor

                # Universal upi://pay — works on Android across all apps (PhonePe, GPay, Paytm…)
                # PhonePe-specific deep link (Android only)
                # GPay/Tez deep link (Android only)
                upi_base      = f"upi://pay?pa={payee_upi}&pn={payee_name}&am={amt_str}&cu=INR&tn={upi_note}"
                phonepe_url   = f"phonepe://pay?pa={payee_upi}&pn={payee_name}&am={amt_str}&cu=INR&tn={upi_note}"
                gpay_url      = f"tez://upi/pay?pa={payee_upi}&pn={payee_name}&am={amt_str}&cu=INR&tn={upi_note}"

                # ── Row HTML ──────────────────────────────────────────────────
                if is_settled:
                    row_html = f"""
                    <div class="owe-card" style="opacity:0.4;flex-direction:column;align-items:flex-start;gap:0.15rem;">
                        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
                            <div>
                                <span style="color:#ff9a9a;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;text-decoration:line-through;">{debtor}</span>
                                <span style="color:#a9a9c8;margin:0 0.35rem;font-size:0.78rem;">→ pays →</span>
                                <span style="color:#90f3a5;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;text-decoration:line-through;">{creditor}</span>
                            </div>
                            <div style="color:#7df5b0;font-weight:700;font-family:'Syne',sans-serif;font-size:0.95rem;">₹0.00 ✔</div>
                        </div>
                    </div>"""
                elif is_picking_upi:
                    row_html = f"""
                    <div class="owe-card" style="flex-direction:column;align-items:flex-start;gap:0.35rem;border-color:rgba(255,200,80,0.4);">
                        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
                            <div>
                                <span style="color:#ff9a9a;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{debtor}</span>
                                <span style="color:#a9a9c8;margin:0 0.35rem;font-size:0.78rem;">→ pays →</span>
                                <span style="color:#90f3a5;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{creditor}</span>
                            </div>
                            <div style="color:#ffd200;font-weight:700;font-family:'Syne',sans-serif;font-size:0.95rem;">₹{amt:,.2f}</div>
                        </div>
                        <a href="{upi_base}"
                           style="text-decoration:none;display:inline-flex;align-items:center;gap:0.4rem;
                                  background:linear-gradient(90deg,#1a6e3c,#1a9e52);
                                  border-radius:8px;padding:0.35rem 0.85rem;
                                  font-size:0.78rem;font-weight:700;color:#fff;
                                  font-family:'Syne',sans-serif;white-space:nowrap;
                                  box-shadow:0 2px 10px rgba(26,158,82,0.4);letter-spacing:0.3px;">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="10" stroke="white" stroke-width="1.5"/>
                                <path d="M12 7v5l3 3" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
                                <path d="M8 12h8M14 9l3 3-3 3" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Open UPI App
                        </a>
                    </div>"""
                else:
                    row_html = f"""
                    <div class="owe-card" style="flex-direction:column;align-items:flex-start;gap:0.15rem;">
                        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
                            <div>
                                <span style="color:#ff9a9a;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{debtor}</span>
                                <span style="color:#a9a9c8;margin:0 0.35rem;font-size:0.78rem;">→ pays →</span>
                                <span style="color:#90f3a5;font-weight:600;font-family:'Syne',sans-serif;font-size:0.88rem;">{creditor}</span>
                            </div>
                            <div style="color:#ffd200;font-weight:700;font-family:'Syne',sans-serif;font-size:0.95rem;">₹{amt:,.2f}</div>
                        </div>
                    </div>"""

                # ── Layout: card | buttons ─────────────────────────────────────
                left_col, btn_col = st.columns([3, 1])
                with left_col:
                    st.markdown(row_html, unsafe_allow_html=True)
                with btn_col:
                    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                    if is_settled:
                        if st.button("↩ Undo", key=f"undo_{pair_key}", help="Mark as unsettled"):
                            st.session_state.settled_payments.discard(pair_key)
                            st.session_state.pending_settle = None
                            st.rerun()
                    elif is_picking_upi:
                        # "Done — mark settled" + cancel side by side
                        d1, d2 = st.columns(2)
                        with d1:
                            if st.button("✔ Done", key=f"done_{pair_key}", help="Mark as settled"):
                                st.session_state.settled_payments.add(pair_key)
                                st.session_state.pending_settle = None
                                st.rerun()
                        with d2:
                            if st.button("✖", key=f"cancel_{pair_key}", help="Cancel"):
                                st.session_state.pending_settle = None
                                st.rerun()
                    else:
                        if st.button("💰 Settle", key=f"settle_{pair_key}", help="Choose payment app"):
                            st.session_state.pending_settle = pair_key
                            st.rerun()

        grand = sum(e["amount"] for e in expenses)
        st.markdown(f'<div style="margin-top:1rem;text-align:right;color:#a9a9c8;font-size:0.82rem;">Total trip spend: <b style="color:#ffd200;font-family:\'Syne\',sans-serif;">₹{grand:,.2f}</b></div>', unsafe_allow_html=True)
