"""
tp1/modeles/Offre.py
────────────────────
Unité atomique de communication entre agents dans le protocole unique.
Une Offre contient le type d'acte, le service concerné et le montant proposé.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto


class TypeOffre(Enum):
    """
    Les quatre actes du protocole unique de négociation bilatérale.

    OFFRE        – acheteur → fournisseur  : "je propose X €"
    CONTRE_OFFRE – fournisseur → acheteur  : "je contre-propose Y €"
    ACCEPTATION  – l'une ou l'autre partie : accord sur le prix en cours
    REFUS        – l'une ou l'autre partie : fin de la négociation sans accord
    """
    OFFRE        = auto()
    CONTRE_OFFRE = auto()
    ACCEPTATION  = auto()
    REFUS        = auto()
# pour donner des valeurs explicites à chaque membre de l'énumération

@dataclass
class Offre:
    """
    Message échangé entre un agent fournisseur et un agent acheteur.

    Attributs
    ---------
    expediteur   : id de l'agent émetteur
    destinataire : id de l'agent récepteur
    type_offre   : acte du protocole (TypeOffre)
    id_service   : service concerné par cette offre
    montant      : prix proposé (None pour REFUS ou ACCEPTATION sans montant)
    tour         : numéro du tour de négociation
    """
    expediteur:   str
    destinataire: str
    type_offre:   TypeOffre
    id_service:   str
    montant:      Optional[float] = None # None pour REFUS ou ACCEPTATION sans montant  
    tour:         int = 0

    def __repr__(self) -> str:
        # Appelé par print(offre) — affiche ex : [Tour 03] A1   → F1   | OFFRE         | service=S001  montant=440.00€
        # m est vide si montant=None (cas REFUS), sinon affiche le montant formaté à 2 décimales
        # :02d = toujours 2 chiffres pour le tour 
        m = f"  montant={self.montant:.2f}€" if self.montant is not None else ""
        return (f"[Tour {self.tour:02d}] {self.expediteur:>4} → "
                f"{self.destinataire:<4} | {self.type_offre.name:<13} "
                f"| service={self.id_service}{m}")
