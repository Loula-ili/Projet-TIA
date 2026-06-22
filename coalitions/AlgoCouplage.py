"""
tp1/coalitions/AlgoCouplage.py
───────────────────────────────
Question 2(a) — Algorithme de type couplage (Ketchpel, 1994)
Formation de coalitions en mode COMPÉTITIF (sans partage d'information privée).

Principe (cours pages 176-180) :
  1. Les agents transmettent leurs offres initiales (prix_reference public).
  2. Chaque agent évalue les offres reçues et les trie par profit décroissant.
  3. Les agents tentent de former des paires avec leur meilleur partenaire
     compatible (stable matching).
  4. Chaque paire désigne un RESPONSABLE qui représentera le groupe.
  5. Le processus se répète : les paires jouent le rôle d'un agent individuel.
  6. Terminaison quand aucune fusion bénéfique n'est plus possible.

Mode compétitif : les valeurs sont calculées sur les PRIX DE RÉFÉRENCE PUBLICS,
pas sur les budgets réels → les agents ne révèlent pas leur information privée.
"""
from __future__ import annotations
from typing import Optional

from coalitions.Coalition import Coalition, ProfilAcheteur


# ══════════════════════════════════════════════════════════════════════════════
# Utilitaires internes
# ══════════════════════════════════════════════════════════════════════════════
# fonction qui classe les autres coalitions compatibles par gain marginal décroissant
#  pour la coalition c, en utilisant les valeurs pré-calculées passées en paramètre
#C la coalition qui cherche a se coupler, autres les coalitions candidates,
#  profils pour vérifier compatibilité et calcul gain marginal , 
# valeurs pour calcul gain marginal a partir des valeurs pré-calculées
def _classement(c: Coalition,
                autres: list[Coalition],
                profils: dict[str, ProfilAcheteur],
                valeurs: dict) -> list[int]:
    """
    Retourne les indices des coalitions 'autres' triés par gain marginal
    décroissant depuis le point de vue de c, en ne gardant que les
    compatibles avec un gain > 0.
    Gain calculé à partir du dict valeurs pré-calculé (passé en entrée).
    """
    #liste des gains potentiels de fusion avec les autres coalitions compatibles, triés par ordre décroissant
    gains = []
    for i, autre in enumerate(autres):
        # Vérifie que ce n'est pas la même coalition et qu'elles sont compatibles
        if autre is not c and c.compatible_avec(autre, profils):
            #on fait l'union des membres de c et autre pour calculer la valeur de la coalition fusionnée
            union = c.membres | autre.membres
            #formule de calcul du gain de fusion : valeur de la coalition fusionnée - valeur de c - valeur d'autre
            g = (valeurs.get(union, 0.0)
                 - valeurs.get(c.membres, 0.0)
                 - valeurs.get(autre.membres, 0.0))
            #si le gain est positif alors la coalition de c avec autre est intéressante et on l'ajoute à la liste des gains potentiels
            if g > 0:
                gains.append((g, i))
    #tri des gains par ordre décroissant          
    gains.sort(reverse=True)
    #on retourne la liste des indices des autres interessants pour c, triés par gain décroissant sans les gains eux-mêmes
    return [i for _, i in gains]

