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
        # Fallback
        st.session_state["data"] = pd.DataFrame(columns=["patient_id","age","gender","diagnosis","admission_date","status","bill_amount","clinical_notes"])

# --- FEATURE: PRE-LOADED CHAT HISTORY ---
# This simulates "Memory" so the user doesn't see a blank screen on login
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome back, Dr. Demo. I have restored your session from **Yesterday, 14:00**."},
        {"role": "user", "content": "Show me the ICU capacity status."},
        {"role": "assistant", "content": "Currently, **4 patients** are in ICU (Cardiac, Stroke, Pneumonia). Bed capacity is at 85%."}
    ]

df = st.session_state["data"]

# --- INTELLIGENT SEARCH ENGINE (v4.0) ---
def execute_natural_language_query(prompt, data):
    prompt_lower = prompt.lower()
    sql_generated = ""
    result = None
    explanation = ""

    # --- STEP 1: KEYWORD CLEANING ---
    stop_phrases = ["show me patients with", "show me", "patients with", "who has", "search for", "find", "list", "the", "patients", "patient"]
    clean_search_term = prompt_lower
    for phrase in stop_phrases:
        clean_search_term = clean_search_term.replace(phrase, "")
    clean_search_term = clean_search_term.strip()

    # --- STEP 2: SYNONYM MAPPING (Smart Grouping) ---
    # This ensures "Heart Attack" finds "Cardiac" and "Sugar" finds "Diabetes"
    synonyms = {
        "heart attack": "cardiac",
        "sugar": "diabetes",
        "flu": "influenza",
        "broken": "fracture",
        "breathing": "lung",
        "cancer": "cancer" # Ensures generic 'cancer' search works
    }
    
    # If the user used a common term, we swap it for the medical term
    # But we ALSO keep the original term to search notes
    search_terms = [clean_search_term]
    for key, value in synonyms.items():
        if key in clean_search_term:
            search_terms.append(value)

    # --- STEP 3: EXECUTE SEARCH ---
    matched_rows = pd.DataFrame()
    
    if len(clean_search_term) > 1:
        # Search for ANY of the terms (Original OR Synonym)
        # e.g. "Heart Attack" searches for "Heart Attack" OR "Cardiac"
        query_mask = False
        for term in search_terms:
            mask = (
                data['diagnosis'].str.lower().str.contains(term, na=False) | 
                data['clinical_notes'].str.lower().str.contains(term, na=False)
            )
            query_mask = query_mask | mask
            
        matched_rows = data[query_mask]

    # --- STEP 4: GENERATE OUTPUT ---
    if "count" in prompt_lower and "all" in prompt_lower:
        sql_generated = "SELECT COUNT(*) FROM patients;"
        explanation = f"Total database size: {len(data)} records."
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
        # Success
        sql_generated = f"SELECT * FROM patients WHERE diagnosis LIKE '%{clean_search_term}%' OR synonyms match;"
        result = matched_rows
        explanation = f"Found {len(result)} records related to '{clean_search_term}'."

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
        # Strict Empty Result
        sql_generated = f"SELECT * FROM patients WHERE diagnosis = '{clean_search_term}';"
        result = pd.DataFrame()
        explanation = f"⚠️ No records found for '{clean_search_term}'. Please check the spelling."

    return sql_generated, result, explanation

# --- LOGIN SCREEN ---
def login_screen():
    st.markdown("<h1 style='text-align: center;'>⚡ VibeOps Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>NLP-to-SQL Healthcare Interface | v4.0 Production</p>", unsafe_allow_html=True)
    
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
    with st.sidebar:
        st.title("⚡ VibeOps")
        st.write("**Connected to:** Secure_Health_DB_v2")
        st.write(f"**Records Loaded:** {len(st.session_state['data'])}")
        
        st.markdown("---")
        st.markdown("### 🛠 Beta Stats")
        st.metric("Beta Cohort", "124", "Closed Access")
        
        st.markdown("---")
        
        with st.expander("➕ Admit / Update Patient File", expanded=False):
            with st.form("add_patient"):
                st.write("**Patient Intake Form**")
                new_pid = st.text_input("Patient ID", value=f"P-{1021 + len(st.session_state['data']) - 20}")
                
                c1, c2 = st.columns(2)
                with c1:
                    new_age = st.number_input("Age", 0, 120, 30)
                with c2:
                    new_gender = st.selectbox("Gender", ["M", "F", "Other"])
                
                new_diag = st.text_input("Primary Diagnosis", placeholder="Type ANY disease...")
                new_notes = st.text_area("Clinical Notes & History", height=100, placeholder="Enter detailed symptoms...")
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

    st.title("Intelligent Query Interface")
    st.markdown("Search by **Disease Group** (e.g. 'Cancer'), **Patient ID**, or **Symptoms**.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Try: 'Show me all cancer patients' or 'Who had a heart attack?'"):
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

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    main_interface()
