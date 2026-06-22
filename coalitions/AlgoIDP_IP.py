
# ...existing code...

# --- Correction : import __future__ doit être tout en haut ---
from __future__ import annotations

from itertools import combinations
from typing import Optional

from coalitions.Coalition import Coalition, ProfilAcheteur, generer_taux


# ══════════════════════════════════════════════════════════════════════════════
# Utilitaires
# ══════════════════════════════════════════════════════════════════════════════

def _compatible(S: frozenset, profils_d: dict) -> bool:
    """
    Une coalition est valide ssi tous ses membres partagent
    la même destination ET la même compagnie ET le même type_service.
    Ex : AirFrance/Rome/AVION + EasyJet/Paris/AVION → incompatible.
    """
    return (len({profils_d[m].destination  for m in S}) == 1 and
            len({profils_d[m].compagnie    for m in S}) == 1 and
            len({profils_d[m].type_service for m in S}) == 1)


def _precomputer_valeurs(profils: list[ProfilAcheteur]) -> dict[frozenset, float]:
    """
    Calcule v(C) pour toutes les coalitions possibles, UNE SEULE FOIS.
    Partagé entre IDP et IP → les deux comparent sur la même base de taux.

    Coalition compatible  → valeur = Σ prix_service_i × taux (taux aléatoire fixé ici)
    Coalition incompatible → valeur = 0  (jamais sélectionnée par IDP ni IP)
    """
    agents    = [p.id for p in profils]
    prix_svc  = {p.id: p.prix_service for p in profils}
    profils_d = {p.id: p for p in profils}
    valeurs: dict[frozenset, float] = {}

    for taille in range(1, len(agents) + 1):
        for combo in combinations(agents, taille):
            S = frozenset(combo)
            if _compatible(S, profils_d):
                taux       = generer_taux(len(S))           # taux tiré une seule fois
                valeurs[S] = sum(prix_svc[m] for m in S) * taux
            else:
                valeurs[S] = 0.0                            # incompatible → jamais choisie
    return valeurs


def elire_leader(profils: list[ProfilAcheteur]) -> ProfilAcheteur:
    """
    Leader = acheteur avec le prix_service le plus élevé.
    Critère : celui qui a le plus à gagner d'une remise est le plus motivé
    à prendre en charge la coordination.
    """
    return max(profils, key=lambda p: p.prix_service)


def _simuler_collecte_info(leader: ProfilAcheteur,
                            profils: list[ProfilAcheteur]) -> None:
    """
    Simule la communication Q2b :
      1. Le leader diffuse un broadcast à tous les agents.
      2. Chaque agent répond avec ses infos PRIVÉES (budget_reel).
      3. Le leader peut vérifier la faisabilité individuelle.

    Différence avec Q2a : ici budget_reel est partagé (mode coopératif).
    """
    print(f"\n   [Q2b] Leader élu : {leader.id}"
          f"  (prix_service={leader.prix_service:.0f}€,"
          f" {leader.compagnie} / {leader.destination})")
    print(f"   Le leader diffuse un BROADCAST à {len(profils)-1} autre(s) agent(s)...")
    for p in profils:
        if p.id == leader.id:
            continue
        faisable = p.prix_service * 0.80 <= p.budget_reel
        print(f"    {leader.id} ← {p.id} : "
              f"service=({p.compagnie}/{p.destination}/{p.type_service.value})  "
              f"prix_svc={p.prix_service:.0f}€  budget_reel={p.budget_reel:.0f}€"
              + ("  [faisable]" if faisable else "  [budget serré]"))
    print(f"   Leader {leader.id} calcule la structure optimale (info complète)...")


# ══════════════════════════════════════════════════════════════════════════════
# IDP — Programmation Dynamique (bipartitions)
# ══════════════════════════════════════════════════════════════════════════════

