#!/bin/bash
set -e

echo "=== Coaxial Recorder GPU Startup ==="
echo ""

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
    echo ""
    
    # Run runtime Lightning patch for RTX 5060 Ti
    echo "Applying Lightning runtime patches for GPU compatibility..."
    conda run --no-capture-output -n coaxial python utils/patch_lightning.py --apply-runtime || echo "Warning: Lightning patch failed (non-critical)"
    echo ""
    
    # Test GPU
    echo "Testing GPU..."
    conda run --no-capture-output -n coaxial python -c "
import torch
if torch.cuda.is_available():
    try:
        x = torch.zeros(10, 10).cuda()
        y = x @ x.T
        print('[OK] GPU test passed - CUDA kernels available')
    except RuntimeError as e:
        if 'no kernel image' in str(e).lower():
            print('[ERROR] CUDA kernels not available for this GPU architecture')
            print('[INFO] Falling back to CPU training')
        else:
            raise
else:
    print('[INFO] No GPU available - will use CPU')
"
else
    echo "[INFO] No NVIDIA GPU detected - will use CPU"
fi

echo ""
echo "=== Starting Application ==="
echo ""

# Run the main application
exec "$@"

