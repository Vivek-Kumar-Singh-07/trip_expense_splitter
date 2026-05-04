import streamlit as st
import gspread
import hashlib
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

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: transparent !important;
}

.main .block-container { position:relative; z-index:1; }
header { position:relative; z-index:1; }

.hero {
    text-align:center; padding:1rem 1rem 0.6rem;
    margin-bottom:0.6rem; position:relative; z-index:1;
}
.hero h1 {
    font-size:1.9rem; font-weight:800;
    background:linear-gradient(90deg,#ffb347,#ffd200,#ff8c00);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; letter-spacing:-0.5px; margin-bottom:0;
    line-height:1.2; white-space:normal; word-break:keep-all;
}
.hero h2 { font-size:0.95rem; color:#d4b87a; font-weight:400; margin-top:0.15rem; letter-spacing:1px; }
.hero-user { font-size:0.8rem; color:#90f3a5; font-family:'Syne',sans-serif; font-weight:600; margin-top:0.3rem; letter-spacing:0.5px; }

.login-box {
    background: rgba(20,35,20,0.75);
    border: 1px solid rgba(210,160,60,0.3);
    border-radius: 16px; padding: 2rem 1.8rem;
    backdrop-filter: blur(8px); max-width: 380px; margin: 2rem auto;
}
.pwd-change-box {
    background: rgba(20,35,20,0.75);
    border: 1px solid rgba(255,200,60,0.45);
    border-radius: 16px; padding: 2rem 1.8rem;
    backdrop-filter: blur(8px); max-width: 380px; margin: 2rem auto;
}

.expense-card { background:rgba(180,100,10,0.1); border:1px solid rgba(220,150,50,0.25); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.5rem; backdrop-filter:blur(4px); }
.owe-card { background:rgba(200,60,60,0.08); border:1px solid rgba(220,100,100,0.22); border-radius:10px; padding:0.55rem 0.9rem; margin-bottom:0.45rem; display:flex; justify-content:space-between; align-items:center; backdrop-filter:blur(4px); }
.settled { background:rgba(50,180,100,0.1); border:1px solid rgba(80,220,130,0.3); border-radius:10px; padding:0.9rem; text-align:center; color:#7df5b0; font-family:'Syne',sans-serif; font-weight:600; font-size:1rem; }
.section-label { font-family:'Syne',sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#d4a84b; margin-bottom:0.6rem; }
.total-box { background:rgba(30,50,30,0.35); border:1px solid rgba(180,140,60,0.2); border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.45rem; backdrop-filter:blur(4px); }
.fancy-divider { border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(210,160,60,0.5),transparent); margin:1rem 0; }
.count-badge { background:rgba(210,160,60,0.2); border:1px solid rgba(210,160,60,0.4); border-radius:50px; padding:0.1rem 0.5rem; font-size:0.7rem; color:#ffd97d; font-family:'Syne',sans-serif; font-weight:700; margin-left:0.4rem; }

.stButton > button { background:linear-gradient(90deg,#b45a00,#e07b00); color:#fff; font-family:'Syne',sans-serif; font-weight:700; border:none; border-radius:10px; padding:0.5rem 1.2rem; font-size:0.95rem; width:100%; }

div[data-testid="column"] .stButton > button {
    padding: 0.2rem 0.55rem; font-size: 1rem; border-radius: 7px;
    background: rgba(255,255,255,0.07); color: #e8d5a0;
    border: 1px solid rgba(210,160,60,0.25); width: auto; min-width: unset;
}

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
    .login-box, .pwd-change-box { margin: 1.2rem auto; padding: 1.4rem 1rem; }
}

.main .block-container { padding-top: 0.8rem !important; padding-bottom: 0.8rem !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.25rem !important; }

div[data-testid="column"] .stButton > button {
    padding: 0.05rem 0.3rem !important; font-size: 0.8rem !important;
    border-radius: 6px !important; background: rgba(255,255,255,0.07) !important;
    color: #e8d5a0 !important; border: 1px solid rgba(210,160,60,0.2) !important;
    width: auto !important; min-width: unset !important;
    line-height: 1.4 !important; height: auto !important; margin-top: 0.3rem !important;
}

button[kind="secondary"][data-testid*="settle_"],
button[kind="secondary"][data-testid*="undo_"],
div[data-testid="column"] button[data-testid*="settle"],
div[data-testid="column"] button[data-testid*="undo"] {
    padding: 0.12rem 0.45rem !important; font-size: 0.72rem !important;
    border-radius: 50px !important; background: rgba(255,200,50,0.12) !important;
    color: #ffd97d !important; border: 1px solid rgba(210,160,60,0.35) !important;
    width: auto !important; min-width: unset !important;
    line-height: 1.5 !important; height: auto !important; margin-top: 0.55rem !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Config ────────────────────────────────────────────────────────────────────
FRIENDS    = ["Sanjeet", "Kundan", "Nayan", "Sanjay", "Govind", "Vivek"]
SHEET_NAME = "TripExpenseSplitter"
HEADERS    = ["timestamp", "paid_by", "description", "amount", "split_with", "all_involved", "per_head"]
IST        = timezone(timedelta(hours=5, minutes=30))

UPI_IDS = {
    "Sanjeet": "sanjeet@upi",
    "Kundan":  "kundan@upi",
    "Nayan":   "nayan@upi",
    "Sanjay":  "sanjay@upi",
    "Govind":  "govind@upi",
    "Vivek":   "vivek@upi",
}

# ─── Helpers ───────────────────────────────────────────────────────────────────
def hash_pwd(pwd: str) -> str:
    """SHA-256 hash — passwords are never stored as plain text in the sheet."""
    return hashlib.sha256(pwd.strip().encode()).hexdigest()

# ─── Google Sheets client (cached) ─────────────────────────────────────────────
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# ─── Expense sheet (Tab 1) ─────────────────────────────────────────────────────
def get_sheet():
    client = get_client()
    try:
        spreadsheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
    try:
        sheet = spreadsheet.sheet1
    except Exception:
        sheet = spreadsheet.add_worksheet("Expenses", 1000, 10)
    if sheet.row_values(1) != HEADERS:
        sheet.insert_row(HEADERS, 1)
    return sheet

# ─── Password sheet (Tab 2) ────────────────────────────────────────────────────
def get_pwd_sheet():
    """
    Tab called 'Passwords'. Columns: name | pwd_hash | is_default
    is_default = "yes"  →  user has never changed from the default password
    is_default = "no"   →  user has set their own password

    FIX: Always checks for missing friends and seeds them,
         not just on first creation. This prevents 'User not found'
         if the sheet existed but was empty or partially seeded.
    """
    client      = get_client()
    spreadsheet = client.open(SHEET_NAME)

    try:
        pwd_sheet = spreadsheet.worksheet("Passwords")
    except gspread.WorksheetNotFound:
        pwd_sheet = spreadsheet.add_worksheet("Passwords", 20, 3)
        pwd_sheet.append_row(["name", "pwd_hash", "is_default"])

    # Always ensure every friend has a row — seed any that are missing
    records      = pwd_sheet.get_all_records()
    existing     = {r["name"] for r in records}
    default_hash = hash_pwd(st.secrets["DEFAULT_PASSWORD"])

    for friend in FRIENDS:
        if friend not in existing:
            pwd_sheet.append_row([friend, default_hash, "yes"])

    return pwd_sheet


def load_pwd_map(pwd_sheet):
    """Returns { name: { "pwd_hash": str, "is_default": bool } }"""
    pwd_map = {}
    for row in pwd_sheet.get_all_records():
        try:
            pwd_map[row["name"]] = {
                "pwd_hash":   row["pwd_hash"],
                "is_default": row["is_default"] == "yes",
            }
        except Exception:
            continue
    return pwd_map


def update_password(pwd_sheet, name: str, new_pwd: str):
    """Update a user's hashed password and mark is_default = no."""
    records = pwd_sheet.get_all_records()
    for i, row in enumerate(records):
        if row["name"] == name:
            row_num = i + 2   # +1 header, +1 for 1-based indexing
            pwd_sheet.update(f"B{row_num}:C{row_num}", [[hash_pwd(new_pwd), "no"]])
            return
    # Fallback: user missing from sheet — add them
    pwd_sheet.append_row([name, hash_pwd(new_pwd), "no"])

# ─── Session State defaults ────────────────────────────────────────────────────
for _k, _v in {
    "authenticated":    False,
    "current_user":     None,
    "must_change_pwd":  False,
    "show_all":         False,
    "editing_idx":      None,
    "form_reset_key":   0,
    "settled_payments": set(),
    "pending_settle":   None,
    "pending_delete":   None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─── Shared login header ────────────────────────────────────────────────────────
def render_login_header():
    st.markdown("""
    <div style="text-align:center;padding-top:1.5rem;">
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;
                    background:linear-gradient(90deg,#ffb347,#ffd200,#ff8c00);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;margin-bottom:0.2rem;">
            🐯 Trip Expense Tracker
        </div>
        <div style="color:#d4b87a;font-size:0.9rem;letter-spacing:2px;margin-bottom:0.2rem;">
            PENCH WILDLIFE TRIP
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — Login
# ══════════════════════════════════════════════════════════════════════════════
def show_login(pwd_sheet):
    render_login_header()
    st.markdown(
        '<div style="color:#a9a9c8;font-size:0.78rem;text-align:center;margin-bottom:1rem;">'
        'Sign in to access the trip expenses</div>',
        unsafe_allow_html=True
    )
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        name = st.selectbox("👤 Who are you?", ["— select your name —"] + FRIENDS, key="login_name")
        pwd  = st.text_input("🔑 Password", type="password", placeholder="Enter your password…", key="login_pwd")
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("Enter the Trip →", use_container_width=True, key="login_btn"):
            if name == "— select your name —":
                st.error("Please select your name.")
            else:
                pwd_map = load_pwd_map(pwd_sheet)
                if name not in pwd_map:
                    st.error("❌ User not found. Contact the trip admin.")
                elif hash_pwd(pwd) != pwd_map[name]["pwd_hash"]:
                    st.error("❌ Wrong password!")
                else:
                    st.session_state.authenticated   = True
                    st.session_state.current_user    = name
                    st.session_state.must_change_pwd = pwd_map[name]["is_default"]
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — First-login / voluntary password change
# ══════════════════════════════════════════════════════════════════════════════
def show_change_password(pwd_sheet, forced: bool = True):
    render_login_header()
    name = st.session_state.current_user

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown('<div class="pwd-change-box">', unsafe_allow_html=True)

        if forced:
            st.markdown(f"""
            <div style="margin-bottom:1rem;">
                <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ffd200;margin-bottom:0.3rem;">
                    👋 Welcome, {name}!
                </div>
                <div style="font-size:0.82rem;color:#d4b87a;line-height:1.6;">
                    You're using the <b>default password</b>.<br>
                    Set your own personal password to continue.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="margin-bottom:1rem;">
                <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ffd200;margin-bottom:0.3rem;">
                    🔑 Change Password — {name}
                </div>
            </div>
            """, unsafe_allow_html=True)

        new_pwd  = st.text_input("New password", type="password", placeholder="Min 4 characters", key="new_pwd")
        conf_pwd = st.text_input("Confirm password", type="password", placeholder="Repeat new password", key="conf_pwd")
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        if forced:
            save_clicked   = st.button("Set My Password →", use_container_width=True, key="set_pwd_btn")
            cancel_clicked = False
        else:
            col_s, col_c = st.columns(2)
            with col_s:
                save_clicked   = st.button("💾 Save", use_container_width=True, key="set_pwd_btn")
            with col_c:
                cancel_clicked = st.button("✖ Cancel", use_container_width=True, key="cancel_pwd_btn")

        if cancel_clicked:
            st.session_state.must_change_pwd = False
            st.rerun()

        if save_clicked:
            if len(new_pwd.strip()) < 4:
                st.error("Password must be at least 4 characters.")
            elif new_pwd != conf_pwd:
                st.error("Passwords don't match — try again.")
            elif new_pwd.strip() == st.secrets["DEFAULT_PASSWORD"]:
                st.error("Please choose a different password from the default one.")
            else:
                update_password(pwd_sheet, name, new_pwd.strip())
                st.session_state.must_change_pwd = False
                st.success("✅ Password updated! Loading your trip…")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOOT — connect pwd sheet first, then run auth gates, then load expenses
# ══════════════════════════════════════════════════════════════════════════════
try:
    pwd_sheet = get_pwd_sheet()
    connected = True
except Exception as e:
    st.error(f"❌ Google Sheets connection failed: {e}")
    st.stop()

# Gate 1 — not logged in → show login screen
if not st.session_state.authenticated:
    show_login(pwd_sheet)
    st.stop()

# Gate 2 — logged in but still on default password → force password change
# This happens BEFORE any expense sheet is loaded, so the user never sees the app
if st.session_state.must_change_pwd:
    show_change_password(pwd_sheet, forced=True)
    st.stop()

# ─── Only now connect expense sheet & load data ────────────────────────────────
try:
    sheet = get_sheet()
except Exception as e:
    st.error(f"❌ Could not load expense sheet: {e}")
    st.stop()

# ─── Load / Save helpers ───────────────────────────────────────────────────────
def load_expenses(sheet):
    rows = []
    for r in sheet.get_all_records():
        try:
            rows.append({
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
    return rows

def save_expense(sheet, exp):
    sheet.append_row([
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ])

def update_expense_in_sheet(sheet, row_index, exp):
    sheet.update(f"A{row_index}:G{row_index}", [[
        exp["timestamp"], exp["paid_by"], exp["description"], exp["amount"],
        ",".join(exp["split_with"]), ",".join(exp["all_involved"]), exp["per_head"],
    ]])

def delete_expense_from_sheet(sheet, row_index):
    sheet.delete_rows(row_index)

expenses     = load_expenses(sheet)
current_user = st.session_state.current_user

# ─── Hero ──────────────────────────────────────────────────────────────────────
hero_col, action_col = st.columns([5, 1])
with hero_col:
    st.markdown(
        f'<div class="hero">'
        f'<h1>Trip Expense Tracker</h1>'
        f'<h2>🐯🌴 PENCH WILDLIFE TRIP</h2>'
        f'<div class="hero-user">👤 {current_user}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with action_col:
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    if st.button("🔑 Pwd", help="Change your password"):
        st.session_state.must_change_pwd = True
        st.rerun()
    if st.button("🚪 Out", help="Logout"):
        for key in ["authenticated", "current_user", "must_change_pwd", "editing_idx",
                    "pending_delete", "pending_settle", "settled_payments", "show_all", "form_reset_key"]:
            st.session_state.pop(key, None)
        st.rerun()

col_left, col_right = st.columns([1, 1.1], gap="large")

# ══════════════════════════════════════════════════
# LEFT — Add / Edit Expense + Log
# ══════════════════════════════════════════════════
with col_left:

    is_editing = st.session_state.editing_idx is not None
    edit_exp   = expenses[st.session_state.editing_idx] if is_editing else None
    fk         = st.session_state.form_reset_key

    st.markdown(
        f'<div class="section-label">{"✏️ Edit Expense" if is_editing else "💳 Add Expense"}</div>',
        unsafe_allow_html=True
    )

    default_paid_by_idx = FRIENDS.index(current_user) if current_user in FRIENDS else 0

    paid_by = st.selectbox(
        "Who paid?", FRIENDS,
        index=FRIENDS.index(edit_exp["paid_by"]) if is_editing else default_paid_by_idx,
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
                    update_expense_in_sheet(sheet, st.session_state.editing_idx + 2, updated)
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
                st.session_state.show_all      = False
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
        showing        = list(reversed(filtered if st.session_state.show_all else filtered[-5:]))

        label_suffix = f" · {filter_person}" if filter_person != "All" else ""
        badge_text   = f"All {total_filtered}" if st.session_state.show_all else f"Last 5 of {total_filtered}"
        st.markdown(
            f'<div class="section-label">🧾 Expense Log{label_suffix} <span class="count-badge">{badge_text}</span></div>',
            unsafe_allow_html=True
        )

        if not filtered:
            st.markdown(f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.7rem;color:#a9a9c8;text-align:center;font-size:0.85rem;">No expenses for {filter_person}.</div>', unsafe_allow_html=True)
        else:
            qp = st.query_params
            if "edit" in qp:
                try:
                    idx = int(qp["edit"])
                    if expenses[idx]["paid_by"] == current_user:
                        st.session_state.editing_idx = idx
                    else:
                        st.warning(f"⛔ Only {expenses[idx]['paid_by']} can edit that expense.")
                except Exception:
                    pass
                st.query_params.clear()
                st.rerun()

            for orig_idx, exp in showing:
                is_confirm_delete = st.session_state.pending_delete == orig_idx
                is_owner          = (current_user == exp["paid_by"])

                if is_confirm_delete:
                    st.markdown(f"""
                    <div class="expense-card" style="border-color:rgba(255,80,80,0.5);background:rgba(200,40,40,0.12);">
                        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.4rem;">
                            <div style="flex:1;min-width:0;">
                                <div style="font-family:'Syne',sans-serif;font-weight:600;color:#ffd200;font-size:0.82rem;line-height:1.3;">#{orig_idx+1} {exp['description']}</div>
                                <div style="font-size:0.72rem;color:#ff9a9a;font-family:'Syne',sans-serif;font-weight:600;margin-top:0.2rem;">Delete this expense?</div>
                            </div>
                            <div style="font-size:0.95rem;font-weight:700;color:#f7971e;font-family:'Syne',sans-serif;white-space:nowrap;">₹{exp['amount']:,.2f}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🗑️ Yes, delete", key=f"confirm_del_{orig_idx}"):
                            delete_expense_from_sheet(sheet, orig_idx + 2)
                            st.session_state.pending_delete = None
                            st.session_state.editing_idx    = None
                            st.rerun()
                    with c2:
                        if st.button("✖ Cancel", key=f"cancel_del_{orig_idx}"):
                            st.session_state.pending_delete = None
                            st.rerun()
                else:
                    if is_owner:
                        edit_btn_html = (
                            f'<a href="?edit={orig_idx}" target="_self" '
                            f'style="text-decoration:none;background:rgba(255,255,255,0.08);'
                            f'border:1px solid rgba(210,160,60,0.3);border-radius:6px;'
                            f'padding:0.15rem 0.4rem;font-size:0.85rem;cursor:pointer;" '
                            f'title="Edit your expense">✏️</a>'
                        )
                    else:
                        payer         = exp["paid_by"]
                        edit_btn_html = (
                            f'<span style="font-size:0.85rem;opacity:0.18;cursor:not-allowed;" '
                            f'title="Only {payer} can edit this">✏️</span>'
                        )

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
                                <div style="display:flex;gap:0.3rem;">{edit_btn_html}</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    if is_owner:
                        _, del_col = st.columns([5, 1])
                        with del_col:
                            if st.button("🗑️", key=f"del_{orig_idx}", help="Delete your expense"):
                                st.session_state.pending_delete = orig_idx
                                st.rerun()

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
                pair_key       = f"{debtor}|{creditor}"
                is_settled     = pair_key in st.session_state.settled_payments
                is_picking_upi = st.session_state.pending_settle == pair_key

                amt_str   = f"{amt:.2f}"
                payee_upi = UPI_IDS.get(creditor, "")
                upi_base  = f"upi://pay?pa={payee_upi}&pn={creditor}&am={amt_str}&cu=INR&tn=Trip+settlement"

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
                                  background:linear-gradient(90deg,#1a6e3c,#1a9e52);border-radius:8px;
                                  padding:0.35rem 0.85rem;font-size:0.78rem;font-weight:700;color:#fff;
                                  font-family:'Syne',sans-serif;white-space:nowrap;
                                  box-shadow:0 2px 10px rgba(26,158,82,0.4);letter-spacing:0.3px;">
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
                        if st.button("💰 Settle", key=f"settle_{pair_key}", help="Pay via UPI"):
                            st.session_state.pending_settle = pair_key
                            st.rerun()

        grand = sum(e["amount"] for e in expenses)
        st.markdown(f'<div style="margin-top:1rem;text-align:right;color:#a9a9c8;font-size:0.82rem;">Total trip spend: <b style="color:#ffd200;font-family:\'Syne\',sans-serif;">₹{grand:,.2f}</b></div>', unsafe_allow_html=True)
