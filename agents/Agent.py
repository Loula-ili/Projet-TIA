"""
tp1/agents/Agent.py
───────────────────
Classe abstraite de base commune à tous les agents du système.

Responsabilités :
  - maintenir une boîte aux lettres (offres reçues non traitées)
  - tenir un historique complet de tous les échanges
  - fournir les primitives send / receive
  - déclarer la méthode abstraite traiter_offres() que chaque agent
    doit implémenter selon son raisonnement individuel
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from modeles.Offre import Offre, TypeOffre


class Agent(ABC):
    """
    Classe mère abstraite de tous les agents (fournisseurs et acheteurs).

    Un agent est une entité autonome qui :
      - possède un identifiant unique
      - reçoit et envoie des Offres via une boîte aux lettres
      - décide seul de ses actions (raisonnement individuel)
    """

    def __init__(self, id_agent: str) -> None:
        self.id_agent     = id_agent
        self._boite:       list[Offre] = []   # offres reçues en attente
        self._historique:  list[Offre] = []   # journal complet

    # ── communication ─────────────────────────────────────────────────────────

    def recevoir(self, offre: Offre) -> None:
        """Dépose une offre entrante dans la boîte de l'agent."""
        self._boite.append(offre)
        self._historique.append(offre)

    def _envoyer(self, dest: "Agent", type_offre: TypeOffre,
                 id_service: str, montant: Optional[float], tour: int) -> Offre:
        """
        Construit une Offre, l'enregistre dans l'historique de l'émetteur
        et la dépose dans la boîte du destinataire.
        """
        o = Offre(
            expediteur=self.id_agent,
            destinataire=dest.id_agent,
            type_offre=type_offre,
            id_service=id_service,
            montant=montant,
            tour=tour,
        )
        self._historique.append(o)
        dest.recevoir(o)
        return o

    def lire_offres(self) -> list[Offre]:
        """Vide et retourne la boîte de réception."""
        offres, self._boite = self._boite, []
        return offres

    # ── raisonnement individuel (méthode à implémenter) ───────────────────────

    @abstractmethod
    def traiter_offres(self, *args, **kwargs) -> None:
        """
        Raisonnement individuel : lit les offres reçues et y répond.
        Chaque sous-classe implémente sa propre stratégie.
        """

    # ── utilitaires ───────────────────────────────────────────────────────────

    def afficher_historique(self) -> None:
        print(f"\n── Historique de {self.id_agent} ──")
        for o in self._historique:
            print(f"  {o}")

    def __repr__(self) -> str: 
        return f"Agent({self.id_agent})"
