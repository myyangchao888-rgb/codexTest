# 报警主机服务端（TCP Server + FastAPI + MySQL）

本项目实现：
1) **TCP 服务器端**：监听端口等待报警主机连接；接收主机上报的 `+DFAI` / `+DFAS` / `+CWMSG` 等数据；解析并写入 MySQL。  
2) **HTTP 接口（FastAPI）**：提供查询防区信息、防区状态、主机事件的 REST API。  
3) **MySQL 持久化**：自动建表，支持 upsert。

...

## 目录结构
alarm_server/
├─ main.py # 入口：启动 FastAPI & TCP 服务器线程
├─ tcp_server.py # TCP 监听与每连接处理、按行解析
├─ alarm_parser.py # 解析 +DFAI/+DFAS/+CWMSG
├─ db.py # MySQL 读写与建表
├─ api.py # FastAPI 路由
├─ config.py # 读取 .env 配置
├─ requirements.txt
├─ .env.example
└─ README.md