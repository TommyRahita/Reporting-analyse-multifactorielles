import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Chargement des données
df = pd.read_csv("data/BASE_FINAL.csv")

# Préparation des variables quantitatives
cols_quant = [col for col in df.columns if col.startswith("NB_") and not col.endswith("par_1000h") and not col.endswith("PAR_1000H") and col not in ["NB_EQUIP_SANTE_TOTAL", "NB_EQUIP_SANTE_PAR_1000H"]]
X = df[cols_quant].fillna(0)

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ACP
pca = PCA(n_components=10)
components = pca.fit_transform(X_scaled)
loadings = pca.components_.T
contrib = np.square(loadings) * 100
cos2 = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
eigval = pca.explained_variance_
explained_var = pca.explained_variance_ratio_ * 100
cumulative_var = np.cumsum(explained_var)

# Résumé des variables
df_vars = pd.DataFrame({
    "Variable": cols_quant,
    **{f"Coord{i+1}": loadings[:, i] for i in range(5)},
    **{f"Contrib{i+1} (%)": contrib[:, i] for i in range(5)},
    **{f"Cos2_{i+1} (%)": cos2[:, i] for i in range(5)}
})

# Ajout des composantes principales au DataFrame
df_indiv = df.copy()
for i in range(5):
    df_indiv[f"ACP{i+1}"] = components[:, i]

# Interface utilisateur
st.title("Maquette Reporting - Analyse des équipements de santé")

# Résumé automatique pour interprétation des axes
with st.expander("💡 Interprétation automatique des axes principaux"):
    st.markdown("""
    - **Axe 1 (ACP1)** : axe qui explique le plus de variance (≈40 %). Il est construit principalement par les variables les plus contributives comme les établissements de **soins courants**, **urgences**, ou **centres de santé**. Il peut représenter un **niveau général d'équipement médical intensif**.

    - **Axe 2 (ACP2)** : différencie les communes avec un accès à des **structures spécifiques** (par exemple, **maternité**, **dialyse**, **laboratoires**). Il peut refléter une **diversité de services spécialisés**.

    - **Axe 3 (ACP3)** : apporte une lecture complémentaire sur des équipements moins fréquents, comme la **psychiatrie ambulatoire** ou l’**hospitalisation à domicile**.

    👉 **Conclusion** : les trois premiers axes permettent une lecture claire des profils communaux : intensité des soins, diversité spécialisée, et dispositifs spécifiques.
    """)

# Recalculer X après filtre
X = df[cols_quant].fillna(0)

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ACP recalculée sur les données filtrées
pca = PCA(n_components=10)
components = pca.fit_transform(X_scaled)
loadings = pca.components_.T
contrib = np.square(loadings) * 100
cos2 = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
eigval = pca.explained_variance_
explained_var = pca.explained_variance_ratio_ * 100
cumulative_var = np.cumsum(explained_var)

menu = st.sidebar.radio("Navigation", ["Statistiques descriptives", "ACP"])

if menu == "Statistiques descriptives":
    st.subheader("Statistiques descriptives des variables sélectionnées")
    st.dataframe(df[cols_quant].describe().transpose().round(2))

elif menu == "ACP":
    choix = st.radio("Choisir la vue ACP :", ["Communes (individus)", "Variables"])

    if choix == "Communes (individus)":
        dens_choices = sorted(df_indiv["DENS"].dropna().unique())
        dens_selected = st.multiselect("Filtrer les communes par niveau de densité", dens_choices, default=dens_choices)
        df_indiv_filtered = df_indiv[df_indiv["DENS"].isin(dens_selected)]
        axes = [f"ACP{i+1}" for i in range(5)]
        axe_x = st.selectbox("Choisir l'axe X", axes, index=0)
        axe_y = st.selectbox("Choisir l'axe Y", axes, index=1)
        fig_ind = px.scatter(
            df_indiv_filtered,
            x=axe_x,
            y=axe_y,
            hover_name="LIBGEO",
            color=df_indiv_filtered["DENS"].astype(str),
            category_orders={"color": ["1", "2", "3", "4", "5", "6", "7"]},
            color_discrete_sequence=px.colors.qualitative.Set1,
            title=f"Projection des communes dans le plan {axe_x} x {axe_y}")
        st.plotly_chart(fig_ind)
        st.dataframe(df_indiv_filtered[["LIBGEO"] + axes])

    elif choix == "Variables":
        axes = [f"ACP{i+1}" for i in range(5)]
        axe_x = st.selectbox("Choisir l'axe X", axes, index=0)
        axe_y = st.selectbox("Choisir l'axe Y", axes, index=1)
        top_contrib_vars = df_vars.sort_values(by=["Contrib1 (%)", "Contrib2 (%)"], ascending=False)["Variable"].head(5).tolist()
        selected_vars = st.multiselect("Variables à afficher", df_vars["Variable"].tolist(), default=top_contrib_vars)

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axhline(0, color='gray', linestyle='--')
        ax.axvline(0, color='gray', linestyle='--')
        circle = plt.Circle((0, 0), 1, color='lightgray', fill=False)
        ax.add_artist(circle)

        for _, row in df_vars.iterrows():
            color = 'black' if row["Variable"] in selected_vars else 'lightgray'
            coord_x = row[f"Coord{axes.index(axe_x)+1}"]
            coord_y = row[f"Coord{axes.index(axe_y)+1}"]
            ax.arrow(0, 0, coord_x, coord_y, head_width=0.025, head_length=0.03, fc=color, ec=color, alpha=1 if color == 'black' else 0.3)
            ax.text(coord_x*1.1, coord_y*1.1, row["Variable"], fontsize=9, color=color, alpha=1 if color == 'black' else 0.3)

        ax.set_title(f"Cercle des corrélations - {axe_x} x {axe_y}")
        st.pyplot(fig)

        st.subheader("Tableau des valeurs propres et variance expliquée")
        df_eigen = pd.DataFrame({
            "Composante": [f"Comp {i+1}" for i in range(len(eigval))],
            "Valeur propre": eigval.round(4),
            "% variance": explained_var.round(2),
            "% cumulée": cumulative_var.round(2)
        })
        st.dataframe(df_eigen)

        st.subheader("Tableau des contributions et cos² (ACP1 à ACP5)")
        st.dataframe(df_vars.round(2))
