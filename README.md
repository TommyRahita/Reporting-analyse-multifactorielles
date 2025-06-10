# Reporting Analyse Multifactorielles

## 📁 Structure du projet

```

Reporting-analyse-multifactorielles/
├── data/                         # Contient `donnees.csv` généré par `generer_base_finale.py`
│   ├── Ensemble-com-2021_csv/    # CSV sources INSEE
│   ├── grille_densite_7_niveaux_2024.csv
│   ├── donnees.csv               # Base de données finale
├── src/
│   ├── generer_base_finale.py    # Script de préparation et agrégation des données
│   └── index.py                  # Script Streamlit (ACP, clustering, CAH…)
├── requirements.txt              # Dépendances Python
├── .gitignore                    # Fichiers / dossiers ignorés par Git
└── README.md                     # Guide d’installation et d’utilisation

````

---

## 🔧 Prérequis

- Python 3.10 ou supérieur  
- `pip` ou `conda`  
- Connexion internet pour installer les bibliothèques

---

## ⚙️ Installation

```bash
git clone https://github.com/votre-utilisateur/Reporting-analyse-multifactorielles.git
cd Reporting-analyse-multifactorielles

# Créer un environnement virtuel
python -m venv .venv

# Activer le venv
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Mettre à jour pip et installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
````

---

## 🚀 Génération des données

Avant de lancer l’application, préparez la base finale :

```bash
# Depuis le dossier src/
cd src
python generer_base_finale.py
```

Cela va créer/mettre à jour `data/donnees.csv` avec :

1. Agrégation des colonnes NB\_D\* en D1…D7
2. Fusion avec la table des communes et DENS
3. Calcul des ratios par 1 000 hab.
4. Filtrage éventuel sur PMUN (10 000–20 000) si activé
5. Sauvegarde de la base propre

---

## ▶️ Lancer l’application Streamlit

```bash
streamlit run src/index.py
```

Ouvrez ensuite votre navigateur à l’adresse :

```
http://localhost:8501
```

---

## 📊 Fonctionnalités principales

* **ACP comparées** : brut vs. par 1 000 hab.
* **Scatter interactif** des communes (ACP1 vs ACP2), coloré par densité ou cluster
* **Clustering k-means** (k paramétrable) et **CAH** (dendrogramme)
* **Tableaux** : contributions, cos², valeurs propres
* **Statistiques descriptives** : total, ratios, distributions
* **Test Kruskal-Wallis** pour valider la relation clusters ↔ densité
* **Cercle de corrélations** dynamique
* *(Optionnel)* **Cartographie Folium** si `communes.geojson` est présent

---

## 📦 Dépendances (`requirements.txt`)

```
streamlit
pandas
numpy
matplotlib
scikit-learn
plotly>=5.18.0
kaleido>=0.2.1
seaborn
scipy
geopandas
shapely
folium
streamlit-folium
geopy
```

---

## ✅ Bonnes pratiques

* Ne pas versionner le dossier `.venv/` (inclus dans `.gitignore`)
* Placer toutes les données source dans `data/`
* Commiter & push avant redeploy sur Streamlit Cloud pour prendre en compte les changements
* Utiliser `@st.experimental_memo` pour mettre en cache les chargements lourds (ex. géométrie simplifiée)

---

*Dernière mise à jour : 10 juin 2025*
