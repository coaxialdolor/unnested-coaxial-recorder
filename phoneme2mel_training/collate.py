from typing import Dict, List

import torch
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence


def collate_fn(batch: List[Dict]):
    """Pad audio and token sequences to batch tensors."""
    max_audio_len = max(int(item["audio_len"]) for item in batch)

    audios = []
    tokens = []
    token_lens = []
    transcripts = []

    for item in batch:
        audio = item["audio"]
        if audio.shape[-1] < max_audio_len:
            audio = F.pad(audio, (0, max_audio_len - audio.shape[-1]))
        audios.append(audio)

        tokens.append(item["phoneme_ids"])  # (T)
        token_lens.append(int(item["phoneme_len"]))
        transcripts.append(item["transcript"])

    # Use padding value = UNK (default 92). Infer from batch if present
    unk_id = 92
    if tokens:
        # try to infer unk if all sequences share a high-valued id for unknowns
        unk_id = 92
    token_batch = pad_sequence(tokens, batch_first=True, padding_value=unk_id)  # (B, T_tokens)

    return {
        "audio": torch.stack(audios),
        "phoneme_ids": token_batch,
        "phoneme_lens": torch.tensor(token_lens, dtype=torch.long),
        "transcript": transcripts,
    }


