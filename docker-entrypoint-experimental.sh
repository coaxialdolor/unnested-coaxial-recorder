#!/bin/bash
set -e

echo "=== Coaxial Recorder GPU Experimental Startup ==="
echo ""

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
    echo ""
    
    # Run runtime Lightning patch for RTX 5060 Ti
    echo "Applying Lightning runtime patches for GPU compatibility..."
    python utils/patch_lightning.py --apply-runtime || echo "Warning: Lightning patch failed (non-critical)"
    echo ""
    
    # CUDA sanity check
    echo "Running CUDA sanity check..."
    python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('Device:', torch.cuda.get_device_name(0))
print('Capability:', torch.cuda.get_device_capability(0))
print('PyTorch version:', torch.__version__)
print('CUDA version:', torch.version.cuda)
x = torch.zeros(1, device='cuda')
print('CUDA basic operations: OK')
print('')
print('Testing Conv2d...')
import torch.nn as nn
conv = nn.Conv2d(3, 64, 3).cuda()
test_input = torch.randn(1, 3, 32, 32).cuda()
output = conv(test_input)
print('Conv2d: OK')
print('')
print('Testing matrix multiplication...')
x = torch.randn(100, 100).cuda()
y = x @ x.T
print('Matrix multiplication: OK')
print('')
print('[OK] GPU is fully functional and ready for training!')
"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=== GPU Verification Passed ==="
        echo ""
    else
        echo ""
        echo "[WARNING] GPU test failed - training may not work"
        echo ""
    fi
else
    echo "[INFO] No GPU detected - will use CPU"
    echo ""
fi

echo "=== Starting Application ==="
echo ""

# Execute the command passed to the container
exec "$@"

