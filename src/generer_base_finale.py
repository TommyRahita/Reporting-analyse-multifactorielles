#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_base_finale.py

1. Parcourt tous les CSV du dossier `../data/Ensemble-com-2021_csv`
2. Construit les colonnes D1…D7 en sommant toutes les colonnes NB_D*
3. Fusionne ces agrégats avec la table des communes (`donnees_communes.csv`)
4. Duplique COM en CODGEO et récupère la variable DENS depuis `grille_densite_7_niveaux_2024.csv`
5. Calcule la colonne nb_equipements_total (somme de D1 à D7)
6. Renomme D1…D7 en D1_<libelle>… sans espaces ni caractères spéciaux
7. Sauvegarde le fichier final sous `../data/donnees.csv`
"""

import os
import pandas as pd

def main():
    # Définition des chemins
    src_dir     = os.path.dirname(__file__)
    data_dir    = os.path.abspath(os.path.join(src_dir, '..', 'data'))
    equip_dir   = os.path.join(data_dir, 'Ensemble-com-2021_csv')
    communes_f  = os.path.join(equip_dir, 'donnees_communes.csv')
    dens_file   = os.path.join(data_dir, 'grille_densite_7_niveaux_2024.csv')
    output_file = os.path.join(data_dir, 'donnees.csv')

    # Vérification des chemins
    for path in (equip_dir, communes_f, dens_file):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Introuvable : {path}")

    # 1. Lecture de la table des communes
    communes = pd.read_csv(communes_f, sep=';', dtype=str)

    # 2. Agrégation D1…D7
    agg = None
    for fname in sorted(os.listdir(equip_dir)):
        if not fname.lower().endswith('.csv'):
            continue
        if fname in ('donnees_communes.csv',) or fname.startswith('meta_'):
            continue

        df = pd.read_csv(os.path.join(equip_dir, fname), sep=';', dtype=str)
        nb_cols = [c for c in df.columns if c.upper().startswith('NB_D')]
        if not nb_cols:
            continue

        # Conversion en int
        df[nb_cols] = (
            df[nb_cols]
            .apply(pd.to_numeric, errors='coerce')
            .fillna(0)
            .astype(int)
        )

        # Détection de la clé de commune
        key = 'CODGEO' if 'CODGEO' in df.columns else 'COM'
        summary = pd.DataFrame({key: df[key]})

        # Initialisation des colonnes D1…D7
        for i in range(1, 8):
            summary[f'D{i}'] = 0

        # Remplissage par catégorie
        for col in nb_cols:
            cat = f'D{col[4]}'  # ex. 'NB_D201' → 'D2'
            summary[cat] += df[col]

        # Somme par commune
        summary = summary.groupby(key)[[f'D{i}' for i in range(1, 8)]].sum().reset_index()

        # Fusion itérative (addition évitant les suffixes _x/_y)
        if agg is None:
            agg = summary
        else:
            agg = agg.set_index(key).add(summary.set_index(key), fill_value=0).reset_index()

    # 3. Fusion avec la table des communes
    final = communes.merge(agg, left_on='COM', right_on=key, how='left').fillna(0)

    # 4. Import de DENS
    #   - Dupliquer COM en CODGEO pour la jointure
    final['CODGEO'] = final['COM']
    #   - Lecture du fichier de densité (séparateur virgule)
    dens = pd.read_csv(dens_file, sep=',', dtype=str, usecols=['CODGEO', 'DENS'])
    #   - Fusion stricte sur CODGEO
    final = final.merge(dens, on='CODGEO', how='left')
    #   - Remplir les manquants
    final['DENS'] = final['DENS'].fillna('0')

    # 5. Calcul du nombre total d’équipements
    d_cols = [f'D{i}' for i in range(1, 8)]
    final['nb_equipements_total'] = final[d_cols].sum(axis=1).astype(int)

    # 6. Renommage D1…D7 en D1_<libelle> (underscore only)
    labels = {
        'D1': 'Etablissements_de_sante_humaine',
        'D2': 'Equipements_medico_paramedicaux',
        'D3': 'Structures_de_sante_publique',
        'D4': 'Actions_sociales',
        'D5': 'Hebergements_sociaux',
        'D6': 'Equipements_educatifs_sportifs',
        'D7': 'Autres_equipements'
    }
    for d, lib in labels.items():
        if d in final.columns:
            final.rename(columns={d: f"{d}_{lib}"}, inplace=True)

    # 7. Sauvegarde finale
    final.to_csv(output_file, sep=';', index=False)
    print(f"✅ Base finale générée : {output_file}")

if __name__ == '__main__':
    main()

