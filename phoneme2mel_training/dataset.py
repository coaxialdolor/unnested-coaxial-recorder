import json
from pathlib import Path
from typing import Dict, List, Optional

import torch
from torch.utils.data import Dataset
import torchaudio


class MultilingualVoiceDataset(Dataset):
    """Loads mono audio and tokenizes phoneme strings into integer IDs.

    Validates that phoneme sequences are non-empty.
    """

    def __init__(
        self,
        audio_files: List[str],
        phoneme_sequences: List[str],
        transcripts: Optional[List[str]] = None,
        sample_rate: int = 22050,
        phoneme_map_path: Optional[str] = None,
        phoneme_map: Optional[Dict[str, int]] = None,
        unk_token: str = "UNK",
        max_wav_value: float = 32768.0,
    ):
        self.audio_files = audio_files
        self.phoneme_sequences = phoneme_sequences
        self.transcripts = transcripts or [""] * len(audio_files)
        self.sample_rate = sample_rate
        self.max_wav_value = max_wav_value

        if phoneme_map is None:
            if phoneme_map_path is None:
                raise ValueError("Either phoneme_map or phoneme_map_path must be provided")
            with open(phoneme_map_path, "r", encoding="utf-8") as f:
                phoneme_map = json.load(f)

        self.phoneme_map = phoneme_map
        self.unk_id = self.phoneme_map.get(unk_token, 0)

        if len(self.audio_files) != len(self.phoneme_sequences):
            raise ValueError("audio_files and phoneme_sequences must be the same length")

    def __len__(self):
        return len(self.audio_files)

    def _load_audio(self, path: str) -> torch.Tensor:
        import soundfile as sf

        waveform, sr = sf.read(path)
        waveform = torch.from_numpy(waveform).float()
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        else:
            waveform = waveform.T

        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        waveform = waveform / self.max_wav_value
        return waveform.squeeze(0)

    def _tokenize(self, seq: str) -> torch.Tensor:
        tokens = [self.phoneme_map.get(p, self.unk_id) for p in (seq.split() if isinstance(seq, str) else [])]
        return torch.tensor(tokens, dtype=torch.long)

    def __getitem__(self, idx: int):
        audio_path = self.audio_files[idx]
        audio = self._load_audio(audio_path)

        seq = self.phoneme_sequences[idx] or ""
        token_ids = self._tokenize(seq)
        if token_ids.numel() == 0:
            raise ValueError(f"Empty phoneme sequence at index {idx} (file: {audio_path})")

        return {
            "audio": audio,
            "audio_len": int(audio.shape[0]),
            "phoneme_ids": token_ids,
            "phoneme_len": int(token_ids.numel()),
            "transcript": self.transcripts[idx],
        }


