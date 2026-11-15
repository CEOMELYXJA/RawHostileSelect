# RawHostileSelect — L'arène des colis / Package Arena

## Français

La v4 représente les messages par de petites boîtes qui traversent un réseau simulé. On peut essayer une phrase, une couleur, un code ou un mélange; voir ce qui est envoyé et ce qui est réellement reconstruit; et suivre les résultats au fil des tours.

- **Population** : nombre de modèles de boîte (protocoles) essayés par tour. Chaque modèle peut envoyer plusieurs messages.
- **Générations** : nombre de tours. Les modèles retenus peuvent donner naissance à d'autres modèles au tour suivant. Les boîtes imbriquées sont une métaphore visuelle, pas une structure physique simulée.
- **Graine** : numéro qui permet de refaire les mêmes tirages aléatoires avec les mêmes réglages et la même version du programme.
- **À l'arrivée** : une boîte peut arriver intacte, arriver avec un message modifié ou illisible, ou se perdre. Des octets corrompus peuvent ne plus former du texte UTF-8 valide : ils ne sont pas transformés en phrase inventée.

L'arène est une application locale pour explorer le moteur Python de RawHostileSelect. La page GitHub Pages présente le projet : elle n'exécute pas Python dans le navigateur. Le script `hostile_protocol_evolution.py` et sa commande existante restent disponibles.

### Installation sous Windows 10 ou 11

Pour utiliser le paquet autonome v4 sur Windows 10 ou 11 **64 bits**, extrayez complètement le ZIP, ouvrez le dossier `RawHostileSelect`, puis double-cliquez sur `LANCER LE PROGRAMME.bat`. Gardez tous ses fichiers ensemble. Ce paquet comprend Python, Tkinter et NumPy; aucune installation séparée n'est nécessaire sur un Windows compatible. Le [site du projet](https://ceomelyxja.github.io/RawHostileSelect/) indique le téléchargement disponible.

Pour une copie du **code source téléchargée depuis GitHub**, le runtime et les dépendances locales ne sont pas inclus :

