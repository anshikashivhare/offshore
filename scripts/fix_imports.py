import os

ROOT_DIR = "/Users/apple/Downloads/offshore/ml"

replacements = {
    "ml.seaice_model.data": "ml.data.seaice.data",
    "ml.seaice_model.real_data_loader": "ml.data.seaice.real_data_loader",
    "ml.seaice_model.grid_sequence": "ml.data.seaice.grid_sequence",
    "ml.seaice_model.convlstm": "ml.models.architectures.convlstm",
    "ml.seaice_model.predict": "ml.inference.seaice_predict",
    "ml.seaice_model.train": "ml.training.seaice_train",
    "ml.seaice_model.train_convlstm": "ml.training.seaice_train_convlstm",
    "ml/seaice_model/seaice_xgb.json": "ml/models/weights/seaice_xgb.json",
    
    "ml.trajectory_model.data": "ml.data.trajectory.data",
    "ml.trajectory_model.real_data_loader": "ml.data.trajectory.real_data_loader",
    "ml.trajectory_model.sequence_data": "ml.data.trajectory.sequence_data",
    "ml.trajectory_model.lstm_model": "ml.models.architectures.lstm_model",
    "ml.trajectory_model.predict": "ml.inference.trajectory_predict",
    "ml.trajectory_model.train": "ml.training.trajectory_train",
    "ml.trajectory_model.train_lstm": "ml.training.trajectory_train_lstm",
    
    "ml.route_optimizer.optimizer": "ml.inference.route_optimizer",
}

for root, _, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    content = f.read()
                except UnicodeDecodeError:
                    continue
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

print("Imports fixed.")
