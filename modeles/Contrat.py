"""
tp1/modeles/Contrat.py
──────────────────────
Accord final signé entre un acheteur et un fournisseur à l'issue
d'une négociation aboutie. Représente le résultat concret de l'interaction.
"""
import datetime
from dataclasses import dataclass


@dataclass
class Contrat:
    """
    Formalisation de l'accord conclu lors d'une négociation bilatérale.

    Attributs
    ---------
    id_service     : service faisant l'objet du contrat
    vendeur        : id de l'agent fournisseur
    acheteur       : id de l'agent acheteur (ou coalition)
    prix_final     : prix d'accord convenu
    date_signature : date à laquelle l'accord a été conclu
    tour_accord    : tour de négociation auquel l'accord a été atteint
    remise_pct     : pourcentage de remise obtenu par rapport au prix catalogue
    """
    id_service:     str
    vendeur:        str
    acheteur:       str
    prix_final:     float
    date_signature: datetime.date
    tour_accord:    int
    remise_pct:     float = 0.0

    def __repr__(self) -> str:
        return (f"Contrat[{self.id_service}] "
                f"{self.acheteur} ← {self.vendeur} "
                f"à {self.prix_final:.2f}€  "
                f"(remise {self.remise_pct:.1f}%  tour {self.tour_accord})")
