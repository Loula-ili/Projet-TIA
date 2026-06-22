"""
tp1/modeles/Service.py
─────────────────────
Représentation du bien échangé : un billet avion ou train.
Toutes les informations sont PUBLIQUES (visibles par tous les agents).
"""
import datetime
from dataclasses import dataclass
from enum import Enum


class TypeService(Enum):
    AVION = "avion"
    TRAIN = "train"


@dataclass
class Service:
    """
    Billet de voyage mis en vente par un agent fournisseur.

    Attributs publics
    -----------------
    id_service     : identifiant unique (ex. "S001")
    type_service   : AVION ou TRAIN
    compagnie      : nom de la compagnie (ex. "AirFrance")
    lieu_depart    : ville de départ
    lieu_arrivee   : ville d'arrivée
    date_depart    : date du voyage
    prix_catalogue : prix affiché (point de départ de la négociation)
    """
    id_service:     str
    type_service:   TypeService
    compagnie:      str
    lieu_depart:    str
    lieu_arrivee:   str
    date_depart:    datetime.date
    prix_catalogue: float

    def __repr__(self) -> str:
        # Appelé automatiquement par print(service) — affiche 
        #  ex : Service[S001] AirFrance Paris→Lyon le 2025-07-10  750.00€
        return (f"Service[{self.id_service}] {self.compagnie} "
                f"{self.lieu_depart}→{self.lieu_arrivee} "
                f"le {self.date_depart}  {self.prix_catalogue:.2f}€")
