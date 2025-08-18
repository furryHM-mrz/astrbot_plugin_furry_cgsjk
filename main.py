from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import sqlite3
import os

PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_furry_cgsjk')
DATABASE_FILE = os.path.join(PLUGIN_DIR, 'cgsjk.db')

def init_database():
    """初始化数据库表结构"""
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # 创建茶叶商品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tea_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tea_name TEXT NOT NULL UNIQUE,
            quantity INTEGER DEFAULT 0,
            tea_type TEXT DEFAULT '普通',
            price REAL DEFAULT 0.0,
            description TEXT DEFAULT ''
        )
    ''')
    
    # 创建管理员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE
        )
    ''')
    
    # 为用户签到系统创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sign_in (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            sign_in_count INTEGER DEFAULT 0,
            last_sign_in_date TEXT,
            sign_in_coins REAL DEFAULT 0.0
        )
    ''')
    
    # 为经济系统创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_economy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            economy REAL DEFAULT 0.0
        )
    ''')
    
    # 为背包系统创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_backpack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_count INTEGER DEFAULT 1,
            item_type TEXT DEFAULT '茶叶',
            item_value REAL DEFAULT 0.0
        )
    ''')
    
    # 为任务系统创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            task_description TEXT NOT NULL,
            task_progress INTEGER DEFAULT 0,
            task_target INTEGER NOT NULL,
            reward INTEGER NOT NULL,
            status TEXT DEFAULT '进行中', -- 进行中/已完成/已领取
            task_type TEXT DEFAULT '每日任务' -- 每日任务/每周任务/特殊任务
        )
    ''')
    
    # 插入默认任务
    default_tasks = [
        ('daily_drink_tea', '品茶师', '品尝3种不同的茶叶', 0, 3, 50, '每日任务'),
        ('daily_buy_tea', '采购员', '购买茶叶2次', 0, 2, 30, '每日任务'),
        ('weekly_collect_tea', '收藏家', '收集5种不同的茶叶', 0, 5, 100, '每周任务')
    ]
    
    # 插入默认任务到数据库
    for task in default_tasks:
        task_id, task_name, desc, progress, target, reward, task_type = task
        cursor.execute('''
            INSERT OR IGNORE INTO user_tasks 
            (task_id, task_name, task_description, task_progress, task_target, reward, task_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, task_name, desc, progress, target, reward, task_type))
    
    # 为任务系统创建用户任务关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_task_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            UNIQUE(user_id, task_id)
        )
    ''')
    
    # 插入默认茶叶商品
    default_teas = [
        ('龙井茶', 100, '绿茶', 50.0, '清香淡雅，回味甘甜'),
        ('铁观音', 100, '乌龙茶', 45.0, '香气浓郁，滋味醇厚'),
        ('普洱茶', 100, '黑茶', 60.0, '陈香浓郁，生津止渴'),
        ('大红袍', 100, '乌龙茶', 80.0, '岩韵明显，香气高长'),
        ('碧螺春', 100, '绿茶', 55.0, '条索紧结，卷曲如螺'),
        ('金骏眉', 50, '红茶', 120.0, '香气高锐，滋味鲜爽'),
        ('银针白毫', 50, '白茶', 90.0, '满披白毫，香气清鲜')
    ]
    
    for tea in default_teas:
        cursor.execute('''
            INSERT OR IGNORE INTO tea_store 
            (tea_name, quantity, tea_type, price, description) 
            VALUES (?, ?, ?, ?, ?)
        ''', tea)
    
    conn.commit()
    conn.close()

def open_databases(config, db_file, user_id):
    """
    打开所有数据库的上下文管理器
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _open_databases(config, db_file, user_id):
        db_path = DATABASE_FILE
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            yield (
                UserDB(conn, user_id),
                EconomyDB(conn, user_id),
                TaskDB(conn, user_id),
                BackpackDB(conn, user_id),
                TeaDB(conn, user_id)
            )
        except sqlite3.Error as e:
            logger.error(f"数据库连接错误: {e}")
            raise  # 向上抛出异常
        finally:
            if conn:
                conn.close()
    
    return _open_databases(config, db_file, user_id)

def open_tea_database(config, db_file, user_id):
    """
    打开茶馆数据库的上下文管理器
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _open_tea_database(config, db_file, user_id):
        db_path = DATABASE_FILE
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            yield TeaDB(conn, user_id)
        except sqlite3.Error as e:
            logger.error(f"数据库连接错误: {e}")
            raise  # 向上抛出异常
        finally:
            if conn:
                conn.close()
    
    return _open_tea_database(config, db_file, user_id)

