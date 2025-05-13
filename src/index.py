import streamlit as st
import pandas as pd
import plotly.express as px

# Chargement de la nouvelle base
df = pd.read_csv("data/BASE_FINAL.csv", encoding='utf-8')

# === Interface Streamlit ===
st.set_page_config(page_title="Analyse Santé", layout="wide")
st.title("Reporting - Équipements de santé par commune")

# --- Menu de navigation ---
menu = st.sidebar.radio("Navigation", [
    "Résumé des communes",
    "Scatterplot santé",
    "Histogramme indicateur santé",
    "Communes sous-dotées"
])

# --- Filtres globaux ---
st.sidebar.header("Filtres")
departements = df["Departement"].unique()
dep_selected = st.sidebar.selectbox("Choisir un département", sorted(departements))
pop_min, pop_max = st.sidebar.slider("Plage de population", int(df["Population"].min()), int(df["Population"].max()), (10000, 20000))
df_filtered = df[(df["Département"] == dep_selected) &
                 (df["Population"] >= pop_min) &
                 (df["Population"] <= pop_max)]

# --- Pages ---
if menu == "Résumé des communes":
    st.subheader("Résumé des communes sélectionnées")
    st.dataframe(df_filtered[["Nom_Commune", "Population", "Densité_INSEE", "Nb_Equip_Santé", "Equip_Santé_par_1000h", "Diversité_Equipements"]])

elif menu == "Scatterplot santé":
    st.subheader("Équipements santé vs diversité")
    fig1 = px.scatter(df_filtered, x="Nb_Equip_Santé", y="Diversité_Equipements",
                      hover_name="Nom_Commune", size="Population",
                      title="Équipements santé totaux vs diversité")
    st.plotly_chart(fig1)

elif menu == "Histogramme indicateur santé":
    st.subheader("Histogramme d'un indicateur")
    indicateurs = [col for col in df.columns if "santé" in col.lower() or "Equip" in col and "par_1000h" in col]
    indicateur = st.selectbox("Choisir un indicateur", indicateurs)
    fig2 = px.histogram(df_filtered, x=indicateur, nbins=10, title=f"Répartition de {indicateur}")
    st.plotly_chart(fig2)

elif menu == "Communes sous-dotées":
    st.subheader("Communes les plus sous-dotées (santé)")
    nb_affichage = st.slider("Nombre de communes à afficher", 1, 20, 5)
    col_tri = st.selectbox("Critère de tri", ["Equip_Santé_par_1000h", "Diversité_Equipements", "Distance_profil_moyen"])
    st.dataframe(df_filtered.sort_values(by=col_tri).head(nb_affichage))
