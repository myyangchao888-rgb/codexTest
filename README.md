# 报警主机服务端（TCP Server + FastAPI）

本项目实现：
1) **TCP 服务器端**：监听端口等待报警主机连接；接收主机上报的 `+DFAI` / `+DFAS` / `+CWMSG` 等数据；解析后存入内存结构。设备连接后服务会依次发送 `ATI`、`AT+AUTH=`、`AT+CWMSG=SET,0,0,60,5,1,1`、`AT+DFAI?`、`AT+DFAI=`、`AT+DFAS?`、`AT+DFAS=` 等指令获取主机信息、用户代码、防区列表及防区状态，并设置设备自动上报消息。收到 `+CWMSG` 后会立即回复 `AT+CWMSG=<消息ID>` 确认，同时定期发送 `AT+CWMSG=`（默认 200 秒，可通过 `CWMSG_KEEPALIVE_SEC` 配置）保持连接活动。
2) **HTTP 接口（FastAPI）**：实时返回最新的防区信息、防区状态、主机事件，并可对单个防区或整个主机进行布防/撤防控制。

服务使用线程安全的内存数据结构保存信息，不依赖任何数据库。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env` 并按需调整配置
3. 运行 `python main.py` 启动 TCP 监听和 HTTP 接口

TCP 监听端口由 `.env` 中的配置决定，HTTP API 默认在 <http://localhost:8000> 提供访问。

### 调试

服务默认会以 INFO 级别打印每条设备上报的数据，便于观察实时情况。如需查看更详细的解析结果，可在 `.env` 中设置 `LOG_LEVEL=DEBUG`，届时控制台会输出每条报文及其解析详情，便于排查 HTTP 接口无数据的原因。

## HTTP API 示例

- `GET /zones` 获取所有防区
- `GET /zone-status` 获取防区状态
- `GET /events` 最近事件
- `GET /host/info` 主机基本信息（ID、OEM、MODEL、VERSION）
- `POST /zones/{id}/arm` 对指定防区布防
- `POST /zones/{id}/disarm` 对指定防区撤防
- `POST /host/arm` 主机布防（语音提示）
- `POST /host/disarm` 主机撤防（语音提示）

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
