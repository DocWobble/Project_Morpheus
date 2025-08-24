import os
import sys
import time
import wave
import numpy as np

try:  # Optional runtime dependency; stubbed if unavailable
    import sounddevice as sd
except Exception:  # pragma: no cover - fallback when PortAudio is missing
    import types

    sd = types.SimpleNamespace(play=lambda *_, **__: None, wait=lambda: None)
from dotenv import load_dotenv

# Helper to detect if running in Uvicorn's reloader
def is_reloader_process():
    """Check if the current process is a uvicorn reloader"""
    return (sys.argv[0].endswith('_continuation.py') or 
            os.environ.get('UVICORN_STARTED') == 'true')

# Set a flag to avoid repeat messages
IS_RELOADER = is_reloader_process()
if not IS_RELOADER:
    os.environ['UVICORN_STARTED'] = 'true'

# Load environment variables from .env file
load_dotenv()

# Detect hardware capabilities and display information
import torch
import psutil

# Detect if we're on a high-end system based on hardware capabilities
HIGH_END_GPU = False
if torch.cuda.is_available():
    # Get GPU properties
    props = torch.cuda.get_device_properties(0)
    gpu_name = props.name
    gpu_mem_gb = props.total_memory / (1024**3)
    compute_capability = f"{props.major}.{props.minor}"
    
    # Consider high-end if: large VRAM (≥16GB) OR high compute capability (≥8.0) OR large VRAM (≥12GB) with good CC (≥7.0)
    HIGH_END_GPU = (gpu_mem_gb >= 16.0 or 
                    props.major >= 8 or 
                    (gpu_mem_gb >= 12.0 and props.major >= 7))
        
    if HIGH_END_GPU:
        if not IS_RELOADER:
            print(f"🖥️ Hardware: High-end CUDA GPU detected")
            print(f"📊 Device: {gpu_name}")
            print(f"📊 VRAM: {gpu_mem_gb:.2f} GB")
            print(f"📊 Compute Capability: {compute_capability}")
            print("🚀 Using high-performance optimizations")
    else:
        if not IS_RELOADER:
            print(f"🖥️ Hardware: CUDA GPU detected")
            print(f"📊 Device: {gpu_name}")
            print(f"📊 VRAM: {gpu_mem_gb:.2f} GB")
            print(f"📊 Compute Capability: {compute_capability}")
            print("🚀 Using GPU-optimized settings")
else:
    # Get CPU info
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    if not IS_RELOADER:
        print(f"🖥️ Hardware: CPU only (No CUDA GPU detected)")
        print(f"📊 CPU: {cpu_cores} cores, {cpu_threads} threads")
        print(f"📊 RAM: {ram_gb:.2f} GB")
        print("⚙️ Using CPU-optimized settings")

# Model generation parameters from environment variables
try:
    MAX_TOKENS = int(os.environ.get("ORPHEUS_MAX_TOKENS", "8192"))
except (ValueError, TypeError):
    print("WARNING: Invalid ORPHEUS_MAX_TOKENS value, using 8192 as fallback")
    MAX_TOKENS = 8192

try:
    TEMPERATURE = float(os.environ.get("ORPHEUS_TEMPERATURE", "0.6"))
except (ValueError, TypeError):
    print("WARNING: Invalid ORPHEUS_TEMPERATURE value, using 0.6 as fallback")
    TEMPERATURE = 0.6

try:
    TOP_P = float(os.environ.get("ORPHEUS_TOP_P", "0.9"))
except (ValueError, TypeError):
    print("WARNING: Invalid ORPHEUS_TOP_P value, using 0.9 as fallback")
    TOP_P = 0.9


def update_generation_params(*, temperature=None, top_p=None, max_tokens=None) -> None:
    """Update runtime generation parameters in-place."""

    global TEMPERATURE, TOP_P, MAX_TOKENS
    if temperature is not None:
        TEMPERATURE = float(temperature)
    if top_p is not None:
        TOP_P = float(top_p)
    if max_tokens is not None:
        MAX_TOKENS = int(max_tokens)

# Repetition penalty is hardcoded to 1.1 which is the only stable value for quality output
REPETITION_PENALTY = 1.1

try:
    SAMPLE_RATE = int(os.environ.get("ORPHEUS_SAMPLE_RATE", "24000"))
except (ValueError, TypeError):
    print("WARNING: Invalid ORPHEUS_SAMPLE_RATE value, using 24000 as fallback")
    SAMPLE_RATE = 24000

# Print loaded configuration only in the main process, not in the reloader
if not IS_RELOADER:
    print(f"Configuration loaded:")
    print(f"  MAX_TOKENS: {MAX_TOKENS}")
    print(f"  TEMPERATURE: {TEMPERATURE}")
    print(f"  TOP_P: {TOP_P}")
    print(f"  REPETITION_PENALTY: {REPETITION_PENALTY}")

