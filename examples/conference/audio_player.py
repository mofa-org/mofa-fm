#!/usr/bin/env python3
"""
Multi-Input Circular Buffer Audio Player with Backpressure Control.
Accepts 3 audio inputs (student1, student2, tutor) and concatenates them into one stream.
Sends buffer fullness percentage for external flow control.
"""

import argparse
import os
import time
import threading
import signal
import sys
import numpy as np
import pyarrow as pa
from dora import Node
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'node-hub', 'dora-common'))
from dora_common.logging import send_log, get_log_level_from_env
import sounddevice as sd


class CircularAudioBuffer:
    """Thread-safe circular buffer for audio streaming."""

    def __init__(self, size_seconds=360, sample_rate=32000):
        self.sample_rate = sample_rate
        self.buffer_size = int(size_seconds * sample_rate)
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)

        self.write_pos = 0
        self.read_pos = 0
        self.available_samples = 0

        self.lock = threading.Lock()

        self.total_written = 0
        self.total_read = 0
        self.underruns = 0
        self.overruns = 0

    def write(self, audio_data: np.ndarray, participant: str = None) -> int:
        """Write audio data to the circular buffer. Concatenates in arrival order."""
        with self.lock:
            data_len = len(audio_data)

            if self.available_samples + data_len > self.buffer_size:
                self.overruns += 1
                overflow = (self.available_samples + data_len) - self.buffer_size
                self.read_pos = (self.read_pos + overflow) % self.buffer_size
                self.available_samples -= overflow
                pass  # print(f"[Buffer] Overrun! Skipping {overflow} samples (from {participant})")

            samples_written = 0
            while samples_written < data_len:
                chunk_size = min(data_len - samples_written, self.buffer_size - self.write_pos)
                end_pos = self.write_pos + chunk_size
                self.buffer[self.write_pos:end_pos] = audio_data[samples_written:samples_written + chunk_size]
                self.write_pos = end_pos % self.buffer_size
                samples_written += chunk_size

            self.available_samples = min(self.available_samples + data_len, self.buffer_size)
            self.total_written += data_len
            return data_len

    def read(self, num_samples: int) -> np.ndarray:
        """Read samples from the circular buffer for playback."""
        with self.lock:
            if self.available_samples < num_samples:
                # Partial read - return what we have plus zeros
                actual_samples = self.available_samples
                output = np.zeros(num_samples, dtype=np.float32)

                if actual_samples > 0:
                    samples_read = 0
                    while samples_read < actual_samples:
                        chunk_size = min(actual_samples - samples_read, self.buffer_size - self.read_pos)
                        end_pos = self.read_pos + chunk_size
                        output[samples_read:samples_read + chunk_size] = self.buffer[self.read_pos:end_pos]
                        self.read_pos = end_pos % self.buffer_size
                        samples_read += chunk_size

                    self.available_samples = 0
                    self.total_read += actual_samples

                if actual_samples < num_samples:
                    self.underruns += 1

                return output
            else:
                # Full read
                output = np.zeros(num_samples, dtype=np.float32)
                samples_read = 0

                while samples_read < num_samples:
                    chunk_size = min(num_samples - samples_read, self.buffer_size - self.read_pos)
                    end_pos = self.read_pos + chunk_size
                    output[samples_read:samples_read + chunk_size] = self.buffer[self.read_pos:end_pos]
                    self.read_pos = end_pos % self.buffer_size
                    samples_read += chunk_size

                self.available_samples -= num_samples
                self.total_read += num_samples
                return output

    def get_stats(self):
        """Get buffer statistics."""
        with self.lock:
            buffer_fill_percentage = (self.available_samples / self.buffer_size) * 100 if self.buffer_size > 0 else 0
            available_seconds = self.available_samples / self.sample_rate if self.sample_rate > 0 else 0

            return {
                'available_samples': self.available_samples,
                'available_seconds': available_seconds,
                'buffer_size': self.buffer_size,
                'buffer_fill': buffer_fill_percentage,
                'underruns': self.underruns,
                'overruns': self.overruns,
                'total_written': self.total_written,
                'total_read': self.total_read,
            }

    def reset(self):
        """Reset buffer state."""
        with self.lock:
            self.write_pos = 0
            self.read_pos = 0
            self.available_samples = 0
            self.total_written = 0
            self.total_read = 0


