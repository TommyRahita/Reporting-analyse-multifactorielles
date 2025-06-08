## 📁 Structure du projet

```

Reporting-analyse-multifactorielles/
├── data/                         # Contient BASE_FINAL.csv
├── src/                          # Contient le script principal index.py
├── requirements.txt              # Dépendances Python
├── .gitignore                    # Fichiers à ignorer dans Git
└── README.md                     # Ce fichier

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
python -m venv .venv
source .venv/bin/activate        # sous macOS/Linux
.venv\\Scripts\\activate         # sous Windows
pip install -r requirements.txt
````

---

## 🚀 Lancer l'application

```bash
streamlit run src/index.py
```

Puis ouvrir dans le navigateur à l’adresse :

```
http://localhost:8501
```

---

## 📊 Fonctionnalités principales

* **ACP sur les équipements de santé** (jusqu’à 5 axes)
* **Projection des communes** sur différents plans (choix de ACP1 à ACP5)
* **Cercle des corrélations** dynamique pour les variables
* **Filtrage interactif** des communes par niveau de densité
* **Export CSV** des variables factorisées
* **Tableaux de contributions, cos² et valeurs propres**
* Bloc d’**interprétation automatique des axes**

---

## 📦 Dépendances principales

* streamlit
* pandas
* numpy
* matplotlib
* scikit-learn
* plotly

---

## ✅ Bonnes pratiques

* Ne pas versionner `.venv/` → déjà exclu via `.gitignore`
* Les données sources doivent être placées dans `data/`
* Le script principal est `src/index.py`
