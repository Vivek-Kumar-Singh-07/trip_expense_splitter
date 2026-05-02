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

# ─── Google Sheets ────────────────────────────────────────────────────────────
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
                "timestamp": r["timestamp"],
                "paid_by": r["paid_by"],
                "description": r["description"],
                "amount": float(r["amount"]),
                "split_with": r["split_with"].split(","),
                "all_involved": r["all_involved"].split(","),
                "per_head": float(r["per_head"]),
            })
        except:
            continue
    return expenses

def save_expense(sheet, exp):
    sheet.append_row([
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ])

def delete_expense(sheet, index):
    sheet.delete_rows(index + 2)

def update_expense(sheet, index, exp):
    sheet.update(f"A{index+2}:G{index+2}", [[
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"]
    ]])

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

# ─── INIT ─────────────────────────────────────────────────────────────────────
sheet = get_sheet()
expenses = load_expenses(sheet)

if "show_all" not in st.session_state:
    st.session_state.show_all = False

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ─── HERO ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero"><h1>✈️ Trip Expense Splitter</h1><h2>🐯🌴 PENCH</h2></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.1], gap="large")

# ── LEFT ──────────────────────────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="section-label">💳 Add Expense</div>', unsafe_allow_html=True)

    edit_mode = st.session_state.edit_index is not None

    if edit_mode:
        exp = expenses[st.session_state.edit_index]
        st.info("✏️ Editing Expense")
    else:
        exp = {"paid_by": FRIENDS[0], "description": "", "amount": 0.0, "split_with": FRIENDS[1:]}

    paid_by = st.selectbox("Who paid?", FRIENDS, index=FRIENDS.index(exp["paid_by"]))
    description = st.text_input("What was it for?", value=exp["description"])
    amount = st.number_input("Amount (₹)", value=float(exp["amount"]), min_value=0.0)

    split_with = st.multiselect("Split with", [f for f in FRIENDS if f != paid_by],
                               default=[f for f in exp["split_with"] if f != paid_by])

    if st.button("💾 Save" if edit_mode else "➕ Add Expense"):
        all_involved = list(set([paid_by] + split_with))
        per_head = round(amount / len(all_involved), 2)

        new_exp = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "paid_by": paid_by,
            "description": description,
            "amount": amount,
            "split_with": split_with,
            "all_involved": all_involved,
            "per_head": per_head,
        }

        if edit_mode:
            update_expense(sheet, st.session_state.edit_index, new_exp)
            st.session_state.edit_index = None
            st.success("Updated!")
        else:
            save_expense(sheet, new_exp)
            st.success("Added!")

        st.rerun()

    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

    st.markdown('<div class="section-label">🧾 Expense Log</div>', unsafe_allow_html=True)

    for exp in expenses:
        idx = expenses.index(exp)

        col1, col2, col3 = st.columns([8, 1, 1])

        with col1:
            render_expense_card(exp, idx + 1)

        with col2:
            if st.button("✏️", key=f"edit_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()

        with col3:
            if st.button("❌", key=f"del_{idx}"):
                delete_expense(sheet, idx)
                st.rerun()

# ── RIGHT ─────────────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="section-label">📊 Who Owes What</div>', unsafe_allow_html=True)

    balance = defaultdict(float)

    for exp in expenses:
        for person in exp["all_involved"]:
            if person == exp["paid_by"]:
                balance[person] += exp["amount"] - exp["per_head"]
            else:
                balance[person] -= exp["per_head"]

    for k, v in balance.items():
        st.markdown(f"<div class='total-box'><b>{k}</b>: ₹{v:.2f}</div>", unsafe_allow_html=True)
