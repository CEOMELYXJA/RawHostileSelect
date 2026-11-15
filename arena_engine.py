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
    # The old binary workload remains the default for existing API users.
    # The v4 interface explicitly selects one of the human-readable modes.
    message_kind: str = "random"
    message_language: str = "fr"

    def __post_init__(self):
        if not 2 <= self.population <= 100 or not 1 <= self.generations <= 1000:
            raise ValueError("population must be 2–100 and generations 1–1000")
        if self.difficulty not in ("light", "medium", "extreme"):
            raise ValueError("unknown difficulty")
        if not 1 <= self.messages <= 100 or not 1 <= self.payload_size <= 256:
            raise ValueError("messages must be 1–100 and payload_size 1–256")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("mutation_rate must be between 0 and 1")
        if self.message_kind not in ("random", "mixed", "phrase", "color", "code"):
            raise ValueError("unknown message kind")
        if self.message_language not in ("fr", "en"):
            raise ValueError("unknown message language")


# These are real UTF-8 payloads, not captions added to unrelated random data.
MESSAGE_SAMPLES = {
    "phrase": {
        "fr": ("J'ai mangé une pomme.", "Le petit chat dort ici.", "Une étoile brille ce soir."),
        "en": ("I ate a red apple.", "The little cat sleeps here.", "A star shines tonight."),
    },
    # A color is transmitted as its exact six-digit hexadecimal value.
    "color": {"fr": ("#FF6B8B", "#8BCFFB", "#A0D9A4"),
              "en": ("#FF6B8B", "#8BCFFB", "#A0D9A4")},
    "code": {"fr": ("0101-1010", "A7-B2-C9", "42-17-83"),
             "en": ("0101-1010", "A7-B2-C9", "42-17-83")},
}


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


def crowding_distance(front):
    """Assign NSGA-II distances without inventing boundaries for a tie.

    An objective that has the same value throughout the front provides no
    information about diversity and must not make arbitrary candidates into
    infinite-distance boundary points. This v4 implementation leaves the
    original v2 CLI untouched.
    """
    for individual in front:
        individual.crowding = 0.0
    for objective in ("delivery", "integrity", "efficiency", "resilience"):
        if not front:
            break
        ordered = sorted(front, key=lambda item: getattr(item.fitness, objective))
        low = getattr(ordered[0].fitness, objective)
        high = getattr(ordered[-1].fitness, objective)
        if high - low < 1e-9:
            continue
        ordered[0].crowding = ordered[-1].crowding = float("inf")
        for i in range(1, len(ordered) - 1):
            previous = getattr(ordered[i - 1].fitness, objective)
            following = getattr(ordered[i + 1].fitness, objective)
            ordered[i].crowding += (following - previous) / (high - low)


def _stage(node, path, before, after, checksum_failed=None):
    """A bounded preview of real stage bytes, with their full lengths."""
    limit = 64
    result = {"path": list(path), "op": node.op.name, "params": list(node.params),
              "before_hex": before[:limit].hex(), "after_hex": after[:limit].hex(),
              "before_bytes": len(before), "after_bytes": len(after),
              "truncated": len(before) > limit or len(after) > limit}
    if checksum_failed is not None:
        result["checksum_failed"] = checksum_failed
    return result


def _encode(node, payload, trace=None):
    """Encode in postorder and remember input lengths for exact inversion."""
    steps = []

    def visit(part, data, path):
        for i, child in enumerate(part.children):
            data = visit(child, data, path + (i,))
        original = data
        before = len(data)
        # Refuse oversized trees instead of consuming unbounded memory.
        if part.op == gp.Op.REPEAT:
            copies = max(1, min(5, int(part.params[0]) if part.params else 2))
            if before * copies > 20000:
                raise ValueError("encoded message exceeds the model limit")
        result = gp.apply_op(part.op, data, part.params)
        if len(result) > 20000:
            raise ValueError("encoded message exceeds the model limit")
        steps.append((part, before, path))
        if trace is not None:
            trace.append(_stage(part, path, original, result))
        return result

    return visit(node, payload, ()), steps


