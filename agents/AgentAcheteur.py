"""
tp1/agents/AgentAcheteur.py
────────────────────────────
Agent acheteur : négocie l'achat d'un service pour le compte de l'utilisateur p_i.

Raisonnement individuel (contraintes + stratégie du sujet) :
  Préférences  : compagnies préférées / refusées
  Contraintes  : budget_max, date_achat_limite
  Stratégie    : offre_initiale, augmentation max 10 %/tour, max 6 soumissions
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from agents.Agent import Agent
from modeles.Service import Service
from modeles.Offre import TypeOffre
from modeles.Contrat import Contrat
from negociation.StrategieNego import StrategieNego, prochaine_offre

if TYPE_CHECKING:
    from agents.AgentFournisseur import AgentFournisseur


# ── Préférences et contraintes ─────────────────────────────────────────────────

@dataclass
class PreferenceAcheteur:
    """
    Préférences de l'utilisateur p_i transmises à son agent a_i.

    compagnies_preferees : compagnies souhaitées
    compagnies_refusees  : compagnies exclues catégoriquement
    """
    compagnies_preferees: list[str] = field(default_factory=list)
    compagnies_refusees:  list[str] = field(default_factory=list)


@dataclass
class ContrainteAcheteur:
    """
    Contraintes fermes de l'acheteur (non négociables).

    budget_max        : plafond budgétaire (ex. < 600 €)
    date_achat_limite : date au plus tard pour conclure l'achat
    """
    budget_max:        float
    date_achat_limite: datetime.date


# ── Agent ──────────────────────────────────────────────────────────────────────

class AgentAcheteur(Agent):
    """
    Agent acheteur : cherche le meilleur prix pour le service souhaité par p_i.

    État interne par négociation (id_service → dict) :
      nb_soumissions  : nombre d'offres déjà envoyées
      derniere_offre  : montant de la dernière offre émise
      termine         : True si la négociation est close (accord ou refus)
      contrat         : Contrat signé (None tant que pas d'accord)
    """
#   Attributs publics hérités de Agent :
#     id_agent     : identifiant unique de l'agent (ex. "A1")
#     preference    : instance de PreferenceAcheteur        
#     contrainte    : instance de ContrainteAcheteur
#     strategie     : instance de StrategieNego
#     negociations   : dict de l'état interne de chaque négociation en cours
#     contrats       : liste des Contrats signés
    def __init__(self, id_agent: str,
                 preference: PreferenceAcheteur,
                 contrainte: ContrainteAcheteur,
                 strategie:  StrategieNego) -> None:
        super().__init__(id_agent)
        self.preference = preference
        self.contrainte = contrainte
        self.strategie  = strategie
        self._negociations: dict[str, dict] = {}
        self.contrats:      list[Contrat]   = []

    # ── raisonnement individuel ───────────────────────────────────────────────

    def _service_compatible(self, service: Service) -> bool:
        """Filtre basé sur les préférences : rejette les compagnies refusées."""
        return service.compagnie not in self.preference.compagnies_refusees

    # ── initiation de la négociation ─────────────────────────────────────────

    def initier_negociation(self, fournisseur: "AgentFournisseur",
                            id_service: str, tour: int) -> bool:
        """
        Démarre une négociation sur le service indiqué.
        Retourne False si le service est incompatible ou si l'offre initiale
        dépasse déjà le budget maximal.
        """
        services_dispo = {s.id_service: s for s in fournisseur.services_disponibles()}
        if id_service in services_dispo:
            if not self._service_compatible(services_dispo[id_service]):
                print(f"  [A {self.id_agent}] {id_service} refusé "
                      f"(compagnie non acceptable).")
                return False

        offre_init = self.strategie.offre_initiale
        if offre_init > self.contrainte.budget_max:
            return False

        self._negociations[id_service] = {
            "nb_soumissions": 1,
            "derniere_offre": offre_init,
            "termine":        False,
            "contrat":        None,
        }
        print(f"  [A {self.id_agent}] Offre initiale {offre_init:.2f}€ "
              f"pour {id_service}")
        self._envoyer(fournisseur, TypeOffre.OFFRE, id_service, offre_init, tour)
        return True

    # ── traitement des offres (interaction) ───────────────────────────────────

    def traiter_offres(self, fournisseur: "AgentFournisseur",
                       date_courante: datetime.date, tour: int) -> None:
        """
        Lit les réponses du fournisseur et poursuit ou clôt la négociation
        selon la stratégie définie par p_i.
        """
        # ---
        # Cette méthode est le "cerveau" de l'acheteur pendant la négociation.
        # Elle lit toutes les offres reçues du fournisseur (ACCEPTATION, CONTRE_OFFRE, REFUS)
        # et décide quoi faire selon la stratégie de l'utilisateur.
        #
        # Pour chaque offre reçue :
        #   - Si c'est une ACCEPTATION :
        #       → Crée un Contrat (accord trouvé), l'ajoute à la liste des contrats signés,
        #         affiche un message d'accord, et marque la négociation comme terminée.
        #   - Si c'est une CONTRE_OFFRE :
        #       → Calcule la prochaine offre possible selon la stratégie (max +10% par tour, max 6 tours, budget max).
        #         Si on ne peut plus faire d'offre (budget dépassé, date limite dépassée, ou max de soumissions atteint),
        #         alors abandonne la négociation (envoie un REFUS au fournisseur, marque comme terminée).
        #         Sinon, met à jour l'état (nouvelle offre, incrémente le nombre de soumissions),
        #         affiche la nouvelle offre, et l'envoie au fournisseur.
        #   - Si c'est un REFUS :
        #       → Affiche un message d'échec et marque la négociation comme terminée.
        #
        # L'état de chaque négociation (par service) est stocké dans self._negociations.
        # Cela permet de gérer plusieurs négociations en parallèle si besoin.
        # ---
        for offre in self.lire_offres():
            id_s = offre.id_service
            etat = self._negociations.setdefault(id_s, {
                "nb_soumissions": 0,
                "derniere_offre": self.strategie.offre_initiale,
                "termine":        False,
                "contrat":        None,
            })

            if offre.type_offre == TypeOffre.ACCEPTATION:
                # Créer le contrat final
                services = {s.id_service: s for s in fournisseur.services_disponibles()}
                prix_cat  = services[id_s].prix_catalogue if id_s in services else offre.montant
                remise    = (1 - offre.montant / prix_cat) * 100 if prix_cat else 0
                c = Contrat(id_service=id_s, vendeur=fournisseur.id_agent,
                            acheteur=self.id_agent, prix_final=offre.montant,
                            date_signature=date_courante, tour_accord=tour,
                            remise_pct=remise)
                etat["contrat"] = c
                self.contrats.append(c)
                print(f"   Accordd : {self.id_agent} achète {id_s} "
                      f"à {offre.montant:.2f}€  (tour {tour})")
                etat["termine"] = True

            elif offre.type_offre == TypeOffre.CONTRE_OFFRE:
                nouvelle    = prochaine_offre(self.strategie,
                                              etat["derniere_offre"],
                                              etat["nb_soumissions"],
                                              self.contrainte.budget_max)
                hors_delai  = date_courante > self.contrainte.date_achat_limite
                max_att     = etat["nb_soumissions"] >= self.strategie.max_soumissions

                if nouvelle is None or hors_delai or max_att:
                    raison = ("budget"     if nouvelle is None
                              else "délai" if hors_delai
                              else "max soumissions")
                    print(f"   {self.id_agent} abandonne {id_s} ({raison})")
                    self._envoyer(fournisseur, TypeOffre.REFUS, id_s, None, tour)
                    etat["termine"] = True
                else:
                    etat["derniere_offre"]  = nouvelle
                    etat["nb_soumissions"] += 1
                    nb = etat["nb_soumissions"]
                    print(f"  [A {self.id_agent}] Offre {nouvelle:.2f}€ "
                          f"(soumission {nb}/{self.strategie.max_soumissions})")
                    self._envoyer(fournisseur, TypeOffre.OFFRE, id_s, nouvelle, tour)

            elif offre.type_offre == TypeOffre.REFUS:
                print(f"   Refus définitive du fournisseur sur {id_s}")
                etat["termine"] = True

    def negociation_terminee(self, id_service: str) -> bool:
        etat = self._negociations.get(id_service)
        return etat is not None and etat["termine"]

    def __repr__(self) -> str:
        return (f"AgentAcheteur({self.id_agent} | "
                f"budget={self.contrainte.budget_max:.0f}€ | "
                f"offre_init={self.strategie.offre_initiale:.0f}€)")
