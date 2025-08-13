import streamlit as st
import requests
import zipfile
import io
import pandas as pd
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>⚕️ TAM Pharma ⚕️</h1>", unsafe_allow_html=True)
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')

url = "https://www.ordre.pharmacien.fr/download/annuaire_csv.zip"
response = requests.get(url)
response.raise_for_status()

# Step 2: Load the ZIP file into a ZipFile object (from bytes, not disk)
zip_file = zipfile.ZipFile(io.BytesIO(response.content))

# Step 3: Find the file containing 'establishment' in its name
pharmacy = [name for name in zip_file.namelist() if "etablissements" in name.lower()]
pharmacists=[name for name in zip_file.namelist() if "pharmaciens" in name.lower()]
pac=[name for name in zip_file.namelist() if "activites" in name.lower()]



pharmacy_filename = pharmacy[0]  
pharmacists_filename = pharmacists[0] 
pac_filename = pac[0] 

# Step 4: Read the file's content
with zip_file.open(pharmacy_filename) as ba:
        pharmacies = pd.read_csv(
        ba,
        encoding="utf-16-le",  
        sep=";",                
        engine="python"         
    ) 

with zip_file.open(pharmacists_filename) as pa:
        pharmacists = pd.read_csv(
        pa,
        encoding="utf-16-le",  
        sep=";",                
        engine="python"         
    ) 

with zip_file.open(pac_filename) as pacs:
        activities = pd.read_csv(
        pacs,
        encoding="utf-16-le",  
        sep=";",                
        engine="python"         
    ) 
pharmacies=pharmacies.astype(str)
pharmacies['phone'] = pharmacies['Téléphone'].apply(lambda x: '+33' + x[1:] if x.startswith('0') else x)
pharmacies=pharmacies.drop(columns='Téléphone',axis=1)
col1, col2 = st.columns(2)
with col1:
    st.markdown('💊 Pharmacies')
    st.dataframe(pharmacies.head(20),use_container_width=True)
with col2:
    st.markdown('🥼 Pharmacists')
    st.dataframe(pharmacists.head(20),use_container_width=True)
