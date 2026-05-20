import os
import json
import numpy as np
from pathlib import Path
from app import create_app
from app.extensions import db
from app.database.models import ReferenceSignature
from app.ai.predictor import get_predictor

def recompute_all_embeddings():
    app = create_app()
    with app.app_context():
        # Get predictor
        predictor = get_predictor(app.config)
        
        # Load all reference signatures
        signatures = ReferenceSignature.query.all()
        print(f"Found {len(signatures)} reference signatures to recompute.")
        
        for idx, sig in enumerate(signatures):
            print(f"[{idx+1}/{len(signatures)}] Processing user {sig.user_id}, signature ID {sig.id}...")
            
            # Check if original image exists
            if not os.path.exists(sig.image_path):
                print(f"Warning: Original image path does not exist: {sig.image_path}")
                continue
                
            # Recompute processed paths
            upload_folder = app.config['UPLOAD_FOLDER']
            processed_path = os.path.join(upload_folder, 'processed', 
                                         f'user_{sig.user_id}_ref_{sig.id}_processed.png')
            embedding_path = os.path.join(upload_folder, 'embeddings',
                                         f'user_{sig.user_id}_ref_{sig.id}_embedding.npy')
                                         
            # Ensure folders exist
            Path(processed_path).parent.mkdir(parents=True, exist_ok=True)
            Path(embedding_path).parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Extract new embedding using the preprocessed image path internally
                embedding, _ = predictor.preprocess_and_extract_embedding(sig.image_path, processed_path)
                
                # Save embedding to npy
                np.save(embedding_path, embedding)
                
                # Update database record
                sig.processed_image_path = processed_path
                sig.embedding_path = embedding_path
                sig.embedding = embedding.tolist()
                sig.embedding_shape = str(embedding.shape)
                
                print(f"Successfully recomputed embedding. Shape: {sig.embedding_shape}")
            except Exception as e:
                print(f"Error processing signature ID {sig.id}: {str(e)}")
                
        db.session.commit()
        print("Database commit successful. All embeddings updated!")

if __name__ == '__main__':
    recompute_all_embeddings()