# Parallel processing settings
NUM_WORKERS = 4 if HIGH_END_GPU else 2

# Define voices by language
ENGLISH_VOICES = ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
FRENCH_VOICES = ["pierre", "amelie", "marie"]
GERMAN_VOICES = ["jana", "thomas", "max"]
KOREAN_VOICES = ["유나", "준서"]
HINDI_VOICES = ["ऋतिका"]
MANDARIN_VOICES = ["长乐", "白芷"]
SPANISH_VOICES = ["javi", "sergio", "maria"]
ITALIAN_VOICES = ["pietro", "giulia", "carlo"]

# Combined list for API compatibility
AVAILABLE_VOICES = (
    ENGLISH_VOICES + 
    FRENCH_VOICES + 
    GERMAN_VOICES + 
    KOREAN_VOICES + 
    HINDI_VOICES + 
    MANDARIN_VOICES + 
    SPANISH_VOICES + 
    ITALIAN_VOICES
)
DEFAULT_VOICE = "tara"  # Best voice according to documentation

# Map voices to languages for the UI
VOICE_TO_LANGUAGE = {}
VOICE_TO_LANGUAGE.update({voice: "english" for voice in ENGLISH_VOICES})
VOICE_TO_LANGUAGE.update({voice: "french" for voice in FRENCH_VOICES})
VOICE_TO_LANGUAGE.update({voice: "german" for voice in GERMAN_VOICES})
VOICE_TO_LANGUAGE.update({voice: "korean" for voice in KOREAN_VOICES})
VOICE_TO_LANGUAGE.update({voice: "hindi" for voice in HINDI_VOICES})
VOICE_TO_LANGUAGE.update({voice: "mandarin" for voice in MANDARIN_VOICES})
VOICE_TO_LANGUAGE.update({voice: "spanish" for voice in SPANISH_VOICES})
VOICE_TO_LANGUAGE.update({voice: "italian" for voice in ITALIAN_VOICES})

# Languages list for the UI
AVAILABLE_LANGUAGES = ["english", "french", "german", "korean", "hindi", "mandarin", "spanish", "italian"]

# Token decoding helpers reside in `speechpipe` but are only required by
# optional remote backends. Importing them here would pull heavy dependencies
# at startup, so callers import from `speechpipe` directly when needed.

# Special token IDs for Orpheus model
START_TOKEN_ID = 128259
END_TOKEN_IDS = [128009, 128260, 128261, 128257]

