"""Checks for the Week 4 evidence validator."""

import unittest

from check_week4 import extract, packet_loss, validate


class EvidenceTests(unittest.TestCase):
    def test_extract_keeps_one_observation_between_markers(self):
        session = "mininet> @W4:EMPTY@\nmininet> first\nmininet> mininet> @W4:HUB@\nsecond\nmininet> @W4:END@\n"
        self.assertEqual("mininet> first", extract(session, "EMPTY"))
        self.assertEqual("second", extract(session, "HUB"))

    def test_packet_loss_reads_ping_summary(self):
        output = "2 packets transmitted, 0 received, 100% packet loss, time 1000ms"
        self.assertEqual(100, packet_loss(output))
        self.assertEqual(0, packet_loss("2 packets transmitted, 2 received, 0% packet loss"))

    def test_missing_observations_fail_validation(self):
        errors = validate("@W4:EMPTY@\n2 packets transmitted, 0 received, 100% packet loss\n")
        self.assertTrue(any("HUB" in error for error in errors), errors)

    def test_disconnected_status_accepts_ovs_table_spacing(self):
        session = "mininet> @W4:DISCONNECTED_STATUS@\nmininet> is_connected        : false\nmininet> @W4:END@\n"
        errors = validate(session)
        self.assertFalse(any("DISCONNECTED_STATUS" in error for error in errors), errors)

    def test_empty_switch_must_have_no_forwarding_rule(self):
        session = "@W4:EMPTY_FLOW@\nNXST_FLOW reply:\n actions=FLOOD\n@W4:END@\n"
        errors = validate(session)
        self.assertTrue(any("EMPTY_FLOW" in error for error in errors), errors)

    def test_learning_capture_must_report_zero_packets(self):
        session = "@W4:LEARNING_CAPTURE@\ntcpdump: interface not found\n@W4:END@\n"
        errors = validate(session)
        self.assertTrue(any("LEARNING_CAPTURE" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
