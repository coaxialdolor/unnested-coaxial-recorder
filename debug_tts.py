#!/usr/bin/env python3
import sys
sys.path.append('/app')
import traceback
from utils.tts import synthesize_speech_with_checkpoint

try:
    result = synthesize_speech_with_checkpoint(
        'Hej', 
        '/app/models/checkpoints/final_model.ckpt', 
        '/tmp/test_output.wav', 
        1.0, 
        0.667
    )
    print(f'Result: {result}')
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
