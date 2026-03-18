import json
import csv

# 示例 JSON 数据 (bytes 类型，解码为字符串)
json_data = b'{"status":"success","data":[{"DrawingDate":"2024-12-20T00:00:00.000Z","FirstNumber":2,"SecondNumber":20,"ThirdNumber":51,"FourthNumber":56,"FifthNumber":67,"MegaBall":19}]}'
decoded_data = json_data.decode("utf-8")  # 解码为字符串

# 解析 JSON 数据
data = json.loads(decoded_data)  # 转换为 Python 字典

# 提取 `data` 列表中的字段
draws = data["data"]
csv_data = [["DrawingDate", "Number1", "Number2", "Number3", "Number4", "Number5", "MegaBall"]]

# 遍历所有记录并提取字段
for draw in draws:
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
csv_file_path = "drawing_data.csv"
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

print(f"数据已存储到 CSV 文件中: {csv_file_path}")

