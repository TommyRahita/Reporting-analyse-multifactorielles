import streamlit as st
import pandas as pd
import plotly.express as px

# === Données factices ===
data = {
    "Nom_Commune": ["Testville", "Exemple-sur-Mer", "DemoCity", "Mockbourg", "DataTown"],
    "Département": ["01", "01", "02", "02", "03"],
    "Population": [12000, 15000, 18000, 13000, 17000],
    "Densité_INSEE": [5, 4, 3, 5, 2],
    "Equip_Totaux": [30, 20, 45, 15, 28],
    "Diversité_Equipements": [6, 5, 8, 3, 6],
    "Equip_Santé_par_1000h": [2.5, 1.8, 3.1, 1.2, 2.0],
    "Equip_Education_par_1000h": [3.2, 2.9, 4.0, 1.5, 2.8],
    "Equip_Total_par_1000h": [7.0, 6.1, 9.8, 4.0, 6.6],
    "Distance_profil_moyen": [0.8, 1.1, 0.5, 1.3, 0.9]
}
df = pd.DataFrame(data)

# === Interface Streamlit ===
st.set_page_config(page_title="Maquette Reporting", layout="wide")
st.title("Maquette - Analyse des équipements par commune")

# --- Menu de navigation ---
menu = st.sidebar.radio("Navigation", [
    "Résumé des communes",
    "Scatterplot équipements",
    "Histogramme d'un indicateur",
    "Communes sous-dotées"
])

# --- Filtres globaux ---
st.sidebar.header("Filtres")
departements = df["Département"].unique()
dep_selected = st.sidebar.selectbox("Choisir un département", sorted(departements))
pop_min, pop_max = st.sidebar.slider("Plage de population", int(df["Population"].min()), int(df["Population"].max()), (10000, 20000))
df_filtered = df[(df["Département"] == dep_selected) &
                 (df["Population"] >= pop_min) &
                 (df["Population"] <= pop_max)]

# --- Pages ---
if menu == "Résumé des communes":
    st.subheader("Résumé des communes sélectionnées")
    st.dataframe(df_filtered[["Nom_Commune", "Population", "Densité_INSEE", "Equip_Totaux", "Diversité_Equipements"]])

elif menu == "Scatterplot équipements":
    st.subheader("Totaux vs Diversité d'équipements")
    fig1 = px.scatter(df_filtered, x="Equip_Totaux", y="Diversité_Equipements",
                      hover_name="Nom_Commune", size="Population",
                      title="Équipements totaux vs diversité")
    st.plotly_chart(fig1)

elif menu == "Histogramme d'un indicateur":
    st.subheader("Histogramme d'un indicateur")
    indicateurs = [col for col in df.columns if col.endswith("par_1000h")]
    indicateur = st.selectbox("Choisir un indicateur", indicateurs)
    fig2 = px.histogram(df_filtered, x=indicateur, nbins=10, title=f"Répartition de {indicateur}")
    st.plotly_chart(fig2)

elif menu == "Communes sous-dotées":
    st.subheader("Communes les plus sous-dotées")
    nb_affichage = st.slider("Nombre de communes à afficher", 1, 10, 5)
    col_tri = st.selectbox("Critère de tri", ["Equip_Total_par_1000h", "Diversité_Equipements", "Distance_profil_moyen"])
    st.dataframe(df_filtered.sort_values(by=col_tri).head(nb_affichage))
