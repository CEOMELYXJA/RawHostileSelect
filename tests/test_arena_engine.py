import json
import math
import unittest
from unittest.mock import patch

import hostile_protocol_evolution as gp
from arena_engine import ArenaConfig, ArenaEngine, _decode, _encode, crowding_distance


class ArenaModelTests(unittest.TestCase):
    def test_constant_objectives_do_not_make_arbitrary_boundaries(self):
        # The first and last items here are interior compromise points. A
        # constant delivery objective must not give them infinite crowding.
        values = [(0.5, 0.33, 0.67, 0), (0.5, 0, 1, 0),
                  (0.5, 1, 0, 0), (0.5, 0.67, 0.33, 0)]
        front = [gp.Individual(gp.Node(gp.Op.IDENTITY), gp.FitnessVector(*fitness),
                               id=str(index))
                 for index, fitness in enumerate(values)]
        crowding_distance(front)
        by_id = {item.id: item.crowding for item in front}
        self.assertTrue(math.isinf(by_id['1']))
        self.assertTrue(math.isinf(by_id['2']))
        self.assertTrue(math.isfinite(by_id['0']))
        self.assertTrue(math.isfinite(by_id['3']))

    def test_operations_round_trip_without_noise(self):
        payload = b"ABCDE"  # exercises interleave padding
        examples = [
            gp.Node(gp.Op.IDENTITY), gp.Node(gp.Op.SCRAMBLE, [1570]),
            gp.Node(gp.Op.INTERLEAVE, [3]), gp.Node(gp.Op.ADD_PARITY),
            gp.Node(gp.Op.CHECKSUM, [1]), gp.Node(gp.Op.CHECKSUM, [2]),
            gp.Node(gp.Op.REPEAT, [4]), gp.Node(gp.Op.FRAGMENT, [16]),
            gp.Node(gp.Op.PAD, [127]), gp.Node(gp.Op.XOR_CONST, [170]),
            gp.Node(gp.Op.REVERSE),
            gp.Node(gp.Op.INTERLEAVE, [3], [gp.Node(gp.Op.ADD_PARITY)]),
        ]
        for node in examples:
            with self.subTest(operation=node.op):
                encoded, steps = _encode(node, payload)
                actual, failed = _decode(encoded, steps)
                self.assertEqual(actual, payload)
                self.assertFalse(failed)

    def test_checksums_detect_a_changed_byte(self):
        for node in [gp.Node(gp.Op.ADD_PARITY), gp.Node(gp.Op.CHECKSUM, [1]),
                     gp.Node(gp.Op.CHECKSUM, [2])]:
            encoded, steps = _encode(node, b"hello")
            damaged = bytes([encoded[0] ^ 1]) + encoded[1:]
            decoded, failed = _decode(damaged, steps)
            self.assertTrue(failed)
            self.assertNotEqual(decoded, b"hello")

    def test_repeat_uses_all_copies(self):
        encoded, steps = _encode(gp.Node(gp.Op.REPEAT, [3]), b"hello")
        damaged = bytes([encoded[0] ^ 1]) + encoded[1:]
        decoded, _ = _decode(damaged, steps)
        self.assertEqual(decoded, b"hello")

    def test_stage_trace_reconstructs_real_operation_sequence(self):
        node = gp.Node(gp.Op.REVERSE, [], [gp.Node(gp.Op.XOR_CONST, [1])])
        encoding, decoding = [], []
        encoded, steps = _encode(node, b"AB", encoding)
        decoded, failed = _decode(encoded, steps, decoding)
        self.assertEqual(decoded, b"AB")
        self.assertFalse(failed)
        self.assertEqual([s["path"] for s in encoding], [[0], []])
        self.assertEqual([s["path"] for s in decoding], [[], [0]])
        self.assertEqual(encoding[0]["before_hex"], b"AB".hex())
        self.assertEqual(encoding[0]["after_hex"], bytes([64, 67]).hex())
        self.assertEqual(encoding[-1]["after_hex"], encoded.hex())
        self.assertEqual(decoding[-1]["after_hex"], decoded.hex())

    def test_stage_previews_signal_truncation(self):
        stages = []
        _encode(gp.Node(gp.Op.IDENTITY), b"a" * 65, stages)
        self.assertTrue(stages[0]["truncated"])
        self.assertEqual(stages[0]["before_bytes"], 65)
        self.assertEqual(len(bytes.fromhex(stages[0]["before_hex"])), 64)

    def test_bit_events_match_actual_encoded_and_received_data(self):
        engine = ArenaEngine(ArenaConfig(population=2, generations=1, messages=1, payload_size=8))
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        noise = gp.HostileConfig(bit_flip_prob=1, packet_drop_prob=0,
                                 adversarial_corruption_prob=0, node_failure_prob=0)
        event = engine._transmit(individual, "baseline", noise)
        self.assertEqual(event["bit_flips"], 64)
        self.assertEqual(event["changed_bit_count"], 64)
        self.assertEqual(len(event["bit_changes"]), 32)
        self.assertTrue(event["bit_changes_truncated"])
        first = event["bit_changes"][0]
        before = bytes.fromhex(event["encoded_hex"])[first["byte_index"]]
        after = bytes.fromhex(event["received_hex"])[first["byte_index"]]
        self.assertEqual(first["before_byte"], format(before, "08b"))
        self.assertEqual(first["after_byte"], format(after, "08b"))
        self.assertNotEqual(first["before_bit"], first["after_bit"])

    def test_genealogy_and_operator_events_are_consistent(self):
        config = ArenaConfig(population=16, generations=2, messages=1, mutation_rate=1, seed=22)
        engine = ArenaEngine(config)
        first = engine.step()
        events = first["events"]
        children = engine.export()["lineage"]
        crossovers = [event for event in events if event["type"] == "crossover"]
        mutations = [event for event in events if event["type"] == "mutation"]
        self.assertTrue(crossovers)
        self.assertTrue(mutations)
        for event in crossovers:
            child = children[event["individual_id"]]
            self.assertEqual(event["parents"], child["parents"])
            self.assertEqual(event["before"], children[event["parents"][0]]["tree"])
            self.assertEqual(event["donor"], children[event["parents"][1]]["tree"])
            self.assertEqual(event["changed"], event["before"] != event["after"])
        for event in mutations:
            self.assertEqual(event["after"], children[event["individual_id"]]["tree"])
            self.assertEqual(event["parents"], children[event["individual_id"]]["parents"])
        next_gen = engine.step()
        for individual in next_gen["individuals"]:
            self.assertIn(individual["id"], children)

    def test_noiseless_and_failure_outcomes_come_from_model(self):
        engine = ArenaEngine(ArenaConfig(population=2, generations=1, messages=2))
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        clean = gp.HostileConfig(bit_flip_prob=0, packet_drop_prob=0,
                                 adversarial_corruption_prob=0, node_failure_prob=0)
        event = engine._transmit(individual, "baseline", clean)
        self.assertEqual(event["outcome"], "intact")
        self.assertEqual(event["original_hex"], event["decoded_hex"])
        clean.node_failure_prob = 1
        failed = engine._transmit(individual, "baseline", clean)
        self.assertEqual(failed["outcome"], "failure")
        self.assertEqual(failed["sent_bytes"], 0)
        clean.node_failure_prob = 0
        clean.packet_drop_prob = 1
        lost = engine._transmit(individual, "baseline", clean)
        self.assertEqual(lost["outcome"], "lost")
        self.assertEqual(lost["sent_bytes"], len(bytes.fromhex(lost["encoded_hex"])))

    def test_reproducibility_and_json_export(self):
        config = ArenaConfig(population=4, generations=2, messages=3, seed=73)
        first, second = ArenaEngine(config), ArenaEngine(config)
        for _ in range(2):
            self.assertEqual(first.step(), second.step())
        self.assertIsNone(first.step())
        json.dumps(first.export(), allow_nan=False)

    def test_metrics_match_recorded_events(self):
        engine = ArenaEngine(ArenaConfig(population=3, generations=1, messages=4))
        snapshot = engine.step()
        for ind in snapshot["individuals"]:
            ev = [e for e in snapshot["events"] if e["type"] == "transmission"
                  and e["individual_id"] == ind["id"]]
            base = [e for e in ev if e["scenario"] == "baseline"]
            stress = [e for e in ev if e["scenario"] == "stress"]
            self.assertEqual(ind["fitness"]["delivery"], sum(e["received_hex"] is not None for e in base) / len(base))
            self.assertEqual(ind["fitness"]["integrity"], sum(e["outcome"] == "intact" for e in base) / len(base))
            self.assertEqual(ind["fitness"]["resilience"], sum(e["outcome"] == "intact" for e in stress) / len(stress))
            self.assertEqual(ind["stats"]["sent_bytes"], sum(e["sent_bytes"] for e in base))
        metrics = snapshot["summary"]["metrics"]
        baseline = [e for e in snapshot["events"] if e["scenario"] == "baseline"]
        self.assertEqual(metrics["attempts"], len(baseline))
        self.assertEqual(metrics["received"], sum(e["received_hex"] is not None for e in baseline))
        self.assertEqual(metrics["changed_bits"], sum(e["changed_bit_count"] for e in baseline))
        self.assertEqual(sum(snapshot["summary"]["niches"].values()), 3)

    def test_every_transmission_trace_and_bit_count_matches_observations(self):
        engine = ArenaEngine(ArenaConfig(population=6, generations=2, messages=3, seed=8))
        for _ in range(2):
            snapshot = engine.step()
            population = {individual["id"]: individual for individual in snapshot["individuals"]}
            transmissions = [event for event in snapshot["events"] if event["type"] == "transmission"]
            for event in transmissions:
                self.assertIn(event["individual_id"], population)
                for step in event["encode_steps"] + event["decode_steps"]:
                    node = population[event["individual_id"]]["tree_data"]
                    for child_index in step["path"]:
                        node = node["children"][child_index]
                    self.assertEqual(step["op"], node["op"])
                    self.assertEqual(step["params"], node["params"])
                if event["received_hex"] is None:
                    self.assertIsNone(event["latency"])
                    self.assertEqual(event["decode_steps"], [])
                    continue
                encoded = bytes.fromhex(event["encoded_hex"])
                received = bytes.fromhex(event["received_hex"])
                count = sum(bin(a ^ b).count("1") for a, b in zip(encoded, received))
                self.assertEqual(event["changed_bit_count"], count)
                self.assertIsNotNone(event["latency"])
                self.assertEqual(event["outcome"] == "intact",
                                 event["decoded_hex"] == event["original_hex"])
                self.assertEqual(event["encode_steps"][-1]["after_hex"], event["encoded_hex"][:128])
                self.assertEqual(event["decode_steps"][-1]["after_hex"], event["decoded_hex"][:128])

    def test_zero_mutation_rate_does_not_emit_mutation(self):
        engine = ArenaEngine(ArenaConfig(population=8, generations=2, messages=1, mutation_rate=0))
        result = engine.step()
        self.assertFalse(any(e["type"] == "mutation" for e in result["events"]))

    def test_negative_seed_is_valid_and_repeatable(self):
        config = ArenaConfig(population=2, generations=1, messages=1, seed=-42)
        self.assertEqual(ArenaEngine(config).step(), ArenaEngine(config).step())

    def test_readable_messages_are_real_utf8_payloads(self):
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        clean = gp.HostileConfig(bit_flip_prob=0, packet_drop_prob=0,
                                 adversarial_corruption_prob=0, node_failure_prob=0)
        for language in ("fr", "en"):
            for kind in ("phrase", "color", "code"):
                with self.subTest(language=language, kind=kind):
                    engine = ArenaEngine(ArenaConfig(population=2, generations=1,
                                                    message_kind=kind, message_language=language))
                    event = engine._transmit(individual, "baseline", clean)
                    payload = event["original_text"].encode("utf-8")
                    self.assertEqual(event["message_kind"], kind)
                    self.assertEqual(event["original_hex"], payload.hex())
                    self.assertEqual(event["decoded_hex"], payload.hex())
                    self.assertEqual(event["decoded_text"], event["original_text"])
                    self.assertEqual(event["payload_bytes"], len(payload))
                    if kind == "color":
                        self.assertRegex(event["original_text"], r"^#[0-9A-F]{6}$")

    def test_corrupted_or_lost_text_is_never_invented(self):
        engine = ArenaEngine(ArenaConfig(population=2, generations=1,
                                        message_kind="phrase", message_language="fr"))
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        all_bits = gp.HostileConfig(bit_flip_prob=1, packet_drop_prob=0,
                                    adversarial_corruption_prob=0, node_failure_prob=0)
        damaged = engine._transmit(individual, "baseline", all_bits)
        self.assertEqual(damaged["outcome"], "corrupted")
        self.assertIsNone(damaged["decoded_text"])
        self.assertNotEqual(damaged["decoded_hex"], damaged["original_hex"])
        self.assertIsNotNone(damaged["received_hex"])
        all_bits.packet_drop_prob = 1
        lost = engine._transmit(individual, "baseline", all_bits)
        self.assertEqual(lost["outcome"], "lost")
        self.assertIsNone(lost["decoded_text"])
        self.assertIsNone(lost["decoded_hex"])
        self.assertIsNone(lost["received_hex"])

    def test_mixed_workload_is_reproducible_and_records_all_kinds(self):
        config = ArenaConfig(population=6, generations=2, messages=8, seed=31,
                             message_kind="mixed", message_language="fr")
        first, second = ArenaEngine(config), ArenaEngine(config)
        one, two = first.step(), second.step()
        self.assertEqual(one, two)
        transmissions = [e for e in one["events"] if e["type"] == "transmission"]
        self.assertEqual({e["message_kind"] for e in transmissions}, {"phrase", "color", "code"})
        for event in transmissions:
            self.assertEqual(event["original_text"].encode("utf-8").hex(), event["original_hex"])
            if event["decoded_text"] is not None:
                self.assertEqual(event["decoded_text"].encode("utf-8").hex(), event["decoded_hex"])
        self.assertEqual(first.export()["config"]["message_kind"], "mixed")
        self.assertEqual(first.export()["version"], "4.0")

    def test_variable_length_costs_use_actual_message_bytes(self):
        engine = ArenaEngine(ArenaConfig(population=6, generations=1, messages=8, seed=11,
                                         message_kind="mixed", message_language="fr"))
        snapshot = engine.step()
        for individual in snapshot["individuals"]:
            base = [event for event in snapshot["events"]
                    if event["type"] == "transmission" and event["scenario"] == "baseline"
                    and event["individual_id"] == individual["id"]]
            sent = sum(e["sent_bytes"] for e in base)
            useful = sum(e["payload_bytes"] for e in base if e["outcome"] == "intact")
            latency = individual["stats"]["mean_latency"]
            expected = useful / sent / (1 + latency / 40) if sent and latency is not None else 0
            self.assertAlmostEqual(individual["fitness"]["efficiency"], expected)
            self.assertLessEqual(individual["fitness"]["efficiency"], 1)
        baseline = [e for e in snapshot["events"] if e["scenario"] == "baseline"]
        sent_events = [e for e in baseline if e["sent_bytes"] > 0]
        expected_ratio = sum(e["sent_bytes"] for e in sent_events) / sum(e["payload_bytes"] for e in sent_events)
        self.assertAlmostEqual(snapshot["summary"]["metrics"]["bytes_per_payload_byte"], expected_ratio)

    def test_invalid_message_options_rejected(self):
        with self.assertRaises(ValueError):
            ArenaConfig(message_kind="unknown")
        with self.assertRaises(ValueError):
            ArenaConfig(message_language="xx")

    def test_missing_invalid_and_empty_decoding_are_distinct(self):
        engine = ArenaEngine(ArenaConfig(population=2, generations=1,
                                        message_kind="phrase", message_language="fr"))
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        conf = gp.HostileConfig(bit_flip_prob=0, packet_drop_prob=0,
                                adversarial_corruption_prob=0, node_failure_prob=1)
        failure = engine._transmit(individual, "baseline", conf)
        self.assertEqual((failure["outcome"], failure["decoded_hex"], failure["decoded_text"]),
                         ("failure", None, None))
        conf.node_failure_prob = 0
        conf.packet_drop_prob = 1
        lost = engine._transmit(individual, "baseline", conf)
        self.assertEqual((lost["outcome"], lost["decoded_hex"], lost["decoded_text"]),
                         ("lost", None, None))
        conf.packet_drop_prob = 0
        conf.bit_flip_prob = 1
        invalid = engine._transmit(individual, "baseline", conf)
        self.assertEqual(invalid["outcome"], "corrupted")
        self.assertIsNotNone(invalid["decoded_hex"])
        self.assertIsNone(invalid["decoded_text"])
        conf.bit_flip_prob = 0
        # If a decoder yields zero bytes, the exact result is an empty string,
        # which must not be confused with absent or invalid UTF-8 data.
        with patch("arena_engine._decode", return_value=(b"", False)):
            empty = engine._transmit(individual, "baseline", conf)
        self.assertEqual((empty["outcome"], empty["decoded_hex"], empty["decoded_text"]),
                         ("corrupted", "", ""))

    def test_encoding_error_has_original_but_no_arrival(self):
        engine = ArenaEngine(ArenaConfig(population=2, generations=1, message_kind="color"))
        individual = gp.Individual(gp.Node(gp.Op.IDENTITY))
        with patch("arena_engine._encode", side_effect=ValueError("size limit")):
            event = engine._transmit(individual, "baseline", gp.HostileConfig())
        self.assertEqual(event["outcome"], "encoding_error")
        self.assertIsNotNone(event["original_text"])
        self.assertIsNone(event["received_hex"])
        self.assertIsNone(event["decoded_hex"])
        self.assertIsNone(event["decoded_text"])
        self.assertEqual(event["sent_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
