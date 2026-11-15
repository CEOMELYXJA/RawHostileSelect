"""Instrumented, reproducible Evolution Arena model.

The legacy CLI remains in hostile_protocol_evolution.py.  A step evaluates a
population, records the actual transmissions and creates the next population.
The four objectives have explicitly different meanings from v2; results from
the two versions must not be directly compared.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import random
import threading

import numpy as np
import hostile_protocol_evolution as gp


@dataclass
class ArenaConfig:
    population: int = 12
    generations: int = 20
    difficulty: str = "medium"
    seed: int = 42
    messages: int = 8
    payload_size: int = 16
    mutation_rate: float = 0.30

    def __post_init__(self):
        if not 2 <= self.population <= 100 or not 1 <= self.generations <= 1000:
            raise ValueError("population must be 2–100 and generations 1–1000")
        if self.difficulty not in ("light", "medium", "extreme"):
            raise ValueError("unknown difficulty")
        if not 1 <= self.messages <= 100 or not 1 <= self.payload_size <= 256:
            raise ValueError("messages must be 1–100 and payload_size 1–256")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("mutation_rate must be between 0 and 1")


def _config(level):
    if level == "light":
        return gp.HostileConfig(bit_flip_prob=.008, packet_drop_prob=.07,
                                adversarial_corruption_prob=.02)
    if level == "extreme":
        return gp.HostileConfig(bit_flip_prob=.04, packet_drop_prob=.25,
                                adversarial_corruption_prob=.10, node_failure_prob=.07)
    return gp.HostileConfig()


def tree_data(node):
    return {"op": node.op.name, "params": list(node.params),
            "children": [tree_data(child) for child in node.children]}


def _encode(node, payload):
    """Encode in postorder and remember input lengths for exact inversion."""
    steps = []

    def visit(part, data):
        for child in part.children:
            data = visit(child, data)
        before = len(data)
        # Refuse oversized trees instead of consuming unbounded memory.
        if part.op == gp.Op.REPEAT:
            copies = max(1, min(5, int(part.params[0]) if part.params else 2))
            if before * copies > 20000:
                raise ValueError("encoded message exceeds the model limit")
        result = gp.apply_op(part.op, data, part.params)
        if len(result) > 20000:
            raise ValueError("encoded message exceeds the model limit")
        steps.append((part, before))
        return result

    return visit(node, payload), steps


def _decode(data, steps):
    """Undo recorded stages. Return decoded bytes and any failed checks.

    Repetition votes on individual bits; an even tie uses the first copy.
    Detection is not correction and checks can themselves be corrupted.
    """
    failed = False
    for node, input_length in reversed(steps):
        op, params = node.op, node.params
        if op in (gp.Op.ADD_PARITY, gp.Op.CHECKSUM):
            strength = int(params[0]) if params else 1
            cut = 1 if op == gp.Op.ADD_PARITY or strength == 1 else 4
            if len(data) < cut:
                failed = True
                data = b""
            else:
                body, given = data[:-cut], data[-cut:]
                expected = (bytes([sum(body) % 256]) if cut == 1 else
                            hashlib.blake2b(body, digest_size=4).digest())
                failed |= given != expected
                data = body
        elif op == gp.Op.REPEAT:
            n = max(1, min(5, int(params[0]) if params else 2))
            if len(data) != input_length * n:
                failed = True
                data = b""
                continue
            chunks = [data[i * input_length:(i + 1) * input_length] for i in range(n)]
            result = bytearray(input_length)
            for i in range(input_length):
                for bit in range(8):
                    count = sum((chunk[i] >> bit) & 1 for chunk in chunks)
                    if count * 2 > n or (count * 2 == n and (chunks[0][i] >> bit) & 1):
                        result[i] |= 1 << bit
            data = bytes(result)
        elif op == gp.Op.INTERLEAVE:
            data = gp.try_inverse(op, data, params, input_length)
        elif op == gp.Op.PAD:
            data = data[:input_length]
        else:
            data = gp.try_inverse(op, data, params, input_length)
    return data, bool(failed)


_random_lock = threading.Lock()


class ArenaEngine:
    """Call step off the UI thread. Snapshots/export contain JSON-safe data."""
    def __init__(self, config: ArenaConfig):
        self.config = config
        # NumPy rejects negative integers; mapping into a fixed-width seed lets
        # the UI accept any signed integer while preserving reproducibility.
        self.rng = np.random.default_rng(config.seed % (1 << 128))
        self._random_state = random.Random(config.seed).getstate()
        self._next_id = 1
        self.history = []
        self._parents = {}
        with _random_lock:
            previous = random.getstate()
            try:
                random.setstate(self._random_state)
                self.population = gp.create_initial_population(config.population)
                for ind in self.population:
                    ind.id = self._id()
                    self._parents[ind.id] = []
                self._random_state = random.getstate()
            finally:
                random.setstate(previous)

    def _id(self):
        value = f"P{self._next_id:05d}"
        self._next_id += 1
        return value

    def _transmit(self, individual, scenario, conf):
        rng = self.rng
        payload = rng.integers(0, 256, self.config.payload_size, dtype=np.uint8).tobytes()
        event = {"type": "transmission", "individual_id": individual.id,
                 "scenario": scenario, "outcome": "lost", "bit_flips": 0,
                 "latency": None, "adversarial": False, "checksum_failed": False,
                 "original_hex": payload.hex(), "encoded_hex": "", "received_hex": None,
                 "decoded_hex": None, "sent_bytes": 0}
        try:
            encoded, steps = _encode(individual.tree, payload)
        except (ValueError, OverflowError, RecursionError):
            event["outcome"] = "encoding_error"
            return event
        event["encoded_hex"] = encoded.hex()
        if rng.random() < conf.node_failure_prob:
            event["outcome"] = "failure"
            return event
        # A node failure occurs before the packet enters the modeled network.
        # A packet dropped by the network was nevertheless sent.
        event["sent_bytes"] = len(encoded)
        if rng.random() < conf.packet_drop_prob:
            return event
        event["latency"] = float(np.clip(rng.normal(conf.latency_mean, conf.latency_std), .5, conf.max_latency))
        if rng.random() < conf.adversarial_corruption_prob:
            received = rng.integers(0, 256, len(encoded), dtype=np.uint8).tobytes()
            event["adversarial"] = True
        else:
            bits = rng.random((len(encoded), 8)) < conf.bit_flip_prob
            mask = np.packbits(bits, axis=1, bitorder="little").reshape(-1)
            received = bytes(a ^ int(b) for a, b in zip(encoded, mask))
            event["bit_flips"] = int(bits.sum())
        decoded, failed = _decode(received, steps)
        event["received_hex"] = received.hex()
        event["decoded_hex"] = decoded.hex()
        event["checksum_failed"] = failed
        event["outcome"] = "intact" if decoded == payload else "corrupted"
        return event

    def _evaluate(self, ind):
        baseline = [self._transmit(ind, "baseline", _config(self.config.difficulty))
                    for _ in range(self.config.messages)]
        stress = [self._transmit(ind, "stress", _config("extreme"))
                  for _ in range(max(2, self.config.messages // 2))]
        count = len(baseline)
        received = [e for e in baseline if e["received_hex"] is not None]
        intact = sum(e["outcome"] == "intact" for e in baseline)
        sent = sum(e["sent_bytes"] for e in baseline)
        latency = (sum(e["latency"] for e in received) / len(received)) if received else None
        # Useful-byte fraction penalizes transmission overhead; latency factor is
        # explicitly scaled by the model's max latency. Unreceived messages
        # contribute no useful bytes; it is a score, not a network throughput.
        useful_fraction = intact * self.config.payload_size / sent if sent else 0.0
        latency_factor = 1 / (1 + (latency / 40)) if latency is not None else 0.0
        delivery = len(received) / count
        integrity = intact / count
        efficiency = useful_fraction * latency_factor
        resilience = sum(e["outcome"] == "intact" for e in stress) / len(stress)
        ind.fitness = gp.FitnessVector(delivery, integrity, efficiency, resilience)
        stats = {"attempts": count, "received": len(received), "intact": intact,
                 "sent_bytes": sent, "mean_latency": latency,
                 "lost": sum(e["outcome"] == "lost" for e in baseline),
                 "failures": sum(e["outcome"] == "failure" for e in baseline),
                 "bit_flips": sum(e["bit_flips"] for e in baseline),
                 "stress_attempts": len(stress),
                 "stress_intact": sum(e["outcome"] == "intact" for e in stress)}
        return baseline + stress, stats

    def step(self):
        if len(self.history) >= self.config.generations:
            return None
        with _random_lock:
            previous = random.getstate()
            try:
                random.setstate(self._random_state)
                result = self._step()
                self._random_state = random.getstate()
                return result
            finally:
                random.setstate(previous)

    def _step(self):
        generation = len(self.history)
        events, stats = [], {}
        for ind in self.population:
            ind.generation = generation
            observations, stats[ind.id] = self._evaluate(ind)
            events.extend(observations)
        fronts = gp.fast_non_dominated_sort(self.population)
        for front in fronts:
            gp.crowding_distance(front)
        gp.assign_niches(self.population)
        individuals = []
        for ind in self.population:
            f = ind.fitness
            individuals.append({"id": ind.id, "tree": ind.tree.to_string(),
                                "tree_data": tree_data(ind.tree), "parents": list(self._parents[ind.id]),
                                "generation": generation, "rank": ind.rank,
                                "crowding": ind.crowding if math.isfinite(ind.crowding) else None,
                                "niche": ind.niche_id, "complexity": ind.complexity(),
                                "fitness": {"delivery": f.delivery, "integrity": f.integrity,
                                            "efficiency": f.efficiency, "resilience": f.resilience,
                                            "scalar": f.scalar()}, "stats": stats[ind.id]})
        scores = [p.fitness.scalar() for p in self.population]
        summary = {"best": max(scores), "average": sum(scores) / len(scores),
                   "best_id": max(self.population, key=lambda x: x.fitness.scalar()).id,
                   "front0": len(fronts[0]),
                   "diversity": len({p.tree.to_string() for p in self.population}) / len(self.population)}
        # Do not construct or claim a next generation after the final evaluation.
        if generation + 1 < self.config.generations:
            ranked = sorted(self.population, key=lambda x: (x.rank, -x.crowding, -x.fitness.scalar(), x.id))
            survivors = ranked[:max(1, self.config.population // 4)]
            next_pop = []
            for parent in survivors:
                elite = parent.copy()
                elite.id = parent.id
                next_pop.append(elite)
                events.append({"type": "selection", "individual_id": parent.id})
            for ind in self.population:
                if ind not in survivors:
                    events.append({"type": "elimination", "individual_id": ind.id})

            def tournament():
                candidates = random.sample(self.population, k=min(4, len(self.population)))
                return min(candidates, key=lambda x: (x.rank, -x.crowding, x.id))

            while len(next_pop) < self.config.population:
                p1, p2 = tournament(), tournament()
                crossed = random.random() < .65
                tree = gp.crossover_trees(p1.tree, p2.tree) if crossed else p1.tree.copy()
                before_mutation = tree.to_string()
                mutated = random.random() < self.config.mutation_rate
                if mutated:
                    tree = gp.mutate_tree(tree)
                # Bound size/depth to keep experiments safe and responsive.
                if tree.size() > 18 or tree.depth() > 8:
                    tree = p1.tree.copy()
                    crossed = mutated = False
                child = gp.Individual(tree=tree)
                child.id = self._id()
                self._parents[child.id] = [p1.id, p2.id] if crossed else [p1.id]
                if crossed:
                    events.append({"type": "crossover", "individual_id": child.id,
                                   "parents": [p1.id, p2.id]})
                if mutated and tree.to_string() != before_mutation:
                    events.append({"type": "mutation", "individual_id": child.id,
                                   "before": before_mutation, "after": tree.to_string()})
                next_pop.append(child)
            self.population = next_pop
        snapshot = {"generation": generation, "individuals": individuals,
                    "events": events, "summary": summary}
        self.history.append(snapshot)
        return snapshot

    def export(self):
        return {"version": "3.0", "config": asdict(self.config), "generations": self.history}
