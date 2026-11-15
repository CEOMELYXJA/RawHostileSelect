#!/usr/bin/env python3
"""
Auto-évolution de protocoles par sélection naturelle
dans un environnement extrêmement hostile.

Idée centrale :
  On ne conçoit plus. On laisse évoluer.
  Populations de protocoles + architectures de mémoire
  s'affrontent sous bruit, pertes, latence variable,
  pannes et attaques adversariales.
  Ce qui survit devient le nouveau stack.

Prototype v1 — extensible vers Genetic Programming
et architectures mémoire non-classiques.
"""

from __future__ import annotations

import copy
import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ============================================================
# 1. ENVIRONNEMENT HOSTILE
# ============================================================

@dataclass
class HostileConfig:
    """Paramètres de l'environnement hostile."""
    bit_flip_prob: float = 0.02          # Probabilité de flip d'un bit
    packet_drop_prob: float = 0.15       # Probabilité de perte pure
    latency_mean: float = 8.0            # Latence moyenne (unités arbitraires)
    latency_std: float = 6.0             # Jitter
    adversarial_corruption_prob: float = 0.05  # Attaquant qui corrompt un paquet
    node_failure_prob: float = 0.03      # Un nœud tombe temporairement
    max_latency: float = 40.0


class HostileEnvironment:
    """Simule le canal et les conditions hostiles."""

    def __init__(self, config: HostileConfig, seed: Optional[int] = None):
        self.config = config
        self.rng = np.random.default_rng(seed)

    def transmit(self, packet: bytes, from_node: int, to_node: int) -> Tuple[Optional[bytes], float]:
        """
        Tente de transmettre un paquet.
        Retourne (paquet reçu ou None si perdu, latence subie).
        """
        # Perte pure
        if self.rng.random() < self.config.packet_drop_prob:
            return None, 0.0

        # Latence
        latency = float(np.clip(
            self.rng.normal(self.config.latency_mean, self.config.latency_std),
            0.5, self.config.max_latency
        ))

        # Corruption adversariale (remplace par données aléatoires)
        if self.rng.random() < self.config.adversarial_corruption_prob:
            corrupted = bytes(self.rng.integers(0, 256, size=len(packet), dtype=np.uint8))
            return corrupted, latency

        # Bruit de bit
        data = bytearray(packet)
        for i in range(len(data)):
            for bit in range(8):
                if self.rng.random() < self.config.bit_flip_prob:
                    data[i] ^= (1 << bit)

        return bytes(data), latency


# ============================================================
# 2. GENOME DU PROTOCOLE + ARCHITECTURE MÉMOIRE
# ============================================================

@dataclass
class ProtocolGenome:
    """
    Représentation évolutive d'un protocole + stratégie mémoire.
    Les gènes sont des paramètres continus/discrets mutables.
    """
    # --- Communication ---
    redundancy: float = 2.0              # Nombre moyen de copies (1.0 – 6.0)
    interleave_depth: int = 2            # Profondeur d'interleaving (1–8)
    ack_mode: int = 1                    # 0=none, 1=simple, 2=selective
    retransmit_timeout: float = 12.0     # Timeout de base
    max_retries: int = 3                 # Tentatives max
    scramble_seed: int = 42              # Seed de scrambling (obfuscation légère)
    fragment_size: int = 32              # Taille de fragment (16–64)

    # --- Mémoire / intégrité ---
    parity_enabled: int = 1              # 0/1
    checksum_strength: int = 1           # 0=none, 1=simple, 2=stronger
    memory_dispersion: float = 0.3       # 0–1 : combien l'état est dispersé
    reconstruction_threshold: float = 0.6  # Fraction minimale pour reconstruire

    # Métadonnées d'évolution
    fitness: float = 0.0
    generation: int = 0
    id: str = field(default_factory=lambda: hashlib.md5(str(time.time()).encode()).hexdigest()[:8])

    def mutate(self, rate: float = 0.18, strength: float = 0.25) -> ProtocolGenome:
        """Retourne une copie mutée."""
        child = copy.deepcopy(self)
        child.id = hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:8]
        child.fitness = 0.0

        def maybe_mutate(val, lo, hi, is_int=False):
            if random.random() < rate:
                delta = random.gauss(0, strength * (hi - lo))
                new_val = val + delta
                new_val = max(lo, min(hi, new_val))
                return int(round(new_val)) if is_int else new_val
            return val

        child.redundancy = maybe_mutate(child.redundancy, 1.0, 6.0)
        child.interleave_depth = maybe_mutate(child.interleave_depth, 1, 8, is_int=True)
        child.ack_mode = maybe_mutate(child.ack_mode, 0, 2, is_int=True)
        child.retransmit_timeout = maybe_mutate(child.retransmit_timeout, 3.0, 40.0)
        child.max_retries = maybe_mutate(child.max_retries, 0, 8, is_int=True)
        child.scramble_seed = maybe_mutate(child.scramble_seed, 0, 9999, is_int=True)
        child.fragment_size = maybe_mutate(child.fragment_size, 16, 64, is_int=True)
        child.parity_enabled = maybe_mutate(child.parity_enabled, 0, 1, is_int=True)
        child.checksum_strength = maybe_mutate(child.checksum_strength, 0, 2, is_int=True)
        child.memory_dispersion = maybe_mutate(child.memory_dispersion, 0.0, 1.0)
        child.reconstruction_threshold = maybe_mutate(child.reconstruction_threshold, 0.3, 0.95)

        return child

    def crossover(self, other: ProtocolGenome) -> ProtocolGenome:
        """Crossover uniforme simple."""
        child = ProtocolGenome()
        child.id = hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:8]

        for attr in [
            "redundancy", "interleave_depth", "ack_mode", "retransmit_timeout",
            "max_retries", "scramble_seed", "fragment_size", "parity_enabled",
            "checksum_strength", "memory_dispersion", "reconstruction_threshold"
        ]:
            setattr(child, attr, getattr(self, attr) if random.random() < 0.5 else getattr(other, attr))

        return child

    def describe(self) -> str:
        return (
            f"id={self.id} | red={self.redundancy:.2f} inter={self.interleave_depth} "
            f"ack={self.ack_mode} to={self.retransmit_timeout:.1f} retries={self.max_retries} "
            f"frag={self.fragment_size} parity={self.parity_enabled} chk={self.checksum_strength} "
            f"disp={self.memory_dispersion:.2f} thr={self.reconstruction_threshold:.2f}"
        )


