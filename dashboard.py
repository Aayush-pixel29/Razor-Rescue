import streamlit as st
import sqlite3
import pandas as pd
import json

st.set_page_config(page_title="Razor-Rescue Audit", layout="wide", initial_sidebar_state="expanded")

st.title("🛡️ Razor-Rescue: AI Revenue Recovery")
st.markdown("Internal audit dashboard for AI-driven payment recovery. Validates **explainability** and **bounded actions**.")

@st.cache_data(ttl=5) # Cache data but refresh every 5 seconds if re-run
def load_data():
    try:
        conn = sqlite3.connect("audit.db")
        df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No audit logs found. Run the python run.py agent first!")
else:
    # Sidebar Filters
    st.sidebar.header("Filter Audit Log")
    status_filter = st.sidebar.multiselect(
        "Filter by Status",
        options=df['status'].unique(),
        default=df['status'].unique()
    )
    
    filtered_df = df[df['status'].isin(status_filter)]
    
    # Top Level Metrics
    total = len(df)
    recovered = df[df['status'] == 'recovered']
    pending_links = df[df['status'] == 'link_sent_pending_payment']
    recovery_rate = len(recovered) / total * 100 if total > 0 else 0
    total_inr = recovered['amount_recovered'].sum() / 100
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Failed Payments", total)
    col2.metric("Pending Payment Links", len(pending_links))
    col3.metric("Confirmed Recoveries", len(recovered))
    col4.metric("True Recovery Rate", f"{recovery_rate:.1f}%")
    col5.metric("Total INR Recovered", f"₹ {total_inr:,.2f}")
    
    st.markdown("---")
    
    # Layout with 2 columns: Master list on left, Details on right
    left_col, right_col = st.columns([1.2, 1])
    
    with left_col:
        st.subheader("Traceability Matrix")
        
        display_df = filtered_df[['payment_id', 'timestamp', 'status', 'amount_recovered']].copy()
        display_df['amount_recovered'] = display_df['amount_recovered'] / 100
        
        # We use st.dataframe with custom column config for better readability
        st.dataframe(
            display_df, 
            use_container_width=True,
            height=500,
            column_config={
                "payment_id": "Payment ID",
                "timestamp": "Time",
                "status": "Recovery Status",
                "amount_recovered": st.column_config.NumberColumn("₹ Recovered", format="₹%.2f")
            }
        )
        
    with right_col:
        st.subheader("Deep Dive: Single Transaction")
        selected_id = st.selectbox("Select Payment ID to Audit:", filtered_df['payment_id'].tolist())
        
        if selected_id:
            record = df[df['payment_id'] == selected_id].iloc[0]
            
            try: input_data = json.loads(record['input_data']) 
            except: input_data = {}
            
            try: llm_data = json.loads(record['classification_result'])
            except: llm_data = {"error": str(record['classification_result'])}
                
            try: decision_data = json.loads(record['decision_result'])
            except: decision_data = {"error": str(record['decision_result'])}
                
            try: exec_data = json.loads(record['execution_outcome'])
            except: exec_data = {"error": str(record['execution_outcome'])}
            
            # 1. Original Failure
            st.markdown("#### 1. The Failure (Input)")
            err_code = input_data.get('error_code', 'Unknown')
            err_desc = input_data.get('error_description', 'No description')
            st.error(f"**{err_code}**: {err_desc}")
            
            # 2. LLM Brain
            st.markdown("#### 2. AI Classification (LLM)")
            root_cause = llm_data.get('root_cause', 'unknown')
            conf = llm_data.get('confidence_score', 0.0)
            reasoning = llm_data.get('reasoning', '')
            st.warning(f"**Diagnosed Cause:** `{root_cause}` (Confidence: {conf*100}%)\n\n**AI Reasoning:** {reasoning}")
            
            # 3. Guardrails
            st.markdown("#### 3. Guardrail Execution (Code)")
            action = decision_data.get('action', 'unknown')
            rule_reason = decision_data.get('reason', '')
            st.info(f"**Enforced Action:** `{action}`\n\n**Rule Triggered:** {rule_reason}")
            
            # 4. Final Outcome
            st.markdown("#### 4. API Outcome")
            outcome_status = exec_data.get('status', 'Unknown')
            if 'link sent' in outcome_status.lower() or 'success' in outcome_status.lower() or 'scheduled' in outcome_status.lower():
                st.success(f"**Result:** {outcome_status}")
            elif outcome_status == 'Escalated to human review':
                st.error(f"**Result:** {outcome_status}")
            else:
                st.error(f"**Result:** {outcome_status}")
                
            with st.expander("View Raw JSON Trace"):
                st.json({
                    "input": input_data,
                    "classification": llm_data,
                    "decision": decision_data,
                    "execution": exec_data
                })
