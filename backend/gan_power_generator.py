# import torch
# import torch.nn as nn
# import torch.optim as optim
# import torch.autograd as autograd
# import numpy as np
# import pandas as pd
# from tqdm import tqdm
# from torch.utils.tensorboard import SummaryWriter
# from scipy.stats import entropy
#
# # ========== 数据加载和预处理 ==========
# file_path = "/scratch/shuhaoz/lotteryAI/Lottery_data/Power_API_data.csv"  # CSV 文件路径
# data = pd.read_csv(file_path)
#
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#
# # 数据筛选
# condition = (
#     (data["Number1"].between(1, 69)) &
#     (data["Number2"].between(1, 69)) &
#     (data["Number3"].between(1, 69)) &
#     (data["Number4"].between(1, 69)) &
#     (data["Number5"].between(1, 69)) &
#     (data["PowerBall"].between(1, 26))
# )
# filtered_data = data[condition]
#
# # 去除非数值列，例如日期列
# numeric_columns = ["Number1", "Number2", "Number3", "Number4", "Number5", "PowerBall"]
# filtered_data_numeric = filtered_data[numeric_columns]
#
# data_values = filtered_data_numeric.values
#
# # 数据归一化
# num_classes = 69
# power_classes = 26
#
# def one_hot_encode(data, num_classes):
#     one_hot = np.zeros((data.size, num_classes))
#     one_hot[np.arange(data.size), data - 1] = 1
#     return one_hot
#
# number_data = np.concatenate([
#     one_hot_encode(data_values[:, i].astype(int), num_classes) for i in range(5)
# ], axis=1)
# power_data = one_hot_encode(data_values[:, 5].astype(int), power_classes)
# data_tensor = torch.tensor(np.concatenate([number_data, power_data], axis=1), dtype=torch.float32).to(device)
#
# # 数据增强：加入轻微扰动
# data_tensor += 0.05 * torch.randn_like(data_tensor)
#
# # 条件信息
# condition_features = torch.mean(data_tensor, dim=0, keepdim=True).repeat(len(data_tensor), 1).to(device)
#
# # ========== 模型定义 ==========
# latent_dim = 30
# number_dim = 5 * num_classes
# power_dim = power_classes
# input_dim = number_dim + power_dim
# condition_dim = input_dim
#
#
# class Generator(nn.Module):
#     def __init__(self, latent_dim, condition_dim, number_dim, power_dim):
#         super(Generator, self).__init__()
#         self.fc1 = nn.Linear(latent_dim + condition_dim, 512)
#         self.fc2 = nn.Linear(512, 1024)
#         self.fc3 = nn.Linear(1024, 2048)
#         self.fc4 = nn.Linear(2048, 1024)
#         self.self_attention = nn.MultiheadAttention(embed_dim=1024, num_heads=8, batch_first=True)
#         self.fc5 = nn.Linear(1024, number_dim + power_dim)
#
#         self.activation = nn.ReLU()
#         self.bn1 = nn.BatchNorm1d(512)
#         self.bn2 = nn.BatchNorm1d(1024)
#         self.bn3 = nn.BatchNorm1d(2048)
#
#     def forward(self, noise, condition):
#         x = torch.cat([noise, condition], dim=1)
#         x = self.activation(self.bn1(self.fc1(x)))  # 第一层
#         x = self.activation(self.bn2(self.fc2(x)))  # 第二层
#         x = self.activation(self.bn3(self.fc3(x)))  # 第三层
#         x = self.activation(self.bn2(self.fc4(x)))  # 第四层
#
#         # 自注意力层
#         x = x.unsqueeze(1)
#         x, _ = self.self_attention(x, x, x)
#         x = x.squeeze(1)
#
#         # 输出层
#         x = self.fc5(x)
#         numbers_logits = x[:, :number_dim].view(-1, 5, num_classes)
#         numbers = torch.softmax(numbers_logits, dim=-1)
#         power_logits = x[:, number_dim:].view(-1, power_classes)
#         power = torch.softmax(power_logits, dim=-1)
#         return numbers, power
#
#
# class Discriminator(nn.Module):
#     def __init__(self, number_dim, power_dim, condition_dim):
#         super(Discriminator, self).__init__()
#         self.self_attention = nn.MultiheadAttention(embed_dim=742, num_heads=2, batch_first=True)
#         # 线性调整层，将自注意力的输出调整为后续模型的输入维度
#         self.fc_adjust = nn.Linear(742, number_dim + power_dim + condition_dim)
#
#         self.model = nn.Sequential(
#             nn.Linear(number_dim + power_dim + condition_dim, 1024),
#             nn.ReLU(),
#             nn.Dropout(0.3),
#             nn.Linear(1024, 512),
#             nn.ReLU(),
#             nn.Dropout(0.3),
#             nn.Linear(512, 1)
#         )
#
#     def forward(self, numbers, power, condition):
#         x = torch.cat([numbers.view(numbers.size(0), -1), power, condition], dim=1)
#         x, _ = self.self_attention(x.unsqueeze(1), x.unsqueeze(1), x.unsqueeze(1))
#         x = x.squeeze(1)
#         return self.model(x)
#
#
# # ========== WGAN-GP ==========
# def gradient_penalty(discriminator, real_data, fake_data, condition):
#     batch_size = real_data.size(0)
#     alpha = torch.rand(batch_size, 1).to(real_data.device)
#     alpha = alpha.expand_as(real_data)
#     interpolated = alpha * real_data + (1 - alpha) * fake_data
#     interpolated.requires_grad_(True)
#
#     numbers_interpolated = interpolated[:, :number_dim]
#     power_interpolated = interpolated[:, number_dim:]
#
#     interpolated_score = discriminator(numbers_interpolated, power_interpolated, condition)
#
#     grads = autograd.grad(outputs=interpolated_score,
#                           inputs=interpolated,
#                           grad_outputs=torch.ones_like(interpolated_score),
#                           create_graph=True,
#                           retain_graph=True)[0]
#     grads = grads.view(grads.size(0), -1)
#     gp = ((grads.norm(2, dim=1) - 1) ** 2).mean()
#     return gp
#
# # ========== 初始化模型和优化器 ==========
# G = Generator(latent_dim, condition_dim, number_dim, power_dim).to(device)
# D = Discriminator(number_dim, power_dim, condition_dim).to(device)
#
#
# def weights_init(m):
#     if isinstance(m, nn.Linear):
#         nn.init.xavier_uniform_(m.weight)
#         if m.bias is not None:
#             nn.init.constant_(m.bias, 0)
#
# G.apply(weights_init)
# D.apply(weights_init)
#
#
# lr = 1e-6
#
# optimizer_G = optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.9))
# optimizer_D = optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.9))
# scheduler_G = optim.lr_scheduler.StepLR(optimizer_G, step_size=1000, gamma=0.5)
# scheduler_D = optim.lr_scheduler.StepLR(optimizer_D, step_size=1000, gamma=0.5)
#
# # 初始化 TensorBoard
# writer = SummaryWriter(log_dir="GanRuns_power")
# writer_Dis = SummaryWriter(log_dir="GanRuns_power/D")
# writer_Gener = SummaryWriter(log_dir="GanRuns_power/G")
#
# # ========== 训练过程 ==========
# num_epochs = 3000
# batch_size = 128
# lambda_gp = 5
#
# real_distribution = {
#     'numbers': data_tensor[:, :number_dim].view(-1, 5, num_classes).mean(dim=0).cpu().numpy(),
#     'power': data_tensor[:, number_dim:].mean(dim=0).cpu().numpy()
# }
#
#
# data_loader = torch.utils.data.DataLoader(data_tensor, batch_size=batch_size, shuffle=True)
#
# def generator_loss(fake_numbers, fake_power, real_distribution):
#     numbers_dist = fake_numbers.mean(dim=0).detach().cpu().numpy()
#     power_dist = fake_power.mean(dim=0).detach().cpu().numpy()
#     # kl_loss_numbers = entropy((numbers_dist + real_distribution['numbers']) / 2, base=2).sum()
#     # kl_loss_power = entropy((power_dist + real_distribution['power']) / 2, base=2).sum()
#     epsilon = 1e-9
#     kl_loss_numbers = entropy((numbers_dist + real_distribution['numbers']) / 2 + epsilon, base=2).sum()
#     kl_loss_power = entropy((power_dist + real_distribution['power']) / 2 + epsilon, base=2).sum()
#
#     return kl_loss_numbers + kl_loss_power
#
#
# for epoch in tqdm(range(num_epochs)):
#     for real_batch in data_loader:
#         condition_batch = condition_features[:len(real_batch)]
#         noise = torch.randn(len(real_batch), latent_dim).to(device)
#
#         # ========== 更新判别器 ==========
#         numbers, power = G(noise, condition_batch)
#         fake_data = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1).detach()
#         real_data = real_batch
#         real_score = D(real_data[:, :number_dim], real_data[:, number_dim:], condition_batch)
#         fake_score = D(fake_data[:, :number_dim], fake_data[:, number_dim:], condition_batch)
#
#         gp = gradient_penalty(D, real_data, fake_data, condition_batch)
#         d_loss = fake_score.mean() - real_score.mean() + lambda_gp * gp
#
#         optimizer_D.zero_grad()
#         d_loss.backward()
#         torch.nn.utils.clip_grad_norm_(D.parameters(), max_norm=1.0)
#         optimizer_D.step()
#
#         # ========== 更新生成器 ==========
#         for _ in range(3):
#             noise = torch.randn(len(real_batch), latent_dim).to(device)
#             numbers, power = G(noise, condition_batch)
#
#             fake_data = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1)
#             fake_score = D(fake_data[:, :number_dim], fake_data[:, number_dim:], condition_batch)
#
#             # g_loss = -D(numbers.view(numbers.size(0), -1), power, condition_batch).mean()
#             g_loss = -fake_score.mean()
#             g_loss += generator_loss(numbers, power, real_distribution)
#
#             #print(f"real_distribution['numbers']: {real_distribution['numbers']}")
#
#             optimizer_G.zero_grad()
#             g_loss.backward()
#             torch.nn.utils.clip_grad_norm_(G.parameters(), max_norm=1.0)
#             optimizer_G.step()
#
#     scheduler_G.step()
#     scheduler_D.step()
#
#     # 记录到 TensorBoard
#     writer_Dis.add_scalar('Loss', d_loss.item(), epoch)
#     writer_Gener.add_scalar('Loss', g_loss.item(), epoch)
#
#     if epoch % 100 == 0:
#         print(f"Epoch {epoch}/{num_epochs}, D Loss: {d_loss.item()}, G Loss: {g_loss.item()}")
#
# writer.close()
#
#
# # ========== 后处理生成数据 ==========
# def post_process_unique(numbers):
#     """
#     后处理：确保 Number1 到 Number5 唯一性。
#     """
#     batch_size, _, num_classes = numbers.size()
#     result = torch.zeros_like(numbers)
#     for i in range(batch_size):
#         chosen = set()
#         for j in range(5):
#             idx = torch.argmax(numbers[i, j]).item()
#             while idx in chosen:
#                 numbers[i, j, idx] = 0  # 将重复的概率置 0
#                 idx = torch.argmax(numbers[i, j]).item()
#             chosen.add(idx)
#             result[i, j, idx] = 1
#     return result
#
# noise = torch.randn(100, latent_dim).to(device)
# condition_sample = condition_features[:100]
# numbers, power = G(noise, condition_sample)
# numbers = post_process_unique(numbers)
#
# # 提取生成的数字和 PowerBall
# generated_numbers = torch.argmax(numbers, dim=-1).cpu().numpy() + 1
# generated_power = torch.argmax(power, dim=-1).cpu().numpy() + 1
#
# # 打印生成结果
# for i in range(100):
#     print(f"Numbers: {generated_numbers[i]}, PowerBall: {generated_power[i]}")
#
# # ========== 分布对比分析 ==========
# def compare_distributions(real_data, generated_data, num_classes=69, power_classes=26):
#     real_numbers_dist = np.mean(real_data[:, :num_classes * 5].reshape(-1, num_classes), axis=0)
#     generated_numbers_dist = np.mean(generated_data[:, :num_classes * 5].reshape(-1, num_classes), axis=0)
#
#     real_power_dist = np.mean(real_data[:, num_classes * 5:].reshape(-1, power_classes), axis=0)
#     generated_power_dist = np.mean(generated_data[:, :power_classes].reshape(-1, power_classes), axis=0)
#
#     js_div_numbers = entropy((real_numbers_dist + generated_numbers_dist) / 2, base=2)
#     js_div_power = entropy((real_power_dist + generated_power_dist) / 2, base=2)
#
#     print("数字分布 JS散度:", js_div_numbers)
#     print("PowerBall分布 JS散度:", js_div_power)
#
# real_data_np = data_tensor.cpu().numpy()
# generated_data_np = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1).detach().cpu().numpy()
# compare_distributions(real_data_np, generated_data_np)
#
# #save model
#
# torch.save(G.state_dict(), "1_gan_powerball_generator.pth")
# print("Save model: 1_gan_powerball_generator.pth")


