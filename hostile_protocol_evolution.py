#!/usr/bin/env python3
"""
RawHostileSelect
================
Self-evolving protocols through natural selection
in an extremely hostile environment.

v2 — Genetic programming (operation trees)
   + Multi-objective selection and niches

Let protocols evolve through simulated selection.
Surviving structures need not resemble TCP, files, or pages.
"""

from __future__ import annotations

import copy
import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# ============================================================
# 0. PROJECT IDENTITY
# ============================================================

PROJECT_NAME = "RawHostileSelect"
VERSION = "2.0.0"

# ============================================================
# 1. HOSTILE ENVIRONMENT
# ============================================================

@dataclass
class HostileConfig:
    bit_flip_prob: float = 0.02
    packet_drop_prob: float = 0.15
    latency_mean: float = 8.0
    latency_std: float = 6.0
    adversarial_corruption_prob: float = 0.05
    node_failure_prob: float = 0.03
    max_latency: float = 40.0


class HostileEnvironment:
    def __init__(self, config: HostileConfig, seed: Optional[int] = None):
        self.config = config
        self.rng = np.random.default_rng(seed)

    def transmit(self, packet: bytes) -> Tuple[Optional[bytes], float]:
        if self.rng.random() < self.config.packet_drop_prob:
            return None, 0.0

        latency = float(np.clip(
            self.rng.normal(self.config.latency_mean, self.config.latency_std),
            0.5, self.config.max_latency
        ))

        if self.rng.random() < self.config.adversarial_corruption_prob:
            corrupted = bytes(self.rng.integers(0, 256, size=len(packet), dtype=np.uint8))
            return corrupted, latency

        data = bytearray(packet)
        for i in range(len(data)):
            for bit in range(8):
                if self.rng.random() < self.config.bit_flip_prob:
                    data[i] ^= (1 << bit)
        return bytes(data), latency


# ============================================================
# 2. GENETIC PROGRAMMING — Operations and Trees
# ============================================================

class Op(Enum):
    """Primitive operations available for building a protocol."""
    IDENTITY = auto()
    SCRAMBLE = auto()
    INTERLEAVE = auto()
    ADD_PARITY = auto()
    CHECKSUM = auto()
    REPEAT = auto()          # redundancy
    FRAGMENT = auto()
    PAD = auto()
    XOR_CONST = auto()
    REVERSE = auto()


# Arity and typical parameters
OP_ARITY = {
    Op.IDENTITY: 0,
    Op.SCRAMBLE: 1,      # seed
    Op.INTERLEAVE: 1,    # depth
    Op.ADD_PARITY: 0,
    Op.CHECKSUM: 1,      # strength 1 or 2
    Op.REPEAT: 1,        # n copies
    Op.FRAGMENT: 1,      # fragment size
    Op.PAD: 1,           # pad value
    Op.XOR_CONST: 1,     # constant
    Op.REVERSE: 0,
}


@dataclass
class Node:
    """Node in a genetic-programming protocol tree."""
    op: Op
    params: List[float] = field(default_factory=list)
    children: List["Node"] = field(default_factory=list)

    def copy(self) -> "Node":
        return Node(
            op=self.op,
            params=list(self.params),
            children=[c.copy() for c in self.children]
        )

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(c.depth() for c in self.children)

    def flatten(self) -> List["Node"]:
        nodes = [self]
        for c in self.children:
            nodes.extend(c.flatten())
        return nodes

    def to_string(self, indent: int = 0) -> str:
        pstr = ",".join(f"{p:.1f}" for p in self.params) if self.params else ""
        s = "  " * indent + f"{self.op.name}({pstr})"
        for c in self.children:
            s += "\n" + c.to_string(indent + 1)
        return s


def random_param(op: Op) -> List[float]:
    if op == Op.SCRAMBLE:
        return [float(random.randint(0, 9999))]
    if op == Op.INTERLEAVE:
        return [float(random.randint(1, 6))]
    if op == Op.CHECKSUM:
        return [float(random.choice([1, 2]))]
    if op == Op.REPEAT:
        return [float(random.randint(1, 4))]
    if op == Op.FRAGMENT:
        return [float(random.choice([16, 24, 32, 40, 48]))]
    if op == Op.PAD:
        return [float(random.randint(0, 255))]
    if op == Op.XOR_CONST:
        return [float(random.randint(0, 255))]
    return []


