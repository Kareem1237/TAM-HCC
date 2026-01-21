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