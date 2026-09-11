"""
Trains the ConvLSTM and compares against the persistence baseline.
Run: python -m ml.training.seaice_train_convlstm
"""
import numpy as np
import torch
import torch.nn as nn

from ml.preprocessing.seaice.data import generate_synthetic_timeseries
from ml.preprocessing.seaice.grid_sequence import dataframe_to_grid_sequence, make_sequences
from ml.models.architectures.convlstm import SeaIceConvLSTM
from ml.path_utils import get_model_path
from ml.training_guard import safe_train


def train_convlstm(input_len=5, epochs=150, lr=3e-3):
    print("Generating data...")
    df = generate_synthetic_timeseries(spatial_correlation=True)
    grid_seq = dataframe_to_grid_sequence(df)

    X, y = make_sequences(grid_seq, input_len=input_len)
    train_split = int(len(X) * 0.7)
    val_split = int(len(X) * 0.85)
    X_train, y_train = X[:train_split], y[:train_split]
    X_val, y_val = X[train_split:val_split], y[train_split:val_split]
    X_test, y_test = X[val_split:], y[val_split:]
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    X_train_t = torch.tensor(X_train).unsqueeze(2)
    y_train_t = torch.tensor(y_train)
    X_val_t = torch.tensor(X_val).unsqueeze(2)
    y_val_t = torch.tensor(y_val)
    X_test_t = torch.tensor(X_test).unsqueeze(2)
    y_test_t = torch.tensor(y_test)

    model = SeaIceConvLSTM(hidden_channels=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    checkpoint_path = get_model_path("convlstm_checkpoint.pt")

    def train_one_epoch(epoch):
        model.train()
        optimizer.zero_grad()
        preds = model(X_train_t)
        loss = loss_fn(preds, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} — train MSE: {loss.item():.5f}")
        return loss.item()

    def val_step_fn(epoch):
        model.eval()
        with torch.no_grad():
            preds = model(X_val_t)
            val_loss = loss_fn(preds, y_val_t)
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} — val MSE: {val_loss.item():.5f}")
            return val_loss.item()

    print("Training...")
    result = safe_train(
        train_step_fn=train_one_epoch,
        num_epochs=epochs,
        val_step_fn=val_step_fn,
        patience=15,
        checkpoint_fn=lambda: torch.save(model.state_dict(), checkpoint_path),
        model_name="seaice_convlstm",
    )

    if result["status"] == "failed":
        print(f"\nTraining stopped early at epoch {result['last_epoch']+1}/{epochs}: {result['error']}")
        print(f"Progress through epoch {result['last_epoch']} was checkpointed to {checkpoint_path}")
        return None, None, None, None

    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t)
        test_rmse = torch.sqrt(loss_fn(test_preds, y_test_t)).item()

    last_input_grid = X_test[:, -1]
    persistence_rmse = np.sqrt(np.mean((last_input_grid - y_test) ** 2))

    print(f"\nConvLSTM test RMSE: {test_rmse:.5f}")
    print(f"Persistence baseline RMSE: {persistence_rmse:.5f}")

    import uuid
    run_id = str(uuid.uuid4())
    artifact_uri = get_model_path(f"convlstm_{run_id}.pt")

    torch.save(model.state_dict(), artifact_uri)
    print(f"Model saved to {artifact_uri}")
    
    from mlops.experiment_log import log_experiment
    log_experiment(
        run_id=run_id,
        model_name="seaice_convlstm",
        data_source="synthetic",
        artifact_uri=artifact_uri,
        metrics={"test_rmse": float(test_rmse), "persistence_rmse": float(persistence_rmse)},
        hyperparams={"hidden_channels": 8, "epochs": epochs, "lr": lr, "input_len": input_len},
    )

    return model, test_rmse, persistence_rmse, artifact_uri


if __name__ == "__main__":
    train_convlstm()
