"""
Attendance Detailed Viewer - Streamlit Version
Reads AttendanceReport Excel + Main Roster + Leave Transactions
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ─── Page Config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Attendance Viewer",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* App background */
.stApp {
    background-color: #0f1117;
    color: #e8eaf0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #2a2f3e;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #7eb8f7;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-bottom: 1px solid #2a2f3e;
    padding-bottom: 6px;
    margin-top: 1.5rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #1a2035;
    border: 1px solid #2a3550;
    border-radius: 8px;
    padding: 1rem;
}
[data-testid="metric-container"] label {
    color: #7eb8f7 !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8eaf0 !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem !important;
    font-weight: 600;
}

/* Buttons */
.stButton > button {
    background: #1e3a5f;
    color: #7eb8f7;
    border: 1px solid #2a5298;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: #2a5298;
    color: #d0e8ff;
    border-color: #5588cc;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #161b27;
    border: 1px dashed #2a3550;
    border-radius: 8px;
    padding: 0.5rem;
}
[data-testid="stFileUploader"] label {
    color: #7eb8f7 !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Selectbox */
[data-testid="stSelectbox"] label {
    color: #7eb8f7 !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #2a3550;
    border-radius: 8px;
    overflow: hidden;
}

/* Success/error/info */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
}

/* Header */
.app-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
    color: #7eb8f7;
    letter-spacing: 0.04em;
    margin-bottom: 0.2rem;
}
.app-subheader {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.85rem;
    color: #5a6a8a;
    margin-bottom: 1.5rem;
}

/* Section labels */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #5a6a8a;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* Status badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
}
.badge-ok   { background: #0d2b1f; color: #4ade80; border: 1px solid #166534; }
.badge-none { background: #1a1a2e; color: #5a6a8a; border: 1px solid #2a2f3e; }

/* Divider */
hr { border-color: #2a2f3e !important; }
</style>
""", unsafe_allow_html=True)

# ─── Helper Functions ────────────────────────────────────────────────────────

def normalize_date(date_val):
    if pd.isna(date_val) or date_val == '' or date_val is None:
        return ''
    try:
        return pd.to_datetime(str(date_val).strip()).strftime('%m/%d/%Y')
    except:
        return str(date_val).strip()


def normalize_id(id_val):
    if pd.isna(id_val) or id_val == '' or id_val is None:
        return ''
    cleaned = str(id_val).strip()
    if cleaned.isdigit():
        return str(int(cleaned))
    return cleaned


# ─── Parsers ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def parse_attendance(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes), sheet_name='Detailed', header=None)
    values = df.values
    n_rows = len(values)

    name_mask = values[:, 0] == 'Name:'
    name_indices = np.where(name_mask)[0]

    records = []
    employees_dict = {}

    for idx in name_indices:
        if idx + 4 >= n_rows:
            continue

        name = str(values[idx, 1]).strip() if pd.notna(values[idx, 1]) else ''
        id_num = str(values[idx + 1, 1]).strip() if pd.notna(values[idx + 1, 1]) else ''
        days_present_total = str(values[idx + 2, 1]).strip() if pd.notna(values[idx + 2, 1]) else ''
        days_absent_total = str(values[idx + 3, 1]).strip() if pd.notna(values[idx + 3, 1]) else ''

        data_start = idx + 5
        if data_start >= n_rows:
            continue

        end_idx = data_start
        while end_idx < n_rows:
            first_cell = str(values[end_idx, 0]).strip() if pd.notna(values[end_idx, 0]) else ''
            if first_cell in ('Totals:', 'Name:', '') or (pd.isna(values[end_idx, 0]) and pd.isna(values[end_idx, 1])):
                break
            end_idx += 1

        if end_idx <= data_start:
            continue

        data_slice = values[data_start:end_idx]

        for row in data_slice:
            if pd.isna(row[0]):
                continue

            biologs = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ''
            is_absent = (biologs.upper() == 'NO LOGS' or biologs == '')

            record = {
                'Name': name,
                'ID Number': normalize_id(id_num),
                'Days Present': '0' if is_absent else '1',
                'Date': normalize_date(row[0]),
                'Day': str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else '',
                'Shift Type': str(row[2]).strip() if len(row) > 2 and pd.notna(row[2]) else '',
                'Shift': str(row[3]).strip() if len(row) > 3 and pd.notna(row[3]) else '',
                'Biologs': biologs,
                'Late': str(row[5]).strip() if len(row) > 5 and pd.notna(row[5]) else '',
                'Undertime': str(row[6]).strip() if len(row) > 6 and pd.notna(row[6]) else '',
                'Total Hours Worked': str(row[7]).strip() if len(row) > 7 and pd.notna(row[7]) else '',
                'Total Hours': str(row[8]).strip() if len(row) > 8 and pd.notna(row[8]) else ''
            }
            records.append(record)

        if records:
            emp_records = [r for r in records if r['Name'] == name]
            if emp_records:
                employees_dict[name] = {
                    'Name': name,
                    'ID Number': normalize_id(id_num),
                    'Days Present': days_present_total,
                    'Days Absent': days_absent_total,
                    'Records': emp_records
                }

    return records, employees_dict


