"""Server-side audio helpers (used by the synthetic test-call generator).

The browser does its own 8 kHz downsampling; this module mirrors that path in
Python so we can verify Prisma on phone-quality, noisy audio without a mic.
"""
import io
import wave

import numpy as np


def read_wav(data: bytes):
    with wave.open(io.BytesIO(data)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    assert sw == 2, "expected 16-bit PCM"
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def write_wav(x: np.ndarray, sr: int) -> bytes:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
    return buf.getvalue()


def to_phone_line(x: np.ndarray, sr: int, target: int = 8000) -> np.ndarray:
    """Telephone band (300-3400 Hz) + resample to 8 kHz, via FFT masking + linear interp."""
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    spec[(freqs < 300) | (freqs > 3400)] = 0
    y = np.fft.irfft(spec, n)
    m = int(n * target / sr)
    return np.interp(np.linspace(0, n - 1, m), np.arange(n), y).astype(np.float32)


def add_noise(x: np.ndarray, sr: int, snr_db: float = 10.0, seed: int = 7) -> np.ndarray:
    """Add fan/TV-like noise: brown-ish hum + white hiss + a 50 Hz-ish mains buzz."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(len(x))
    brown = np.cumsum(white)
    brown = brown - np.convolve(brown, np.ones(400) / 400, mode="same")
    t = np.arange(len(x)) / sr
    hum = 0.3 * np.sin(2 * np.pi * 150 * t)
    noise = brown / (np.std(brown) + 1e-9) + 0.5 * white + hum
    sig_p = np.mean(x ** 2) + 1e-12
    noise *= np.sqrt(sig_p / (10 ** (snr_db / 10)) / (np.mean(noise ** 2) + 1e-12))
    return (x + noise).astype(np.float32)
