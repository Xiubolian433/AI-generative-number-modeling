import os
import sqlite3
import psycopg2
from urllib.parse import urlparse


class DatabaseConfig:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///payments.db')
        self.is_sqlite = self.database_url.startswith('sqlite')
        self.is_postgres = self.database_url.startswith('postgresql')

    def get_connection(self):
        """获取数据库连接"""
        if self.is_sqlite:
            # SQLite连接
            db_path = self.database_url.replace('sqlite:///', '')
            return sqlite3.connect(db_path)
        elif self.is_postgres:
            # PostgreSQL连接
            return psycopg2.connect(self.database_url)
        else:
            raise ValueError(f"Unsupported database URL: {self.database_url}")

    def get_placeholder(self):
        """获取SQL占位符"""
        return '?' if self.is_sqlite else '%s'


# 全局配置实例
db_config = DatabaseConfig()

