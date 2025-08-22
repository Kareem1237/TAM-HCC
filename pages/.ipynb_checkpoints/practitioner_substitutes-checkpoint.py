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
    df = pd.read_csv(df_file ,dtype=str)
    specs = pd.read_csv(specs_file,dtype=str)
    agendas = pd.read_csv(agendas_file,dtype=str)
    
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

    specs = specs[specs['job']=='practitioner']
    specs = specs[specs['agenda_owner'].isna()]
    specs = specs[specs['sf_status']!='Customer']
    specs = specs[['name_metabase','email_metabase','phone_metabase',
                   'organization_id_metabase','agenda_owner','sf_status',
                   'account_id','agenda_id','job','sf_id','owner_name',
                   'agenda_specialty','agenda_specialty_sub_group',
                   'sf_account_specialty.1']]

    df = df[['substitute_id_sheet','name_sheet','email_sheet',
             'phone_sheet','organization_id_sheet','status']]

    merged_name = specs.merge(df, how='inner',
                              left_on='name_metabase', right_on='name_sheet')

    merged_email = specs.merge(df, how='inner',
                               left_on='email_metabase', right_on='email_sheet')
    merged_email = merged_email[merged_email['email_metabase'].notna()]

    specs_clean = specs.dropna(subset=['phone_metabase'])
    df_clean = df.dropna(subset=['phone_sheet'])

    specs_clean['phone_metabase'] = specs_clean['phone_metabase'].astype(str)
    df_clean['phone_sheet'] = df_clean['phone_sheet'].astype(str)

    merged_phone = specs_clean.merge(
        df_clean,
        how='inner',
        left_on='phone_metabase',
        right_on='phone_sheet',
        indicator=True
    )
    merged_phone = merged_phone[merged_phone['phone_metabase'].notna()]

    result = pd.concat([merged_name, merged_phone, merged_email],
                       ignore_index=True).drop_duplicates()
    result = result.groupby(['account_id','organization_id_sheet','agenda_id'],
                            as_index=False).first()

    final_subs_sheet = result.merge(
        agendas,
        how='left',
        left_on=['agenda_id','substitute_id_sheet'],
        right_on=['agenda_id','practitioner_substitute_id']
    )
    final_subs_sheet = final_subs_sheet[final_subs_sheet['practitioner_substitute_id'].notna()]
    final_subs_sheet['practitioner_substitute_id'] = final_subs_sheet['practitioner_substitute_id'].astype(int)
    final_subs_sheet=final_subs_sheet[['account_id', 'name_metabase','sf_id', 'sf_account_specialty.1','sf_status',
       'phone_metabase', 'phone_sheet',
       'agenda_owner', 'owner_name',
       'agenda_specialty', 'agenda_specialty_sub_group',
       'email_sheet', 'email_metabase', 'status','practitioner_substitute_id','agenda_id','organization_id_sheet'
       ]]
    final_subs_sheet.rename(columns={'email_metabase':'email_sf','name_metabase':'name','sf_account_specialty.1':'sf_specialty',\
                                             'email_sheet':'email_rak_file','phone_sheet':'phone_rak_file','status':'status_rak_file',\
                                    'organization_id_sheet':'organization_id','account_id':'doctolib_account_id'},inplace=True)
    final_subs_sheet=final_subs_sheet.astype(str)
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
    
