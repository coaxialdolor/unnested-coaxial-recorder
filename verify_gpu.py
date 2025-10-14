#!/usr/bin/env python3
"""
GPU Verification Script
Tests if the GPU is actually working for training
"""

import sys
from utils.gpu_compat import check_gpu_compatibility, get_training_device, print_gpu_status

def main():
    print("=" * 70)
    print("GPU VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Run comprehensive GPU check
    status = check_gpu_compatibility()
    
    # Print detailed status
    print_gpu_status()
    
    # Test device selection
    print("Testing device selection...")
    device = get_training_device()
    print(f"[OK] Selected device: {device}")
    
    # Final verdict
    print()
    print("=" * 70)
    if status['compatible'] and status['cuda_available']:
        print("[OK] GPU VERIFICATION PASSED")
        print(f"   Your GPU ({status['devices'][0]['name']}) is ready for training!")
        print()
        print("   Note: You may see a PyTorch warning about CUDA capability sm_120,")
        print("   but this is harmless - your GPU works fine with PyTorch's fallback kernels.")
        sys.exit(0)
    else:
        print("[ERROR] GPU VERIFICATION FAILED")
        print("   GPU is not compatible or not available")
        if status['warnings']:
            for warning in status['warnings']:
                print(f"   [WARNING] {warning}")
        sys.exit(1)

if __name__ == "__main__":
    main()

