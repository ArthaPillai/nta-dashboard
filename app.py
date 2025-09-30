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

st.set_page_config(page_title="NTA Accommodation Dashboard", layout="wide")

st.title("📊 NTA Accommodation Requests Dashboard")

# =============================
# Helper functions
# =============================
def extract_extended_time(accommodations):
    if pd.isna(accommodations):
        return None
    match = re.search(r'(\d+)%\s+Extended Time', str(accommodations))
    if match:
        return int(match.group(1))
    return None

def extract_diagnoses(diagnosis_text):
    if pd.isna(diagnosis_text):
        return []
    diagnoses = [d.strip() for d in str(diagnosis_text).split(',')]
    return diagnoses

# Add column for extended time
df['Extended_Time_Percent'] = df['Requested_Accommodations'].apply(extract_extended_time)

# =============================
# Tabs
# =============================
tabs = st.tabs([
    "Request Types", "Extended Time by Law School", "Extended Time Distribution",
    "Top Diagnoses", "Requests by Law School", "Approval by Request Type",
    "Approval Distribution", "Extended Time Distribution by Law School",
    "Extended Time vs Approval", "Correlations with Extended Time", "Comprehensive Stats"
])

# 1. Request Types
with tabs[0]:
    request_type_counts = df['Request_Type'].value_counts()
    fig1 = px.pie(
        values=request_type_counts.values,
        names=request_type_counts.index,
        title="Distribution of Request Types",
        color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
    )
    st.plotly_chart(fig1, use_container_width=True)

# 2. Extended Time by Law School
with tabs[1]:
    df_with_extended_time = df[df['Extended_Time_Percent'].notna()].copy()
    law_school_analysis = df_with_extended_time.groupby('Law_School').agg({
        'Extended_Time_Percent': ['mean', 'median', 'std', 'count'],
        'Approved?': lambda x: (x == 'Appv.').sum() / len(x) * 100
    }).round(2)

    law_school_analysis.columns = ['Avg_Extended_Time', 'Median_Extended_Time', 'Std_Extended_Time', 'Request_Count', 'Approval_Rate']
    law_school_analysis = law_school_analysis.reset_index().sort_values('Avg_Extended_Time', ascending=False)

    fig2 = px.bar(
        law_school_analysis,
        x="Law_School",
        y="Avg_Extended_Time",
        title="Average Extended Time Requests by Law School",
        labels={'Avg_Extended_Time': 'Average Extended Time (%)', 'Law_School': 'Law School'},
        color="Avg_Extended_Time",
        color_continuous_scale="Viridis",
        text="Avg_Extended_Time"
    )
    fig2.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

# 3. Extended Time Distribution
with tabs[2]:
    extended_time_counts = df['Extended_Time_Percent'].value_counts().sort_index()
    fig3 = px.bar(
        x=extended_time_counts.index,
        y=extended_time_counts.values,
        title="Distribution of Extended Time Requests",
        labels={'x': 'Extended Time Percentage', 'y': 'Number of Requests'},
        color=extended_time_counts.values,
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig3, use_container_width=True)

# 4. Top Diagnoses
with tabs[3]:
    all_diagnoses = []
    for diagnosis in df['Diagnosis']:
        all_diagnoses.extend(extract_diagnoses(diagnosis))
    diagnosis_counts = pd.Series(all_diagnoses).value_counts().head(10)

    fig4 = px.bar(
        y=diagnosis_counts.index,
        x=diagnosis_counts.values,
        orientation="h",
        title="Top 10 Most Common Diagnoses",
        labels={'x': 'Number of Cases', 'y': 'Diagnosis'},
        color=diagnosis_counts.values,
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig4, use_container_width=True)

# 5. Requests by Law School
with tabs[4]:
    law_school_counts = df['Law_School'].value_counts()
    fig5 = px.bar(
        y=law_school_counts.index,
        x=law_school_counts.values,
        orientation="h",
        title="Accommodation Requests by Law School",
        labels={'x': 'Number of Requests', 'y': 'Law School'},
        color=law_school_counts.values,
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig5, use_container_width=True)

