from pathlib import Path

from utils.tts import synthesize_speech_with_checkpoint


def main() -> None:
    text = "Hej! Detta är ett test av den nya svenska rösten. Hur låter det?"
    checkpoint_path = Path("models/checkpoints/final_model.ckpt")
    output_path = Path("output/test_swe_cpu.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ok = synthesize_speech_with_checkpoint(
        text=text,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
        length_scale=1.0,
        noise_scale=0.667,
    )

    size = output_path.stat().st_size if output_path.exists() else 0
    print({"ok": ok, "path": str(output_path), "exists": output_path.exists(), "size": size})


if __name__ == "__main__":
    main()


