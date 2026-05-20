"""
Inspect internal structure of the .h5 and .keras model files
to understand how to correctly load their weights.
"""
import h5py
import sys

def print_h5_structure(name, obj, indent=0):
    prefix = "  " * indent
    if isinstance(obj, h5py.Group):
        print(f"{prefix}[GROUP] {name}")
        for key in obj.keys():
            print_h5_structure(key, obj[key], indent + 1)
    elif isinstance(obj, h5py.Dataset):
        print(f"{prefix}[DATASET] {name} shape={obj.shape} dtype={obj.dtype}")

def inspect_h5(path):
    print(f"\n{'='*60}")
    print(f"Inspecting: {path}")
    print('='*60)
    with h5py.File(path, 'r') as f:
        print("Top-level keys:", list(f.keys()))
        # Print first 2 levels
        for key in f.keys():
            print_h5_structure(key, f[key], indent=0)

def inspect_model_config(path):
    """Try to read model config from H5"""
    with h5py.File(path, 'r') as f:
        if 'model_config' in f.attrs:
            import json
            config = json.loads(f.attrs['model_config'])
            print("\n--- Model Config ---")
            print(json.dumps(config, indent=2)[:3000])
        
        # Check for keras version
        if 'keras_version' in f.attrs:
            print("\nKeras version in file:", f.attrs['keras_version'])
        if 'backend' in f.attrs:
            print("Backend:", f.attrs['backend'])

if __name__ == '__main__':
    h5_path = 'model/siamese_signature_model.h5'
    keras_path = 'model/siamese_signature_model.keras'
    
    inspect_h5(h5_path)
    inspect_model_config(h5_path)
    
    # Also try to load the .keras file as a zip (it's actually a zip archive)
    print(f"\n\n{'='*60}")
    print(f"Inspecting .keras file as ZIP: {keras_path}")
    print('='*60)
    import zipfile, os
    try:
        with zipfile.ZipFile(keras_path, 'r') as z:
            print("Contents of .keras zip:")
            for name in z.namelist():
                info = z.getinfo(name)
                print(f"  {name}  ({info.file_size} bytes)")
    except Exception as e:
        print(f"Not a zip: {e}")
