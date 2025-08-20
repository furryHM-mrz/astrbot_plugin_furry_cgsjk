# 小茶馆数据库插件 (astrbot_plugin_furry_cgsjk)

![版本](https://img.shields.io/badge/version-1.0.0-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-plugin-green)

为小茶馆插件提供数据支持的数据库插件。

## 功能介绍

本插件为AstrBot平台上的小茶馆系统提供完整的数据库支持，包括以下功能模块：

### 1. 茶叶商店管理
- 茶叶商品信息存储
- 商品数量管理
- 商品价格设置
- 商品类型分类
- 商品描述信息

### 2. 用户签到系统
- 用户签到次数统计
- 上次签到日期记录
- 签到获得金币累计

### 3. 经济系统
- 用户虚拟货币管理
- 货币增减操作

### 4. 背包系统
- 用户物品存储
- 物品数量管理
- 物品类型分类

### 5. 任务系统
- 每日任务
- 每周任务
- 特殊任务
- 任务进度追踪
- 任务奖励领取

## 数据库结构

插件使用SQLite数据库存储所有信息，包含以下数据表：

### tea_store (茶叶商品表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| tea_name | TEXT | 茶叶名称（唯一） |
| quantity | INTEGER | 数量 |
| tea_type | TEXT | 茶叶类型 |
| price | REAL | 价格 |
| description | TEXT | 描述 |

### admins (管理员表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID（唯一） |

### user_sign_in (用户签到表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID（唯一） |
| sign_in_count | INTEGER | 签到次数 |
| last_sign_in_date | TEXT | 上次签到日期 |
| sign_in_coins | REAL | 签到获得金币 |

### user_economy (用户经济表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID（唯一） |
| economy | REAL | 用户经济余额 |

### user_backpack (用户背包表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID |
| item_name | TEXT | 物品名称 |
| item_count | INTEGER | 物品数量 |
| item_type | TEXT | 物品类型 |
| item_value | REAL | 物品价值 |

### user_tasks (用户任务表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID |
| task_id | TEXT | 任务ID |
| task_name | TEXT | 任务名称 |
| task_description | TEXT | 任务描述 |
| task_progress | INTEGER | 任务进度 |
| task_target | INTEGER | 任务目标 |
| reward | INTEGER | 奖励 |
| status | TEXT | 状态（进行中/已完成/已领取） |
| task_type | TEXT | 任务类型（每日任务/每周任务/特殊任务） |

### user_task_progress (用户任务进度表)
| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| user_id | TEXT | 用户ID |
| task_id | TEXT | 任务ID |
| last_updated | TEXT | 最后更新时间 |

## API接口

插件提供以下数据库操作类：

### UserDB - 用户签到数据库操作
- `query_sign_in_count()` - 查询用户签到次数
- `query_last_sign_in_date()` - 查询用户上次签到日期
- `query_sign_in_coins()` - 查询用户签到获得的金币
- `update_sign_in(coins)` - 更新用户签到信息

### EconomyDB - 用户经济数据库操作
- `get_economy()` - 获取用户经济余额
- `add_economy(amount)` - 增加用户经济
- `reduce_economy(amount)` - 减少用户经济

### BackpackDB - 用户背包数据库操作
- `query_backpack()` - 查询用户背包
- `add_item(item_name, quantity, item_type, item_value)` - 添加物品到背包
- `remove_item(item_name, quantity)` - 从背包移除物品

### TeaDB - 茶叶商店数据库操作
- `get_all_tea_store()` - 获取所有茶叶商品
- `get_all_tea_store_with_continuous_id()` - 获取所有茶叶商品（连续ID）
- `get_tea_store_item(tea_id)` - 根据ID获取茶叶商品
- `get_tea_store_item_by_continuous_id(continuous_id)` - 根据连续ID获取茶叶商品
- `get_actual_id_by_continuous_id(continuous_id)` - 根据连续ID获取实际数据库ID
- `add_tea_to_store(tea_name, quantity, tea_type, price, description)` - 添加茶叶到商店
- `update_tea_quantity(tea_id, quantity_change)` - 更新茶叶数量
- `restock_tea(tea_id, quantity)` - 为茶叶补货
- `remove_tea_from_store(tea_id)` - 从商店移除茶叶

### TaskDB - 任务系统数据库操作
- `get_user_tasks()` - 获取用户任务
- `get_task_by_id(task_id)` - 根据任务ID获取任务
- `create_task(task_id, task_name, task_description, task_target, reward, task_type)` - 创建用户任务
- `update_task_progress(task_id, progress)` - 更新任务进度
- `complete_task(task_id)` - 完成任务
- `reset_daily_tasks()` - 重置每日任务
- `reset_weekly_tasks()` - 重置每周任务
- `get_task_progress(task_id)` - 获取任务进度更新时间
- `update_task_progress_time(task_id)` - 更新任务进度时间
- `claim_reward(task_id)` - 领取任务奖励
- `update_daily_random_task()` - 更新每日随机任务

## 使用说明

该插件作为AstrBot的数据库支持插件，主要为其他功能插件提供数据存储和查询服务。插件会在加载时自动初始化数据库结构。

数据文件存储在 `data/plugins/astrbot_plugin_furry_cgsjk/cgsjk.db` 路径下。

## 开发信息

- **插件名称**: astrbot_plugin_furry_cgsjk
- **作者**: furryhm
- **版本**: 1.0.0
- **描述**: 小茶馆数据库插件，为小茶馆插件提供数据支持