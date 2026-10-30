"""Checks for the Week 4 evidence validator."""

import unittest

from check_week4 import extract, packet_loss, validate


class EvidenceTests(unittest.TestCase):
    def test_extract_keeps_one_observation_between_markers(self):
        session = "@W4:EMPTY@\nfirst\n@W4:HUB@\nsecond\n@W4:END@\n"
        self.assertEqual("first", extract(session, "EMPTY"))
        self.assertEqual("second", extract(session, "HUB"))

    def test_packet_loss_reads_ping_summary(self):
        output = "2 packets transmitted, 0 received, 100% packet loss, time 1000ms"
        self.assertEqual(100, packet_loss(output))
        self.assertEqual(0, packet_loss("2 packets transmitted, 2 received, 0% packet loss"))

    def test_missing_observations_fail_validation(self):
        errors = validate("@W4:EMPTY@\n2 packets transmitted, 0 received, 100% packet loss\n")
        self.assertTrue(any("HUB" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
