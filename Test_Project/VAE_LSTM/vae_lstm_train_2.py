import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import pandas as pd
from vae_lstm_model import VAE, LotteryPredictor, vae_loss
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import os
from torch.optim.lr_scheduler import StepLR,ReduceLROnPlateau
import random
import matplotlib.pyplot as plt

# Data Preprocessing and Feature Engineering
def prepare_data(csv_file, window_size=5):
    data = pd.read_csv(csv_file)
    numbers = data[['Number1', 'Number2', 'Number3', 'Number4', 'Number5']].values / 70.0  # Normalize main numbers
    mega_ball = data['MegaBall'].values / 25.0  # Normalize Mega Ball
    all_data = np.hstack([numbers, mega_ball.reshape(-1, 1)])

    features, targets = [], []
    for i in range(len(all_data) - window_size):
        features.append(all_data[i:i + window_size])
        targets.append(all_data[i + window_size])

    features = torch.tensor(features, dtype=torch.float32)
    targets = torch.tensor(targets, dtype=torch.float32)
    dataset = TensorDataset(features, targets)

    return dataset

def evaluate_combined_model(vae, lstm_predictor, data_loader, criterion):
    vae.eval()
    lstm_predictor.eval()
    total_loss = 0
    all_predictions = []
    all_targets = []
    with torch.no_grad():
        for features, targets in data_loader:
            reconstructed, z_mean, z_log_var = vae(features)
            predictions = lstm_predictor(z_mean)
            vae_loss_value = vae_loss(reconstructed, features, z_mean, z_log_var)
            lstm_loss_value = criterion(predictions, targets)
            total_loss += (vae_loss_value + lstm_loss_value).item()

            all_predictions.append(predictions.cpu().numpy())
            all_targets.append(targets.cpu().numpy())

    mean_predictions = np.mean(np.vstack(all_predictions), axis=0)
    mean_targets = np.mean(np.vstack(all_targets), axis=0)

    return total_loss / len(data_loader), mean_predictions, mean_targets


# 绘制 Mean Predictions 和 Mean Targets
def plot_predictions_vs_targets(mean_predictions, mean_targets, save_path="predictions_vs_targets.png"):
    plt.figure(figsize=(10, 6))
    plt.plot(mean_predictions, label="Mean Predictions", marker='o')
    plt.plot(mean_targets, label="Mean Targets", marker='x')
    plt.title("Mean Predictions vs Mean Targets")
    plt.xlabel("Feature Index")
    plt.ylabel("Normalized Value")
    plt.legend()
    plt.grid()

    # 保存图片而不显示
    plt.savefig(save_path, dpi=300, bbox_inches='tight')  # 高分辨率保存，紧凑边界
    plt.close()  # 关闭当前图形，释放内存

# Parameters
csv_file = "E:\Pychram\lotteryAI\Lottery_data\API_drawing_data.csv"
input_dim = 6
latent_dim = 64
hidden_dim = 64
num_epochs = 5000
batch_size = 64
learning_rate = 0.01
window_size = 5

# Load Data
dataset = prepare_data(csv_file, window_size=window_size)
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Initialize Models and Optimizers
vae = VAE(input_dim=input_dim, latent_dim=latent_dim)
lstm_predictor = LotteryPredictor(input_dim=latent_dim, hidden_dim=hidden_dim, output_dim=input_dim)
vae_optimizer = optim.Adam(vae.parameters(), lr=learning_rate)
scheduler = ReduceLROnPlateau(vae_optimizer, mode='min', factor=0.1, patience=5, verbose=True)
lstm_optimizer = optim.Adam(lstm_predictor.parameters(), lr=learning_rate)
scheduler = ReduceLROnPlateau(lstm_optimizer, mode='min', factor=0.1, patience=5, verbose=True)


# Logging
log_dir = os.path.abspath("run")
writer = SummaryWriter(log_dir=log_dir)
log_train = "run/train"
writer_train = SummaryWriter(log_train)
log_val = "run/val"
writer_val = SummaryWriter(log_val)
print(f"TensorBoard logs saved at: {log_dir}")


# Combined Training for VAE and LSTM
vae.train()
lstm_predictor.train()
for epoch in tqdm(range(num_epochs)):
    combined_epoch_loss = 0
    for batch_idx, (features, targets) in enumerate(train_loader):
        # VAE Forward and Loss
        vae_optimizer.zero_grad()
        reconstructed, z_mean, z_log_var = vae(features)
        vae_loss_value = vae_loss(reconstructed, features, z_mean, z_log_var)

        # LSTM Forward and Loss
        lstm_optimizer.zero_grad()
        predictions = lstm_predictor(z_mean.detach())  # Use latent space from VAE
        lstm_loss_value = nn.MSELoss()(predictions, targets)

        # Backpropagation
        total_loss = vae_loss_value + lstm_loss_value
        total_loss.backward()
        vae_optimizer.step()
        lstm_optimizer.step()

        combined_epoch_loss += total_loss.item()

    combined_epoch_loss /= len(train_loader)
    writer_train.add_scalar("Loss", combined_epoch_loss, epoch)

    # 验证阶段
    val_loss, _, _ = evaluate_combined_model(vae, lstm_predictor, test_loader, nn.MSELoss())
    writer_val.add_scalar("Loss", val_loss, epoch)
    print(f"Epoch {epoch + 1}, Combined Loss: {combined_epoch_loss:.4f}")

