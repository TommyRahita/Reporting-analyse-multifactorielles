#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_base_finale.py

1. Parcourt les CSV du dossier `data/Ensemble-com-2021_csv`
2. Construit les colonnes D1…D7 en sommant NB_D*
3. Fusionne avec donnees_communes.csv (incluant PTOT, LIBGEO, etc.)
4. Récupère la densité (DENS)
5. Calcule nb_equipements_total
6. Renomme D1…D7 en D1_<libellé>
7. Crée les ratios D*_libellé_1000 par 1 000 habitants
8. Sauvegarde sous `data/donnees.csv`
"""
import os
import sys
import pandas as pd

def main():
    src_dir   = os.path.dirname(__file__)
    data_dir  = os.path.abspath(os.path.join(src_dir, '..', 'data'))
    equip_dir = os.path.join(data_dir, 'Ensemble-com-2021_csv')
    communes_f= os.path.join(equip_dir, 'donnees_communes.csv')
    dens_f    = os.path.join(data_dir, 'grille_densite_7_niveaux_2024.csv')
    out_f     = os.path.join(data_dir, 'donnees.csv')

    # 1. Lecture des communes
    comm = pd.read_csv(communes_f, sep=';', dtype=str)
    comm['PTOT'] = pd.to_numeric(comm['PTOT'], errors='coerce').fillna(0).astype(int)

    # 2. Agrégation D1…D7
    agg = None
    for fn in sorted(os.listdir(equip_dir)):
        if not fn.endswith('.csv') or fn in ('donnees_communes.csv',) or fn.startswith('meta_'):
            continue
        df = pd.read_csv(os.path.join(equip_dir, fn), sep=';', dtype=str)
        nb = [c for c in df.columns if c.upper().startswith('NB_D')]
        if not nb: 
            continue
        df[nb] = df[nb].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        key = 'CODGEO' if 'CODGEO' in df.columns else 'COM'
        tmp = pd.DataFrame({key: df[key]})
        for i in range(1, 8):
            tmp[f'D{i}'] = 0
        for c in nb:
            tmp[f'D{c[4]}'] += df[c]
        tmp = tmp.groupby(key)[[f'D{i}' for i in range(1, 8)]].sum().reset_index()
        agg = tmp if agg is None else agg.set_index(key).add(tmp.set_index(key), fill_value=0).reset_index()

    # 3. Fusion communes + agg
    final = comm.merge(agg, left_on='COM', right_on=key, how='left').fillna(0)

    # 4. Densité
    dens = pd.read_csv(dens_f, sep=',', dtype=str, usecols=['CODGEO', 'DENS'])
    final['CODGEO'] = final['COM']
    final = final.merge(dens, on='CODGEO', how='left')
    final['DENS'] = final['DENS'].fillna('0')

    # 5. Nombre total d’équipements
    d_cols = [f'D{i}' for i in range(1, 8)]
    final['nb_equipements_total'] = final[d_cols].sum(axis=1).astype(int)

    # 6. Renommage D1…D7 en D1_<libellé>
    labels = {
        'D1': 'Etablissements_de_sante_humaine',
        'D2': 'Equipements_medico_paramedicaux',
        'D3': 'Structures_de_sante_publique',
        'D4': 'Actions_sociales',
        'D5': 'Hebergements_sociaux',
        'D6': 'Equipements_educatifs_sportifs',
        'D7': 'Autres_equipements'
    }
    for d, lbl in labels.items():
        if d in final.columns:
            final.rename(columns={d: f"{d}_{lbl}"}, inplace=True)

    # 7. Création des ratios par 1000 hab.
    for d, lbl in labels.items():
        raw = f"{d}_{lbl}"
        ratio = f"{d}_{lbl}_1000"
        # division sécurisée et conversion numérique
        final[ratio] = pd.to_numeric(
            final[raw] / (final['PTOT'] / 1000),
            errors='coerce'
        ).fillna(0).round(2)

    # Nettoyage
    final.drop(columns=['CODGEO'], inplace=True)

    # 8. Sauvegarde
    try:
        if os.path.exists(out_f):
            os.remove(out_f)
        final.to_csv(out_f, sep=';', index=False)
        print(f"✅ Base générée : {out_f}")
    except Exception as e:
        print(f"❌ Échec de la sauvegarde : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()