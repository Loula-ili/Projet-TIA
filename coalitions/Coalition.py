# Ce fichier définit la structure de base pour la formation de coalitions d'acheteurs.
# Il contient :
#   - ProfilAcheteur : la fiche descriptive d'un acheteur pour les algorithmes de groupe
#   - Coalition : la classe qui représente un groupe d'acheteurs, calcule sa valeur, son responsable, etc.
#   - Les fonctions utilitaires pour générer les taux de réduction et évaluer les gains de fusion
# Ce fichier sert de brique de base pour tous les algorithmes de coalition (Ketchpel, IDP, IP).

"""
tp1/coalitions/Coalition.py
────────────────────────────
Représentation d'un groupe d'agents (coalition) et calcul de sa valeur.

Règles du prof :
  • Critère de regroupement : même service (destination + type) ET même compagnie.
  • Le taux de réduction négocié est ALÉATOIRE (pas fixe) — il dépend de la
    négociation réelle avec le fournisseur.
  • La valeur = Σ prix_service_i × taux  (prix CATALOGUE du billet, pas le
    budget perso de l'acheteur : 1 + 499 ≠ 250 + 250 en termes de distribution).
  • Q2a (compétitif) : chaque agent connaît son prix_service (public) mais
    garde son budget_reel secret.
  • Q2b (coopératif) : les agents partagent aussi budget_reel avec le leader.

ProfilAcheteur :
  prix_service  — prix catalogue du billet souhaité (PUBLIC, base du calcul)
  budget_reel   — maximum que l'agent est prêt à payer (PRIVÉ, Q2b uniquement)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from modeles.Service import TypeService


# ══════════════════════════════════════════════════════════════════════════════
# Profil d'un acheteur pour la formation de coalition
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProfilAcheteur:
    """
    Représentation d'un acheteur pour les algorithmes de coalition.

    Attributs publics (observables par tous les agents)
    ----------------------------------------------------
    id            : identifiant
    destination   : ville d'arrivée souhaitée
    type_service  : AVION ou TRAIN
    compagnie     : transporteur souhaité (critère de compatibilité, cf. prof)
    prix_service  : prix catalogue du billet (base du calcul de valeur, ≠ budget)

    Attribut privé (partagé uniquement en mode coopératif Q2b)
    -----------------------------------------------------------
    budget_reel   : budget réel de l'acheteur
    """
    id:           str
    destination:  str
    type_service: TypeService
    compagnie:    str             # info publique — critère de regroupement
    prix_service: float           # prix catalogue du billet (info publique)
    budget_reel:  float           # budget max de l'acheteur (info privée)


# ══════════════════════════════════════════════════════════════════════════════
# Taux de réduction : aléatoire 
# ══════════════════════════════════════════════════════════════════════════════

def generer_taux(n: int) -> float:
    """
    Génère un taux de réduction aléatoire négocié selon la taille du groupe.

    Plus le groupe est grand, plus la plage de réduction est haute,
    mais le résultat reste non-déterministe (simulation de la négociation).
      |S| = 1 → uniform(1 %, 4 %)
      |S| = 2 → uniform(5 %, 12 %)
      |S| = 3 → uniform(11 %, 20 %)
      |S| ≥ 4 → uniform(18 %, 30 %)
    """
    if n == 1:
        return random.uniform(0.01, 0.04)
    elif n == 2:
        return random.uniform(0.05, 0.12)
    elif n == 3:
        return random.uniform(0.11, 0.20)
    else:
        return random.uniform(0.18, 0.30)


def _taux_moyen(n: int) -> float:
    """
    Taux déterministe (valeur attendue) utilisé uniquement pour ÉVALUER
    les fusions potentielles (gain_marginal) sans déclencher une nouvelle
    négociation aléatoire.
    """
    if n <= 1:
        return 0.0
    elif n == 2:
        return 0.085          # milieu de [0.05, 0.12]
    elif n == 3:
        return 0.155          # milieu de [0.11, 0.20]
    else:
        return 0.24           # milieu de [0.18, 0.30]


# ══════════════════════════════════════════════════════════════════════════════
# Coalition
# ══════════════════════════════════════════════════════════════════════════════

class Coalition:
    """
    Groupe d'acheteurs négociant ensemble pour obtenir une remise de groupe.

    La VALEUR d'une coalition est le montant total d'économies réalisées :
      valeur(S) = (Σ prix_service_i) × taux_négocié_aléatoire

    Le RESPONSABLE est l'agent qui représente la coalition lors des prochaines
    négociations (Ketchpel 94 : la paire désigne un agent responsable).
    """

    def __init__(self, membres: list[str],
                 prix_par_membre: dict[str, float],
                 taux_override: Optional[float] = None) -> None:
        self.membres:     frozenset[str]   = frozenset(membres)
        self._prix:       dict[str, float] = prix_par_membre
        self.responsable: Optional[str]    = membres[0] if membres else None # responsable par défaut : le premier membre de la liste (coalition d'un seul agent) , leader qui sert de point de contact pour les négociations avec le fournisseur
        # Taux de réduction négocié — aléatoire selon la taille du groupe, ou valeur imposée pour les évaluations internes (gain_marginal)
        # Taux aléatoire négocié — ou valeur imposée pour les évaluations internes
        self._taux: float = taux_override if taux_override is not None \
                            else generer_taux(len(membres))

    # ── valeur ────────────────────────────────────────────────────────────────

    def valeur(self) -> float:
        """
        Valeur totale (économies cumulées).
        Basée sur le prix CATALOGUE de chaque billet, pas sur les budgets.
        """
        total = sum(self._prix.get(m, 0.0) for m in self.membres)
        return total * self._taux

    def gain_marginal(self, autre: "Coalition") -> float:
        """
        Gain potentiel de fusionner this coalition avec 'autre'.
        Utilise un taux déterministe (valeur attendue) pour une évaluation stable.
        """
        fusionnee = self._fusion_temp(autre)
        return fusionnee.valeur() - self.valeur() - autre.valeur()

    def gain_par_membre(self) -> dict[str, float]:
        """
        Répartition des économies proportionnelle au prix_service de chaque membre.
        (250+250 ≠ 1+499 : la distribution individuelle compte.)
        """
        v = self.valeur()
        total_prix = sum(self._prix.get(m, 0.0) for m in self.membres)
        if total_prix == 0:
            return {m: 0.0 for m in self.membres}
        return {m: v * self._prix.get(m, 0.0) / total_prix for m in self.membres}

    # ── fusion ────────────────────────────────────────────────────────────────

    def _fusion_temp(self, autre: "Coalition") -> "Coalition":
        """
        Coalition temporaire pour évaluer la fusion.
        Utilise le taux moyen déterministe (pas de tirage aléatoire supplémentaire).
        """
        prix_fusion = {**self._prix, **autre._prix}
        n = len(self.membres | autre.membres)
        return Coalition(list(self.membres | autre.membres), prix_fusion,
                         taux_override=_taux_moyen(n))

    def fusionner(self, autre: "Coalition") -> "Coalition":
        """
        Fusionne this coalition avec 'autre' → nouvelle coalition avec taux aléatoire.
        Le responsable de la coalition d'origine conserve son rôle (Ketchpel 94).
        """
        prix_fusion = {**self._prix, **autre._prix}
        c = Coalition(list(self.membres | autre.membres), prix_fusion)
        c.responsable = self.responsable   # leader de la coalition absorbante
        return c

    # ── compatibilité ─────────────────────────────────────────────────────────

    def compatible_avec(self, autre: "Coalition",
                        profils: dict[str, ProfilAcheteur]) -> bool:
        """
        Deux coalitions sont compatibles si tous leurs membres partagent :
          • la même destination
          • le même type de service (AVION / TRAIN)
          • la même compagnie  ← critère ajouté (prof : « service ET compagnie »)

        On ne négocie un tarif de groupe qu'avec UN seul fournisseur.
        """
        tous = self.membres | autre.membres
        destinations  = {profils[m].destination   for m in tous}
        types_service = {profils[m].type_service   for m in tous}
        compagnies    = {profils[m].compagnie       for m in tous}
        return (len(destinations)  == 1 and
                len(types_service) == 1 and
                len(compagnies)    == 1)

    def __repr__(self) -> str:
        membres_str = ", ".join(sorted(self.membres))
        return (f"Coalition({{{membres_str}}} | "
                f"valeur={self.valeur():.2f}€ | "
                f"remise={self._taux*100:.1f}% | "
                f"responsable={self.responsable})")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Coalition) and self.membres == other.membres

    def __hash__(self) -> int:
        return hash(self.membres)
