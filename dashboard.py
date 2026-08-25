import streamlit as st
import sqlite3
import pandas as pd
import json

st.set_page_config(page_title="Razor-Rescue Audit", layout="wide")

st.title("🛡️ Razor-Rescue: AI Revenue Recovery Audit")
st.markdown("This dashboard proves **explainability** and **bounded actions** by displaying the exact decision trail of the AI Agent.")

def load_data():
    try:
        conn = sqlite3.connect("audit.db")
        df = pd.read_sql_query("SELECT * FROM audit_log", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No audit logs found. Run the python run.py agent first!")
else:
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
    st.subheader("Traceability Matrix: LLM vs Guardrails")
    
    display_df = df[['payment_id', 'timestamp', 'status', 'amount_recovered']].copy()
    display_df['amount_recovered'] = display_df['amount_recovered'] / 100
    st.dataframe(display_df, use_container_width=True)
    
    st.subheader("Deep Dive: Single Transaction Audit")
    st.markdown("Select a payment to see how the LLM classification maps to the hard-coded guardrails.")
    selected_id = st.selectbox("Select a Payment ID to Audit:", df['payment_id'])
    
    if selected_id:
        record = df[df['payment_id'] == selected_id].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("**1. Input Failure Data**")
            try:
                st.json(json.loads(record['input_data']))
            except:
                st.write(record['input_data'])
        with c2:
            st.warning("**2. LLM Classification**")
            try:
                st.json(json.loads(record['classification_result']))
            except:
                st.write(record['classification_result'])
        with c3:
            st.success("**3. Guardrail Action & Outcome**")
            try:
                st.json(json.loads(record['decision_result']))
                st.json(json.loads(record['execution_outcome']))
            except:
                st.write(record['decision_result'])
                st.write(record['execution_outcome'])
