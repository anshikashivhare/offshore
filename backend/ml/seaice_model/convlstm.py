"""
ConvLSTM for forecasting the next sea-ice concentration grid from a
sequence of past grids. Learns spatial patterns jointly with temporal
trend, unlike the XGBoost baseline which treats each cell independently.
Reference: Shi et al., "Convolutional LSTM Network" (2015).
"""
import torch
import torch.nn as nn


class ConvLSTMCell(nn.Module):
    def __init__(self, input_channels: int, hidden_channels: int, kernel_size: int = 3):
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv2d(
            in_channels=input_channels + hidden_channels,
            out_channels=4 * hidden_channels,
            kernel_size=kernel_size,
            padding=padding,
        )
        self.hidden_channels = hidden_channels

    def forward(self, x, h_prev, c_prev):
        combined = torch.cat([x, h_prev], dim=1)
        gates = self.conv(combined)
        i, f, o, g = torch.split(gates, self.hidden_channels, dim=1)
        i, f, o = torch.sigmoid(i), torch.sigmoid(f), torch.sigmoid(o)
        g = torch.tanh(g)
        c_next = f * c_prev + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

    def init_hidden(self, batch_size, height, width, device):
        return (
            torch.zeros(batch_size, self.hidden_channels, height, width, device=device),
            torch.zeros(batch_size, self.hidden_channels, height, width, device=device),
        )


class SeaIceConvLSTM(nn.Module):
    def __init__(self, hidden_channels: int = 8, kernel_size: int = 3):
        super().__init__()
        self.cell = ConvLSTMCell(1, hidden_channels, kernel_size)
        self.output_conv = nn.Conv2d(hidden_channels, 1, kernel_size=1)

    def forward(self, x):
        # x: (batch, seq_len, 1, H, W)
        batch_size, seq_len, _, height, width = x.shape
        h, c = self.cell.init_hidden(batch_size, height, width, x.device)
        for t in range(seq_len):
            h, c = self.cell(x[:, t], h, c)
        out = self.output_conv(h)
        return torch.sigmoid(out).squeeze(1)