def random_node(max_depth: int = 3, current_depth: int = 0) -> Node:
    """Generate a random node and optionally its children."""
    if current_depth >= max_depth or random.random() < 0.35:
        # Leaf
        op = random.choice([Op.IDENTITY, Op.SCRAMBLE, Op.ADD_PARITY, Op.REVERSE, Op.XOR_CONST])
        return Node(op=op, params=random_param(op))

    op = random.choice(list(Op))
    node = Node(op=op, params=random_param(op))

    # Most operations are stacked sequentially (one child).
    # REPEAT and FRAGMENT are also unary in this simplified model.
    if random.random() < 0.7 and current_depth + 1 < max_depth:
        node.children = [random_node(max_depth, current_depth + 1)]
    return node


def random_tree(max_depth: int = 4) -> Node:
    return random_node(max_depth=max_depth)


# ---------- Tree execution (encode) ----------

def apply_op(op: Op, data: bytes, params: List[float]) -> bytes:
    if op == Op.IDENTITY or not data:
        return data

    if op == Op.SCRAMBLE:
        seed = int(params[0]) if params else 42
        rng = np.random.default_rng(seed)
        mask = rng.integers(0, 256, size=len(data), dtype=np.uint8)
        return bytes(a ^ b for a, b in zip(data, mask))

    if op == Op.INTERLEAVE:
        depth = max(1, int(params[0]) if params else 2)
        if depth <= 1 or len(data) < depth:
            return data
        cols = depth
        rows = (len(data) + cols - 1) // cols
        padded = data + b"\x00" * (rows * cols - len(data))
        matrix = [padded[i * cols:(i + 1) * cols] for i in range(rows)]
        out = bytearray()
        for c in range(cols):
            for r in range(rows):
                out.append(matrix[r][c])
        return bytes(out)

    if op == Op.ADD_PARITY:
        parity = bytes([sum(data) % 256])
        return data + parity

    if op == Op.CHECKSUM:
        strength = int(params[0]) if params else 1
        if strength == 1:
            return data + bytes([sum(data) % 256])
        h = hashlib.blake2b(data, digest_size=4).digest()
        return data + h

    if op == Op.REPEAT:
        n = max(1, min(5, int(params[0]) if params else 2))
        return data * n

    if op == Op.FRAGMENT:
        # This simplified model does not actually fragment data;
        # the upper layer would handle fragmentation.
        return data

    if op == Op.PAD:
        val = int(params[0]) if params else 0
        return data + bytes([val % 256])

    if op == Op.XOR_CONST:
        const = int(params[0]) if params else 0
        return bytes(b ^ (const % 256) for b in data)

    if op == Op.REVERSE:
        return data[::-1]

    return data


def execute_tree(node: Node, data: bytes) -> bytes:
    """Execute the tree bottom-up (post-order)."""
    # Process children first.
    current = data
    for child in node.children:
        current = execute_tree(child, current)
    # Then apply the node operation.
    return apply_op(node.op, current, node.params)


# ---------- Approximate decoding (heuristic inverse) ----------

def try_inverse(op: Op, data: bytes, params: List[float], original_len: int) -> bytes:
    """Attempt inversion (not always perfect, allowing selection)."""
    if not data:
        return data

    if op == Op.SCRAMBLE:
        # Scramble is self-inverse with the same seed.
        return apply_op(Op.SCRAMBLE, data, params)

    if op == Op.REVERSE:
        return data[::-1]

    if op == Op.XOR_CONST:
        return apply_op(Op.XOR_CONST, data, params)

    if op == Op.ADD_PARITY:
        if len(data) >= 1:
            return data[:-1]
        return data

    if op == Op.CHECKSUM:
        strength = int(params[0]) if params else 1
        cut = 1 if strength == 1 else 4
        if len(data) >= cut:
            return data[:-cut]
        return data

    if op == Op.REPEAT:
        n = max(1, int(params[0]) if params else 2)
        chunk = len(data) // n
        if chunk > 0:
            return data[:chunk]
        return data

    if op == Op.INTERLEAVE:
        # Approximate inverse
        depth = max(1, int(params[0]) if params else 2)
        if depth <= 1:
            return data
        cols = depth
        rows = (len(data) + cols - 1) // cols
        matrix = [[0] * cols for _ in range(rows)]
        idx = 0
        for c in range(cols):
            for r in range(rows):
                if idx < len(data):
                    matrix[r][c] = data[idx]
                    idx += 1
        out = bytearray()
        for r in range(rows):
            for c in range(cols):
                out.append(matrix[r][c])
        return bytes(out[:original_len])

    return data


