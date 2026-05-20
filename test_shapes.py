import numpy as np
import cv2
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.ai.load_model import load_pretrained_model, ModelLoader

# Load model
model = load_pretrained_model('model/siamese_signature_model.keras', 128)
input_shape = model.input_shape[1:]

# Create a circle image
img_circle = np.ones(input_shape, dtype=np.uint8) * 255
cv2.circle(img_circle, (input_shape[1]//2, input_shape[0]//2), 40, (0, 0, 0), -1)

# Create a cross/X image
img_cross = np.ones(input_shape, dtype=np.uint8) * 255
cv2.line(img_cross, (20, 20), (input_shape[1]-20, input_shape[0]-20), (0, 0, 0), 10)
cv2.line(img_cross, (input_shape[1]-20, 20), (20, input_shape[0]-20), (0, 0, 0), 10)

# Save temporarily to test preprocessing pipeline
cv2.imwrite('circle.png', img_circle)
cv2.imwrite('cross.png', img_cross)

# Extract using our EmbeddingExtractor
from app.ai.embedding_model import get_embedding_extractor
extractor = get_embedding_extractor(input_shape[:2])

emb_circle = extractor.extract_embedding('circle.png')
emb_cross = extractor.extract_embedding('cross.png')

# Clean up
if os.path.exists('circle.png'): os.remove('circle.png')
if os.path.exists('cross.png'): os.remove('cross.png')

def cosine(a, b):
    return float(np.dot(a, b))

def euclidean(a, b):
    return float(np.linalg.norm(a - b))

cos_sim = cosine(emb_circle, emb_cross)
euc_dist = euclidean(emb_circle, emb_cross)

print("=" * 60)
print("MobileNetV2 Shape Comparison:")
print("=" * 60)
print(f"Cosine Similarity (Circle vs Cross): {cos_sim:.4f}")
print(f"Euclidean Distance (Circle vs Cross): {euc_dist:.4f}")
print("=" * 60)
