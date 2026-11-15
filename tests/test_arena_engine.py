import json
import unittest

import hostile_protocol_evolution as gp
from arena_engine import ArenaConfig, ArenaEngine, _decode, _encode


class ArenaModelTests(unittest.TestCase):
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

    def test_zero_mutation_rate_does_not_emit_mutation(self):
        engine = ArenaEngine(ArenaConfig(population=8, generations=2, messages=1, mutation_rate=0))
        result = engine.step()
        self.assertFalse(any(e["type"] == "mutation" for e in result["events"]))

    def test_negative_seed_is_valid_and_repeatable(self):
        config = ArenaConfig(population=2, generations=1, messages=1, seed=-42)
        self.assertEqual(ArenaEngine(config).step(), ArenaEngine(config).step())


if __name__ == "__main__":
    unittest.main()
