import streamlit as st
import requests
import zipfile
import io
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pyproj import Transformer
import requests
from bs4 import BeautifulSoup


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
activities=activities.astype("string")
st.markdown("<h3 style='text-align: center;'> Order of Pharmacies </h3>", unsafe_allow_html=True)
st.write(' ')
pharmacies=pharmacies[pharmacies['Adresse'].notnull()]
pharmacies=pharmacies.astype("string")
types = ["OFFICINE", "SIEGE SOCIAL PHARMACEUTIQUE", "ETS C PHARMACEU. NON SIEGE SOCIAL", "ETS B PHARMACEUT.NON SIEGE SOCIAL", "PHARMACIEN MULTI - EMPLOYEURS", "ETS BC PHARMACEU. NON SIEGE SOCIAL", "PHARMACIE MUTUALISTE", "PHARMACIE DE SECOURS MINIER", "ANTENNE D'OFFICINE"]
pharmacies['phone'] = pharmacies['Téléphone'].apply(lambda x: '+33' + x[1:] if pd.notna(x) and x.startswith('0') else x)
pharmacies=pharmacies.drop(columns='Téléphone',axis=1)
pharmacies["Adresse"] = pharmacies["Adresse"].str.replace(r' {2,}', ' ', regex=True)
pharmacies['Code postal']=pharmacies['Code postal'].apply(lambda x: '0'+x if pd.notna(x) and len(x)==4 else x)
pharmacies.rename(columns={"Numéro d'établissement":'numero_establishment','Type établissement':'type','Dénomination commerciale':'denomination_commerciale','Raison sociale':'raison_sociale','Adresse':'address','Code postal':'code_postal','Département':'department'},inplace=True)
pharmacies=pharmacies[pharmacies['type'].isin(types)]
pharmacists=pharmacists.astype("string")

roles = ['PHARMACIEN TITULAIRE D\'OFFICINE', 'ADJOINT INTERMITTENT EN OFFICINE', 'ADJOINT D\'OFFICINE TEMPS PARTIEL', 'ADJOINT  INDUSTRIE', 'ADJOINT INDUSTRIE TEMPS PARTIEL', 'PHARMACIEN ADJOINT D\'OFFICINE', 'PHARMACIEN RESPONSABLE', 'PRATICIEN ADJOINT CONTRACTUEL', 'PHARMACIEN ADJOINT ES PRIVÉ T.PLEIN', 'GERANT APRES DECES DU TITULAIRE', 'PHARMACIEN SP ADJOINT VOLONTAIRE', 'PHARMACIEN ADJOINT ES PRIVÉ T.PARTI', 'ADJOINT CARMI', 'ADJOINT PHARMACIE MUTUALISTE', 'PHARMACIEN ADJOINT BPDO', 'PHARMACIEN SP ADJOINT PROFESSIONNEL', 'ADJOINT DISTRIBUTION', 'PHARMACIEN SAPEUR-POMPIER ADJOINT', 'RESPONSABLE']

activities=activities[activities["Numéro d'établissement"].isin(pharmacies['numero_establishment'].unique())]
activities=activities[activities["Fonction"].isin(roles)]
pharmacists=pharmacists[pharmacists['n° RPPS'].isin(activities['n° RPPS pharmacien'].unique())]
pharmacists=pharmacists.rename(columns={"n° RPPS":'rpps'})

activities=activities.rename(columns={"Numéro d'établissement":'numero_establishment',"n° RPPS pharmacien":'rpps'})

col1, col2 = st.columns(2)
with col1:
    st.markdown(f'💊 Pharmacies: {len(pharmacies)}')
    st.dataframe(pharmacies,use_container_width=True)
with col2:
    st.markdown('🥼 Pharmacists')
    st.dataframe(pharmacists,use_container_width=True)
st.write(' ')

st.write('Activities')
st.dataframe(activities)