def IDP(profils: list[ProfilAcheteur],
        valeurs: Optional[dict] = None,
        leader: Optional[ProfilAcheteur] = None) -> tuple[list[Coalition], float]:
    """
    Recherche la structure de coalitions optimale par DP sur les bipartitions.

    Principe :
        f(S) = valeur de la meilleure partition de S
        f({i}) = v({i})   (singleton)
        f(S)   = max( v(S),  max sur tous les splits (S1,S2) de  f(S1)+f(S2) )

    On calcule d'abord les singletons, puis les paires, puis les triplets...
    (bottom-up par taille croissante) pour que f(S1) et f(S2) soient déjà
    connus quand on traite S.
    Complexité O(3^n).
    """
    agents   = [p.id for p in profils]
    prix_svc = {p.id: p.prix_service for p in profils}
    n        = len(agents)

    if valeurs is None:
        valeurs = _precomputer_valeurs(profils)

    sep = "─" * 62
    print(f"\n{'═'*62}")
    print(f"  IDP — Programmation Dynamique  (O(3^n))")
    print(f"{'═'*62}")
    if leader:
        print(f"  Leader : {leader.id} | {n} agents | {2**n - 1} coalitions à évaluer")
    print()

    f:     dict[frozenset, float]                                 = {}
    split: dict[frozenset, Optional[tuple[frozenset, frozenset]]] = {}

    for taille in range(1, n + 1):
        print(f"  ── Taille {taille} ──────────────────────────────────────")
        for combo in combinations(agents, taille):
            S        = frozenset(combo)
            f[S]     = valeurs[S]   # valeur initiale : S reste entière
            split[S] = None         # pas de split pour l'instant
            S_str    = "{" + ",".join(sorted(S)) + "}"

            if taille == 1:
                print(f"    f({S_str}) = v({S_str}) = {f[S]:.2f}€  (singleton)")
            else:
                print(f"    f({S_str}) : v({S_str})={valeurs[S]:.2f}€ (rester entier)")
                agents_S = list(S)
                for r in range(1, taille):
                    for sous in combinations(agents_S, r):
                        S1 = frozenset(sous)
                        S2 = S - S1
                        if sorted(S1) > sorted(S2):
                            continue
                        val = f[S1] + f[S2]
                        S1_str = "{" + ",".join(sorted(S1)) + "}"
                        S2_str = "{" + ",".join(sorted(S2)) + "}"
                        marker = " ← MEILLEUR" if val > f[S] else ""
                        print(f"      split {S1_str}|{S2_str} : f({S1_str})={f[S1]:.2f} + f({S2_str})={f[S2]:.2f} = {val:.2f}€{marker}")
                        if val > f[S]:
                            f[S]     = val
                            split[S] = (S1, S2)
                decision = "rester entier" if split[S] is None else "{" + ",".join(sorted(split[S][0])) + "}|{" + ",".join(sorted(split[S][1])) + "}"
                print(f"    → f({S_str}) = {f[S]:.2f}€  (meilleure décision : {decision})")
        print()

    def reconstruire(S: frozenset) -> list[frozenset]:
        if split[S] is None:
            return [S]
        S1, S2 = split[S]
        return reconstruire(S1) + reconstruire(S2)

    A         = frozenset(agents)
    partition = reconstruire(A)
    coalitions = [Coalition(list(S), prix_svc) for S in partition]

    print(f"  {sep}")
    print(f"  Reconstruction de la structure optimale depuis f(A) :")
    for S in partition:
        print(f"    {'{' + ','.join(sorted(S)) + '}'} → v = {valeurs[S]:.2f}€")
    print(f"  Valeur totale optimale (IDP) : {f[A]:.2f}€")
    print(f"{'═'*62}")
    return coalitions, f[A]


# ══════════════════════════════════════════════════════════════════════════════
# IP — Branch-and-Bound arborescent
# ══════════════════════════════════════════════════════════════════════════════

def IP(profils: list[ProfilAcheteur],
       valeurs: Optional[dict] = None,
       leader: Optional[ProfilAcheteur] = None) -> tuple[list[Coalition], float]:
    """
    Recherche la structure optimale par Branch-and-Bound sur sous-espaces.

    Principe (cours) :
      1. Diviser l'espace en sous-espaces = partitions entières de N
         (ex N=3 : [1,1,1], [1,2], [3]).
      2. UB([t1,t2,...]) = Σ max_{|S|=ti} v(S)  (borne optimiste par taille).
      3. Explorer par ordre décroissant d'UB.
      4. Élaguer si UB < meilleure valeur courante.
    """
    agents   = [p.id for p in profils]
    prix_svc = {p.id: p.prix_service for p in profils}
    n        = len(agents)

    if valeurs is None:
        valeurs = _precomputer_valeurs(profils)

    sep = "─" * 62
    print(f"\n{'═'*62}")
    print(f"  IP — Branch-and-Bound par sous-espaces")
    print(f"{'═'*62}")
    if leader:
        print(f"  Leader : {leader.id} | N={n}")

    # max_par_taille[t] = meilleure valeur d'une coalition de taille exactement t
    max_par_taille: dict[int, float] = {}
    for t in range(1, n + 1):
        vals = [valeurs[S] for S in valeurs if len(S) == t]
        max_par_taille[t] = max(vals) if vals else 0.0

    print(f"\n  Étape 1 — max par taille (meilleure coalition de chaque taille) :")
    for t in range(1, n + 1):
        best_S = max((S for S in valeurs if len(S) == t), key=lambda s: valeurs[s])
        print(f"    max_taille[{t}] = {max_par_taille[t]:.2f}€  "
              f"(meilleure coalition : {'{' + ','.join(sorted(best_S)) + '}'}  v={valeurs[best_S]:.2f}€)")

    # Partitions entières de n
    def partitions_entieres(reste: int, min_val: int = 1):
        if reste == 0:
            yield []
            return
        for first in range(min_val, reste + 1):
            for rest in partitions_entieres(reste - first, first):
                yield [first] + rest

    # UB de chaque sous-espace → tri décroissant
    sous_espaces = []
    for tailles in partitions_entieres(n):
        ub = sum(max_par_taille[t] for t in tailles)
        sous_espaces.append((ub, tailles))
    sous_espaces.sort(key=lambda x: -x[0])

    print(f"\n  Étape 2 — {len(sous_espaces)} sous-espaces triés par UB décroissant :")
    for ub, tailles in sous_espaces:
        ub_detail = " + ".join(f"max[{t}]={max_par_taille[t]:.2f}" for t in tailles)
        print(f"    {str(tailles):<14}  UB = {ub_detail} = {ub:.2f}€")

    # Énumération des partitions d'ensembles pour des tailles données
    def partitions_ensembles(agents_list: list, tailles: list):
        if not tailles:
            yield []
            return
        t = tailles[0]
        for combo in combinations(agents_list, t):
            restants = [a for a in agents_list if a not in combo]
            for rest in partitions_ensembles(restants, tailles[1:]):
                yield [frozenset(combo)] + rest

    meilleur_val     = -1.0
    meilleure_struct: list[frozenset] = []
    stats = {"explores": 0, "elagues": 0}

    print(f"\n  Étape 3 — Exploration (meilleur_val mis à jour en temps réel) :")
    for ub, tailles in sous_espaces:
        if ub < meilleur_val:
            stats["elagues"] += 1
            print(f"    {str(tailles):<14}  UB={ub:.2f}€ < meilleur={meilleur_val:.2f}€  → ÉLAGUÉ ✗")
            continue
        print(f"    {str(tailles):<14}  UB={ub:.2f}€ ≥ meilleur={max(meilleur_val,0):.2f}€  → EXPLORE")
        seen: set = set()
        for partition in partitions_ensembles(agents, tailles):
            key = frozenset(partition)
            if key in seen:
                continue
            seen.add(key)
            stats["explores"] += 1
            val = sum(valeurs.get(C, 0.0) for C in partition)
            parts_str = " | ".join("{" + ",".join(sorted(C)) + "}=" + f"{valeurs.get(C,0):.2f}€" for C in partition)
            marker = "  ← NOUVEAU MEILLEUR" if val > meilleur_val else ""
            print(f"      {parts_str}  → total={val:.2f}€{marker}")
            if val > meilleur_val:
                meilleur_val     = val
                meilleure_struct = list(partition)

    val_finale = max(meilleur_val, 0.0)
    print(f"\n  {sep}")
    print(f"  {stats['explores']} partition(s) explorée(s), {stats['elagues']} sous-espace(s) élagué(s)")
    print(f"  Valeur totale optimale (IP) : {val_finale:.2f}€")
    print(f"{'═'*62}")

    coalitions = [Coalition(list(S), prix_svc) for S in meilleure_struct]
    return coalitions, val_finale
