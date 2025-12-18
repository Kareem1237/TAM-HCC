# app_tam_labo.py
# Streamlit TAM Labo - SELAS & Labs Process + gsheet update 

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pyproj import Transformer
from bs4 import BeautifulSoup
import requests
from io import StringIO

st.set_page_config(page_title="TAM Labo", layout="wide")

METABASE_URL = "https://metabase.doctolibdata.com/dashboard/5447-tam-labo-dashboard?tab=5023-dq-ops-process"


def fetch_latest_finess_urls():
    url_etab_page = "https://www.data.gouv.fr/datasets/finess-extraction-du-fichier-des-etablissements/#_"
    page = requests.get(url_etab_page, timeout=30)
    soup = BeautifulSoup(page.text, "html.parser")
    url_etabs = soup.find("div", class_="flex items-center buttons").find("a")["href"]

    url_juridique_page = "https://www.data.gouv.fr/datasets/finess-extraction-des-entites-juridiques/"
    page_jur = requests.get(url_juridique_page, timeout=30)
    soup_jur = BeautifulSoup(page_jur.text, "html.parser")
    url_juridique = soup_jur.find("div", class_="flex items-center buttons").find("a")["href"]

    return url_etabs, url_juridique

def load_finess_etablissements(url_etabs):
    headers = [
        "section","numero_finess","numero_finess_juridique","raison_sociale",
        "raison_sociale_long","raison_sociale_complement","distribution_complement",
        "voie_numero","voie_type","voie_label","voie_complement","lieu_dit_bp",
        "ville","departement","departement_label","ligne_acheminement","telephone",
        "fax","code_categorie","label_categorie","code_status","label_status",
        "siret","ape","code_tarif","label_tarif","code_psph",
        "label_psph","date_ouverture","date_autor","date_update","num_uai"
    ]
    geoloc_names = ["numero_finess","coord_x","coord_y","source_coord","date_update_coord"]

    df = pd.read_csv(url_etabs, sep=";", skiprows=1, header=None, names=headers, encoding="utf-8")
    df.drop(columns=["section"], inplace=True)

    geoloc = df.iloc[int(len(df)/2):].copy()
    geoloc.drop(columns=geoloc.columns[5:], inplace=True)
    geoloc.columns = [
        geoloc_names[list(df.columns).index(c)] if list(df.columns).index(c) < len(geoloc_names) else c
        for c in geoloc.columns
    ]

    df = df.iloc[:int(len(df)/2)].copy()
    df["numero_finess"] = df["numero_finess"].astype(str)
    geoloc["numero_finess"] = geoloc["numero_finess"].astype(str)
    final = df.merge(geoloc, on="numero_finess", how="left")

    # Clean / enrich
    dico = {
        "R":"RUE","PL":"PLACE","RTE":"ROUTE","AV":"AVENUE","GR":"GRANDE RUE","ALL":"ALLEE","CHE":"CHEMIN","QUA":"QUARTIER",
        "BD":"BOULEVARD","PROM":"PROMENADE","ZA":"ZONE ARTISANALE","QU":"QUAI","ESPA":"ESPACE","IMP":"IMPASSE","LD":"LIEU DIT","SQ":"SQUARE",
        "LOT":"LOTISSEMENT","ZAC":"ZONE D'AMENAGEMENT CONCERTE","IMM":"IMMEUBLE","RES":"RESIDENCE","CRS":"COURS","ESP":"ESPLANADE","FG":"FAUBOURG",
        "CHS":"CHAUSSEE","MTE":"MONTEE","DOM":"DOMAINE","PAS":"PASSAGE","SEN":"SENTIER","VAL":"VALLEE","VOI":"VOIE",
        "PKG":"PARKING","RLE":"RUELLE"
    }
    final.replace({"voie_type": dico}, inplace=True)
    final["raison_sociale"] = final["raison_sociale"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    final["adresse"] = (
        final["voie_numero"].apply(lambda x: str(x).replace(".0","").replace("nan","")) +
        final["voie_complement"].apply(lambda x: str(x).replace(".0","").replace("nan","")) + " " +
        final["voie_type"].astype(str) + " " + final["voie_label"].astype(str)
    ).str.strip()
    final["code_postal"] = final["ligne_acheminement"].apply(lambda x: str(re.search(r"\d\d\d\d\d|\$", str(x))[0]))
    final["ville"] = final["ligne_acheminement"].apply(lambda x: re.split(r"\d\d\d\d\d|\$", str(x))[1].strip(" "))
    final.rename(columns={"ligne_acheminement": "libelle_routage"}, inplace=True)
    final["telephone"] = final["telephone"].apply(lambda x: ("+33" + str(x).replace(".0","")).replace("+33nan",""))
    final["fax"] = final["fax"].apply(lambda x: ("+33" + str(x).replace(".0","")).replace("+33nan",""))
    final["siret"] = final["siret"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    final["code_categorie"] = final["code_categorie"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    final["code_status"] = final["code_status"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    final["code_psph"] = final["code_psph"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    final["ape"] = final["ape"].apply(lambda x: str(x).replace(" ","").replace("nan",""))

    return final

def load_finess_juridique(url_juridique):
    headers_juridique = [
        "section","numero_finess","raison_sociale","raison_sociale_long","raison_sociale_complement",
        "voie_numero","voie_type","voie_label","voie_complement","distribution_complement","lieu_dit_bp",
        "commune","ligne_acheminement","departement","departement_label","telephone","statut_juridique",
        "statut_juridique_libel","categorie_etablissement","libelle_categorie_etablissement",
        "numero_de_siren","code_APE","date_de_creation"
    ]
    df_j = pd.read_csv(url_juridique, sep=";", skiprows=1, header=None, names=headers_juridique, encoding="utf-8")
    df_j.drop(columns=["section"], inplace=True)
    df_j["numero_finess"] = df_j["numero_finess"].astype(str).str.replace(".0","").str.strip()

    dico = {
        "R":"RUE","PL":"PLACE","RTE":"ROUTE","AV":"AVENUE","GR":"GRANDE RUE","ALL":"ALLEE",
        "CHE":"CHEMIN","QUA":"QUARTIER","BD":"BOULEVARD","PROM":"PROMENADE","ZA":"ZONE ARTISANALE",
        "QU":"QUAI","ESPA":"ESPACE","IMP":"IMPASSE","LD":"LIEU DIT","SQ":"SQUARE",
        "LOT":"LOTISSEMENT","ZAC":"ZONE D'AMENAGEMENT CONCERTE","IMM":"IMMEUBLE","RES":"RESIDENCE",
        "CRS":"COURS","ESP":"ESPLANADE","FG":"FAUBOURG","CHS":"CHAUSSEE","MTE":"MONTEE",
        "DOM":"DOMAINE","PAS":"PASSAGE","SEN":"SENTIER","VAL":"VALLEE","VOI":"VOIE",
        "PKG":"PARKING","RLE":"RUELLE"
    }
    df_j.replace({"voie_type": dico}, inplace=True)

    df_j["raison_sociale"] = df_j["raison_sociale"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    df_j["adresse"] = (
        df_j["voie_numero"].apply(lambda x: str(x).replace(".0","").replace("nan","")) +
        df_j["voie_complement"].apply(lambda x: str(x).replace(".0","").replace("nan","")) + " " +
        df_j["voie_type"].astype(str) + " " +
        df_j["voie_label"].astype(str)
    ).str.strip()
    df_j["code_postal"] = df_j["ligne_acheminement"].apply(lambda x: str(re.search(r"\d\d\d\d\d|\$", str(x))[0]))
    df_j["ville"] = df_j["ligne_acheminement"].apply(lambda x: re.split(r"\d\d\d\d\d|\$", str(x))[1].strip(" "))
    df_j["telephone"] = df_j["telephone"].apply(lambda x: ("+33" + str(x).replace(".0","")).replace("+33nan",""))
    df_j["numero_de_siren"] = df_j["numero_de_siren"].apply(lambda x: str(x).replace(".0","").replace("nan",""))
    df_j["code_APE"] = df_j["code_APE"].apply(lambda x: str(x).replace(" ","").replace("nan",""))
    df_j["statut_juridique"] = df_j["statut_juridique"].apply(lambda x: str(x).replace(".0","").replace("nan",""))

    to_keep_juridique = [
        "numero_finess","numero_de_siren","code_APE","raison_sociale","raison_sociale_long",
        "raison_sociale_complement","distribution_complement","adresse","lieu_dit_bp",
        "code_postal","ville","commune","telephone","statut_juridique","statut_juridique_libel",
        "categorie_etablissement","libelle_categorie_etablissement","date_de_creation"
    ]
    final_j = df_j[to_keep_juridique].copy()
    return final_j

def normalize_address_value(street: str, zipcode: str):
    if pd.isna(street) or pd.isna(zipcode):
        return None
    s = str(street).upper().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    z = str(zipcode).replace(".0","").strip()
    return f"{s}|{z}"

def add_address_normalized(df, street_col, zipcode_col, out_col="address_normalized"):
    df[out_col] = df.apply(lambda row: normalize_address_value(row.get(street_col), row.get(zipcode_col)), axis=1)
    return df

def export_df_download(df, filename_prefix):
    if df is None or len(df) == 0:
        return None, None
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    today = datetime.now().strftime("%Y%m%d")
    filename = f"{filename_prefix}_{today}.csv"
    return csv_bytes, filename


# Labs & SELAS comparison + creation

def compute_selas_creation(final_finess_etabs, final_finess_juridique, df_selas_sf):
    # Scope labs (code_categorie 611/612)
    scope = ["611", "612"]
    final_scope = final_finess_etabs[final_finess_etabs["code_categorie"].isin(scope)].copy()

    # SELAS à créer = entités juridiques présentes dans FINESS 2025 mais absentes de SF
    finess_selas_sf = set(df_selas_sf["numero_finess"].astype(str).str.strip())
    finess_juridique_2025_list = (
        final_scope[final_scope["numero_finess_juridique"].notna()]["numero_finess_juridique"]
        .astype(str).str.strip().unique()
    )
    finess_selas_to_create = [f for f in finess_juridique_2025_list if f not in finess_selas_sf]

    df_selas_to_create = final_finess_juridique[
        final_finess_juridique["numero_finess"].isin(finess_selas_to_create)
    ].copy()

    # Export format SELAS
    if len(df_selas_to_create) > 0:
        df_selas_export = pd.DataFrame()
        df_selas_export["account name"] = df_selas_to_create["raison_sociale"].values
        df_selas_export["finessnumber__c"] = df_selas_to_create["numero_finess"].values
        df_selas_export["billingstreet"] = df_selas_to_create["adresse"].values
        df_selas_export["billingpostalcode"] = df_selas_to_create["code_postal"].values
        df_selas_export["billingcity"] = df_selas_to_create["ville"].values
        df_selas_export["phone"] = df_selas_to_create["telephone"].values
        df_selas_export["recordtypeid"] = "0121i000000kJplAAE"
        df_selas_export["organisationtype__c"] = "Laboratory"
        df_selas_export["billingcountrycode"] = "FR"
        df_selas_export["numero_de_siren"] = df_selas_to_create["numero_de_siren"].values 
        df_selas_export["createddate"] = df_selas_to_create["date_de_creation"].values  

        # Filtre adresse non vide
        nb_avant = len(df_selas_export)
        df_selas_export = df_selas_export[
            (df_selas_export["billingstreet"].notna()) &
            (df_selas_export["billingstreet"].astype(str).str.strip() != "") &
            (df_selas_export["billingstreet"].astype(str).str.strip() != "nan")
        ]
        exclues = nb_avant - len(df_selas_export)
    else:
        df_selas_export, exclues = pd.DataFrame(), 0

    return df_selas_to_create, df_selas_export, exclues

def compute_labs_and_hierarchy(final_finess_etabs, final_finess_juridique, df_labs_sf, df_selas_sf):
    # Scope labs (code_categorie 611/612)
    scope = ["611","612"]
    final_scope = final_finess_etabs[final_finess_etabs["code_categorie"].isin(scope)].copy()

    # Adresses normalisées (important pour matching process)
    df_labs_sf = df_labs_sf.copy()
    df_selas_sf = df_selas_sf.copy()
    add_address_normalized(df_labs_sf, "street", "zipcode")
    add_address_normalized(final_scope, "adresse", "code_postal")

    # Filtrer FINESS avec adresse valide
    final_scope_with_address = final_scope[
        (final_scope["voie_label"].notna()) &
        (final_scope["voie_label"].astype(str).str.strip() != "") &
        (final_scope["voie_label"].astype(str).str.strip() != "nan")
    ].copy()

    # Matching par FINESS
    finess_labs_sf = set(df_labs_sf["numero_finess"].astype(str).str.strip())
    finess_labs_2025_list = final_scope_with_address["numero_finess"].astype(str).str.strip().unique()
    labs_matched_by_finess = set(finess_labs_2025_list) & finess_labs_sf
    labs_not_matched_by_finess = set(finess_labs_2025_list) - finess_labs_sf

    # Matching par adresse
    address_sf = set(df_labs_sf["address_normalized"].dropna())
    address_finess = set(final_scope_with_address["address_normalized"].dropna())
    labs_matched_by_address_normalized = address_finess & address_sf

    finess_from_address_match = set(
        final_scope_with_address[
            final_scope_with_address["address_normalized"].isin(labs_matched_by_address_normalized)
        ]["numero_finess"].astype(str)
    )

    only_finess_match = labs_matched_by_finess - finess_from_address_match
    only_address_match = finess_from_address_match - labs_matched_by_finess
    both_match = labs_matched_by_finess & finess_from_address_match

    # Labs à créer (union des 2 méthodes)
    all_matched = labs_matched_by_finess | finess_from_address_match
    finess_labs_to_create = [f for f in finess_labs_2025_list if f not in all_matched]

    df_labs_to_create = final_scope_with_address[
        final_scope_with_address["numero_finess"].astype(str).isin(finess_labs_to_create)
    ].copy()

    # Export format Labs
    if len(df_labs_to_create) > 0:
        df_labs_export = pd.DataFrame()
        df_labs_export["account name"] = df_labs_to_create["raison_sociale"]
        df_labs_export["finessnumber__c"] = df_labs_to_create["numero_finess"].astype(str)
        df_labs_export["siret"] = df_labs_to_create["siret"]  # NOUVEAU
        df_labs_export["createddate"] = df_labs_to_create["date_ouverture"]  # NOUVEAU
        df_labs_export["billingstreet"] = (
            df_labs_to_create["voie_numero"].astype(str).str.replace(".0","").str.replace("nan","") + " " +
            df_labs_to_create["voie_type"].astype(str).str.replace("nan","") + " " +
            df_labs_to_create["voie_label"].astype(str).str.replace("nan","")
        ).str.strip()
        df_labs_export["billingpostalcode"] = df_labs_to_create["code_postal"]
        df_labs_export["billingcity"] = df_labs_to_create["ville"]
        df_labs_export["phone"] = df_labs_to_create["telephone"]

        # Parent_id via SELAS SF
        selas_mapping = df_selas_sf.set_index("numero_finess")["id"].to_dict()
        parent = df_labs_to_create["numero_finess_juridique"].astype(str).map(selas_mapping)
        df_labs_export["Parent_id"] = parent.fillna(" ")

        df_labs_export["recordtypeid"] = "0121i000000kJpkAAE"
        df_labs_export["organisationtype__c"] = "Laboratory"
        df_labs_export["billingcountrycode"] = "FR"

        nb_avant = len(df_labs_export)
        df_labs_export = df_labs_export[
            (df_labs_export["billingstreet"].notna()) &
            (df_labs_export["billingstreet"].astype(str).str.strip() != "")
        ]
        exclues = nb_avant - len(df_labs_export)
    else:
        df_labs_export, exclues = pd.DataFrame(), 0
    
    # Contrôle hiérarchie
    df_labs_sf_clean = df_labs_sf[
        (df_labs_sf["numero_finess"].notna()) & (df_labs_sf["selas_id"].notna())
    ].copy()

    # Map selas_id -> finess selas
    selas_id_to_finess = df_selas_sf.set_index("id")["numero_finess"].to_dict()
    df_labs_sf_clean["selas_finess_sf"] = df_labs_sf_clean["selas_id"].map(selas_id_to_finess)
    df_labs_sf_clean["numero_finess"] = df_labs_sf_clean["numero_finess"].astype(str).str.strip()
    df_labs_sf_clean["selas_finess_sf"] = df_labs_sf_clean["selas_finess_sf"].astype(str).str.strip()

    final_scope_hierarchy = final_scope[
        (final_scope["numero_finess"].notna()) & (final_scope["numero_finess_juridique"].notna())
    ].copy()
    final_scope_hierarchy["numero_finess"] = final_scope_hierarchy["numero_finess"].astype(str).str.strip()
    final_scope_hierarchy["numero_finess_juridique"] = final_scope_hierarchy["numero_finess_juridique"].astype(str).str.strip()

    comparison = df_labs_sf_clean.merge(
        final_scope_hierarchy[["numero_finess", "numero_finess_juridique"]],
        on="numero_finess", how="inner", suffixes=("_sf", "_finess")
    )

    comparison["hierarchy_changed"] = comparison["selas_finess_sf"] != comparison["numero_finess_juridique"]
    nb_changes = int(comparison["hierarchy_changed"].sum())

    changes = comparison[comparison["hierarchy_changed"]].copy()
    selas_finess_in_sf = set(df_selas_sf["numero_finess"].astype(str).str.strip())
    changes["new_selas_in_sf"] = changes["numero_finess_juridique"].isin(selas_finess_in_sf)

    changes_with_existing_selas = changes[changes["new_selas_in_sf"]].copy()
    changes_with_new_selas = changes[~changes["new_selas_in_sf"]].copy()

    # Si existante, ajouter new_selas_id
    df_hierarchy_update = pd.DataFrame()
    if len(changes_with_existing_selas) > 0:
        selas_finess_to_id = df_selas_sf.set_index("numero_finess")["id"].to_dict()
        changes_with_existing_selas["new_selas_id"] = changes_with_existing_selas["numero_finess_juridique"].map(selas_finess_to_id)

        df_hierarchy_update["id"] = changes_with_existing_selas["id"]
        df_hierarchy_update["parent_id"] = changes_with_existing_selas["new_selas_id"]

    metrics = {
        "labs_total_finess": int(len(final_scope)),
        "labs_with_addr": int(len(final_scope[
            (final_scope["voie_label"].notna()) &
            (final_scope["voie_label"].astype(str).str.strip() != "") &
            (final_scope["voie_label"].astype(str).str.strip() != "nan")
        ])),
        "matched_by_finess": int(len(labs_matched_by_finess)),
        "matched_by_address": int(len(finess_from_address_match)),
        "both_match": int(len(both_match)),
        "only_finess_match": int(len(only_finess_match)),
        "only_address_match": int(len(only_address_match)),
        "labs_to_create": int(len(df_labs_export)),
        "labs_excluded_no_addr": int(exclues),
        "hierarchy_changes": nb_changes,
        "hierarchy_changes_existing_selas": int(len(changes_with_existing_selas)),
        "hierarchy_changes_new_selas": int(len(changes_with_new_selas)),
    }

    return (
        df_labs_export,
        df_hierarchy_update,
        metrics,
        changes_with_existing_selas.head(10),
        changes_with_new_selas.head(10)
    )



# part gsheet update 


def clean_value(x):
    return str(x).replace('.0', '').replace('nan', '').replace('None', '').strip()

def extract_postal(x):
    match = re.search(r'\d{5}', str(x))
    if match:
        return match.group(0).zfill(5)
    return ''

def extract_city(x):
    parts = re.split(r'\d{5}', str(x))
    return parts[1].strip() if len(parts) > 1 else ''

def process_gsheet_update(gsheet_csv, final_finess_etabs, final_finess_juridique):
    """
    Mise à jour du GSheet avec la base FINESS
    """
    # Dictionnaire SELAS
    selas_dict = dict(zip(final_finess_juridique['numero_finess'], final_finess_juridique['raison_sociale']))
    
    # Charger le gsheet
    gsheet_labs = pd.read_csv(gsheet_csv, dtype=str)
    
    # Nettoyer les colonnes (important pour matching)
    gsheet_labs['numero_finess'] = gsheet_labs['numero_finess'].apply(clean_value)
    gsheet_labs['numero_finess_juridique'] = gsheet_labs['numero_finess_juridique'].apply(clean_value)
    gsheet_labs['raison_sociale'] = gsheet_labs['raison_sociale'].apply(clean_value)
    gsheet_labs['raison_sociale_longue'] = gsheet_labs['raison_sociale_longue'].apply(clean_value)
    gsheet_labs['selas'] = gsheet_labs['selas'].apply(clean_value)
    
    stats = {
        'selas_completes': 0,
        'raison_sociale': 0,
        'raison_sociale_longue': 0,
        'numero_finess_juridique': 0,
        'selas_updates': 0,
        'nouveaux_labs': 0
    }
    
    # Compléter SELAS vides (parfois on a le numéro finess juridique mais pas le nom de la SELAS dans la base finess juridique, 
    # l'idée est de voir si deux mois plus tard on l'a)
    selas_vides = gsheet_labs['selas'] == ''
    for idx, row in gsheet_labs[selas_vides].iterrows():
        numero_juridique = clean_value(row['numero_finess_juridique'])
        if numero_juridique:
            selas_name = selas_dict.get(numero_juridique, '')
            if selas_name:
                gsheet_labs.at[idx, 'selas'] = selas_name
                stats['selas_completes'] += 1
    
    # Mise à jour des labos existants
    for idx, row in gsheet_labs.iterrows():
        numero_finess = clean_value(row['numero_finess'])
        finess_row = final_finess_etabs[final_finess_etabs['numero_finess'] == numero_finess]
        
        if not finess_row.empty:
            finess_row = finess_row.iloc[0]
            
            # Raison sociale
            if clean_value(row['raison_sociale']) != clean_value(finess_row['raison_sociale']):
                gsheet_labs.at[idx, 'raison_sociale'] = clean_value(finess_row['raison_sociale'])
                stats['raison_sociale'] += 1
            
            # Raison sociale longue
            if clean_value(row['raison_sociale_longue']) != clean_value(finess_row['raison_sociale_long']):
                gsheet_labs.at[idx, 'raison_sociale_longue'] = clean_value(finess_row['raison_sociale_long'])
                stats['raison_sociale_longue'] += 1
            
            # Numéro FINESS juridique
            if clean_value(row['numero_finess_juridique']) != clean_value(finess_row['numero_finess_juridique']):
                new_juridique = clean_value(finess_row['numero_finess_juridique'])
                gsheet_labs.at[idx, 'numero_finess_juridique'] = new_juridique
                stats['numero_finess_juridique'] += 1
                
                # Mettre à jour SELAS
                new_selas = selas_dict.get(new_juridique, '')
                gsheet_labs.at[idx, 'selas'] = new_selas
                stats['selas_updates'] += 1
                
                # Effacer labo_group
                gsheet_labs.at[idx, 'labo_group'] = ''
    
    # Ajouter nouveaux laboratoires
    existing_finess = set(gsheet_labs['numero_finess'])
    new_labs = final_finess_etabs[~final_finess_etabs['numero_finess'].isin(existing_finess)].copy()
    
    if len(new_labs) > 0:
        nouvelles_lignes = []
        
        for _, lab in new_labs.iterrows():
            selas_name = selas_dict.get(clean_value(lab['numero_finess_juridique']), '')
            
            # Dictionnaire voies
            dico = {
                'R':'RUE', 'PL':'PLACE', 'RTE':'ROUTE', 'AV':'AVENUE', 'GR':'GRANDE RUE', 'ALL':'ALLEE',
                'CHE':'CHEMIN', 'QUA':'QUARTIER', 'BD':'BOULEVARD', 'PROM':'PROMENADE', 'ZA':'ZONE ARTISANALE',
                'QU':'QUAI', 'ESPA':'ESPACE', 'IMP':'IMPASSE', 'LD':'LIEU DIT', 'SQ':'SQUARE',
                'LOT':'LOTISSEMENT', 'ZAC':"ZONE D'AMENAGEMENT CONCERTE", 'IMM':'IMMEUBLE', 'RES':'RESIDENCE',
                'CRS':'COURS', 'ESP':'ESPLANADE', 'FG':'FAUBOURG', 'CHS':'CHAUSSEE', 'MTE':'MONTEE',
                'DOM':'DOMAINE', 'PAS':'PASSAGE', 'SEN':'SENTIER', 'VAL':'VALLEE', 'VOI':'VOIE',
                'PKG':'PARKING', 'RLE':'RUELLE'
            }
            
            voie_type_complet = dico.get(str(lab['voie_type']), str(lab['voie_type']))
            adress = f"{clean_value(lab['voie_numero'])} {clean_value(lab['voie_complement'])} {voie_type_complet} {clean_value(lab['voie_label'])}".strip()
            adress = re.sub(r'\s+', ' ', adress)
            
            nouvelle_ligne = {
                'numero_finess': lab['numero_finess'],
                'numero_finess_juridique': lab['numero_finess_juridique'],
                'raison_sociale': clean_value(lab['raison_sociale']),
                'raison_sociale_longue': clean_value(lab['raison_sociale_long']),
                'selas': selas_name,
                'labo_group': '',
                'complement_raison_sociale': clean_value(lab['raison_sociale_complement']),
                'complement_de_distribution': clean_value(lab['distribution_complement']),
                'numer_de_voie': clean_value(lab['voie_numero']),
                'type_de_voie': str(lab['voie_type']),
                'libelle_de_voie': clean_value(lab['voie_label']),
                'complement_de_voie': clean_value(lab['voie_complement']),
                'lieu': clean_value(lab['lieu_dit_bp']),
                'code_commune': clean_value(lab['ville']),
                'departement': str(lab['departement']),
                'libelle_departement': str(lab['departement_label']),
                'ligne_acheminement': str(lab['libelle_routage']),
                'adress': adress,
                'code_postal': extract_postal(lab['libelle_routage']),
                'city': extract_city(lab['libelle_routage']),
                'telephone': str(lab['telephone']),
                'fax': str(lab['fax']),
                'code_categorie': clean_value(lab['code_categorie']),
                'libelle_categorie': str(lab['label_categorie']),
                'categorie_agregat_etablissement': '',
                'libelle_categorie_agregat_etablissement': '',
                'siret': clean_value(lab['siret']),
                'code_ape': clean_value(lab['ape']),
                'code_mft': '',
                'libelle_mft': '',
                'code_sph': clean_value(lab['code_psph']),
                'libelle_sph': str(lab['label_psph']),
                'date_ouverture': str(lab['date_ouverture']),
                'date_autorisation': str(lab['date_autor']),
                'date_mise_jour': str(lab['date_update'])
            }
            
            nouvelles_lignes.append(nouvelle_ligne)
        
        df_nouvelles = pd.DataFrame(nouvelles_lignes)
        gsheet_updated = pd.concat([gsheet_labs, df_nouvelles], ignore_index=True)
        stats['nouveaux_labs'] = len(nouvelles_lignes)
    else:
        gsheet_updated = gsheet_labs
    
    # Forcer code postal en format texte (important sinon je n'ai pas le 0 pour les codes postaux commençant par 0)
    gsheet_updated['code_postal'] = "'" + gsheet_updated['code_postal'].astype(str)
    
    return gsheet_updated, stats












# UI

st.markdown("<h1 style='text-align: center;'>🏢 TAM Labo 🏢</h1>", unsafe_allow_html=True)
st.markdown("📚 **Documentation:** [Labo TAM: DQ ops process](https://doctolib.atlassian.net/wiki/x/MQCnww)")
st.info(f"Process DQ Ops – Dashboard Metabase: {METABASE_URL}", icon="ℹ️")

tab1, tab2, tab3, tab4 = st.tabs(["Day 1 – SELAS", "Day 2 – Labs + Hierarchy", "DQProject - Gsheet", "Download FINESS Labs"])

with tab1:
    st.markdown("### Step Day 1: Create new SELAS")
    st.write("1. In Metabase, Download DQ Ops SELAS")
    uploaded_selas_sf = st.file_uploader("Upload CSV DQ Ops SELAS", type=["csv"], key="selas_j1")

    if st.button("Run - Day 1"):
        if uploaded_selas_sf is None:
            st.error("Please upload CSV DQ Ops SELAS.")
        else:
            try:
                url_etabs, url_juridique = fetch_latest_finess_urls()
                fin_etabs = load_finess_etablissements(url_etabs)
                fin_juridique = load_finess_juridique(url_juridique)

                df_selas_sf = pd.read_csv(uploaded_selas_sf)

                _, df_selas_export, exclues = compute_selas_creation(fin_etabs, fin_juridique, df_selas_sf)

                st.success(f"SELAS export: {len(df_selas_export)}")
                st.dataframe(df_selas_export.head(20), use_container_width=True)

                csv_bytes, filename = export_df_download(df_selas_export, "selas_to_create")
                if csv_bytes:
                    st.download_button("📥 Download CSV SELAS to create", data=csv_bytes, file_name=filename, mime="text/csv")
                    st.caption("Add it to a new file in the drive: TAM Labo backup (LaboTAM_MM_YY)")
                else:
                    st.info("No SELAS to create detected")
            except Exception as e:
                st.exception(e)

with tab2:
    st.markdown("### Step Day 2: New Labs + Hierarchy")
    st.write("1. In Metabase, Download DQ Ops Laboratories and DQ Ops SELAS (day 2)")
    uploaded_labs_sf = st.file_uploader("Upload CSV DQ Ops Laboratories", type=["csv"], key="labs_j2")
    uploaded_selas_sf_2 = st.file_uploader("Upload CSV DQ Ops SELAS", type=["csv"], key="selas_j2")

    if st.button("Run - Day 2"):
        if uploaded_labs_sf is None or uploaded_selas_sf_2 is None:
            st.error("Please upload CSV DQ Ops Labs & DQ Ops SELAS.")
        else:
            try:
                url_etabs, url_juridique = fetch_latest_finess_urls()
                fin_etabs = load_finess_etablissements(url_etabs)
                fin_juridique = load_finess_juridique(url_juridique)

                df_labs_sf = pd.read_csv(uploaded_labs_sf)
                df_selas_sf = pd.read_csv(uploaded_selas_sf_2)

                df_labs_export, df_hierarchy_update, metrics, preview_existing, preview_new = \
                    compute_labs_and_hierarchy(fin_etabs, fin_juridique, df_labs_sf, df_selas_sf)

                st.subheader("Export – New Labs")
                st.dataframe(df_labs_export.head(20), use_container_width=True)
                csv_labs, filename_labs = export_df_download(df_labs_export, "labs_to_create")
                if csv_labs:
                    st.download_button("📥 Download CSV Labs", data=csv_labs, file_name=filename_labs, mime="text/csv")
                else:
                    st.info("Aucun laboratoire à créer détecté (ou adresses exclues).")

                st.caption(f"Excluded for empty address: {metrics['labs_excluded_no_addr']}")

                st.markdown("---")
                st.subheader("Hierarchy Control")

                if len(df_hierarchy_update) > 0:
                    st.dataframe(df_hierarchy_update.head(20), use_container_width=True)
                    csv_h, filename_h = export_df_download(df_hierarchy_update, "labs_hierarchy_update")
                    st.download_button("📥 Download CSV Hierarchy", data=csv_h, file_name=filename_h, mime="text/csv")
                    st.caption("This file contains lab_id, old/new selas (id/finess) to be updated.")
                else:
                    st.info("No hierarchy updates to apply with existing SELAS.")

                st.markdown("---")
                st.write("Add the downloaded files to the same Drive file as the SELAS (Day 1)")

            except Exception as e:
                st.exception(e)

with tab3:
    st.markdown("### DQProject - Gsheet Update")
    st.write("Upload your current Google Sheet CSV to update it with the latest FINESS data.")
    
    uploaded_gsheet = st.file_uploader("Upload Current Gsheet CSV (tam_labo)", type=["csv"], key="gsheet_upload")
    
    if st.button("Run - Gsheet Update"):
        if uploaded_gsheet is None:
            st.error("Please upload the current Gsheet CSV.")
        else:
            try:
                with st.spinner("Loading FINESS databases..."):
                    url_etabs, url_juridique = fetch_latest_finess_urls()
                    fin_etabs = load_finess_etablissements(url_etabs)
                    fin_juridique = load_finess_juridique(url_juridique)
                    
                    # Nettoyer et préparer FINESS
                    fin_etabs['code_categorie'] = fin_etabs['code_categorie'].apply(clean_value)
                    scope = ["611", "612"]
                    fin_etabs = fin_etabs[fin_etabs['code_categorie'].isin(scope)].copy()
                    
                    # Nettoyage colonnes FINESS
                    for col in ['raison_sociale', 'raison_sociale_long', 'raison_sociale_complement', 
                               'distribution_complement', 'voie_numero', 'voie_complement', 
                               'lieu_dit_bp', 'ville', 'voie_label']:
                        if col in fin_etabs.columns:
                            fin_etabs[col] = fin_etabs[col].apply(clean_value)
                    
                    fin_etabs['code_postal'] = fin_etabs['libelle_routage'].apply(extract_postal)
                    fin_etabs['city'] = fin_etabs['libelle_routage'].apply(extract_city)
                    
                    fin_juridique['numero_finess'] = fin_juridique['numero_finess'].apply(clean_value)
                    fin_juridique['raison_sociale'] = fin_juridique['raison_sociale'].apply(clean_value)
                
                with st.spinner("Processing Gsheet update..."):
                    gsheet_updated, stats = process_gsheet_update(uploaded_gsheet, fin_etabs, fin_juridique)
                
                st.success("Gsheet updated successfully!")
                
                # Afficher les statistiques
                col1, col2, col3 = st.columns(3)
                col1.metric("SELAS complétées", stats['selas_completes'])
                col2.metric("Raisons sociales modifiées", stats['raison_sociale'] + stats['raison_sociale_longue'])
                col3.metric("Numéros juridiques modifiés", stats['numero_finess_juridique'])
                
                col1.metric("SELAS mises à jour", stats['selas_updates'])
                col2.metric("Nouveaux laboratoires", stats['nouveaux_labs'])
                col3.metric("Total lignes", len(gsheet_updated))
                
                st.markdown("---")
                
                # Export
                csv_bytes, filename = export_df_download(gsheet_updated, "gsheet_tam_labo_updated")
                if csv_bytes:
                    st.download_button(
                        "📥 Download Updated Gsheet CSV",
                        data=csv_bytes,
                        file_name=filename,
                        mime="text/csv"
                    )
            except Exception as e:
                st.exception(e)

with tab4:
    st.markdown("### Download FINESS Labs Database")
    st.write("Download the complete FINESS database filtered for laboratories (codes 611 and 612).")
    st.info("Source: https://www.data.gouv.fr/datasets/finess-extraction-du-fichier-des-etablissements/", icon="ℹ️")
    
    if st.button("📥 Run FINESS Labs Database"):
        try:
            with st.spinner("Fetching latest FINESS data..."):
                url_etabs, url_juridique = fetch_latest_finess_urls()
                fin_etabs = load_finess_etablissements(url_etabs)
                
                # Filter for laboratories (code_categorie 611 and 612)
                scope = ["611", "612"]
                fin_etabs_labs = fin_etabs[fin_etabs["code_categorie"].isin(scope)].copy()
                
                st.success(f"✅ FINESS Labs database loaded: {len(fin_etabs_labs)} laboratories found")
                
                # Display preview
                st.dataframe(fin_etabs_labs.head(20), use_container_width=True)
                
                # Generate download
                csv_bytes, filename = export_df_download(fin_etabs_labs, "finess_labs_database")
                if csv_bytes:
                    st.download_button(
                        "📥 Download Complete FINESS Labs CSV",
                        data=csv_bytes,
                        file_name=filename,
                        mime="text/csv",
                        key="download_finess_labs"
                    )
                    
                    # Display statistics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Labs", len(fin_etabs_labs))
                    col2.metric("With Complete Address", 
                               len(fin_etabs_labs[
                                   (fin_etabs_labs["voie_label"].notna()) & 
                                   (fin_etabs_labs["voie_label"].astype(str).str.strip() != "")
                               ]))
        except Exception as e:
            st.error(f"Error fetching FINESS data: {str(e)}")
            st.exception(e)