class CircularBufferAudioPlayer:
    """Audio player with circular buffer and playback control."""

    def __init__(self, buffer_seconds=360, sample_rate=32000, blocksize=2048):
        self.buffer = CircularAudioBuffer(size_seconds=buffer_seconds, sample_rate=sample_rate)
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.stream = None
        self.is_playing = False

    def audio_callback(self, outdata, frames, time_info, status):
        """Callback for sounddevice stream."""
        if status:
            pass  # print(f"[Audio Callback] Status: {status}")

        data = self.buffer.read(frames)
        outdata[:, 0] = data

    def start(self):
        """Start the audio stream."""
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.blocksize,
                callback=self.audio_callback
            )
            self.stream.start()

    def set_sample_rate(self, new_rate):
        """Update sample rate if changed."""
        if new_rate != self.sample_rate:
            self.sample_rate = new_rate
            self.buffer.sample_rate = new_rate
            pass  # print(f"[Audio Player] Sample rate updated to {new_rate} Hz")

    def add_audio(self, audio_data, participant=None):
        """Add audio data to buffer. Concatenates from all participants."""
        self.buffer.write(audio_data, participant)

    def pause(self):
        """Pause playback."""
        self.is_playing = False

    def resume(self):
        """Resume playback."""
        self.is_playing = True

    def reset(self):
        """Reset the audio buffer."""
        self.pause()
        self.buffer.reset()
        pass  # print("[Audio Player] Buffer reset to empty")


shutdown_flag = threading.Event()

def signal_handler(signum, frame):
    pass  # print("\n[Multi-Audio Player] Shutting down...")
    shutdown_flag.set()


