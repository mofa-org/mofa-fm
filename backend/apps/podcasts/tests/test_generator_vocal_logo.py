import os
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings
from pydub import AudioSegment

from apps.podcasts.services.generator import _prepend_append_vocal_logo


class VocalLogoTests(SimpleTestCase):
    @staticmethod
    def _write_wav(path: str, duration_ms: int) -> None:
        AudioSegment.silent(duration=duration_ms).export(path, format="wav")

    def test_prepend_and_append_vocal_logo(self):
        with TemporaryDirectory() as tmpdir:
            start_path = os.path.join(tmpdir, "start.wav")
            end_path = os.path.join(tmpdir, "end.wav")
            self._write_wav(start_path, 300)
            self._write_wav(end_path, 500)

            with override_settings(
                BASE_DIR=tmpdir,
                MINIMAX_TTS={
                    "enable_vocal_logo": True,
                    "vocal_logo_start_path": start_path,
                    "vocal_logo_end_path": end_path,
                },
            ):
                body_audio = AudioSegment.silent(duration=1000)
                final_audio = _prepend_append_vocal_logo(body_audio)

            self.assertAlmostEqual(len(final_audio), 1800, delta=5)

    def test_missing_logo_files_are_skipped(self):
        with TemporaryDirectory() as tmpdir:
            with override_settings(
                BASE_DIR=tmpdir,
                MINIMAX_TTS={
                    "enable_vocal_logo": True,
                    "vocal_logo_start_path": os.path.join(tmpdir, "missing-start.wav"),
                    "vocal_logo_end_path": os.path.join(tmpdir, "missing-end.wav"),
                },
            ):
                body_audio = AudioSegment.silent(duration=1000)
                final_audio = _prepend_append_vocal_logo(body_audio)

            self.assertAlmostEqual(len(final_audio), 1000, delta=5)

    def test_disable_vocal_logo(self):
        with TemporaryDirectory() as tmpdir:
            start_path = os.path.join(tmpdir, "start.wav")
            end_path = os.path.join(tmpdir, "end.wav")
            self._write_wav(start_path, 300)
            self._write_wav(end_path, 500)

            with override_settings(
                BASE_DIR=tmpdir,
                MINIMAX_TTS={
                    "enable_vocal_logo": False,
                    "vocal_logo_start_path": start_path,
                    "vocal_logo_end_path": end_path,
                },
            ):
                body_audio = AudioSegment.silent(duration=1000)
                final_audio = _prepend_append_vocal_logo(body_audio)

            self.assertAlmostEqual(len(final_audio), 1000, delta=5)
