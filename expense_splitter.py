import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="Trip Splitter 🧳", page_icon="✈️", layout="wide")

# ─── CONFIG ────────────────────────────────────────────────────────────────
FRIENDS = ["Sanjeet", "Kundan", "Nayan", "Sanjay", "Govind", "Vivek"]
SHEET_NAME = "TripExpenseSplitter"
HEADERS = ["timestamp", "paid_by", "description", "amount", "split_with", "all_involved", "per_head"]

# ─── GOOGLE SHEETS ─────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def get_sheet():
    client = get_client()
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except:
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
    sheet.delete_rows(index + 2)  # +2 because header is row 1

def update_expense(sheet, index, exp):
    sheet.update(f"A{index+2}:G{index+2}", [[
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"]
    ]])

# ─── LOAD DATA ─────────────────────────────────────────────────────────────
sheet = get_sheet()
expenses = load_expenses(sheet)

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ─── UI ────────────────────────────────────────────────────────────────────
st.title("✈️ Trip Expense Splitter")

col1, col2 = st.columns(2)

# ── ADD / EDIT EXPENSE ─────────────────────────────────────────────────────
with col1:
    st.subheader("Add / Edit Expense")

    edit_mode = st.session_state.edit_index is not None

    if edit_mode:
        exp = expenses[st.session_state.edit_index]
        st.info("✏️ Editing Expense")
    else:
        exp = {"paid_by": FRIENDS[0], "description": "", "amount": 0.0, "split_with": FRIENDS[1:]}

    paid_by = st.selectbox("Paid by", FRIENDS, index=FRIENDS.index(exp["paid_by"]))
    description = st.text_input("Description", value=exp["description"])
    amount = st.number_input("Amount", value=float(exp["amount"]))
    split_with = st.multiselect("Split with", [f for f in FRIENDS if f != paid_by],
                               default=[f for f in exp["split_with"] if f != paid_by])

    if st.button("Save" if edit_mode else "Add"):
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

# ── EXPENSE LIST ────────────────────────────────────────────────────────────
with col2:
    st.subheader("Expenses")

    for i, exp in enumerate(expenses):
        colA, colB, colC = st.columns([6, 1, 1])

        with colA:
            st.markdown(f"**{exp['description']}** — ₹{exp['amount']} (Paid by {exp['paid_by']})")

        with colB:
            if st.button("✏️", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()

        with colC:
            if st.button("❌", key=f"del_{i}"):
                delete_expense(sheet, i)
                st.success("Deleted")
                st.rerun()

# ── BALANCE ────────────────────────────────────────────────────────────────
st.subheader("Balances")

balance = defaultdict(float)

for exp in expenses:
    for person in exp["all_involved"]:
        if person == exp["paid_by"]:
            balance[person] += exp["amount"] - exp["per_head"]
        else:
            balance[person] -= exp["per_head"]

for k, v in balance.items():
    st.write(f"{k}: ₹{v:.2f}")