class UserDB:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.cursor = conn.cursor()
        self.user_id = user_id
        # 确保用户存在
        self.cursor.execute('INSERT OR IGNORE INTO user_sign_in (user_id) VALUES (?)', (user_id,))
        self.conn.commit()
        
    def query_sign_in_count(self):
        """查询用户签到次数"""
        self.cursor.execute('SELECT sign_in_count FROM user_sign_in WHERE user_id=?', (self.user_id,))
        result = self.cursor.fetchone()
        return result if result else (0,)
        
    def query_last_sign_in_date(self):
        """查询用户上次签到日期"""
        self.cursor.execute('SELECT last_sign_in_date FROM user_sign_in WHERE user_id=?', (self.user_id,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None
        
    def query_sign_in_coins(self):
        """查询用户签到获得的金币"""
        self.cursor.execute('SELECT sign_in_coins FROM user_sign_in WHERE user_id=?', (self.user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0.0
        
    def update_sign_in(self, coins):
        """更新用户签到信息"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            UPDATE user_sign_in 
            SET sign_in_count = sign_in_count + 1, 
                last_sign_in_date = ?, 
                sign_in_coins = sign_in_coins + ?
            WHERE user_id = ?
        ''', (today, coins, self.user_id))
        self.conn.commit()

class EconomyDB:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.cursor = conn.cursor()
        self.user_id = user_id
        # 确保用户存在
        self.cursor.execute('INSERT OR IGNORE INTO user_economy (user_id) VALUES (?)', (user_id,))
        self.conn.commit()
        
    def get_economy(self):
        """获取用户经济"""
        self.cursor.execute('SELECT economy FROM user_economy WHERE user_id=?', (self.user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0.0
        
    def add_economy(self, amount):
        """增加用户经济"""
        self.cursor.execute('''
            UPDATE user_economy 
            SET economy = economy + ? 
            WHERE user_id = ?
        ''', (amount, self.user_id))
        self.conn.commit()
        
    def reduce_economy(self, amount):
        """减少用户经济"""
        self.cursor.execute('''
            UPDATE user_economy 
            SET economy = economy - ? 
            WHERE user_id = ?
        ''', (amount, self.user_id))
        self.conn.commit()

class BackpackDB:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.cursor = conn.cursor()
        self.user_id = user_id
        
    def query_backpack(self):
        """查询用户背包"""
        self.cursor.execute('SELECT * FROM user_backpack WHERE user_id=?', (self.user_id,))
        return self.cursor.fetchall()
        
    def add_item(self, item_name, quantity=1, item_type='茶叶', item_value=0.0):
        """添加物品到背包"""
        # 检查物品是否已存在
        self.cursor.execute('''
            SELECT id, item_count FROM user_backpack 
            WHERE user_id=? AND item_name=?
        ''', (self.user_id, item_name))
        result = self.cursor.fetchone()
        
        if result:
            # 物品已存在，更新数量
            item_id, current_count = result
            new_count = current_count + quantity
            self.cursor.execute('''
                UPDATE user_backpack 
                SET item_count = ? 
                WHERE id = ?
            ''', (new_count, item_id))
        else:
            # 物品不存在，插入新记录
            self.cursor.execute('''
                INSERT INTO user_backpack 
                (user_id, item_name, item_count, item_type, item_value) 
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, item_name, quantity, item_type, item_value))
        self.conn.commit()
        
    def remove_item(self, item_name, quantity=1):
        """从背包移除物品"""
        self.cursor.execute('''
            SELECT id, item_count FROM user_backpack 
            WHERE user_id=? AND item_name=?
        ''', (self.user_id, item_name))
        result = self.cursor.fetchone()
        
        if result:
            item_id, current_count = result
            if current_count <= quantity:
                # 数量不足或相等，删除整行
                self.cursor.execute('DELETE FROM user_backpack WHERE id = ?', (item_id,))
            else:
                # 数量足够，减少数量
                new_count = current_count - quantity
                self.cursor.execute('''
                    UPDATE user_backpack 
                    SET item_count = ? 
                    WHERE id = ?
                ''', (new_count, item_id))
            self.conn.commit()  # 提交事务
            return True
        return False

class TeaDB:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.cursor = conn.cursor()
        self.user_id = user_id
        
    def get_all_tea_store(self):
        """获取所有茶叶商品"""
        self.cursor.execute('SELECT * FROM tea_store')
        return self.cursor.fetchall()
        
    def get_tea_store_item(self, tea_id):
        """根据ID获取茶叶商品"""
        self.cursor.execute('SELECT * FROM tea_store WHERE id=?', (tea_id,))
        return self.cursor.fetchone()
        
    def add_tea_to_store(self, tea_name, quantity, tea_type, price, description):
        """添加茶叶到商店"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO tea_store 
            (tea_name, quantity, tea_type, price, description) 
            VALUES (?, ?, ?, ?, ?)
        ''', (tea_name, quantity, tea_type, price, description))
        self.conn.commit()
        return self.cursor.lastrowid
        
    def update_tea_quantity(self, tea_id, quantity_change):
        """更新茶叶数量"""
        self.cursor.execute('''
            UPDATE tea_store 
            SET quantity = quantity + ? 
            WHERE id = ?
        ''', (quantity_change, tea_id))
        self.conn.commit()
        
    def restock_tea(self, tea_id, quantity):
        """为茶叶补货"""
        self.cursor.execute('''
            UPDATE tea_store 
            SET quantity = quantity + ? 
            WHERE id = ?
        ''', (quantity, tea_id))
        self.conn.commit()
        # 返回更新后的茶叶信息
        return self.get_tea_store_item(tea_id)
        
    def remove_tea_from_store(self, tea_id):
        """从商店移除茶叶"""
        self.cursor.execute('DELETE FROM tea_store WHERE id=?', (tea_id,))
        self.conn.commit()
        
    def is_admin(self, user_id):
        """检查用户是否为管理员"""
        # 不再使用数据库检查，由主插件通过配置文件管理
        return False
        
    def add_admin(self, user_id):
        """添加管理员"""
        # 不再使用数据库操作，由主插件通过配置文件管理
        pass
        
    def remove_admin(self, user_id):
        """移除管理员"""
        # 不再使用数据库操作，由主插件通过配置文件管理
        pass

class TaskDB:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.cursor = conn.cursor()
        self.user_id = user_id
        
    def get_user_tasks(self):
        """获取用户任务"""
        self.cursor.execute('''
            SELECT * FROM user_tasks 
            WHERE user_id=? 
            ORDER BY task_type, task_name
        ''', (self.user_id,))
        return self.cursor.fetchall()
        
    def get_task_by_id(self, task_id):
        """根据任务ID获取任务"""
        self.cursor.execute('''
            SELECT * FROM user_tasks 
            WHERE user_id=? AND task_id=?
        ''', (self.user_id, task_id))
        return self.cursor.fetchone()
        
    def create_task(self, task_id, task_name, task_description, task_target, reward, task_type):
        """创建用户任务"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO user_tasks 
            (user_id, task_id, task_name, task_description, task_progress, task_target, reward, status, task_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.user_id, task_id, task_name, task_description, 0, task_target, reward, '进行中', task_type))
        self.conn.commit()
        
    def update_task_progress(self, task_id, progress):
        """更新任务进度"""
        self.cursor.execute('''
            UPDATE user_tasks 
            SET task_progress = ? 
            WHERE user_id=? AND task_id=?
        ''', (progress, self.user_id, task_id))
        self.conn.commit()
        
    def complete_task(self, task_id):
        """完成任务"""
        self.cursor.execute('''
            UPDATE user_tasks 
            SET status = '已完成' 
            WHERE user_id=? AND task_id=?
        ''', (self.user_id, task_id))
        self.conn.commit()
        
    def reset_daily_tasks(self):
        """重置每日任务"""
        self.cursor.execute('''
            UPDATE user_tasks 
            SET task_progress = 0, status = '进行中'
            WHERE user_id=? AND task_type='每日任务'
        ''', (self.user_id,))
        self.conn.commit()
        
    def reset_weekly_tasks(self):
        """重置每周任务"""
        self.cursor.execute('''
            UPDATE user_tasks 
            SET task_progress = 0, status = '进行中'
            WHERE user_id=? AND task_type='每周任务'
        ''', (self.user_id,))
        self.conn.commit()
        
    def get_task_progress(self, task_id):
        """获取任务进度更新时间"""
        self.cursor.execute('''
            SELECT last_updated FROM user_task_progress
            WHERE user_id=? AND task_id=?
        ''', (self.user_id, task_id))
        result = self.cursor.fetchone()
        return result[0] if result else None
        
    def update_task_progress_time(self, task_id):
        """更新任务进度时间"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT OR REPLACE INTO user_task_progress
            (user_id, task_id, last_updated)
            VALUES (?, ?, ?)
        ''', (self.user_id, task_id, now))
        self.conn.commit()

    def claim_reward(self, task_id):
        """领取任务奖励"""
        # 更新任务状态为已领取
        # 为了简单起见，我们将状态更新为"已领取"
        self.cursor.execute('''
            UPDATE user_tasks 
            SET status = '已领取' 
            WHERE user_id=? AND task_id=? AND status='已完成'
        ''', (self.user_id, task_id))
        self.conn.commit()
        
        # 返回是否成功更新（即是否真的领取了奖励）
        return self.cursor.rowcount > 0

    def update_daily_random_task(self):
        """更新每日随机任务"""
        from datetime import datetime, date
        import random
        
        # 获取今天的日期作为任务ID的一部分
        today = date.today()
        daily_random_task_id = f"daily_random_{today.strftime('%Y%m%d')}"
        
        # 随机任务选项
        random_tasks = [
            ('random_tea_master', '茶道大师', '品尝5种不同的茶叶', 5, 80),
            ('random_tea_collector', '茶叶收藏家', '收集3种不同的茶叶', 3, 60),
            ('random_tea_drinker', '品茶达人', '品尝同一种茶叶3次', 3, 40),
            ('random_shop_helper', '购物助手', '购买茶叶3次', 3, 45),
            ('random_tea_seller', '茶叶商人', '卖出茶叶2次', 2, 35)
        ]
        
        # 检查是否已有今天的随机任务
        self.cursor.execute('''
            SELECT * FROM user_tasks 
            WHERE user_id=? AND task_id=?
        ''', (self.user_id, daily_random_task_id))
        
        existing_task = self.cursor.fetchone()
        
        # 如果没有今天的随机任务，则创建一个
        if not existing_task:
            # 随机选择一个任务
            random_task = random.choice(random_tasks)
            # 创建新的每日随机任务
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_tasks 
                (user_id, task_id, task_name, task_description, task_progress, task_target, reward, status, task_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.user_id, daily_random_task_id, f"今日挑战: {random_task[1]}", 
                  random_task[2], 0, random_task[3], random_task[4], '进行中', '每日任务'))
            self.conn.commit()
            
        return daily_random_task_id

@register("furryhm", "astrbot_plugin_furry_cgsjk", "小茶馆数据库插件", "1.0.0")
class TeaDatabasePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        init_database()
        self.config = {}  # 添加配置属性
        # 提供获取数据库连接的方法，供主插件调用
        self.get_databases = lambda config, db_file, user_id: open_databases(config, db_file, user_id)
        self.get_db_path = lambda: DATABASE_FILE
        
    async def on_astrbot_loaded(self):
        logger.info("------ cgsjk ------")
        logger.info("小茶馆数据库插件已加载")
        logger.info("------ cgsjk ------")
        