1. Téléchargez le dépôt complet depuis GitHub avec **Code → Download ZIP**, puis extrayez-le dans un dossier. Gardez tous les fichiers ensemble.
2. Installez Python 3 depuis [python.org](https://www.python.org/downloads/windows/) si nécessaire. Pendant l'installation, incluez Tcl/Tk et pip; si l'option est proposée, ajoutez Python au PATH.
3. Ouvrez un terminal dans le dossier extrait et installez la dépendance :

   ```bat
   py -3 -m pip install -r requirements.txt --target .deps
   ```

   Si `py` n'est pas disponible, essayez `python -m pip install -r requirements.txt --target .deps`. Ce dossier garde la dépendance près du projet. Le lanceur peut aussi utiliser une installation de NumPy déjà présente ou, si disponible, le runtime Codex de l'ordinateur.
4. Double-cliquez sur `Démarrer_RawHostileSelect.bat`. Le lanceur vérifie Python, Tkinter et NumPy, puis ouvre `app.py`. En cas d'erreur, il garde la fenêtre ouverte avec des indications.

Vous pouvez aussi utiliser un terminal dans le dossier et saisir les commandes ci-dessous si NumPy est installé dans `.deps` :

```bat
set "PYTHONPATH=%CD%\.deps;%PYTHONPATH%"
py -3 app.py
```

La commande originale en mode texte demeure `py -3 hostile_protocol_evolution.py --generations 20 --pop 36 --hostile medium` (après avoir défini `PYTHONPATH` comme ci-dessus si nécessaire).

### À propos des résultats

Le bouton **HISTORIQUE DES COLIS** ouvre une liste des messages par tour : choisis un colis pour revoir son contenu au départ et à l'arrivée. L'historique reste disponible après la fin du test tant que le programme est ouvert, et **RECOMMENCER** le vide. Pour le conserver après la fermeture, utilise l'export JSON et ouvre ce fichier en replay.

L'application permet d'exécuter l'évolution par générations, de voir un échantillon de transmissions, sélections, éliminations, mutations et croisements enregistrés, d'exporter les résultats en JSON ou CSV et de rouvrir un replay JSON. La simulation tourne en arrière-plan. L'arène emploie des métaphores visuelles : elle ne simule pas des personnages physiques. Les animations ne montrent qu'un échantillon des événements enregistrés.

La fiche d'un protocole comprend un arbre cliquable, des explications en français ou en anglais, les parents et l'historique enregistrés. Choisis un essai puis clique sur une opération pour voir les traces d'octets avant et après, lorsque disponibles. Ces extraits se limitent à 64 octets et sont clairement identifiés comme tels. Les anciens replays sans trace affichent leur absence plutôt qu'un exemple inventé. Le tableau de bord présente notamment le front de Pareto, les niches, la complexité, la latence, les pertes et les octets envoyés.

Les résultats décrivent le modèle informatique et ses hypothèses, pas des tests d'un réseau physique. Chaque protocole est évalué sur un petit nombre de messages; les valeurs peuvent donc beaucoup varier. Les mesures de la v3/v4 utilisent d'autres définitions que celles de la v2 : **leurs scores ne sont pas directement comparables**. En v4, changer le type ou la longueur des messages change aussi l'expérience; comparez des essais avec les mêmes réglages.

Dans la v4 :

- **Livraison** : paquets reçus divisés par le nombre de tentatives.
- **Intégrité** : messages reconstruits exactement divisés par le nombre de tentatives.
- **Résilience** : proportion de messages reconstruits exactement lors d'essais extrêmes séparés.
- **Efficacité** : somme des octets d'origine des messages reconstruits exactement, divisée par les octets réellement envoyés, puis multipliée par `1 / (1 + latence moyenne des paquets reçus / 40)`. C'est un score calculé du modèle, pas un débit réel; il vaut zéro lorsqu'il n'y a aucun octet envoyé ou aucune latence mesurée.

La latence est exprimée en unités simulées. Dans ce modèle, l'opération `FRAGMENT` est neutre; une somme de contrôle peut manquer certaines erreurs. Une livraison ne garantit pas une reconstruction exacte.

Cette première version n'inclut pas encore toutes les fonctions souhaitées. Les animations sont des représentations pédagogiques d'un échantillon d'événements; elles ne démontrent pas une performance sur un vrai réseau.

## English

Version 4 represents messages as little boxes travelling through a simulated network. Try a sentence, color, code, or a mix; see what was sent and what was actually reconstructed; and follow results across rounds.

- **Population**: number of box designs (protocols) tested in each round. Each design may send several messages.
- **Generations**: number of rounds. Selected designs can give rise to other designs in the next round. Nested boxes are a visual metaphor, not a physical structure simulated by the model.
- **Seed**: a number that repeats the same random draws with the same settings and program version.
- **At the end**: a box can arrive intact, arrive with a changed or unreadable message, or get lost. Corrupted bytes may no longer form valid UTF-8 text; no replacement sentence is invented.

The arena is a local interface for exploring RawHostileSelect's Python engine. The GitHub Pages website describes the project; it does not execute Python in the browser. The `hostile_protocol_evolution.py` script and its existing command remain available.

### Installation on Windows 10 or 11

To use the self-contained v4 package on **64-bit** Windows 10 or 11, extract the ZIP completely, open the `RawHostileSelect` folder, then double-click `LANCER LE PROGRAMME.bat`. Keep all its files together. This package includes Python, Tkinter and NumPy; no separate installation is needed on a compatible Windows computer. The [project website](https://ceomelyxja.github.io/RawHostileSelect/) shows the available download.

For a **source-code copy downloaded from GitHub**, the runtime and local dependencies are not included:

1. Download the complete repository from GitHub using **Code → Download ZIP**, then extract it to a folder. Keep all the files together.
2. Install Python 3 from [python.org](https://www.python.org/downloads/windows/) if needed. Include Tcl/Tk and pip in the installation; add Python to PATH if the option is offered.
3. Open a terminal in the extracted folder and install the dependency:

   ```bat
   py -3 -m pip install -r requirements.txt --target .deps
   ```

   If `py` is unavailable, try `python -m pip install -r requirements.txt --target .deps`. This folder keeps the dependency beside the project. The launcher can also use an existing NumPy installation or, when available, the computer's Codex runtime.
4. Double-click `Démarrer_RawHostileSelect.bat`. The launcher checks for Python, Tkinter and NumPy, then opens `app.py`. If it encounters an error, it keeps the window open with guidance.

Alternatively, open a terminal in the folder and run the following if NumPy is installed in `.deps`:

```bat
set "PYTHONPATH=%CD%\.deps;%PYTHONPATH%"
py -3 app.py
```

The original text-mode command remains `py -3 hostile_protocol_evolution.py --generations 20 --pop 36 --hostile medium` (after setting `PYTHONPATH` as above if necessary).

### About the results

The **PACKAGE HISTORY** button opens a list of messages by round: choose a package to review its contents at departure and arrival. History remains available after the test while the app is open, and **RESTART** clears it. To keep it after closing the app, export JSON and reopen that file as a replay.

The application can run evolution one generation at a time, display a sample of recorded transmissions, selections, eliminations, mutations and crossovers, export results as JSON or CSV, and reopen a JSON replay. The simulation runs in the background. The arena uses visual metaphors: it does not simulate physical characters. The animation shows only a sample of recorded events.

A protocol's details include a clickable tree, explanations in French or English, and recorded parents and history. Choose a trial and click an operation to see before-and-after byte traces when available. These excerpts are limited to 64 bytes and clearly identified as such. Older replays without traces show that the information is unavailable instead of inventing an example. The dashboard includes the Pareto front, niches, complexity, latency, losses, and bytes sent.

Results describe the computer model and its assumptions, not tests of a physical network. Each protocol is evaluated on a small number of messages, so values can vary considerably. Versions 3 and 4 use different definitions from version 2: **their scores are not directly comparable**. In v4, changing message type or length also changes the experiment; compare trials with the same settings.

In v4:

- **Delivery**: packets received divided by attempts.
- **Integrity**: messages reconstructed exactly divided by attempts.
- **Resilience**: fraction of messages reconstructed exactly in separate extreme trials.
- **Efficiency**: sum of the original bytes of exactly reconstructed messages, divided by bytes actually sent, multiplied by `1 / (1 + average latency of received packets / 40)`. This is a calculated model score, not actual throughput; it is zero when no bytes were sent or no latency was measured.

Latency is expressed in simulated units. In this model, `FRAGMENT` is a neutral operation; a checksum can miss some errors. Delivery does not guarantee exact reconstruction.

This first version does not yet include every requested feature. Animations are educational representations of a sample of events; they do not demonstrate performance on a real network.
