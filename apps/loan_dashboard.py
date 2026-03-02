"""Loan Processing Dashboard - Analytics and Productivity Metrics."""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml

from audit_log import redact_pii, log_audit_event

# Authentication
with open(Path(__file__).parent / 'config.yaml') as file:
    config = yaml.safe_load(file)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None
    st.session_state.login_time = None

def check_credentials(username, password):
    """Check if credentials are valid"""
    if username in config['credentials']['usernames']:
        stored_password = config['credentials']['usernames'][username]['password']
        if stored_password == password:
            return True, config['credentials']['usernames'][username]['name']
    return False, None


def check_session_timeout(timeout_seconds: int = 1800) -> bool:
    """
    Check if session has timed out (default 30 minutes).
    Returns True if session is still valid, False if expired.
    """
    if not st.session_state.logged_in or not st.session_state.login_time:
        return True
    
    elapsed = time.time() - st.session_state.login_time
    
    if elapsed > timeout_seconds:
        st.session_state.logged_in = False
        st.session_state.login_time = None
        return False
    
    return True

# Login UI
st.set_page_config(page_title="Loan Processing Dashboard", layout="wide")

if not st.session_state.logged_in:
    st.title("🔐 Loan Dashboard Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Please log in")
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")
        
        if st.button("Login", use_container_width=True, type="primary"):
            valid, user_name = check_credentials(username, password)
            if valid:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.name = user_name
                st.session_state.login_time = time.time()
                log_audit_event(username, "login", resource="loan_dashboard")
                st.rerun()
            else:
                log_audit_event(username, "login_failed", resource="loan_dashboard", status="failure")
                st.error("❌ Invalid username or password")
        
        st.divider()
        st.caption("Demo credentials: admin / admin123 or demo / demo123")
    st.stop()

# Check for session timeout
if not check_session_timeout():
    st.error("⏱️ Session expired. Please log in again.")
    st.stop()

# Logout button
with st.sidebar:
    st.write(f"👤 Welcome, **{st.session_state.name}**")
    if st.button("🚪 Logout", use_container_width=True):
        log_audit_event(st.session_state.username, "logout", resource="loan_dashboard")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()

# Import tracking after login
from loan_tracking import (
    load_applications,
    get_qualification_stats,
    get_average_processing_time,
    get_document_confidence_stats,
    get_applications_by_user,
    get_applications_by_date_range,
    get_quality_issues
)

# Main Dashboard
st.title("📊 Loan Processing Dashboard")
st.write("Real-time analytics and productivity metrics")

# Load data
applications = load_applications()

if not applications:
    st.info("📭 No loan applications tracked yet. Process applications using the Loan Checker app to see metrics here.")
    st.stop()

# Convert to DataFrame for easy analysis
df = pd.DataFrame(applications)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

# Date range filter
col1, col2 = st.columns(2)
with col1:
    date_filter = st.selectbox(
        "Time Period",
        ["All Time", "Today", "Last 7 Days", "Last 30 Days", "Custom"]
    )

# Apply date filter
if date_filter == "Today":
    today = datetime.now().date()
    df_filtered = df[df['date'] == today]
elif date_filter == "Last 7 Days":
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    df_filtered = df[df['date'] >= seven_days_ago]
elif date_filter == "Last 30 Days":
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    df_filtered = df[df['date'] >= thirty_days_ago]
else:
    df_filtered = df

# Key Metrics Row
st.header("📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Applications", len(df_filtered))

with col2:
    avg_time = df_filtered['processing_time_seconds'].mean()
    st.metric("Avg Processing Time", f"{avg_time:.1f}s")

with col3:
    approval_rate = (df_filtered['qualification'] == 'Likely to Qualify').sum() / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
    st.metric("Approval Rate", f"{approval_rate:.1f}%")

with col4:
    apps_today = len(df[df['date'] == datetime.now().date()])
    st.metric("Applications Today", apps_today)

st.divider()

# Two column layout for charts
col1, col2 = st.columns(2)

with col1:
    # Qualification Distribution
    st.subheader("🎯 Qualification Distribution")
    qual_counts = df_filtered['qualification'].value_counts()
    fig_qual = px.pie(
        values=qual_counts.values,
        names=qual_counts.index,
        color=qual_counts.index,
        color_discrete_map={
            'Likely to Qualify': '#00cc66',
            'Conditional Approval': '#ffaa00',
            'High Risk': '#ff4444'
        }
    )
    fig_qual.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_qual, use_container_width=True)

with col2:
    # Processing Time Distribution
    st.subheader("⏱️ Processing Time Distribution")
    fig_time = px.histogram(
        df_filtered,
        x='processing_time_seconds',
        nbins=20,
        labels={'processing_time_seconds': 'Processing Time (seconds)'},
        color_discrete_sequence=['#4CAF50']
    )
    fig_time.update_layout(showlegend=False)
    st.plotly_chart(fig_time, use_container_width=True)

