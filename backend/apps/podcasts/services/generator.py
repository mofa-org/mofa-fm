import os
import re
import json
import time
import random
import asyncio
import logging
import numpy as np
from typing import List, Tuple, Optional, Dict
from django.conf import settings
from pydub import AudioSegment
import websockets

logger = logging.getLogger(__name__)

class PodcastGenerator:
    """
    Service to generate two-person podcasts from markdown scripts using MiniMax API.
    """
    
    # Voice IDs (Hardcoded for now as per requirement, could be configurable)
    VOICE_IDS = {
        "daniu": "ttv-voice-2025103011222725-sg8dZxUP",  # Luo Xiang style
        "yifan": "moss_audio_aaa1346a-7ce7-11f0-8e61-2e6e3c7ee85d", # Doubao style
    }
    
    CHARACTER_ALIASES = {
        "大牛": "daniu",
        "一帆": "yifan",
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY is not set")
            
        self.url = f"wss://api.minimax.chat/v1/t2a_v2?GroupId={os.getenv('MINIMAX_GROUP_ID', '1813378404020551699')}"
        
    def generate(self, script_content: str, output_path: str) -> str:
        """
        Main entry point: Parse script, generate audio for each segment, stitch them, and save.
        """
        logger.info("Starting podcast generation...")
        
        # 1. Parse Script
        segments = self._parse_markdown(script_content)
        if not segments:
            raise ValueError("No valid segments found in script")
        
        logger.info(f"Parsed {len(segments)} segments.")
        
        # 2. Generate Audio for each segment
        audio_segments = []
        
        # Run async generation loop
        try:
            audio_segments = asyncio.run(self._generate_all_segments(segments))
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
            
        # 3. Stitch Audio
        logger.info("Stitching audio segments...")
        final_audio = AudioSegment.empty()
        
        last_speaker = None
        
        for speaker, audio_chunk in audio_segments:
            # Add silence if speaker changes (and it's not the very first segment)
            if last_speaker and last_speaker != speaker:
                silence_duration = random.randint(1000, 3000) # 1-3 seconds
                final_audio += AudioSegment.silent(duration=silence_duration)
                
            final_audio += audio_chunk
            last_speaker = speaker
            
        # 4. Save to file
        logger.info(f"Saving to {output_path}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_audio.export(output_path, format="mp3")
        
        return output_path

    def _parse_markdown(self, script_content: str) -> List[Tuple[str, str]]:
        """
        Parse markdown script into (character, text) tuples.
        """
        segments: List[Tuple[str, str]] = []
        current_character: Optional[str] = None
        current_text: List[str] = []

        def finalize_segment():
            nonlocal current_character, current_text
            if current_character and current_text:
                combined_text = " ".join(current_text).strip()
                if combined_text:
                    segments.append((current_character, combined_text))
            current_text = []

        for raw_line in script_content.splitlines():
            line = raw_line.strip()

            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue

            # Detect character tags
            match = re.search(r'【([^】]+)】', line)
            if match:
                finalize_segment()

                tag_content = match.group(1).strip()
                character = self.CHARACTER_ALIASES.get(tag_content)
                
                if not character:
                    # Try to see if the tag content itself is a known key (e.g. "daniu")
                    if tag_content.lower() in self.VOICE_IDS:
                        character = tag_content.lower()
                    else:
                        # Unknown character, skip
                        current_character = None
                        current_text = []
                        continue

                # Extract text after tag
                remainder = line.split('】', 1)[1] if '】' in line else ''
                remainder = remainder.lstrip('*').strip()

                current_character = character
                current_text = [remainder] if remainder else []
                continue

            if current_character:
                clean_line = line.strip('*').strip()
                if clean_line:
                    current_text.append(clean_line)

        finalize_segment()
        return segments

    async def _generate_all_segments(self, segments: List[Tuple[str, str]]) -> List[Tuple[str, AudioSegment]]:
        """
        Generate audio for all segments sequentially.
        """
        results = []
        for i, (speaker, text) in enumerate(segments):
            logger.info(f"Generating segment {i+1}/{len(segments)} for {speaker}...")
            audio_data = await self._synthesize_text(speaker, text)
            
            # Convert raw PCM/MP3 bytes to AudioSegment
            # MiniMax returns raw audio, we need to handle it. 
            # Actually MiniMax returns PCM or MP3 depending on config. 
            # Let's assume we request MP3 or handle PCM.
            # Based on previous code, it returns streaming PCM.
            # But for simplicity in this service, we can accumulate and convert.
            
            # Since we are using pydub, we can create AudioSegment from bytes
            # Assuming 32kHz, 1 channel, 16-bit PCM (from previous analysis)
            
            segment = AudioSegment(
                data=audio_data,
                sample_width=2, # 16-bit
                frame_rate=32000,
                channels=1
            )
            results.append((speaker, segment))
            
        return results

    async def _synthesize_text(self, speaker: str, text: str) -> bytes:
        """
        Call MiniMax API to synthesize text.
        """
        voice_id = self.VOICE_IDS.get(speaker)
        if not voice_id:
            raise ValueError(f"No voice ID for speaker: {speaker}")
            
        payload = {
            "model": "speech-01-turbo",
            "text": text,
            "stream": True,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0 if speaker == 'yifan' else -1, # Match previous config
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "pcm",
                "channel": 1,
            },
            "pronunciation_dict": {
                "tone": []
            },
            "language": "CN" # or Auto
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        audio_buffer = bytearray()
        
        async with websockets.connect(self.url, extra_headers=headers) as websocket:
            await websocket.send(json.dumps(payload))
            
            async for message in websocket:
                if isinstance(message, str):
                    # Parse JSON message
                    data = json.loads(message)
                    if data.get("base_resp", {}).get("status_code") != 0:
                         logger.error(f"MiniMax Error: {data}")
                         # Continue or raise?
                         continue
                         
                    # Check if done
                    if data.get("status") == 2: # Finished
                        break
                        
                    # Extract audio
                    if "data" in data and "audio" in data["data"]:
                        # Hex string to bytes
                        chunk = bytes.fromhex(data["data"]["audio"])
                        audio_buffer.extend(chunk)
                        
                elif isinstance(message, bytes):
                    # Should not happen with this API usually, but just in case
                    audio_buffer.extend(message)
                    
        return bytes(audio_buffer)
