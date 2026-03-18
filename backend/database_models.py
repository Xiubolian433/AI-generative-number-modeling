from database_config import db_config


def init_database():
    """初始化数据库表"""
    conn = db_config.get_connection()
    cursor = conn.cursor()

    try:
        if db_config.is_sqlite:
            # SQLite表创建
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT UNIQUE NOT NULL,
                    payer_id TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    credits INTEGER NOT NULL,
                    status TEXT DEFAULT 'created',
                    access_code TEXT UNIQUE NOT NULL,
                    device_fingerprint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_credits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    access_code TEXT UNIQUE NOT NULL,
                    total_credits INTEGER NOT NULL DEFAULT 0,
                    used_credits INTEGER NOT NULL DEFAULT 0,
                    remaining_credits INTEGER NOT NULL DEFAULT 0,
                    device_fingerprint TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES payments (access_code)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    access_code TEXT NOT NULL,
                    device_fingerprint TEXT NOT NULL,
                    is_primary BOOLEAN DEFAULT 0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES payments (access_code)
                )
            ''')

            # 新增：免费试用表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS free_trials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_fingerprint TEXT UNIQUE NOT NULL,
                    total_free_credits INTEGER NOT NULL DEFAULT 3,
                    used_free_credits INTEGER NOT NULL DEFAULT 0,
                    remaining_free_credits INTEGER NOT NULL DEFAULT 3,
                    is_active BOOLEAN DEFAULT 1,
                    first_used_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        else:
            # PostgreSQL表创建
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    payment_id VARCHAR(255) UNIQUE NOT NULL,
                    payer_id VARCHAR(255),
                    amount DECIMAL(10,2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    credits INTEGER NOT NULL,
                    status VARCHAR(50) DEFAULT 'created',
                    access_code VARCHAR(50) UNIQUE NOT NULL,
                    device_fingerprint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_credits (
                    id SERIAL PRIMARY KEY,
                    access_code VARCHAR(50) UNIQUE NOT NULL,
                    total_credits INTEGER NOT NULL DEFAULT 0,
                    used_credits INTEGER NOT NULL DEFAULT 0,
                    remaining_credits INTEGER NOT NULL DEFAULT 0,
                    device_fingerprint TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES payments (access_code)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_sessions (
                    id SERIAL PRIMARY KEY,
                    access_code VARCHAR(50) NOT NULL,
                    device_fingerprint TEXT NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (access_code) REFERENCES payments (access_code)
                )
            ''')

            # 新增：免费试用表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS free_trials (
                    id SERIAL PRIMARY KEY,
                    device_fingerprint TEXT UNIQUE NOT NULL,
                    total_free_credits INTEGER NOT NULL DEFAULT 3,
                    used_free_credits INTEGER NOT NULL DEFAULT 0,
                    remaining_free_credits INTEGER NOT NULL DEFAULT 3,
                    is_active BOOLEAN DEFAULT TRUE,
                    first_used_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        conn.commit()
        print("✅ 数据库表初始化成功")
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def create_indexes():
    """创建数据库索引"""
    conn = db_config.get_connection()
    cursor = conn.cursor()

    try:
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_access_code ON payments(access_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_device_fingerprint ON payments(device_fingerprint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_credits_access_code ON user_credits(access_code)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_user_credits_device_fingerprint ON user_credits(device_fingerprint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_sessions_access_code ON device_sessions(access_code)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_device_sessions_device_fingerprint ON device_sessions(device_fingerprint)')

        # 新增：免费试用索引
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_free_trials_device_fingerprint ON free_trials(device_fingerprint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_free_trials_is_active ON free_trials(is_active)')

        conn.commit()
        print("✅ 数据库索引创建成功")

    except Exception as e:
        print(f"⚠️ 索引创建失败: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    create_indexes()

