@st.cache_data(show_spinner=False)
def parse_roster(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes), sheet_name='Headcount')
    df.columns = [str(c).strip() for c in df.columns]

    def find_col(target):
        t = target.lower().replace('/', '').replace('-', '').replace(' ', '')
        for c in df.columns:
            if c.lower().replace('/', '').replace('-', '').replace(' ', '') == t:
                return c
        return target

    cols = {
        'ecn': find_col('ECN'),
        'date': find_col('Date'),
        'project': find_col('Project'),
        'sub': find_col('Sub-Process'),
        'role': find_col('Role'),
        'super': find_col('Supervisor'),
        'bill': find_col('Billable/Buffer'),
        'tagging': find_col('Tagging')
    }

    df['_ecn'] = df[cols['ecn']].astype(str).str.strip().apply(normalize_id)
    df['_date'] = df[cols['date']].apply(normalize_date)

    valid = (df['_ecn'] != '') & (df['_date'] != '')
    df = df[valid]

    roster_dict = {}
    for _, row in df.iterrows():
        key = f"{row['_ecn']}|{row['_date']}"
        roster_dict[key] = {
            'Project': str(row[cols['project']]).strip() if pd.notna(row[cols['project']]) else '',
            'Sub-Process': str(row[cols['sub']]).strip() if pd.notna(row[cols['sub']]) else '',
            'Role': str(row[cols['role']]).strip() if pd.notna(row[cols['role']]) else '',
            'Supervisor': str(row[cols['super']]).strip() if pd.notna(row[cols['super']]) else '',
            'Billable/Buffer': str(row[cols['bill']]).strip() if pd.notna(row[cols['bill']]) else '',
            'Tagging': str(row[cols['tagging']]).strip() if pd.notna(row[cols['tagging']]) else ''
        }

    return roster_dict


@st.cache_data(show_spinner=False)
def parse_leave(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes), sheet_name='LEAVE TRANSACTIONS REPORT')
    df.columns = [str(c).strip() for c in df.columns]

    def find_col(target):
        t = target.lower().replace('/', '').replace('-', '').replace(' ', '')
        for c in df.columns:
            if c.lower().replace('/', '').replace('-', '').replace(' ', '') == t:
                return c
        return target

    cols = {
        'id': find_col('EmployeeID'),
        'type': find_col('LeaveTypeName'),
        'from': find_col('DateFrom'),
        'to': find_col('DateTo'),
        'status': find_col('LeaveStatus')
    }

    df = df[df[cols['status']].astype(str).str.strip().str.lower() == 'approved']

    leave_dict = {}
    for _, row in df.iterrows():
        emp_id = str(row[cols['id']]).strip()
        if not emp_id:
            continue

        norm_id = normalize_id(emp_id)
        is_sick = str(row[cols['type']]).strip().lower() == 'sick'

        try:
            d_from = pd.to_datetime(row[cols['from']])
            d_to = pd.to_datetime(row[cols['to']])
        except:
            continue

        dates = pd.date_range(d_from, d_to)
        for d in dates:
            nd = normalize_date(d)
            if nd:
                leave_dict[f"{norm_id}|{nd}"] = {'is_sick': is_sick}

    return leave_dict


# ─── Business Logic ──────────────────────────────────────────────────────────

def get_roster_info(roster_dict, id_number, date_str):
    key = f"{normalize_id(id_number)}|{date_str}"
    return roster_dict.get(key, {
        'Project': '', 'Sub-Process': '', 'Role': '',
        'Supervisor': '', 'Billable/Buffer': '', 'Tagging': ''
    })


