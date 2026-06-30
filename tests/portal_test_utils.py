from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

BACKEND_DIRS = {
    "admin": REPO_ROOT / "admin" / "backend",
    "editor": REPO_ROOT / "editor" / "backend",
    "user": REPO_ROOT / "user" / "backend",
    "trainer": REPO_ROOT / "trainer" / "backend",
    "coordinator": REPO_ROOT / "coordinator" / "backend",
    "superadmin": REPO_ROOT / "superadmin" / "backend",
    "admission": REPO_ROOT / "admission-center" / "backend",
    "registration": REPO_ROOT / "registration" / "backend",
}

MODULE_PREFIXES_TO_PURGE = (
    "core",
    "routers",
    "schemas",
    "main",
)


def ensure_test_env() -> None:
    os.environ.setdefault("SECRET_KEY", "codex-test-secret-key")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
    os.environ.setdefault("NTA_DEBUG", "1")


def purge_backend_modules() -> None:
    for name in list(sys.modules):
        if name in MODULE_PREFIXES_TO_PURGE or name.startswith(
            tuple(f"{prefix}." for prefix in MODULE_PREFIXES_TO_PURGE)
        ):
            sys.modules.pop(name, None)


def _is_repo_backend_path(path_entry: str) -> bool:
    try:
        path = Path(path_entry).resolve()
    except OSError:
        return False
    return path.name == "backend" and REPO_ROOT in path.parents


def load_backend(service: str) -> ModuleType:
    ensure_test_env()
    purge_backend_modules()

    backend_dir = BACKEND_DIRS[service]
    main_path = backend_dir / "main.py"
    unique_name = f"nta_test_{service}_main"
    original_sys_path = list(sys.path)

    try:
        sys.path = [entry for entry in sys.path if not _is_repo_backend_path(entry)]
        sys.path.insert(0, str(backend_dir))

        spec = importlib.util.spec_from_file_location(unique_name, main_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load backend module from {main_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path = original_sys_path


def loaded_module(name: str) -> ModuleType:
    module = sys.modules.get(name)
    if module is None:
        raise AssertionError(f"Expected module '{name}' to be loaded")
    return module


def noop(*args: Any, **kwargs: Any) -> None:
    return None


def maybe_patch_noop(monkeypatch, module: ModuleType, attribute: str) -> None:
    if hasattr(module, attribute):
        monkeypatch.setattr(module, attribute, noop)


def silence_backend_logging(monkeypatch, app_module: ModuleType) -> None:
    maybe_patch_noop(monkeypatch, app_module, "log_activity")


@dataclass
class FakeCursor:
    user_row: dict[str, Any] | None
    executed: list[tuple[str, Any]] = field(default_factory=list)
    lastrowid: int = 91

    def execute(self, query: str, params: Any = None) -> None:
        self.executed.append((" ".join(query.split()), params))

    def fetchone(self) -> dict[str, Any] | None:
        if self.user_row is None:
            return None
        return dict(self.user_row)

    def close(self) -> None:
        return None


@dataclass
class FakeDB:
    user_row: dict[str, Any] | None
    commit_calls: int = 0
    cursor_obj: FakeCursor = field(init=False)

    def __post_init__(self) -> None:
        self.cursor_obj = FakeCursor(self.user_row)

    def cursor(self, dictionary: bool = False) -> FakeCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.commit_calls += 1

    def close(self) -> None:
        return None


def build_user_row(
    *,
    role: str,
    email: str,
    national_id: str = "29001011234567",
    full_name: str = "Test User",
    user_id: int = 7,
    password_hash: str = "hashed-password",
) -> dict[str, Any]:
    return {
        "id": user_id,
        "full_name_ar": full_name,
        "email": email,
        "role": role,
        "national_id": national_id,
        "password_hash": password_hash,
    }
