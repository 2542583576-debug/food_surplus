# 惜食余量魔法袋

找实习期间做的一个小项目。想法挺朴素的：面包店、便利店每天打烊前总有些还没坏、但当天卖不掉的东西，直接扔了可惜。我就做了个网页，让商家把这些食物打包成"魔法袋"低价挂出来，住附近的人按时段去自提。

后端用 FastAPI + MySQL，前端 Vue 3。顾客下单会拿到一个 6 位核销码，到店给商家核销，核销完自动往"环保账本"里记一条减碳数据。商家那边能新建魔法袋、看门店订单、做核销。

这个 README 主要是写给你看的，方便你自己动手跑起来验证。想先了解做了什么就看"功能"，想直接跑就看"怎么跑起来"，想看我当时踩的坑就看"我卡最久的一个问题"。

## 功能

顾客登录后在魔法袋广场看到附近门店挂出来的袋子，挑一个预订，下单拿到 6 位核销码；到店把码给商家，商家核销，这次领取就记进你的环保账本里——每个魔法袋按 0.5kg 食物、1.2kg 碳估算。核销完还会有一条站内通知提醒你。

商家端就是登录、新建和编辑魔法袋（可以传封面图）、查看并核销门店订单、看自提门店信息（地址可复制、可跳转导航）这几件事。

## 我卡最久的一个问题

下单这块我调试了挺久。魔法袋是按门店挂出来的，但订单表里得记"哪个商家来核销这个单"。一开始我直接把魔法袋上的 merchant_id 写到订单里，结果发现是空的——顾客这边下单成功了，商家那边的订单列表却根本看不到这个单，核销也就没法做。

后来发现应该从魔法袋所属的 store_id 反查这家门店的管理员（role=1、is_active 的），再把管理员 ID 写进订单。改完之后下单 → 商家可见 → 核销 → 碳账本这条线才算真的通了。代码在 `backend/app/services/order_service.py`，我留了一行注释标着这是闭环的关键点。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3、Vite、Element Plus、Pinia、Axios |
| 后端 | FastAPI、SQLAlchemy、Pydantic、JWT、Uvicorn |
| 存储 | MySQL 8.0、Redis（可选，连不上会自动降级成内存） |
| 部署 | Docker Compose、Nginx、多阶段构建 |

## 怎么跑起来

### 方式 A：本机启动（不用 Docker，Windows 上推荐这个）

前置条件：装好 Python 3.10+ 和 Node.js 18+，MySQL 已经在跑，并把连接信息填进 `backend/.env`（可以照着 `backend/.env.example` 改）。

然后双击项目根目录的 `start-local.bat`。这个脚本会依次清理占着端口的旧进程、建虚拟环境、装依赖、初始化数据库、启动前后端，等两边都就绪了自动打开浏览器（前端和后端接口文档两个标签页）。

启动后访问：
- 前端页面：http://127.0.0.1:5173
- 接口文档：http://127.0.0.1:8000/docs

要停服务就双击 `stop-local.bat`，它按端口把前后端进程关掉。

顺带说一句，启动和停止脚本我是用纯 ASCII + CRLF 编码写的，因为之前中文提示在 cmd 里按 GBK 解读，双击就一闪而过，排查了好一会儿才定位到是编码问题。

<details>
<summary>手动启动（脚本出问题时可以这么试）</summary>

```bat
cd /d D:\food_surplus\backend
set PYTHONPATH=
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
```bat
cd /d D:\food_surplus\frontend
npm run dev -- --host 127.0.0.1
```
</details>

### 方式 B：Docker Compose

```bash
# 1. 生成配置文件，把里面的 SECRET_KEY、MYSQL_PASSWORD、CORS_ORIGINS 改成你自己的
cp backend/.env.example .env

# 2. 启动全部服务（MySQL + Redis + 后端 + 前端）
docker compose up -d --build
```

然后访问 `http://服务器IP`（前端走 80 端口），接口文档在 `http://服务器IP:8000/docs`。

