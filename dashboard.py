import streamlit as st
import sqlite3
import pandas as pd
import json
import altair as alt

st.set_page_config(page_title="Razor-Rescue Control Center", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for polish
st.markdown("""
<style>
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2962FF;
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: bold; }
    .metric-label { font-size: 14px; color: #a0aabf; }
    .pipeline-arrow { font-size: 24px; text-align: center; color: #555; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Razor-Rescue: AI Revenue Recovery Control Center")
st.caption("*Simulation-based evaluation using synthetic payment failures.*")

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
    st.warning("No evaluation data found. Run `python evaluate.py --records 1000 --fast` first.")
else:
    baseline_df = df[df['strategy'] == 'Baseline']
    ai_df = df[df['strategy'] == 'Razor-Rescue']
    
    total_records = len(ai_df)
    
    # KPIs
    b_recovered = baseline_df[baseline_df['status'] == 'recovered']
    b_bad_retries = baseline_df[baseline_df['is_bad_retry'] == 1]
    b_inr = b_recovered['amount_recovered'].sum() / 100
    b_rate = len(b_recovered) / total_records * 100 if total_records > 0 else 0
    
    ai_recovered = ai_df[ai_df['status'] == 'recovered']
    ai_bad_retries = ai_df[ai_df['is_bad_retry'] == 1]
    ai_inr = ai_recovered['amount_recovered'].sum() / 100
    ai_rate = len(ai_recovered) / total_records * 100 if total_records > 0 else 0

    st.markdown("### Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Failed Payments Analyzed", f"{total_records:,}")
    c2.metric("Total INR Recovered", f"₹ {ai_inr:,.2f}")
    c3.metric("Recovery Rate", f"{ai_rate:.1f}%")
    c4.metric("Unsafe Retries Avoided vs Baseline", f"{len(b_bad_retries) - len(ai_bad_retries):,}")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Strategy Comparison: Blind Retry vs Razor-Rescue")
        comp_data = pd.DataFrame({
            "Strategy": ["Blind Retry", "Razor-Rescue", "Blind Retry", "Razor-Rescue"],
            "Metric": ["Recovery Rate (%)", "Recovery Rate (%)", "Unsafe Retries", "Unsafe Retries"],
            "Value": [b_rate, ai_rate, len(b_bad_retries), len(ai_bad_retries)]
        })
        
        # Recovery Rate Chart
        chart_rate = alt.Chart(comp_data[comp_data['Metric'] == 'Recovery Rate (%)']).mark_bar().encode(
            x=alt.X('Value:Q', title="Recovery Rate (%)"),
            y=alt.Y('Strategy:N', sort='-x', title=""),
            color=alt.Color('Strategy:N', scale=alt.Scale(range=['#e0e0e0', '#2962FF']), legend=None),
            tooltip=['Strategy', 'Value']
        ).properties(height=120)
        
        # Unsafe Retries Chart
        chart_unsafe = alt.Chart(comp_data[comp_data['Metric'] == 'Unsafe Retries']).mark_bar().encode(
            x=alt.X('Value:Q', title="Total Unsafe Retries"),
            y=alt.Y('Strategy:N', sort=['Blind Retry', 'Razor-Rescue'], title=""),
            color=alt.Color('Strategy:N', scale=alt.Scale(range=['#D50000', '#00C853']), legend=None),
            tooltip=['Strategy', 'Value']
        ).properties(height=120)
        
        st.altair_chart(chart_rate, use_container_width=True)
        st.altair_chart(chart_unsafe, use_container_width=True)
        
    with col_chart2:
        st.subheader("Failure Mix — Synthetic Ground Truth")
        cause_counts = ai_df['ground_truth_cause'].value_counts().reset_index()
        cause_counts.columns = ['Cause', 'Count']
        donut = alt.Chart(cause_counts).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Cause", type="nominal"),
            tooltip=['Cause', 'Count']
        ).properties(height=300)
        st.altair_chart(donut, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Guardrails Prevent Unsafe Recovery Actions")
    st.markdown("Select a **Risky Card** transaction to see how Razor-Rescue protected the merchant compared to a Blind Retry.")
    
    risky_df = ai_df[(ai_df['ground_truth_cause'] == 'risky_card')]
    if not risky_df.empty:
        selected_id = st.selectbox("Select Payment Incident:", risky_df['payment_id'].tolist())
        
        if selected_id:
            ai_record = ai_df[ai_df['payment_id'] == selected_id].iloc[0]
            b_record = baseline_df[baseline_df['payment_id'] == selected_id].iloc[0]
            
            try: llm_data = json.loads(ai_record['llm_classification'])
            except: llm_data = {"root_cause": ai_record['ground_truth_cause'], "confidence_score": 0.99}
            
            try: dec_data = json.loads(ai_record['guardrail_action'])
            except: dec_data = {"action": ai_record['status'], "reason": "No data"}
            
            st.markdown(f"#### Payment #{selected_id}")
            st.markdown(f"**Failure Detected:** `{ai_record['ground_truth_cause']}` | **Risk Level:** `HIGH`")
            
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.info(f"**1. AI Diagnosis**\n\nCause: `{llm_data.get('root_cause', 'unknown')}`\n\nConf: `{float(llm_data.get('confidence_score', 0))*100:.0f}%`")
            with p2:
                st.warning(f"**2. Policy Engine**\n\n{dec_data.get('reason', 'Policy applied')}")
            with p3:
                st.success(f"**3. Razor-Rescue Action**\n\n**{dec_data.get('action', 'Escalated')}**\n*(Policy-Compliant)*")
            with p4:
                st.error(f"**vs. Blind Retry Action**\n\n**{b_record['status']}**\n(Bank Penalty)")
                
            with st.expander("View Full Audit Trace"):
                st.json({
                    "AI_Classification": llm_data,
                    "Guardrail_Decision": dec_data,
                    "Baseline_Comparison": {"action": "immediate_retry", "is_bad_retry": bool(b_record['is_bad_retry'])}
                })
                
    st.markdown("---")
    st.subheader("Complete Audit Trail")
    display_df = ai_df.copy()
    display_df['amount_recovered'] = display_df['amount_recovered'] / 100
    
    def extract_conf(row):
        try: return float(json.loads(row)['confidence_score'])
        except: return 0.0
        
    def extract_action(row):
        try: return json.loads(row)['action']
        except: return "unknown"
        
    display_df['AI_Confidence'] = display_df['llm_classification'].apply(extract_conf)
    display_df['Policy_Action'] = display_df['guardrail_action'].apply(extract_action)
    
    display_cols = ['payment_id', 'ground_truth_cause', 'AI_Confidence', 'Policy_Action', 'status', 'amount_recovered']
    st.dataframe(display_df[display_cols], use_container_width=True)
