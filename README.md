# TP TIA — Négociation multiagent pour la réservation de voyage

Simulation d'un système multiagent de négociation et de formation de coalitions dans le cadre d'une réservation de voyages (avion, train, hôtel). Réalisé en deux parties : négociation bilatérale puis formation de coalitions.

## Structure du projet

```
tp_tia/
├── main.py                      # Point d'entrée — lance les 3 questions
├── agents/
│   ├── Agent.py                 # Classe abstraite de base (boîte aux lettres, historique)
│   ├── AgentAcheteur.py         # Agent acheteur (stratégie, contraintes budget/date)
│   └── AgentFournisseur.py      # Agent fournisseur (catalogue, prix minimal, date limite)
├── modeles/
│   ├── Service.py               # Définition d'un service (avion, train, hôtel…)
│   ├── Offre.py                 # Offre échangée entre agents
│   └── Contrat.py               # Contrat signé à l'issue d'un accord
├── negociation/
│   ├── Protocole.py             # Protocole bilatéral tour par tour
│   └── StrategieNego.py         # Stratégies de négociation (concession, ancre…)
└── coalitions/
    ├── Coalition.py             # Modèle de coalition et profils acheteurs
    ├── AlgoCouplage.py          # Q2a — Couplage stable (mode compétitif)
    └── AlgoIDP_IP.py            # Q2b — IDP et IP (mode coopératif)
```

## Fonctionnalités

### Question 1 — Négociation bilatérale
Chaque agent acheteur négocie avec un ou plusieurs agents fournisseurs (Air France, EasyJet, SNCF…). Le protocole est unique pour tous les agents :
- l'acheteur soumet une offre initiale ;
- à chaque tour, le fournisseur accepte, contre-propose (concède 15 %/tour) ou refuse ;
- l'acheteur ajuste son offre (augmentation max 10 %/tour, 6 soumissions max) ;
- fin en cas d'accord, de refus ou d'épuisement des tours.

### Question 2a — Coalitions par couplage (mode compétitif)
Algorithme inspiré de Ketchpel (1994) : les agents forment des paires par stable matching sur les prix de référence publics, sans révéler leur information privée. Les paires fusionnent itérativement jusqu'à ce qu'aucune fusion bénéfique ne soit possible.

### Question 2b — Coalitions par IDP/IP (mode coopératif)
Deux algorithmes de programmation dynamique :
- **IDP** (Individual Dynamic Programming) : chaque agent optimise sa propre coalition localement.
- **IP** (Integer Programming) : partition optimale globale de l'ensemble des agents.

Les valeurs de toutes les coalitions possibles sont pré-calculées une seule fois puis partagées entre IDP et IP pour une comparaison équitable.

## Lancement

```bash
cd tp_tia
python main.py
```

La simulation affiche successivement les résultats des trois questions et une comparaison finale des algorithmes de coalition.

## Dépendances

Python 3.10+ — aucune dépendance externe.
