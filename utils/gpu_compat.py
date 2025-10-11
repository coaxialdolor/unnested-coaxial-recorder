"""
GPU Compatibility Utilities for RTX 50-series and newer GPUs

This module handles GPU detection and device configuration for training,
with special support for RTX 5060 Ti and other Compute Capability 12.x GPUs.
"""

import logging
import sys
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_compute_capability() -> Optional[Tuple[int, int]]:
    """
    Get CUDA compute capability of the current GPU.

    Returns:
        Tuple of (major, minor) version or None if no GPU available
    """
    try:
        import torch
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            capability = torch.cuda.get_device_capability(0)
            return capability
    except Exception as e:
        logger.warning(f"Could not get compute capability: {e}")
    return None


def check_gpu_compatibility() -> dict:
    """
    Check GPU compatibility and return detailed status.

    Returns:
        Dictionary with GPU status information
    """
    result = {
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
        "compute_capability": None,
        "pytorch_version": None,
        "cuda_version": None,
        "compatible": True,
        "warnings": [],
        "recommended_action": None
    }

    try:
        import torch
        result["pytorch_version"] = torch.__version__
        result["cuda_available"] = torch.cuda.is_available()
        result["device_count"] = torch.cuda.device_count() if result["cuda_available"] else 0

        if result["cuda_available"]:
            result["cuda_version"] = torch.version.cuda

            # Get device information
            for i in range(result["device_count"]):
                device_name = torch.cuda.get_device_name(i)
                capability = torch.cuda.get_device_capability(i)
                result["devices"].append({
                    "id": i,
                    "name": device_name,
                    "compute_capability": f"{capability[0]}.{capability[1]}"
                })

            # Check primary device
            if result["device_count"] > 0:
                capability = torch.cuda.get_device_capability(0)
                result["compute_capability"] = f"{capability[0]}.{capability[1]}"
                major, minor = capability

                # Check for RTX 50-series (sm_120)
                if major >= 12:
                    # Check if PyTorch supports sm_120
                    try:
                        # Try to run a simple operation
                        device = torch.device('cuda:0')
                        test_tensor = torch.randn(10, 10).to(device)
                        _ = test_tensor @ test_tensor.T
                        result["compatible"] = True
                    except RuntimeError as e:
                        if "no kernel image" in str(e).lower():
                            result["compatible"] = False
                            result["warnings"].append(
                                f"GPU has Compute Capability {major}.{minor} (sm_{major}{minor}), "
                                f"but PyTorch {torch.__version__} doesn't have kernels for this architecture."
                            )
                            result["recommended_action"] = (
                                "Upgrade PyTorch to a version with CUDA 12.8+ support:\n"
                                "pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128"
                            )
                        else:
                            result["warnings"].append(f"GPU test failed: {str(e)}")

                # Check for older GPUs
                elif major < 6:
                    result["warnings"].append(
                        f"GPU has old Compute Capability {major}.{minor}. "
                        "Some features may not work optimally."
                    )

    except ImportError:
        result["warnings"].append("PyTorch not installed")
    except Exception as e:
        result["warnings"].append(f"Error checking GPU: {str(e)}")

    return result


def get_training_device(force_cuda: bool = False, fallback_to_cpu: bool = True) -> str:
    """
    Get the best available device for training.

    Args:
        force_cuda: Force CUDA device even if compatibility test fails
        fallback_to_cpu: Fall back to CPU if CUDA has issues

    Returns:
        Device string: "cuda", "cuda:0", "mps", or "cpu"
    """
    try:
        import torch

        # Check CUDA
        if torch.cuda.is_available():
            # Test if CUDA actually works
            try:
                device = torch.device('cuda:0')
                test_tensor = torch.randn(10, 10).to(device)
                _ = test_tensor @ test_tensor.T
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
                return "cuda"
            except RuntimeError as e:
                if "no kernel image" in str(e).lower():
                    logger.error("CUDA kernel image not available for your GPU architecture!")
                    logger.error(f"GPU: {torch.cuda.get_device_name(0)}")
                    logger.error(f"Compute Capability: {torch.cuda.get_device_capability(0)}")
                    logger.error(f"PyTorch version: {torch.__version__}")
                    logger.error(f"CUDA version: {torch.version.cuda}")

                    if force_cuda:
                        logger.warning("--force-cuda specified, attempting to use CUDA anyway")
                        return "cuda"
                    elif fallback_to_cpu:
                        logger.warning("Falling back to CPU")
                        return "cpu"
                    else:
                        raise RuntimeError(
                            "CUDA is not compatible with your GPU. "
                            "Upgrade PyTorch with: pip install torch --index-url https://download.pytorch.org/whl/cu128"
                        )
                else:
                    raise

        # Check MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Using MPS (Apple Silicon) device")
            return "mps"

        # Default to CPU
        logger.info("Using CPU device")
        return "cpu"

    except ImportError:
        logger.warning("PyTorch not available, defaulting to CPU")
        return "cpu"


def print_gpu_status():
    """Print detailed GPU status information"""
    status = check_gpu_compatibility()

    print("\n" + "=" * 70)
    print("GPU STATUS")
    print("=" * 70)

    print(f"PyTorch version: {status['pytorch_version']}")
    print(f"CUDA available: {status['cuda_available']}")

    if status['cuda_available']:
        print(f"CUDA version: {status['cuda_version']}")
        print(f"Device count: {status['device_count']}")

        for device in status['devices']:
            print(f"\n  Device {device['id']}: {device['name']}")
            print(f"  Compute Capability: {device['compute_capability']}")

        if status['compatible']:
            print("\n✅ GPU is compatible and ready for training")
        else:
            print("\n❌ GPU compatibility issue detected")

        if status['warnings']:
            print("\nWarnings:")
            for warning in status['warnings']:
                print(f"  ⚠️  {warning}")

        if status['recommended_action']:
            print("\nRecommended action:")
            print(f"  {status['recommended_action']}")
    else:
        print("\n⚠️  No CUDA device available - will use CPU")
        if status['warnings']:
            for warning in status['warnings']:
                print(f"  {warning}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Run GPU diagnostics
    print_gpu_status()

    # Test device selection
    print("\nTesting device selection...")
    device = get_training_device(force_cuda="--force-cuda" in sys.argv)
    print(f"Selected device: {device}")

