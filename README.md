# Hostile Protocol Evolution

**Auto-évolution de protocoles par sélection naturelle dans un environnement hostile**

> On ne conçoit plus. On laisse évoluer.  
> Des populations de protocoles et d’architectures de mémoire s’affrontent sous bruit, pertes de paquets, latence variable, pannes et attaques adversariales.  
> Ce qui survit devient le nouveau stack.

## Idée

Ce projet explore la *reverse-technology par sélection* plutôt que par ingénierie classique.  
L’objectif n’est pas d’optimiser TCP/IP ou les abstractions actuelles (fichiers, processus, pages), mais de faire émerger des mécanismes de communication et de mémoire radicalement différents, adaptés à des conditions extrêmement hostiles.

## Fonctionnalités actuelles (v1)

- Environnement hostile paramétrable (`light` / `medium` / `extreme`)
  - Flips de bits
  - Pertes de paquets
  - Latence + jitter
  - Corruption adversariale
  - Pannes de nœuds
- Genome évolutif (protocole + stratégie mémoire)
  - Redondance, interleaving, ACK, timeout, retries
  - Fragmentation, scrambling, parité, checksum
  - Dispersion mémoire + seuil de reconstruction
- Boucle évolutive complète (sélection, crossover, mutation, élitisme)
- Fitness multi-critères (livraison + intégrité + efficacité)

## Installation

```bash
# Python 3.9+ recommandé
pip install numpy
```

## Utilisation

```bash
# Évolution standard
python hostile_protocol_evolution.py --generations 25 --pop 36 --hostile medium

# Environnement extrême
python hostile_protocol_evolution.py --generations 30 --pop 40 --hostile extreme --seed 7

# Options disponibles
python hostile_protocol_evolution.py --help
```

## Exemple de sortie

```
Gen   0 | Best: 0.5281 | Avg: 0.1228 | id=... | red=1.21 inter=3 ack=2 ...
Gen   1 | Best: 0.5109 | Avg: 0.2193 | ...
...
ÉVOLUTION TERMINÉE
Meilleur protocole final : fitness=0.6083
```

## Roadmap / directions futures

1. **Genetic Programming** – représenter les protocoles comme des arbres d’opérations (vraie émergence de structures)
2. **Architectures mémoire non-classiques** – codes dispersés, reconstruction partielle, mémoire « dans le bruit »
3. **Co-évolution adversaire** – l’attaquant évolue aussi
4. **Sélection multi-objectifs + niches**
5. **Agents sans concept de « message »** – maintien d’état partagé par effets de bord uniquement

## Licence

MIT

## Auteur / Contexte

Prototype exploratoire issu d’une discussion sur l’auto-évolution de protocoles par sélection naturelle.
