"""
Inspect the inner model.weights.h5 inside the .keras zip file
"""
import h5py
import zipfile
import os
import io

def print_h5_structure(obj, prefix="", max_depth=5, current_depth=0):
    if current_depth > max_depth:
        return
    if isinstance(obj, h5py.Group):
        for key in sorted(obj.keys()):
            child = obj[key]
            if isinstance(child, h5py.Dataset):
                print(f"{prefix}[DATA] {key} shape={child.shape} dtype={child.dtype}")
            else:
                print(f"{prefix}[GRP]  {key}/")
                print_h5_structure(child, prefix + "  ", max_depth, current_depth + 1)
    elif isinstance(obj, h5py.Dataset):
        print(f"{prefix}[DATA] shape={obj.shape}")

# Extract and inspect inner weights h5
keras_path = 'model/siamese_signature_model.keras'
with zipfile.ZipFile(keras_path, 'r') as z:
    print("=== config.json ===")
    config_data = z.read('config.json').decode('utf-8')
    print(config_data[:2000])
    
    print("\n=== model.weights.h5 structure ===")
    weights_data = z.read('model.weights.h5')
    with h5py.File(io.BytesIO(weights_data), 'r') as f:
        print("Top-level keys:", list(f.keys()))
        print_h5_structure(f, max_depth=6)