def decode_tree(node: Node, data: bytes, original_len: int) -> bytes:
    """Decode by reversing the tree operations."""
    # Reverse the node operation first, then its children in reverse order.
    current = try_inverse(node.op, data, node.params, original_len)
    for child in reversed(node.children):
        current = decode_tree(child, current, original_len)
    return current


# ============================================================
# 3. GP INDIVIDUAL + MULTI-OBJECTIVE
# ============================================================

@dataclass
class FitnessVector:
    delivery: float = 0.0      # delivery rate
    integrity: float = 0.0     # data integrity
    efficiency: float = 0.0    # low overhead
    resilience: float = 0.0    # resistance to extreme conditions

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.delivery, self.integrity, self.efficiency, self.resilience)

    def dominates(self, other: "FitnessVector") -> bool:
        """Return true if this fitness dominates the other (Pareto)."""
        better_or_equal = all(a >= b for a, b in zip(self.as_tuple(), other.as_tuple()))
        strictly_better = any(a > b for a, b in zip(self.as_tuple(), other.as_tuple()))
        return better_or_equal and strictly_better

    def scalar(self, weights: Optional[Sequence[float]] = None) -> float:
        w = weights or (0.40, 0.30, 0.15, 0.15)
        t = self.as_tuple()
        return sum(wi * ti for wi, ti in zip(w, t))


@dataclass
class Individual:
    tree: Node
    fitness: FitnessVector = field(default_factory=FitnessVector)
    rank: int = 0                  # Pareto rank
    crowding: float = 0.0
    niche_id: int = 0
    generation: int = 0
    id: str = field(default_factory=lambda: hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:10])

    def copy(self) -> "Individual":
        ind = Individual(tree=self.tree.copy())
        ind.fitness = copy.deepcopy(self.fitness)
        ind.rank = self.rank
        ind.crowding = self.crowding
        ind.niche_id = self.niche_id
        ind.generation = self.generation
        return ind

    def complexity(self) -> int:
        return self.tree.size()

    def describe(self) -> str:
        return (f"id={self.id} rank={self.rank} crowd={self.crowding:.2f} "
                f"fit=({self.fitness.delivery:.2f},{self.fitness.integrity:.2f},"
                f"{self.fitness.efficiency:.2f},{self.fitness.resilience:.2f}) "
                f"size={self.complexity()}")


# ---------- Genetic operators ----------

def mutate_tree(node: Node, rate: float = 0.25) -> Node:
    node = node.copy()
    nodes = node.flatten()
    target = random.choice(nodes)

    r = random.random()
    if r < 0.40:
        # Change the operation.
        target.op = random.choice(list(Op))
        target.params = random_param(target.op)
    elif r < 0.70:
        # Change the parameters.
        target.params = random_param(target.op)
    elif r < 0.90 and target.children:
        # Replace a subtree.
        idx = random.randint(0, len(target.children) - 1)
        target.children[idx] = random_node(max_depth=2)
    else:
        # Add or remove a child.
        if target.children and random.random() < 0.5:
            target.children.pop(random.randint(0, len(target.children) - 1))
        elif len(target.children) < 2:
            target.children.append(random_node(max_depth=2))

    return node


def crossover_trees(a: Node, b: Node) -> Node:
    """Exchange subtrees."""
    child = a.copy()
    nodes_a = child.flatten()
    nodes_b = b.flatten()
    if not nodes_a or not nodes_b:
        return child

    # Choose an exchange point in the child.
    target = random.choice(nodes_a)
    donor = random.choice(nodes_b).copy()

    # Replace the target operation, parameters, and children with the donor.
    target.op = donor.op
    target.params = list(donor.params)
    target.children = [c.copy() for c in donor.children]
    return child


# ============================================================
# 4. EVALUATION
# ============================================================

