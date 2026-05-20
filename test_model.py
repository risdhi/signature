"""
Validate that the MobileNetV2 fallback produces discriminative embeddings.
Run: .venv/bin/python test_model.py
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

# Reset singletons so we always do a fresh load
from app.ai.load_model import ModelLoader
from app.ai import load_model as lm_module

ModelLoader._instance = None
ModelLoader._model = None
ModelLoader._model_type = None

from app.ai.load_model import load_pretrained_model

model_path = 'model/siamese_signature_model.keras'
embedding_dim = 128

print("=" * 65)
print("  Testing Signature Verification Model")
print("=" * 65)
model = load_pretrained_model(model_path, embedding_dim)
model_type = ModelLoader.get_model_type()
print(f"\n✅ Model loaded  —  type: {model_type}")
print(f"   Input  : {model.input_shape}")
print(f"   Output : {model.output_shape}")

# ---------- Similarity tests ----------
def embed(m, arr):
    e = m.predict(arr, verbose=0).squeeze()
    n = np.linalg.norm(e)
    return e / n if n > 1e-8 else e

def cosine(a, b):
    return float(np.dot(a, b))

def euclid(a, b):
    return float(np.linalg.norm(a - b))

input_shape = model.input_shape[1:]   # (H, W, C)

# Same image → must be ~1.0
img_x = np.random.rand(1, *input_shape).astype(np.float32) * 255
emb_x1 = embed(model, img_x)
emb_x2 = embed(model, img_x)
cos_same = cosine(emb_x1, emb_x2)

# Two completely different random images
img_a = np.random.rand(1, *input_shape).astype(np.float32) * 255
img_b = np.random.rand(1, *input_shape).astype(np.float32) * 255
emb_a = embed(model, img_a)
emb_b = embed(model, img_b)
cos_rand = cosine(emb_a, emb_b)
euc_rand = euclid(emb_a, emb_b)

# All-zero vs all-ones (extreme difference)
img_zeros = np.zeros((1, *input_shape), dtype=np.float32)
img_ones  = np.ones ((1, *input_shape), dtype=np.float32) * 255
emb_zeros = embed(model, img_zeros)
emb_ones  = embed(model, img_ones)
cos_ext = cosine(emb_zeros, emb_ones)
euc_ext = euclid(emb_zeros, emb_ones)

print("\n" + "─" * 65)
print("  Embedding Similarity Tests")
print("─" * 65)
print(f"  Same image  (cos)  : {cos_same:.6f}   [expected ≈ 1.0]")
print(f"  Random pair (cos)  : {cos_rand:.6f}   [expected < 0.75 threshold]")
print(f"  Random pair (euc)  : {euc_rand:.6f}   [expected > 0.72 threshold]")
print(f"  Zeros vs Ones (cos): {cos_ext:.6f}")
print(f"  Zeros vs Ones (euc): {euc_ext:.6f}")
print("─" * 65)

# Verdict
if cos_rand > 0.98:
    print("\n❌  FAIL  — Embeddings still DEGENERATE (cos ≈ 1.0 for different images)")
    print("         MobileNetV2 fallback did not activate correctly.")
elif cos_rand > 0.75:
    print(f"\n⚠️  WARN  — Random images score {cos_rand:.3f} > 0.75 threshold → classified GENUINE")
    print("         Consider lowering SIMILARITY_THRESHOLD to ~0.70.")
else:
    print(f"\n✅  PASS  — Random images score {cos_rand:.3f} < 0.75 threshold → correctly FORGED")
    print("         Model is working. Remember to recompute existing DB embeddings:")
    print("         python recompute_embeddings.py")
print("=" * 65)
