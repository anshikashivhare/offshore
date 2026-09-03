"""
Trains the ConvLSTM and compares against the persistence baseline.
Run: python -m ml.seaice_model.train_convlstm
"""
import numpy as np
import torch
import torch.nn as nn

from ml.seaice_model.data import generate_synthetic_timeseries
from ml.seaice_model.grid_sequence import dataframe_to_grid_sequence, make_sequences
from ml.seaice_model.convlstm import SeaIceConvLSTM


def train_convlstm(input_len=5, epochs=300, lr=3e-3):
    print("Generating data...")
    df = generate_synthetic_timeseries(spatial_correlation=True)
    grid_seq = dataframe_to_grid_sequence(df)

    X, y = make_sequences(grid_seq, input_len=input_len)
    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    X_train_t = torch.tensor(X_train).unsqueeze(2)
    y_train_t = torch.tensor(y_train)
    X_test_t = torch.tensor(X_test).unsqueeze(2)
    y_test_t = torch.tensor(y_test)

    model = SeaIceConvLSTM(hidden_channels=8)
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
            print(f"Epoch {epoch+1}/{epochs} — train MSE: {loss.item():.5f}")

    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t)
        test_rmse = torch.sqrt(loss_fn(test_preds, y_test_t)).item()

    last_input_grid = X_test[:, -1]
    persistence_rmse = np.sqrt(np.mean((last_input_grid - y_test) ** 2))

    print(f"\nConvLSTM test RMSE: {test_rmse:.5f}")
    print(f"Persistence baseline RMSE: {persistence_rmse:.5f}")

    torch.save(model.state_dict(), "ml/seaice_model/convlstm.pt")
    print("Model saved to ml/seaice_model/convlstm.pt")
    return model, test_rmse, persistence_rmse


if __name__ == "__main__":
    train_convlstm()
