"""
tp1/main.py
───────────
Point d'entrée de la simulation TP1 — Négociation multiagent pour voyage.

Lance dans l'ordre :
  1. Question 1  : négociation bilatérale (agent fournisseur ↔ agent acheteur)
  2. Question 2a : formation de coalitions par couplage (mode compétitif)
  3. Question 2b : formation de coalitions par IDP et IP (mode coopératif)
  4. Comparaison des trois algorithmes

Run : python main.py   (depuis le dossier tp1/)
"""

import datetime
import sys
import os

# Assure que l'importation fonctionne en lançant depuis tp1/
sys.path.insert(0, os.path.dirname(__file__))

# ── Imports ────────────────────────────────────────────────────────────────────
from modeles.Service      import Service, TypeService
from agents.AgentFournisseur import (AgentFournisseur, ContrainteFournisseur,
                                     PreferenceFournisseur)
from agents.AgentAcheteur    import (AgentAcheteur, PreferenceAcheteur,
                                     ContrainteAcheteur)
from negociation.StrategieNego import StrategieNego
from negociation.Protocole     import negocier
from coalitions.Coalition      import ProfilAcheteur, TypeService as TS
from coalitions.AlgoCouplage   import algorithme_couplage, afficher_resultats_couplage
from coalitions.AlgoIDP_IP     import IDP, IP, _precomputer_valeurs


# ══════════════════════════════════════════════════════════════════════════════
# ─── QUESTION 1 : Négociation bilatérale ─────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def demo_question1() -> None:
    titre = "QUESTION 1 — Négociation bilatérale"
    print(f"\n{'╔'+'═'*60+'╗'}")
    print(f"  {titre}")
    print(f"{'╚'+'═'*60+'╝'}")

    date_ref = datetime.date(2025, 6, 1)

    # ── Fournisseur F1 : Air France ────────────────────────────────────────────
    f1 = AgentFournisseur("F1-AirFrance")

    s001 = Service("S001", TypeService.AVION, "AirFrance",
                   "Paris", "Lyon", datetime.date(2025, 7, 10), 750.0)
    f1.ajouter_service(
        s001,
        ContrainteFournisseur(prix_minimal=500.0,
                              date_limite_vente=datetime.date(2025, 7, 5)),
        PreferenceFournisseur(date_vente_souhaitee=datetime.date(2025, 6, 15))
    )

    # ── Fournisseur F2 : EasyJet ──────────────────────────────────────────────
    f2 = AgentFournisseur("F2-EasyJet")

    s003 = Service("S003", TypeService.AVION, "EasyJet",
                   "Paris", "Lyon", datetime.date(2025, 7, 10), 300.0)
    f2.ajouter_service(
        s003,
        ContrainteFournisseur(prix_minimal=180.0,
                              date_limite_vente=datetime.date(2025, 7, 9)),
        PreferenceFournisseur()
    )

    # ── Fournisseur F3 : SNCF ─────────────────────────────────────────────────
    f3 = AgentFournisseur("F3-SNCF")

    s005 = Service("S005", TypeService.TRAIN, "SNCF",
                   "Paris", "Lyon", datetime.date(2025, 7, 10), 120.0)
    f3.ajouter_service(
        s005,
        ContrainteFournisseur(prix_minimal=70.0,
                              date_limite_vente=datetime.date(2025, 7, 8)),
        PreferenceFournisseur()
    )

    # ── Acheteur A1 : budget 600 € — veut un vol AirFrance ───────────────────
    a1 = AgentAcheteur(
        "A1",
        PreferenceAcheteur(compagnies_preferees=["AirFrance"]),
        ContrainteAcheteur(budget_max=600.0,
                           date_achat_limite=datetime.date(2025, 7, 1)),
        StrategieNego(offre_initiale=400.0, max_soumissions=6,
                      taux_augmentation_max=0.10)
    )

    # ── Acheteur A2 : budget 100 € — veut le train ────────────────────────────
    a2 = AgentAcheteur(
        "A2",
        PreferenceAcheteur(),
        ContrainteAcheteur(budget_max=100.0,
                           date_achat_limite=datetime.date(2025, 7, 1)),
        StrategieNego(offre_initiale=70.0, max_soumissions=6,
                      taux_augmentation_max=0.10)
    )

    # ── Acheteur A3 : budget 500 € — refuse EasyJet ──────────────────────────
    a3 = AgentAcheteur(
        "A3",
        PreferenceAcheteur(compagnies_refusees=["EasyJet"]),
        ContrainteAcheteur(budget_max=500.0,
                           date_achat_limite=datetime.date(2025, 7, 1)),
        StrategieNego(offre_initiale=350.0, max_soumissions=6,
                      taux_augmentation_max=0.10)
    )

    # ── Négociations ──────────────────────────────────────────────────────────
    print("\n[1] A1 négocie S001 (AirFrance 750€) avec F1")
    c1 = negocier(f1, a1, "S001", date_ref)

    print("\n[2] A2 négocie S005 (SNCF train 120€) avec F3")
    c2 = negocier(f3, a2, "S005", date_ref)

    print("\n[3] A3 négocie S003 (EasyJet — société refusée!) avec F2")
    c3 = negocier(f2, a3, "S003", date_ref)

    print("\n[4] A3 négocie S001 (AirFrance 750€, budget A3=500€) avec F1")
    c4 = negocier(f1, a3, "S001", date_ref)

    # ── Récapitulatif ─────────────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print("  Résumé des négociations Q1")
    print(f"{'─'*62}")
    for (lbl, c) in [("A1↔F1 (S001)", c1), ("A2↔F3 (S005)", c2),
                     ("A3↔F2 (S003)", c3), ("A3↔F1 (S001)", c4)]:
        if c:
            remise = c.remise_pct * 100
            print(f"  {lbl:<20}   {c.prix_final:.2f}€ "
                  f"(tour {c.tour_accord}, remise {remise:.1f}%)")
        else:
            print(f"  {lbl:<20}   Aucun accord")


