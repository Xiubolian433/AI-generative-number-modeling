import torch
import torch.optim as optim
from vae_model import VAE, prepare_data, vae_loss
from tqdm import tqdm
import os
from torch.utils.tensorboard import SummaryWriter

# 超参数
csv_file = "E:\Pychram\lotteryAI\Lottery_data\API_drawing_data.csv"
input_dim = 6
latent_dim = 2
num_epochs = 500
batch_size = 32
learning_rate = 0.001

# 加载数据
dataloader = prepare_data(csv_file)

# 初始化模型和优化器
vae = VAE(input_dim=input_dim, latent_dim=latent_dim)
optimizer = optim.Adam(vae.parameters(), lr=learning_rate)


log_dir = os.path.abspath("VAE_loss")
writer = SummaryWriter(log_dir=log_dir)
print(f"TensorBoard logs saved at: {log_dir}")

# 训练模型
vae.train()
for epoch in tqdm(range(num_epochs)):
    epoch_loss = 0
    for batch_idx, batch in enumerate(dataloader):
        original = batch[0]
        optimizer.zero_grad()
        reconstructed, z_mean, z_log_var = vae(original)
        loss = vae_loss(reconstructed, original, z_mean, z_log_var)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    # 记录每个 epoch 的平均损失
    epoch_loss /= len(dataloader)
    writer.add_scalar("Loss/train", epoch_loss, epoch)

    print(f"Epoch {epoch + 1}, Loss: {epoch_loss:.4f}")

writer.close()

# 保存模型
torch.save(vae.state_dict(), "vae_lottery_predictor.pth")
print("Model saved as 'vae_lottery_predictor.pth'")

# 使用模型生成新号码
vae.eval()
def generate_numbers(n_samples=5):
    """
    Generates lottery numbers using the VAE decoder.

    Parameters:
        n_samples (int): Number of lottery number sets to generate.

    Returns:
        numpy.ndarray: Generated lottery numbers as a NumPy array.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be a positive integer.")

    device = next(vae.parameters()).device  # Ensure compatibility with model's device
    scale_factors = torch.tensor([70, 70, 70, 70, 70, 25], device=device)

    with torch.no_grad():
        z_samples = torch.randn(n_samples, latent_dim, device=device)  # Sample latent space
        generated = vae.decoder(z_samples)  # Decode to original space
        generated = (generated * scale_factors).round().int()  # Scale and convert to int
        generated = torch.clip(generated, min=0, max=70)  # Clip first 5 numbers
        generated[:, -1] = torch.clip(generated[:, -1], min=0, max=25)  # Clip last number

    return generated.cpu().numpy()  # Convert to NumPy array

# 测试生成
print("Generated Lottery Numbers:")
print(generate_numbers(10))  # 生成 10 组彩票号码























# def generate_numbers(n_samples=5):
#     with torch.no_grad():
#         # 从标准正态分布采样
#         z_samples = torch.randn(n_samples, latent_dim)  # 2 是潜在空间维度
#         generated = vae.decoder(z_samples)  # 解码生成数据
#         generated = (generated * torch.tensor([70, 70, 70, 70, 70, 25])).round().int()  # 恢复原始范围
#         generated = torch.clip(generated, min=0, max=70)  # For first 5 numbers
#         generated[:, -1] = torch.clip(generated[:, -1], min=0, max=25)  # For the last number
#
#         return generated.numpy()
