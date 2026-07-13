import unittest

from wzlcli.passwords import DEFAULT_PASSWORD, EncryptionPolicy


class EncryptionPolicyTests(unittest.TestCase):
    def test_default_conversion_decrypts_and_encrypts(self):
        policy = EncryptionPolicy.default()
        self.assertTrue(policy.decrypt_input)
        self.assertTrue(policy.encrypt_output)
        self.assertEqual(policy.input_password, DEFAULT_PASSWORD)
        self.assertEqual(policy.output_password, DEFAULT_PASSWORD)

    def test_policy_can_disable_both_sides(self):
        policy = EncryptionPolicy(False, False, "", "")
        self.assertFalse(policy.decrypt_input)
        self.assertFalse(policy.encrypt_output)