# ============================================================
# 3. ENCODAGE / DÉCODAGE (implémentation simplifiée du protocole)
# ============================================================

def simple_checksum(data: bytes, strength: int) -> bytes:
    if strength == 0:
        return b""
    if strength == 1:
        return bytes([sum(data) % 256])
    # strength 2 : un peu plus fort
    h = hashlib.blake2b(data, digest_size=4).digest()
    return h


def apply_scramble(data: bytes, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    mask = rng.integers(0, 256, size=len(data), dtype=np.uint8)
    return bytes(a ^ b for a, b in zip(data, mask))


def interleave(data: bytes, depth: int) -> bytes:
    if depth <= 1 or len(data) < depth:
        return data
    # Simple block interleaving
    cols = depth
    rows = (len(data) + cols - 1) // cols
    padded = data + b"\x00" * (rows * cols - len(data))
    matrix = [padded[i*cols:(i+1)*cols] for i in range(rows)]
    interleaved = bytearray()
    for c in range(cols):
        for r in range(rows):
            interleaved.append(matrix[r][c])
    return bytes(interleaved)


def deinterleave(data: bytes, depth: int, original_len: int) -> bytes:
    if depth <= 1 or len(data) < depth:
        return data[:original_len]
    cols = depth
    rows = (len(data) + cols - 1) // cols
    matrix = [[0] * cols for _ in range(rows)]
    idx = 0
    for c in range(cols):
        for r in range(rows):
            if idx < len(data):
                matrix[r][c] = data[idx]
                idx += 1
    deinter = bytearray()
    for r in range(rows):
        for c in range(cols):
            deinter.append(matrix[r][c])
    return bytes(deinter[:original_len])


def encode_message(payload: bytes, genome: ProtocolGenome) -> List[bytes]:
    """
    Transforme un payload en une liste de fragments/paquets
    selon le genome.
    """
    # Checksum
    chk = simple_checksum(payload, genome.checksum_strength)
    data = payload + chk

    # Scramble
    data = apply_scramble(data, genome.scramble_seed)

    # Interleave
    data = interleave(data, genome.interleave_depth)

    # Fragmentation + redondance
    frag_size = max(8, genome.fragment_size)
    fragments = []
    for i in range(0, len(data), frag_size):
        frag = data[i:i+frag_size]
        # Parité simple optionnelle
        if genome.parity_enabled:
            parity = bytes([sum(frag) % 256])
            frag = frag + parity

        # Redondance : on envoie plusieurs copies (arrondi stochastique)
        n_copies = max(1, int(round(genome.redundancy + random.uniform(-0.3, 0.3))))
        for _ in range(n_copies):
            # On ajoute un petit header : index + longueur originale approximative
            header = bytes([i // frag_size % 256, len(payload) % 256])
            fragments.append(header + frag)

    return fragments


def decode_message(received_packets: List[bytes], genome: ProtocolGenome, expected_payload_len: int) -> Optional[bytes]:
    """
    Tente de reconstruire le payload à partir des paquets reçus.
    Retourne None si reconstruction échoue sous le seuil.
    """
    if not received_packets:
        return None

    # Collecte des fragments par index
    buckets: Dict[int, List[bytes]] = {}
    for pkt in received_packets:
        if len(pkt) < 3:
            continue
        idx = pkt[0]
        frag = pkt[2:]
        buckets.setdefault(idx, []).append(frag)

    # Pour chaque index, on prend le fragment le plus "consensuel"
    # (version simplifiée : on prend le premier qui a une parité correcte si activée)
    reconstructed = bytearray()
    max_idx = max(buckets.keys()) if buckets else -1

    valid_frags = 0
    total_possible = max_idx + 1 if max_idx >= 0 else 0

    for idx in range(max_idx + 1):
        candidates = buckets.get(idx, [])
        chosen = None
        for cand in candidates:
            if genome.parity_enabled and len(cand) >= 2:
                data_part = cand[:-1]
                parity = cand[-1]
                if sum(data_part) % 256 == parity:
                    chosen = data_part
                    break
            else:
                chosen = cand
                break
        if chosen is not None:
            reconstructed.extend(chosen)
            valid_frags += 1

    if total_possible == 0:
        return None

    # Seuil de reconstruction (mémoire dispersée)
    ratio = valid_frags / max(1, total_possible)
    if ratio < genome.reconstruction_threshold:
        return None

    data = bytes(reconstructed)

    # De-interleave
    # On ne connaît pas parfaitement la longueur, approximation
    data = deinterleave(data, genome.interleave_depth, len(data))

    # De-scramble
    data = apply_scramble(data, genome.scramble_seed)

    # Vérification checksum
    if genome.checksum_strength > 0:
        chk_len = 1 if genome.checksum_strength == 1 else 4
        if len(data) < chk_len:
            return None
        payload = data[:-chk_len]
        received_chk = data[-chk_len:]
        expected_chk = simple_checksum(payload, genome.checksum_strength)
        if received_chk != expected_chk:
            return None
        return payload[:expected_payload_len]

    return data[:expected_payload_len]


# ============================================================
# 4. SIMULATION D'UNE COMMUNICATION
# ============================================================

def evaluate_protocol(
    genome: ProtocolGenome,
    env: HostileEnvironment,
    n_messages: int = 40,
    n_nodes: int = 4,
    payload_size: int = 48,
) -> float:
    """
    Évalue un genome dans l'environnement hostile.
    Retourne un score de fitness (plus haut = meilleur).
    """
    successful = 0
    total_latency = 0.0
    total_packets_sent = 0
    integrity_ok = 0

    for msg_idx in range(n_messages):
        # Payload aléatoire
        payload = bytes(np.random.randint(0, 256, size=payload_size, dtype=np.uint8))

        # Encode
        packets = encode_message(payload, genome)
        total_packets_sent += len(packets)

        # Transmission (on simule un broadcast simplifié vers un destinataire)
        received: List[bytes] = []
        latencies = []

        for pkt in packets:
            # Chance de panne de nœud (on ignore simplement le paquet)
            if random.random() < env.config.node_failure_prob:
                continue

            recv, lat = env.transmit(pkt, from_node=0, to_node=1)
            if recv is not None:
                received.append(recv)
                latencies.append(lat)

        # Décodage
        decoded = decode_message(received, genome, expected_payload_len=payload_size)

        if decoded is not None:
            successful += 1
            if decoded == payload:
                integrity_ok += 1
            if latencies:
                total_latency += float(np.mean(latencies))

        # Simulation très simplifiée des retries / ACK
        # (pour ne pas exploser le temps de calcul)
        if genome.ack_mode > 0 and decoded is None and genome.max_retries > 0:
            # Une seule tentative de retry pour la démo
            retry_packets = encode_message(payload, genome)
            total_packets_sent += len(retry_packets)
            for pkt in retry_packets:
                recv, lat = env.transmit(pkt, 0, 1)
                if recv is not None:
                    received.append(recv)
            decoded = decode_message(received, genome, payload_size)
            if decoded is not None and decoded == payload:
                successful += 1
                integrity_ok += 1

    # Métriques
    delivery_rate = successful / max(1, n_messages)
    integrity_rate = integrity_ok / max(1, n_messages)
    avg_overhead = total_packets_sent / max(1, n_messages)
    # Pénalité d'overhead (on veut de la redondance, mais pas trop)
    efficiency = 1.0 / (1.0 + max(0, avg_overhead - 3.0) * 0.15)

    # Fitness composite
    fitness = (
        0.55 * delivery_rate +
        0.30 * integrity_rate +
        0.15 * efficiency
    )

    # Bonus léger pour des stratégies de mémoire dispersée qui marchent
    if genome.memory_dispersion > 0.4 and integrity_rate > 0.5:
        fitness += 0.03

    return float(np.clip(fitness, 0.0, 1.0))


# ============================================================
# 5. BOUCLE ÉVOLUTIVE
# ============================================================

def create_initial_population(size: int) -> List[ProtocolGenome]:
    pop = []
    for _ in range(size):
        g = ProtocolGenome(
            redundancy=random.uniform(1.2, 4.5),
            interleave_depth=random.randint(1, 5),
            ack_mode=random.randint(0, 2),
            retransmit_timeout=random.uniform(5.0, 25.0),
            max_retries=random.randint(1, 5),
            scramble_seed=random.randint(0, 9999),
            fragment_size=random.choice([16, 24, 32, 40, 48]),
            parity_enabled=random.randint(0, 1),
            checksum_strength=random.randint(0, 2),
            memory_dispersion=random.uniform(0.1, 0.8),
            reconstruction_threshold=random.uniform(0.4, 0.85),
        )
        pop.append(g)
    return pop


def evolve(
    generations: int = 25,
    pop_size: int = 36,
    elite_size: int = 4,
    mutation_rate: float = 0.22,
    hostile_level: str = "medium",
    seed: int = 42,
) -> List[ProtocolGenome]:
    """
    Lance l'évolution.
    Retourne la population finale (triée par fitness décroissante).
    """
    random.seed(seed)
    np.random.seed(seed)

    # Config hostile selon le niveau
    if hostile_level == "light":
        conf = HostileConfig(bit_flip_prob=0.008, packet_drop_prob=0.06, adversarial_corruption_prob=0.01)
    elif hostile_level == "extreme":
        conf = HostileConfig(bit_flip_prob=0.045, packet_drop_prob=0.28, adversarial_corruption_prob=0.12, node_failure_prob=0.08)
    else:  # medium
        conf = HostileConfig()

    env = HostileEnvironment(conf, seed=seed)

    population = create_initial_population(pop_size)

    print("=" * 72)
    print("  AUTO-ÉVOLUTION DE PROTOCOLES — ENVIRONNEMENT HOSTILE")
    print("=" * 72)
    print(f"Générations : {generations} | Population : {pop_size} | Niveau : {hostile_level}")
    print(f"Config hostile → bitflip={conf.bit_flip_prob:.3f} drop={conf.packet_drop_prob:.2f} "
          f"adv={conf.adversarial_corruption_prob:.2f}")
    print("-" * 72)

    history = []

    for gen in range(generations):
        # Évaluation
        for ind in population:
            ind.fitness = evaluate_protocol(ind, env, n_messages=32)
            ind.generation = gen

        # Tri
        population.sort(key=lambda x: x.fitness, reverse=True)
        best = population[0]
        avg = float(np.mean([p.fitness for p in population]))
        history.append((gen, best.fitness, avg))

        print(f"Gen {gen:3d} | Best: {best.fitness:.4f} | Avg: {avg:.4f} | {best.describe()}")

        # Nouvelle population
        new_pop: List[ProtocolGenome] = []

        # Élites
        for i in range(elite_size):
            elite = copy.deepcopy(population[i])
            elite.id = hashlib.md5(str(time.time_ns() + i).encode()).hexdigest()[:8]
            new_pop.append(elite)

        # Remplissage par sélection + croisement + mutation
        while len(new_pop) < pop_size:
            # Tournament selection
            def tournament():
                candidates = random.sample(population, k=min(5, len(population)))
                return max(candidates, key=lambda x: x.fitness)

            parent1 = tournament()
            parent2 = tournament()

            if random.random() < 0.7:
                child = parent1.crossover(parent2)
            else:
                child = copy.deepcopy(parent1)

            child = child.mutate(rate=mutation_rate)
            new_pop.append(child)

        population = new_pop

    # Évaluation finale
    for ind in population:
        ind.fitness = evaluate_protocol(ind, env, n_messages=48)
    population.sort(key=lambda x: x.fitness, reverse=True)

    print("-" * 72)
    print("ÉVOLUTION TERMINÉE")
    print(f"Meilleur protocole final : fitness={population[0].fitness:.4f}")
    print(population[0].describe())
    print("=" * 72)

    return population, history


# ============================================================
# 6. POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Évolution de protocoles en environnement hostile")
    parser.add_argument("--generations", type=int, default=20, help="Nombre de générations")
    parser.add_argument("--pop", type=int, default=30, help="Taille de population")
    parser.add_argument("--hostile", choices=["light", "medium", "extreme"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    final_pop, history = evolve(
        generations=args.generations,
        pop_size=args.pop,
        hostile_level=args.hostile,
        seed=args.seed,
    )

    print("\n--- Top 5 protocoles émergents ---")
    for i, p in enumerate(final_pop[:5]):
        print(f"{i+1}. fitness={p.fitness:.4f} | {p.describe()}")
