import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy.stats import chi2_contingency

# --- Chargement des données
DATA_CSV = "data/donnees.csv"
df = pd.read_csv(DATA_CSV, sep=';')

# --- Sidebar : paramètres
st.sidebar.header("Paramètres généraux")
k = st.sidebar.slider("Nombre de clusters k-means", 2, 8, 3)
show_cluster = st.sidebar.checkbox("Afficher clustering", value=False)
show_cah     = st.sidebar.checkbox("Afficher dendrogramme CAH", value=False)

# --- Préparation ACP
labels = {
    'D1': 'Etablissements_de_sante_humaine',
    'D2': 'Equipements_medico_paramedicaux',
    'D3': 'Structures_de_sante_publique',
    'D4': 'Actions_sociales',
    'D5': 'Hebergements_sociaux',
    'D6': 'Equipements_educatifs_sportifs',
    'D7': 'Autres_equipements'
}
cols_brut  = [f"{d}_{lbl}" for d,lbl in labels.items()]
cols_1000  = [f"{d}_{lbl}_1000" for d,lbl in labels.items()]

# --- Menu
menu = st.sidebar.radio("Navigation", ["Statistiques descriptives", "ACP comparées"])

if menu == "Statistiques descriptives":
    st.title("Statistiques descriptives")
    # tableau descriptif
    desc = df[["nb_equipements_total"] + cols_brut + cols_1000].describe().T.round(2)
    st.dataframe(desc)

else:
    st.title("ACP comparées : brut vs. par 1 000 hab.")
    mode = st.radio("Mode ACP", ["Brut", "Par 1 000 hab."])
    X_cols = cols_brut if mode == "Brut" else cols_1000

    # --- Calcul ACP
    X = df[X_cols].fillna(0).astype(float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    pca = PCA(n_components=len(X_cols))
    comps = pca.fit_transform(Xs)
    load = pca.components_.T

    # Table variances
    eigval        = pca.explained_variance_.round(4)
    explained_var = (pca.explained_variance_ratio_ * 100).round(2)
    cumul_var     = np.cumsum(explained_var).round(2)
    df_var = pd.DataFrame({
        "Composante": [f"Comp {i+1}" for i in range(len(eigval))],
        "Valeur propre": eigval,
        "% variance": explained_var,
        "% cumulée": cumul_var
    })
    st.subheader("Variances expliquées par axe")
    st.dataframe(df_var)

    # Table contributions / cos2
    contrib = (load**2 * 100).round(2)
    cos2    = (contrib / contrib.sum(axis=1, keepdims=True)).round(2)
    df_contrib = pd.DataFrame({
        "Variable": X_cols,
        **{f"Contrib{i+1} (%)": contrib[:, i] for i in range(len(X_cols))},
        **{f"Cos2_{i+1} (%)":    cos2[:, i]    for i in range(len(X_cols))}
    })
    st.subheader("Contributions (%) et cos² pour chaque axe")
    st.dataframe(df_contrib)

    # Cercle des corrélations
    st.subheader(f"Cercle des corrélations ({mode})")
    fig_corr, ax = plt.subplots(figsize=(6,6))
    circle = plt.Circle((0,0),1, color='gray', fill=False)
    ax.add_artist(circle)
    ax.axhline(0, color='gray', linestyle='--')
    ax.axvline(0, color='gray', linestyle='--')
    for i, var in enumerate(X_cols):
        ax.arrow(0,0, load[i,0], load[i,1],
                 head_width=0.03, head_length=0.03, color="blue", alpha=0.7)
        ax.text(load[i,0]*1.1, load[i,1]*1.1, var, fontsize=8)
    ax.set_xlim(-1.1,1.1)
    ax.set_ylim(-1.1,1.1)
    st.pyplot(fig_corr)

    # Préparer DataFrame individus
    df_ind = df.copy()
    df_ind["ACP1"] = comps[:,0]
    df_ind["ACP2"] = comps[:,1]

    # k-means
    if show_cluster:
        km = KMeans(n_clusters=k, random_state=0)
        df_ind["cluster"] = km.fit_predict(df_ind[["ACP1","ACP2"]]).astype(str)

    # Scatter
    color_arg = "cluster" if show_cluster else "DENS"
    fig_scatter = px.scatter(
        df_ind, x="ACP1", y="ACP2",
        color=color_arg,
        color_discrete_sequence=px.colors.qualitative.Set1 if show_cluster else None,
        color_continuous_scale="Blues" if not show_cluster else None,
        hover_name="Commune",
        title=f"Projection des communes ({mode})"
    )
    st.subheader("Projection des communes (individus)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # CAH dendrogramme (échantillon)
    if show_cah:
        from scipy.cluster.hierarchy import linkage, dendrogram
        sample = df_ind.sample(500, random_state=0)
        Z = linkage(scaler.transform(sample[X_cols]), method='ward')
        fig_dend, axd = plt.subplots(figsize=(8,4))
        dendrogram(Z, ax=axd, no_labels=True, color_threshold=0.7*Z[-(k-1),2])
        axd.set_title("Dendrogramme CAH (Ward) sur ACP1 & ACP2")
        st.pyplot(fig_dend)

    # Khi-2 cluster ↔ densité
    if show_cluster:
        ct = pd.crosstab(df_ind["cluster"], df_ind["DENS"])
        chi2, p, dof, _ = chi2_contingency(ct)
        st.subheader("🔗 Lien cluster ↔ densité (Khi²)")
        st.write("Table de contingence :")
        st.dataframe(ct)
        st.write(f"Chi² = {chi2:.1f}, ddl = {dof}, p = {p:.2g}")
        if p < 0.05:
            st.success("p < 0.05 → association significative entre cluster et densité")
        else:
            st.info("p ≥ 0.05 → pas d'association significative")