def get_leave_info(leave_dict, id_number, date_str):
    key = f"{normalize_id(id_number)}|{date_str}"
    return leave_dict.get(key, None)


def is_scheduled(shift_value, days_present, biologs):
    if not shift_value:
        return '1'
    shift = str(shift_value).strip().upper()
    biologs_upper = str(biologs).strip().upper() if biologs else ''
    has_time = ' TO ' in shift and ('AM' in shift or 'PM' in shift)

    exact_non_scheduled = ['NOT YET HIRED', 'SEPARATED', 'ON LEAVE']
    for phrase in exact_non_scheduled:
        if shift == phrase:
            if phrase == 'ON LEAVE':
                if days_present == '1' or biologs_upper == 'NO LOGS':
                    return '1'
            return '0'

    if shift == 'REST DAY' or shift == 'REST DAY AND HOLIDAY':
        return '0'

    if has_time and ('REST DAY' in shift or 'REST DAY AND HOLIDAY' in shift):
        return '1'

    if has_time:
        return '1'

    for marker in ['NOT YET HIRED', 'SEPARATED', 'ON LEAVE', 'REST DAY', 'REST DAY AND HOLIDAY']:
        if marker in shift:
            return '0'

    return '1'


def merge_records(records, roster_dict, leave_dict):
    merged = []

    for record in records:
        id_num = record['ID Number']
        date_str = record['Date']
        days_present = record['Days Present']

        roster_info = get_roster_info(roster_dict, id_num, date_str) if roster_dict else {
            'Project': '', 'Sub-Process': '', 'Role': '',
            'Supervisor': '', 'Billable/Buffer': '', 'Tagging': ''
        }

        on_leave = '0'
        absent = '0'
        if leave_dict:
            leave_info = get_leave_info(leave_dict, id_num, date_str)
            if leave_info:
                if days_present == '1':
                    on_leave = '0'
                    absent = '0'
                else:
                    if leave_info['is_sick']:
                        absent = '1'
                    else:
                        on_leave = '1'

        sched = is_scheduled(record.get('Shift', ''), days_present, record.get('Biologs', ''))
        if sched == '0' and absent == '1':
            absent = '0'

        shift_upper = str(record.get('Shift', '')).strip().upper()
        biologs_upper = str(record.get('Biologs', '')).strip().upper()

        if shift_upper == 'REST DAY' and biologs_upper == 'NO LOGS' and on_leave == '1':
            on_leave = '0'

        if shift_upper == 'ON LEAVE' and biologs_upper == 'NO LOGS':
            on_leave = '0'
            absent = '1'

        if sched == '1' and biologs_upper == 'NO LOGS':
            is_rest_variant = (
                shift_upper == 'REST DAY' or
                shift_upper == 'REST DAY AND HOLIDAY' or
                'REST DAY AND HOLIDAY' in shift_upper or
                ('REST DAY' in shift_upper and ' TO ' in shift_upper and ('AM' in shift_upper or 'PM' in shift_upper))
            )
            is_on_leave_exact = shift_upper == 'ON LEAVE'
            if not is_rest_variant and not is_on_leave_exact:
                absent = '1'

        merged.append({
            **record,
            **roster_info,
            'On Leave': on_leave,
            'Absent': absent,
            'Is Scheduled': sched,
            'Tagging': roster_info.get('Tagging', '')
        })

    return merged


# ─── Export Helper ───────────────────────────────────────────────────────────

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = BytesIO()
    df_export = df.copy()

    int_cols = ['Days Present', 'Absent', 'On Leave', 'Is Scheduled']
    float_cols = ['Late', 'Undertime', 'Total Hours Worked', 'Total Hours']

    for c in int_cols:
        if c in df_export.columns:
            df_export[c] = pd.to_numeric(df_export[c], errors='coerce').fillna(0).astype(int)
    for c in float_cols:
        if c in df_export.columns:
            df_export[c] = pd.to_numeric(df_export[c], errors='coerce').fillna(0.0)

    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Merged')
    return out.getvalue()


# ─── Column Display Order ────────────────────────────────────────────────────

DISPLAY_COLS = [
    'Name', 'ID Number', 'Days Present', 'Absent',
    'Date', 'Day', 'Shift Type', 'Shift', 'Biologs',
    'Late', 'Undertime', 'Total Hours Worked', 'Total Hours',
    'Project', 'Sub-Process', 'Role', 'Supervisor', 'Billable/Buffer', 'Tagging',
    'On Leave', 'Is Scheduled'
]


