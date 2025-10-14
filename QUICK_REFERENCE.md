# GPU Training Quick Reference

## 🚀 One-Command Setup

```bash
# Build and run in one go (Windows)
docker build -f Dockerfile.gpuexperimental -t coaxial-gpu:experimental . && docker run --gpus all -p 8000:8000 -v "%cd%/voices:/app/voices" -v "%cd%/output:/app/output" -v "%cd%/models:/app/models" -v "%cd%/checkpoints:/app/checkpoints" --name coaxial-gpu-experimental -d coaxial-gpu:experimental
```

## 📋 Essential Commands

### Build Image
```bash
docker build -f Dockerfile.gpuexperimental -t coaxial-gpu:experimental .
```

### Run Container
```bash
docker run --gpus all -p 8000:8000 -v "%cd%/voices:/app/voices" -v "%cd%/output:/app/output" -v "%cd%/models:/app/models" -v "%cd%/checkpoints:/app/checkpoints" --name coaxial-gpu-experimental -d coaxial-gpu:experimental
```

### Check GPU
```bash
docker exec coaxial-gpu-experimental nvidia-smi
```

### Run Training
```bash
docker exec coaxial-gpu-experimental python train_model.py --profile-id "PROFILE" --prompt-list-id "PROMPT_LIST" --language-code "sv-SE" --model-size medium --epochs 100 --use-gpu --mixed-precision
```

### View Logs
```bash
docker logs coaxial-gpu-experimental
```

### Stop Container
```bash
docker stop coaxial-gpu-experimental
```

### Remove Container
```bash
docker stop coaxial-gpu-experimental && docker rm coaxial-gpu-experimental
```

## 🔧 What's Fixed

| Issue | Solution | Status |
|-------|----------|--------|
| PyTorch sm_120 support | PyTorch nightly build | ✅ Auto |
| Audio loading crashes | Use soundfile | ✅ Auto |
| DataLoader crashes | num_workers=0 | ✅ Auto |
| Device mismatch | .to(audio.device) | ✅ Auto |
| Export fails | pydub + ffmpeg | ✅ Auto |
| Lightning compatibility | Runtime patches | ✅ Auto |

## 📊 Expected Performance

- **GPU Utilization**: 95-100%
- **Training Speed**: 1-2 sec/epoch (25 samples)
- **Memory Usage**: 2-3 GB GPU
- **Loss**: 132 → 0.07 (100 epochs)

## 🔍 Quick Checks

### GPU Working?
```bash
docker exec coaxial-gpu-experimental python -c "import torch; print('GPU:', torch.cuda.is_available())"
```

### PyTorch Version?
```bash
docker exec coaxial-gpu-experimental python -c "import torch; print(torch.__version__)"
```

### CUDA Version?
```bash
docker exec coaxial-gpu-experimental python -c "import torch; print(torch.version.cuda)"
```

## 📚 Documentation

- **GPU_SETUP_SUMMARY.md** - Overview and quick start
- **GPU_TRAINING_FIXES.md** - Detailed technical explanation
- **EXPERIMENTAL_DOCKER_GUIDE.md** - Complete usage guide
- **QUICK_REFERENCE.md** - This file

## 🎯 Common Tasks

### Start Training
```bash
docker exec coaxial-gpu-experimental python train_model.py \
  --profile-id "latestPetter ny svenska pc" \
  --prompt-list-id "latestPetter ny svenska pc_sv-SE_0000000001_0300000050_General" \
  --language-code "sv-SE" \
  --model-size medium \
  --epochs 100 \
  --use-gpu \
  --mixed-precision
```

### Access Web Interface
```
http://localhost:8000
```

### Export Dataset
Use the web interface at http://localhost:8000/export

## ⚡ Pro Tips

1. **Always mount volumes** - Your data persists outside the container
2. **Check logs first** - `docker logs coaxial-gpu-experimental` shows startup info
3. **GPU verification** - Container automatically checks GPU on startup
4. **No manual config** - Everything is automatic!

## 🐛 Quick Fixes

### Container won't start
```bash
docker logs coaxial-gpu-experimental
```

### GPU not detected
```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi
```

### Training fails
```bash
docker exec coaxial-gpu-experimental python -c "import torch; print(torch.cuda.is_available())"
```

## 📞 Need Help?

1. Check **GPU_SETUP_SUMMARY.md** for overview
2. Check **GPU_TRAINING_FIXES.md** for technical details
3. Check **EXPERIMENTAL_DOCKER_GUIDE.md** for complete guide
4. Check container logs: `docker logs coaxial-gpu-experimental`

## ✨ Success Indicators

✅ Container starts without errors  
✅ GPU detected in logs  
✅ CUDA sanity check passes  
✅ Training starts and loss decreases  
✅ Model saves successfully  

All of these happen automatically! 🎉

