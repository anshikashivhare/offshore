import os
import re
import shutil

ROOT_DIR = "/Users/apple/Downloads/offshore"

moves = {
    "ml/seaice_model/data.py": "ml/data/seaice/data.py",
    "ml/seaice_model/real_data_loader.py": "ml/data/seaice/real_data_loader.py",
    "ml/seaice_model/grid_sequence.py": "ml/data/seaice/grid_sequence.py",
    "ml/trajectory_model/data.py": "ml/data/trajectory/data.py",
    "ml/trajectory_model/real_data_loader.py": "ml/data/trajectory/real_data_loader.py",
    "ml/trajectory_model/sequence_data.py": "ml/data/trajectory/sequence_data.py",
    
    "ml/seaice_model/train.py": "ml/training/seaice_train.py",
    "ml/seaice_model/train_convlstm.py": "ml/training/seaice_train_convlstm.py",
    "ml/trajectory_model/train.py": "ml/training/trajectory_train.py",
    "ml/trajectory_model/train_lstm.py": "ml/training/trajectory_train_lstm.py",
    
    "ml/seaice_model/convlstm.py": "ml/models/architectures/convlstm.py",
    "ml/trajectory_model/lstm_model.py": "ml/models/architectures/lstm_model.py",
    
    "ml/models/weights/seaice_xgb.json": "ml/models/weights/seaice_xgb.json",
    "ml/models/weights/convlstm.pt": "ml/models/weights/convlstm.pt",
    "ml/models/weights/lstm_model.pt": "ml/models/weights/lstm_model.pt",
    
    "ml/seaice_model/predict.py": "ml/inference/seaice_predict.py",
    "ml/trajectory_model/predict.py": "ml/inference/trajectory_predict.py",
    "ml/route_optimizer/optimizer.py": "ml/inference/route_optimizer.py"
}

replacements = {
    "ml.data.seaice.data": "ml.data.seaice.data",
    "ml.data.seaice.real_data_loader": "ml.data.seaice.real_data_loader",
    "ml.data.seaice.grid_sequence": "ml.data.seaice.grid_sequence",
    "ml.models.architectures.convlstm": "ml.models.architectures.convlstm",
    "ml.inference.seaice_predict": "ml.inference.seaice_predict",
    
    "ml.data.trajectory.data": "ml.data.trajectory.data",
    "ml.data.trajectory.real_data_loader": "ml.data.trajectory.real_data_loader",
    "ml.data.trajectory.sequence_data": "ml.data.trajectory.sequence_data",
    "ml.models.architectures.lstm_model": "ml.models.architectures.lstm_model",
    "ml.inference.trajectory_predict": "ml.inference.trajectory_predict",
    
    "ml.inference.route_optimizer": "ml.inference.route_optimizer",
    
    "ml/models/weights/seaice_xgb.json": "ml/models/weights/seaice_xgb.json",
    "ml/models/weights/convlstm.pt": "ml/models/weights/convlstm.pt",
    "ml/models/weights/trajectory_model.joblib": "ml/models/weights/trajectory_model.joblib",
    "ml/models/weights/lstm_model.pt": "ml/models/weights/lstm_model.pt",
}

# Create dirs
for dest in moves.values():
    os.makedirs(os.path.join(ROOT_DIR, os.path.dirname(dest)), exist_ok=True)

# Move files
for src, dest in moves.items():
    src_path = os.path.join(ROOT_DIR, src)
    dest_path = os.path.join(ROOT_DIR, dest)
    if os.path.exists(src_path):
        shutil.move(src_path, dest_path)

# Update imports in all python files
for root, _, files in os.walk(ROOT_DIR):
    if "node_modules" in root or ".venv" in root or "venv" in root or ".git" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r") as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
            
            if new_content != content:
                with open(filepath, "w") as f:
                    f.write(new_content)

print("ML restructuring and imports updated.")