# ─── Styling Function ────────────────────────────────────────────────────────

def get_column_config():
    """Return column_config for st.dataframe — works on all Streamlit versions."""
    return {
        'Name':              st.column_config.TextColumn('Name', width='medium'),
        'ID Number':         st.column_config.TextColumn('ID Number', width='small'),
        'Days Present':      st.column_config.NumberColumn('Days Present', width='small', format='%d'),
        'Absent':            st.column_config.NumberColumn('Absent', width='small', format='%d'),
        'Date':              st.column_config.TextColumn('Date', width='small'),
        'Day':               st.column_config.TextColumn('Day', width='small'),
        'Shift Type':        st.column_config.TextColumn('Shift Type', width='small'),
        'Shift':             st.column_config.TextColumn('Shift', width='large'),
        'Biologs':           st.column_config.TextColumn('Biologs', width='medium'),
        'Late':              st.column_config.TextColumn('Late', width='small'),
        'Undertime':         st.column_config.TextColumn('Undertime', width='small'),
        'Total Hours Worked':st.column_config.TextColumn('Total Hours Worked', width='small'),
        'Total Hours':       st.column_config.TextColumn('Total Hours', width='small'),
        'Project':           st.column_config.TextColumn('Project', width='medium'),
        'Sub-Process':       st.column_config.TextColumn('Sub-Process', width='medium'),
        'Role':              st.column_config.TextColumn('Role', width='medium'),
        'Supervisor':        st.column_config.TextColumn('Supervisor', width='medium'),
        'Billable/Buffer':   st.column_config.TextColumn('Billable/Buffer', width='small'),
        'Tagging':           st.column_config.TextColumn('Tagging', width='small'),
        'On Leave':          st.column_config.NumberColumn('On Leave', width='small', format='%d'),
        'Is Scheduled':      st.column_config.NumberColumn('Is Scheduled', width='small', format='%d'),
    }


# ─── Session State Init ──────────────────────────────────────────────────────

for key in ('attendance_records', 'employees_dict', 'roster_dict', 'leave_dict', 'merged_df'):
    if key not in st.session_state:
        st.session_state[key] = None


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="app-header">Attendance Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subheader">Attendance · Roster · Leave</div>', unsafe_allow_html=True)
    st.markdown('---')

    # ── Attendance File
    st.markdown('### 01 · Attendance')
    att_file = st.file_uploader(
        "Attendance Excel", type=['xlsx', 'xls'], key='att_upload',
        help="Must contain a 'Detailed' sheet"
    )
    if att_file:
        with st.spinner("Parsing attendance..."):
            try:
                records, emp_dict = parse_attendance(att_file.read())
                st.session_state.attendance_records = records
                st.session_state.employees_dict = emp_dict
                st.session_state.merged_df = None  # reset merged on new file
                st.success(f"✓ {len(records):,} records · {len(emp_dict)} employees")
            except Exception as e:
                st.error(f"Error: {e}")

    # ── Roster File
    st.markdown('### 02 · Roster')
    roster_file = st.file_uploader(
        "Roster Excel", type=['xlsx', 'xls'], key='roster_upload',
        help="Must contain a 'Headcount' sheet"
    )
    if roster_file:
        with st.spinner("Parsing roster..."):
            try:
                roster_dict = parse_roster(roster_file.read())
                st.session_state.roster_dict = roster_dict
                st.session_state.merged_df = None
                st.success(f"✓ {len(roster_dict):,} entries")
            except Exception as e:
                st.error(f"Error: {e}")

    # ── Leave File
    st.markdown('### 03 · Leave')
    leave_file = st.file_uploader(
        "Leave Excel", type=['xlsx', 'xls'], key='leave_upload',
        help="Must contain a 'LEAVE TRANSACTIONS REPORT' sheet"
    )
    if leave_file:
        with st.spinner("Parsing leave..."):
            try:
                leave_dict = parse_leave(leave_file.read())
                st.session_state.leave_dict = leave_dict
                st.session_state.merged_df = None
                st.success(f"✓ {len(leave_dict):,} daily leave entries")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('---')

    # ── Merge Button
    can_merge = st.session_state.attendance_records is not None
    if st.button("Merge All Data", disabled=not can_merge, use_container_width=True):
        with st.spinner("Merging..."):
            merged = merge_records(
                st.session_state.attendance_records,
                st.session_state.roster_dict or {},
                st.session_state.leave_dict or {}
            )
            available_cols = [c for c in DISPLAY_COLS if c in merged[0]] if merged else DISPLAY_COLS
            st.session_state.merged_df = pd.DataFrame(merged)[available_cols]
        st.success("Merge complete!")

    if not can_merge:
        st.caption("Load the Attendance file to enable merge.")

    st.markdown('---')
    st.markdown(
        '<div style="font-family:IBM Plex Mono;font-size:0.65rem;color:#3a4a6a;text-align:center;">'
        'Roster + Leave are optional.<br>Attendance is required.</div>',
        unsafe_allow_html=True
    )


