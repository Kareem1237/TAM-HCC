import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pyproj import Transformer


mapping = {
    '124': 'HEALTH_CENTER_MVZ',
    '125': 'DENTAL_CENTER',
    '130': 'NURSING_CENTER',
    '142': 'HEALTH_CENTER_MVZ',
    '143': 'HEALTH_CENTER_MVZ',
    '197': 'CSAPA',
    '223': 'PMI',
    '224': 'CPEF',
    '228': 'HEALTH_CENTER_MVZ',
    '230': 'PMI',
    '266': 'HEALTH_CENTER_MVZ',
    '267': 'HEALTH_CENTER_MVZ',
    '268': 'CMS',
    '269': 'SIUMPPS',
    '270': 'HEALTH_CENTER_MVZ',
    '289': 'NURSING_CENTER',
    '294': 'HEALTH_CENTER_MVZ',
    '347': 'CES_CENTRE_DEXAMENS_DE_SANTE',
    '438': 'HEALTH_CENTER_MVZ',
    '439': 'HEALTH_CENTER_MVZ',
    '616': 'WORKMEDICINE',
    '630': 'HEALTH_CENTER_MVZ',
    '636': 'HEALTH_CENTER_MVZ',
    '637': 'HEALTH_CENTER_MVZ',
    '638': 'HEALTH_CENTER_MVZ',
    '645': 'HEALTH_CENTER_MVZ'
}

st.markdown("<h1 style='text-align: center;'>🏢 TAM HCC 🏢</h1>", unsafe_allow_html=True)

filename = "https://static.data.gouv.fr/resources/finess-extraction-du-fichier-des-etablissements/20250704-114227/etalab-cs1100507-stock-20250703-0338.csv"

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

# upload the csv
df = pd.read_csv(filename,sep=';', skiprows=1, header=None, names=headers,
                encoding='utf-8')
df.drop(columns=['section'], inplace=True)
geoloc = df.iloc[int(len(df)/2):]
geoloc.drop(columns=geoloc.columns[5:], inplace=True)
geoloc.rename(columns=lambda x: geoloc_names[list(df.columns).index(x)], inplace=True)
df = df.iloc[:int(len(df)/2)]
df['numero_finess'] = df['numero_finess'].astype(str)
geoloc['numero_finess'] = geoloc['numero_finess'].astype(str)
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
final_scope=final[to_keep]

scope= [
    "124", "142", "143", "197", "223", "224", "228", "230", 
    "266", "267", "268", "269", "270", "294", "347", "438", 
    "616", "630", "636", "637", "638", "645", "125", "130", 
    "289", "439"
]
final_scope=final[final['code_categorie'].isin(scope)]
preventif= ["142", "143", "197", "223", "224", "228", "230", "266", "267", "268", 
                     "269", "270", "294", "347", "438", "616", "636", "637", "638", "645"]
curatif=["124","125","130","289","439","630"]
final_scope.loc[final_scope['code_categorie'].isin(preventif),'orga_type']='PREVENTION'
final_scope.loc[final_scope['code_categorie'].isin(curatif),'orga_type']='CURATIVE'
final_scope['organization_type']=final_scope['code_categorie'].astype(str).map(mapping).fillna('OTHER')

final_scope['status']='open'
final_scope['closed_at']=np.nan
final_scope['new_establishment_this_month']=False
final_scope['coord_x'] = final_scope['coord_x'].replace(",", ".")
final_scope['coord_y'] = final_scope['coord_y']
transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

final_scope[["longitude", "lattitude"]] = final_scope.apply(
    lambda row: pd.Series(transformer.transform(row['coord_x'], row['coord_y'])),
    axis=1
)
new_tam=final_scope.copy()

gsheet_columns= [
    "numero_finess", "numero_finess_juridique", "raison_sociale", "raison_sociale_long",
    "raison_sociale_complement", "distribution_complement", "voie_numero", "voie_type",
    "voie_label", "voie_complement", "lieu_dit_bp", "ville", "departement",
    "departement_label", "libelle_routage", "telephone", "fax", "code_categorie",
    "label_categorie", "code_status", "label_status", "siret", "ape", "code_tarif",
    "label_tarif", "code_psph", "label_psph", "date_ouverture", "date_autor",
    "date_update", "num_uai", "coord_x", "coord_y", "source_coord", "date_update_coord",
    "adresse", "code_postal", "orga_type", "status", "closed_at", "new_establishment_this_month",
    "longitude", "lattitude"
]
opps_columns = [
    "finessnumber__c", "name", "phone", "adresse", "code_postal",
    "healthcareservice type", "orga type", "siret", "label_categorie",
    "label_status", "date_ouverture", "date_update", "numero_finess_juridique"
]
today_date= datetime.today().strftime("%d-%m-%Y")
accounts_in_tam=len(new_tam['numero_finess'].unique())
st.markdown(f'## Total accounts in TAM on {today_date}:')
st.markdown(f'## {accounts_in_tam} accounts')

st.markdown('### New TAM details: ')
st.dataframe(new_tam)

st.markdown("<hr style='border:2px solid #000;'>", unsafe_allow_html=True)


current_tam = st.file_uploader("Upload the current TAM in SF as csv", type=["csv"])
if current_tam is not None:
    current_tam = pd.read_csv(current_tam)
    st.markdown(f'Current tam details: {len(current_tam)} accounts')
    st.dataframe(current_tam)  
    
    new_tam_finess=set(new_tam['numero_finess'].unique())
    current_tam_finess=set(current_tam['numero_finess'].unique())
    new_finess=new_tam_finess - current_tam_finess
    
    number_of_new_accounts_in_tam=len(new_finess)
    st.markdown(f'New accounts : {number_of_new_accounts_in_tam}')
    new_tam.loc[new_tam['numero_finess'].isin(list(new_finess)),'new_establishment_this_month']=True
    new_accounts=new_tam[new_tam['numero_finess'].isin(list(new_finess))]
    
    new_accounts_modified=new_accounts.copy()
    new_accounts_modified.rename(columns={'numero_finess':'finessnumber__c','raison_sociale':'name','telephone':'phone','orga_type':'healthcareservice type','organization_type':'orga type'},inplace=True)
    new_accounts_modified=new_accounts_modified[opps_columns]
    st.dataframe(new_accounts_modified)
    csv = new_accounts_modified.to_csv(index=False).encode('utf-8')
    st.markdown("**For DQ Operations team**") 
    st.download_button(
    label="📥   Download new finess accounts as a csv ",
    data=csv,
    file_name=f'new_finess_accounts_{today_date}.csv',
    mime='text/csv',
    )
    st.write(' ')
    current_tam=current_tam[gsheet_columns]
    current_tam['new_establishment_this_month']=False
    new_accounts=new_accounts[gsheet_columns]
    import_gsheet = pd.concat([current_tam, new_accounts], ignore_index=True)
    st.markdown(f'TAM to import gsheet : {len(import_gsheet)} accounts')
    st.dataframe(import_gsheet)
    csv_import_gsheet = import_gsheet.to_csv(index=False).encode('utf-8')
    st.markdown("**For DQ Projects team**")    
    st.download_button(
    label="📥   Download new csv to replace current linked sheet in metabase ",
    data=csv_import_gsheet,
    file_name=f'new_import_gsheet_{today_date}.csv',
    mime='text/csv',
    )

    