# retourne les coalition stables mutuelles ( dictionnaire)(paires de coalitions qui se préfèrent mutuellement) à partir d'une liste de coalitions et de leurs classements respectifs
def _stable_matching(coalitions: list[Coalition],
                     profils: dict[str, ProfilAcheteur],
                     valeurs: dict) -> dict[int, Optional[int]]:
    """
    Algorithme de couplage stable (type Gale-Shapley adapté aux coalitions).

    Chaque coalition propose à son partenaire préféré disponible.
    Une coalition accepte si le proposant est meilleur que son partenaire actuel.
    Retourne un dictionnaire partenaire[i] = j ou None.
    """
    # nombre total des coalitions
    n = len(coalitions)
    # classements[i] : indices des coalitions autres triés par gain marginal décroissant depuis le point de vue de coalitions[i]
    #Pour chaque coalition i, on calcule sa liste de candidats préférés.Ex. classements[0] = [2, 1] → la coalition 0 préfère la 2, puis la 1
    classements  = {i: _classement(coalitions[i], coalitions, profils, valeurs)
                    for i in range(n)}
    suivant      = {i: 0 for i in range(n)}
    partenaire   = {i: None for i in range(n)}
    offre_active = {i: False for i in range(n)}

    print("\nDÉTAILS DU COUPLAGE (itération stable matching) :")
    for i in range(n):
        print(f"  Agent {i} ({sorted(coalitions[i].membres)}) : candidats compatibles par gain décroissant : {[sorted(coalitions[j].membres) for j in classements[i]]}")

    libres = [i for i in range(n) if classements[i]]
    etape = 1
    while libres:
        proposant = libres.pop(0)
        print(f"\n[Étape {etape}] Agent {proposant} ({sorted(coalitions[proposant].membres)}) propose à : ", end='')
        if suivant[proposant] >= len(classements[proposant]):
            print("(plus de candidats)")
            etape += 1
            continue
        cible = classements[proposant][suivant[proposant]]
        print(f"Agent {cible} ({sorted(coalitions[cible].membres)})")
        offre_active[proposant] = True

        if partenaire[proposant] is not None and classements[proposant] and classements[proposant][0] == partenaire[proposant]:
            print("    Déjà en couple avec son meilleur choix.")
            etape += 1
            continue

        if partenaire[cible] is None:
            print(f"    Cible libre : appariement provisoire entre {proposant} et {cible}.")
            partenaire[cible]     = proposant
            partenaire[proposant] = cible
        else:
            actuel = partenaire[cible]
            union_prop  = coalitions[cible].membres | coalitions[proposant].membres
            union_act   = coalitions[cible].membres | coalitions[actuel].membres
            g_proposant = (valeurs.get(union_prop, 0.0)
                           - valeurs.get(coalitions[cible].membres,    0.0)
                           - valeurs.get(coalitions[proposant].membres, 0.0))
            g_actuel    = (valeurs.get(union_act,  0.0)
                           - valeurs.get(coalitions[cible].membres,   0.0)
                           - valeurs.get(coalitions[actuel].membres,  0.0))
            print(f"    Cible déjà en couple avec {actuel} ({sorted(coalitions[actuel].membres)})")
            print(f"    Gain si accepte proposant : {g_proposant:.2f} | Gain si garde actuel : {g_actuel:.2f}")
            if g_proposant > g_actuel:
                print(f"    Cible préfère le proposant. {actuel} redevient libre.")
                partenaire[actuel]    = None
                offre_active[actuel]  = False
                suivant[actuel]      += 1
                partenaire[cible]     = proposant
                partenaire[proposant] = cible
                if suivant[actuel] < len(classements[actuel]):
                    libres.append(actuel)
            else:
                print(f"    Cible préfère son partenaire actuel. Proposant passe au suivant.")
                offre_active[proposant] = False
                suivant[proposant]     += 1
                if suivant[proposant] < len(classements[proposant]):
                    libres.append(proposant)
        # Affichage de l'état courant des appariements
        print("    Appariements actuels :", {k: v for k, v in partenaire.items() if v is not None})
        etape += 1

    return partenaire


