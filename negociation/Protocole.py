# Ce fichier définit le protocole unique de négociation bilatérale entre un agent acheteur et un agent fournisseur.
# Il orchestre les échanges tour par tour :
#   - L'acheteur envoie son offre initiale
#   - À chaque tour, le fournisseur répond (accepte, contre-propose, refuse), puis l'acheteur répond
#   - La négociation s'arrête en cas d'accord, de refus, ou si le nombre maximal de tours est atteint
# Ce protocole est utilisé pour toutes les négociations du TP (un seul protocole pour tous les agents).

"""
tp1/negociation/Protocole.py
─────────────────────────────
Protocole unique de négociation bilatérale (note prof : « un seul protocole »).

La fonction negocier() orchestre les échanges tour par tour entre un
agent fournisseur et un agent acheteur sur un service donné.

Déroulement :
  Tour 0      : l'acheteur soumet son offre initiale.
  Tours 1..N  :
      1. Le fournisseur lit sa boîte et répond (accepte / contre-propose / refuse).
      2. L'acheteur lit sa boîte et répond (nouvelle offre / abandon).
  Fin         : accord, refus ou dépassement du nombre maximal de tours.
"""
from __future__ import annotations
import datetime
from typing import Optional

from modeles.Offre import TypeOffre
from modeles.Contrat import Contrat
from agents.AgentFournisseur import AgentFournisseur
from agents.AgentAcheteur import AgentAcheteur


def negocier(fournisseur:  AgentFournisseur,
             acheteur:     AgentAcheteur,
             id_service:   str,
             date_debut:   datetime.date,
             nb_tours_max: int = 20) -> Optional[Contrat]:
    """
    Lance et conduit la négociation bilatérale.

    Paramètres
    ----------
    fournisseur   : agent fournisseur détenteur du service
    acheteur      : agent acheteur demandeur
    id_service    : identifiant du service négocié
    date_debut    : date du jour à la reprise de la négociation
    nb_tours_max  : garde-fou contre les boucles infinies

    Retour
    ------
    Contrat signé si accord, None si échec.
    """
    sep = "═" * 62
    print(f"\n{sep}")
    print(f"  Négociation : {acheteur.id_agent} ↔ {fournisseur.id_agent}"
          f"  |  service {id_service}")
    print(sep)

    # ── Tour 0 : offre initiale ────────────────────────────────────────────────
    ok = acheteur.initier_negociation(fournisseur, id_service, tour=0)
    if not ok:
        print("  Impossible : service incompatible ou budget insuffisant.")
        return None

    # ── Tours 1..N ─────────────────────────────────────────────────────────────
    for tour in range(1, nb_tours_max + 1):
        date_courante = date_debut + datetime.timedelta(days=tour - 1)

        fournisseur.traiter_offres(acheteur, date_courante, tour)
        acheteur.traiter_offres(fournisseur, date_courante, tour)

        if acheteur.negociation_terminee(id_service):
            # Récupérer le contrat éventuellement signé
            etat = acheteur._negociations.get(id_service, {})
            return etat.get("contrat")   # None si refus

    print(f"  Tours max ({nb_tours_max}) atteints sans accord.")
    return None
