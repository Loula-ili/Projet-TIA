"""
tp1/agents/AgentFournisseur.py
──────────────────────────────
Agent fournisseur : gère un catalogue de services à vendre et négocie
leur prix avec les agents acheteurs.

Raisonnement individuel (contraintes + préférences du sujet) :
  Contraintes : prix_minimal, date_limite_vente
  Préférences : date_vente_souhaitee
  Stratégie   : accepte si prix ≥ min ET date ≤ limite ; sinon contre-propose
                en cédant 15 % de l'écart (catalogue − minimum) par tour.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from agents.Agent import Agent
from modeles.Service import Service
from modeles.Offre import TypeOffre

if TYPE_CHECKING:
    from agents.AgentAcheteur import AgentAcheteur


# ── Contraintes et préférences ─────────────────────────────────────────────────

@dataclass
class ContrainteFournisseur:
    """
    Limites fermes imposées par le fournisseur pour un service donné.

    prix_minimal      : tarif en dessous duquel la vente est refusée
    date_limite_vente : le service ne peut plus être vendu après cette date
    """
    prix_minimal:      float
    date_limite_vente: datetime.date


@dataclass
class PreferenceFournisseur:
    """
    Orientations souhaitées (non contraignantes) du fournisseur.

    date_vente_souhaitee : date préférée pour conclure la vente
                           (ex. avant le 1er décembre)
    """
    date_vente_souhaitee: Optional[datetime.date] = None


# ── Agent ──────────────────────────────────────────────────────────────────────

class AgentFournisseur(Agent):
    """
    Agent fournisseur : met des services en vente et négocie leur prix.

    Le catalogue associe chaque id_service à :
      (Service, ContrainteFournisseur, PreferenceFournisseur)
    """

    def __init__(self, id_agent: str) -> None:
        super().__init__(id_agent)
        self._catalogue: dict[str, tuple[Service,
                                          ContrainteFournisseur,
                                          PreferenceFournisseur]] = {}

    # ── gestion du catalogue ──────────────────────────────────────────────────

    def ajouter_service(self, service: Service,
                        contrainte: ContrainteFournisseur,
                        preference: PreferenceFournisseur) -> None:
        """Enregistre un service disponible à la vente avec ses règles."""
        self._catalogue[service.id_service] = (service, contrainte, preference)
        print(f"  [F {self.id_agent}] Service ajouté : {service}")

    def retirer_service(self, id_service: str) -> None:
        """Retire un service vendu ou expiré."""
        self._catalogue.pop(id_service, None)

    def services_disponibles(self) -> list[Service]:
        return [s for s, _, _ in self._catalogue.values()]

    # ── raisonnement individuel ───────────────────────────────────────────────

    def _acceptable(self, id_s: str, prix: float, date: datetime.date) -> bool:
        """
        Vérifie les deux contraintes fermes :
          prix proposé ≥ prix_minimal  ET  date courante ≤ date_limite_vente
        """
        # ---
        # Cette méthode vérifie si une offre reçue respecte les contraintes "dures" du fournisseur :
        #   - Le prix proposé doit être supérieur ou égal au prix minimal fixé pour ce service
        #   - La date courante doit être avant ou égale à la date limite de vente
        # Si l'une des deux conditions n'est pas respectée, la vente est impossible (refus ou contre-offre).
        # Si le service n'existe plus dans le catalogue (déjà vendu ou retiré), on refuse aussi.
        # ---
        if id_s not in self._catalogue:
            return False
        _, c, _ = self._catalogue[id_s]
        return prix >= c.prix_minimal and date <= c.date_limite_vente

    def _contre_proposition(self, id_s: str, offre: float) -> float:
        """
        Stratégie de concession progressive :
          le fournisseur cède 15 % de l'écart (catalogue − minimum) par tour.
          La contre-offre ne descend jamais sous le prix_minimal.
        """
        # ---
        # Cette méthode calcule la contre-offre du fournisseur quand il refuse l'offre de l'acheteur.
        # Idée : le fournisseur ne baisse pas d'un coup, il cède 15% de l'écart entre le prix catalogue et son prix minimal à chaque tour.
        #
        # Exemple :
        #   - prix catalogue = 750€, prix_minimal = 500€, offre reçue = 400€
        #   - écart = 750 - 500 = 250
        #   - concession = 250 * 0.15 = 37.5
        #   - contre-offre = 400 + 37.5 = 437.5
        #   - MAIS comme c'est en dessous du prix minimal, on retourne max(500, 437.5) = 500
        # Donc la contre-offre ne descend jamais sous le prix minimal.
        # ---
        service, contrainte, _ = self._catalogue[id_s]
        ecart  = service.prix_catalogue - contrainte.prix_minimal
        retour = offre + ecart * 0.15
        return max(contrainte.prix_minimal, retour)

    # ── traitement des offres (interaction) ───────────────────────────────────

    def traiter_offres(self, acheteur: "AgentAcheteur",
                       date_courante: datetime.date, tour: int) -> None:
        """
        Lit la boîte de réception et répond à chaque offre reçue :
          - ACCEPTATION si l'offre respecte les contraintes
          - CONTRE_OFFRE avec une proposition plus haute
          - REFUS si le service n'est plus disponible
        """
        for offre in self.lire_offres():
            id_s = offre.id_service

            if offre.type_offre in (TypeOffre.OFFRE, TypeOffre.CONTRE_OFFRE):
                if self._acceptable(id_s, offre.montant, date_courante):
                    print(f"  [F {self.id_agent}] Accepte {offre.montant:.2f}€ "
                          f"pour {id_s}")
                    self._envoyer(acheteur, TypeOffre.ACCEPTATION,
                                  id_s, offre.montant, tour)
                    self.retirer_service(id_s)

                elif id_s in self._catalogue:
                    contre = self._contre_proposition(id_s, offre.montant)
                    print(f"  [F {self.id_agent}] Contre-offre {contre:.2f}€ "
                          f"pour {id_s}")
                    self._envoyer(acheteur, TypeOffre.CONTRE_OFFRE,
                                  id_s, contre, tour)
                else:
                    self._envoyer(acheteur, TypeOffre.REFUS, id_s, None, tour)

    def __repr__(self) -> str:
        return (f"AgentFournisseur({self.id_agent} | "
                f"{len(self._catalogue)} service(s))")
