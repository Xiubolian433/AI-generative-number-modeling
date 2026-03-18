import torch
import torch.nn as nn

class VAE(nn.Module):
    def __init__(self, input_dim=6, latent_dim=2):
        super(VAE, self).__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        self.z_mean = nn.Linear(64, latent_dim)  # Mean of latent variables
        self.z_log_var = nn.Linear(64, latent_dim)  # Log variance of latent variables

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid()  # Output normalized to [0, 1]
        )

    def reparameterize(self, z_mean, z_log_var):
        # Reparameterization trick
        epsilon = torch.randn_like(z_mean)
        return z_mean + torch.exp(0.5 * z_log_var) * epsilon

    def forward(self, x):
        encoded = self.encoder(x)
        z_mean = self.z_mean(encoded)
        z_log_var = self.z_log_var(encoded)
        z = self.reparameterize(z_mean, z_log_var)
        reconstructed = self.decoder(z)
        return reconstructed, z_mean, z_log_var


def vae_loss(reconstructed, targets, z_mean, z_log_var, beta = 0.01):
    """
    计算 VAE 的损失，包括重建损失和 KL 散度损失。
    """
    # 如果目标是独热编码，转换为类别索引
    if targets.dim() > 1:  # 检查是否为二维张量
        targets = targets.argmax(dim=1)

    # 重建损失（交叉熵损失）
    reconstruction_loss = nn.CrossEntropyLoss()(reconstructed, targets)

    # KL 散度损失
    kl_loss = -0.5 * torch.sum(1 + z_log_var - z_mean.pow(2) - z_log_var.exp())

    return reconstruction_loss + beta * kl_loss

class LotteryPredictor(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(LotteryPredictor, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)  # 输出与独热编码维度匹配

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])  # 只取最后一个时间步的输出
        return out

