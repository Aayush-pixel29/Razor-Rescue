import streamlit as st
import sqlite3
import pandas as pd
import json

st.set_page_config(page_title="Razor-Rescue Evaluation", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .status-recovered { color: #00C853; font-weight: bold; }
    .status-escalated { color: #D50000; font-weight: bold; }
    .metric-good { color: #00C853; font-size: 24px; font-weight: bold; }
    .metric-bad { color: #D50000; font-size: 24px; font-weight: bold; }
    .metric-neutral { color: #2962FF; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Razor-Rescue: A/B Strategy Evaluation")
st.markdown("This dashboard proves measured ROI by comparing **Strategy A (Blind Retries)** against **Strategy B (Razor-Rescue AI + Guardrails)**.")

@st.cache_data(ttl=5)
def load_data():
    try:
        conn = sqlite3.connect("evaluation.db")
        df = pd.read_sql_query("SELECT * FROM eval_log", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No evaluation data found. Run `python evaluate.py --records 1000 --fast` to populate the DB.")
else:
    baseline_df = df[df['strategy'] == 'Baseline']
    ai_df = df[df['strategy'] == 'Razor-Rescue']
    
    total_records = len(baseline_df)
    
    st.markdown("### Executive Summary")
    c1, c2, c3 = st.columns(3)
    
    # Baseline Metrics
    b_recovered = baseline_df[baseline_df['status'] == 'recovered']
    b_bad_retries = baseline_df[baseline_df['is_bad_retry'] == 1]
    b_inr = b_recovered['amount_recovered'].sum() / 100
    
    # AI Metrics
    ai_recovered = ai_df[ai_df['status'] == 'recovered']
    ai_bad_retries = ai_df[ai_df['is_bad_retry'] == 1]
    ai_inr = ai_recovered['amount_recovered'].sum() / 100
    ai_links = len(ai_df[ai_df['status'] == 'link_sent'])
    ai_escalated = len(ai_df[ai_df['status'] == 'escalated'])
    
    with c1:
        st.markdown("**Metric**")
        st.markdown("Recovery Rate")
        st.markdown("Total ₹ Recovered")
        st.markdown("Unsafe / Bad Retries")
        st.markdown("Human Escalations")
        st.markdown("Payment Links Sent")
        
    with c2:
        st.markdown("**Strategy A: Dumb Baseline**")
        st.markdown(f"**{(len(b_recovered)/total_records)*100:.1f}%**")
        st.markdown(f"**₹ {b_inr:,.2f}**")
        st.markdown(f"<span class='metric-bad'>{len(b_bad_retries)}</span>", unsafe_allow_html=True)
        st.markdown("0 (Blind retry)")
        st.markdown("0")
        
    with c3:
        st.markdown("**Strategy B: Razor-Rescue**")
        st.markdown(f"**{(len(ai_recovered)/total_records)*100:.1f}%**")
        st.markdown(f"**₹ {ai_inr:,.2f}**")
        st.markdown(f"<span class='metric-good'>{len(ai_bad_retries)}</span>", unsafe_allow_html=True)
        st.markdown(f"{ai_escalated}")
        st.markdown(f"{ai_links}")

    st.markdown("---")
    
    st.subheader("Deep Dive: How the Guardrails Prevented Disaster")
    st.markdown("Select a **Risky Card** transaction that the Baseline blindly retried, but Razor-Rescue caught.")
    
    risky_df = ai_df[(ai_df['ground_truth_cause'] == 'risky_card')]
    if not risky_df.empty:
        selected_id = st.selectbox("Select Risky Payment ID:", risky_df['payment_id'].tolist())
        
        if selected_id:
            baseline_record = baseline_df[baseline_df['payment_id'] == selected_id].iloc[0]
            ai_record = ai_df[ai_df['payment_id'] == selected_id].iloc[0]
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.error("#### Strategy A: Baseline Action")
                st.write("**Action:** Blind Immediate Retry")
                st.write(f"**Result:** {baseline_record['status']}")
                st.write(f"**Bad Retry?** {'Yes (Flagged by bank)' if baseline_record['is_bad_retry'] else 'No'}")
                
            with col_b:
                st.success("#### Strategy B: Razor-Rescue")
                try:
                    dec = json.loads(ai_record['guardrail_action'])
                    st.write(f"**Action:** {dec['action']}")
                    st.write(f"**Reason:** {dec['reason']}")
                except:
                    st.write(f"**Action:** {ai_record['status']}")
                    
            with st.expander("View AI Classification JSON"):
                try: st.json(json.loads(ai_record['llm_classification']))
                except: st.write(ai_record['llm_classification'])