## 演示的时候怎么操作

建议用无痕窗口打开前端，先在 Swagger（http://127.0.0.1:8000/docs）把后端过一遍，再切到前端演示界面。

| 步骤 | 操作 | 期望结果 / 讲解点 |
|---|---|---|
| 1 | `GET /health`、`GET /ready` | 200，两个健康检查是分层的 |
| 2 | `POST /api/v1/auth/login` 填 `admin/admin123` | 200，JWT 里带了 ID、角色、门店 |
| 3 | 右上角 Authorize，在 HTTPBearer 栏粘贴 token | 带锁的接口解锁了（注意别用 OAuth2 那个弹窗，会报 500） |
| 4 | `POST /api/v1/orders/create` | 201，把响应里的 `id`（数字）和 `verify_code`（6 位码）记下来 |
| 5 | `POST /api/v1/merchant/orders/{id}/verify` | 200，`status` 从 1 变成 2；这里可以讲上面那个 merchant_id 的问题 |
| 6 | `GET /api/carbon/platform/summary` | 200，`total_order_count` +1，一次核销串起了三个模块 |

演示账号：顾客 `user / user123`，商家 `admin / admin123`，登录页有一键填入。

两个容易踩的坑：下单请求体不要用 Swagger 默认的 `"order_no":"string"`，会撞唯一约束报 500，只传 `bag_id`、`customer_phone`、`customer_name`、`pay_method` 就行；另外订单 15 分钟没核销会超时，超时了就重新下一单再核销。

前端可以这么走一遍：顾客登录 → 魔法袋广场预订拿核销码 → 退出换商家登录 → 门店订单核销 → 回到顾客看环保账本和通知铃铛。

## 测试怎么跑的

在 backend 目录下执行：

```bash
# 后端接口冒烟测试（16 项）
cd backend && .venv\Scripts\python.exe tests\smoke_test.py

# 端到端闭环测试（15 项）：下单→商家可见→核销→碳账本→通知→门店
.venv\Scripts\python.exe tests\e2e_test.py

# 前端构建
cd frontend && npm run build
```

两组测试我都跑过，能过：冒烟 16 项、端到端 15 项，前端构建也过了。端到端那条是从下单一路走到商家可见、核销、碳账本、通知、门店的，能把前面说的主线整个串一遍。

## 目录结构

```
food_surplus/
├── start-local.bat / stop-local.bat   # 本机一键启停
├── docker-compose.yml                 # Docker 编排
├── backend/
│   ├── app/
│   │   ├── api/            # 接口路由（含 v1 盲盒体系 + 魔法袋兼容层）
│   │   ├── core/           # 配置、安全、依赖注入
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 校验模型
│   │   ├── services/       # 业务逻辑（order_service.py 含闭环修复）
│   │   └── main.py         # 应用入口、健康检查、日志中间件
│   ├── scripts/init_db.py  # 幂等初始化
│   ├── tests/              # smoke_test.py / e2e_test.py
│   └── .env.example        # 环境变量示例（真实 .env 不入库）
└── frontend/
    └── src/
        ├── api/            # 请求封装
        ├── views/          # 页面（Bags/MyOrders/Carbon/Stores/...）
        ├── layout/         # 顶部导航
        └── styles/         # 环保主题样式
```

## 还有哪些没做完

先说实话："在线支付"目前只是个状态标记，没有接微信或者支付宝，不会真的扣钱。这块我没做完，说出来免得你误会。

真要部署到服务器的话还有几件事得处理：把 `.env` 里的 SECRET_KEY 换成随机长字符串，改掉 MYSQL_PASSWORD 和种子数据里的默认账号密码；CORS_ORIGINS 只留真实的前端域名；DEBUG 关掉。MySQL 和上传的 `upload_data` 目录要做定时备份，不然数据丢了没法找回来。如果开多个实例，得启用 Redis 并让几个实例共用同一个 SECRET_KEY，否则登录状态对不上。
