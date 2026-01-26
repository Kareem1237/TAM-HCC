import streamlit as st
import requests
import zipfile
import io
import pandas as pd
from datetime import datetime

today_date= datetime.today().strftime("%d-%m-%Y")

st.markdown("<h1 style='text-align: center;'>🔄 Substitutes 🔄</h1>", unsafe_allow_html=True)







df_file = st.file_uploader("Upload the substitutes rak file as csv", type=["csv"])
specs_file = st.file_uploader("Upload the csv of the needed specialties agendas and practitioners query", type=["csv"])
agendas_file = st.file_uploader("Upload the csv of the Substitutes from recurring events query", type=["csv"])

if df_file and specs_file and agendas_file:
    df = pd.read_csv(df_file, dtype=str)
    specs = pd.read_csv(specs_file, dtype=str)
    agendas = pd.read_csv(agendas_file, dtype=str)
    
    # Validate required columns exist
    required_df_cols = ['first_name', 'last_name', 'phone_number', 'id', 'organization_id', 'email', 'status']
    required_specs_cols = ['phone', 'full_name', 'organization_id', 'email', 'job', 'agenda_owner', 'sf_status', 
                          'account_id', 'agenda_id', 'sf_id', 'owner_name', 'agenda_specialty', 
                          'agenda_specialty_sub_group', 'sf_account_specialty.1']
    required_agendas_cols = ['agenda_id', 'practitioner_substitute_id']
    
    missing_df = [col for col in required_df_cols if col not in df.columns]
    missing_specs = [col for col in required_specs_cols if col not in specs.columns]
    missing_agendas = [col for col in required_agendas_cols if col not in agendas.columns]
    
    if missing_df:
        st.error(f"❌ Missing columns in substitutes file: {', '.join(missing_df)}")
        st.stop()
    if missing_specs:
        st.error(f"❌ Missing columns in specialties file: {', '.join(missing_specs)}")
        st.stop()
    if missing_agendas:
        st.error(f"❌ Missing columns in agendas file: {', '.join(missing_agendas)}")
        st.stop()
    
    def format_phone_number(phone_number):
        if pd.isna(phone_number):  
            return phone_number
        phone_number = str(phone_number).replace('.', '').replace(' ', '')

        if phone_number.startswith(("06", "07", "01", "02", "03", "04", "05")):
            phone_number = "+33" + phone_number[1:]
        elif phone_number.startswith(("6", "7", "1", "2", "3", "4", "5")):
            phone_number = "+33" + phone_number  
        elif phone_number.startswith(("+33")):
            phone_number =  phone_number 
        elif phone_number.startswith(("33")):
            phone_number =  "+" + phone_number 
        return phone_number
    
    df['phone_number'] = df['phone_number'].apply(format_phone_number)
    specs['phone'] = specs['phone'].apply(format_phone_number)

    df['name'] = df['first_name'] + ' ' + df['last_name']
    df['name'] = df['name'].str.lower()
    specs['name'] = specs['full_name'].str.lower()

    specs.rename(columns={
        'organization_id':'organization_id_metabase',
        'name':'name_metabase',
        'phone':'phone_metabase',
        'email':'email_metabase'
    }, inplace=True)

    df.rename(columns={
        'id':'substitute_id_sheet',
        'organization_id':'organization_id_sheet',
        'name':'name_sheet',
        'phone_number':'phone_sheet',
        'email':'email_sheet'
    }, inplace=True)

    specs = specs[specs['job']=='practitioner'].copy()
    specs = specs[specs['agenda_owner'].isna()].copy()
    specs = specs[specs['sf_status']!='Customer'].copy()
    specs = specs[['name_metabase','email_metabase','phone_metabase',
                   'organization_id_metabase','agenda_owner','sf_status',
                   'account_id','agenda_id','job','sf_id','owner_name',
                   'agenda_specialty','agenda_specialty_sub_group',
                   'sf_account_specialty.1']].copy()

    df = df[['substitute_id_sheet','name_sheet','email_sheet',
             'phone_sheet','organization_id_sheet','status']]

    # Diagnostic: count specs before merges
    count_specs_before_merge = len(specs)
    
    merged_name = specs.merge(df, how='inner',
                              left_on='name_metabase', right_on='name_sheet')
    count_merged_name = len(merged_name)

    merged_email = specs.merge(df, how='inner',
                               left_on='email_metabase', right_on='email_sheet')
    merged_email = merged_email[merged_email['email_metabase'].notna()]
    count_merged_email = len(merged_email)

    # Create clean DataFrames with phone columns already converted to string
    specs_clean = specs.dropna(subset=['phone_metabase']).copy()
    specs_clean = specs_clean.assign(phone_metabase=specs_clean['phone_metabase'].astype(str))
    
    df_clean = df.dropna(subset=['phone_sheet']).copy()
    df_clean = df_clean.assign(phone_sheet=df_clean['phone_sheet'].astype(str))

    merged_phone = specs_clean.merge(
        df_clean,
        how='inner',
        left_on='phone_metabase',
        right_on='phone_sheet',
        indicator=True
    )
    merged_phone = merged_phone[merged_phone['phone_metabase'].notna()]
    count_merged_phone = len(merged_phone)

    result = pd.concat([merged_name, merged_phone, merged_email],
                       ignore_index=True).drop_duplicates()
    
    # Diagnostic: count before groupby
    count_before_groupby = len(result)
    
    result = result.groupby(['account_id','organization_id_sheet','agenda_id'],
                            as_index=False).first()
    
    # Diagnostic: count after groupby
    count_after_groupby = len(result)

    final_subs_sheet = result.merge(
        agendas,
        how='left',
        left_on=['agenda_id','substitute_id_sheet'],
        right_on=['agenda_id','practitioner_substitute_id']
    )
    
    # Diagnostic: count after merge (before filtering)
    count_after_merge = len(final_subs_sheet)
    count_with_practitioner_id = final_subs_sheet['practitioner_substitute_id'].notna().sum()
    
    final_subs_sheet = final_subs_sheet[final_subs_sheet['practitioner_substitute_id'].notna()]
    
    # Convert to int, handling any non-numeric values
    final_subs_sheet['practitioner_substitute_id'] = pd.to_numeric(
        final_subs_sheet['practitioner_substitute_id'], 
        errors='coerce'
    ).astype('Int64')
    final_subs_sheet['practitioner_substitute_id'] = final_subs_sheet['practitioner_substitute_id'].astype(str)
    
    final_subs_sheet=final_subs_sheet[['account_id', 'name_metabase','sf_id', 'sf_account_specialty.1','sf_status',
       'phone_metabase', 'phone_sheet',
       'agenda_owner', 'owner_name',
       'agenda_specialty', 'agenda_specialty_sub_group',
       'email_sheet', 'email_metabase', 'status','practitioner_substitute_id','agenda_id','organization_id_sheet'
       ]]
    final_subs_sheet.rename(columns={
        'email_metabase':'email_sf',
        'name_metabase':'name',
        'sf_account_specialty.1':'sf_specialty',
        'email_sheet':'email_rak_file',
        'phone_sheet':'phone_rak_file',
        'status':'status_rak_file',
        'organization_id_sheet':'organization_id',
        'account_id':'doctolib_account_id'
    }, inplace=True)
    final_subs_sheet = final_subs_sheet.astype(str)
    
    # Diagnostic info
    diagnostics = {
        'count_specs_before_merge': count_specs_before_merge,
        'count_merged_name': count_merged_name,
        'count_merged_email': count_merged_email,
        'count_merged_phone': count_merged_phone,
        'count_before_groupby': count_before_groupby,
        'count_after_groupby': count_after_groupby,
        'count_after_merge': count_after_merge,
        'count_with_practitioner_id': count_with_practitioner_id,
        'count_final': len(final_subs_sheet),
        'count_agendas': len(agendas)
    }
    
    # Show diagnostic information
    st.markdown('### Processing Statistics')
    st.write(f"**Specs before merge:** {diagnostics['count_specs_before_merge']} | **Agendas file:** {diagnostics['count_agendas']}")
    
    st.write("**Merge Results:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Merged by Name", diagnostics['count_merged_name'])
    with col2:
        st.metric("Merged by Email", diagnostics['count_merged_email'])
    with col3:
        st.metric("Merged by Phone", diagnostics['count_merged_phone'])
    
    st.write("**After Processing:**")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Before Groupby", diagnostics['count_before_groupby'])
    with col2:
        st.metric("After Groupby", diagnostics['count_after_groupby'])
    with col3:
        st.metric("After Merge with Agendas", diagnostics['count_after_merge'])
    with col4:
        st.metric("With Practitioner ID", diagnostics['count_with_practitioner_id'])
    with col5:
        st.metric("Final Output", diagnostics['count_final'])
    
    st.markdown('### Substitute sheet formatted')
    st.dataframe(final_subs_sheet)
    
    sub_sheet = final_subs_sheet.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥   Download the substitute sheet ",
        data=sub_sheet,
        file_name=f'sub_sheet_{today_date}.csv',
        mime='text/csv',
    )
else:
    st.info("⬆️ Please upload all 3 CSV files to run the process.")
    
