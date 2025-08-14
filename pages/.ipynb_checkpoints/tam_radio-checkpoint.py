import streamlit as st

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pyproj import Transformer

today_date= datetime.today().strftime("%d-%m-%Y")

st.markdown("<h1 style='text-align: center;'>🩻 TAM Radiology 🩻</h1>", unsafe_allow_html=True)
st.write(' ')
st.write(' ')
st.write(' ')
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
final=final[to_keep]
scope= ["698"]

final_scope=final[(final['code_categorie'].isin(scope))&(~final['raison_sociale'].str.contains('DIALYSE|DOMICILE', na=False)) & (~final['code_psph'].str.contains('1', na=False))]

st.write(f'Total TAM Radiology accounts = {len(final_scope)} accounts')
st.write(' ')

st.dataframe(final_scope)
radio_csv=final_scope.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥   Download the new TAM for Radiology as a csv ",
    data=radio_csv,
    file_name=f'radio_tam_accounts_{today_date}.csv',
    mime='text/csv',
    )