import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="VibeOps Systems", page_icon="⚡", layout="wide")

# --- MOCK DATA LOADING ---
@st.cache_data
def load_data():
    try:
        # Tries to load the CSV you created
        return pd.read_csv("patients_dummy.csv")
    except:
        # Fallback if CSV is missing (prevents crash)
        return pd.DataFrame({
            "patient_id": ["P-001", "P-002"],
            "diagnosis": ["Flu", "Covid"],
            "status": ["Active", "Discharged"],
            "bill_amount": [1000, 2000]
        })

df = load_data()

# --- LOGIN SIMULATION ---
def login_screen():
    st.markdown("<h1 style='text-align: center;'>⚡ VibeOps Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>NLP-to-SQL Healthcare Interface | v2.4 Beta</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("🔒 Access Restricted: This system is currently available to authorized beta testers only.")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # The "Secret" Credentials
            if user == "demo" and pw == "harvard2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials. Please contact administrator.")
        
        st.markdown("---")
        st.caption("Forget password? Contact sysadmin@vibeops.io")

# --- MAIN DASHBOARD ---
def main_interface():
    # Sidebar
    with st.sidebar:
        st.title("⚡ VibeOps")
        st.write(f"**Status:** 🟢 Connected")
        st.write(f"**Database:** PostgreSQL (v14)")
        st.write(f"**Latency:** 12ms")
        st.markdown("---")
        st.markdown("### 🛠 Beta Stats")
        st.metric("Active Testers", "124", "+12%")
        st.metric("Queries Today", "8,430", "+5%")
        
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    # Main Chat Area
    st.title("Intelligent Query Interface")
    st.markdown("Ask questions about patient data in natural language. VibeOps translates intent to SQL.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input Logic
    if prompt := st.chat_input("Ex: 'Show me all patients with Influenza'"):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Response (The "Wizard of Oz" Logic)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Simulate "thinking"
            with st.status("Parsing Natural Language...", expanded=True) as status:
                st.write("Tokenizing input...")
                time.sleep(0.5)
                st.write("Mapping intent to schema...")
                time.sleep(0.5)
                st.write("Generating SQL...")
                time.sleep(0.5)
                status.update(label="Query Executed Successfully", state="complete", expanded=False)
            
            # LOGIC: Keyword Matching (Fake Intelligence)
            prompt_lower = prompt.lower()
            
            # Scenario 1: User asks for a specific disease
            if "influenza" in prompt_lower:
                sql_query = "SELECT * FROM patients WHERE diagnosis = 'Influenza';"
                result_df = df[df['diagnosis'] == 'Influenza']
                explanation = "Found active cases matching diagnosis 'Influenza'."

            elif "sinusitis" in prompt_lower:
                sql_query = "SELECT * FROM patients WHERE diagnosis = 'Chronic Sinusitis';"
                result_df = df[df['diagnosis'] == 'Chronic Sinusitis']
                explanation = "Found active cases matching diagnosis 'Chronic Sinusitis'."
            
            # Scenario 2: User asks for counts
            elif "count" in prompt_lower or "how many" in prompt_lower:
                sql_query = "SELECT COUNT(*) FROM patients;"
                count = len(df)
                result_df = None # Don't show table, show metric
                explanation = f"Total patient count in current view: {count}"
                
            # Scenario 3: User asks about billing/money
            elif "bill" in prompt_lower or "cost" in prompt_lower:
                sql_query = "SELECT AVG(bill_amount) FROM patients;"
                avg_cost = df['bill_amount'].mean()
                result_df = None
                explanation = f"Average billing amount across cohort: ${avg_cost:.2f}"
            
            # Fallback for anything else
            else:
                sql_query = "SELECT * FROM patients LIMIT 5;"
                result_df = df.head()
                explanation = "Displaying most recent patient records."

            # Render the Fake SQL Block
            st.code(sql_query, language="sql")
            st.write(f"**System:** {explanation}")
            
            if result_df is not None:
                st.dataframe(result_df, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": f"Executed: `{sql_query}`"})

# --- APP FLOW CONTROL ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    main_interface()