# 以下代码是封装为main函数的


import torch
import torch.nn as nn
import torch.optim as optim
import torch.autograd as autograd
import numpy as np
import pandas as pd
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter
from scipy.stats import entropy

num_classes = 69
power_classes = 26

latent_dim = 30
number_dim = 5 * num_classes
power_dim = power_classes
input_dim = number_dim + power_dim
condition_dim = input_dim

# ========== 模型定义 ==========
class Generator(nn.Module):
    def __init__(self, latent_dim, condition_dim, number_dim, power_dim):
        super(Generator, self).__init__()
        self.fc1 = nn.Linear(latent_dim + condition_dim, 512)
        self.fc2 = nn.Linear(512, 1024)
        self.fc3 = nn.Linear(1024, 2048)
        self.fc4 = nn.Linear(2048, 1024)
        self.self_attention = nn.MultiheadAttention(embed_dim=1024, num_heads=8, batch_first=True)
        self.fc5 = nn.Linear(1024, number_dim + power_dim)

        self.activation = nn.ReLU()
        self.bn1 = nn.BatchNorm1d(512)
        self.bn2 = nn.BatchNorm1d(1024)
        self.bn3 = nn.BatchNorm1d(2048)

    def forward(self, noise, condition):
        x = torch.cat([noise, condition], dim=1)
        x = self.activation(self.bn1(self.fc1(x)))
        x = self.activation(self.bn2(self.fc2(x)))
        x = self.activation(self.bn3(self.fc3(x)))
        x = self.activation(self.bn2(self.fc4(x)))

        x = x.unsqueeze(1)
        x, _ = self.self_attention(x, x, x)
        x = x.squeeze(1)

        x = self.fc5(x)
        numbers_logits = x[:, :number_dim].view(-1, 5, num_classes)
        numbers = torch.softmax(numbers_logits, dim=-1)
        power_logits = x[:, number_dim:].view(-1, power_classes)
        power = torch.softmax(power_logits, dim=-1)
        return numbers, power

