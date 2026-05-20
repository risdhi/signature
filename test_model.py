"""
Test model loading and verify weights are actually loaded (not random).
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from app.ai.load_model import ModelLoader, load_pretrained_model

# Reset singleton so we don't use cached model from previous test
ModelLoader._instance = None
ModelLoader._model = None

model_path = 'model/siamese_signature_model.keras'
embedding_dim = 128

print("=" * 60)
print("Loading model with fixed loader...")
print("=" * 60)
model = load_pretrained_model(model_path, embedding_dim)
print(f"\nModel loaded: {model.name}")
model.summary()

# Test 1: Same image → similarity must be 1.0
img_same = np.random.rand(1, 105, 105, 1).astype(np.float32)
emb_same_a = model.predict(img_same, verbose=0).squeeze()
emb_same_b = model.predict(img_same, verbose=0).squeeze()
emb_same_a /= (np.linalg.norm(emb_same_a) + 1e-8)
emb_same_b /= (np.linalg.norm(emb_same_b) + 1e-8)
cos_same = float(np.dot(emb_same_a, emb_same_b))

# Test 2: Two completely different random images
img_a = np.random.rand(1, 105, 105, 1).astype(np.float32)
img_b = np.random.rand(1, 105, 105, 1).astype(np.float32)
emb_a = model.predict(img_a, verbose=0).squeeze()
emb_b = model.predict(img_b, verbose=0).squeeze()
emb_a /= (np.linalg.norm(emb_a) + 1e-8)
emb_b /= (np.linalg.norm(emb_b) + 1e-8)
cos_diff = float(np.dot(emb_a, emb_b))
euc_diff = float(np.linalg.norm(emb_a - emb_b))

# Test 3: All-zeros vs all-ones
img_zero = np.zeros((1, 105, 105, 1), dtype=np.float32)
img_ones = np.ones((1, 105, 105, 1), dtype=np.float32)
emb_zero = model.predict(img_zero, verbose=0).squeeze()
emb_ones = model.predict(img_ones, verbose=0).squeeze()
emb_zero /= (np.linalg.norm(emb_zero) + 1e-8)
emb_ones /= (np.linalg.norm(emb_ones) + 1e-8)
cos_zero_ones = float(np.dot(emb_zero, emb_ones))
euc_zero_ones = float(np.linalg.norm(emb_zero - emb_ones))

print("\n" + "=" * 60)
print("VERIFICATION TESTS")
print("=" * 60)
print(f"Same image cosine similarity      : {cos_same:.6f}  (expected ~1.0)")
print(f"Random vs Random cosine similarity: {cos_diff:.6f}  (expected < 0.82 if weights loaded)")
print(f"Random vs Random euclidean dist   : {euc_diff:.6f}  (expected > 0.25 if weights loaded)")
print(f"Zeros vs Ones cosine similarity   : {cos_zero_ones:.6f}")
print(f"Zeros vs Ones euclidean dist      : {euc_zero_ones:.6f}")

print("\n" + "=" * 60)
if cos_diff > 0.98:
    print("❌ WEIGHTS STILL RANDOM — cosine similarity near 1.0 for different images!")
    print("   Check logs above for any weight loading errors.")
elif cos_diff > 0.82:
    print(f"⚠️  WARNING: Different images still score {cos_diff:.3f} cosine similarity > 0.82 threshold")
    print("   They will be classified as GENUINE. Consider tightening thresholds.")
else:
    print(f"✅ Weights loaded correctly! Random images score {cos_diff:.3f} < 0.82 threshold.")
    print("   The model should now correctly detect forged signatures.")
print("=" * 60)
