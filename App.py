import streamlit as st
import pandas as pd
import time
import re
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VibeOps Systems", page_icon="⚡", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "data" not in st.session_state:
    try:
        st.session_state["data"] = pd.read_csv("patients_dummy.csv")
    except:
        # Fallback with empty structure
        st.session_state["data"] = pd.DataFrame(columns=["patient_id","age","gender","diagnosis","admission_date","status","bill_amount","clinical_notes"])

if "messages" not in st.session_state:
    st.session_state.messages = []

df = st.session_state["data"]

# --- ADVANCED LOGIC ENGINE (v3.1 - Full Text Search) ---
def execute_natural_language_query(prompt, data):
    prompt_lower = prompt.lower()
    sql_generated = ""
    result = None
    explanation = ""

    # DYNAMIC SEARCH: Scans Diagnosis AND Clinical Notes
    # This allows searching for symptoms ("fever") not just disease names
    
    # 1. Search for specific terms in Diagnosis OR Notes
    matched_rows = data[
        data['diagnosis'].str.lower().str.contains(prompt_lower, na=False) | 
        data['clinical_notes'].str.lower().str.contains(prompt_lower, na=False)
    ]

    # LOGIC BRANCHES
    if "count" in prompt_lower:
        sql_generated = "SELECT COUNT(*) FROM patients;"
        explanation = f"Total count: {len(data)} patients in current cohort."
        result = None 
        
    elif "average" in prompt_lower:
        if "bill" in prompt_lower:
            avg = data['bill_amount'].mean()
            sql_generated = "SELECT AVG(bill_amount) FROM patients;"
            explanation = f"Average Billing Amount: ${avg:.2f}"
            result = None
        elif "age" in prompt_lower:
            avg = data['age'].mean()
            sql_generated = "SELECT AVG(age) FROM patients;"
            explanation = f"Average Patient Age: {avg:.1f} years"
            result = None
            
    elif not matched_rows.empty:
        # If we found matches in diagnosis or notes
        # We extract the key term from the prompt for the SQL display
        key_term = prompt.replace("Show me patients with ", "").replace("Search for ", "")
        sql_generated = f"SELECT * FROM patients WHERE diagnosis LIKE '%{key_term}%' OR clinical_notes LIKE '%{key_term}%';"
        result = matched_rows
        explanation = f"Query executed. Found {len(result)} records matching keywords in Diagnosis or Clinical Notes."

    elif "p-" in prompt_lower:
        match = re.search(r"p-\d+", prompt_lower)
        if match:
            pid = match.group(0).upper()
            result = data[data['patient_id'] == pid]
            sql_generated = f"SELECT * FROM patients WHERE patient_id = '{pid}';"
            explanation = f"Record found for Patient ID: {pid}"
        else:
            result = pd.DataFrame()
            explanation = "No ID matched."

    else:
        # Fallback
        sql_generated = "SELECT * FROM patients ORDER BY admission_date DESC LIMIT 5;"
        result = data.tail(5)
        explanation = "Could not map specific intent. Displaying most recent records."

    return sql_generated, result, explanation

# --- LOGIN SCREEN ---
def login_screen():
    st.markdown("<h1 style='text-align: center;'>⚡ VibeOps Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>NLP-to-SQL Healthcare Interface | v3.1 EHR Build</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("🔒 Access Restricted: Beta testers only.")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if user == "demo" and pw == "harvard2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials.")

# --- MAIN DASHBOARD ---
def main_interface():
    # --- SIDEBAR: DOCTOR'S PORTAL ---
    with st.sidebar:
        st.title("⚡ VibeOps")
        st.write("**Connected to:** Secure_Health_DB_v2")
        st.write(f"**Records Loaded:** {len(st.session_state['data'])}")
        
        st.markdown("---")
        st.markdown("### 🛠 Beta Stats")
        st.metric("Beta Cohort", "124", "Closed Access")
        
        st.markdown("---")
        
        # --- DOCTOR ADMISSION FORM ---
        with st.expander("➕ Admit / Update Patient File", expanded=False):
            with st.form("add_patient"):
                st.write("**Patient Intake Form**")
                new_pid = st.text_input("Patient ID", value=f"P-{1021 + len(st.session_state['data']) - 20}")
                
                c1, c2 = st.columns(2)
                with c1:
                    new_age = st.number_input("Age", 0, 120, 30)
                with c2:
                    new_gender = st.selectbox("Gender", ["M", "F", "Other"])
                
                # FREE TEXT INPUTS FOR UNLIMITED DISEASE SUPPORT
                new_diag = st.text_input("Primary Diagnosis", placeholder="Type ANY disease (e.g. Zika, Ebola...)")
                
                # DETAILED CLINICAL NOTES
                new_notes = st.text_area("Clinical Notes & History", height=100, placeholder="Enter detailed symptoms, history, vitals, prescriptions...")
                
                new_status = st.selectbox("Status", ["Active", "ICU", "Outpatient", "Discharged"])
                new_bill = st.number_input("Est. Bill ($)", value=1000.0)
                
                submitted = st.form_submit_button("Save to Registry")
                if submitted:
                    new_row = {
                        "patient_id": new_pid,
                        "age": new_age,
                        "gender": new_gender,
                        "diagnosis": new_diag,
                        "admission_date": str(datetime.date.today()),
                        "status": new_status,
                        "bill_amount": new_bill,
                        "clinical_notes": new_notes
                    }
                    st.session_state["data"] = pd.concat([st.session_state["data"], pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"File created for {new_pid}")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- MAIN CHAT ---
    st.title("Intelligent Query Interface")
    st.markdown("Search by **Disease**, **Patient ID**, or **Symptoms in Notes**.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Try: 'Show me patients with fever' or 'Who has a broken bone?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("Analyzing Clinical Notes...", expanded=True) as status:
                time.sleep(0.6)
                status.update(label="Query Executed", state="complete", expanded=False)
            
            sql, res_df, expl = execute_natural_language_query(prompt, st.session_state["data"])

            st.code(sql, language="sql")
            st.write(f"**System:** {expl}")
            
            if res_df is not None and not res_df.empty:
                st.dataframe(res_df, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": f"Executed: `{sql}`"})

# --- APP CONTROL ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    main_interface()