class Discriminator(nn.Module):
    def __init__(self, number_dim, power_dim, condition_dim):
        super(Discriminator, self).__init__()
        self.self_attention = nn.MultiheadAttention(embed_dim=742, num_heads=2, batch_first=True)
        self.fc_adjust = nn.Linear(742, number_dim + power_dim + condition_dim)

        self.model = nn.Sequential(
            nn.Linear(number_dim + power_dim + condition_dim, 1024),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 1)
        )

    def forward(self, numbers, power, condition):
        x = torch.cat([numbers.view(numbers.size(0), -1), power, condition], dim=1)
        x, _ = self.self_attention(x.unsqueeze(1), x.unsqueeze(1), x.unsqueeze(1))
        x = x.squeeze(1)
        return self.model(x)

# 将 Generator 暴露为 PowerBallGenerator
PowerBallGenerator = Generator

def main():
    # ========== 数据加载和预处理 ==========
    file_path = "/scratch/shuhaoz/lotteryAI/Lottery_data/Power_API_data.csv"
    data = pd.read_csv(file_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    condition = (
        (data["Number1"].between(1, 69)) &
        (data["Number2"].between(1, 69)) &
        (data["Number3"].between(1, 69)) &
        (data["Number4"].between(1, 69)) &
        (data["Number5"].between(1, 69)) &
        (data["PowerBall"].between(1, 26))
    )
    filtered_data = data[condition]

    numeric_columns = ["Number1", "Number2", "Number3", "Number4", "Number5", "PowerBall"]
    filtered_data_numeric = filtered_data[numeric_columns]

    data_values = filtered_data_numeric.values

    def one_hot_encode(data, num_classes):
        one_hot = np.zeros((data.size, num_classes))
        one_hot[np.arange(data.size), data - 1] = 1
        return one_hot

    number_data = np.concatenate([
        one_hot_encode(data_values[:, i].astype(int), num_classes) for i in range(5)
    ], axis=1)
    power_data = one_hot_encode(data_values[:, 5].astype(int), power_classes)
    data_tensor = torch.tensor(np.concatenate([number_data, power_data], axis=1), dtype=torch.float32).to(device)

    data_tensor += 0.05 * torch.randn_like(data_tensor)
    condition_features = torch.mean(data_tensor, dim=0, keepdim=True).repeat(len(data_tensor), 1).to(device)

    G = PowerBallGenerator(latent_dim, condition_dim, number_dim, power_dim).to(device)
    D = Discriminator(number_dim, power_dim, condition_dim).to(device)

    def gradient_penalty(discriminator, real_data, fake_data, condition):
        batch_size = real_data.size(0)
        alpha = torch.rand(batch_size, 1).to(real_data.device)
        alpha = alpha.expand_as(real_data)
        interpolated = alpha * real_data + (1 - alpha) * fake_data
        interpolated.requires_grad_(True)

        numbers_interpolated = interpolated[:, :number_dim]
        power_interpolated = interpolated[:, number_dim:]

        interpolated_score = discriminator(numbers_interpolated, power_interpolated, condition)

        grads = autograd.grad(outputs=interpolated_score,
                              inputs=interpolated,
                              grad_outputs=torch.ones_like(interpolated_score),
                              create_graph=True,
                              retain_graph=True)[0]
        grads = grads.view(grads.size(0), -1)
        gp = ((grads.norm(2, dim=1) - 1) ** 2).mean()
        return gp

    def generator_loss(fake_numbers, fake_power, real_distribution):
        numbers_dist = fake_numbers.mean(dim=0).detach().cpu().numpy()
        power_dist = fake_power.mean(dim=0).detach().cpu().numpy()
        # kl_loss_numbers = entropy((numbers_dist + real_distribution['numbers']) / 2, base=2).sum()
        # kl_loss_power = entropy((power_dist + real_distribution['power']) / 2, base=2).sum()
        epsilon = 1e-9
        kl_loss_numbers = entropy((numbers_dist + real_distribution['numbers']) / 2 + epsilon, base=2).sum()
        kl_loss_power = entropy((power_dist + real_distribution['power']) / 2 + epsilon, base=2).sum()

        return kl_loss_numbers + kl_loss_power


    def weights_init(m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)

    G.apply(weights_init)
    D.apply(weights_init)

    lr = 1e-6

    optimizer_G = optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.9))
    optimizer_D = optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.9))
    scheduler_G = optim.lr_scheduler.StepLR(optimizer_G, step_size=1000, gamma=0.5)
    scheduler_D = optim.lr_scheduler.StepLR(optimizer_D, step_size=1000, gamma=0.5)

    writer = SummaryWriter(log_dir="GanRuns_power")
    writer_Dis = SummaryWriter(log_dir="GanRuns_power/D")
    writer_Gener = SummaryWriter(log_dir="GanRuns_power/G")

    num_epochs = 3000
    batch_size = 128
    lambda_gp = 5

    real_distribution = {
        'numbers': data_tensor[:, :number_dim].view(-1, 5, num_classes).mean(dim=0).cpu().numpy(),
        'power': data_tensor[:, number_dim:].mean(dim=0).cpu().numpy()
    }

    data_loader = torch.utils.data.DataLoader(data_tensor, batch_size=batch_size, shuffle=True)

    for epoch in tqdm(range(num_epochs)):
        for real_batch in data_loader:
            condition_batch = condition_features[:len(real_batch)]
            noise = torch.randn(len(real_batch), latent_dim).to(device)

            numbers, power = G(noise, condition_batch)
            fake_data = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1).detach()
            real_data = real_batch
            real_score = D(real_data[:, :number_dim], real_data[:, number_dim:], condition_batch)
            fake_score = D(fake_data[:, :number_dim], fake_data[:, number_dim:], condition_batch)

            gp = gradient_penalty(D, real_data, fake_data, condition_batch)
            d_loss = fake_score.mean() - real_score.mean() + lambda_gp * gp

            optimizer_D.zero_grad()
            d_loss.backward()
            torch.nn.utils.clip_grad_norm_(D.parameters(), max_norm=1.0)
            optimizer_D.step()

            for _ in range(3):
                noise = torch.randn(len(real_batch), latent_dim).to(device)
                numbers, power = G(noise, condition_batch)

                fake_data = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1)
                fake_score = D(fake_data[:, :number_dim], fake_data[:, number_dim:], condition_batch)

                g_loss = -fake_score.mean()
                g_loss += generator_loss(numbers, power, real_distribution)

                optimizer_G.zero_grad()
                g_loss.backward()
                torch.nn.utils.clip_grad_norm_(G.parameters(), max_norm=1.0)
                optimizer_G.step()

        scheduler_G.step()
        scheduler_D.step()

        writer_Dis.add_scalar('Loss', d_loss.item(), epoch)
        writer_Gener.add_scalar('Loss', g_loss.item(), epoch)

        if epoch % 100 == 0:
            print(f"Epoch {epoch}/{num_epochs}, D Loss: {d_loss.item()}, G Loss: {g_loss.item()}")

    writer.close()

    # ========== 后处理生成数据 ==========
    def post_process_unique(numbers):
        """
        后处理：确保 Number1 到 Number5 唯一性。
        """
        batch_size, _, num_classes = numbers.size()
        result = torch.zeros_like(numbers)
        for i in range(batch_size):
            chosen = set()
            for j in range(5):
                idx = torch.argmax(numbers[i, j]).item()
                while idx in chosen:
                    numbers[i, j, idx] = 0  # 将重复的概率置 0
                    idx = torch.argmax(numbers[i, j]).item()
                chosen.add(idx)
                result[i, j, idx] = 1
        return result

    noise = torch.randn(100, latent_dim).to(device)
    condition_sample = condition_features[:100]
    numbers, power = G(noise, condition_sample)
    numbers = post_process_unique(numbers)

    # 提取生成的数字和 PowerBall
    generated_numbers = torch.argmax(numbers, dim=-1).cpu().numpy() + 1
    generated_power = torch.argmax(power, dim=-1).cpu().numpy() + 1

    # 打印生成结果
    for i in range(100):
        print(f"Numbers: {generated_numbers[i]}, PowerBall: {generated_power[i]}")

    # ========== 分布对比分析 ==========
    def compare_distributions(real_data, generated_data, num_classes=69, power_classes=26):
        real_numbers_dist = np.mean(real_data[:, :num_classes * 5].reshape(-1, num_classes), axis=0)
        generated_numbers_dist = np.mean(generated_data[:, :num_classes * 5].reshape(-1, num_classes), axis=0)

        real_power_dist = np.mean(real_data[:, num_classes * 5:].reshape(-1, power_classes), axis=0)
        generated_power_dist = np.mean(generated_data[:, :power_classes].reshape(-1, power_classes), axis=0)

        js_div_numbers = entropy((real_numbers_dist + generated_numbers_dist) / 2, base=2)
        js_div_power = entropy((real_power_dist + generated_power_dist) / 2, base=2)

        print("数字分布 JS散度:", js_div_numbers)
        print("PowerBall分布 JS散度:", js_div_power)

    real_data_np = data_tensor.cpu().numpy()
    generated_data_np = torch.cat([numbers.view(numbers.size(0), -1), power], dim=1).detach().cpu().numpy()
    compare_distributions(real_data_np, generated_data_np)

    # save model

    torch.save(G.state_dict(), "1_gan_powerball_generator.pth")
    print("Save model: 1_gan_powerball_generator.pth")


if __name__ == "__main__":
    main()







































'''
数字分布 JS散度: 6.019204346192687                    //5.652906969432243
PowerBall分布 JS散度: 4.6119604899514695             //3.95523823808786
'''

