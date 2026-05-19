# Dify Bridge - Dify 服务中台

为 Dify Agent 提供数据服务和能力封装的中转平台。

## 功能特性

- **设备记忆管理** - 存储和查询设备基本信息、常见故障 Top3、保养记录
- **历史解决方案** - 记录和检索历史维修案例
- **Dify 工具接口** - 为 Dify Chatflow 提供可调用的工具 API
- **长期记忆能力** - 支持跨会话的设备画像和案例积累
- **Dify 能力封装** - 未来可封装 Dify Agent API 供外部系统调用

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      Dify Chatflow                       │
│  (对话流程、会话变量管理、知识库检索)                      │
└─────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│                   Dify Bridge 服务层                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Dify 工具 API                            │ │
│  │  • 设备记忆查询/更新  • 相似案例检索  • 解决方案保存  │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              核心业务逻辑层                           │ │
│  │  • 设备管理  • 案例匹配                               │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                数据访问层 (Repository)                │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                    SQLite 数据库                          │
│  • device_memory      - 设备记忆表 (设备画像、常见故障)     │
│  • solution_history   - 历史解决方案表                   │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
vi .env  # 编辑配置
```

### 2. 数据库迁移

本项目使用 Alembic 管理数据库迁移。

```bash
# 激活虚拟环境
source venv/Scripts/activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac

# 执行迁移（首次运行会创建数据库和表）
python -m alembic upgrade head

# 查看当前迁移状态
python -m alembic current

# 查看迁移历史
python -m alembic history
```

**创建新迁移：**

当修改了 `app/db/models.py` 中的模型后：

```bash
# 1. 生成新迁移文件
python -m alembic revision --autogenerate -m "描述你的更改"

# 2. 检查生成的迁移脚本 (alembic/versions/xxx_xxx.py)
# 确保 upgrade() 和 downgrade() 正确

# 3. 执行迁移
python -m alembic upgrade head

# 4. 验证
python -m alembic current
```

**回滚迁移：**

```bash
# 回滚到上一个版本
python -m alembic downgrade -1

# 回滚到特定版本
python -m alembic downgrade <revision_id>

# 回滚所有（清空数据）
python -m alembic downgrade base
```

### 3. 本地开发运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## API 接口

### Dify 工具接口 (`/api/v1/dify`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/device/{device_id}` | GET | 查询设备记忆 |
| `/device/{device_id}/update` | POST | 创建/更新设备记忆 |
| `/device/{device_id}/fault` | POST | 添加故障到常见故障 Top3 |
| `/cases/similar` | POST | 查找相似案例 |
| `/solution/save` | POST | 保存解决方案 |
| `/error-code/{error_code}/history` | GET | 获取故障码历史解决方案 |

## 数据库表结构

### device_memory (设备记忆表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| device_id | VARCHAR(50) | 设备唯一编号（唯一索引） |
| model | VARCHAR(100) | 型号，如 IEVC-3.0 |
| device_name | VARCHAR(50) | 设备名称 |
| common_faults | JSON | 历史故障 Top3 (JSON 数组) |
| last_maintenance_date | DATETIME | 上次保养日期 |
| notes | TEXT | 特殊备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### solution_history (历史解决方案表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| error_code | VARCHAR(20) | 故障码（索引） |
| symptoms | TEXT | 故障现象描述 |
| solution | TEXT | 成功解决方案 |
| solved_at | DATETIME | 解决日期（索引） |
| created_at | DATETIME | 创建时间 |

## 部署到腾讯云服务器

### 首次部署

```bash
# 1. 克隆代码
cd /opt
git clone <your-repo-url> dify-bridge
cd dify-bridge

# 2. 配置环境
cp .env.example .env
vi .env

# 3. 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 数据库迁移
python -m alembic upgrade head

# 5. 启动服务（开发环境）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用 Docker Compose（生产环境）
docker-compose up -d
```

### 更新代码

```bash
# 方式一：使用更新脚本
./scripts/update.sh

# 方式二：手动更新
cd /opt/dify-bridge
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head  # 执行新迁移
docker-compose up -d --build
```

