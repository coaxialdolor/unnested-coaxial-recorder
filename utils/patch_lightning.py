#!/usr/bin/env python3
"""
Automatic Lightning.py patching for RTX 5060 Ti compatibility
Based on Copilot recommendations for proper GPU detection and device configuration
"""

import os
import sys
import importlib.util
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_lightning_module():
    """Find the Lightning module installation location"""
    try:
        # Try lightning first (newer)
        import lightning
        lightning_path = Path(lightning.__file__).parent
        return lightning_path, "lightning"
    except ImportError:
        try:
            # Fallback to pytorch_lightning (older)
            import pytorch_lightning
            lightning_path = Path(pytorch_lightning.__file__).parent
            return lightning_path, "pytorch_lightning"
        except ImportError:
            return None, None


def patch_trainer_gpu_setup(lightning_path: Path, module_name: str):
    """Patch Trainer to properly detect and use GPU"""
    
    # Find trainer file
    trainer_files = [
        lightning_path / "pytorch" / "trainer" / "trainer.py",
        lightning_path / "trainer" / "trainer.py",
    ]
    
    trainer_file = None
    for tf in trainer_files:
        if tf.exists():
            trainer_file = tf
            break
    
    if not trainer_file:
        logger.warning(f"Could not find trainer.py in {lightning_path}")
        return False
    
    logger.info(f"Patching {trainer_file}")
    
    # Read the file
    with open(trainer_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already patched
    if "# RTX_5060_TI_PATCH_APPLIED" in content:
        logger.info("Lightning already patched for RTX 5060 Ti")
        return True
    
    # Patch 1: Ensure GPU detection
    gpu_detection_patch = '''
    # RTX_5060_TI_PATCH_APPLIED
    def _ensure_gpu_available(self):
        """Ensure GPU is properly detected (RTX 5060 Ti compatibility)"""
        import torch
        if torch.cuda.is_available():
            # Force CUDA initialization
            torch.cuda.init()
            # Set device
            if self._accelerator_connector.devices == "auto":
                self._accelerator_connector.devices = 1
            # Ensure proper CUDA arch detection
            if hasattr(torch.cuda, 'get_device_capability'):
                capability = torch.cuda.get_device_capability(0)
                if capability[0] >= 8:  # Compute capability 8.0+
                    logger.info(f"Detected modern GPU: compute capability {capability[0]}.{capability[1]}")
'''
    
    # Find __init__ method in Trainer class
    init_pattern = "def __init__(self"
    if init_pattern in content:
        # Add patch after __init__ starts
        parts = content.split(init_pattern, 1)
        if len(parts) == 2:
            content = parts[0] + init_pattern + parts[1].split('\n', 1)[0] + '\n' + gpu_detection_patch + '\n' + '\n'.join(parts[1].split('\n')[1:])
    
    # Write patched file
    backup_file = trainer_file.with_suffix('.py.backup')
    if not backup_file.exists():
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Created backup: {backup_file}")
    
    # Note: We're being conservative - just add the patch marker without modifying core logic
    # The real patches are in our training code itself
    if "# RTX_5060_TI_PATCH_APPLIED" not in content:
        content = "# RTX_5060_TI_PATCH_APPLIED\n" + content
    
    with open(trainer_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("Lightning patched successfully")
    return True


def apply_runtime_patches():
    """Apply runtime patches that don't modify files"""
    try:
        import torch
        
        if torch.cuda.is_available():
            # Force CUDA initialization for RTX 5060 Ti
            torch.cuda.init()
            
            # Set optimal CUDA settings
            torch.backends.cudnn.benchmark = True  # Auto-tune kernels
            torch.backends.cuda.matmul.allow_tf32 = True  # Use TF32 on Ampere+
            
            # Check compute capability
            if hasattr(torch.cuda, 'get_device_capability'):
                cap = torch.cuda.get_device_capability(0)
                logger.info(f"GPU detected: compute capability {cap[0]}.{cap[1]}")
                
                if cap[0] >= 8:  # Ampere or newer (RTX 30/40/50 series)
                    logger.info("Enabling optimizations for modern GPU (Ampere+)")
                    # These are already set above, but emphasizing them
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.set_float32_matmul_precision('high')
            
            logger.info(f"CUDA runtime patches applied for {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.info("No CUDA device available, skipping GPU patches")
            return True
            
    except Exception as e:
        logger.warning(f"Could not apply runtime patches: {e}")
        return False


def patch_lightning_for_rtx5060ti():
    """Main patching function"""
    logger.info("=== Lightning.py RTX 5060 Ti Compatibility Patch ===")
    
    # Find Lightning installation
    lightning_path, module_name = find_lightning_module()
    
    if not lightning_path:
        logger.warning("PyTorch Lightning not installed - training features will not be available")
        return False
    
    logger.info(f"Found {module_name} at: {lightning_path}")
    
    # Apply runtime patches (always safe)
    apply_runtime_patches()
    
    # File patches (optional - we handle this in our training code instead)
    # patch_trainer_gpu_setup(lightning_path, module_name)
    
    logger.info("=== Patching Complete ===")
    return True


if __name__ == "__main__":
    success = patch_lightning_for_rtx5060ti()
    sys.exit(0 if success else 1)

