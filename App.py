import streamlit as st
import pandas as pd
import time
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="VibeOps Systems", page_icon="⚡", layout="wide")

# --- MOCK DATA LOADING ---
@st.cache_data
def load_data():
    try:
        # Tries to load the CSV you created
        return pd.read_csv("patients_dummy.csv")
    except:
        return pd.DataFrame({
            "patient_id": ["P-001", "P-002"],
            "diagnosis": ["Flu", "Covid"],
            "status": ["Active", "Discharged"],
            "bill_amount": [1000, 2000]
        })

df = load_data()

# --- REAL LOGIC ENGINE ---
def execute_natural_language_query(prompt, data):
    """
    This function simulates an NLP-to-SQL parser.
    It uses Python keyword matching to generate 'real' filters.
    """
    prompt_lower = prompt.lower()
    sql_generated = ""
    result = None
    explanation = ""

    # LOGIC 1: SEARCH BY DIAGNOSIS (Dynamic)
    # We scan the unique diagnosis list to see if the user mentioned one
    unique_diagnoses = data['diagnosis'].unique()
    found_diagnosis = None
    for d in unique_diagnoses:
        if d.lower() in prompt_lower:
            found_diagnosis = d
            break
    
    if found_diagnosis:
        sql_generated = f"SELECT * FROM patients WHERE diagnosis = '{found_diagnosis}';"
        result = data[data['diagnosis'] == found_diagnosis]
        explanation = f"Query executed. Found {len(result)} records matching '{found_diagnosis}'."

    # LOGIC 2: SEARCH BY ID
    elif "p-" in prompt_lower:
        # Extract ID using Regex
        match = re.search(r"p-\d+", prompt_lower)
        if match:
            pid = match.group(0).upper() # Normalize to P-1001
            # Actually check if ID exists
            if pid in data['patient_id'].values:
                sql_generated = f"SELECT * FROM patients WHERE patient_id = '{pid}';"
                result = data[data['patient_id'] == pid]
                explanation = f"Record found for Patient ID: {pid}"
            else:
                sql_generated = f"SELECT * FROM patients WHERE patient_id = '{pid}';"
                result = pd.DataFrame() # Empty
                explanation = f"No patient found with ID: {pid}"

    # LOGIC 3: AGGREGATIONS (Math)
    elif "count" in prompt_lower or "how many" in prompt_lower:
        sql_generated = "SELECT COUNT(*) FROM patients;"
        explanation = f"Total count: {len(data)} patients in current cohort."
        result = None # Just show text
        
    elif "average" in prompt_lower or "mean" in prompt_lower:
        if "bill" in prompt_lower or "cost" in prompt_lower:
            avg = data['bill_amount'].mean()
            sql_generated = "SELECT AVG(bill_amount) FROM patients;"
            explanation = f"Average Billing Amount: ${avg:.2f}"
            result = None
        elif "age" in prompt_lower:
            avg = data['age'].mean()
            sql_generated = "SELECT AVG(age) FROM patients;"
            explanation = f"Average Patient Age: {avg:.1f} years"
            result = None

    # FALLBACK
    else:
        sql_generated = "SELECT * FROM patients ORDER BY admission_date DESC LIMIT 5;"
        result = data.head()
        explanation = "Could not map specific intent. Displaying recent records."

    return sql_generated, result, explanation

# --- LOGIN SCREEN ---
def login_screen():
    st.markdown("<h1 style='text-align: center;'>⚡ VibeOps Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>NLP-to-SQL Healthcare Interface | v2.4 Beta</p>", unsafe_allow_html=True)
    
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
        
        st.markdown("---")
        st.caption("Contact sysadmin@vibeops.io for access.")

# --- MAIN DASHBOARD ---
def main_interface():
    with st.sidebar:
        st.title("⚡ VibeOps")
        st.write("**Connected to:** Secure_Health_DB_v2")
        st.write(f"**Records Loaded:** {len(df)}")
        st.markdown("---")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.title("Intelligent Query Interface")
    st.markdown("Use natural language to query the patient database.")

    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input Logic
    if prompt := st.chat_input("Try: 'Show me patients with Migraine' or 'What is the average age?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Simulate Processing Time (to look like AI)
            with st.status("Translating Natural Language to SQL...", expanded=True) as status:
                time.sleep(0.8) 
                status.update(label="Query Executed", state="complete", expanded=False)
            
            # CALL THE REAL LOGIC ENGINE
            sql, res_df, expl = execute_natural_language_query(prompt, df)

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