# Applications Over Time
st.subheader("📅 Applications Over Time")
apps_by_date = df_filtered.groupby('date').size().reset_index(name='count')
fig_timeline = px.line(
    apps_by_date,
    x='date',
    y='count',
    labels={' date': 'Date', 'count': 'Applications'},
    markers=True
)
fig_timeline.update_traces(line_color='#2196F3')
st.plotly_chart(fig_timeline, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # Document Confidence Scores
    st.subheader("📄 Avg Document Confidence")
    
    # Extract confidence scores
    confidence_data = []
    for _, row in df_filtered.iterrows():
        conf = row.get('extraction_confidence', {})
        for doc_type, score in conf.items():
            confidence_data.append({'Document Type': doc_type, 'Confidence': score * 100})
    
    if confidence_data:
        conf_df = pd.DataFrame(confidence_data)
        avg_conf = conf_df.groupby('Document Type')['Confidence'].mean().reset_index()
        
        fig_conf = px.bar(
            avg_conf,
            x='Document Type',
            y='Confidence',
            color='Confidence',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig_conf.update_layout(showlegend=False)
        st.plotly_chart(fig_conf, use_container_width=True)
    else:
        st.info("No confidence data available")

with col2:
    # Hourly Processing Activity
    st.subheader("🕐 Peak Processing Hours")
    hourly = df_filtered.groupby('hour').size().reset_index(name='count')
    
    fig_hourly = px.bar(
        hourly,
        x='hour',
        y='count',
        labels={'hour': 'Hour of Day', 'count': 'Applications'},
        color='count',
        color_continuous_scale='Viridis'
    )
    fig_hourly.update_layout(showlegend=False)
    st.plotly_chart(fig_hourly, use_container_width=True)

# Team Performance
st.subheader("👥 Team Performance")
user_stats = df_filtered.groupby('reviewed_by').agg({
    'application_id': 'count',
    'processing_time_seconds': 'mean',
    'qualification': lambda x: (x == 'Likely to Qualify').sum() / len(x) * 100
}).reset_index()
user_stats.columns = ['User', 'Applications Processed', 'Avg Time (sec)', 'Approval Rate (%)']

st.dataframe(
    user_stats.style.format({
        'Avg Time (sec)': '{:.1f}',
        'Approval Rate (%)': '{:.1f}%'
    }),
    use_container_width=True,
    hide_index=True
)

# Metrics Breakdown
st.subheader("💰 Financial Metrics Analysis")

metrics_data = []
for _, row in df_filtered.iterrows():
    metrics = row.get('metrics', {})
    if metrics:
        metrics_data.append({
            'Application': row['application_id'],
            'Payment/Income Ratio': metrics.get('payment_to_income_ratio', 0),
            'Disposable Income': metrics.get('disposable_income', 0),
            'Liquidity/Payment': metrics.get('liquidity_vs_payment', 0),
            'Qualification': row['qualification']
        })

if metrics_data:
    metrics_df = pd.DataFrame(metrics_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Avg Payment/Income Ratio",
            f"{metrics_df['Payment/Income Ratio'].mean():.2f}",
            help="Lower is better (< 0.30 ideal)"
        )
    
    with col2:
        st.metric(
            "Avg Disposable Income",
            f"${metrics_df['Disposable Income'].mean():,.0f}",
            help="Higher is better (> $1000 ideal)"
        )
    
    with col3:
        st.metric(
            "Avg Liquidity Ratio",
            f"{metrics_df['Liquidity/Payment'].mean():.1f}x",
            help="Higher is better (> 3x ideal)"
        )

# Recent Applications Table
st.subheader("📋 Recent Applications")
recent_apps = df_filtered.sort_values('timestamp', ascending=False).head(10)

display_df = recent_apps[['application_id', 'timestamp', 'applicant_name', 'reviewed_by', 'qualification', 'processing_time_seconds']].copy()
# Redact applicant names for privacy
display_df['applicant_name'] = display_df['applicant_name'].apply(redact_pii)
display_df.columns = ['Application ID', 'Timestamp', 'Applicant', 'Reviewed By', 'Qualification', 'Time (sec)']

st.dataframe(
    display_df.style.format({'Time (sec)': '{:.1f}'}),
    use_container_width=True,
    hide_index=True
)

# Export Data
st.divider()
if st.button("📥 Export All Data (CSV)"):
    # Redact applicant names in export for privacy
    export_df = df.copy()
    export_df['applicant_name'] = export_df['applicant_name'].apply(redact_pii)
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"loan_applications_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