def _decode(data, steps, trace=None):
    """Undo recorded stages. Return decoded bytes and any failed checks.

    Repetition votes on individual bits; an even tie uses the first copy.
    Detection is not correction and checks can themselves be corrupted.
    """
    failed = False
    for node, input_length, path in reversed(steps):
        before = data
        stage_failed = None
        op, params = node.op, node.params
        if op in (gp.Op.ADD_PARITY, gp.Op.CHECKSUM):
            stage_failed = False
            strength = int(params[0]) if params else 1
            cut = 1 if op == gp.Op.ADD_PARITY or strength == 1 else 4
            if len(data) < cut:
                failed = stage_failed = True
                data = b""
            else:
                body, given = data[:-cut], data[-cut:]
                expected = (bytes([sum(body) % 256]) if cut == 1 else
                            hashlib.blake2b(body, digest_size=4).digest())
                stage_failed = given != expected
                failed |= stage_failed
                data = body
        elif op == gp.Op.REPEAT:
            n = max(1, min(5, int(params[0]) if params else 2))
            if len(data) != input_length * n:
                failed = True
                data = b""
                if trace is not None:
                    trace.append(_stage(node, path, before, data))
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
        if trace is not None:
            trace.append(_stage(node, path, before, data, stage_failed))
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
        self.lineage = {}
        with _random_lock:
            previous = random.getstate()
            try:
                random.setstate(self._random_state)
                self.population = gp.create_initial_population(config.population)
                for ind in self.population:
                    ind.id = self._id()
                    self._parents[ind.id] = []
                    self.lineage[ind.id] = {"id": ind.id, "birth_generation": 0,
                                            "parents": [], "tree": ind.tree.to_string(),
                                            "tree_data": tree_data(ind.tree)}
                self._random_state = random.getstate()
            finally:
                random.setstate(previous)

    def _id(self):
        value = f"P{self._next_id:05d}"
        self._next_id += 1
        return value

    def _message_payload(self):
        """Return the actual bytes, kind and text selected for one trial.

        The binary mode consumes exactly the same RNG calls as the v3 model.
        Text samples use strict UTF-8; no padding or hidden substitution occurs.
        """
        kind = self.config.message_kind
        if kind == "random":
            payload = self.rng.integers(0, 256, self.config.payload_size, dtype=np.uint8).tobytes()
            return payload, kind, None
        if kind == "mixed":
            kind = ("phrase", "color", "code")[int(self.rng.integers(0, 3))]
        samples = MESSAGE_SAMPLES[kind][self.config.message_language]
        text = samples[int(self.rng.integers(0, len(samples)))]
        return text.encode("utf-8"), kind, text

    def _transmit(self, individual, scenario, conf):
        rng = self.rng
        payload, message_kind, original_text = self._message_payload()
        event = {"type": "transmission", "individual_id": individual.id,
                 "scenario": scenario, "outcome": "lost", "bit_flips": 0,
                 "latency": None, "adversarial": False, "checksum_failed": False,
                 "message_kind": message_kind, "original_text": original_text,
                 "decoded_text": None, "payload_bytes": len(payload),
                 "original_hex": payload.hex(), "encoded_hex": "", "received_hex": None,
                 "decoded_hex": None, "sent_bytes": 0, "encode_steps": [],
                 "decode_steps": [], "bit_changes": [], "changed_bit_count": 0,
                 "bit_changes_truncated": False}
        try:
            encoded, steps = _encode(individual.tree, payload, event["encode_steps"])
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
        for byte_index, (before, after) in enumerate(zip(encoded, received)):
            changed = before ^ after
            if not changed:
                continue
            for bit_index in range(8):
                if changed & (1 << bit_index):
                    event["changed_bit_count"] += 1
                    if len(event["bit_changes"]) < 32:
                        event["bit_changes"].append({
                            "byte_index": byte_index, "bit_index": bit_index,
                            "before_bit": (before >> bit_index) & 1,
                            "after_bit": (after >> bit_index) & 1,
                            "before_byte": format(before, "08b"),
                            "after_byte": format(after, "08b")})
        event["bit_changes_truncated"] = event["changed_bit_count"] > len(event["bit_changes"])
        decoded, failed = _decode(received, steps, event["decode_steps"])
        event["received_hex"] = received.hex()
        event["decoded_hex"] = decoded.hex()
        if original_text is not None:
            try:
                event["decoded_text"] = decoded.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                # Keep the actual bytes in decoded_hex; never manufacture text.
                pass
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
        useful_bytes = sum(e["payload_bytes"] for e in baseline if e["outcome"] == "intact")
        useful_fraction = useful_bytes / sent if sent else 0.0
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
            crowding_distance(front)
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
        baseline = [event for event in events if event["scenario"] == "baseline"]
        stress = [event for event in events if event["scenario"] == "stress"]
        received = [event for event in baseline if event["latency"] is not None]
        sent = [event for event in baseline if event["sent_bytes"] > 0]
        total_bytes = sum(event["sent_bytes"] for event in baseline)
        summary["metrics"] = {
            "attempts": len(baseline), "sent_packets": len(sent), "received": len(received),
            "intact": sum(event["outcome"] == "intact" for event in baseline),
            "lost": sum(event["outcome"] == "lost" for event in baseline),
            "failures": sum(event["outcome"] == "failure" for event in baseline),
            "encoding_errors": sum(event["outcome"] == "encoding_error" for event in baseline),
            "sent_bytes": total_bytes,
            "bytes_per_payload_byte": (total_bytes / sum(event["payload_bytes"] for event in sent)) if sent else None,
            "mean_latency": sum(event["latency"] for event in received) / len(received) if received else None,
            "checksum_failures": sum(event["checksum_failed"] for event in baseline),
            "bit_flips": sum(event["bit_flips"] for event in baseline),
            "changed_bits": sum(event["changed_bit_count"] for event in baseline),
            "stress_attempts": len(stress),
            "stress_intact": sum(event["outcome"] == "intact" for event in stress),
        }
        summary["metrics"]["delivery"] = len(received) / len(baseline)
        summary["metrics"]["integrity"] = summary["metrics"]["intact"] / len(baseline)
        summary["metrics"]["resilience"] = summary["metrics"]["stress_intact"] / len(stress)
        summary["niches"] = {str(niche): sum(ind.niche_id == niche for ind in self.population)
                             for niche in sorted({ind.niche_id for ind in self.population})}
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
                parent_tree = p1.tree.to_string()
                donor_tree = p2.tree.to_string()
                tree = gp.crossover_trees(p1.tree, p2.tree) if crossed else p1.tree.copy()
                crossover_tree = tree.to_string()
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
                self.lineage[child.id] = {"id": child.id, "birth_generation": generation + 1,
                                          "parents": list(self._parents[child.id]),
                                          "tree": child.tree.to_string(),
                                          "tree_data": tree_data(child.tree)}
                if crossed:
                    events.append({"type": "crossover", "individual_id": child.id,
                                   "parents": [p1.id, p2.id], "before": parent_tree,
                                   "donor": donor_tree, "after": crossover_tree,
                                   "changed": crossover_tree != parent_tree})
                if mutated and tree.to_string() != before_mutation:
                    events.append({"type": "mutation", "individual_id": child.id,
                                   "parents": list(self._parents[child.id]),
                                   "before": before_mutation, "after": tree.to_string()})
                next_pop.append(child)
            self.population = next_pop
        snapshot = {"generation": generation, "individuals": individuals,
                    "events": events, "summary": summary}
        self.history.append(snapshot)
        return snapshot

    def export(self):
        return {"version": "4.0", "config": asdict(self.config),
                "lineage": self.lineage, "generations": self.history}