def evaluate_individual(
    ind: Individual,
    env: HostileEnvironment,
    n_messages: int = 28,
    payload_size: int = 40,
) -> FitnessVector:
    successful = 0
    integrity_ok = 0
    total_sent = 0
    total_received = 0

    for _ in range(n_messages):
        payload = bytes(np.random.randint(0, 256, size=payload_size, dtype=np.uint8))

        # Encode with the tree.
        try:
            encoded = execute_tree(ind.tree, payload)
        except Exception:
            encoded = payload

        # Simulate packets; REPEAT in the tree provides implicit redundancy.
        packets = [encoded]
        # REPEAT has already increased the encoded length, if present.
        total_sent += len(packets)

        received = []
        for pkt in packets:
            if random.random() < env.config.node_failure_prob:
                continue
            recv, _ = env.transmit(pkt)
            if recv is not None:
                received.append(recv)
                total_received += 1

        if not received:
            continue

        # Take the first received packet and attempt to decode it.
        try:
            decoded = decode_tree(ind.tree, received[0], payload_size)
            decoded = decoded[:payload_size]
        except Exception:
            decoded = b""

        if len(decoded) >= payload_size // 2:  # at least partially recovered
            successful += 1
            if decoded == payload:
                integrity_ok += 1

    delivery = successful / max(1, n_messages)
    integrity = integrity_ok / max(1, n_messages)

    # Efficiency penalizes large or redundant trees.
    size_penalty = min(1.0, ind.complexity() / 18.0)
    efficiency = max(0.0, 1.0 - size_penalty * 0.6)

    # Approximate resilience is derived from delivery and integrity.
    # This legacy score is not an independent stress test.
    resilience = delivery * 0.7 + integrity * 0.3
    if ind.complexity() > 12:
        resilience *= 0.85

    return FitnessVector(
        delivery=float(np.clip(delivery, 0, 1)),
        integrity=float(np.clip(integrity, 0, 1)),
        efficiency=float(np.clip(efficiency, 0, 1)),
        resilience=float(np.clip(resilience, 0, 1)),
    )


# ============================================================
# 5. MULTI-OBJECTIVE + NICHES (simplified NSGA-II + speciation)
# ============================================================

def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    fronts: List[List[Individual]] = [[]]
    for p in population:
        p.rank = 0
        dominated_count = 0
        dominated_set = []
        for q in population:
            if p.fitness.dominates(q.fitness):
                dominated_set.append(q)
            elif q.fitness.dominates(p.fitness):
                dominated_count += 1
        if dominated_count == 0:
            p.rank = 0
            fronts[0].append(p)
        # Store temporary sorting data.
        p._dominated_count = dominated_count  # type: ignore
        p._dominated_set = dominated_set      # type: ignore

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in p._dominated_set:  # type: ignore
                q._dominated_count -= 1  # type: ignore
                if q._dominated_count == 0:  # type: ignore
                    q.rank = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    # Clean up temporary sorting data.
    for p in population:
        if hasattr(p, "_dominated_count"):
            del p._dominated_count
        if hasattr(p, "_dominated_set"):
            del p._dominated_set

    return [f for f in fronts if f]


def crowding_distance(front: List[Individual]) -> None:
    if not front:
        return
    n = len(front)
    for ind in front:
        ind.crowding = 0.0

    objectives = ["delivery", "integrity", "efficiency", "resilience"]
    for obj in objectives:
        front.sort(key=lambda x: getattr(x.fitness, obj))
        front[0].crowding = float("inf")
        front[-1].crowding = float("inf")
        lo = getattr(front[0].fitness, obj)
        hi = getattr(front[-1].fitness, obj)
        if hi - lo < 1e-9:
            continue
        for i in range(1, n - 1):
            dist = (getattr(front[i + 1].fitness, obj) - getattr(front[i - 1].fitness, obj)) / (hi - lo)
            front[i].crowding += dist


