"""RawHostileSelect Evolution Arena: local, bilingual view of recorded events.

The simulation runs in a worker; Tk is touched only by the main thread.
"""
import csv
import json
import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from arena_engine import ArenaConfig, ArenaEngine


TEXT = {
    "fr": {
        "title": "RawHostileSelect — Evolution Arena", "subtitle": "Laboratoire évolutif · événements réels du moteur",
        "settings": "Réglages", "population": "Population", "generations": "Générations", "difficulty": "Difficulté", "seed": "Graine (seed)", "speed": "Vitesse",
        "slow": "Démonstration lente", "fast": "Exécution rapide", "start": "DÉMARRER", "pause": "PAUSE", "resume": "REPRENDRE", "next": "GÉNÉRATION SUIVANTE", "reset": "RECOMMENCER",
        "ready": "Prêt. Configure l'expérience puis démarre.", "working": "Calcul en cours…", "paused": "En pause entre deux générations.", "complete": "Expérience terminée.",
        "arena": "Arène des transmissions", "metaphor": "Furie : perturbations · Bolide : message · Planète : réseau hostile (métaphores)",
        "legend": "Vert : intact   Rouge : altéré   Gris : perdu   Orange : échec", "sample": "Animation : échantillon d'événements enregistrés, pas toutes les transmissions.",
        "progress": "Progression", "metrics": "Résultats de la génération", "best": "Meilleur score", "average": "Moyenne", "delivery": "Livraison", "integrity": "Intégrité", "efficiency": "Efficacité", "resilience": "Résilience", "front": "Front de Pareto", "diversity": "Diversité", "generation": "Génération", "individuals": "Protocoles — sélectionne pour inspecter", "inspect": "Inspecter", "narrative": "Journal de l'expérience", "export": "Exporter JSON", "csv": "Exporter CSV", "replay": "Ouvrir un replay", "replaymode": "Replay enregistré", "live": "Simulation locale", "no_data": "Aucune génération enregistrée.",
        "not_evaluated": "Pas encore évalué", "saved": "Fichier enregistré.", "error": "Erreur", "invalid": "Vérifie les paramètres : population de 2 à 100, générations de 1 à 1 000 et seed entière.", "no_history": "Lance au moins une génération avant l'export.", "open_error": "Impossible d'ouvrir ce replay.", "light": "Légère", "medium": "Moyenne", "extreme": "Extrême", "scalar": "Score pondéré", "original_hex": "Original (hex)", "encoded_hex": "Encodé (hex)", "received_hex": "Reçu (hex)", "decoded_hex": "Décodé (hex)",
        "gen_log": "Génération {g} : meilleur {best:.3f}, moyenne {avg:.3f}, front de Pareto {front}, diversité {div:.3f}.",
        "delta": "Variation du meilleur score : {delta:+.3f}. Les résultats peuvent fluctuer.", "events": "Événements enregistrés : {trans} transmissions, {mut} mutations, {cross} croisements, {sel} sélections, {elim} éliminations.",
        "transmission": "Protocole {id} · {scenario} : {outcome} · bits inversés {bits} · latence {latency}",
        "intact": "reconstruit intact", "corrupted": "contenu altéré", "lost": "paquet perdu", "failure": "panne", "encoding_error": "erreur d'encodage", "baseline": "épreuve normale", "stress": "épreuve extrême", "unavailable": "non mesuré",
        "inspect_title": "Fiche du protocole", "structure": "Structure génétique", "parents": "Parents enregistrés", "rank": "Rang de Pareto", "niche": "Niche", "stats": "Mesures enregistrées", "pipeline": "Original → Encodage → Réseau hostile → Décodage → Comparaison",
        "no_event": "Aucune transmission enregistrée pour ce protocole.", "measure_help": "Livraison : proportion de paquets reçus. Intégrité : proportion reconstruite exactement. Résilience : intégrité mesurée à l'épreuve extrême. Efficacité : score calculé selon le coût des octets et la latence. Score pondéré : 40 % livraison, 30 % intégrité, 15 % efficacité, 15 % résilience. Ces résultats ne démontrent pas une performance réelle.",
        "current": "Événement affiché", "id": "Protocole", "status": "Résultat", "limit": "Les temps d'animation sont adaptés à l'écran ; la latence numérique provient du moteur.", "report": "Bilan", "summary_end": "Les résultats décrivent uniquement les essais simulés. Une livraison ne garantit pas l'intégrité. Le front de Pareto regroupe les compromis non dominés, pas nécessairement le meilleur score pondéré.",
    },
    "en": {
        "title": "RawHostileSelect — Evolution Arena", "subtitle": "Evolution lab · actual engine events",
        "settings": "Settings", "population": "Population", "generations": "Generations", "difficulty": "Difficulty", "seed": "Seed", "speed": "Speed",
        "slow": "Slow demonstration", "fast": "Fast run", "start": "START", "pause": "PAUSE", "resume": "RESUME", "next": "NEXT GENERATION", "reset": "RESTART",
        "ready": "Ready. Configure the experiment and start.", "working": "Computing…", "paused": "Paused between generations.", "complete": "Experiment complete.",
        "arena": "Transmission arena", "metaphor": "Fury: disturbances · Racer: message · Planet: hostile network (metaphors)",
        "legend": "Green: intact   Red: corrupted   Grey: lost   Orange: failure", "sample": "Animation: a sample of recorded events, not every transmission.",
        "progress": "Progress", "metrics": "Generation results", "best": "Best score", "average": "Average", "delivery": "Delivery", "integrity": "Integrity", "efficiency": "Efficiency", "resilience": "Resilience", "front": "Pareto front", "diversity": "Diversity", "generation": "Generation", "individuals": "Protocols — select one to inspect", "inspect": "Inspect", "narrative": "Experiment log", "export": "Export JSON", "csv": "Export CSV", "replay": "Open replay", "replaymode": "Recorded replay", "live": "Local simulation", "no_data": "No generation recorded.",
        "not_evaluated": "Not evaluated yet", "saved": "File saved.", "error": "Error", "invalid": "Check settings: population 2–100, generations 1–1,000 and integer seed.", "no_history": "Run at least one generation before exporting.", "open_error": "Could not open this replay.", "light": "Light", "medium": "Medium", "extreme": "Extreme", "scalar": "Weighted score", "original_hex": "Original (hex)", "encoded_hex": "Encoded (hex)", "received_hex": "Received (hex)", "decoded_hex": "Decoded (hex)",
        "gen_log": "Generation {g}: best {best:.3f}, average {avg:.3f}, Pareto front {front}, diversity {div:.3f}.",
        "delta": "Change in best score: {delta:+.3f}. Results can fluctuate.", "events": "Recorded events: {trans} transmissions, {mut} mutations, {cross} crossovers, {sel} selections, {elim} eliminations.",
        "transmission": "Protocol {id} · {scenario}: {outcome} · flipped bits {bits} · latency {latency}",
        "intact": "reconstructed intact", "corrupted": "corrupted content", "lost": "packet lost", "failure": "node failure", "encoding_error": "encoding error", "baseline": "baseline trial", "stress": "extreme trial", "unavailable": "not measured",
        "inspect_title": "Protocol details", "structure": "Genetic structure", "parents": "Recorded parents", "rank": "Pareto rank", "niche": "Niche", "stats": "Recorded measurements", "pipeline": "Original → Encoding → Hostile network → Decoding → Comparison",
        "no_event": "No transmission recorded for this protocol.", "measure_help": "Delivery: proportion of packets received. Integrity: proportion reconstructed exactly. Resilience: integrity measured in the extreme trial. Efficiency: score calculated from byte cost and latency. Weighted score: 40% delivery, 30% integrity, 15% efficiency, 15% resilience. These results do not demonstrate real-world performance.",
        "current": "Displayed event", "id": "Protocol", "status": "Result", "limit": "Animation timing is adapted for display; the numerical latency comes from the engine.", "report": "Report", "summary_end": "Results describe simulated trials only. Delivery does not guarantee integrity. The Pareto front contains non-dominated trade-offs, not necessarily the highest weighted score.",
    },
}

