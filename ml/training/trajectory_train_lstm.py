"""
Trains the LSTM iceberg model and compares against naive + XGBoost.
Run: python -m ml.training.trajectory_train_lstm
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ml.models.architectures.lstm_model import IcebergLSTM
from ml.path_utils import get_model_path
from ml.preprocessing.trajectory.data import generate_synthetic_tracks
from ml.preprocessing.trajectory.sequence_data import make_sequences
from ml.training_guard import safe_train


def train_lstm(seq_len=5, epochs=100, lr=3e-3, batch_size=64):
    print("Generating data...")
    df = generate_synthetic_tracks(time_varying_env=True)
    X, y = make_sequences(df, seq_len=seq_len)

    train_split = int(len(X) * 0.7)
    val_split = int(len(X) * 0.85)
    X_train, y_train = X[:train_split], y[:train_split]
    X_val, y_val = X[train_split:val_split], y[train_split:val_split]
    X_test, y_test = X[val_split:], y[val_split:]
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    X_train_t, y_train_t = torch.tensor(X_train), torch.tensor(y_train)
    X_val_t, y_val_t = torch.tensor(X_val), torch.tensor(y_val)
    X_test_t, y_test_t = torch.tensor(X_test), torch.tensor(y_test)

    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val_t, y_val_t), batch_size=batch_size, shuffle=False)


    model = IcebergLSTM(input_size=X.shape[2], hidden_size=32)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    checkpoint_path = get_model_path("lstm_model_checkpoint.pt")

    def train_one_epoch(epoch):
        model.train()
        total_loss = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            preds = model(X_batch)
            loss = loss_fn(preds, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * X_batch.size(0)
        avg_loss = total_loss / len(train_loader.dataset)
        if (epoch + 1) % 50 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} — train MSE: {avg_loss:.6f}")
        return avg_loss

    def val_step_fn(epoch):
        model.eval()
        total_val_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                preds = model(X_batch)
                val_loss = loss_fn(preds, y_batch)
                total_val_loss += val_loss.item() * X_batch.size(0)
        avg_val_loss = total_val_loss / len(val_loader.dataset)
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} — val MSE: {avg_val_loss:.6f}")
        return avg_val_loss

    print("Training...")
    result = safe_train(
        train_step_fn=train_one_epoch,
        num_epochs=epochs,
        val_step_fn=val_step_fn,
        patience=10,
        checkpoint_fn=lambda: torch.save(model.state_dict(), checkpoint_path),
        model_name="trajectory_lstm",
    )

    if result["status"] == "failed":
        print(
            f"\nTraining stopped early at epoch {result['last_epoch']+1}/{epochs}: {result['error']}"
        )
        print(
            f"Progress through epoch {result['last_epoch']} was checkpointed to {checkpoint_path}"
        )
        return None, None, None

    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t)
        rmse_lat = torch.sqrt(loss_fn(test_preds[:, 0], y_test_t[:, 0])).item()
        rmse_lon = torch.sqrt(loss_fn(test_preds[:, 1], y_test_t[:, 1])).item()

    naive_rmse_lat = np.sqrt(np.mean(y_test[:, 0] ** 2))
    naive_rmse_lon = np.sqrt(np.mean(y_test[:, 1] ** 2))

    print(f"\nLSTM test RMSE — delta_lat: {rmse_lat:.5f}, delta_lon: {rmse_lon:.5f}")
    print(
        f"Naive RMSE — delta_lat: {naive_rmse_lat:.5f}, delta_lon: {naive_rmse_lon:.5f}"
    )

    import uuid

    run_id = str(uuid.uuid4())
    artifact_uri = get_model_path(f"lstm_model_{run_id}.pt")

    torch.save(model.state_dict(), artifact_uri)
    print(f"Model saved to {artifact_uri}")

    from mlops.experiment_log import log_experiment

    log_experiment(
        run_id=run_id,
        model_name="trajectory_lstm",
        data_source="synthetic_time_varying",
        artifact_uri=artifact_uri,
        metrics={
            "rmse_lat": float(rmse_lat),
            "rmse_lon": float(rmse_lon),
            "naive_rmse_lat": float(naive_rmse_lat),
            "naive_rmse_lon": float(naive_rmse_lon),
        },
        hyperparams={"hidden_size": 32, "epochs": epochs, "lr": lr, "seq_len": seq_len},
    )

    return model, (rmse_lat, rmse_lon), artifact_uri


if __name__ == "__main__":
    train_lstm()
