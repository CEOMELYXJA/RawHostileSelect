# RawHostileSelect

**Auto-évolution de protocoles par sélection naturelle dans un environnement hostile**

> On ne conçoit plus. On laisse évoluer.  
> Des populations de protocoles (sous forme d’arbres d’opérations) s’affrontent sous bruit, pertes, latence, pannes et attaques.  
> Ce qui survit n’a plus besoin de ressembler aux abstractions classiques.

**Site / pages** : [https://ceomelyxja.github.io/RawHostileSelect/](https://ceomelyxja.github.io/RawHostileSelect/)

---

## Version 2.0 — Genetic Programming + Multi-objectif + Niches

### Ce qui a changé

1. **Genetic Programming (priorité #1)**  
   Les protocoles ne sont plus des vecteurs de paramètres.  
   Ce sont des **arbres d’opérations** :
   - `SCRAMBLE`, `INTERLEAVE`, `ADD_PARITY`, `CHECKSUM`
   - `REPEAT`, `REVERSE`, `XOR_CONST`, `PAD`, `FRAGMENT`, `IDENTITY`
   - Mutation de nœuds / paramètres / sous-arbres
   - Crossover par échange de sous-arbres

2. **Sélection multi-objectifs + niches (priorité #4)**  
   - Fitness vectorielle : `(delivery, integrity, efficiency, resilience)`
   - Tri de non-domination (Pareto) style NSGA-II
   - Crowding distance
   - Speciation / niches basées sur la structure de l’arbre

### Objectif

Faire émerger des stratégies de communication et de reconstruction qui n’ont plus rien à voir avec les protocoles classiques.

---

## Installation

```bash
pip install numpy
```

## Utilisation

```bash
# Évolution standard
python hostile_protocol_evolution.py --generations 20 --pop 36 --hostile medium

# Environnement extrême
python hostile_protocol_evolution.py --generations 25 --pop 40 --hostile extreme --seed 7
```

### Options

| Argument       | Défaut   | Description                  |
|----------------|----------|------------------------------|
| `--generations`| 15       | Nombre de générations        |
| `--pop`        | 32       | Taille de la population      |
| `--hostile`    | medium   | light / medium / extreme     |
| `--seed`       | 42       | Graine aléatoire             |

---

## Exemple de sortie

```
Gen   0 | Best scalar: 0.31 | Avg: 0.18 | Front0: 4 | id=... rank=0 ...
Gen   5 | Best scalar: 0.47 | ...
...
ÉVOLUTION TERMINÉE
Arbre du meilleur protocole :
REPEAT(2.0)
  SCRAMBLE(3142.0)
    ADD_PARITY()
      REVERSE()
```

---

## Structure du dépôt

```
RawHostileSelect/
├── hostile_protocol_evolution.py   # Cœur (GP + multi-objectif)
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

---

## Roadmap

- [x] Genetic Programming (arbres d’opérations)
- [x] Multi-objectif + niches
- [ ] Architectures mémoire non-classiques (codes dispersés, reconstruction partielle)
- [ ] Co-évolution de l’adversaire
- [ ] Agents sans concept explicite de « message »

---

## Licence

MIT