# FINESS DATABASE
url="https://www.data.gouv.fr/datasets/finess-extraction-du-fichier-des-etablissements/#_"
page=requests.get(url)
soup=BeautifulSoup(page.text,'html')
url=soup.find('div',class_='flex items-center buttons').find('a')['href']
filename = url


headers = [
    'section','numero_finess','numero_finess_juridique','raison_sociale',
    'raison_sociale_long','raison_sociale_complement','distribution_complement',
    'voie_numero','voie_type','voie_label','voie_complement','lieu_dit_bp',
    'ville','departement','departement_label','ligne_acheminement','telephone',
    'fax','code_categorie','label_categorie','code_status','label_status',
    'siret','ape','code_tarif','label_tarif','code_psph',
    'label_psph','date_ouverture','date_autor','date_update','num_uai'
]
geoloc_names = [
    'numero_finess','coord_x','coord_y','source_coord','date_update_coord'
]



df = pd.read_csv(filename,sep=';', skiprows=1, header=None, names=headers,
                encoding='utf-8')
df.drop(columns=['section'], inplace=True)
geoloc = df.iloc[int(len(df)/2):]
geoloc.drop(columns=geoloc.columns[5:], inplace=True)
geoloc.rename(columns=lambda x: geoloc_names[list(df.columns).index(x)], inplace=True)
df = df.iloc[:int(len(df)/2)]
df['numero_finess'] = df['numero_finess'].astype("string")
geoloc['numero_finess'] = geoloc['numero_finess'].astype("string")
final = df.merge(geoloc, on='numero_finess', how='left')
dico={'R':'RUE', 'PL':'PLACE', 'RTE':'ROUTE', 'AV':'AVENUE', 'GR':'GRANDE RUE', 'ALL':'ALLEE', 'CHE':'CHEMIN', 'QUA':'QUARTIER',
'BD':'BOULEVARD', 'PROM':'PROMENADE', 'ZA':'ZONE ARTISANALE', 'QU':'QUAI', 'ESPA':'ESPACE', 'IMP':'IMPASSE', 'LD':'LIEU DIT', 'SQ':'SQUARE',
 'LOT':'LOTISSEMENT', 'ZAC':"ZONE D'AMENAGEMENT CONCERTE", 'IMM':'IMMEUBLE', 'RES':'RESIDENCE', 'CRS':'COURS', 'ESP':'ESPLANADE', 'FG':'FAUBOURG',
'CHS':'CHAUSSEE', 'MTE':'MONTEE', 'DOM':'DOMAINE', 'PAS':'PASSAGE', 'SEN':'SENTIER', 'VAL':'VALLEE', 'VOI':'VOIE',
'PKG':'PARKING', 'RLE':'RUELLE'}
final.replace({"voie_type": dico},inplace=True)
final['raison_sociale']=final['raison_sociale'].apply(lambda x : str(x).replace('.0','').replace('nan',''))
final['adresse']=final['voie_numero'].apply(lambda x : str(x).replace('.0','').replace('nan',''))+final['voie_complement'].apply(lambda x : str(x).replace('.0','').replace('nan',''))+ ' ' + final['voie_type'] + ' ' + final['voie_label']
final['code_postal']=final['ligne_acheminement'].apply(lambda x: str(re.search('\d\d\d\d\d|$',str(x))[0]))
final['ville']=final['ligne_acheminement'].apply(lambda x: re.split('\d\d\d\d\d|$',str(x))[1].strip(' '))
final.rename(columns={"ligne_acheminement": "libelle_routage"},inplace=True)
final['telephone']=final['telephone'].apply(lambda x : ('+33' + str(x).replace('.0','')).replace('+33nan',''))
final['fax']=final['fax'].apply(lambda x : ('+33' + str(x).replace('.0','')).replace('+33nan',''))
final['siret']=final['siret'].apply(lambda x : str(x).replace('.0','').replace('nan',''))
final['code_categorie']=final['code_categorie'].apply(lambda x : str(x).replace('.0','').replace('nan',''))
final['code_status']=final['code_status'].apply(lambda x : str(x).replace('.0','').replace('nan',''))
final['code_psph']=final['code_psph'].apply(lambda x : str(x).replace('.0','').replace('nan',''))
final['ape']=final['ape'].apply(lambda x : str(x).replace(' ','').replace('nan',''))
to_keep=['numero_finess','siret','ape','raison_sociale','raison_sociale_long','distribution_complement','adresse','lieu_dit_bp','code_postal','ville','telephone','fax','code_categorie','label_categorie','code_status','label_status','code_psph','date_ouverture','date_update','num_uai','numero_finess_juridique','coord_x','coord_y']
final=final[to_keep]
pharma=final[final['label_categorie'].str.contains('pharma',case=False)]
st.write(' ')
st.write(' ')
st.write(' ')