def comparer_couplage_idp_ip(profils: list[ProfilAcheteur], valeurs: dict, profils_dict: dict) -> None:
    """
    Compare les résultats des trois méthodes : Couplage (Q2a), IDP, IP (Q2b).
    Affiche les coalitions, la valeur totale, le détail du meilleur groupe et une interprétation.
    """
    from coalitions.AlgoCouplage import algorithme_couplage
    print("\n" + "═"*70)
    print("  COMPARAISON : Couplage (Q2a) vs IDP/IP (Q2b)")
    print("═"*70)

    # Couplage (Q2a)
    coal_couplage = algorithme_couplage(profils, valeurs)
    val_couplage = sum(c.valeur() for c in coal_couplage)
    print("\n[COUPLAGE — Mode compétitif]")
    for c in coal_couplage:
        print(f"  {c}")
    print(f"  → Valeur totale (économies) : {val_couplage:.2f}€")
    best_coup = max(coal_couplage, key=lambda c: c.valeur())
    print(f"  Meilleure coalition : {best_coup}")

    # IDP (Q2b)
    print("\n[IDP — Mode coopératif]")
    coal_idp, val_idp = IDP(profils, valeurs=valeurs)
    for c in coal_idp:
        print(f"  {c}")
    print(f"  → Valeur totale (économies) : {val_idp:.2f}€")
    best_idp = max(coal_idp, key=lambda c: c.valeur())
    print(f"  Meilleure coalition : {best_idp}")

    # IP (Q2b)
    print("\n[IP — Mode coopératif]")
    coal_ip, val_ip = IP(profils, valeurs=valeurs)
    for c in coal_ip:
        print(f"  {c}")
    print(f"  → Valeur totale (économies) : {val_ip:.2f}€")
    best_ip = max(coal_ip, key=lambda c: c.valeur())
    print(f"  Meilleure coalition : {best_ip}")

    print("\n" + "─"*70)
    print("INTERPRÉTATION :")
    print("- Le couplage (Q2a) forme des groupes localement stables, mais pas forcément optimaux.")
    print("- IDP et IP (Q2b) trouvent la structure globale optimale (même résultat attendu pour les deux).\n")
    if abs(val_idp - val_ip) < 1e-6:
        print("- IDP et IP donnent la même valeur totale, confirmant l'optimalité.")
    else:
        print("- Différence inattendue entre IDP et IP : vérifier l'implémentation !")
    if val_idp > val_couplage:
        print(f"- Le mode coopératif (IDP/IP) permet d'obtenir {val_idp - val_couplage:.2f}€ d'économies supplémentaires par rapport au mode compétitif.")
    else:
        print("- Le mode compétitif a donné un résultat aussi bon ou meilleur (rare !)")
    print("─"*70)
