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

# --- 0. Chargement des données
df = pd.read_csv("data/donnees.csv", sep=';')

# --- 1. Sidebar : paramètres généraux
st.sidebar.header("Paramètres généraux")
k_clusters  = st.sidebar.slider("Nombre de clusters k-means", 2, 8, 3)
use_cluster = st.sidebar.checkbox("Afficher clustering", value=False)
show_cah    = st.sidebar.checkbox("Afficher dendrogramme CAH", value=False)

# --- 2. Définitions des domaines D1…D7
labels = {
    'D1': 'Etablissements_de_sante_humaine',
    'D2': 'Equipements_medico_paramedicaux',
    'D3': 'Structures_de_sante_publique',
    'D4': 'Actions_sociales',
    'D5': 'Hebergements_sociaux',
    'D6': 'Equipements_educatifs_sportifs',
    'D7': 'Autres_equipements'
}
cols_brut  = [f"{d}_{lbl}"      for d,lbl in labels.items() if f"{d}_{lbl}" in df.columns]
cols_ratio = [f"{d}_{lbl}_1000" for d,lbl in labels.items() if f"{d}_{lbl}_1000" in df.columns]

# --- 3. Menu principal
menu = st.sidebar.radio("Navigation", ["Statistiques descriptives", "ACP comparées"])

if menu == "Statistiques descriptives":
    st.title("📊 Statistiques descriptives")
    cols = ["nb_equipements_total"] + cols_brut + cols_ratio + (["DENS"] if "DENS" in df.columns else [])
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].describe().transpose().round(2))

else:
    st.title("🧮 ACP comparées : brut vs. par 1 000 hab.")
    mode   = st.radio("Mode ACP", ["Brut", "Par 1 000 hab."])
    X_cols = cols_brut if mode == "Brut" else cols_ratio
    if not X_cols:
        st.error("Aucune colonne disponible pour l'ACP.")
        st.stop()

    # --- 4. Calcul de l’ACP (jusqu'à 10 composantes max)
    X    = df[X_cols].fillna(0).astype(float)
    Xs   = StandardScaler().fit_transform(X)
    n_comp = min(10, Xs.shape[1])
    pca  = PCA(n_components=n_comp)
    comps = pca.fit_transform(Xs)
    load  = pca.components_.T

    # --- 5. Variances expliquées
    explained_var  = pca.explained_variance_ratio_ * 100
    cumulative_var = np.cumsum(explained_var)
    eigval         = pca.explained_variance_

    st.subheader("📈 Variance expliquée par composante")
    df_eigen = pd.DataFrame({
        "Composante":    [f"Comp {i+1}" for i in range(n_comp)],
        "Valeur propre": eigval.round(4),
        "% variance":    explained_var.round(2),
        "% cumulée":     cumulative_var.round(2)
    })
    st.dataframe(df_eigen)

    # --- 6. Contributions & cos² (axes 1 & 2)
    contrib = np.square(load) * 100
    cos2    = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
    df_vars = pd.DataFrame({
        "Variable":     X_cols,
        "Contrib1 (%)": contrib[:, 0],
        "Cos2_1 (%)":   cos2[:, 0],
        "Contrib2 (%)": contrib[:, 1],
        "Cos2_2 (%)":   cos2[:, 1],
    })
    st.subheader("🔢 Contributions & cos² (axes 1 & 2)")
    st.dataframe(df_vars.round(2))

    # --- 7. Préparation des scores ACP
    df_ind = df.copy()
    df_ind["ACP1"], df_ind["ACP2"] = comps[:, 0], comps[:, 1]

    # --- 8. Clustering k-means optionnel
    if use_cluster:
        km = KMeans(n_clusters=k_clusters, random_state=0)
        df_ind["cluster"] = km.fit_predict(df_ind[["ACP1", "ACP2"]]).astype(str)

    # --- 9. Cercle de corrélations
    st.subheader("🎯 Cercle de corrélations (ACP1 vs ACP2)")
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    circ = plt.Circle((0, 0), 1, color="gray", fill=False)
    ax2.add_artist(circ)
    ax2.axhline(0, ls="--", color="gray")
    ax2.axvline(0, ls="--", color="gray")
    for i, var in enumerate(X_cols):
        ax2.arrow(0, 0, load[i, 0], load[i, 1],
                  head_width=0.03, head_length=0.03, color="blue", alpha=0.7)
        ax2.text(load[i, 0]*1.1, load[i, 1]*1.1, var, fontsize=8)
    ax2.set_xlim(-1.1, 1.1)
    ax2.set_ylim(-1.1, 1.1)
    st.pyplot(fig2)

    # --- 10. Scatter des communes (individus)
    color_arg = "cluster" if use_cluster else ("DENS" if "DENS" in df.columns else None)
    title = f"Projection communes ({mode}) — ACP1 : {explained_var[0]:.1f}% ; ACP2 : {explained_var[1]:.1f}%"
    fig1 = px.scatter(
        df_ind, x="ACP1", y="ACP2",
        color=color_arg,
        color_continuous_scale=None if use_cluster else "Blues",
        hover_name="LIBGEO" if "LIBGEO" in df_ind.columns else None,
        title=title
    )
    st.plotly_chart(fig1, use_container_width=True)

    # --- 11. Dendrogramme CAH (optionnel)
    if show_cah:
        st.subheader("🌳 Dendrogramme CAH (Ward)")
        sample = df_ind.sample(n=min(len(df), 500), random_state=0)
        Z = linkage(sample[["ACP1", "ACP2"]], method="ward")
        fig_cah, ax = plt.subplots(figsize=(8, 4))
        dendrogram(Z, ax=ax, truncate_mode="level", p=5)
        ax.set_xlabel("Index de la commune")
        ax.set_ylabel("Distance")
        st.pyplot(fig_cah)

    # --- 12. Relation clusters ↔ densité
    if use_cluster and "DENS" in df_ind.columns:
        st.subheader("📦 Densité par cluster & test Kruskal–Wallis")
        fig_box, axb = plt.subplots(figsize=(6, 4))
        sns.boxplot(x="cluster", y="DENS", data=df_ind, ax=axb)
        st.pyplot(fig_box)
        groups = [grp["DENS"].astype(int).values for _, grp in df_ind.groupby("cluster")]
        H, p = kruskal(*groups)
        st.markdown(f"**H**={H:.1f}, **p**={p:.3g}")
        if p < 0.05:
            st.success("p < 0.05 → densité diffère significativement entre clusters")
        else:
            st.info("p ≥ 0.05 → pas de différence significative")
