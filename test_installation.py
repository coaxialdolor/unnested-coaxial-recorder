#!/usr/bin/env python3
"""
Test script to verify installation
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False

def main():
    print("Testing installation...")
    print("=" * 50)

    # Core dependencies
    core_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydub", "Pydub"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
    ]

    # Training dependencies
    training_modules = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
        ("transformers", "Transformers"),
        ("datasets", "Datasets"),
        ("librosa", "Librosa"),
        ("soundfile", "SoundFile"),
        ("scipy", "SciPy"),
        ("sklearn", "Scikit-learn"),
    ]

    # TTS dependencies
    tts_modules = [
        ("piper", "Piper TTS"),
        ("phonemizer", "Phonemizer"),
    ]

    print("Core Dependencies:")
    core_success = all(test_import(module, name) for module, name in core_modules)

    print("\nTraining Dependencies:")
    training_success = all(test_import(module, name) for module, name in training_modules)

    print("\nTTS Dependencies:")
    tts_success = all(test_import(module, name) for module, name in tts_modules)

    # Test PyTorch CUDA
    print("\nPyTorch CUDA Support:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.device_count()} device(s)")
            for i in range(torch.cuda.device_count()):
                print(f"   - {torch.cuda.get_device_name(i)}")
        else:
            print("⚠️  CUDA not available (CPU-only mode)")
    except ImportError:
        print("❌ PyTorch not available")

    print("\n" + "=" * 50)
    if core_success and training_success and tts_success:
        print("🎉 Installation test passed!")
        return True
    else:
        print("❌ Installation test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