pharma=pharma.astype("string")
pharma=pharma[['numero_finess','raison_sociale','adresse','code_postal','telephone']]
pharma['raison_sociale']=pharma['raison_sociale'].str.strip()
pharmacies['raison_sociale']=pharmacies['raison_sociale'].str.strip()

ba=pharmacies.copy()
ba_0=ba.copy()
ba_0.rename(columns={'raison_sociale':'name_in_order','code_postal':'code_postal_in_order'},inplace=True)
pharma_0=pharma.copy()
ba_0=ba_0.astype("string")
pharma_0=pharma_0.astype("string")






matched_ba_ids = set()
matched_pharma_ids = set()

merge1 = pd.merge(
    ba_0, pharma_0,left_on=['address','name_in_order','phone','code_postal_in_order'],right_on=['adresse','raison_sociale','telephone','code_postal'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge1['numero_establishment'])
matched_pharma_ids.update(merge1['numero_finess'])


ba_2 = ba_0[~ba_0['numero_establishment'].isin(matched_ba_ids)]
pharma_2 = pharma_0[~pharma_0['numero_finess'].isin(matched_pharma_ids)]

merge2 = pd.merge(
    ba_2, pharma_2,
    left_on=['address','name_in_order','code_postal_in_order'],right_on=['adresse','raison_sociale','code_postal'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge2['numero_establishment'])
matched_pharma_ids.update(merge2['numero_finess'])



ba_3 = ba_0[~ba_0['numero_establishment'].isin(matched_ba_ids)]
pharma_3 = pharma_0[~pharma_0['numero_finess'].isin(matched_pharma_ids)]

merge3 = pd.merge(
    ba_3, pharma_3,
    left_on=['address','denomination_commerciale','code_postal_in_order'],right_on=['adresse','raison_sociale','code_postal'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge3['numero_establishment'])
matched_pharma_ids.update(merge3['numero_finess'])



ba_4 = ba_0[~ba_0['numero_establishment'].isin(matched_ba_ids)]
pharma_4 = pharma_0[~pharma_0['numero_finess'].isin(matched_pharma_ids)]

merge4 = pd.merge(
    ba_4, pharma_4,
    left_on=['code_postal_in_order','address'],right_on=['code_postal','adresse'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge4['numero_establishment'])
matched_pharma_ids.update(merge4['numero_finess'])



ba_5 = ba_0[~ba_0['numero_establishment'].isin(matched_ba_ids)]
pharma_5 = pharma_0[~pharma_0['numero_finess'].isin(matched_pharma_ids)]

merge5 = pd.merge(
    ba_5, pharma_5,
    left_on=['code_postal_in_order','name_in_order'],right_on=['code_postal','raison_sociale'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge5['numero_establishment'])
matched_pharma_ids.update(merge5['numero_finess'])



ba_6 = ba_0[~ba_0['numero_establishment'].isin(matched_ba_ids)]
pharma_6 = pharma_0[~pharma_0['numero_finess'].isin(matched_pharma_ids)]

merge6 = pd.merge(
    ba_6, pharma_6,
    left_on=['code_postal_in_order','denomination_commerciale'],right_on=['code_postal','raison_sociale'],
    suffixes=('_ba', '_pharma'),
    how='inner'
)

matched_ba_ids.update(merge6['numero_establishment'])
matched_pharma_ids.update(merge6['numero_finess'])


final_merged = pd.concat([merge1, merge2, merge3, merge4, merge5,merge6], ignore_index=True)
final_merged=final_merged.drop_duplicates()


st.write(' ')
st.write(' ')
st.write(' ')
st.write(' ')


order_finess_pharmas=pharmacies.merge(final_merged[['numero_establishment','numero_finess']],how='left',on='numero_establishment')

columns = ["numero_establishment", "numero_finess", "type", "denomination_commerciale", "raison_sociale", "address", "code_postal", "Commune", "department", "Région", "Fax", "phone"]
types = ["OFFICINE", "SIEGE SOCIAL PHARMACEUTIQUE", "ETS C PHARMACEU. NON SIEGE SOCIAL", "ETS B PHARMACEUT.NON SIEGE SOCIAL", "PHARMACIEN MULTI - EMPLOYEURS", "ETS BC PHARMACEU. NON SIEGE SOCIAL", "PHARMACIE MUTUALISTE", "PHARMACIE DE SECOURS MINIER", "ANTENNE D'OFFICINE"]

order_finess_pharmas=order_finess_pharmas[order_finess_pharmas['type'].isin(types)]
order_finess_pharmas=order_finess_pharmas[columns]
st.write(f'💊 Order of Pharma with {len(list(order_finess_pharmas['numero_finess'].unique()))} matched finess accounts')

st.dataframe(order_finess_pharmas)

current_tam = st.file_uploader("Upload the current TAM in SF as csv", type=["csv"])
current_pharmacists=st.file_uploader("Upload the pharmacists in SF as csv",type=['csv'])

if current_tam is not None and current_pharmacists is not None :
    current_tam = pd.read_csv(current_tam)
    current_pharmacists=pd.read_csv(current_pharmacists)
    st.markdown(f'Current tam details: {len(current_tam['external_id'].unique())} accounts')
    #st.dataframe(current_tam)  
    missing_activities_current_tam = (
    activities[['numero_establishment', 'rpps', 'Fonction']].merge(
        current_tam[['external_id', 'pa_rpps']],
        how='left',
        left_on=['numero_establishment', 'rpps'],
        right_on=['external_id', 'pa_rpps']
     )
     )
    missing_activities_current_tam = missing_activities_current_tam[
    (missing_activities_current_tam['numero_establishment'].isin(
        current_tam['external_id'].unique()
    )) 
    & 
    (missing_activities_current_tam['external_id'].isna())
    ][['numero_establishment','rpps','Fonction']]
    
    new_pharmacies_external_id=set(order_finess_pharmas['numero_establishment'].dropna().unique())
    new_pharmacies_finess=set(order_finess_pharmas['numero_finess'].dropna().unique())
    new_pharmacies_address=set(order_finess_pharmas['address'].dropna().str.lower().unique())

    current_pharmacies_external_id=set(current_tam['external_id'].dropna().unique())
    current_pharmacies_finess=set(current_tam['numero_finess'].dropna().unique())
    current_pharmacies_address=set(current_tam['street'].dropna().unique())
                              
    new_external_id=new_pharmacies_external_id - current_pharmacies_external_id
    new_finess=new_pharmacies_finess-current_pharmacies_finess
    new_addresses=new_pharmacies_address-current_pharmacies_address
    
    missing_pharmacies=order_finess_pharmas[order_finess_pharmas['numero_establishment'].isin(list(new_external_id))]
    missing_pharmacies=missing_pharmacies[missing_pharmacies['numero_finess'].isin(list(new_finess))]
    missing_pharmacies=missing_pharmacies[missing_pharmacies['address'].str.lower().isin(list(new_addresses))]
    missing_pharmacies=missing_pharmacies.drop(columns='Fax',axis=1)
    
    pharmacies_to_create=missing_pharmacies.copy().drop_duplicates()
    st.write(' ')
    st.write(f'## Missing pharmacies to create: {len(pharmacies_to_create)}')
    pharmacies_to_create.rename(columns={'numero_establishment':'external_id','numero_finess':'finessnumber__c','raison_sociale':'name',
                                         'address':'billingstreet','code_postal':'billingpostalcode','Commune':'billingcity'},inplace=True)
    pharmacies_to_create=pharmacies_to_create[['external_id','finessnumber__c','name','billingstreet','billingpostalcode','billingcity','phone']]
    pharmacies_to_create['recordtype']='0121i000000kJpkAAE'
    pharmacies_to_create['organisationtype__c']='Pharmacy'
    pharmacies_to_create['billingcountrycode']='FR'
    st.dataframe(pharmacies_to_create)
    #st.write('Missing pharmacies,pharmacists and activities to add:')
    csv=pharmacies_to_create.to_csv(index=False).encode('utf-8')
    st.download_button(
    label="📥   Download pharmacies to create ",
    data=csv,
    file_name=f'new_pharma_ba.csv',
    mime='text/csv',
    )

    missing_pharmacies=missing_pharmacies.merge(activities,how='left',left_on='numero_establishment',right_on='numero_establishment')

    
    missing_pharmacies=missing_pharmacies.merge(pharmacists,how='left',left_on='rpps',right_on='rpps')

    missing_activities=missing_pharmacies[['numero_establishment','rpps','Fonction']].drop_duplicates()
    missing_activities=pd.concat([missing_activities,missing_activities_current_tam])
    missing_activities=missing_activities.drop_duplicates()

    current_pharmacists['rpps'] = current_pharmacists['rppsnumber__c'].astype('string')
    missing_activities['rpps'] = missing_activities['rpps'].astype('string')
    missing_activities=missing_activities.merge(current_pharmacists[['id','rpps']],how='left',left_on='rpps',right_on='rpps')

    rpps_found=list(missing_activities[missing_activities['id'].isnull()]['rpps'].unique())
    pharmacists_to_create=missing_activities[missing_activities['rpps'].isin(rpps_found)&missing_activities['rpps'].notnull()].drop_duplicates()
    pharmacists_to_create=pharmacists_to_create.merge(pharmacists[['rpps','Prénom','Nom de naissance']],how='inner',on='rpps')
    pharmacists_to_create=pharmacists_to_create[['rpps','Prénom','Nom de naissance']]
    pharmacists_to_create.rename(columns={'rpps':'rppsnumber__c','Prénom':'firstname','Nom de naissance':'lastname'},inplace=True)
    pharmacists_to_create['specialty__c']='a0h1i000000niyxAAA'
    
    st.write('## Pharmacists to create: ')
    st.dataframe(pharmacists_to_create)
    csv=pharmacists_to_create.to_csv(index=False).encode('utf-8')
    st.download_button(
    label="📥   Download pharmacists to create ",
    data=csv,
    file_name=f'new_pharmacists_pa.csv',
    mime='text/csv',
    )
    
    st.write(' ')
    st.write('## Activities to create: ')
    missing_activities.rename(columns={'numero_establishment':'external_id','rpps':'rppsnumber__c','Fonction':'roleintheworkplace__c','id':'personaccount_id'},inplace=True)
    missing_activities=missing_activities[missing_activities['rppsnumber__c'].notnull()]
    st.dataframe(missing_activities)
    csv=missing_activities.to_csv(index=False).encode('utf-8')
    st.download_button(
    label="📥   Download missing activities to create ",
    data=csv,
    file_name=f'new_pharmacists_pa.csv',
    mime='text/csv',
    )
    st.write(' ')