# ─── Main Content ─────────────────────────────────────────────────────────────

# Header
st.markdown('<div class="app-header">Attendance Detailed Viewer</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subheader">Load files in the sidebar → Merge → Filter · Export</div>', unsafe_allow_html=True)

# File status row
c1, c2, c3 = st.columns(3)
with c1:
    loaded = st.session_state.attendance_records is not None
    badge = 'badge-ok' if loaded else 'badge-none'
    label = f"{len(st.session_state.attendance_records):,} records" if loaded else "not loaded"
    st.markdown(f'<div class="section-label">Attendance</div><span class="badge {badge}">{"✓ " + label if loaded else "✗ " + label}</span>', unsafe_allow_html=True)
with c2:
    loaded = st.session_state.roster_dict is not None
    badge = 'badge-ok' if loaded else 'badge-none'
    label = f"{len(st.session_state.roster_dict):,} entries" if loaded else "not loaded"
    st.markdown(f'<div class="section-label">Roster</div><span class="badge {badge}">{"✓ " + label if loaded else "○ " + label}</span>', unsafe_allow_html=True)
with c3:
    loaded = st.session_state.leave_dict is not None
    badge = 'badge-ok' if loaded else 'badge-none'
    label = f"{len(st.session_state.leave_dict):,} entries" if loaded else "not loaded"
    st.markdown(f'<div class="section-label">Leave</div><span class="badge {badge}">{"✓ " + label if loaded else "○ " + label}</span>', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# ── If merged data is available, show it
if st.session_state.merged_df is not None:
    df = st.session_state.merged_df

    # ── Metrics
    total_records = len(df)
    total_employees = df['Name'].nunique() if 'Name' in df.columns else 0
    total_absent = int(df['Absent'].astype(str).eq('1').sum()) if 'Absent' in df.columns else 0
    total_on_leave = int(df['On Leave'].astype(str).eq('1').sum()) if 'On Leave' in df.columns else 0
    roster_matched = int((df['Project'].astype(str) != '').sum()) if 'Project' in df.columns else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Records", f"{total_records:,}")
    m2.metric("Employees", f"{total_employees:,}")
    m3.metric("Absent Days", f"{total_absent:,}")
    m4.metric("On Leave Days", f"{total_on_leave:,}")
    m5.metric("Roster Matches", f"{roster_matched:,}")

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Export Button
    view_df = df
    excel_bytes = to_excel_bytes(view_df)
    st.download_button(
        label="⬇ Export Excel",
        data=excel_bytes,
        file_name="Attendance_Merged.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ── Date range info
    if 'Date' in view_df.columns:
        dates = view_df['Date'][view_df['Date'] != ''].tolist()
        if dates:
            st.caption(f"📅 Date range: **{dates[0]}** → **{dates[-1]}**  ·  Showing **{len(view_df):,}** records")

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Data Table
    st.markdown('<div class="section-label">Records</div>', unsafe_allow_html=True)
    st.dataframe(
        view_df,
        use_container_width=True,
        height=520,
        hide_index=True,
        column_config=get_column_config(),
    )

else:
    # ── Empty state
    st.markdown('<br>' * 3, unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align:center; padding: 4rem 2rem;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:3rem; color:#2a3550; margin-bottom:1rem;">⬤ ◯ ◯</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:1rem; color:#3a4a6a; margin-bottom:0.5rem;">No data merged yet</div>
            <div style="font-family:'IBM Plex Sans',sans-serif; font-size:0.85rem; color:#2a3550;">
                Upload files in the sidebar, then click <strong style="color:#5a7ab7;">Merge All Data</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )