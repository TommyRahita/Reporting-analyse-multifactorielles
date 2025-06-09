import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np

# --- Chargement des données
df = pd.read_csv("data/donnees.csv", sep=';')

# --- Sidebar : paramètres généraux
st.sidebar.header("Paramètres généraux")
k = st.sidebar.slider("Nombre de clusters k-means", 2, 8, 3)
use_cluster = st.sidebar.checkbox("Afficher clustering", value=False)

# --- Libellés pour extraire les colonnes
labels = {
    'D1': 'Etablissements_de_sante_humaine',
    'D2': 'Equipements_medico_paramedicaux',
    'D3': 'Structures_de_sante_publique',
    'D4': 'Actions_sociales',
    'D5': 'Hebergements_sociaux',
    'D6': 'Equipements_educatifs_sportifs',
    'D7': 'Autres_equipements'
}

# Colonnes brutes et ratios
cols_brut  = [f"{d}_{lbl}"      for d,lbl in labels.items() if f"{d}_{lbl}" in df.columns]
cols_ratio = [f"{d}_{lbl}_1000" for d,lbl in labels.items() if f"{d}_{lbl}_1000" in df.columns]

# --- Menu principal
menu = st.sidebar.radio("Navigation", ["Statistiques descriptives", "ACP comparées"])

if menu == "Statistiques descriptives":
    st.title("Statistiques descriptives")
    cols = ["nb_equipements_total"] + cols_brut + cols_ratio
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].describe().transpose().round(2))

else:
    st.title("ACP comparées : brut vs. par 1 000 hab.")
    mode = st.radio("Mode ACP", ["Brut", "Par 1 000 hab."])
    X_cols = cols_brut if mode == "Brut" else cols_ratio
    if not X_cols:
        st.error("Aucune colonne disponible pour l'ACP.")
        st.stop()

    # --- Calcul de l’ACP (2 composantes)
    X = df[X_cols].fillna(0).astype(float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    pca = PCA(n_components=2)
    comps = pca.fit_transform(Xs)
    load = pca.components_.T

    # --- Tableau des contributions & cos²
    contrib = np.square(load) * 100
    cos2    = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
    df_vars = pd.DataFrame({
        "Variable":      X_cols,
        "Contrib1 (%)":  contrib[:, 0],
        "Cos2_1 (%)":    cos2[:, 0],
        "Contrib2 (%)":  contrib[:, 1],
        "Cos2_2 (%)":    cos2[:, 1],
    })

    # --- Préparer le DataFrame des individus
    df_ind = df.copy()
    df_ind["ACP1"] = comps[:, 0]
    df_ind["ACP2"] = comps[:, 1]

    # --- Clustering optionnel
    if use_cluster:
        km = KMeans(n_clusters=k, random_state=0)
        df_ind["cluster"] = km.fit_predict(df_ind[["ACP1", "ACP2"]]).astype(str)

    # --- 1) Scatter des communes
    color_arg = "cluster" if use_cluster else ("DENS" if "DENS" in df.columns else None)
    fig1 = px.scatter(
        df_ind,
        x="ACP1", y="ACP2",
        color=color_arg,
        color_continuous_scale=None if use_cluster else "Blues",
        hover_name="LIBGEO" if "LIBGEO" in df_ind.columns else None,
        title=f"Projection des communes ({mode})" + (" avec clustering" if use_cluster else "")
    )
    st.plotly_chart(fig1, use_container_width=True)

    # --- 2) Cercle de corrélations
    fig2, ax = plt.subplots(figsize=(6, 6))
    circle = plt.Circle((0, 0), 1, color="gray", fill=False)
    ax.add_artist(circle)
    ax.axhline(0, color="gray", linestyle="--")
    ax.axvline(0, color="gray", linestyle="--")
    for i, var in enumerate(X_cols):
        ax.arrow(0, 0, load[i, 0], load[i, 1],
                 head_width=0.03, head_length=0.03, color="blue", alpha=0.7)
        ax.text(load[i, 0] * 1.1, load[i, 1] * 1.1, var, fontsize=8)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_title(f"Cercle de corrélations ({mode})")
    st.pyplot(fig2)

    # --- 3) Tableau contributions & cos²
    st.subheader("Contributions (%) & cos² (axes 1 & 2)")
    st.dataframe(df_vars.round(2))
