# RawHostileSelect — Evolution Arena

## Français

Evolution Arena est l'interface locale en cours de développement pour explorer le moteur Python de RawHostileSelect. La page GitHub Pages présente le projet : elle n'exécute pas Python dans le navigateur. Le script `hostile_protocol_evolution.py` et sa commande existante restent disponibles.

### Installation sous Windows 10 ou 11

Pour Windows 10 ou 11 **64 bits**, [téléchargez le paquet autonome](https://github.com/CEOMELYXJA/RawHostileSelect/releases/download/v3.0.0-arena/RawHostileSelect-Windows.zip), extrayez complètement le ZIP, puis double-cliquez sur `Démarrer_RawHostileSelect.bat` dans le dossier extrait. Gardez tous ses fichiers ensemble. Ce paquet comprend Python, Tkinter et NumPy; aucune installation séparée n'est nécessaire sur un Windows compatible.

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

L'application permet d'exécuter l'évolution par générations, de voir un échantillon de transmissions, sélections, éliminations, mutations et croisements enregistrés, d'exporter les résultats en JSON ou CSV et de rouvrir un replay JSON. La simulation tourne en arrière-plan. L'arène emploie des métaphores visuelles : elle ne simule pas des personnages physiques. Les animations ne montrent qu'un échantillon des événements enregistrés.

La fiche d'un protocole comprend un arbre cliquable, des explications en français ou en anglais, les parents et l'historique enregistrés. Choisis un essai puis clique sur une opération pour voir les traces d'octets avant et après, lorsque disponibles. Ces extraits se limitent à 64 octets et sont clairement identifiés comme tels. Les anciens replays sans trace affichent leur absence plutôt qu'un exemple inventé. Le tableau de bord présente notamment le front de Pareto, les niches, la complexité, la latence, les pertes et les octets envoyés.

Les résultats décrivent le modèle informatique et ses hypothèses, pas des tests d'un réseau physique. Chaque protocole est évalué sur un petit nombre de messages; les valeurs peuvent donc beaucoup varier. Les mesures de la v3 utilisent d'autres définitions que celles de la v2 : **leurs scores ne sont pas directement comparables**.

Dans la v3 :

- **Livraison** : paquets reçus divisés par le nombre de tentatives.
- **Intégrité** : messages reconstruits exactement divisés par le nombre de tentatives.
- **Résilience** : proportion de messages reconstruits exactement lors d'essais extrêmes séparés.
- **Efficacité** : octets utiles reconstruits divisés par les octets envoyés, multipliés par `1 / (1 + latence moyenne des paquets reçus / 40)`. C'est un score calculé du modèle, pas un débit réel; il vaut zéro lorsqu'il n'y a aucun octet envoyé ou aucune latence mesurée.

La latence est exprimée en unités simulées. Dans ce modèle, l'opération `FRAGMENT` est neutre; une somme de contrôle peut manquer certaines erreurs. Une livraison ne garantit pas une reconstruction exacte.

Cette première version n'inclut pas encore toutes les fonctions souhaitées. Les animations sont des représentations pédagogiques d'un échantillon d'événements; elles ne démontrent pas une performance sur un vrai réseau.

## English

Evolution Arena is the local interface under development for exploring RawHostileSelect's Python engine. The GitHub Pages website describes the project; it does not execute Python in the browser. The `hostile_protocol_evolution.py` script and its existing command remain available.

### Installation on Windows 10 or 11

For **64-bit** Windows 10 or 11, [download the self-contained package](https://github.com/CEOMELYXJA/RawHostileSelect/releases/download/v3.0.0-arena/RawHostileSelect-Windows.zip), extract the ZIP completely, then double-click `Démarrer_RawHostileSelect.bat` in the extracted folder. Keep all its files together. This package includes Python, Tkinter and NumPy; no separate installation is needed on a compatible Windows computer.

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

The application can run evolution one generation at a time, display a sample of recorded transmissions, selections, eliminations, mutations and crossovers, export results as JSON or CSV, and reopen a JSON replay. The simulation runs in the background. The arena uses visual metaphors: it does not simulate physical characters. The animation shows only a sample of recorded events.

A protocol's details include a clickable tree, explanations in French or English, and recorded parents and history. Choose a trial and click an operation to see before-and-after byte traces when available. These excerpts are limited to 64 bytes and clearly identified as such. Older replays without traces show that the information is unavailable instead of inventing an example. The dashboard includes the Pareto front, niches, complexity, latency, losses, and bytes sent.

Results describe the computer model and its assumptions, not tests of a physical network. Each protocol is evaluated on a small number of messages, so values can vary considerably. Version 3 uses different definitions from version 2: **their scores are not directly comparable**.

In v3:

- **Delivery**: packets received divided by attempts.
- **Integrity**: messages reconstructed exactly divided by attempts.
- **Resilience**: fraction of messages reconstructed exactly in separate extreme trials.
- **Efficiency**: reconstructed useful bytes divided by sent bytes, multiplied by `1 / (1 + average latency of received packets / 40)`. This is a calculated model score, not actual throughput; it is zero when no bytes were sent or no latency was measured.

Latency is expressed in simulated units. In this model, `FRAGMENT` is a neutral operation; a checksum can miss some errors. Delivery does not guarantee exact reconstruction.

This first version does not yet include every requested feature. Animations are educational representations of a sample of events; they do not demonstrate performance on a real network.