# ══════════════════════════════════════════════════════════════════════════════
# Algorithme principal
# ══════════════════════════════════════════════════════════════════════════════
# L'algorithme de couplage stable (Ketchpel 94) — mode compétitif.
#profils: liste des 6 acheteurs avec leurs infos publiques (destination, compagnie, type_service, prix_service) et leurs infos privées (budget_max)
#valeurs: dict qui associe à chaque coalition (ensemble de membres) sa valeur precalculé dans le main partagé avec idp et ip pour que les 3 algos comparent sur la même base
def algorithme_couplage(profils: list[ProfilAcheteur],
                        valeurs: dict) -> list[Coalition]:
    """
    Algorithme de type couplage (Ketchpel 94) — mode compétitif.

    Paramètre
    ---------
    profils : liste des ProfilAcheteur (seul prix_reference est utilisé)

    Retour
    ------
    Structure de coalitions stable (liste de Coalition).
    """
    # Prix catalogue du service (PUBLIC : affiché sur le site du transporteur)
    # ≠ budget_reel (privé) — la valeur de coalition se base sur le PRIX DU BILLET
    prix_svc = {p.id: p.prix_service for p in profils} #creer dictionnaire a partir de profils qui stock le prix du billet
    profils_dict = {p.id: p for p in profils} #creer dictionnaire a partir de profil qui stock l'objet profil complet utilsé dans stable matching pour verifier la comptabilité

    # Coalitions initiales : chaque agent calcule pour lui-même (singleton)
    # cree 6 singletons sous forme coalition le mebmre c'est lid de lacheteur et sa valeur c le prix du billet 
    # → chacun diffuse son offre : (destination, compagnie, type, prix_service)
    coalitions: list[Coalition] = [
        Coalition([p.id], prix_svc) for p in profils
    ]

    print("\n── Algorithme de couplage Ketchpel 94 (mode compétitif) ──")
    print(f"  {len(coalitions)} agents — phase 1 : chacun calcule pour soi")
    for p in profils:
        print(f"    {p.id} : {p.compagnie} / {p.destination} / "
              f"{p.type_service.value} / prix_service={p.prix_service:.0f}€")
    #boucle principale de l'algorithme de couplage : tant qu'il existe des paires stables mutuelles, on les fusionne et on recommence
    iteration = 0 #comptre du nombre d'itérations de fusion de coalitions
    while True:
        iteration += 1
        partenaire = _stable_matching(coalitions, profils_dict, valeurs) #appel gale-shapley sur letat actuel des coalitions et retourne un nouvel etat de couplage (partenaire[i] = j ou None) qui indique les paires stables mutuelles à fusionner

        # Identifier les paires stables mutuelles
        #
        paires = set() 
        #pour chaque coalition i
        for i in range(len(coalitions)):
            j = partenaire[i] #on regarde son partenaire j
            if j is not None and partenaire[j] == i and i < j: #si j est un partenaire mutuel de i (partenaire[j] == i) et pour éviter les doublons on prend que les paires (i, j) avec i < j
                paires.add((i, j)) #on ajoute la paire (i, j) à la liste des paires stables mutuelles à fusionner
        #condition d'arret
        if not paires: #personne veut fusionner
            print(f"  Stabilité atteinte après {iteration - 1} itération(s).")
            break #on sort de la boucle while

        # Fusionner les paires et conserver les coalitions non fusionnées
        fusionnes = {idx for paire in paires for idx in paire} #ensemble des indices des coalitions qui vont être fusionnées  ex  {(1, 2), (4, 5)} → indices des coalitions qui forment des paires Résultat : fusionnes = {1, 2, 4, 5}
        nouvelles: list[Coalition] = [
            c for k, c in enumerate(coalitions) if k not in fusionnes
        ] #liste des coalitions qui ne sont pas fusionnées (celles dont les indices ne sont pas dans fusionnes)
        for i, j in paires:
            c_i = coalitions[i]
            c_j = coalitions[j]
            nouvelle = c_i.fusionner(c_j)
            nouvelles.append(nouvelle)
            print("\n  ─────────────────────────────────────────────────────────────")
            print(f"  [itération {iteration}] Nouvelle paire formée :")
            print(f"    - Groupe 1 : {sorted(c_i.membres)} (leader : {c_i.responsable})")
            print(f"    - Groupe 2 : {sorted(c_j.membres)} (leader : {c_j.responsable})")
            print(f"    → Fusion : {sorted(nouvelle.membres)}")
            print(f"      - Nouveau leader : {nouvelle.responsable}")
            print(f"      - Taux de remise : {nouvelle._taux*100:.1f}%")
            print(f"      - Valeur de la coalition : {nouvelle.valeur():.2f}€")
            print("  ─────────────────────────────────────────────────────────────")

        coalitions = nouvelles #L'ancienne liste (6 singletons) est remplacée par la nouvelle liste.Au prochain tour de while True, Gale-Shapley travaillera sur ces nouveaux groupes.

    return coalitions


# ══════════════════════════════════════════════════════════════════════════════
# Affichage des résultats
# ══════════════════════════════════════════════════════════════════════════════

def afficher_resultats_couplage(coalitions: list[Coalition],
                                 profils: dict[str, ProfilAcheteur]) -> None:
    """Affiche la structure de coalitions, rôle des leaders et gains par membre."""
    print("\n" + "─"*70)
    print("  Résultats Q2a : structure de coalitions (mode compétitif)")
    print("─"*70)
    total_val = 0.0
    for idx, c in enumerate(coalitions, 1):
        gains = c.gain_par_membre()
        print(f"\n  ── Coalition {idx} ──")
        print(f"  {c}")
        print(f"    Leader (responsable de la négociation groupe) : {c.responsable}")
        print(f"    Membres :")
        total_prix = sum(profils[x].prix_service for x in c.membres)
        for m in sorted(c.membres):
            svc = profils[m].prix_service
            eco = gains[m]
            # Formule détaillée pour chaque membre
            formule = f"économie = valeur_coalition × (prix_service / somme_prix) = {c.valeur():.2f} × ({svc} / {total_prix}) = {eco:.2f}€"
            print(f"      - {m} : prix_service={svc:.0f}€  économie={eco:.2f}€  (paie {svc - eco:.2f}€ au lieu de {svc:.0f}€)")
            print(f"            {formule}")
        total_val += c.valeur()
        print("  " + "─"*60)
    print(f"\n  Valeur totale des économies (base prix_service) : {total_val:.2f}€")
    print("      Formule : valeur = (somme des prix des membres) × taux de remise")
    print("      Exemple pour chaque coalition : valeur = (prix1 + prix2 + ...) × taux")
    print("─"*70)
