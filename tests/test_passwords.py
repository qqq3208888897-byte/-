import unittest

from wzlcli.passwords import DEFAULT_PASSWORD, PasswordError, resolve_password


class PasswordPolicyTests(unittest.TestCase):
    def test_default_password_is_tried(self):
        self.assertEqual(resolve_password(lambda value: value == DEFAULT_PASSWORD), DEFAULT_PASSWORD)

    def test_supplied_password_wins(self):
        self.assertEqual(resolve_password(lambda value: value == "secret", supplied="secret"), "secret")

    def test_prompt_after_default_fails(self):
        prompts = iter(["secret"])
        self.assertEqual(resolve_password(lambda value: value == "secret", prompt=lambda _: next(prompts)), "secret")

    def test_three_failed_prompts_raise(self):
        with self.assertRaises(PasswordError):
            resolve_password(lambda _: False, prompt=lambda _: "wrong")