TEXT['fr'].update({
    'simple_title': 'En bref — une simulation',
    'simple_explain': 'On fait semblant d’envoyer des colis : les colis sont des messages. Ils peuvent se perdre, arriver abîmés ou arriver intacts.',
    'simple_wait': 'Appuie sur DÉMARRER pour voir ce qui arrive aux colis.',
    'simple_result': 'Pour l’idée {id} : sur {attempts} essais, {received} colis sont arrivés ({delivery:.0%}). Parmi eux, {intact} messages étaient intacts ({integrity:.0%} des essais) et {damaged} encore abîmés. {lost} colis se sont perdus ; {other} autres essais ont échoué.',
    'simple_best': 'C’est la meilleure idée selon le score calculé. C’est une simulation, pas une preuve dans la vraie vie.',
    'simple_missing': 'Ce replay ne contient pas tous les comptes nécessaires pour ce résumé.',
    'dashboard': 'Tableau de bord', 'tree_tab': 'Arbre interactif', 'details_tab': 'Résultats', 'family_tab': 'Filiation',
    'click_node': 'Clique sur une opération. Les enfants sont exécutés avant leur parent.',
    'no_trace': "Cet enregistrement ne contient pas le détail de cette opération ; aucun exemple n'est inventé.",
    'before': 'Avant', 'after': 'Après', 'encoding': 'Encodage', 'decoding': 'Décodage', 'truncated': 'Extrait limité aux premiers octets',
    'no_tree': "Arbre détaillé non enregistré dans ce replay.", 'family_intro': 'Parents et historique enregistrés dans cette expérience :',
    'no_parents': 'Aucun parent enregistré (population initiale ou données absentes).', 'no_family_history': 'Aucun historique supplémentaire disponible.',
    'event_mutation': 'Mutation enregistrée · enfant {id} · parents {parents}',
    'event_crossover': 'Croisement enregistré · enfant {id} · parents {parents}',
    'event_selection': 'Sélection enregistrée · {id}', 'event_elimination': 'Élimination enregistrée · {id}',
    'unchanged': 'Le croisement a produit le même arbre que le premier parent.',
    'niches': 'Répartition par niche', 'complexity': 'Complexité des arbres (nombre de nœuds)', 'latency_mean': 'Latence moyenne mesurée',
    'pareto_note': 'Points : chaque protocole ; horizontal = livraison, vertical = intégrité. Vert = front 0.',
    'population_stats': 'Population évaluée', 'lost_count': 'Pertes', 'failure_count': 'Pannes', 'byte_count': 'Octets envoyés',
    'trial_note': 'Les coûts et les pertes ci-dessous concernent les essais de référence ; la résilience correspond aux essais extrêmes distincts.',
    'history_generation': 'Génération {g} : score {score:.3f}, rang {rank}, structure :\n{tree}',
    'bit_changes': 'Bits modifiés enregistrés', 'no_bits': 'Aucun détail de bit disponible pour cet essai.',
    'observation': 'Observation réelle (essai enregistré)', 'generation_change': 'Évolution depuis la génération précédente',
    'tree_size': 'Complexité', 'attack': 'Corruption adversariale', 'checksum_failed': 'Contrôle détecté en échec',
    'yes': 'oui', 'no': 'non', 'sample': "Animation : échantillon de transmissions et d'événements évolutifs enregistrés.",
    'report_progress': "Bilan jusqu'ici : {first} → {last} ; meilleur score {start:.3f} → {end:.3f} ({delta:+.3f}).",
    'report_result': "Dans la dernière population, {id} a le meilleur score pondéré : livraison {delivery:.1%}, intégrité {integrity:.1%}, résilience {resilience:.1%}. Sur les essais de référence : {lost} pertes, {failures} pannes, {bytes} octets envoyés.",
    'report_failure': "Une intégrité de 0 % signifie qu'aucun essai de ce protocole n'a reconstruit le message exactement ; elle ne signifie pas nécessairement qu'aucun paquet n'est arrivé.",
})
TEXT['en'].update({
    'simple_title': 'In a nutshell — a simulation',
    'simple_explain': 'We pretend to send packages: the packages are messages. They can get lost, arrive damaged or arrive intact.',
    'simple_wait': 'Press START to see what happens to the packages.',
    'simple_result': 'For idea {id}: out of {attempts} trials, {received} packages arrived ({delivery:.0%}). Of those, {intact} messages were intact ({integrity:.0%} of trials) and {damaged} were still damaged. {lost} packages were lost; {other} other trials failed.',
    'simple_best': 'This is the best idea by calculated score. It is a simulation, not proof of real-world performance.',
    'simple_missing': 'This replay does not contain all the counts needed for this summary.',
    'dashboard': 'Dashboard', 'tree_tab': 'Interactive tree', 'details_tab': 'Results', 'family_tab': 'Lineage',
    'click_node': 'Click an operation. Children are executed before their parent.',
    'no_trace': 'This recording contains no detail for this operation; no example is invented.',
    'before': 'Before', 'after': 'After', 'encoding': 'Encoding', 'decoding': 'Decoding', 'truncated': 'Excerpt limited to the first bytes',
    'no_tree': 'Detailed tree not recorded in this replay.', 'family_intro': 'Parents and history recorded in this experiment:',
    'no_parents': 'No recorded parents (initial population or missing data).', 'no_family_history': 'No additional history available.',
    'event_mutation': 'Recorded mutation · child {id} · parents {parents}',
    'event_crossover': 'Recorded crossover · child {id} · parents {parents}',
    'event_selection': 'Recorded selection · {id}', 'event_elimination': 'Recorded elimination · {id}',
    'unchanged': 'Crossover produced the same tree as the first parent.',
    'niches': 'Population by niche', 'complexity': 'Tree complexity (node count)', 'latency_mean': 'Measured average latency',
    'pareto_note': 'Dots: each protocol; horizontal = delivery, vertical = integrity. Green = front 0.',
    'population_stats': 'Evaluated population', 'lost_count': 'Packet losses', 'failure_count': 'Failures', 'byte_count': 'Bytes sent',
    'trial_note': 'Costs and losses below concern baseline trials; resilience comes from separate extreme trials.',
    'history_generation': 'Generation {g}: score {score:.3f}, rank {rank}, structure:\n{tree}',
    'bit_changes': 'Recorded changed bits', 'no_bits': 'No bit detail is available for this trial.',
    'observation': 'Actual observation (recorded trial)', 'generation_change': 'Change since previous generation',
    'tree_size': 'Complexity', 'attack': 'Adversarial corruption', 'checksum_failed': 'Failed check detected',
    'yes': 'yes', 'no': 'no', 'sample': 'Animation: a sample of recorded transmission and evolution events.',
    'report_progress': 'Report so far: {first} → {last}; best score {start:.3f} → {end:.3f} ({delta:+.3f}).',
    'report_result': 'In the last population, {id} has the highest weighted score: delivery {delivery:.1%}, integrity {integrity:.1%}, resilience {resilience:.1%}. Across baseline trials: {lost} losses, {failures} failures, {bytes} bytes sent.',
    'report_failure': 'Integrity of 0% means that no trial for this protocol reconstructed the message exactly; it does not necessarily mean that no packet arrived.',
})

# Version 4 keeps the scientific model but introduces a concrete delivery
# analogy. A design is a protocol candidate; an individual trial is a box.
TEXT['fr'].update({
    'title': 'RawHostileSelect 4 · Le voyage des colis',
    'subtitle': 'Une petite aventure pour voir comment les messages voyagent',
    'population': 'Modèles de boîtes', 'generations': 'Tours', 'generation': 'Tour',
    'seed': 'Numéro magique', 'arena': 'Le voyage des boîtes',
    'metaphor': 'Départ → Furie et le chemin perturbé → arrivée',
    'progress': 'Que deviennent les boîtes ?',
    'legend': 'Vert : intact   Rose : abîmé   Gris : perdu   Orange : panne ou échec',
    'sample': 'On anime quelques essais enregistrés. Chaque boîte est un message testé.',
    'seed_help': 'Numéro magique = graine : avec le même numéro et les mêmes réglages, les mêmes tirages se répètent.',
    'population_help': 'Modèles : façons de protéger les boîtes. Un tour teste chaque modèle ; les suivants héritent de modèles sélectionnés.',
    'message_type': 'Message dans les boîtes', 'mixed': 'Un mélange', 'phrase': 'Une phrase', 'color': 'Une couleur', 'code': 'Un petit code', 'mode_note': '(type et langue choisis au démarrage)',
    'start_box': 'AU DÉPART', 'arrival_box': 'À L’ARRIVÉE', 'waiting_box': 'En attente du prochain colis…',
    'not_arrived': 'La boîte n’est pas arrivée.', 'not_decoded': 'Le contenu ne peut pas être lu en texte.', 'invalid_color': 'Code couleur non valide.',
    'waiting_arrival': 'La boîte est encore en chemin…', 'original_unknown': 'Contenu non enregistré.',
    'outcome_intact': 'Message intact', 'outcome_corrupted': 'Message modifié', 'outcome_lost': 'Boîte perdue',
    'outcome_failure': 'Panne avant le départ', 'outcome_encoding_error': 'Préparation impossible',
    'departure': 'DÉPART', 'weather': 'FURIE / RÉSEAU', 'destination': 'ARRIVÉE',
    'next_box': 'VOIR UN AUTRE COLIS', 'excerpt': 'Extrait : les données complètes sont dans les détails.',
    'trial_graph': 'Part des essais normaux à chaque tour :', 'intact_short': 'Intacts', 'damaged_short': 'Abîmés',
    'lost_short': 'Perdus', 'other_short': 'Pannes / erreurs', 'gen_axis': 'Tours',
    'box_totals': 'Ce tour : {sent} envoyés sur {attempts} essais · {intact} intacts · {damaged} abîmés · {lost} perdus · {other} pannes/erreurs',
    'graph_help': 'Pourcentages calculés sur les essais normaux de tous les modèles, pas sur les essais extrêmes.',
    'scroll_hint': 'Défile vers le bas pour voir le graphique.',
    'nested_note': 'Petite boîte = nouvelle idée issue des parents enregistrés (image).',
    'bit_note': '{count} bits modifiés', 'attack_note': 'Corruption enregistrée',
    'limit': 'La vitesse dessinée est illustrative ; les événements et les messages viennent de la simulation.',
    'simple_explain': 'Un modèle est une façon de protéger une boîte. On met un vrai petit message dans chaque boîte et on regarde ce qui arrive.',
})
TEXT['en'].update({
    'title': 'RawHostileSelect 4 · The package journey',
    'subtitle': 'A little adventure to see how messages travel',
    'population': 'Box designs', 'generations': 'Rounds', 'generation': 'Round',
    'seed': 'Magic number', 'arena': 'The journey of the boxes',
    'metaphor': 'Departure → Fury and the troubled path → arrival',
    'progress': 'What happens to the boxes?',
    'legend': 'Green: intact   Pink: damaged   Grey: lost   Orange: failure',
    'sample': 'A few recorded trials are animated. Each box is a tested message.',
    'seed_help': 'Magic number = seed: the same number and settings repeat the same random draws.',
    'population_help': 'Designs are ways to protect boxes. Each round tests every design; later rounds inherit selected designs.',
    'message_type': 'Message in the boxes', 'mixed': 'A mixture', 'phrase': 'A sentence', 'color': 'A color', 'code': 'A little code', 'mode_note': '(type and language set at start)',
    'start_box': 'AT DEPARTURE', 'arrival_box': 'AT ARRIVAL', 'waiting_box': 'Waiting for the next package…',
    'not_arrived': 'The box did not arrive.', 'not_decoded': 'The contents cannot be read as text.', 'invalid_color': 'Invalid color code.',
    'waiting_arrival': 'The box is still on its way…', 'original_unknown': 'Contents were not recorded.',
    'outcome_intact': 'Message intact', 'outcome_corrupted': 'Message changed', 'outcome_lost': 'Box lost',
    'outcome_failure': 'Failure before departure', 'outcome_encoding_error': 'Could not prepare the box',
    'departure': 'DEPARTURE', 'weather': 'FURY / NETWORK', 'destination': 'ARRIVAL',
    'next_box': 'SEE ANOTHER BOX', 'excerpt': 'Excerpt: full data is available in the details.',
    'trial_graph': 'Share of normal trials in each round:', 'intact_short': 'Intact', 'damaged_short': 'Damaged',
    'lost_short': 'Lost', 'other_short': 'Failures / errors', 'gen_axis': 'Rounds',
    'box_totals': 'This round: {sent} sent in {attempts} trials · {intact} intact · {damaged} damaged · {lost} lost · {other} failures/errors',
    'graph_help': 'Percentages use normal trials from all designs, not separate extreme trials.',
    'scroll_hint': 'Scroll down to see the graph.',
    'nested_note': 'Small box = a new idea from recorded parents (metaphor).',
    'bit_note': '{count} changed bits', 'attack_note': 'Corruption recorded',
    'limit': 'The drawn speed is illustrative; the events and messages come from the simulation.',
    'simple_explain': 'A design is a way to protect a box. We put a real little message in each box and see what happens.',
})

TEXT['fr'].update({
    'messages_history': 'HISTORIQUE DES COLIS',
    'history_title': 'Historique des colis — du départ à l’arrivée',
    'history_empty': 'Il n’y a pas encore de colis à montrer. Lance un test, puis reviens ici.',
    'history_intro': 'Choisis un tour, puis un colis. Les essais extrêmes ont un chemin plus difficile. L’historique reste après le test tant que le programme est ouvert ; RECOMMENCER le vide.',
    'history_refresh': 'ACTUALISER', 'history_round': 'Tour à regarder',
    'history_count': '{count} colis enregistrés dans ce tour.',
    'history_kind': 'Contenu', 'history_trial': 'Essai',
    'history_departure': 'Départ :', 'history_arrival': 'Arrivée :',
    'history_choose': 'Choisis un colis dans la liste pour lire son message.',
    'history_binary': 'Données binaires', 'history_empty_message': '(message vide)',
})
TEXT['en'].update({
    'messages_history': 'PACKAGE HISTORY',
    'history_title': 'Package history — from departure to arrival',
    'history_empty': 'There are no packages to show yet. Start a test, then come back here.',
    'history_intro': 'Choose a round, then a package. Extreme trials use a harder path. History stays after the test while the app is open; RESTART clears it.',
    'history_refresh': 'REFRESH', 'history_round': 'Round to view',
    'history_count': '{count} packages recorded in this round.',
    'history_kind': 'Contents', 'history_trial': 'Trial',
    'history_departure': 'Departure:', 'history_arrival': 'Arrival:',
    'history_choose': 'Choose a package in the list to read its message.',
    'history_binary': 'Binary data', 'history_empty_message': '(empty message)',
})

OP_INFO = {
    'IDENTITY': ('Conserve les octets tels quels.', 'Leaves the bytes unchanged.'),
    'SCRAMBLE': ('Applique un XOR avec un masque pseudo-aléatoire déterminé par la graine.', 'Applies XOR with a seed-derived pseudorandom mask.'),
    'INTERLEAVE': ('Réordonne les octets en colonnes et peut ajouter des zéros.', 'Reorders bytes in columns and may add zero padding.'),
    'ADD_PARITY': ('Ajoute la somme des octets modulo 256 ; elle est vérifiée au décodage.', 'Appends the byte sum modulo 256; it is checked during decoding.'),
    'CHECKSUM': ('Ajoute une somme modulo 256 ou quatre octets de BLAKE2b selon le paramètre ; vérifiée au décodage.', 'Appends a modulo-256 sum or four BLAKE2b bytes depending on the parameter; checked during decoding.'),
    'REPEAT': ('Répète les octets ; le décodage vote bit par bit entre les copies.', 'Repeats the bytes; decoding votes bit by bit among the copies.'),
    'FRAGMENT': ("Marqueur sans effet sur les octets dans ce modèle ; aucune fragmentation réelle.", 'Marker with no effect on bytes in this model; no actual fragmentation.'),
    'PAD': ('Ajoute un octet de remplissage.', 'Appends one padding byte.'),
    'XOR_CONST': ('Applique un XOR à chaque octet avec une constante.', 'XORs each byte with a constant.'),
    'REVERSE': ("Inverse l'ordre des octets.", 'Reverses byte order.'),
}

# Soft pastel surfaces use dark ink for readable text. Parcel colors remain
# tied to the recorded outcomes, not to the decorative theme.
PAPER = '#fff8fc'
INK = '#49374d'
MUTED = '#6c566f'
SOFT_CARD = '#f5e8f5'
PLOT_BG = '#fffafd'
PLOT_COLORS = ('#358565', '#b84873', '#617595', '#a7652b')


class ArenaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = max(320, min(1380, screen_w - 60)), max(300, min(900, screen_h - 100))
        self.geometry(f"{width}x{height}")
        self.minsize(min(900, width), min(650, height))
        self.lang = tk.StringVar(value="fr")
        self.population = tk.StringVar(value="12")
        self.generations = tk.StringVar(value="20")
        self.difficulty = tk.StringVar(value="medium")
        self.seed = tk.StringVar(value="42")
        self.speed = tk.StringVar(value="slow")
        self.message_kind = tk.StringVar(value="mixed")
        self.status = tk.StringVar()
        self.engine = None
        self.history = []
        self.replay_data = None
        self.replay_index = 0
        self.running = False
        self.busy = False
        self.token = 0
        self.results = queue.Queue()
        self.animation_token = 0
        self.current = None
        self.box_events = []
        self.box_index = -1
        self._build()
        self.bind_all('<MouseWheel>', self._scroll_left, add='+')
        self.status.set(self.t("ready"))
        self.after(80, self._poll)

    def t(self, key):
        return TEXT[self.lang.get()].get(key, key)

    def _rounded_buttons(self, style):
        """Nine-slice rounded button images, made with Tk only."""
        if not hasattr(self, '_button_images'):
            images = []
            for fill in ('#edd6ed', '#f8d9e8', '#e4c5e3'):
                image = tk.PhotoImage(master=self, width=36, height=36)
                for y in range(36):
                    dy = max(0, 11-y, y-24)
                    inset = 12 - int(max(0, 144-dy*dy) ** .5) if dy else 0
                    image.put(fill, to=(inset, y, 36-inset, y+1))
                images.append(image)
            self._button_images = images
        if 'PastelRounded.button' not in style.element_names():
            normal, active, pressed = self._button_images
            style.element_create('PastelRounded.button', 'image', normal,
                                 ('pressed', pressed), ('active', active),
                                 border=(12, 12, 12, 12), sticky='nsew')
        style.layout('TButton', [('PastelRounded.button', {'sticky': 'nsew', 'children': [
            ('Button.padding', {'sticky': 'nsew', 'children': [('Button.label', {'sticky': 'nsew'})]})]})])

    def _build(self):
        for child in self.winfo_children():
            child.destroy()
        self.title(self.t("title"))
        self.configure(bg=PAPER)
        style = ttk.Style(self)
        style.theme_use("clam")
        self._rounded_buttons(style)
        style.configure("TFrame", background=PAPER)
        style.configure("TLabel", background=PAPER, foreground=INK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"), foreground="#784967")
        style.configure("TButton", padding=(12, 7), font=("Segoe UI", 9, "bold"), foreground=INK, borderwidth=0)
        style.map("TButton", foreground=[("disabled", "#988998")])
        style.configure("TLabelframe", background=PAPER, foreground=INK, bordercolor='#ead9e9')
        style.configure("TLabelframe.Label", background=PAPER, foreground="#784967", font=("Segoe UI", 10, "bold"))
        style.configure('TEntry', fieldbackground='#ffffff', foreground=INK, bordercolor='#d9c6d9')
        style.configure('TCombobox', fieldbackground='#ffffff', background='#f2e3f0', foreground=INK, arrowcolor=INK)
        style.map('TCombobox', fieldbackground=[('readonly', '#fffefe')], foreground=[('readonly', INK)])
        style.configure('TNotebook', background=PAPER, borderwidth=0)
        style.configure('TNotebook.Tab', background='#f2e3f0', foreground=INK, padding=(10, 5))
        style.map('TNotebook.Tab', background=[('selected', '#e9d2e9')])
        self.option_add('*TCombobox*Listbox.background', '#fffafd')
        self.option_add('*TCombobox*Listbox.foreground', INK)
        header = ttk.Frame(self, padding=(15, 10)); header.pack(fill="x")
        ttk.Label(header, text=self.t("title"), style="Title.TLabel").pack(side="left")
        ttk.Combobox(header, textvariable=self.lang, values=("fr", "en"), state="readonly", width=4).pack(side="right")
        header.winfo_children()[-1].bind("<<ComboboxSelected>>", lambda _e: self._rebuild())
        ttk.Label(self, text=self.t("subtitle")).pack(anchor="w", padx=18)
        # Canvas-backed card gives the main summary actual rounded corners,
        # while the inner frame keeps its text accessible and selectable.
        summary_card = tk.Canvas(self, bg=PAPER, highlightthickness=0, height=68)
        summary_card.pack(fill='x', padx=14, pady=(6, 0))
        summary = tk.Frame(summary_card, bg=SOFT_CARD, padx=8, pady=3)
        summary_window = summary_card.create_window(12, 7, window=summary, anchor='nw')
        self.simple_text = tk.StringVar()
        tk.Label(summary, text=self.t('simple_title'), bg=SOFT_CARD, fg='#784967', font=('Segoe UI', 10, 'bold'), anchor='w').pack(fill='x')
        simple_label = tk.Label(summary, textvariable=self.simple_text, bg=SOFT_CARD, fg=INK, font=('Segoe UI', 9), justify='left', anchor='w')
        simple_label.pack(fill='x')
        def resize_summary(event):
            simple_label.configure(wraplength=max(200, event.width - 18))
            desired = event.height + 14
            if int(summary_card.cget('height')) != desired: summary_card.configure(height=desired)
        def paint_summary(event):
            summary_card.itemconfigure(summary_window, width=max(1, event.width-24))
            summary_card.delete('card_background')
            self.rounded(summary_card, 0, 0, event.width, event.height, 16,
                         fill=SOFT_CARD, outline='', tags=('card_background',))
            summary_card.tag_lower('card_background')
        summary.bind('<Configure>', resize_summary)
        summary_card.bind('<Configure>', paint_summary)
        self.update_simple_summary()
        settings = ttk.LabelFrame(self, text=self.t("settings"), padding=8); settings.pack(fill="x", padx=14, pady=7)
        for key, var, width in (("population", self.population, 5), ("generations", self.generations, 5), ("seed", self.seed, 8)):
            ttk.Label(settings, text=self.t(key)).pack(side="left", padx=(4, 3))
            ttk.Entry(settings, textvariable=var, width=width).pack(side="left", padx=(0, 7))
        ttk.Label(settings, text=self.t("difficulty")).pack(side="left")
        difficulty = ttk.Combobox(settings, values=tuple(self.t(x) for x in ('light', 'medium', 'extreme')), state="readonly", width=8)
        difficulty.current(('light', 'medium', 'extreme').index(self.difficulty.get())); difficulty.pack(side="left", padx=5)
        difficulty.bind("<<ComboboxSelected>>", lambda _e: self.difficulty.set(('light', 'medium', 'extreme')[difficulty.current()]))
        ttk.Label(settings, text=self.t("speed")).pack(side="left")
        speed = ttk.Combobox(settings, values=(self.t("slow"), self.t("fast")), state="readonly", width=20)
        speed.current(0 if self.speed.get() == "slow" else 1); speed.pack(side="left", padx=5)
        speed.bind("<<ComboboxSelected>>", lambda _e: self.speed.set("slow" if speed.current() == 0 else "fast"))
        message_row = ttk.Frame(self, padding=(18, 0)); message_row.pack(fill='x')
        ttk.Label(message_row, text=self.t('message_type')).pack(side='left', padx=(0, 6))
        kinds = ('mixed', 'phrase', 'color', 'code')
        chooser = ttk.Combobox(message_row, values=tuple(self.t(k) for k in kinds), state='readonly', width=15)
        chooser.current(kinds.index(self.message_kind.get())); chooser.pack(side='left')
        chooser.bind('<<ComboboxSelected>>', lambda _e: self.message_kind.set(kinds[chooser.current()]))
        ttk.Label(message_row, text=self.t('mode_note'), foreground=MUTED).pack(side='left', padx=6)
        ttk.Label(self, text=self.t('seed_help'), foreground=MUTED, wraplength=1300).pack(anchor='w', padx=18)
        ttk.Label(self, text=self.t('population_help'), foreground=MUTED, wraplength=1300).pack(anchor='w', padx=18)
        controls = ttk.Frame(self, padding=(14, 0)); controls.pack(fill="x")
        for label, cmd in (("start", self.start), ("pause", self.pause), ("next", self.step), ("reset", self.reset)):
            button = ttk.Button(controls, text=self.t(label), command=cmd); button.pack(side="left", padx=2, pady=2)
            if label == 'pause': self.pause_button = button
        file_controls = ttk.Frame(self, padding=(14, 0)); file_controls.pack(fill="x")
        for label, cmd in (("messages_history", self.open_messages_history), ("export", self.export_json), ("csv", self.export_csv), ("replay", self.open_replay)):
            ttk.Button(file_controls, text=self.t(label), command=cmd).pack(side="left", padx=2, pady=2)
        self._update_pause_button()
        ttk.Label(self, textvariable=self.status).pack(anchor="w", padx=18, pady=3)
        main = ttk.Panedwindow(self, orient="horizontal"); main.pack(fill="both", expand=True, padx=14, pady=5)
        left = ttk.Frame(main); right = ttk.Frame(main); main.add(left, weight=3); main.add(right, weight=2)
        ttk.Label(left, text=self.t('scroll_hint'), foreground=MUTED).pack(anchor='w')
        scroll_host = ttk.Frame(left); scroll_host.pack(fill='both', expand=True)
        self.left_scroll = tk.Canvas(scroll_host, bg=PAPER, highlightthickness=0)
        left_bar = ttk.Scrollbar(scroll_host, orient='vertical', command=self.left_scroll.yview)
        self.left_scroll.configure(yscrollcommand=left_bar.set)
        left_bar.pack(side='right', fill='y'); self.left_scroll.pack(side='left', fill='both', expand=True)
        left_content = ttk.Frame(self.left_scroll)
        left_window = self.left_scroll.create_window((0, 0), window=left_content, anchor='nw')
        left_content.bind('<Configure>', lambda _e: self.left_scroll.configure(scrollregion=self.left_scroll.bbox('all')))
        self.left_scroll.bind('<Configure>', lambda event: self.left_scroll.itemconfigure(left_window, width=event.width))
        arena = ttk.LabelFrame(left_content, text=self.t("arena"), padding=6); arena.pack(fill="x")
        ttk.Label(arena, text=self.t("metaphor"), wraplength=650).pack(anchor="w")
        self.canvas = tk.Canvas(arena, height=150, bg="#f5e9fa", highlightthickness=0); self.canvas.pack(fill="x", pady=4)
        self.canvas.bind('<Configure>', lambda _e: self.draw_arena(self.displayed_event, self.displayed_fraction) if hasattr(self, 'displayed_event') else None)
        package_row = ttk.Frame(arena); package_row.pack(fill='x')
        self.message_before = tk.StringVar(value=self.t('waiting_box'))
        self.message_after = tk.StringVar(value=self.t('waiting_arrival'))
        self.message_swatches = []
        for title, var, bg in ((self.t('start_box'), self.message_before, '#cdeedb'), (self.t('arrival_box'), self.message_after, '#ffdce8')):
            card = tk.Frame(package_row, bg=bg, padx=8, pady=5); card.pack(side='left', fill='both', expand=True, padx=3)
            head = tk.Frame(card, bg=bg); head.pack(fill='x')
            tk.Label(head, text=title, bg=bg, fg='#4b3750', font=('Segoe UI', 9, 'bold'), anchor='w').pack(side='left')
            swatch = tk.Label(head, text='   ', bg=bg, width=3, relief='flat'); swatch.pack(side='right')
            self.message_swatches.append((swatch, bg))
            label = tk.Label(card, textvariable=var, bg=bg, fg='#332c42', justify='left', anchor='nw', wraplength=280, font=('Segoe UI', 10))
            label.pack(fill='both', expand=True)
            card.bind('<Configure>', lambda event, widget=label: widget.configure(wraplength=max(100, event.width-18)))
        ttk.Button(arena, text=self.t('next_box'), command=self.next_box).pack(anchor='e', pady=2)
        ttk.Label(arena, text=self.t("legend"), foreground=MUTED).pack(anchor="w")
        ttk.Label(arena, text=self.t("sample"), foreground=MUTED, wraplength=650).pack(anchor="w")
        graph = ttk.LabelFrame(left_content, text=self.t("progress"), padding=6); graph.pack(fill="x", pady=(8, 0))
        self.chart_counts = tk.StringVar(value=self.t('no_data'))
        ttk.Label(graph, textvariable=self.chart_counts, wraplength=650).pack(anchor='w')
        self.graph = tk.Canvas(graph, height=130, bg=PLOT_BG, highlightthickness=0); self.graph.pack(fill="x")
        key = ttk.Frame(graph); key.pack(anchor="w")
        for i, (color, label) in enumerate(zip(PLOT_COLORS, (self.t('intact_short'), self.t('damaged_short'), self.t('lost_short'), self.t('other_short')))):
            entry = ttk.Frame(key); entry.grid(row=i // 2, column=i % 2, sticky='w', padx=(0, 10))
            ttk.Label(entry, text='●', foreground=color).pack(side='left'); ttk.Label(entry, text=' ' + label).pack(side='left')
        ttk.Label(graph, text=self.t('graph_help'), foreground=MUTED, wraplength=650).pack(anchor='w')
        self.graph.bind("<Configure>", lambda _e: self.draw_graph())
        panel = ttk.LabelFrame(right, text=self.t("metrics"), padding=7); panel.pack(fill="x")
        self.metric_text = tk.Text(panel, height=5, wrap="word", bg=SOFT_CARD, fg=INK, relief="flat", font=("Segoe UI", 10)); self.metric_text.pack(fill="x"); self.metric_text.config(state="disabled")
        ttk.Label(panel, text=self.t("measure_help"), wraplength=450, foreground=MUTED).pack(anchor="w", pady=4)
        people = ttk.LabelFrame(right, text=self.t("individuals"), padding=6); people.pack(fill="both", expand=True, pady=6)
        self.listbox = tk.Listbox(people, bg=SOFT_CARD, fg=INK, selectbackground="#dfbee2", selectforeground=INK, relief="flat", height=7, font=("Consolas", 10)); self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(people, command=self.listbox.yview); scroll.pack(side="right", fill="y"); self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.bind("<Double-Button-1>", lambda _e: self.inspect())
        actions = ttk.Frame(right); actions.pack(fill='x')
        ttk.Button(actions, text=self.t("inspect"), command=self.inspect).pack(side='right')
        ttk.Button(actions, text=self.t("dashboard"), command=self.dashboard).pack(side='right', padx=4)
        log = ttk.LabelFrame(right, text=self.t("narrative"), padding=6); log.pack(fill="both", expand=True, pady=6)
        self.log = tk.Text(log, height=7, bg=SOFT_CARD, fg=INK, relief="flat", wrap="word", font=("Segoe UI", 9)); self.log.pack(side="left", fill="both", expand=True)
        s = ttk.Scrollbar(log, command=self.log.yview); s.pack(side="right", fill="y"); self.log.config(yscrollcommand=s.set, state="disabled")
        self.draw_arena()
        if self.current: self.show_snapshot(self.current, animate=False)
        self.render_log()

    def _rebuild(self):
        displayed = getattr(self, 'displayed_event', None)
        fraction = getattr(self, 'displayed_fraction', 0)
        self.animation_token += 1
        self._build()
        if displayed: self.draw_arena(displayed, fraction)
        self.status.set(self.t('working') if self.busy else (self.t('paused') if self.current else self.t('ready')))

    def _scroll_left(self, event):
        widget = event.widget
        while widget is not None:
            if widget is getattr(self, 'left_scroll', None):
                self.left_scroll.yview_scroll(-1 if event.delta > 0 else 1, 'units')
                return 'break'
            widget = getattr(widget, 'master', None)

    def _update_pause_button(self):
        if hasattr(self, 'pause_button'):
            self.pause_button.configure(text=self.t('pause' if self.running else 'resume'))

    def make_engine(self):
        try:
            population, generations, seed = int(self.population.get()), int(self.generations.get()), int(self.seed.get())
            if not 2 <= population <= 100 or not 1 <= generations <= 1000: raise ValueError()
            self.engine = ArenaEngine(ArenaConfig(population=population, generations=generations, difficulty=self.difficulty.get(), seed=seed,
                                                  message_kind=self.message_kind.get(), message_language=self.lang.get()))
            return True
        except (ValueError, TypeError) as exc:
            messagebox.showerror(self.t("error"), self.t("invalid") + "\n" + str(exc)); return False

    def start(self):
        if self.running: return
        if not self.replay_data and self.engine is None and not self.make_engine(): return
        self.running = True
        self._update_pause_button()
        if not self.busy: self._request_step()

    def pause(self):
        if self.running:
            self.running = False; self.status.set(self.t("paused"))
            self._update_pause_button()
        else:
            self.start()

    def step(self):
        self.running = False
        self._update_pause_button()
        if self.busy: return
        if not self.replay_data and self.engine is None and not self.make_engine(): return
        self._request_step()

    def _request_step(self):
        if self.busy: return
        if self.replay_data:
            gens = self.replay_data["generations"]
            if self.replay_index >= len(gens): self.running = False; self._update_pause_button(); self.status.set(self.t("complete")); return
            self.current = gens[self.replay_index]; self.replay_index += 1
            self.history = gens[:self.replay_index]
            self.show_snapshot(self.current); self.render_log()
            self.status.set(f"{self.t('replaymode')} · {self.t('generation')} {self.current['generation']}")
            if self.running: self.after(5000 if self.speed.get() == "slow" else 30, self._continue)
            return
        self.busy = True; self.status.set(self.t("working")); token, engine = self.token, self.engine
        def work():
            try: self.results.put((token, engine.step(), None))
            except Exception as exc: self.results.put((token, None, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _continue(self):
        if self.running and not self.busy: self._request_step()

    def _poll(self):
        try:
            while True:
                token, snapshot, error = self.results.get_nowait()
                if token != self.token: continue
                self.busy = False
                if error:
                    self.running = False; self._update_pause_button(); self.status.set(self.t("error")); messagebox.showerror(self.t("error"), error)
                elif snapshot is None:
                    self.running = False; self._update_pause_button(); self.status.set(self.t("complete"))
                else:
                    self.current = snapshot; self.history = list(self.engine.history)
                    self.show_snapshot(snapshot); self.render_log()
                    self.status.set(f"{self.t('live')} · {self.t('generation')} {snapshot['generation']}")
                    if self.running: self.after(5000 if self.speed.get() == "slow" else 20, self._continue)
        except queue.Empty: pass
        self.after(80, self._poll)

    def reset(self):
        self.running = False; self.busy = False; self.token += 1; self.animation_token += 1
        self.engine = None; self.history = []; self.current = None; self.replay_data = None; self.replay_index = 0
        self.box_events = []; self.box_index = -1
        self.status.set(self.t("ready")); self._build()

    def put_text(self, widget, value):
        widget.config(state="normal"); widget.delete("1.0", "end"); widget.insert("end", value); widget.config(state="disabled")

    def update_simple_summary(self):
        lines = [self.t('simple_explain')]
        if not self.current:
            lines.append(self.t('simple_wait'))
        else:
            people = self.current.get('individuals', [])
            scored = [p for p in people if isinstance(p.get('fitness', {}).get('scalar'), (int, float))]
            best = max(scored, key=lambda p: p['fitness']['scalar']) if scored else None
            metrics = best.get('stats', {}) if best else {}
            required = ('attempts', 'received', 'intact', 'lost')
            if all(isinstance(metrics.get(k), (int, float)) for k in required) and metrics['attempts'] > 0:
                attempts, received, intact, lost = (metrics[k] for k in required)
                lines.append(self.t('simple_result').format(id=best.get('id', '—'), attempts=attempts, received=received, intact=intact, damaged=received-intact, lost=lost, other=attempts-received-lost, delivery=received/attempts, integrity=intact/attempts))
                lines.append(self.t('simple_best'))
            else:
                lines.append(self.t('simple_missing'))
        self.simple_text.set('\n'.join(lines))

    def show_snapshot(self, snap, animate=True):
        self.update_simple_summary()
        history_window = getattr(self, '_messages_history_window', None)
        if history_window is not None and history_window.winfo_exists():
            history_window.update_history_rounds()
        self.box_events = [e for e in snap.get('events', []) if e.get('type') == 'transmission' and e.get('scenario') == 'baseline']
        self.box_index = -1
        summary = snap.get("summary", {})
        people = snap.get("individuals", [])
        best = max(people, key=lambda p: p.get("fitness", {}).get("scalar", 0), default=None)
        fit = best.get("fitness", {}) if best else {}
        lines = [f"{self.t('generation')} {snap.get('generation', '?')} · {self.t('best')}: {summary.get('best', 0):.3f} · {self.t('average')}: {summary.get('average', 0):.3f}",
                 f"{self.t('front')}: {summary.get('front0', 0)} · {self.t('diversity')}: {summary.get('diversity', 0):.3f}"]
        if best:
            lines.append(f"{self.t('id')} {best['id']} — " + " · ".join(f"{self.t(k)} {fit.get(k, 0):.1%}" for k in ('delivery', 'integrity', 'efficiency', 'resilience')))
        self.put_text(self.metric_text, "\n".join(lines))
        self.listbox.delete(0, 'end')
        for p in people:
            f = p.get("fitness", {}); self.listbox.insert('end', f"{p['id']}  |  {f.get('scalar', 0):.3f}  |  {str(p.get('tree', ''))[:45]}")
        trials = [e for e in snap.get('events', []) if e.get('type') == 'transmission' and e.get('scenario') == 'baseline']
        if trials:
            count = lambda *k: sum(e.get('outcome') in k for e in trials)
            sent = (sum(e.get('sent_bytes', 0) > 0 for e in trials)
                    if all('sent_bytes' in e for e in trials) else self.t('unavailable'))
            self.chart_counts.set(self.t('box_totals').format(sent=sent, attempts=len(trials), intact=count('intact'), damaged=count('corrupted'), lost=count('lost'), other=count('failure', 'encoding_error')))
        else: self.chart_counts.set(self.t('no_data'))
        self.draw_graph()
        if animate:
            transmissions = [e for e in snap.get('events', []) if e.get('type') == 'transmission']
            self.animate_events(transmissions)

    def render_log(self):
        out = []
        for i, snap in enumerate(self.history):
            s = snap.get('summary', {}); events = snap.get('events', [])
            out.append(self.t('gen_log').format(g=snap.get('generation', i), best=s.get('best', 0), avg=s.get('average', 0), front=s.get('front0', 0), div=s.get('diversity', 0)))
            if i:
                delta = s.get('best', 0) - self.history[i-1].get('summary', {}).get('best', 0)
                out.append(self.t('delta').format(delta=delta))
            counts = {x: sum(e.get('type') == x for e in events) for x in ('transmission', 'mutation', 'crossover', 'selection', 'elimination')}
            out.append(self.t('events').format(trans=counts['transmission'], mut=counts['mutation'], cross=counts['crossover'], sel=counts['selection'], elim=counts['elimination']))
            people = snap.get('individuals', [])
            if people:
                best = max(people, key=lambda p: p.get('fitness', {}).get('scalar', 0))
                f = best.get('fitness', {})
                out.append(f"{self.t('id')} {best.get('id')} — " + ' · '.join(f"{self.t(k)} {f.get(k, 0):.1%}" for k in ('delivery', 'integrity', 'resilience')))
                observation = next((e for e in events if e.get('type') == 'transmission' and e.get('individual_id') == best.get('id')), None)
                if observation: out.append(self.t('observation') + ': ' + self.describe_event(observation))
            out.append("")
        if self.history:
            first, last = self.history[0], self.history[-1]
            fs, ls = first.get('summary', {}), last.get('summary', {})
            start, end = fs.get('best', 0), ls.get('best', 0)
            out.extend([self.t('report') + ':', self.t('report_progress').format(first=first.get('generation', 0), last=last.get('generation', 0), start=start, end=end, delta=end-start)])
            people = last.get('individuals', [])
            if people:
                best = max(people, key=lambda p: p.get('fitness', {}).get('scalar', 0)); fit = best.get('fitness', {})
                stats = [p.get('stats', {}) for p in people]
                out.append(self.t('report_result').format(id=best.get('id'), delivery=fit.get('delivery', 0), integrity=fit.get('integrity', 0), resilience=fit.get('resilience', 0), lost=sum(s.get('lost', 0) for s in stats), failures=sum(s.get('failures', 0) for s in stats), bytes=sum(s.get('sent_bytes', 0) for s in stats)))
                if fit.get('integrity') == 0: out.append(self.t('report_failure'))
            out.append(self.t('summary_end'))
        self.put_text(self.log, '\n'.join(out)); self.log.see('end')

    def draw_arena(self, event=None, fraction=0):
        if not hasattr(self, 'canvas'): return
        self.displayed_event, self.displayed_fraction = event, fraction
        c = self.canvas; c.delete('all'); w = c.winfo_width() if c.winfo_width() > 5 else 340; h = c.winfo_height() if c.winfo_height() > 5 else 150; y = h * .61
        c.create_line(65, y+30, w-65, y+30, fill='#d6c5df', width=10, capstyle='round')
        c.create_line(65, y+30, w-65, y+30, fill='#fffafc', width=2, dash=(8, 7))
        # The three stations are pictograms, not physical simulations.
        self.rounded(c, 14, y-32, 94, y+24, 14, fill='#c7eadc', outline='#82bea4', width=2)
        c.create_text(54, y-8, text='B2', font=('Segoe UI', 12, 'bold'), fill='#496c5c')
        self.rounded(c, w-94, y-32, w-14, y+24, 14, fill='#ffe0e5', outline='#e8a6b1', width=2)
        c.create_text(w-54, y-8, text='♡', font=('Segoe UI', 18, 'bold'), fill='#bc7482')
        # A friendly cloud stands for the network; lightning appears only
        # when the engine recorded changed bits or adversarial corruption.
        c.create_oval(w/2-35, y-44, w/2+35, y+12, fill='#cfc5ed', outline='#aa9ad2', width=2)
        c.create_oval(w/2-47, y-28, w/2-5, y+10, fill='#cfc5ed', outline='')
        c.create_oval(w/2+5, y-29, w/2+47, y+10, fill='#cfc5ed', outline='')
        c.create_oval(w/2-15, y-19, w/2-10, y-14, fill='#544b70', outline='')
        c.create_oval(w/2+10, y-19, w/2+15, y-14, fill='#544b70', outline='')
        c.create_arc(w/2-9, y-12, w/2+9, y-2, start=190, extent=160, style='arc', outline='#544b70', width=2)
        for x, label in ((54, self.t('departure')), (w/2, self.t('weather')), (w-54, self.t('destination'))):
            c.create_text(x, h-22, text=label, fill='#64546b', font=('Segoe UI', 8, 'bold'))
        if event:
            outcome = event.get('outcome', 'failure')
            arrived = fraction >= .95
            color = ({'intact':'#a7dfba','corrupted':'#ffa9bf','lost':'#bcc6d8','failure':'#ffcf95', 'encoding_error':'#ffcf95'}.get(outcome, '#ffcf95') if arrived else '#ffe0a7')
            x = 100 + fraction * max(0, w - 200)
            if outcome in ('failure', 'encoding_error'): x = 104
            if not (outcome == 'lost' and fraction > .68):
                self.draw_box(c, x, y, color)
            changed = event.get('changed_bit_count', event.get('bit_flips', 0)) or 0
            if event.get('adversarial') or changed:
                c.create_text(w/2+49, y-47, text='✦', fill='#eb7498', font=('Segoe UI', 20, 'bold'))
            label = self.t('outcome_' + outcome) if arrived or outcome in ('failure', 'encoding_error') else self.t('waiting_arrival')
            c.create_text(w/2, 18, text=f"{self.t('id')} {event.get('individual_id', '?')}  ·  {label}", fill='#58475e', font=('Segoe UI', 10, 'bold'), width=w-15)
            detail = self.t('attack_note') if event.get('adversarial') else self.t('bit_note').format(count=changed)
            if event.get('received_hex') is not None and (changed or event.get('adversarial')):
                c.create_text(w/2, 37, text=detail, fill='#8c5678', font=('Segoe UI', 8), width=w-20)
            self.update_message_cards(event, arrived)
        else:
            c.create_text(w/2, 18, text=self.t('waiting_box'), fill='#58475e', font=('Segoe UI', 10, 'bold'), width=w-15)

    @staticmethod
    def rounded(canvas, x1, y1, x2, y2, radius, **kwargs):
        r = min(radius, abs(x2-x1)/2, abs(y2-y1)/2)
        return canvas.create_polygon(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1, smooth=True, **kwargs)

    def draw_box(self, canvas, x, y, fill):
        self.rounded(canvas, x-23, y-21, x+23, y+21, 9, fill=fill, outline='#b79578', width=2)
        canvas.create_line(x, y-20, x, y+19, fill='#e5bc94', width=4)
        canvas.create_line(x-22, y-5, x+22, y-5, fill='#e5bc94', width=3)
        canvas.create_oval(x-12, y+3, x-9, y+6, fill='#615060', outline='')
        canvas.create_oval(x+9, y+3, x+12, y+6, fill='#615060', outline='')
        canvas.create_arc(x-6, y+6, x+6, y+13, start=190, extent=160, style='arc', outline='#615060')

    @staticmethod
    def escape_message(value):
        # Preserve accents; show control characters rather than hiding them.
        return ''.join(ch if ch.isprintable() else f'\\u{ord(ch):04x}' for ch in value)

    def message_preview(self, event, field):
        hex_key = 'original_hex' if field == 'original' else 'decoded_hex'
        data_hex = event.get(hex_key)
        if data_hex is None:
            return self.t('original_unknown') if field == 'original' else self.t('not_arrived')
        try:
            data = bytes.fromhex(data_hex)
        except (TypeError, ValueError):
            return self.t('original_unknown')
        try:
            shown = self.escape_message(data.decode('utf-8', errors='strict'))
        except UnicodeDecodeError:
            suffix = '\n' + self.t('excerpt') if len(data) > 64 else ''
            return self.t('not_decoded') + '\nHEX: ' + data[:64].hex(' ') + suffix
        if len(shown) > 180: return shown[:180] + '…\n' + self.t('excerpt')
        return shown if shown else '∅'

    def update_message_cards(self, event, arrived):
        if not hasattr(self, 'message_before'): return
        self.message_before.set(self.message_preview(event, 'original'))
        self.message_after.set(self.message_preview(event, 'decoded') if arrived else self.t('waiting_arrival'))
        for (swatch, default), field, show in zip(self.message_swatches, ('original_hex', 'decoded_hex'), (True, arrived)):
            color = None
            if show and event.get('message_kind') == 'color' and event.get(field) is not None:
                try:
                    candidate = bytes.fromhex(event[field]).decode('ascii')
                    if re.fullmatch(r'#[0-9a-fA-F]{6}', candidate): color = candidate
                except (ValueError, TypeError, UnicodeDecodeError):
                    pass
            swatch.configure(bg=color or default, relief='solid' if color else 'flat', borderwidth=1 if color else 0)
        if arrived and event.get('message_kind') == 'color' and event.get('decoded_hex') is not None:
            try:
                candidate = bytes.fromhex(event['decoded_hex']).decode('ascii')
                valid = bool(re.fullmatch(r'#[0-9a-fA-F]{6}', candidate))
            except (ValueError, TypeError, UnicodeDecodeError):
                valid = False
            if not valid: self.message_after.set(self.message_after.get() + '\n' + self.t('invalid_color'))

    def describe_event(self, event):
        latency = event.get('latency')
        bits = self.t('unavailable') if event.get('adversarial') or event.get('received_hex') is None else event.get('bit_flips', 0)
        return self.t('transmission').format(id=event.get('individual_id', '?'), scenario=self.t(event.get('scenario', 'baseline')), outcome=self.t(event.get('outcome', 'failure')), bits=bits, latency=f'{latency:.3f}' if latency is not None else self.t('unavailable'))

    def animate_events(self, events):
        self.animation_token += 1; token = self.animation_token
        evolutions = [e for e in (self.current or {}).get('events', []) if e.get('type') in ('mutation', 'crossover', 'selection', 'elimination')]
        if not events and not evolutions: self.draw_arena(); return
        # When possible, show several kinds in the slow demonstration, using
        # only real observations from this generation.
        baseline = [e for e in events if e.get('scenario') == 'baseline'] or list(events)
        sample = []
        seen = set()
        for event in baseline:
            kind = event.get('message_kind', 'legacy')
            if kind not in seen:
                sample.append(event); seen.add(kind)
            if len(sample) >= (3 if self.speed.get() == 'slow' else 1): break
        if len(sample) < 2 and self.speed.get() == 'slow':
            sample.extend(e for e in baseline if e not in sample and len(sample) < 2)
        for kind in ('mutation', 'crossover', 'selection', 'elimination'):
            item = next((e for e in evolutions if e.get('type') == kind), None)
            if item: sample.append(item)
        if self.speed.get() != 'slow': sample = sample[:2]
        def frame(i, n):
            if token != self.animation_token or not self.winfo_exists(): return
            if i >= len(sample): return
            if sample[i].get('type') == 'transmission': self.draw_arena(sample[i], n/12)
            else: self.draw_evolution(sample[i], n/12)
            if n < 12: self.after(35 if self.speed.get() == 'slow' else 10, lambda: frame(i, n+1))
            else: self.after(100, lambda: frame(i+1, 0))
        frame(0, 0)

    def next_box(self):
        if not self.box_events: return
        self.animation_token += 1
        self.box_index = (self.box_index + 1) % len(self.box_events)
        self.draw_arena(self.box_events[self.box_index], 1.0)

    def history_message(self, event, field):
        """Read the recorded bytes without inventing or shortening a message."""
        key = 'original_hex' if field == 'original' else 'decoded_hex'
        raw = event.get(key)
        if raw is None:
            return self.t('original_unknown') if field == 'original' else self.t('not_arrived')
        try:
            data = bytes.fromhex(raw)
        except (TypeError, ValueError):
            return self.t('original_unknown')
        if not data:
            return self.t('history_empty_message')
        try:
            return self.escape_message(data.decode('utf-8', errors='strict'))
        except UnicodeDecodeError:
            return self.t('not_decoded') + '\nHEX: ' + data.hex(' ')

    def open_messages_history(self):
        """Show recorded trials one round at a time, including after completion."""
        if not self.history:
            messagebox.showinfo(self.t('messages_history'), self.t('history_empty'))
            return
        existing = getattr(self, '_messages_history_window', None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return

        win = tk.Toplevel(self, bg=PAPER)
        self._messages_history_window = win
        win.title(self.t('history_title'))
        win.geometry('1100x690')
        win.minsize(700, 450)
        outer = ttk.Frame(win, padding=12)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text=self.t('history_title'), style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text=self.t('history_intro'), wraplength=1000).pack(anchor='w', pady=(4, 10))
        choose = ttk.Frame(outer)
        choose.pack(fill='x', pady=(0, 8))
        ttk.Label(choose, text=self.t('history_round')).pack(side='left', padx=(0, 8))
        rounds = ttk.Combobox(choose, state='readonly', width=18)
        rounds.pack(side='left')
        count = tk.StringVar(value='')
        ttk.Label(choose, textvariable=count).pack(side='left', padx=12)

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill='both', expand=True)
        columns = ('trial', 'kind', 'departure', 'arrival', 'status')
        style = ttk.Style(win)
        style.configure('History.Treeview', background=PLOT_BG, fieldbackground=PLOT_BG,
                        foreground=INK, rowheight=26)
        style.configure('History.Treeview.Heading', background='#eeddee', foreground=INK)
        style.map('History.Treeview', background=[('selected', '#dfc6e5')],
                  foreground=[('selected', INK)])
        table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse',
                             height=10, style='History.Treeview')
        for key, title, width in (
            ('trial', self.t('history_trial'), 125),
            ('kind', self.t('history_kind'), 115),
            ('departure', self.t('start_box'), 250),
            ('arrival', self.t('arrival_box'), 250),
            ('status', self.t('status'), 150),
        ):
            table.heading(key, text=title)
            table.column(key, width=width, minwidth=90, stretch=True)
        vertical = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=table.xview)
        table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        table.pack(side='left', fill='both', expand=True)

        detail_frame = ttk.Frame(outer)
        detail_frame.pack(fill='x', pady=(10, 0))
        details = tk.Text(detail_frame, height=7, wrap='word', bg=SOFT_CARD, fg=INK,
                          relief='flat', font=('Segoe UI', 10), padx=10, pady=8)
        detail_scroll = ttk.Scrollbar(detail_frame, orient='vertical', command=details.yview)
        details.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side='right', fill='y')
        details.pack(side='left', fill='both', expand=True)
        self.put_text(details, self.t('history_choose'))
        state = {'snapshots': [], 'events': []}

        def show_details(_event=None):
            selection = table.selection()
            if not selection:
                self.put_text(details, self.t('history_choose'))
                return
            event = state['events'][int(selection[0])]
            outcome = event.get('outcome')
            result = self.t('outcome_' + outcome) if outcome in ('intact', 'corrupted', 'lost', 'failure', 'encoding_error') else self.t('unavailable')
            text = (self.t('history_departure') + '\n' + self.history_message(event, 'original') +
                    '\n\n' + self.t('history_arrival') + '\n' + self.history_message(event, 'decoded') +
                    '\n\n' + self.t('status') + ' : ' + result)
            self.put_text(details, text)

        def show_round(_event=None):
            for item in table.get_children():
                table.delete(item)
            index = rounds.current()
            if index < 0 or index >= len(state['snapshots']):
                state['events'] = []
                count.set(self.t('history_count').format(count=0))
                self.put_text(details, self.t('history_choose'))
                return
            snapshot = state['snapshots'][index]
            state['events'] = [e for e in snapshot.get('events', []) if e.get('type') == 'transmission']
            for i, event in enumerate(state['events']):
                scenario = event.get('scenario')
                trial = self.t(scenario) if scenario in ('baseline', 'stress') else self.t('unavailable')
                kind = event.get('message_kind')
                contents = self.t(kind) if kind in ('phrase', 'color', 'code') else self.t('history_binary')
                outcome = event.get('outcome')
                result = self.t('outcome_' + outcome) if outcome in ('intact', 'corrupted', 'lost', 'failure', 'encoding_error') else self.t('unavailable')
                before = self.message_preview(event, 'original').replace('\n', ' · ')[:70]
                after = self.message_preview(event, 'decoded').replace('\n', ' · ')[:70]
                table.insert('', 'end', iid=str(i), values=(trial, contents, before, after, result))
            count.set(self.t('history_count').format(count=len(state['events'])))
            if state['events']:
                table.selection_set('0')
                show_details()
            else:
                self.put_text(details, self.t('history_choose'))

        def refresh():
            selected = rounds.current()
            state['snapshots'] = list(self.history)
            rounds.configure(values=[f"{self.t('generation')} {s.get('generation', i)}" for i, s in enumerate(state['snapshots'])])
            if state['snapshots']:
                rounds.current(selected if 0 <= selected < len(state['snapshots']) else len(state['snapshots']) - 1)
            show_round()

        def update_rounds():
            # Add new rounds without disturbing the message being examined.
            current_history = list(self.history)
            if len(current_history) != len(state['snapshots']):
                state['snapshots'] = current_history
                rounds.configure(values=[f"{self.t('generation')} {s.get('generation', i)}" for i, s in enumerate(current_history)])

        ttk.Button(choose, text=self.t('history_refresh'), command=refresh).pack(side='right')
        rounds.bind('<<ComboboxSelected>>', show_round)
        table.bind('<<TreeviewSelect>>', show_details)
        # Retain widget references for accessibility and automated verification.
        win.history_rounds, win.history_table, win.history_details = rounds, table, details
        win.refresh_history, win.update_history_rounds = refresh, update_rounds
        refresh()

    def draw_evolution(self, event, fraction):
        self.displayed_event = None
        c = self.canvas; c.delete('all'); w = c.winfo_width() if c.winfo_width() > 5 else 340; h = c.winfo_height() if c.winfo_height() > 5 else 150
        kind = event.get('type'); ident = event.get('individual_id', '?'); parents = ', '.join(event.get('parents', [])) or '—'
        label = self.t('event_' + kind).format(id=ident, parents=parents)
        c.create_text(w/2, 24, text=label, fill='#58475e', font=('Segoe UI', 10, 'bold'), width=w-20)
        color = {'mutation': '#ffe0a7', 'crossover': '#d7c6f0', 'selection': '#bcead0', 'elimination': '#efb5c1'}.get(kind, '#d1d5df')
        self.rounded(c, w/2-70, h/2-37, w/2+70, h/2+37, 14, fill=color, outline='#a892aa', width=2)
        c.create_text(w/2, h/2-18, text=parents, fill='#615267', font=('Segoe UI', 9))
        if kind in ('mutation', 'crossover') and event.get('parents'):
            # This nested box is explicitly labelled as a metaphor for a
            # child produced by the actually recorded parents.
            self.rounded(c, w/2-34, h/2-3, w/2+34, h/2+26, 8, fill='#fff2d6', outline='#bd9b8b', width=2)
            c.create_text(w/2, h/2+11, text=ident, fill='#58475e', font=('Segoe UI', 9, 'bold'))
            c.create_text(w/2, h-20, text=self.t('nested_note'), fill='#75657b', font=('Segoe UI', 8), width=w-20)
        else:
            c.create_text(w/2, h/2+10, text=ident, fill='#58475e', font=('Segoe UI', 10, 'bold'))
        if kind == 'crossover' and event.get('changed') is False:
            c.create_text(w/2, h-36, text=self.t('unchanged'), fill='#75657b', width=w-20)

    def draw_graph(self):
        if not hasattr(self, 'graph'): return
        c = self.graph; c.delete('all'); w = c.winfo_width() if c.winfo_width() > 5 else 350; h = c.winfo_height() if c.winfo_height() > 5 else 130; left, right, top, bottom = 42, w-15, 10, h-25
        c.create_line(left, top, left, bottom, right, bottom, fill='#846e87')
        for yv in (0, .5, 1):
            y = bottom - yv * (bottom-top); c.create_line(left, y, right, y, fill='#e2d8e5'); c.create_text(left-7, y, text=f'{yv:.0%}', fill=MUTED, anchor='e')
        # Normal-trial outcomes are exclusive: intact, changed, lost, and
        # failures/errors. Extreme trials are separate resilience experiments.
        groups = [('intact',), ('corrupted',), ('lost',), ('failure', 'encoding_error')]
        colors = PLOT_COLORS
        series = []
        for color, group in zip(colors, groups):
            values = []
            for snap in self.history:
                trials = [e for e in snap.get('events', []) if e.get('type') == 'transmission' and e.get('scenario') == 'baseline']
                values.append(sum(e.get('outcome') in group for e in trials) / len(trials) if trials else None)
            series.append((color, values))
        for color, values in series:
            pts=[]
            for i, value in enumerate(values):
                if value is None:
                    if len(pts) >= 4: c.create_line(*pts, fill=color, width=2)
                    pts=[]
                    continue
                x = left + (right-left)*i/max(1, len(values)-1); y = bottom - max(0, min(1, value))*(bottom-top); pts.extend((x,y)); c.create_oval(x-3,y-3,x+3,y+3,fill=color,outline='')
            if len(pts) >= 4: c.create_line(*pts, fill=color, width=2)

    def inspect(self):
        if not self.current or not self.listbox.curselection(): return
        p = self.current['individuals'][self.listbox.curselection()[0]]
        win = tk.Toplevel(self, bg=PAPER); win.title(self.t('inspect_title') + ' — ' + str(p.get('id'))); win.geometry('900x730')
        tabs = ttk.Notebook(win); tabs.pack(fill='both', expand=True, padx=8, pady=8)
        tree_tab = ttk.Frame(tabs, padding=8); details = ttk.Frame(tabs, padding=8); family = ttk.Frame(tabs, padding=8)
        tabs.add(tree_tab, text=self.t('tree_tab')); tabs.add(details, text=self.t('details_tab')); tabs.add(family, text=self.t('family_tab'))
        ttk.Label(tree_tab, text=self.t('click_node'), wraplength=850).pack(anchor='w')
        transmissions = [e for e in self.current.get('events', []) if e.get('type') == 'transmission' and e.get('individual_id') == p.get('id')]
        selected = tk.IntVar(value=0)
        if transmissions:
            values = [f"{i+1} · {self.t(e.get('scenario','baseline'))} · {self.t(e.get('outcome','failure'))}" for i, e in enumerate(transmissions)]
            chooser = ttk.Combobox(tree_tab, values=values, state='readonly', width=55); chooser.current(0); chooser.pack(anchor='w', pady=4)
            chooser.bind('<<ComboboxSelected>>', lambda _e: selected.set(chooser.current()))
        tree_holder = ttk.Frame(tree_tab); tree_holder.pack(fill='both', expand=True)
        canvas = tk.Canvas(tree_holder, bg=PLOT_BG, height=300, highlightthickness=0)
        vs = ttk.Scrollbar(tree_holder, orient='vertical', command=canvas.yview); hs = ttk.Scrollbar(tree_tab, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set); vs.pack(side='right', fill='y'); canvas.pack(side='left', fill='both', expand=True); hs.pack(fill='x')
        node_details = tk.Text(tree_tab, height=9, wrap='word', bg=SOFT_CARD, fg=INK, relief='flat', font=('Consolas', 10)); node_details.pack(fill='x', pady=6)
        self.put_text(node_details, self.t('click_node'))
        root = p.get('tree_data')
        if isinstance(root, dict):
            nodes = []
            def layout(node, path, depth):
                children = node.get('children', [])
                children = children if isinstance(children, list) else []
                child_nodes = [layout(ch, path + [i], depth + 1) for i, ch in enumerate(children) if isinstance(ch, dict)]
                if child_nodes: x = sum(n['x'] for n in child_nodes) / len(child_nodes)
                else: x = 90 + 150 * sum(not n.get('children') for n in nodes)
                item = {'x': x, 'y': 45 + depth * 80, 'data': node, 'path': path, 'children': child_nodes}; nodes.append(item); return item
            layout(root, [], 0)
            for node in nodes:
                for child in node['children']:
                    canvas.create_line(node['x'], node['y']+17, child['x'], child['y']-17, fill='#907d9b', width=2, arrow='first')
            def show_node(node):
                data = node['data']; op = str(data.get('op', '?')); info = OP_INFO.get(op, ('', ''))[0 if self.lang.get() == 'fr' else 1]
                lines = [f"{op} {data.get('params', [])}", info, '']
                event = transmissions[selected.get()] if transmissions and selected.get() < len(transmissions) else {}
                found = False
                for key, label in (('encode_steps', 'encoding'), ('decode_steps', 'decoding')):
                    for step in event.get(key, []):
                        if step.get('path') == node['path']:
                            found = True; lines.extend([self.t(label), f"{self.t('before')}: {step.get('before_hex', '—')}", f"{self.t('after')}: {step.get('after_hex', '—')}"])
                            if step.get('truncated'): lines.append(self.t('truncated'))
                            lines.append('')
                if not found: lines.append(self.t('no_trace'))
                self.put_text(node_details, '\n'.join(lines))
            for i, node in enumerate(nodes):
                x, y = node['x'], node['y']; tag = f'node_{i}'
                self.rounded(canvas, x-65, y-17, x+65, y+17, 10, fill='#ccebdc', outline='#8cc4ad', tags=(tag,))
                canvas.create_text(x, y, text=str(node['data'].get('op', '?')), fill=INK, tags=(tag,))
                canvas.tag_bind(tag, '<Button-1>', lambda _e, node=node: show_node(node))
            if transmissions: chooser.bind('<<ComboboxSelected>>', lambda _e: (selected.set(chooser.current()), self.put_text(node_details, self.t('click_node'))))
            canvas.configure(scrollregion=(0, 0, max(650, max(n['x'] for n in nodes) + 90), max(280, max(n['y'] for n in nodes) + 60)))
        else: canvas.create_text(30, 30, text=self.t('no_tree'), fill=INK, anchor='w')
        text = tk.Text(details, wrap='word', padx=15, pady=15, bg=SOFT_CARD, fg=INK, relief='flat', font=('Consolas', 10)); text.pack(fill='both', expand=True)
        fit = p.get('fitness', {})
        value = [f"{self.t('id')}: {p.get('id')}", f"{self.t('generation')}: {p.get('generation')}", f"{self.t('parents')}: {p.get('parents') or '—'}", f"{self.t('rank')}: {p.get('rank')}   {self.t('niche')}: {p.get('niche')}", '', self.t('structure'), str(p.get('tree', '')), '', self.t('stats')]
        value += [f"{self.t(k)} ({k}): {fit.get(k, 0):.3f}" for k in ('delivery','integrity','efficiency','resilience','scalar')]
        value.append('\n' + json.dumps(p.get('stats', {}), ensure_ascii=False, indent=2))
        value += ['', self.t('measure_help'), '', self.t('pipeline')]
        event = next((e for e in self.current.get('events', []) if e.get('type') == 'transmission' and e.get('individual_id') == p.get('id')), None)
        if event:
            for key in ('original_hex','encoded_hex','received_hex','decoded_hex'): value.append(f"{self.t(key)}: {event.get(key) if event.get(key) is not None else '—'}")
            value.append(self.describe_event(event))
            value.append(f"{self.t('attack')}: {self.t('yes' if event.get('adversarial') else 'no')}; {self.t('checksum_failed')}: {self.t('yes' if event.get('checksum_failed') else 'no')}")
            changes = event.get('bit_changes', [])
            value.append(self.t('bit_changes') + ': ' + (json.dumps(changes, ensure_ascii=False) if changes else self.t('no_bits')))
            if event.get('bit_changes_truncated'): value.append(self.t('truncated'))
        else: value.append(self.t('no_event'))
        text.insert('1.0', '\n'.join(value)); text.config(state='disabled')
        family_text = tk.Text(family, wrap='word', padx=15, pady=15, bg=SOFT_CARD, fg=INK, relief='flat', font=('Consolas', 10)); family_text.pack(fill='both', expand=True)
        lines = [self.t('family_intro'), f"{self.t('id')}: {p.get('id')}", f"{self.t('parents')}: {', '.join(p.get('parents') or []) or self.t('no_parents')}", '']
        for snapshot in self.history:
            person = next((item for item in snapshot.get('individuals', []) if item.get('id') == p.get('id')), None)
            if person:
                lines.append(self.t('history_generation').format(g=snapshot.get('generation'), score=person.get('fitness', {}).get('scalar', 0), rank=person.get('rank'), tree=person.get('tree', '')))
            for event in snapshot.get('events', []):
                if event.get('individual_id') == p.get('id') and event.get('type') in ('mutation', 'crossover'):
                    lines.append(self.t('event_' + event['type']).format(id=p.get('id'), parents=', '.join(event.get('parents', [])) or '—'))
                    for key in ('before', 'donor', 'after'):
                        if key in event: lines.append(f"{key}:\n{event[key]}")
        family_text.insert('1.0', '\n\n'.join(lines)); family_text.config(state='disabled')
        return win

    def dashboard(self):
        if not self.current: messagebox.showinfo(self.t('dashboard'), self.t('no_data')); return
        people = self.current.get('individuals', []); win = tk.Toplevel(self, bg=PAPER); win.title(self.t('dashboard')); win.geometry('860x650')
        ttk.Label(win, text=self.t('pareto_note'), wraplength=800).pack(anchor='w', padx=12, pady=6)
        canvas = tk.Canvas(win, bg=PLOT_BG, width=760, height=300, highlightthickness=0); canvas.pack(fill='x', padx=12)
        x0, x1, y0, y1 = 70, 700, 260, 30
        canvas.create_line(x0,y1,x0,y0,x1,y0,fill='#846e87',width=2)
        canvas.create_text((x0+x1)/2, 287, text=self.t('delivery') + ' 0 → 1', fill=INK)
        canvas.create_text(10, 15, text=self.t('integrity') + ' 0 → 1', fill=INK, anchor='w')
        for person in people:
            f = person.get('fitness', {}); x = x0 + (x1-x0)*float(f.get('delivery',0)); y = y0 - (y0-y1)*float(f.get('integrity',0))
            color = PLOT_COLORS[0] if person.get('rank') == 0 else PLOT_COLORS[1]
            canvas.create_oval(x-5,y-5,x+5,y+5,fill=color,outline='')
        stats = [p.get('stats', {}) for p in people]; niches = {}
        for p in people: niches[str(p.get('niche', '—'))] = niches.get(str(p.get('niche', '—')), 0) + 1
        sizes = [p.get('complexity') for p in people if isinstance(p.get('complexity'), (int,float))]
        received = sum(s.get('received', 0) for s in stats if s.get('mean_latency') is not None)
        mean_latency = sum(s.get('mean_latency', 0)*s.get('received', 0) for s in stats if s.get('mean_latency') is not None)/received if received else None
        lines = [self.t('trial_note'), '', f"{self.t('population_stats')}: {len(people)}   ·   {self.t('front')}: {self.current.get('summary',{}).get('front0', 0)}", f"{self.t('niches')}: " + ', '.join(f'{n}: {v}' for n,v in sorted(niches.items())), f"{self.t('complexity')}: " + (f"{min(sizes)}–{max(sizes)} · {self.t('average')} {sum(sizes)/len(sizes):.1f}" if sizes else self.t('unavailable')), f"{self.t('latency_mean')}: " + (f'{mean_latency:.3f}' if mean_latency is not None else self.t('unavailable')), f"{self.t('lost_count')}: {sum(s.get('lost',0) for s in stats)}   ·   {self.t('failure_count')}: {sum(s.get('failures',0) for s in stats)}   ·   {self.t('byte_count')}: {sum(s.get('sent_bytes',0) for s in stats)}"]
        text = tk.Text(win, wrap='word', height=10, padx=12, pady=10, bg=SOFT_CARD, fg=INK, relief='flat', font=('Segoe UI', 10)); text.pack(fill='both', expand=True, padx=12, pady=8); text.insert('1.0', '\n'.join(lines)); text.config(state='disabled')
        return win

    def export_json(self):
        if not self.history: messagebox.showinfo(self.t('export'), self.t('no_history')); return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if not path: return
        data = self.replay_data if self.replay_data else self.engine.export()
        try:
            with open(path, 'w', encoding='utf-8') as file: json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
            self.status.set(self.t('saved'))
        except (OSError, ValueError, TypeError) as exc: messagebox.showerror(self.t('error'), str(exc))

    def export_csv(self):
        if not self.history: messagebox.showinfo(self.t('csv'), self.t('no_history')); return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file); writer.writerow(['generation','id','tree','rank','niche','delivery','integrity','efficiency','resilience','scalar'])
                for s in self.history:
                    for p in s.get('individuals', []):
                        f = p.get('fitness', {}); writer.writerow([s.get('generation'),p.get('id'),p.get('tree'),p.get('rank'),p.get('niche')] + [f.get(k) for k in ('delivery','integrity','efficiency','resilience','scalar')])
            self.status.set(self.t('saved'))
        except OSError as exc: messagebox.showerror(self.t('error'), str(exc))

    def open_replay(self):
        path = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if not path: return
        try:
            with open(path, encoding='utf-8') as file: data = json.load(file)
            if not isinstance(data, dict) or not isinstance(data.get('generations'), list) or not all(isinstance(g, dict) and isinstance(g.get('individuals'), list) and isinstance(g.get('events'), list) and isinstance(g.get('summary'), dict) for g in data['generations']): raise ValueError('Invalid replay format')
        except (OSError, ValueError, TypeError) as exc: messagebox.showerror(self.t('error'), self.t('open_error') + '\n' + str(exc)); return
        self.reset(); self.replay_data = data; self.status.set(self.t('replaymode'))


if __name__ == '__main__':
    ArenaApp().mainloop()
