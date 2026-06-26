import importlib.util
from pathlib import Path
import sys
import types

import pytest


CLIENT_DIR = Path(__file__).resolve().parents[1]


class FakeStream:
    def __init__(self):
        self.is_playing = True
        self.volume = 1.0


class FakeSoundCacher:
    def __init__(self):
        self.cache = {}
        self.refs = []

    def play(self, file_name, pan=0.0, volume=1.0, pitch=1.0):
        stream = FakeStream()
        stream.file_name = file_name
        stream.pan = pan
        stream.volume = volume
        stream.pitch = pitch
        self.refs.append(stream)
        return stream


def _load_sound_manager_module(monkeypatch):
    fake_sound_cacher = types.ModuleType("sound_cacher")
    fake_sound_cacher.SoundCacher = FakeSoundCacher
    monkeypatch.setitem(sys.modules, "sound_cacher", fake_sound_cacher)

    spec = importlib.util.spec_from_file_location(
        "sound_manager_under_test", CLIENT_DIR / "sound_manager.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sound_volume_updates_currently_playing_effects(monkeypatch):
    sound_manager = _load_sound_manager_module(monkeypatch)
    manager = sound_manager.SoundManager()

    manager.set_sound_volume(0.5)
    stream = manager.play("roll.ogg", volume=0.8)

    assert stream.volume == pytest.approx(0.4)

    manager.set_sound_volume(0.25)

    assert stream.volume == pytest.approx(0.2)


def test_sound_volume_can_mute_active_effects(monkeypatch):
    sound_manager = _load_sound_manager_module(monkeypatch)
    manager = sound_manager.SoundManager()
    stream = manager.play("notify.ogg", volume=1.0)

    manager.set_sound_volume(0)

    assert stream.volume == pytest.approx(0)