def main():
    # Read buffer size from environment variable with fallback
    default_buffer_seconds = int(os.getenv("BUFFER_SECONDS", "360"))

    parser = argparse.ArgumentParser(description="Multi-input circular buffer audio player")
    parser.add_argument("--sample-rate", type=int, default=32000,
                        help="Initial playback sample rate (Hz)")
    parser.add_argument("--buffer-seconds", type=int, default=default_buffer_seconds,
                        help="Buffer capacity in seconds")
    parser.add_argument("--blocksize", type=int, default=2048,
                        help="Audio callback blocksize")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    player = None
    try:
        node = Node("audio-player")
        player = CircularBufferAudioPlayer(
            buffer_seconds=args.buffer_seconds,
            sample_rate=args.sample_rate,
            blocksize=args.blocksize,
        )
        player.start()

        # Clear screen and show banner
        # print("\033[2J\033[H", end="")
        # print("=" * 60)
        # print("MULTI-INPUT CIRCULAR BUFFER AUDIO PLAYER")
        # print("=" * 60)
        # print(f"Buffer: {args.buffer_seconds} seconds")
        # print(f"Inputs: student1, student2, tutor")
        # print("Audio streams concatenated in arrival order (FIFO)")
        # print("Outputs buffer percentage for backpressure control")
        # print("=" * 60 + "\n")

        # State
        playback_started = False

        # Dynamically track participants based on actual inputs
        # Initialize with empty dicts - will populate on first event from each participant
        segments_per_participant = {}
        last_question_id = {}
        completed_sessions = set()

        # Smart reset state
        reset_question_id = None  # Expected question_id after reset
        filtering_mode = False     # Whether to filter by question_id

        # Timing
        last_status_time = time.time()
        status_interval = 1.0  # Send status every second

        # Get configurable timeout from environment
        node_timeout_ms = int(os.getenv("NODE_TIMEOUT_MS", "1000"))
        node_timeout = node_timeout_ms / 1000.0

        # Get log level from environment
        log_level = get_log_level_from_env()

        # Send startup log
        send_log(node, "INFO", "🔊 Audio Player initialized - Ready for audio streams", "audio-player")

        while not shutdown_flag.is_set():
            # Process events with timeout
            try:
                event = node.next(timeout=node_timeout)
            except KeyboardInterrupt:
                break
            except Exception:
                event = None

            # Handle control input for reset/cancel (accept both "control" and "reset" as input names)
            if event and event["type"] == "INPUT" and event["id"] in ["control", "reset"]:
                try:
                    send_log(node, "INFO", "📥 Audio player received CONTROL input", "audio-player")
                    control_value = event.get("value")
                    if control_value and len(control_value) > 0:
                        control_text = str(control_value[0].as_py()).strip().lower()
                        metadata = event.get("metadata", {})
                        send_log(node, "INFO", f"📥 Control: text='{control_text}', metadata={metadata}", "audio-player")

                        # Extract command and question_id from metadata
                        command = metadata.get("command", control_text)
                        new_question_id = metadata.get("question_id")

                        if command in ["reset", "cancel"]:
                            if new_question_id is None:
                                # Full reset - clear everything
                                player.reset()
                                segments_per_participant.clear()
                                last_question_id.clear()
                                completed_sessions.clear()
                                reset_question_id = None
                                filtering_mode = False
                                send_log(node, "INFO", f"🔄 Audio buffer FULL RESET (command: {command})", "audio-player")
                            else:
                                # Smart reset - filter incoming audio by question_id
                                # 1. Clear the buffer (discard all old audio)
                                player.reset()
                                segments_per_participant.clear()
                                last_question_id.clear()
                                completed_sessions.clear()

                                # 2. Enable filtering mode - reject audio until matching question_id arrives
                                reset_question_id = new_question_id
                                filtering_mode = True

                                send_log(node, "INFO",
                                    f"🔄 Audio buffer SMART RESET with question_id={new_question_id}, entering filtering mode (command: {command})",
                                    "audio-player")
                except Exception as e:
                    send_log(node, "ERROR", f"❌ Error handling control input: {e}", "audio-player")
                continue

            # Handle audio inputs: any input starting with "audio_"
            if event and event["type"] == "INPUT" and event["id"].startswith("audio_"):
                try:
                    participant = event["id"].replace("audio_", "")  # Extract participant name from input id

                    # Initialize participant tracking on first encounter
                    if participant not in segments_per_participant:
                        segments_per_participant[participant] = 0
                        last_question_id[participant] = None
                        send_log(node, "INFO", f"📌 Registered new participant: {participant}", "audio-player")

                    raw_value = event.get("value")

                    if raw_value and len(raw_value) > 0:
                        audio_data = raw_value[0].as_py()
                        if audio_data is not None:
                            if not isinstance(audio_data, np.ndarray):
                                audio_data = np.array(audio_data, dtype=np.float32)

                            if len(audio_data) > 0:
                                metadata = event.get("metadata", {})

                                # Smart reset filtering: Check if we should filter by question_id
                                if filtering_mode:
                                    incoming_qid = metadata.get("question_id")

                                    # Convert to string for comparison
                                    incoming_qid_str = str(incoming_qid) if incoming_qid is not None else None
                                    reset_qid_str = str(reset_question_id) if reset_question_id is not None else None

                                    if incoming_qid_str != reset_qid_str:
                                        # Reject old audio - question_id doesn't match
                                        send_log(node, "DEBUG",
                                            f"🚫 Filtering out old audio from {participant} (question_id={incoming_qid_str}, expected={reset_qid_str})",
                                            "audio-player")
                                        continue  # Skip this audio chunk
                                    else:
                                        # First chunk with matching question_id - exit filtering mode
                                        filtering_mode = False
                                        send_log(node, "INFO",
                                            f"✅ Received matching question_id={reset_qid_str} from {participant}, exiting filtering mode",
                                            "audio-player")

                                # Update sample rate if provided
                                incoming_rate = metadata.get("sample_rate")
                                if incoming_rate is not None:
                                    player.set_sample_rate(incoming_rate)

                                # Calculate duration
                                effective_rate = float(player.sample_rate)
                                duration = len(audio_data) / effective_rate if effective_rate > 0 else 0.0

                                # Add audio to buffer (concatenates in arrival order)
                                player.add_audio(audio_data, participant)

                                segments_per_participant[participant] += 1
                                segment_index = metadata.get("segment_index", -1)

                                # Send audio_complete signal immediately after receiving audio
                                # This replaces TTS segment_complete for flow control
                                audio_complete_metadata = {
                                    "participant": participant,
                                    "question_id": metadata.get("question_id", "unknown"),
                                    "session_status": metadata.get("session_status", "unknown"),
                                    "session_id": metadata.get("session_id", "unknown")
                                }
                                node.send_output(
                                    "audio_complete",
                                    pa.array(["received"]),
                                    metadata=audio_complete_metadata
                                )
                                send_log(node, "DEBUG", f"📤 AUDIO_COMPLETE: {participant} (qid={metadata.get('question_id')}, status={metadata.get('session_status')})", "audio-player")

                                # Log first few audio segments to verify reception
                                if segments_per_participant[participant] <= 3:
                                    send_log(node, "INFO", f"🎵 {participant.upper()}: segment {segment_index + 1}, {duration:.3f}s", "audio-player")

                                # Extract metadata and simply pass through whatever LLM sent
                                question_id = metadata.get("question_id")
                                session_status = metadata.get("session_status")
                                session_id = metadata.get("session_id")

                                # Store latest question_id for this participant
                                if question_id is not None:
                                    last_question_id[participant] = question_id

                                # Session start detection: send signal when new session starts
                                if session_status == "started":
                                    # Create unique session identifier to avoid duplicates
                                    session_key = f"{participant}_{session_id}" if session_id else f"{participant}_{question_id}"

                                    if session_key not in completed_sessions and last_question_id[participant] is not None:
                                        # Track that we've seen this session start
                                        completed_sessions.add(session_key)

                                        # Send session_start signal, passing through ALL original metadata
                                        session_start_metadata = metadata.copy() if metadata else {}
                                        session_start_metadata["source"] = "audio_player"
                                        # Remove None values from metadata (PyArrow can't handle None)
                                        session_start_metadata = {k: (v if v is not None else "unknown") for k, v in session_start_metadata.items()}

                                        node.send_output("session_start",
                                            pa.array([session_status]),
                                            metadata=session_start_metadata
                                        )
                                        # Send log using common logging utility
                                        send_log(node, "INFO", f"🎬 Session START: {participant} (question_id={last_question_id[participant]}, status={session_status})", "audio-player")

                                # print(f"[Audio Player] 🎵 {participant.upper()}: "
                                #       f"segment {segment_index + 1}, "
                                #       f"{len(audio_data)} samples, "
                                #       f"{duration:.3f}s", flush=True)

                                # Auto-start playback
                                if not playback_started:
                                    player.resume()
                                    playback_started = True
                                    send_log(node, "INFO", "▶️  Playback STARTED", "audio-player")

                except Exception as e:
                    pass  # print(f"[Error] Processing audio from {event['id']}: {e}")

            # Send buffer status periodically
            current_time = time.time()
            if current_time - last_status_time >= status_interval:
                stats = player.buffer.get_stats()
                buffer_percentage = stats['buffer_fill']
                buffer_seconds = stats['available_seconds']

                # Send buffer percentage to controller
                node.send_output("buffer_status",
                    pa.array([buffer_percentage], type=pa.float64()))

                # Send regular buffer status log to viewer
                send_log(node, "INFO", f"🔊 Buffer: {buffer_percentage:.1f}% ({buffer_seconds:.1f}s)", "audio-player")

                # ASCII Art Buffer Visualization
                bar_width = 40
                chars_per_second = bar_width / args.buffer_seconds
                chars_filled = int(buffer_seconds * chars_per_second)

                # Build buffer bar
                buffer_bar = "█" * min(chars_filled, bar_width) + "░" * max(0, bar_width - chars_filled)

                # Status indicators
                if buffer_percentage < 5:
                    status = "EMPTY"
                    icon = "⚠️"
                elif buffer_percentage < 20:
                    status = "LOW"
                    icon = "⚠️"
                elif buffer_percentage > 80:
                    status = "HIGH"
                    icon = "⚠️"
                else:
                    status = "NORMAL"
                    icon = "✓"

                playback_status = "PLAYING" if (playback_started and player.is_playing) else "PAUSED" if not player.is_playing and playback_started else "WAITING"

                # Display buffer visualization with dynamic participants
                # Build participant stats string dynamically
                participant_stats = " ".join([
                    f"{name[:3].upper()}:{count:3d}"
                    for name, count in sorted(segments_per_participant.items())
                ])

                print(f"\r[{buffer_percentage:5.1f}%] {status:6s} {icon} [{buffer_bar}] {buffer_seconds:5.1f}s/{args.buffer_seconds}s | "
                      f"{participant_stats} | "
                      f"{playback_status}",
                      end="", flush=True)

                last_status_time = current_time

    except Exception as e:
        pass  # print(f"\n[Error] Main loop: {e}")
        # import traceback
        # traceback.print_exc()
    finally:
        if player and player.stream:
            player.stream.stop()
            player.stream.close()
        pass  # print("\n[Multi-Audio Player] Shutdown complete")


if __name__ == "__main__":
    main()
