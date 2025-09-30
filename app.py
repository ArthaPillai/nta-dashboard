import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# =============================
# Load Data
# =============================
file_path = "Master_NTA_KeyDetails.xlsx"  # Keep the file in the repo
df = pd.read_excel(file_path)

st.set_page_config(page_title="NTA Accommodations Dashboard", layout="wide")

st.title("📊 NTA Accommodations Dashboard")

# =============================
# KPI Summary
# =============================
st.markdown("### 📌 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_requests = len(df)
approval_rate = (df['Approved?'].eq('Appv.').mean() * 100).round(1)
most_common_diagnosis = df['Diagnosis'].mode()[0] if df['Diagnosis'].notna().any() else "N/A"
top_request_type = df['Request_Type'].mode()[0] if df['Request_Type'].notna().any() else "N/A"

col1.metric("Total Requests", f"{total_requests:,}")
col2.metric("Approval Rate", f"{approval_rate}%")
col3.metric("Most Common Diagnosis", most_common_diagnosis)
col4.metric("Top Request Type", top_request_type)

# =============================
# Sidebar Filters
# =============================
st.sidebar.header("🔍 Filters")

law_schools = st.sidebar.multiselect(
    "Select Law Schools",
    options=df['Law_School'].dropna().unique(),
    default=df['Law_School'].dropna().unique()
)

request_types = st.sidebar.multiselect(
    "Select Request Types",
    options=df['Request_Type'].dropna().unique(),
    default=df['Request_Type'].dropna().unique()
)

approval_status = st.sidebar.multiselect(
    "Select Approval Status",
    options=df['Approved?'].dropna().unique(),
    default=df['Approved?'].dropna().unique()
)

# Apply filters globally
df = df[df['Law_School'].isin(law_schools)]
df = df[df['Request_Type'].isin(request_types)]
df = df[df['Approved?'].isin(approval_status)]

# =============================
# Navigation
# =============================
section = st.sidebar.radio(
    "📍 Navigate Dashboard",
    ["Overview", "Extended Time Analysis", "Diagnoses"]
)

# =============================
# Section 1: Overview
# =============================
if section == "Overview":
    st.header("📍 Overview")

    # Request Types
    request_type_counts = df['Request_Type'].value_counts()
    fig1 = px.pie(values=request_type_counts.values, names=request_type_counts.index,
                  title='Distribution of Request Types')
    st.plotly_chart(fig1, use_container_width=True)

    # Requests by Law School
    law_school_counts = df['Law_School'].value_counts()
    fig2 = px.bar(y=law_school_counts.index, x=law_school_counts.values, orientation='h',
                  title='Accommodation Requests by Law School',
                  labels={'x': 'Number of Requests', 'y': 'Law School'},
                  color=law_school_counts.values, color_continuous_scale='Blues')
    st.plotly_chart(fig2, use_container_width=True)

    # Approval Distribution
    approval_counts = df['Approved?'].value_counts()
    fig3 = px.bar(x=approval_counts.index, y=approval_counts.values,
                  title='Approval Status Distribution',
                  labels={'x': 'Approval Status', 'y': 'Count'},
                  color=approval_counts.values, color_continuous_scale='Blues')
    st.plotly_chart(fig3, use_container_width=True)

    # Approval by Request Type
    approval_by_request = pd.crosstab(df['Request_Type'], df['Approved?'], normalize='index') * 100
    fig4 = px.bar(approval_by_request, x=approval_by_request.index,
                  y=['Appv.', 'Appv. Part', 'Prev. Exam'],
                  title='Approval Status by Request Type (%)',
                  barmode='stack')
    st.plotly_chart(fig4, use_container_width=True)

# =============================
# Section 2: Extended Time Analysis
# =============================
elif section == "Extended Time Analysis":
    st.header("⏳ Extended Time Analysis")

    def extract_extended_time(accommodations):
        if pd.isna(accommodations):
            return None
        match = re.search(r'(\d+)%\s+Extended Time', str(accommodations))
        if match:
            return int(match.group(1))
        return None

    df['Extended_Time_Percent'] = df['Requested_Accommodations'].apply(extract_extended_time)
    df_with_extended_time = df[df['Extended_Time_Percent'].notna()].copy()

    # Extended Time Distribution
    extended_time_counts = df['Extended_Time_Percent'].value_counts().sort_index()
    fig5 = px.bar(x=extended_time_counts.index, y=extended_time_counts.values,
                  title='Distribution of Extended Time Requests',
                  labels={'x': 'Extended Time %', 'y': 'Requests'},
                  color=extended_time_counts.values, color_continuous_scale='Viridis')
    st.plotly_chart(fig5, use_container_width=True)

    # Extended Time by Law School
    law_school_analysis = df_with_extended_time.groupby('Law_School').agg({
        'Extended_Time_Percent': ['mean', 'median'],
        'Approved?': lambda x: (x == 'Appv.').sum() / len(x) * 100
    }).round(2).reset_index()
    law_school_analysis.columns = ['Law_School', 'Avg_Extended_Time', 'Median_Extended_Time', 'Approval_Rate']

    fig6 = px.bar(law_school_analysis, x='Law_School', y='Avg_Extended_Time',
                  title='Average Extended Time Requests by Law School',
                  color='Avg_Extended_Time', text='Avg_Extended_Time',
                  color_continuous_scale='Viridis')
    fig6.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig6, use_container_width=True)

    # Extended Time vs Approval
    law_school_stats = df_with_extended_time.groupby('Law_School').agg({
        'Extended_Time_Percent': 'mean',
        'Approved?': lambda x: (x.isin(['Appv.', 'Appv. Part'])).sum() / len(x) * 100,
        'File_Name': 'count'
    }).round(2).reset_index()
    law_school_stats.columns = ['Law_School', 'Avg_Extended_Time', 'Approval_Rate', 'Request_Count']

    fig7 = px.scatter(law_school_stats, x='Avg_Extended_Time', y='Approval_Rate',
                      size='Request_Count', color='Law_School',
                      title='Extended Time vs Approval Rate by Law School')
    st.plotly_chart(fig7, use_container_width=True)

    # Correlation Matrix
    df_clean = df.copy()
    df_clean['Extended_Time'] = df_clean['Requested_Accommodations'].str.contains('Extended Time', na=False).astype(int)
    df_clean['Laptop'] = df_clean['Requested_Accommodations'].str.contains('Laptop', na=False).astype(int)
    df_clean['Reduced_Distraction'] = df_clean['Requested_Accommodations'].str.contains('Reduced distraction', na=False).astype(int)
    df_clean['OTC_Breaks'] = df_clean['Requested_Accommodations'].str.contains('OTC', na=False).astype(int)
    df_clean['Large_Print'] = df_clean['Requested_Accommodations'].str.contains('Large Print|18 pt|24 pt', na=False).astype(int)
    df_clean['Medication'] = df_clean['Requested_Accommodations'].str.contains('Medication|Medicine', na=False).astype(int)

    df_clean['ADHD'] = df_clean['Diagnosis'].str.contains('ADHD', na=False).astype(int)
    df_clean['Anxiety'] = df_clean['Diagnosis'].str.contains('Anxiety', na=False).astype(int)
    df_clean['Depression'] = df_clean['Diagnosis'].str.contains('Depression', na=False).astype(int)
    df_clean['Physical_Condition'] = df_clean['Diagnosis'].str.contains('Glaucoma|Carpal Tunnel|Vertigo|Polyneuropathy|Osteoarthritis', na=False).astype(int)

    df_clean['Retake_Request'] = df_clean['Request_Type'].str.contains('Retake', na=False).astype(int)
    df_clean['Approved'] = df_clean['Approved?'].str.contains('Appv', na=False).astype(int)

    correlation_columns = ['Extended_Time', 'Laptop', 'Reduced_Distraction', 'OTC_Breaks',
                          'Large_Print', 'Medication', 'ADHD', 'Anxiety', 'Depression',
                          'Physical_Condition', 'Retake_Request', 'Approved']
    corr_matrix = df_clean[correlation_columns].corr()

    fig8 = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                     color_continuous_scale='RdBu',
                     title='Correlation Heatmap of Accommodations, Diagnoses, Request Type, and Approval')
    st.plotly_chart(fig8, use_container_width=True)

# =============================
# Section 3: Diagnoses
# =============================
elif section == "Diagnoses":
    st.header("🧠 Diagnoses Insights")

    def extract_diagnoses(diagnosis_text):
        if pd.isna(diagnosis_text):
            return []
        return [d.strip() for d in str(diagnosis_text).split(',')]

    all_diagnoses = []
    for diagnosis in df['Diagnosis']:
        all_diagnoses.extend(extract_diagnoses(diagnosis))

    diagnosis_counts = pd.Series(all_diagnoses).value_counts().head(10)
    fig9 = px.bar(y=diagnosis_counts.index, x=diagnosis_counts.values, orientation='h',
                  title='Top 10 Most Common Diagnoses',
                  labels={'x': 'Number of Cases', 'y': 'Diagnosis'},
                  color=diagnosis_counts.values, color_continuous_scale='Reds')
    fig9.update_layout(height=600) 
    st.plotly_chart(fig9, use_container_width=True)
