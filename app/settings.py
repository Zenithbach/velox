# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# ⚙️ settings.py
# Your preferences, loaded from a TOML file that lives at ~/.config/velox/velox.toml.
# First run? No config file? No problem — we'll create one with sane defaults.
# Edit the file, restart the app, done. No settings UI needed (yet).

import os
import copy
import toml

from app.constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG


class Settings:
    """
    Loads, saves, and provides access to user configuration.

    Behaves like a nested dict but with dot-access convenience methods.
    Falls back to defaults for anything missing — your config file
    doesn't need every key, just the ones you've changed.
    """

    def __init__(self):
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._ensure_config_dir()
        self._load()

    # ─── Public API ──────────────────────────────────────────────────────

    def get(self, section: str, key: str, fallback=None):
        """
        Grab a config value. Examples:
            settings.get("window", "width")       → 1200
            settings.get("zoom", "level")          → 1.0
            settings.get("made_up", "nope", 42)    → 42
        """
        try:
            return self._config[section][key]
        except KeyError:
            return fallback

    def set(self, section: str, key: str, value):
        """
        Update a config value in memory. Call save() to persist.
        Creates the section if it doesn't exist, because life's too short
        for KeyErrors.
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    def save(self):
        """Write current config to disk. Overwrites the whole file."""
        try:
            with open(CONFIG_FILE, "w") as f:
                toml.dump(self._config, f)
        except OSError as e:
            # If we can't save config, that's annoying but not fatal.
            # The app still works with in-memory settings.
            print(f"⚠️  Couldn't save config: {e}")
            print("   Your settings are fine in memory, just won't persist.")

    def get_section(self, section: str) -> dict:
        """Get a whole section as a dict. Returns empty dict if missing."""
        return self._config.get(section, {})

    @property
    def raw(self) -> dict:
        """The full config dict. Use get() instead unless you have a reason."""
        return self._config

    # ─── Internal ────────────────────────────────────────────────────────

    def _ensure_config_dir(self):
        """
        Create the config directory if it doesn't exist.
        Permissions: 700 — owner only. Your sessions, your business.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Lock it down. 700 = only you can read/write/list.
        # This matters because session cookies live nearby.
        try:
            os.chmod(CONFIG_DIR, 0o700)
        except OSError:
            # If we can't set permissions (weird filesystem?), warn but continue.
            print(f"⚠️  Couldn't set permissions on {CONFIG_DIR}")
            print("   Consider checking directory permissions manually.")

    def _load(self):
        """
        Load config from disk, merging with defaults.
        Missing file → write defaults.
        Missing keys → filled from defaults.
        Extra keys → kept (forward compatibility).
        """
        if CONFIG_FILE.exists():
            try:
                user_config = toml.load(CONFIG_FILE)
                self._merge(self._config, user_config)
            except toml.TomlDecodeError as e:
                print(f"⚠️  Config file is mangled: {e}")
                print(f"   Using defaults. You might want to check {CONFIG_FILE}")
        else:
            # First run! Welcome aboard. 🦋
            print(f"📝 First run detected — creating config at {CONFIG_FILE}")
            self.save()

    def _merge(self, base: dict, override: dict):
        """
        Deep merge override into base.
        Override wins for individual values.
        Base provides anything the override is missing.
        """
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                self._merge(base[key], value)
            else:
                base[key] = value
