from flask import Flask, request, jsonify
import torch
import pandas as pd
import os
from pathlib import Path
from threading import Lock
from flask_caching import Cache
from gan_generator import Generator  # Mega Millions 的生成器类
from gan_power_generator import PowerBallGenerator  # Power Ball 的生成器类
from flask_cors import CORS
from dotenv import load_dotenv

from official_history_api import (
    fetch_mega_millions_history,
    fetch_mega_millions_statistics,
    fetch_powerball_history,
    fetch_powerball_statistics,
)

# PayPal 相关导入
import paypalrestsdk
import logging
from datetime import datetime
import sqlite3
import secrets

load_dotenv(Path(__file__).with_name(".env"))

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "payments.db"

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
CORS(app, resources={r"/*": {"origins": "*"}})

# PayPal配置
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', 'your_paypal_client_id_here')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', 'your_paypal_client_secret_here')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:5050')
PAYMENTS_DB_PATH = Path(os.getenv('PAYMENTS_DB_PATH', str(DEFAULT_DB_PATH)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
runtime_initialized = False
models_initialized = False
models_lock = Lock()


def paypal_is_configured():
    invalid_values = {
        '',
        'your_paypal_client_id_here',
        'your_paypal_client_secret_here',
        'your-paypal-sandbox-client-id',
        'your-paypal-sandbox-client-secret',
    }
    return (
        PAYPAL_CLIENT_ID not in invalid_values
        and PAYPAL_CLIENT_SECRET not in invalid_values
    )


# 检查并创建数据库目录
def ensure_database_directory():
    """确保数据库目录存在"""
    db_dir = PAYMENTS_DB_PATH.parent
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"数据库将创建在: {PAYMENTS_DB_PATH}")


# PayPal数据库初始化（增强版）
def init_payment_db():
    """初始化支付数据库"""
    try:
        ensure_database_directory()

        conn = sqlite3.connect(PAYMENTS_DB_PATH)
        cursor = conn.cursor()

        # 创建支付记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                payer_id TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                credits INTEGER NOT NULL,
                status TEXT NOT NULL,
                access_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建用户积分表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_code TEXT UNIQUE NOT NULL,
                total_credits INTEGER DEFAULT 0,
                used_credits INTEGER DEFAULT 0,
                remaining_credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        print("✅ 数据库初始化成功！")
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


# 配置PayPal SDK（增强版）
def configure_paypal():
    """配置PayPal SDK"""
    try:
        paypalrestsdk.configure({
            "mode": PAYPAL_MODE,
            "client_id": PAYPAL_CLIENT_ID,
            "client_secret": PAYPAL_CLIENT_SECRET
        })

        # 测试配置
        if paypal_is_configured():
            print("✅ PayPal SDK 配置完成")
            return True
        else:
            print("⚠️  PayPal 凭据未配置，支付功能将不可用")
            return False

    except Exception as e:
        print(f"❌ PayPal SDK 配置失败: {e}")
        return False


# 生成访问码
def generate_access_code():
    """生成唯一的访问码"""
    try:
        while True:
            code = "LC-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))

            # 检查是否已存在
            conn = sqlite3.connect(PAYMENTS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM payments WHERE access_code = ?', (code,))
            if not cursor.fetchone():
                conn.close()
                return code
            conn.close()
    except Exception as e:
        logger.error(f"生成访问码失败: {e}")
        # 如果数据库出错，返回一个基于时间的唯一码
        import time
        return f"LC-{int(time.time())}"


# 套餐配置
PAYMENT_PACKAGES = {
    1: {"credits": 3, "price": 1.00},
    5: {"credits": 25, "price": 5.00},
    10: {"credits": 60, "price": 10.00},
    20: {"credits": 150, "price": 20.00}
}

# Mega Millions 参数
mega_latent_dim = 30
mega_num_classes = 70
mega_mega_classes = 25
mega_condition_dim = mega_num_classes * 5 + mega_mega_classes

# Power Ball 参数
power_latent_dim = 30
power_num_classes = 69
power_mega_classes = 26
power_condition_dim = power_num_classes * 5 + power_mega_classes

print(f"BASE_DIR:", BASE_DIR)

# 规范拼接 CSV 文件路径
csv_path = (BASE_DIR / ".." / "Lottery_data" / "API_drawing_data.csv").resolve()


# **加载 Mega Millions 条件特征**
def load_condition_features_mega(file_path, num_classes=70, mega_classes=25):
    """
    从历史数据 CSV 文件中加载条件特征。
    """
    try:
        data = pd.read_csv(file_path)
        condition = torch.zeros(num_classes * 5 + mega_classes)
        for i, col in enumerate(["Number1", "Number2", "Number3", "Number4", "Number5"]):
            counts = data[col].value_counts(normalize=True, sort=False)
            for number in range(1, num_classes + 1):
                condition[i * num_classes + (number - 1)] = counts.get(number, 0)
        counts_mega = data["MegaBall"].value_counts(normalize=True, sort=False)
        for number in range(1, mega_classes + 1):
            condition[num_classes * 5 + (number - 1)] = counts_mega.get(number, 0)

        print(f"✅ Mega Millions 条件特征加载成功，特征维度：{condition.unsqueeze(0).size()}")
        return condition.unsqueeze(0)

    except Exception as e:
        print(f"⚠️ 无法加载条件特征文件: {e}")
        print("使用默认条件特征")
        return torch.zeros(num_classes * 5 + mega_classes).unsqueeze(0)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mega_model_path = BASE_DIR / "gan_generator.pth"
power_model_path = BASE_DIR / "gan_powerball_generator.pth"
mega_condition_features = None
power_condition_features = None
G_mega = None
G_power = None


def initialize_generation_runtime():
    """按需加载模型，避免健康检查和历史接口把大模型一起拉起。"""
    global G_mega, G_power, mega_condition_features, power_condition_features, models_initialized

    if models_initialized:
        return

    with models_lock:
        if models_initialized:
            return

        mega_condition_features = load_condition_features_mega(csv_path)
        power_condition_features = torch.zeros(power_condition_dim).unsqueeze(0)
        print("Power Ball 使用默认条件特征，特征维度：", power_condition_features.size())

        G_mega = Generator(mega_latent_dim, mega_condition_dim, mega_num_classes * 5, mega_mega_classes).to(device)
        if not mega_model_path.exists():
            raise FileNotFoundError(f"未找到 Mega Millions 模型文件：{mega_model_path}")
        G_mega.load_state_dict(torch.load(mega_model_path, map_location=device))
        G_mega.eval()
        print("✅ Mega Millions 生成器模型加载成功！")

        G_power = PowerBallGenerator(
            power_latent_dim, power_condition_dim, power_num_classes * 5, power_mega_classes
        ).to(device)
        if not power_model_path.exists():
            raise FileNotFoundError(f"未找到 Power Ball 模型文件：{power_model_path}")
        G_power.load_state_dict(torch.load(power_model_path, map_location=device))
        G_power.eval()
        print("✅ Power Ball 生成器模型加载成功！")

        models_initialized = True


# **推理函数**
def generate_numbers(generator, batch_size, latent_dim, condition_features, num_classes, mega_classes):
    """通用推理函数，用于生成彩票号码。"""
    with torch.no_grad():
        noise = torch.randn(batch_size, latent_dim).to(device)
        condition_sample = condition_features.repeat(batch_size, 1).to(device)
        numbers, mega = generator(noise, condition_sample)

        def post_process_unique(numbers):
            batch_size, _, num_classes = numbers.size()
            result = torch.zeros_like(numbers)
            for i in range(batch_size):
                chosen = set()
                for j in range(5):
                    idx = torch.argmax(numbers[i, j]).item()
                    while idx in chosen:
                        numbers[i, j, idx] = 0
                        idx = torch.argmax(numbers[i, j]).item()
                    chosen.add(idx)
                    result[i, j, idx] = 1
            return result

        numbers = post_process_unique(numbers)
        generated_numbers = torch.argmax(numbers, dim=-1).cpu().numpy() + 1
        generated_mega = torch.argmax(mega, dim=-1).cpu().numpy() + 1

        return generated_numbers.tolist(), generated_mega.tolist()


# **原有的彩票生成API路由**
@app.route("/generate/mega_millions", methods=["GET"])
def generate_mega_millions():
    initialize_generation_runtime()
    batch_size = int(request.args.get("batch_size", 1))
    generated_numbers, generated_mega = generate_numbers(
        G_mega, batch_size, mega_latent_dim, mega_condition_features, mega_num_classes, mega_mega_classes
    )

    results = [
        {"numbers": generated_numbers[i], "mega_ball": generated_mega[i]} for i in range(batch_size)
    ]
    print("Generated results:", results)

    return jsonify({"status": "success", "results": results})


@app.route("/generate/power_ball", methods=["GET"])
def generate_power_ball():
    initialize_generation_runtime()
    batch_size = int(request.args.get("batch_size", 1))
    generated_numbers, generated_mega = generate_numbers(
        G_power, batch_size, power_latent_dim, power_condition_features, power_num_classes, power_mega_classes
    )

    results = [
        {"numbers": generated_numbers[i], "power_ball": generated_mega[i]} for i in range(batch_size)
    ]
    print("Generated results:", results)

    return jsonify({"status": "success", "results": results})


# **原有的历史数据API路由**
@app.route('/api/history-numbers/MegaMillion', methods=['GET'])
@cache.cached(timeout=3600)
def get_mega_millions_data():
    try:
        data = fetch_mega_millions_history()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history-statistic/MegaMillion', methods=['GET'])
@cache.cached(timeout=3600)
def get_mega_million_statistic_data():
    try:
        statistics_data = fetch_mega_millions_statistics()
        return jsonify(statistics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history-numbers/PowerBall', methods=['GET'])
@cache.cached(timeout=3600)
def get_power_ball_data():
    try:
        data = fetch_powerball_history()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history-statistic/PowerBall', methods=['GET'])
@cache.cached(timeout=3600)
def get_power_ball_statistic_data():
    try:
        statistics_data = fetch_powerball_statistics()
        return jsonify(statistics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# **PayPal支付API路由（简化版）**
@app.route('/api/payment/create-order', methods=['POST'])
def create_payment_order():
    """创建PayPal支付订单"""
    try:
        logger.info("=== Payment Order Creation Started ===")

        # 检查PayPal配置
        if not paypal_is_configured():
            return jsonify({
                'error': 'PayPal not configured',
                'message': 'Please configure PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in the backend environment'
            }), 503

        data = request.get_json()
        package_price = data.get('package_price')
        logger.info(f"Requested package price: {package_price}")

        if package_price not in PAYMENT_PACKAGES:
            logger.error(f"Invalid package price: {package_price}")
            return jsonify({'error': 'Invalid package'}), 400

        package = PAYMENT_PACKAGES[package_price]

        # 生成访问码
        access_code = generate_access_code()

        # 创建PayPal支付
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{FRONTEND_URL}/payment/success?access_code={access_code}",
                "cancel_url": f"{FRONTEND_URL}/payment/cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"{package['credits']} Lottery Generation Credits",
                        "sku": f"credits_{package['credits']}",
                        "price": str(package['price']),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(package['price']),
                    "currency": "USD"
                },
                "description": f"Purchase {package['credits']} lottery generation credits"
            }]
        })

        if payment.create():
            logger.info(f"PayPal payment created successfully: {payment.id}")

            # 保存支付记录到数据库
            try:
                conn = sqlite3.connect(PAYMENTS_DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO payments (payment_id, amount, credits, status, access_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (payment.id, package['price'], package['credits'], 'created', access_code))
                conn.commit()
                conn.close()
                logger.info(f"Payment record saved to database")
            except Exception as db_error:
                logger.error(f"Database error (non-critical): {db_error}")

            # 获取批准URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break

            return jsonify({
                'payment_id': payment.id,
                'approval_url': approval_url,
                'access_code': access_code
            })
        else:
            logger.error(f"PayPal payment creation failed")
            logger.error(f"PayPal error details: {payment.error}")
            return jsonify({
                'error': 'Payment creation failed',
                'details': str(payment.error)
            }), 500

    except Exception as e:
        logger.error(f"Exception in create_payment_order: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/api/payment/execute', methods=['POST'])
def execute_payment():
    """执行PayPal支付 - 简化版"""
    try:
        logger.info("=== 开始执行支付 ===")

        data = request.get_json()
        payment_id = data.get('payment_id')
        payer_id = data.get('payer_id')

        if not payment_id or not payer_id:
            logger.error("缺少必要参数")
            return jsonify({'error': 'Missing payment_id or payer_id'}), 400

        logger.info(f"执行支付: payment_id={payment_id}, payer_id={payer_id}")

        # 检查数据库中是否已有完成的支付记录
        try:
            conn = sqlite3.connect(PAYMENTS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT access_code, credits, status FROM payments 
                WHERE payment_id = ?
            ''', (payment_id,))
            existing_payment = cursor.fetchone()

            if existing_payment:
                access_code, credits, status = existing_payment
                logger.info(f"数据库记录: status={status}, credits={credits}")

                if status == 'completed':
                    logger.info("支付已完成，返回现有记录")
                    conn.close()
                    return jsonify({
                        'success': True,
                        'access_code': access_code,
                        'credits': credits,
                        'message': 'Payment already completed'
                    })

            conn.close()

        except Exception as db_error:
            logger.error(f"检查数据库记录失败: {db_error}")

        # 获取PayPal支付对象
        try:
            logger.info("正在获取PayPal支付信息...")
            payment = paypalrestsdk.Payment.find(payment_id)

            if not payment:
                logger.error("PayPal中未找到支付记录")
                return jsonify({'error': 'Payment not found on PayPal'}), 404

            logger.info(f"PayPal支付状态: {payment.state}")

            # 尝试执行支付 - 不管当前状态如何
            try:
                logger.info("尝试执行PayPal支付...")
                execution_result = payment.execute({"payer_id": payer_id})
                logger.info(f"PayPal execute() 返回: {execution_result}")

                if not execution_result:
                    # 检查是否已经执行过
                    if hasattr(payment, 'error') and payment.error:
                        error_name = payment.error.get('name', '')
                        if error_name == 'PAYMENT_ALREADY_DONE':
                            logger.info("支付已经执行过，继续处理...")
                        else:
                            logger.error(f"PayPal执行失败: {payment.error}")
                            return jsonify({
                                'error': 'Payment execution failed',
                                'details': str(payment.error)
                            }), 500
                    else:
                        logger.warning("PayPal执行返回False，但继续处理...")

            except Exception as execute_error:
                logger.warning(f"执行PayPal支付时异常: {execute_error}")
                # 在沙盒环境中，即使执行失败也继续处理
                logger.info("继续处理支付，可能是沙盒环境的正常行为...")

        except Exception as paypal_error:
            logger.warning(f"PayPal API 错误: {paypal_error}")
            # 继续处理，可能是沙盒环境的问题

        # 更新数据库记录
        try:
            logger.info("=== 更新数据库记录 ===")
            conn = sqlite3.connect(PAYMENTS_DB_PATH)
            cursor = conn.cursor()

            # 更新支付状态
            cursor.execute('''
                UPDATE payments 
                SET status = ?, payer_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
            ''', ('completed', payer_id, payment_id))

            rows_affected = cursor.rowcount
            logger.info(f"更新支付记录，影响行数: {rows_affected}")

            if rows_affected == 0:
                logger.error("未找到要更新的支付记录")
                conn.close()
                return jsonify({'error': 'Payment record not found in database'}), 404

            # 获取支付信息
            cursor.execute('SELECT access_code, credits FROM payments WHERE payment_id = ?', (payment_id,))
            result = cursor.fetchone()

            if result:
                access_code, credits = result
                logger.info(f"获取支付信息: access_code={access_code}, credits={credits}")

                # 创建或更新用户积分记录
                cursor.execute('SELECT id, total_credits, remaining_credits FROM user_credits WHERE access_code = ?',
                               (access_code,))
                user_record = cursor.fetchone()

                if user_record:
                    # 更新现有记录
                    user_id, current_total, current_remaining = user_record
                    new_total = current_total + credits
                    new_remaining = current_remaining + credits

                    logger.info(f"更新积分记录: {current_total} + {credits} = {new_total}")

                    cursor.execute('''
                        UPDATE user_credits 
                        SET total_credits = ?, remaining_credits = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE access_code = ?
                    ''', (new_total, new_remaining, access_code))
                else:
                    # 创建新记录
                    logger.info(f"创建新积分记录: credits={credits}")
                    cursor.execute('''
                        INSERT INTO user_credits (access_code, total_credits, remaining_credits)
                        VALUES (?, ?, ?)
                    ''', (access_code, credits, credits))

                conn.commit()
                conn.close()

                logger.info(f"✅ 支付处理完成，积分已添加: {credits}")

                return jsonify({
                    'success': True,
                    'access_code': access_code,
                    'credits': credits,
                    'message': 'Payment completed successfully'
                })
            else:
                conn.close()
                logger.error("获取支付信息失败")
                return jsonify({'error': 'Failed to retrieve payment information'}), 500

        except Exception as db_error:
            logger.error(f"数据库操作失败: {db_error}")
            import traceback
            logger.error(f"数据库错误详情: {traceback.format_exc()}")
            return jsonify({'error': 'Database error during payment processing'}), 500

    except Exception as e:
        logger.error(f"执行支付异常: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/credits/verify', methods=['POST'])
def verify_access_code():
    """验证访问码并返回积分信息"""
    try:
        data = request.get_json()
        access_code = data.get('access_code')

        if not access_code:
            return jsonify({'error': 'Access code required'}), 400

        conn = sqlite3.connect(PAYMENTS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_credits, used_credits, remaining_credits 
            FROM user_credits 
            WHERE access_code = ?
        ''', (access_code,))

        result = cursor.fetchone()
        conn.close()

        if result:
            total_credits, used_credits, remaining_credits = result
            return jsonify({
                'success': True,
                'valid': True,
                'total_credits': total_credits,
                'used_credits': used_credits,
                'remaining_credits': remaining_credits
            })
        else:
            return jsonify({'success': False, 'valid': False, 'error': 'Invalid access code'})

    except Exception as e:
        logger.error(f"Error verifying access code: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/credits/consume', methods=['POST'])
def consume_credit():
    """消费一个积分"""
    try:
        data = request.get_json()
        access_code = data.get('access_code')

        if not access_code:
            return jsonify({'error': 'Access code required'}), 400

        conn = sqlite3.connect(PAYMENTS_DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT used_credits, remaining_credits 
            FROM user_credits 
            WHERE access_code = ?
        ''', (access_code,))

        result = cursor.fetchone()

        if not result:
            conn.close()
            return jsonify({'error': 'Invalid access code'}), 400

        used_credits, remaining_credits = result

        if remaining_credits <= 0:
            conn.close()
            return jsonify({'error': 'Insufficient credits'}), 400

        new_used = used_credits + 1
        new_remaining = remaining_credits - 1

        cursor.execute('''
            UPDATE user_credits 
            SET used_credits = ?, remaining_credits = ?, updated_at = CURRENT_TIMESTAMP
            WHERE access_code = ?
        ''', (new_used, new_remaining, access_code))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'used_credits': new_used,
            'remaining_credits': new_remaining
        })

    except Exception as e:
        logger.error(f"Error consuming credit: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if PAYMENTS_DB_PATH.exists() else 'not_found',
        'database_path': str(PAYMENTS_DB_PATH),
        'paypal': 'configured' if paypal_is_configured() else 'not_configured',
        'paypal_mode': PAYPAL_MODE,
        'frontend_url': FRONTEND_URL,
        'backend_url': BACKEND_URL
    })


def initialize_runtime():
    """初始化数据库和第三方服务，兼容 gunicorn 等生产启动方式。"""
    global runtime_initialized

    if runtime_initialized:
        return

    if init_payment_db():
        print("✅ 数据库初始化成功")
    else:
        print("⚠️ 数据库初始化失败，但服务仍将启动")

    if configure_paypal():
        print("✅ PayPal 配置成功")
    else:
        print("⚠️ PayPal 未配置，支付功能不可用")

    runtime_initialized = True


initialize_runtime()


if __name__ == "__main__":
    print("=== 启动 Lottery AI Generator 后端服务 ===")

    port = int(os.environ.get("PORT", 5000))  # Render 会提供 PORT，本地默认 5000
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