# Save Combined Model
def save_combined_model(vae, lstm_predictor, path):
    torch.save({
        'vae_state_dict': vae.state_dict(),
        'lstm_state_dict': lstm_predictor.state_dict()
    }, path)

save_combined_model(vae, lstm_predictor, "combined_lottery_model.pth")
print("Combined model saved.")


combined_test_loss, mean_predictions, mean_targets = evaluate_combined_model(vae, lstm_predictor, test_loader, nn.MSELoss())
print(f"Combined Test Loss: {combined_test_loss:.4f}")
print(f"Mean Predictions: {mean_predictions}")
print(f"Mean Targets: {mean_targets}")

print("===========================================================")
# 在训练结束后调用评估和绘制函数
combined_test_loss, mean_predictions, mean_targets = evaluate_combined_model(
    vae, lstm_predictor, test_loader, nn.MSELoss()
)

print(f"Combined Test Loss: {combined_test_loss:.4f}")
plot_predictions_vs_targets(mean_predictions, mean_targets, save_path="final_predictions_vs_targets.png")
print("Prediction vs Target plot saved as final_predictions_vs_targets.png")


def calculate_accuracy(mean_predictions, mean_targets, threshold=0.001):
    """
    Calculate the percentage accuracy of predictions within a threshold.

    Args:
        mean_predictions (numpy array): The mean predictions from the model.
        mean_targets (numpy array): The actual mean target values.
        threshold (float): The maximum allowed difference for a prediction to be considered correct.

    Returns:
        float: Accuracy as a percentage.
    """
    # Calculate the absolute difference between predictions and targets
    diff = np.abs(mean_predictions - mean_targets)
    correct_predictions = np.sum(diff <= threshold)
    total_predictions = len(mean_predictions)
    accuracy = (correct_predictions / total_predictions) * 100
    return accuracy


# Evaluate and calculate accuracy
combined_test_loss, mean_predictions, mean_targets = evaluate_combined_model(
    vae, lstm_predictor, test_loader, nn.MSELoss()
)
accuracy = calculate_accuracy(mean_predictions, mean_targets, threshold=0.1)

print(f"Combined Test Loss: {combined_test_loss:.4f}")
print(f"Mean Predictions: {mean_predictions}")
print(f"Mean Targets: {mean_targets}")
print(f"Prediction Accuracy: {accuracy:.2f}%")

# Plot predictions vs targets
plot_predictions_vs_targets(mean_predictions, mean_targets, save_path="final_predictions_vs_targets.png")
print("Prediction vs Target plot saved as final_predictions_vs_targets.png")

print("===================================================")


def predict_random_samples_with_debugging(vae, lstm_predictor, test_loader, num_samples=5):
    """
    Randomly selects samples from the test dataset, performs predictions,
    and includes debugging to check the diversity of latent features (z_mean).
    """
    vae.eval()
    lstm_predictor.eval()

    # Collect all test data
    all_features = []
    all_targets = []

    for features, targets in test_loader:
        all_features.append(features)
        all_targets.append(targets)

    # Concatenate all test features and targets into a single tensor
    all_features = torch.cat(all_features, dim=0)
    all_targets = torch.cat(all_targets, dim=0)

    # Select random indices
    random_indices = random.sample(range(len(all_features)), num_samples)
    selected_features = all_features[random_indices]
    selected_targets = all_targets[random_indices]

    predictions = []

    print("Checking z_mean values for each sample:")
    with torch.no_grad():
        for idx, features in enumerate(selected_features):
            features = features.unsqueeze(0)  # Add batch dimension
            _, z_mean, _ = vae(features)
            print(f"Sample {idx}, z_mean: {z_mean.squeeze().cpu().numpy()}")
            prediction = lstm_predictor(z_mean)
            predictions.append(prediction.squeeze().cpu().numpy())

    # Convert normalized values back to actual lottery numbers
    def denormalize(numbers):
        main_numbers = np.clip((numbers[:5] * 70).round(), 1, 70).astype(int).tolist()
        mega_ball = np.clip((numbers[5] * 25).round(), 1, 25).astype(int)
        return main_numbers + [mega_ball]

    # Display results
    print(f"{'Index':<10}{'Actual Numbers':<40}{'Predicted Numbers':<40}")
    print("=" * 90)
    for i, idx in enumerate(random_indices):
        actual = denormalize(selected_targets[i].cpu().numpy())
        predicted = denormalize(predictions[i])
        print(f"{idx:<10}{actual!s:<40}{predicted!s:<40}")

predict_random_samples_with_debugging(vae, lstm_predictor, test_loader, num_samples=2)


'''
检查数据样本的 z_mean 分布和值
'''

import numpy as np

all_z_means = []
vae.eval()
with torch.no_grad():
    for features, _ in test_loader:
        _, z_mean, _ = vae(features)
        all_z_means.append(z_mean.cpu().numpy())
all_z_means = np.vstack(all_z_means)

# 计算均值和方差
mean = np.mean(all_z_means, axis=0)
std = np.std(all_z_means, axis=0)
print("z_mean 均值:", mean)
print("z_mean 标准差:", std)


import matplotlib.pyplot as plt
plt.scatter(z_mean[:, 0], z_mean[:, 1])
plt.xlabel("z_mean[0]")
plt.ylabel("z_mean[1]")
plt.title("Latent Space Distribution")
plt.show()








