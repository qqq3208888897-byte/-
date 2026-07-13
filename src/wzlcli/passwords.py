from __future__ import annotations

import getpass
from dataclasses import dataclass
from typing import Callable


DEFAULT_PASSWORD = "V8M2"
MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class EncryptionPolicy:
    """Default resource conversion policy: decrypt input and encrypt output."""

    decrypt_input: bool = True
    encrypt_output: bool = True
    input_password: str = DEFAULT_PASSWORD
    output_password: str = DEFAULT_PASSWORD

    @classmethod
    def default(cls) -> "EncryptionPolicy":
        return cls()


class PasswordError(RuntimeError):
    pass


def resolve_password(
    verify: Callable[[str], bool],
    supplied: str | None = None,
    prompt: Callable[[str], str] = getpass.getpass,
) -> str:
    """Use V8M2 first, then interactively retry up to three times."""
    candidates: list[str] = []
    if supplied is not None:
        candidates.append(supplied)
    if DEFAULT_PASSWORD not in candidates:
        candidates.append(DEFAULT_PASSWORD)
    for candidate in candidates:
        if verify(candidate):
            return candidate

    for attempt in range(MAX_ATTEMPTS):
        candidate = prompt("资源密码：")
        if verify(candidate):
            return candidate
    raise PasswordError("密码验证失败，已超过最大尝试次数")