# 6. Approval by Request Type
with tabs[5]:
    approval_by_request = pd.crosstab(df['Request_Type'], df['Approved?'], normalize='index') * 100
    fig6 = px.bar(
        approval_by_request,
        x=approval_by_request.index,
        y=['Appv.', 'Appv. Part', 'Prev. Exam'],
        title="Approval Status by Request Type (%)",
        labels={'x': 'Request Type', 'value': 'Percentage'},
        barmode="stack",
        color_discrete_sequence=['#2ecc71', '#f39c12', '#3498db']
    )
    st.plotly_chart(fig6, use_container_width=True)

# 7. Approval Distribution
with tabs[6]:
    approval_counts = df['Approved?'].value_counts()
    fig7 = px.bar(
        x=approval_counts.index,
        y=approval_counts.values,
        title="Approval Status Distribution",
        labels={'x': 'Approval Status', 'y': 'Count'},
        color=approval_counts.values,
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig7, use_container_width=True)

# 8. Extended Time Distribution by Law School
with tabs[7]:
    df_with_extended_time = df[df['Extended_Time_Percent'].notna()].copy()
    extended_time_pivot = df_with_extended_time.pivot_table(
        index="Law_School",
        columns="Extended_Time_Percent",
        values="File_Name",
        aggfunc="count",
        fill_value=0
    )
    extended_time_pct = extended_time_pivot.div(extended_time_pivot.sum(axis=1), axis=0) * 100

    fig8 = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, time_pct in enumerate([25, 50, 100]):
        if time_pct in extended_time_pct.columns:
            fig8.add_trace(go.Bar(
                name=f"{time_pct}% Extended Time",
                x=extended_time_pct.index,
                y=extended_time_pct[time_pct],
                marker_color=colors[i % len(colors)]
            ))

    fig8.update_layout(
        title="Distribution of Extended Time Requests by Law School (%)",
        xaxis_title="Law School",
        yaxis_title="Percentage of Requests",
        barmode="stack"
    )
    st.plotly_chart(fig8, use_container_width=True)

# 9. Extended Time vs Approval
with tabs[8]:
    law_school_stats = df_with_extended_time.groupby('Law_School').agg({
        'Extended_Time_Percent': 'mean',
        'Approved?': lambda x: (x.isin(['Appv.', 'Appv. Part'])).sum() / len(x) * 100,
        'File_Name': 'count'
    }).round(2)
    law_school_stats.columns = ['Avg_Extended_Time', 'Approval_Rate', 'Request_Count']
    law_school_stats = law_school_stats.reset_index()

    fig9 = px.scatter(
        law_school_stats,
        x="Avg_Extended_Time",
        y="Approval_Rate",
        size="Request_Count",
        color="Law_School",
        hover_data=["Law_School", "Avg_Extended_Time", "Approval_Rate", "Request_Count"],
        title="Extended Time vs Approval Rate by Law School"
    )
    st.plotly_chart(fig9, use_container_width=True)

# 10. Correlations with Extended Time
with tabs[9]:
    df['Extended_Time_Numeric'] = df['Requested_Accommodations'].apply(extract_extended_time)
    df['Is_Fully_Approved'] = (df['Approved?'] == 'Appv.').astype(int)
    df['Is_Partially_Approved'] = (df['Approved?'] == 'Appv. Part').astype(int)
    df['Is_Previously_Examined'] = (df['Approved?'] == 'Prev. Exam').astype(int)
    df['Is_New_Request'] = (df['Request_Type'] == 'New Request').astype(int)
    df['Is_Retake_Same'] = (df['Request_Type'] == 'Retake - Same Request').astype(int)
    df['Is_Retake_Changed'] = (df['Request_Type'] == 'Retake - Changed Request').astype(int)

    extended_time_correlations = df[['Extended_Time_Numeric', 'Is_Fully_Approved', 'Is_Partially_Approved',
                                     'Is_Previously_Examined', 'Is_New_Request', 'Is_Retake_Same', 'Is_Retake_Changed']].corr()['Extended_Time_Numeric']

    fig10 = px.bar(
        x=extended_time_correlations.index,
        y=extended_time_correlations.values,
        title="Correlations with Extended Time Percentage",
        labels={'x': 'Variables', 'y': 'Correlation'}
    )
    st.plotly_chart(fig10, use_container_width=True)

# 11. Correlation Matrix
with tabs[10]:
    st.header("Correlation Matrix")
    corr = df.corr(numeric_only=True)

    fig_corr = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap"
    )
    st.plotly_chart(fig_corr, use_container_width=True)
