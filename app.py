"""RawHostileSelect Evolution Arena: local, bilingual view of recorded events.

The simulation runs in a worker; Tk is touched only by the main thread.
"""
import csv
import json
import queue
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


class ArenaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1280x850")
        self.minsize(900, 650)
        self.lang = tk.StringVar(value="fr")
        self.population = tk.StringVar(value="12")
        self.generations = tk.StringVar(value="20")
        self.difficulty = tk.StringVar(value="medium")
        self.seed = tk.StringVar(value="42")
        self.speed = tk.StringVar(value="slow")
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
        self._build()
        self.status.set(self.t("ready"))
        self.after(80, self._poll)

    def t(self, key):
        return TEXT[self.lang.get()].get(key, key)

    def _build(self):
        for child in self.winfo_children():
            child.destroy()
        self.title(self.t("title"))
        self.configure(bg="#101522")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#101522")
        style.configure("TLabel", background="#101522", foreground="#e4ecf7", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"), foreground="#7be5d2")
        style.configure("TButton", padding=(9, 6), font=("Segoe UI", 9, "bold"))
        style.configure("TLabelframe", background="#101522", foreground="#e4ecf7")
        style.configure("TLabelframe.Label", background="#101522", foreground="#7be5d2", font=("Segoe UI", 10, "bold"))
        header = ttk.Frame(self, padding=(15, 10)); header.pack(fill="x")
        ttk.Label(header, text=self.t("title"), style="Title.TLabel").pack(side="left")
        ttk.Combobox(header, textvariable=self.lang, values=("fr", "en"), state="readonly", width=4).pack(side="right")
        header.winfo_children()[-1].bind("<<ComboboxSelected>>", lambda _e: self._rebuild())
        ttk.Label(self, text=self.t("subtitle")).pack(anchor="w", padx=18)
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
        controls = ttk.Frame(self, padding=(14, 0)); controls.pack(fill="x")
        for label, cmd in (("start", self.start), ("pause", self.pause), ("next", self.step), ("reset", self.reset)):
            button = ttk.Button(controls, text=self.t(label), command=cmd); button.pack(side="left", padx=2, pady=2)
            if label == 'pause': self.pause_button = button
        file_controls = ttk.Frame(self, padding=(14, 0)); file_controls.pack(fill="x")
        for label, cmd in (("export", self.export_json), ("csv", self.export_csv), ("replay", self.open_replay)):
            ttk.Button(file_controls, text=self.t(label), command=cmd).pack(side="left", padx=2, pady=2)
        self._update_pause_button()
        ttk.Label(self, textvariable=self.status).pack(anchor="w", padx=18, pady=3)
        main = ttk.Panedwindow(self, orient="horizontal"); main.pack(fill="both", expand=True, padx=14, pady=5)
        left = ttk.Frame(main); right = ttk.Frame(main); main.add(left, weight=3); main.add(right, weight=2)
        arena = ttk.LabelFrame(left, text=self.t("arena"), padding=6); arena.pack(fill="both", expand=True)
        ttk.Label(arena, text=self.t("metaphor"), wraplength=650).pack(anchor="w")
        self.canvas = tk.Canvas(arena, height=180, bg="#161f33", highlightthickness=0); self.canvas.pack(fill="both", expand=True, pady=4)
        ttk.Label(arena, text=self.t("legend"), foreground="#b5c6d9").pack(anchor="w")
        ttk.Label(arena, text=self.t("sample"), foreground="#b5c6d9", wraplength=650).pack(anchor="w")
        graph = ttk.LabelFrame(left, text=self.t("progress"), padding=6); graph.pack(fill="both", expand=True, pady=(8, 0))
        self.graph = tk.Canvas(graph, height=150, bg="#161f33", highlightthickness=0); self.graph.pack(fill="both", expand=True)
        key = ttk.Frame(graph); key.pack(anchor="w")
        for color, label in (('#7be5d2', self.t('best')), ('#f5cb6f', self.t('average')), ('#ef8797', self.t('best') + ' ' + self.t('integrity'))):
            ttk.Label(key, text='●', foreground=color).pack(side='left'); ttk.Label(key, text=' ' + label + '   ').pack(side='left')
        self.graph.bind("<Configure>", lambda _e: self.draw_graph())
        panel = ttk.LabelFrame(right, text=self.t("metrics"), padding=7); panel.pack(fill="x")
        self.metric_text = tk.Text(panel, height=5, wrap="word", bg="#1c2940", fg="#e4ecf7", relief="flat", font=("Segoe UI", 10)); self.metric_text.pack(fill="x"); self.metric_text.config(state="disabled")
        ttk.Label(panel, text=self.t("measure_help"), wraplength=450, foreground="#b5c6d9").pack(anchor="w", pady=4)
        people = ttk.LabelFrame(right, text=self.t("individuals"), padding=6); people.pack(fill="both", expand=True, pady=6)
        self.listbox = tk.Listbox(people, bg="#1c2940", fg="#e4ecf7", selectbackground="#39786f", relief="flat", height=7, font=("Consolas", 10)); self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(people, command=self.listbox.yview); scroll.pack(side="right", fill="y"); self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.bind("<Double-Button-1>", lambda _e: self.inspect())
        actions = ttk.Frame(right); actions.pack(fill='x')
        ttk.Button(actions, text=self.t("inspect"), command=self.inspect).pack(side='right')
        ttk.Button(actions, text=self.t("dashboard"), command=self.dashboard).pack(side='right', padx=4)
        log = ttk.LabelFrame(right, text=self.t("narrative"), padding=6); log.pack(fill="both", expand=True, pady=6)
        self.log = tk.Text(log, height=7, bg="#1c2940", fg="#e4ecf7", relief="flat", wrap="word", font=("Segoe UI", 9)); self.log.pack(side="left", fill="both", expand=True)
        s = ttk.Scrollbar(log, command=self.log.yview); s.pack(side="right", fill="y"); self.log.config(yscrollcommand=s.set, state="disabled")
        self.draw_arena()
        if self.current: self.show_snapshot(self.current, animate=False)
        self.render_log()

    def _rebuild(self):
        self.animation_token += 1
        self._build()
        self.status.set(self.t('working') if self.busy else (self.t('paused') if self.current else self.t('ready')))

    def _update_pause_button(self):
        if hasattr(self, 'pause_button'):
            self.pause_button.configure(text=self.t('pause' if self.running else 'resume'))

    def make_engine(self):
        try:
            population, generations, seed = int(self.population.get()), int(self.generations.get()), int(self.seed.get())
            if not 2 <= population <= 100 or not 1 <= generations <= 1000: raise ValueError()
            self.engine = ArenaEngine(ArenaConfig(population=population, generations=generations, difficulty=self.difficulty.get(), seed=seed))
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
            if self.running: self.after(3800 if self.speed.get() == "slow" else 30, self._continue)
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
                    if self.running: self.after(3800 if self.speed.get() == "slow" else 20, self._continue)
        except queue.Empty: pass
        self.after(80, self._poll)

    def reset(self):
        self.running = False; self.busy = False; self.token += 1; self.animation_token += 1
        self.engine = None; self.history = []; self.current = None; self.replay_data = None; self.replay_index = 0
        self.status.set(self.t("ready")); self._build()

    def put_text(self, widget, value):
        widget.config(state="normal"); widget.delete("1.0", "end"); widget.insert("end", value); widget.config(state="disabled")

    def show_snapshot(self, snap, animate=True):
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
        c = self.canvas; c.delete('all'); w = max(c.winfo_width(), 600); h = max(c.winfo_height(), 180); y = h * .57
        c.create_line(75, y, w-75, y, fill='#647895', width=3, dash=(7, 6))
        for x, fill, label in ((60, '#7ee8d2', 'B2'), (w/2, '#936ee8', 'C3'), (w-60, '#ef7b83', 'A1')):
            c.create_oval(x-25, y-25, x+25, y+25, fill=fill, outline=''); c.create_text(x, y, text=label, fill='#111827', font=('Segoe UI', 12, 'bold'))
        if event:
            outcome = event.get('outcome', 'failure'); color = {'intact':'#51d691','corrupted':'#ef636c','lost':'#91a0b6','failure':'#f7a955'}.get(outcome, '#f7a955')
            x = 90 + fraction * (w - 180)
            if outcome not in ('failure', 'encoding_error') and not (outcome == 'lost' and fraction > .65): c.create_rectangle(x-9,y-9,x+9,y+9,fill=color,outline='white')
            c.create_text(w/2, 26, text=self.describe_event(event), fill='#e4ecf7', font=('Segoe UI', 9), width=w-20)
        else: c.create_text(w/2, 26, text=self.t('ready'), fill='#e4ecf7')
        c.create_text(w/2, h-16, text=self.t('limit'), fill='#b5c6d9', font=('Segoe UI', 8), width=w-10)

    def describe_event(self, event):
        latency = event.get('latency')
        bits = self.t('unavailable') if event.get('adversarial') or event.get('received_hex') is None else event.get('bit_flips', 0)
        return self.t('transmission').format(id=event.get('individual_id', '?'), scenario=self.t(event.get('scenario', 'baseline')), outcome=self.t(event.get('outcome', 'failure')), bits=bits, latency=f'{latency:.3f}' if latency is not None else self.t('unavailable'))

    def animate_events(self, events):
        self.animation_token += 1; token = self.animation_token
        evolutions = [e for e in (self.current or {}).get('events', []) if e.get('type') in ('mutation', 'crossover', 'selection', 'elimination')]
        if not events and not evolutions: self.draw_arena(); return
        sample = list(events[:2] if self.speed.get() == 'slow' else events[:1])
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

    def draw_evolution(self, event, fraction):
        c = self.canvas; c.delete('all'); w = max(c.winfo_width(), 600); h = max(c.winfo_height(), 180)
        kind = event.get('type'); ident = event.get('individual_id', '?'); parents = ', '.join(event.get('parents', [])) or '—'
        label = self.t('event_' + kind).format(id=ident, parents=parents)
        c.create_text(w/2, 26, text=label, fill='#e4ecf7', font=('Segoe UI', 10, 'bold'), width=w-20)
        color = {'mutation': '#f5cb6f', 'crossover': '#bba0ff', 'selection': '#7be5d2', 'elimination': '#ef8797'}.get(kind, '#b5c6d9')
        # Animated emphasis only: every label and structure is taken from the recorded event.
        radius = 20 + 5 * fraction
        c.create_oval(w/2-radius, h/2-radius, w/2+radius, h/2+radius, outline=color, width=4)
        c.create_text(w/2, h/2, text=ident, fill='#e4ecf7')
        if kind == 'crossover' and event.get('changed') is False:
            c.create_text(w/2, h-24, text=self.t('unchanged'), fill='#b5c6d9', width=w-20)

    def draw_graph(self):
        if not hasattr(self, 'graph'): return
        c = self.graph; c.delete('all'); w = max(c.winfo_width(), 400); h = max(c.winfo_height(), 150); left, right, top, bottom = 42, w-15, 10, h-25
        c.create_line(left, top, left, bottom, right, bottom, fill='#8296b0')
        for yv in (0, .5, 1):
            y = bottom - yv * (bottom-top); c.create_line(left, y, right, y, fill='#34445b'); c.create_text(left-7, y, text=f'{yv:.1f}', fill='#b5c6d9', anchor='e')
        series = [('#7be5d2', [s.get('summary', {}).get('best', 0) for s in self.history]), ('#f5cb6f', [s.get('summary', {}).get('average', 0) for s in self.history]), ('#ef8797', [max((p.get('fitness', {}).get('integrity', 0) for p in s.get('individuals', [])), default=0) for s in self.history])]
        for color, values in series:
            pts=[]
            for i, value in enumerate(values):
                x = left + (right-left)*i/max(1, len(values)-1); y = bottom - max(0, min(1, value))*(bottom-top); pts.extend((x,y)); c.create_oval(x-2,y-2,x+2,y+2,fill=color,outline='')
            if len(pts) >= 4: c.create_line(*pts, fill=color, width=2)

    def inspect(self):
        if not self.current or not self.listbox.curselection(): return
        p = self.current['individuals'][self.listbox.curselection()[0]]
        win = tk.Toplevel(self); win.title(self.t('inspect_title') + ' — ' + str(p.get('id'))); win.geometry('900x730')
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
        canvas = tk.Canvas(tree_holder, bg='#161f33', height=300, highlightthickness=0)
        vs = ttk.Scrollbar(tree_holder, orient='vertical', command=canvas.yview); hs = ttk.Scrollbar(tree_tab, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set); vs.pack(side='right', fill='y'); canvas.pack(side='left', fill='both', expand=True); hs.pack(fill='x')
        node_details = tk.Text(tree_tab, height=9, wrap='word', bg='#1c2940', fg='#e4ecf7', relief='flat', font=('Consolas', 10)); node_details.pack(fill='x', pady=6)
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
                    canvas.create_line(node['x'], node['y']+17, child['x'], child['y']-17, fill='#91a4c0', width=2, arrow='first')
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
                canvas.create_rectangle(x-65, y-17, x+65, y+17, fill='#3f777c', outline='#8debd7', tags=(tag,))
                canvas.create_text(x, y, text=str(node['data'].get('op', '?')), fill='white', tags=(tag,))
                canvas.tag_bind(tag, '<Button-1>', lambda _e, node=node: show_node(node))
            if transmissions: chooser.bind('<<ComboboxSelected>>', lambda _e: (selected.set(chooser.current()), self.put_text(node_details, self.t('click_node'))))
            canvas.configure(scrollregion=(0, 0, max(650, max(n['x'] for n in nodes) + 90), max(280, max(n['y'] for n in nodes) + 60)))
        else: canvas.create_text(30, 30, text=self.t('no_tree'), fill='white', anchor='w')
        text = tk.Text(details, wrap='word', padx=15, pady=15, font=('Consolas', 10)); text.pack(fill='both', expand=True)
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
        family_text = tk.Text(family, wrap='word', padx=15, pady=15, font=('Consolas', 10)); family_text.pack(fill='both', expand=True)
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
        people = self.current.get('individuals', []); win = tk.Toplevel(self); win.title(self.t('dashboard')); win.geometry('860x650')
        ttk.Label(win, text=self.t('pareto_note'), wraplength=800).pack(anchor='w', padx=12, pady=6)
        canvas = tk.Canvas(win, bg='#161f33', width=760, height=300, highlightthickness=0); canvas.pack(fill='x', padx=12)
        x0, x1, y0, y1 = 70, 700, 260, 30
        canvas.create_line(x0,y1,x0,y0,x1,y0,fill='#b5c6d9',width=2)
        canvas.create_text((x0+x1)/2, 287, text=self.t('delivery') + ' 0 → 1', fill='white')
        canvas.create_text(10, 15, text=self.t('integrity') + ' 0 → 1', fill='white', anchor='w')
        for person in people:
            f = person.get('fitness', {}); x = x0 + (x1-x0)*float(f.get('delivery',0)); y = y0 - (y0-y1)*float(f.get('integrity',0))
            color = '#7be5d2' if person.get('rank') == 0 else '#ef8797'
            canvas.create_oval(x-5,y-5,x+5,y+5,fill=color,outline='')
        stats = [p.get('stats', {}) for p in people]; niches = {}
        for p in people: niches[str(p.get('niche', '—'))] = niches.get(str(p.get('niche', '—')), 0) + 1
        sizes = [p.get('complexity') for p in people if isinstance(p.get('complexity'), (int,float))]
        received = sum(s.get('received', 0) for s in stats if s.get('mean_latency') is not None)
        mean_latency = sum(s.get('mean_latency', 0)*s.get('received', 0) for s in stats if s.get('mean_latency') is not None)/received if received else None
        lines = [self.t('trial_note'), '', f"{self.t('population_stats')}: {len(people)}   ·   {self.t('front')}: {self.current.get('summary',{}).get('front0', 0)}", f"{self.t('niches')}: " + ', '.join(f'{n}: {v}' for n,v in sorted(niches.items())), f"{self.t('complexity')}: " + (f"{min(sizes)}–{max(sizes)} · {self.t('average')} {sum(sizes)/len(sizes):.1f}" if sizes else self.t('unavailable')), f"{self.t('latency_mean')}: " + (f'{mean_latency:.3f}' if mean_latency is not None else self.t('unavailable')), f"{self.t('lost_count')}: {sum(s.get('lost',0) for s in stats)}   ·   {self.t('failure_count')}: {sum(s.get('failures',0) for s in stats)}   ·   {self.t('byte_count')}: {sum(s.get('sent_bytes',0) for s in stats)}"]
        text = tk.Text(win, wrap='word', height=10, padx=12, pady=10, bg='#1c2940', fg='#e4ecf7', relief='flat', font=('Segoe UI', 10)); text.pack(fill='both', expand=True, padx=12, pady=8); text.insert('1.0', '\n'.join(lines)); text.config(state='disabled')
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