# ══════════════════════════════════════════════════════════════════════════════
# ─── QUESTION 2 : Formation de coalitions ─────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def demo_question2() -> None:
    titre = "QUESTION 2 — Formation de coalitions"
    print(f"\n{'╔'+'═'*60+'╗'}")
    print(f"  {titre}")
    print(f"{'╚'+'═'*60+'╝'}")

    # ── Profils acheteurs ─────────────────────────────────────────────────────
    # Critère de regroupement : même destination + même type + même COMPAGNIE
    # prix_service  : prix catalogue du billet (PUBLIC, base du calcul de valeur)
    # budget_reel   : max que l'acheteur veut payer (PRIVÉ, Q2b uniquement)
    # ≠ budget_reel car 1€+499€=500€ mais 250€+250€=500€ :
    #   la distribution individuelle compte pour les économies de chaque membre.
    profils = [
        ProfilAcheteur("B1", "Rome",  TS.AVION, "AirFrance", prix_service=320, budget_reel=500),
        ProfilAcheteur("B2", "Rome",  TS.AVION, "AirFrance", prix_service=310, budget_reel=480),
        ProfilAcheteur("B3", "Rome",  TS.AVION, "AirFrance", prix_service=335, budget_reel=510),
        ProfilAcheteur("B4", "Paris", TS.AVION, "EasyJet",   prix_service=250, budget_reel=400),
        ProfilAcheteur("B5", "Paris", TS.AVION, "EasyJet",   prix_service=260, budget_reel=420),
        ProfilAcheteur("B6", "Paris", TS.AVION, "EasyJet",   prix_service=245, budget_reel=390),
    ]

    profils_dict = {p.id: p for p in profils}

    print("\n  Profils des acheteurs :")
    for p in profils:
        print(f"    {p.id} → {p.compagnie} / {p.destination} ({p.type_service.value})"
              f"  prix_service={p.prix_service}€  budget_reel={p.budget_reel}€")

    # ── Pré-calcul des valeurs (partagé entre Q2a, IDP et IP) ─────────────────
    valeurs = _precomputer_valeurs(profils)

    # ── 2a : Couplage (Ketchpel 94) ───────────────────────────────────────────
    print(f"\n{'─'*62}")
    print("  Q2a — Algorithme de couplage (mode COMPÉTITIF, Ketchpel 94)")
    print(f"{'─'*62}")
    coalitions_couplage = algorithme_couplage(profils, valeurs)
    afficher_resultats_couplage(coalitions_couplage, profils_dict)

    # ── 2b : IDP + IP ──────────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print("  Q2b — IDP et IP (mode COOPÉRATIF, information complète)")
    print(f"{'─'*62}")
    leader = max(profils, key=lambda p: p.prix_service)
    IDP(profils, valeurs=valeurs, leader=leader)
    IP(profils, valeurs=valeurs, leader=leader)

    # ── Comparaison détaillée des trois méthodes ──
    from coalitions.AlgoIDP_IP import comparer_couplage_idp_ip
    comparer_couplage_idp_ip(profils, valeurs, profils_dict)


# ══════════════════════════════════════════════════════════════════════════════
# ─── MAIN ──────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_question1()
    demo_question2()

    print(f"\n{'═'*62}")
    print("  Simulation terminée.")
    print(f"{'═'*62}\n")