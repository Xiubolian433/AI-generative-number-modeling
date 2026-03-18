import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd

# 数据加载与准备
def prepare_data(csv_file):
    data = pd.read_csv(csv_file)
    numbers = data[['Number1', 'Number2', 'Number3', 'Number4', 'Number5']].values / 70.0  # 主号码归一化
    mega_ball = data['MegaBall'].values / 25.0  # Mega Ball 归一化
    all_data = np.hstack([numbers, mega_ball.reshape(-1, 1)])  # 合并数据
    all_data_tensor = torch.tensor(all_data, dtype=torch.float32)
    dataset = TensorDataset(all_data_tensor)
    return DataLoader(dataset, batch_size=32, shuffle=True)

# VAE 模型
class VAE(nn.Module):
    def __init__(self, input_dim=6, latent_dim=2):
        super(VAE, self).__init__()
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 16),
            nn.ReLU()
        )
        self.z_mean = nn.Linear(16, latent_dim)  # 均值
        self.z_log_var = nn.Linear(16, latent_dim)  # 方差

        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid()  # 输出范围为 [0, 1]
        )

    def reparameterize(self, z_mean, z_log_var):
        # 重参数化技巧：z = mean + std * epsilon
        epsilon = torch.randn_like(z_mean)
        return z_mean + torch.exp(0.5 * z_log_var) * epsilon

    def forward(self, x):
        # 编码
        encoded = self.encoder(x)
        z_mean = self.z_mean(encoded)
        z_log_var = self.z_log_var(encoded)
        # 采样
        z = self.reparameterize(z_mean, z_log_var)
        # 解码
        reconstructed = self.decoder(z)
        return reconstructed, z_mean, z_log_var

# VAE 损失函数
def vae_loss(reconstructed, original, z_mean, z_log_var, beta=1.0):
    reconstruction_loss = nn.MSELoss()(reconstructed, original)
    kl_loss = -0.5 * torch.sum(1 + z_log_var - z_mean.pow(2) - z_log_var.exp())
    return reconstruction_loss + beta * kl_loss / original.size(0)

