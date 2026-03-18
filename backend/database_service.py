from datetime import datetime
from database_config import db_config
from database_models import init_database


class DatabaseService:
    def __init__(self):
        # 确保数据库表存在
        init_database()

    def create_payment_record(self, payment_id, amount, credits, access_code, device_fingerprint=None):
        """创建支付记录"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 插入支付记录
            cursor.execute(f'''
                INSERT INTO payments (payment_id, amount, credits, access_code, device_fingerprint, status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (payment_id, amount, credits, access_code, device_fingerprint, 'created'))

            conn.commit()
            print(f"✅ 支付记录创建成功: {payment_id}")
            return True

        except Exception as e:
            print(f"❌ 创建支付记录失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def complete_payment(self, payment_id, payer_id, device_fingerprint=None):
        """完成支付并立即激活积分"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 查找支付记录
            cursor.execute(f'''
                SELECT access_code, credits FROM payments 
                WHERE payment_id = {placeholder}
            ''', (payment_id,))

            result = cursor.fetchone()
            if not result:
                print(f"❌ 未找到支付记录: {payment_id}")
                return None

            access_code, credits = result

            # 更新支付状态
            cursor.execute(f'''
                UPDATE payments 
                SET status = {placeholder}, payer_id = {placeholder}, device_fingerprint = {placeholder}, updated_at = {placeholder}
                WHERE payment_id = {placeholder}
            ''', ('completed', payer_id, device_fingerprint, datetime.now(), payment_id))

            # 立即创建并激活积分记录
            cursor.execute(f'''
                INSERT INTO user_credits (access_code, total_credits, remaining_credits, device_fingerprint, is_active)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT(access_code) DO UPDATE SET
                total_credits = total_credits + {placeholder},
                remaining_credits = remaining_credits + {placeholder},
                updated_at = {placeholder}
            ''' if not db_config.is_sqlite else f'''
                INSERT OR REPLACE INTO user_credits (access_code, total_credits, remaining_credits, device_fingerprint, is_active)
                VALUES ({placeholder}, 
                        COALESCE((SELECT total_credits FROM user_credits WHERE access_code = {placeholder}), 0) + {placeholder},
                        COALESCE((SELECT remaining_credits FROM user_credits WHERE access_code = {placeholder}), 0) + {placeholder},
                        {placeholder}, 1)
            ''', (access_code, credits, credits, device_fingerprint, 1) if not db_config.is_sqlite
            else (access_code, access_code, credits, access_code, credits, device_fingerprint))

            # 创建设备会话记录（首次支付设备为主设备）
            cursor.execute(f'''
                INSERT INTO device_sessions (access_code, device_fingerprint, is_primary, last_used)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (access_code, device_fingerprint, 1, datetime.now()))

            conn.commit()
            print(f"✅ 支付完成，积分已立即激活: {credits}")
            return (access_code, credits)

        except Exception as e:
            print(f"❌ 完成支付失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def verify_access_code_with_device(self, access_code, device_fingerprint):
        """验证访问码并绑定新设备"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 检查访问码是否存在且激活
            cursor.execute(f'''
                SELECT total_credits, used_credits, remaining_credits, is_active 
                FROM user_credits 
                WHERE access_code = {placeholder} AND is_active = TRUE
            ''', (access_code,))

            result = cursor.fetchone()
            if not result:
                return None

            total_credits, used_credits, remaining_credits, is_active = result

            # 检查设备是否已经绑定
            cursor.execute(f'''
                SELECT id FROM device_sessions 
                WHERE access_code = {placeholder} AND device_fingerprint = {placeholder}
            ''', (access_code, device_fingerprint))

            device_exists = cursor.fetchone()

            if not device_exists:
                # 绑定新设备
                cursor.execute(f'''
                    INSERT INTO device_sessions (access_code, device_fingerprint, is_primary, last_used)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ''', (access_code, device_fingerprint, 0, datetime.now()))
            else:
                # 更新最后使用时间
                cursor.execute(f'''
                    UPDATE device_sessions 
                    SET last_used = {placeholder}
                    WHERE access_code = {placeholder} AND device_fingerprint = {placeholder}
                ''', (datetime.now(), access_code, device_fingerprint))

            conn.commit()

            return {
                'total_credits': total_credits,
                'used_credits': used_credits,
                'remaining_credits': remaining_credits,
                'device_bound': True
            }

        except Exception as e:
            print(f"❌ 验证访问码失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_or_create_free_trial(self, device_fingerprint):
        """获取或创建免费试用记录"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 检查是否已存在免费试用记录
            cursor.execute(f'''
                SELECT total_free_credits, used_free_credits, remaining_free_credits, is_active
                FROM free_trials 
                WHERE device_fingerprint = {placeholder}
            ''', (device_fingerprint,))

            result = cursor.fetchone()

            if result:
                # 已存在记录
                total_free_credits, used_free_credits, remaining_free_credits, is_active = result
                return {
                    'total_free_credits': total_free_credits,
                    'used_free_credits': used_free_credits,
                    'remaining_free_credits': remaining_free_credits,
                    'is_new_device': False
                }
            else:
                # 新设备，创建免费试用记录
                cursor.execute(f'''
                    INSERT INTO free_trials (device_fingerprint, total_free_credits, used_free_credits, remaining_free_credits, is_active)
                    VALUES ({placeholder}, 3, 0, 3, TRUE)
                ''', (device_fingerprint,))

                conn.commit()
                print(f"✅ 新设备免费试用创建成功: {device_fingerprint[:8]}...")

                return {
                    'total_free_credits': 3,
                    'used_free_credits': 0,
                    'remaining_free_credits': 3,
                    'is_new_device': True
                }

        except Exception as e:
            print(f"❌ 获取免费试用失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def consume_free_trial_credit(self, device_fingerprint):
        """消费一个免费试用积分"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 检查免费试用状态
            cursor.execute(f'''
                SELECT remaining_free_credits, used_free_credits FROM free_trials 
                WHERE device_fingerprint = {placeholder} AND is_active = TRUE
            ''', (device_fingerprint,))

            result = cursor.fetchone()
            if not result:
                return None

            remaining_free_credits, used_free_credits = result
            if remaining_free_credits <= 0:
                return None

            # 更新免费试用积分
            new_remaining = remaining_free_credits - 1
            new_used = used_free_credits + 1
            now = datetime.now()

            cursor.execute(f'''
                UPDATE free_trials 
                SET remaining_free_credits = {placeholder}, 
                    used_free_credits = {placeholder}, 
                    last_used_at = {placeholder},
                    first_used_at = COALESCE(first_used_at, {placeholder}),
                    updated_at = {placeholder}
                WHERE device_fingerprint = {placeholder}
            ''', (new_remaining, new_used, now, now, now, device_fingerprint))

            conn.commit()
            print(f"✅ 免费试用积分消费成功，剩余: {new_remaining}")
            return new_remaining

        except Exception as e:
            print(f"❌ 消费免费试用积分失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_credits_by_device(self, device_fingerprint):
        """通过设备指纹获取积分信息（包括免费试用和付费积分）"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 获取免费试用积分
            free_trial_info = self.get_or_create_free_trial(device_fingerprint)

            # 获取付费积分
            cursor.execute(f'''
                SELECT uc.total_credits, uc.used_credits, uc.remaining_credits, uc.access_code
                FROM user_credits uc
                JOIN device_sessions ds ON uc.access_code = ds.access_code
                WHERE ds.device_fingerprint = {placeholder} AND uc.is_active = TRUE
                ORDER BY ds.last_used DESC
                LIMIT 1
            ''', (device_fingerprint,))

            paid_result = cursor.fetchone()

            if paid_result:
                total_credits, used_credits, remaining_credits, access_code = paid_result

                # 更新最后使用时间
                cursor.execute(f'''
                    UPDATE device_sessions 
                    SET last_used = {placeholder}
                    WHERE device_fingerprint = {placeholder} AND access_code = {placeholder}
                ''', (datetime.now(), device_fingerprint, access_code))

                conn.commit()

                # 合并免费试用和付费积分
                total_remaining = free_trial_info['remaining_free_credits'] + remaining_credits

                return {
                    'total_credits': total_credits,
                    'used_credits': used_credits,
                    'remaining_credits': remaining_credits,
                    'free_credits': free_trial_info['remaining_free_credits'],
                    'paid_credits': remaining_credits,
                    'total_remaining': total_remaining,
                    'access_code': access_code,
                    'is_new_device': free_trial_info.get('is_new_device', False)
                }
            else:
                # 只有免费试用积分
                return {
                    'total_credits': 0,
                    'used_credits': 0,
                    'remaining_credits': 0,
                    'free_credits': free_trial_info['remaining_free_credits'],
                    'paid_credits': 0,
                    'total_remaining': free_trial_info['remaining_free_credits'],
                    'access_code': None,
                    'is_new_device': free_trial_info.get('is_new_device', False)
                }

        except Exception as e:
            print(f"❌ 获取设备积分失败: {e}")
            return None
        finally:
            conn.close()

    def consume_credit(self, access_code, device_fingerprint):
        """消费一个积分（优先使用免费试用，然后使用付费积分）"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            # 首先尝试消费免费试用积分
            free_remaining = self.consume_free_trial_credit(device_fingerprint)
            if free_remaining is not None:
                # 免费试用积分消费成功
                # 获取付费积分信息用于返回总剩余数
                cursor.execute(f'''
                    SELECT uc.remaining_credits
                    FROM user_credits uc
                    JOIN device_sessions ds ON uc.access_code = ds.access_code
                    WHERE ds.device_fingerprint = {placeholder} AND uc.is_active = TRUE
                    ORDER BY ds.last_used DESC
                    LIMIT 1
                ''', (device_fingerprint,))

                paid_result = cursor.fetchone()
                paid_remaining = paid_result[0] if paid_result else 0

                total_remaining = free_remaining + paid_remaining
                return total_remaining

            # 免费试用积分用完，尝试消费付费积分
            if access_code:
                # 验证设备权限
                cursor.execute(f'''
                    SELECT ds.id FROM device_sessions ds
                    JOIN user_credits uc ON ds.access_code = uc.access_code
                    WHERE ds.access_code = {placeholder} AND ds.device_fingerprint = {placeholder} AND uc.is_active = TRUE
                ''', (access_code, device_fingerprint))

                if not cursor.fetchone():
                    print(f"❌ 设备未授权: {device_fingerprint[:8]}...")
                    return None

                # 检查剩余积分
                cursor.execute(f'''
                    SELECT remaining_credits, used_credits FROM user_credits 
                    WHERE access_code = {placeholder} AND is_active = TRUE
                ''', (access_code,))

                result = cursor.fetchone()
                if not result:
                    return None

                remaining_credits, used_credits = result
                if remaining_credits <= 0:
                    return None

                # 更新积分
                new_remaining = remaining_credits - 1
                new_used = used_credits + 1

                cursor.execute(f'''
                    UPDATE user_credits 
                    SET remaining_credits = {placeholder}, used_credits = {placeholder}, updated_at = {placeholder}
                    WHERE access_code = {placeholder}
                ''', (new_remaining, new_used, datetime.now(), access_code))

                # 更新设备最后使用时间
                cursor.execute(f'''
                    UPDATE device_sessions 
                    SET last_used = {placeholder}
                    WHERE access_code = {placeholder} AND device_fingerprint = {placeholder}
                ''', (datetime.now(), access_code, device_fingerprint))

                conn.commit()

                # 获取免费试用剩余积分
                cursor.execute(f'''
                    SELECT remaining_free_credits FROM free_trials 
                    WHERE device_fingerprint = {placeholder}
                ''', (device_fingerprint,))

                free_result = cursor.fetchone()
                free_remaining = free_result[0] if free_result else 0

                total_remaining = free_remaining + new_remaining
                return total_remaining

            return None

        except Exception as e:
            print(f"❌ 消费积分失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def verify_access_code(self, access_code):
        """验证访问码（兼容旧接口）"""
        conn = db_config.get_connection()
        cursor = conn.cursor()
        placeholder = db_config.get_placeholder()

        try:
            cursor.execute(f'''
                SELECT total_credits, used_credits, remaining_credits 
                FROM user_credits 
                WHERE access_code = {placeholder} AND is_active = TRUE
            ''', (access_code,))

            result = cursor.fetchone()
            if result:
                total_credits, used_credits, remaining_credits = result
                return {
                    'total_credits': total_credits,
                    'used_credits': used_credits,
                    'remaining_credits': remaining_credits
                }
            return None

        except Exception as e:
            print(f"❌ 验证访问码失败: {e}")
            return None
        finally:
            conn.close()


# 全局服务实例
db_service = DatabaseService()





















