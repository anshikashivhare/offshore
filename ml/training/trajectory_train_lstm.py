"""
Trains the LSTM iceberg model and compares against naive + XGBoost.
Run: python -m ml.training.trajectory_train_lstm
"""
import numpy as np
import torch
import torch.nn as nn

from ml.preprocessing.trajectory.data import generate_synthetic_tracks
from ml.preprocessing.trajectory.sequence_data import make_sequences
from ml.models.architectures.lstm_model import IcebergLSTM


def train_lstm(seq_len=5, epochs=300, lr=3e-3):
    print("Generating data...")
    df = generate_synthetic_tracks(time_varying_env=True)
    X, y = make_sequences(df, seq_len=seq_len)

    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    X_train_t, y_train_t = torch.tensor(X_train), torch.tensor(y_train)
    X_test_t, y_test_t = torch.tensor(X_test), torch.tensor(y_test)

    model = IcebergLSTM(input_size=X.shape[2], hidden_size=32)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        preds = model(X_train_t)
        loss = loss_fn(preds, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0:
            print(f"Epoch {epoch+1}/{epochs} — train MSE: {loss.item():.6f}")

    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t)
        rmse_lat = torch.sqrt(loss_fn(test_preds[:, 0], y_test_t[:, 0])).item()
        rmse_lon = torch.sqrt(loss_fn(test_preds[:, 1], y_test_t[:, 1])).item()

    naive_rmse_lat = np.sqrt(np.mean(y_test[:, 0] ** 2))
    naive_rmse_lon = np.sqrt(np.mean(y_test[:, 1] ** 2))

    print(f"\nLSTM test RMSE — delta_lat: {rmse_lat:.5f}, delta_lon: {rmse_lon:.5f}")
    print(f"Naive RMSE — delta_lat: {naive_rmse_lat:.5f}, delta_lon: {naive_rmse_lon:.5f}")

    torch.save(model.state_dict(), "ml/trajectory_model/lstm_model.pt")
    print("Model saved to ml/trajectory_model/lstm_model.pt")
    
    from mlops.experiment_log import log_experiment
    log_experiment(
        model_name="trajectory_lstm",
        data_source="synthetic_time_varying",
        metrics={
            "rmse_lat": float(rmse_lat), "rmse_lon": float(rmse_lon),
            "naive_rmse_lat": float(naive_rmse_lat), "naive_rmse_lon": float(naive_rmse_lon),
        },
        hyperparams={"hidden_size": 32, "epochs": epochs, "lr": lr, "seq_len": seq_len},
    )

    return model, (rmse_lat, rmse_lon)


if __name__ == "__main__":
    train_lstm()
