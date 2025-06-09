import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.stats import kruskal
import seaborn as sns
import numpy as np

# --- Chargement des données
df = pd.read_csv("data/donnees.csv", sep=';')

# --- Sidebar : paramètres généraux
st.sidebar.header("Paramètres généraux")
k           = st.sidebar.slider("Nombre de clusters k-means", 2, 8, 3)
use_cluster = st.sidebar.checkbox("Afficher clustering", value=False)
show_cah    = st.sidebar.checkbox("Afficher dendrogramme CAH", value=False)

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
    mode   = st.radio("Mode ACP", ["Brut", "Par 1 000 hab."])
    X_cols = cols_brut if mode == "Brut" else cols_ratio

    if not X_cols:
        st.error("Aucune colonne disponible pour l'ACP.")
        st.stop()

    # --- 1) Calcul ACP (2 composantes)
    X   = df[X_cols].fillna(0).astype(float)
    Xs  = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    comps = pca.fit_transform(Xs)
    load  = pca.components_.T

    # --- 2) Contributions & cos²
    contrib = np.square(load) * 100
    cos2    = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
    df_vars = pd.DataFrame({
        "Variable":     X_cols,
        "Contrib1 (%)": contrib[:, 0],
        "Cos2_1 (%)":   cos2[:, 0],
        "Contrib2 (%)": contrib[:, 1],
        "Cos2_2 (%)":   cos2[:, 1],
    })

    # --- 3) Préparer le DataFrame des individus
    df_ind = df.copy()
    df_ind["ACP1"] = comps[:, 0]
    df_ind["ACP2"] = comps[:, 1]

    # --- 4) Clustering optionnel (k-means)
    if use_cluster:
        km = KMeans(n_clusters=k, random_state=0)
        df_ind["cluster"] = km.fit_predict(df_ind[["ACP1", "ACP2"]]).astype(str)

    # --- 5) Scatter des communes
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

    # --- 6) Dendrogramme CAH (si demandé)
    if show_cah:
        st.subheader("Dendrogramme CAH (Ward) sur ACP1 & ACP2")
        try:
            n_max = 500
            sample = df_ind if len(df_ind) <= n_max else df_ind.sample(n_max, random_state=0)
            Z = linkage(sample[["ACP1", "ACP2"]], method='ward')
            fig_cah, ax = plt.subplots(figsize=(8, 4))
            dendrogram(Z, truncate_mode='level', p=5, ax=ax, labels=sample.index)
            ax.set_xlabel("Index de la commune")
            ax.set_ylabel("Distance")
            st.pyplot(fig_cah)
            if len(df_ind) > n_max:
                st.caption(f"(CAH sur échantillon de {n_max} communes)")
        except Exception as e:
            st.error(f"Erreur CAH : {e}")

    # --- 7) Relation cluster ↔ densité
    if use_cluster and "DENS" in df_ind.columns:
        st.subheader("Densité par cluster et test statistique")
        # Boxplot
        fig_box, ax_box = plt.subplots(figsize=(6, 4))
        sns.boxplot(x="cluster", y="DENS", data=df_ind, ax=ax_box)
        ax_box.set_title("Distribution de DENS par cluster")
        st.pyplot(fig_box)

        # Test de Kruskal-Wallis
        groups = [grp["DENS"].astype(int).values for _, grp in df_ind.groupby("cluster")]
        stat, p = kruskal(*groups)
        st.markdown(f"**Kruskal-Wallis** : H={stat:.2f}, p={p:.3g}")
        if p < 0.05:
            st.success("p < 0.05 → différence significative de densité entre clusters")
        else:
            st.info("p ≥ 0.05 → pas de différence significative")

        # ACP coloré côte-à-côte
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**ACP par cluster**")
            fig_c1 = px.scatter(df_ind, x="ACP1", y="ACP2", color="cluster",
                                title="Clusters k-means")
            st.plotly_chart(fig_c1, use_container_width=True)
        with c2:
            st.markdown("**ACP par densité**")
            fig_c2 = px.scatter(df_ind, x="ACP1", y="ACP2", color="DENS",
                                color_continuous_scale="Blues",
                                title="Niveau de densité")
            st.plotly_chart(fig_c2, use_container_width=True)

    # --- 8) Cercle de corrélations
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

    # --- 9) Tableau contributions & cos²
    st.subheader("Contributions (%) & cos² (axes 1 & 2)")
    st.dataframe(df_vars.round(2))
