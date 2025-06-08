import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Chargement des données
df = pd.read_csv("data/donnees.csv", sep=';')

# Préparation des variables quantitatives pour l’ACP
# On prend uniquement les colonnes D1_… D7_ (avec underscore) et on exclut nb_equipements_total
cols_pca = [col for col in df.columns 
            if col.startswith("D") and "_" in col]

# Matrice X pour l’ACP
X = df[cols_pca].fillna(0).astype(float)

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ACP
n_comp = min(10, X_scaled.shape[1])
pca = PCA(n_components=n_comp)
components = pca.fit_transform(X_scaled)
loadings = pca.components_.T
contrib = np.square(loadings) * 100
cos2 = contrib / np.sum(contrib, axis=1, keepdims=True) * 100
eigval = pca.explained_variance_
explained_var = pca.explained_variance_ratio_ * 100
cumulative_var = np.cumsum(explained_var)

# Résumé des variables
n_axes = min(5, n_comp)
df_vars = pd.DataFrame({
    "Variable": cols_pca,
    **{f"Coord{j+1}": loadings[:, j] for j in range(n_axes)},
    **{f"Contrib{j+1} (%)": contrib[:, j] for j in range(n_axes)},
    **{f"Cos2_{j+1} (%)": cos2[:, j] for j in range(n_axes)}
})

# Ajout des composantes principales au DataFrame
df_indiv = df.copy()
for j in range(n_axes):
    df_indiv[f"ACP{j+1}"] = components[:, j]

# Interface utilisateur
st.title("Maquette Reporting - Analyse des équipements de santé")

# Interprétation automatique
with st.expander("💡 Interprétation automatique des axes principaux"):
    st.markdown(f"""
    - **Axe 1 (ACP1)** : explique environ {explained_var[0]:.1f}% de la variance, principalement chargé par {', '.join(df_vars.sort_values(by="Contrib1 (%)", ascending=False)["Variable"].head(3).tolist())}.
    - **Axe 2 (ACP2)** : explique environ {explained_var[1]:.1f}%, chargé par {', '.join(df_vars.sort_values(by="Contrib2 (%)", ascending=False)["Variable"].head(3).tolist())}.
    - **Axe 3 (ACP3)** : explique environ {explained_var[2]:.1f}%.
    """)

# Menu de navigation
menu = st.sidebar.radio("Navigation", ["Statistiques descriptives", "ACP"])

if menu == "Statistiques descriptives":
    st.subheader("Statistiques descriptives des variables sélectionnées")
    # Inclure ici nb_equipements_total si besoin dans les stats
    cols_desc = cols_pca + ["nb_equipements_total"]
    desc = df[cols_desc].describe().transpose().round(2)
    st.dataframe(desc)

elif menu == "ACP":
    choix = st.radio("Vue ACP :", ["Communes (individus)", "Variables"])

    if choix == "Communes (individus)":
        axes = [f"ACP{i+1}" for i in range(n_axes)]
        axe_x = st.selectbox("Axe X", axes, index=0)
        axe_y = st.selectbox("Axe Y", axes, index=1)

        fig = px.scatter(
            df_indiv,
            x=axe_x,
            y=axe_y,
            hover_name="LIBGEO" if "LIBGEO" in df_indiv.columns else None,
            color="DENS" if "DENS" in df_indiv.columns else None,
            title=f"Projection des communes ({axe_x} vs {axe_y})"
        )
        st.plotly_chart(fig)
        cols_show = ["LIBGEO"] + axes if "LIBGEO" in df_indiv.columns else axes
        st.dataframe(df_indiv[cols_show])

    else:  # Variables
        axes = [f"ACP{i+1}" for i in range(n_axes)]
        axe_x = st.selectbox("Axe X", axes, index=0)
        axe_y = st.selectbox("Axe Y", axes, index=1)

        top_vars = df_vars.sort_values(by="Contrib1 (%)", ascending=False)["Variable"].head(5).tolist()
        selected_vars = st.multiselect("Variables à afficher", df_vars["Variable"].tolist(), default=top_vars)

        fig, ax = plt.subplots(figsize=(7, 7))
        ax.axhline(0, color='gray', linestyle='--')
        ax.axvline(0, color='gray', linestyle='--')
        circle = plt.Circle((0, 0), 1, color='lightgray', fill=False)
        ax.add_artist(circle)

        for _, row in df_vars.iterrows():
            var = row["Variable"]
            coord_x = row[f"Coord{axes.index(axe_x) + 1}"]
            coord_y = row[f"Coord{axes.index(axe_y) + 1}"]
            color = 'red' if var in selected_vars else 'gray'
            ax.arrow(0, 0, coord_x, coord_y,
                     head_width=0.03, head_length=0.03,
                     length_includes_head=True, color=color, alpha=0.7)
            ax.text(coord_x * 1.1, coord_y * 1.1, var,
                    fontsize=8, color=color)

        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_title(f"Cercle des corrélations ({axe_x} vs {axe_y})")
        st.pyplot(fig)

        st.subheader("Variances expliquées")
        df_eigen = pd.DataFrame({
            "Composante": [f"Comp {i+1}" for i in range(len(eigval))],
            "Valeur propre": eigval.round(4),
            "% variance": explained_var.round(2),
            "% cumulée": cumulative_var.round(2)
        })
        st.dataframe(df_eigen)

