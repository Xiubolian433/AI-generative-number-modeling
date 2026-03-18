import http.client
import json
import csv
from tqdm import tqdm

# 创建 HTTPS 连接
conn = http.client.HTTPSConnection("mega-millions.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "b5b78de802msh45b4a624c9a36b0p196f8djsn0b3ec34ef836",
    'x-rapidapi-host': "mega-millions.p.rapidapi.com"
}

# 发送 GET 请求
conn.request("GET", "/", headers=headers)

# 获取响应数据
res = conn.getresponse()
data = res.read()  # 获取 bytes 数据
decoded_data = data.decode("utf-8")  # 解码为字符串

# 解析 JSON 数据
json_data = json.loads(decoded_data)  # 转换为 Python 字典

print(json.dumps(json_data, indent=4))

# 提取 `data` 列表中的字段
draws = json_data["data"]
csv_data = [["DrawingDate", "Number1", "Number2", "Number3", "Number4", "Number5", "MegaBall"]]

# 遍历所有记录并提取字段
for draw in tqdm(draws):
    row = [
        draw["DrawingDate"],
        draw["FirstNumber"],
        draw["SecondNumber"],
        draw["ThirdNumber"],
        draw["FourthNumber"],
        draw["FifthNumber"],
        draw["MegaBall"]
    ]
    csv_data.append(row)

# 写入 CSV 文件
csv_file_path = "API_drawing_data.csv"
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

print(f"数据已存储到 CSV 文件中: {csv_file_path}")







