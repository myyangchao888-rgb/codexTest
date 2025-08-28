# 报警主机服务端（TCP Server + FastAPI）

本项目实现：
1) **TCP 服务器端**：监听端口等待报警主机连接；接收主机上报的 `+DFAI` / `+DFAS` / `+CWMSG` 等数据；解析后存入内存结构。
   设备连接后服务会首先发送 `ATI` 指令以触发主机上报。
2) **HTTP 接口（FastAPI）**：实时返回最新的防区信息、防区状态、主机事件，并可对单个防区进行布防/撤防控制。
服务使用线程安全的内存数据结构保存信息，不依赖任何数据库。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env` 并按需调整配置
3. 运行 `python main.py` 启动 TCP 监听和 HTTP 接口

TCP 监听端口由 `.env` 中的配置决定，HTTP API 默认在 <http://localhost:8000> 提供访问。

### 调试

服务默认会以 INFO 级别打印每条设备上报的数据，便于观察实时情况。
如需查看更详细的解析结果，可在 `.env` 中设置 `LOG_LEVEL=DEBUG`，届时控制台会输出每条报文及其解析详情，便于排查 HTTP 接口无数据的原因。

## HTTP API 示例

- `GET /zones` 获取所有防区
- `GET /zone-status` 获取防区状态
- `GET /events` 最近事件
- `POST /zones/{id}/arm` 对指定防区布防
- `POST /zones/{id}/disarm` 对指定防区撤防

## 目录结构
.
├─ app/
│  ├─ __init__.py
│  ├─ alarm_parser.py # 解析 +DFAI/+DFAS/+CWMSG
│  ├─ api.py # FastAPI 路由
│  ├─ config.py # 读取 .env 配置
│  ├─ data_store.py # 内存数据存取
│  └─ tcp_server.py # TCP 监听与每连接处理、按行解析
├─ main.py # 入口：启动 FastAPI & TCP 服务器线程
├─ requirements.txt
├─ .env.example
└─ README.md