# Performance monitoring
class PerformanceMonitor:
    """Track and report performance metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.token_count = 0
        self.audio_chunks = 0
        self.last_report_time = time.time()
        self.report_interval = 2.0  # seconds

    def add_tokens(self, count: int = 1) -> None:
        self.token_count += count
        self._check_report()

    def add_audio_chunk(self) -> None:
        self.audio_chunks += 1
        self._check_report()

    def _check_report(self) -> None:
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            self.report()
            self.last_report_time = current_time

    def report(self) -> None:
        elapsed = time.time() - self.start_time
        if elapsed < 0.001:
            return

        tokens_per_sec = self.token_count / elapsed
        chunks_per_sec = self.audio_chunks / elapsed

        # Estimate audio duration based on audio chunks (each chunk is ~0.085s of audio)
        est_duration = self.audio_chunks * 0.085

        print(
            f"Progress: {tokens_per_sec:.1f} tokens/sec, est. {est_duration:.1f}s audio generated, {self.token_count} tokens, {self.audio_chunks} chunks in {elapsed:.1f}s"
        )

def format_prompt(prompt: str, voice: str = DEFAULT_VOICE) -> str:
    """Format prompt for Orpheus model with voice prefix and special tokens."""
    # Validate voice and provide fallback
    if voice not in AVAILABLE_VOICES:
        print(f"Warning: Voice '{voice}' not recognized. Using '{DEFAULT_VOICE}' instead.")
        voice = DEFAULT_VOICE
        
    # Format similar to how engine_class.py does it with special tokens
    formatted_prompt = f"{voice}: {prompt}"
    
    # Add special token markers for the Orpheus-FASTAPI
    special_start = "<|audio|>"  # Using the additional_special_token from config
    special_end = "<|eot_id|>"   # Using the eos_token from config
    
    return f"{special_start}{formatted_prompt}{special_end}"


def stream_audio(audio_buffer):
    """Stream audio buffer to output device with error handling."""
    if audio_buffer is None or len(audio_buffer) == 0:
        return
    
    try:
        # Convert bytes to NumPy array (16-bit PCM)
        audio_data = np.frombuffer(audio_buffer, dtype=np.int16)
        
        # Normalize to float in range [-1, 1] for playback
        audio_float = audio_data.astype(np.float32) / 32767.0
        
        # Play the audio with proper device selection and error handling
        sd.play(audio_float, SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print(f"Audio playback error: {e}")

import re
import numpy as np
from io import BytesIO
import wave

def split_text_into_sentences(text):
    """Split text into sentences with a more reliable approach."""
    # We'll use a simple approach that doesn't rely on variable-width lookbehinds
    # which aren't supported in Python's regex engine
    
    # First, split on common sentence ending punctuation
    # This isn't perfect but works for most cases and avoids the regex error
    parts = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        
        # If we hit a sentence ending followed by a space, consider this a potential sentence end
        if char in (' ', '\n', '\t') and len(current_sentence) > 1:
            prev_char = current_sentence[-2]
            if prev_char in ('.', '!', '?'):
                # Check if this is likely a real sentence end and not an abbreviation
                # (Simple heuristic: if there's a space before the period, it's likely a real sentence end)
                if len(current_sentence) > 3 and current_sentence[-3] not in ('.', ' '):
                    parts.append(current_sentence.strip())
                    current_sentence = ""
    
    # Add any remaining text
    if current_sentence.strip():
        parts.append(current_sentence.strip())
    
    # Combine very short segments to avoid tiny audio files
    min_chars = 20  # Minimum reasonable sentence length
    combined_sentences = []
    i = 0
    
    while i < len(parts):
        current = parts[i]
        
        # If this is a short sentence and not the last one, combine with next
        while i < len(parts) - 1 and len(current) < min_chars:
            i += 1
            current += " " + parts[i]
            
        combined_sentences.append(current)
        i += 1
    
    return combined_sentences

def stitch_wav_files(input_files, output_file, crossfade_ms=50):
    """Stitch multiple WAV files together with crossfading for smooth transitions."""
    if not input_files:
        return
        
    print(f"Stitching {len(input_files)} WAV files together with {crossfade_ms}ms crossfade")
    
    # If only one file, just copy it
    if len(input_files) == 1:
        import shutil
        shutil.copy(input_files[0], output_file)
        return
    
    # Convert crossfade_ms to samples
    crossfade_samples = int(SAMPLE_RATE * crossfade_ms / 1000)
    print(f"Using {crossfade_samples} samples for crossfade at {SAMPLE_RATE}Hz")
    
    # Build the final audio in memory with crossfades
    final_audio = np.array([], dtype=np.int16)
    first_params = None
    
    for i, input_file in enumerate(input_files):
        try:
            with wave.open(input_file, 'rb') as wav:
                if first_params is None:
                    first_params = wav.getparams()
                elif wav.getparams() != first_params:
                    print(f"Warning: WAV file {input_file} has different parameters")
                    
                frames = wav.readframes(wav.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                
                if i == 0:
                    # First segment - use as is
                    final_audio = audio
                else:
                    # Apply crossfade with previous segment
                    if len(final_audio) >= crossfade_samples and len(audio) >= crossfade_samples:
                        # Create crossfade weights
                        fade_out = np.linspace(1.0, 0.0, crossfade_samples)
                        fade_in = np.linspace(0.0, 1.0, crossfade_samples)
                        
                        # Apply crossfade
                        crossfade_region = (final_audio[-crossfade_samples:] * fade_out + 
                                           audio[:crossfade_samples] * fade_in).astype(np.int16)
                        
                        # Combine: original without last crossfade_samples + crossfade + new without first crossfade_samples
                        final_audio = np.concatenate([final_audio[:-crossfade_samples], 
                                                    crossfade_region, 
                                                    audio[crossfade_samples:]])
                    else:
                        # One segment too short for crossfade, just append
                        print(f"Segment {i} too short for crossfade, concatenating directly")
                        final_audio = np.concatenate([final_audio, audio])
        except Exception as e:
            print(f"Error processing file {input_file}: {e}")
            if i == 0:
                raise  # Critical failure if first file fails
    
    # Write the final audio data to the output file
    try:
        with wave.open(output_file, 'wb') as output_wav:
            if first_params is None:
                raise ValueError("No valid WAV files were processed")
                
            output_wav.setparams(first_params)
            output_wav.writeframes(final_audio.tobytes())
        
        print(f"Successfully stitched audio to {output_file} with crossfading")
    except Exception as e:
        print(f"Error writing output file {output_file}: {e}")
        raise

def list_available_voices():
    """List all available voices with the recommended one marked."""
    print("Available voices (in order of conversational realism):")
    for i, voice in enumerate(AVAILABLE_VOICES):
        marker = "★" if voice == DEFAULT_VOICE else " "
        print(f"{marker} {voice}")
    print(f"\nDefault voice: {DEFAULT_VOICE}")
    
    print("\nAvailable emotion tags:")
    print("<laugh>, <chuckle>, <sigh>, <cough>, <sniffle>, <groan>, <yawn>, <gasp>")