### 备份数据

```bash
# 手动备份
./scripts/backup.sh

# 定时备份（crontab）
0 2 * * * /opt/dify-bridge/scripts/backup.sh
```

## 与 Dify 集成

### 1. 配置 Dify 工具

进入 Dify 后台 → 工具 → 自定义工具 → 创建

- **API Base URL**: `http://<服务器 IP>:8000/api/v1/dify`
- **认证**: 无 (或自定义 Header)

### 2. 在 Chatflow 中使用

在 Chatflow 中添加 HTTP 请求节点，调用以下接口：

| 场景 | 接口 |
|------|------|
| 用户提到设备编号 | `GET /device/{device_id}` 查询设备记忆 |
| 更新设备信息 | `POST /device/{device_id}/update` |
| 诊断完成 | `POST /solution/save` 保存解决方案 |
| 查询历史案例 | `POST /cases/similar` 或 `GET /error-code/{error_code}/history` |

### 3. Swagger 文档

访问 `http://localhost:8000/docs` 查看完整 API 文档。

## 开发指南

### 项目结构

```
dify-bridge/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/                 # API 路由层
│   │   ├── __init__.py
│   │   └── dify_tools.py    # Dify 工具接口
│   ├── core/                # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── device_manager.py# 设备管理
│   │   └── case_matcher.py  # 案例匹配
│   ├── db/                  # 数据层
│   │   ├── database.py      # DB 连接
│   │   ├── models.py        # SQLAlchemy 模型
│   │   └── repository.py    # 数据访问
│   └── schemas/             # Pydantic 数据模型
│       ├── __init__.py
│       └── diagnosis.py     # 诊断相关 Schema
├── alembic/                 # 数据库迁移
│   ├── versions/            # 迁移脚本
│   └── env.py               # 迁移环境配置
├── scripts/
│   ├── deploy.sh            # 部署脚本
│   ├── update.sh            # 更新脚本
│   └── backup.sh            # 备份脚本
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### 添加新接口

1. 在对应路由文件中添加 endpoint（如 `app/api/dify_tools.py`）
2. 定义请求/响应 Schema（如 `app/schemas/diagnosis.py`）
3. 实现业务逻辑（如 `app/core/device_manager.py`）

### 数据库迁移流程

1. 修改 `app/db/models.py` 添加/修改模型
2. 生成迁移：`python -m alembic revision --autogenerate -m "描述"`
3. 检查 `alembic/versions/xxx_xxx.py` 确保正确
4. 执行迁移：`python -m alembic upgrade head`

## 故障排查

### 服务无法启动

```bash
# 查看日志
docker-compose logs battery-service

# 进入容器调试
docker exec -it dify-bridge bash
```

### 数据库迁移问题

```bash
# 查看当前迁移版本
python -m alembic current

# 查看迁移历史
python -m alembic history

# 如果迁移失败，清空重建（会丢失数据！）
rm data/battery.db
python -m alembic upgrade head
```

### 端口被占用

```bash
# Windows: 查找占用端口的进程
netstat -ano | findstr :8000

# 杀死进程
taskkill /F /PID <进程 ID>
```

## 与 Dify 集成

### 1. 配置 Dify 工具

进入 Dify 后台 → 工具 → 自定义工具 → 创建

- **API Base URL**: `http://<服务器 IP>:8000/api/v1/dify`
- **认证**: 无 (或自定义 Header)

### 2. 在 Chatflow 中使用

在 Chatflow 中添加 HTTP 请求节点，调用以下接口：

| 场景 | 接口 |
|------|------|
| 用户提到设备编号 | `GET /device/{device_id}` 查询设备记忆 |
| 更新设备信息 | `POST /device/{device_id}/update` |
| 诊断完成 | `POST /solution/save` 保存解决方案 |
| 查询历史案例 | `POST /cases/similar` 或 `GET /error-code/{error_code}/history` |

### 3. Swagger 文档

访问 `http://localhost:8000/docs` 查看完整 API 文档。

## 许可证

MIT
