import torch
import torch.nn as nn


class IcebergLSTM(nn.Module):
    def __init__(self, input_size: int = 6, hidden_size: int = 32, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.head = nn.Linear(hidden_size, 2)

    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        return self.head(h_n[-1])