def assign_niches(population: List[Individual], n_niches: int = 6) -> None:
    """Simple speciation based on tree size and operation signature."""
    if not population:
        return

    def signature(ind: Individual) -> Tuple:
        ops = tuple(sorted(n.op.name for n in ind.tree.flatten()))
        return (ind.complexity() // 3, ops[:4])

    groups: Dict[Tuple, List[Individual]] = {}
    for ind in population:
        sig = signature(ind)
        groups.setdefault(sig, []).append(ind)

    # Assign niche IDs.
    niche_list = list(groups.values())
    for i, group in enumerate(niche_list):
        nid = i % n_niches
        for ind in group:
            ind.niche_id = nid


# ============================================================
# 6. EVOLUTION LOOP
# ============================================================

def create_initial_population(size: int, max_depth: int = 4) -> List[Individual]:
    return [Individual(tree=random_tree(max_depth=max_depth)) for _ in range(size)]


def evolve(
    generations: int = 20,
    pop_size: int = 40,
    elite_per_front: int = 3,
    mutation_rate: float = 0.30,
    hostile_level: str = "medium",
    seed: int = 42,
) -> Tuple[List[Individual], List[Tuple]]:
    random.seed(seed)
    np.random.seed(seed)

    if hostile_level == "light":
        conf = HostileConfig(bit_flip_prob=0.008, packet_drop_prob=0.07, adversarial_corruption_prob=0.02)
    elif hostile_level == "extreme":
        conf = HostileConfig(bit_flip_prob=0.04, packet_drop_prob=0.25, adversarial_corruption_prob=0.10, node_failure_prob=0.07)
    else:
        conf = HostileConfig()

    env = HostileEnvironment(conf, seed=seed)
    population = create_initial_population(pop_size)

    print("=" * 78)
    print(f"  {PROJECT_NAME} v{VERSION} — Genetic Programming + Multi-Objective + Niches")
    print("=" * 78)
    print(f"Generations: {generations} | Population : {pop_size} | Hostile : {hostile_level}")
    print(f"bitflip={conf.bit_flip_prob:.3f} drop={conf.packet_drop_prob:.2f} adv={conf.adversarial_corruption_prob:.2f}")
    print("-" * 78)

    history = []

    for gen in range(generations):
        # Evaluation
        for ind in population:
            ind.fitness = evaluate_individual(ind, env)
            ind.generation = gen

        # Pareto sorting and crowding
        fronts = fast_non_dominated_sort(population)
        for front in fronts:
            crowding_distance(front)

        # Niches
        assign_niches(population)

        # Best scalar score for the log
        best = max(population, key=lambda x: x.fitness.scalar())
        avg_scalar = float(np.mean([p.fitness.scalar() for p in population]))
        history.append((gen, best.fitness.scalar(), avg_scalar))

        print(f"Gen {gen:3d} | Best scalar: {best.fitness.scalar():.4f} | Avg: {avg_scalar:.4f} | "
              f"Front0: {len(fronts[0]) if fronts else 0} | {best.describe()}")

        # New population
        new_pop: List[Individual] = []

        # Keep the leading fronts (Pareto elitism).
        for front in fronts:
            front_sorted = sorted(front, key=lambda x: (-x.crowding, -x.fitness.scalar()))
            for ind in front_sorted[:elite_per_front]:
                if len(new_pop) < pop_size:
                    elite = ind.copy()
                    elite.id = hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:10]
                    new_pop.append(elite)
            if len(new_pop) >= pop_size // 2:
                break

        # Fill by selection, crossover, and mutation.
        def tournament():
            candidates = random.sample(population, k=min(4, len(population)))
            # Prefer low rank, then high crowding.
            return min(candidates, key=lambda x: (x.rank, -x.crowding))

        while len(new_pop) < pop_size:
            p1 = tournament()
            p2 = tournament()
            if random.random() < 0.65:
                child_tree = crossover_trees(p1.tree, p2.tree)
            else:
                child_tree = p1.tree.copy()
            child_tree = mutate_tree(child_tree, rate=mutation_rate)
            child = Individual(tree=child_tree)
            new_pop.append(child)

        population = new_pop

    # Final evaluation
    for ind in population:
        ind.fitness = evaluate_individual(ind, env, n_messages=36)
    fronts = fast_non_dominated_sort(population)
    for front in fronts:
        crowding_distance(front)
    assign_niches(population)

    population.sort(key=lambda x: (x.rank, -x.crowding, -x.fitness.scalar()))

    print("-" * 78)
    print("EVOLUTION COMPLETE")
    print(f"Selected individual (Pareto order): {population[0].describe()}")
    print("\nSelected protocol tree:")
    print(population[0].tree.to_string())
    print("=" * 78)

    return population, history


# ============================================================
# 7. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — GP + Multi-objective")
    parser.add_argument("--generations", type=int, default=15)
    parser.add_argument("--pop", type=int, default=32)
    parser.add_argument("--hostile", choices=["light", "medium", "extreme"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    final_pop, history = evolve(
        generations=args.generations,
        pop_size=args.pop,
        hostile_level=args.hostile,
        seed=args.seed,
    )

    print("\n--- Pareto front (rank 0) — Top individuals ---")
    rank0 = [p for p in final_pop if p.rank == 0]
    for i, p in enumerate(rank0[:8]):
        print(f"{i+1}. {p.describe()}")
        print(p.tree.to_string())
        print()
