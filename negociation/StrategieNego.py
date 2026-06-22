# Ce fichier définit la stratégie de négociation d'un agent acheteur :
# - Les paramètres (offre initiale, max de soumissions, taux d'augmentation, fréquence)
# - La fonction qui calcule la prochaine offre à faire selon ces règles
# Il permet de contrôler comment l'acheteur négocie (combien il commence, à quelle vitesse il monte, combien de fois il tente, etc.)

"""
tp1/negociation/StrategieNego.py
─────────────────────────────────
Paramètres stratégiques que l'utilisateur p_i fournit à son agent acheteur a_i
pour guider la négociation. (Section "paramètres de négociation" du sujet.)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategieNego:
    """
    Orientations stratégiques de négociation définies par p_i.

    Attributs
    ---------
    offre_initiale        : valeur de départ soumise au fournisseur
    max_soumissions       : nombre maximal d'offres sur un même service (≤ 6)
    taux_augmentation_max : une offre ne peut augmenter de plus de 10 % par tour
    frequence_soumission  : soumettre une offre tous les N tours (1 = chaque tour)
    """
    offre_initiale:        float # valeur de départ soumise au fournisseur
    max_soumissions:       int   = 6 # nombre maximal d'offres sur un même service (≤ 6)
    taux_augmentation_max: float = 0.10 # une offre ne peut augmenter de plus de 10 % par tour
    frequence_soumission:  int   = 1 # soumettre une offre tous les N tours (1 = chaque tour)


def prochaine_offre(strategie: StrategieNego,
                    derniere_offre: float,
                    nb_soumissions: int,
                    budget_max: float) -> Optional[float]:
    """
    Calcule la prochaine offre à soumettre selon la stratégie de p_i.

    Règles appliquées (du sujet) :
      1. Augmentation ≤ taux_augmentation_max par rapport à la dernière offre
      2. Plafonnée au budget_max de l'acheteur
      3. Si nb_soumissions ≥ max_soumissions → None (arrêt)
      4. Si aucune progression possible → None (arrêt)

    Retourne None si la négociation doit s'arrêter.
    """
    if nb_soumissions >= strategie.max_soumissions:
        return None

    nouvelle = derniere_offre * (1 + strategie.taux_augmentation_max)
    nouvelle = min(nouvelle, budget_max)

    if nouvelle <= derniere_offre:
        return None   # aucune progression possible
    return nouvelle
