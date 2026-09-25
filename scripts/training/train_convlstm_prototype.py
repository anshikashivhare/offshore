import torch
import torch.nn as nn
from pathlib import Path

print("Preparing ConvLSTM prototype...")

class SimpleConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, bias):
        super().__init__()
        self.conv = nn.Conv2d(in_channels=input_dim + hidden_dim,
                              out_channels=4 * hidden_dim,
                              kernel_size=kernel_size,
                              padding=kernel_size // 2,
                              bias=bias)
    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, combined_conv.size(1) // 4, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

# Dummy check for environment
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Hardware initialized for ConvLSTM on: {device}")
print("Note: Full ConvLSTM training on Mac CPU/MPS requires converting tabular CSV into 2D grid tensors.")
print("This prototype proves the architecture layers load successfully.")

model = SimpleConvLSTMCell(input_dim=17, hidden_dim=32, kernel_size=3, bias=True).to(device)
dummy_input = torch.randn(1, 17, 16, 16).to(device)
dummy_h = torch.randn(1, 32, 16, 16).to(device)
dummy_c = torch.randn(1, 32, 16, 16).to(device)

h_next, c_next = model(dummy_input, (dummy_h, dummy_c))
print(f"Forward pass successful. Output shape: {h_next.shape}")
