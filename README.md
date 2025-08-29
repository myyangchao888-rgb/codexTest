# 报警主机服务端（TCP Server + FastAPI）

本项目实现：
1) **TCP 服务器端**：监听端口等待报警主机连接；接收主机上报的 `+DFAI` / `+DFAS` / `+CWMSG` 等数据；解析后存入内存结构。设备连接后服务会依次发送 `ATI`、`AT+AUTH=`、`AT+CWMSG=SET,0,0,60,5,1,1`、`AT+DFAI?`、`AT+DFAI=`、`AT+DFAS?`、`AT+DFAS=` 等指令获取主机信息、用户代码、防区列表及防区状态，并设置设备自动上报消息。收到 `+CWMSG` 后会立即回复 `AT+CWMSG=<消息ID>` 确认，同时定期发送 `AT+CWMSG=`（默认 200 秒，可通过 `CWMSG_KEEPALIVE_SEC` 配置）保持连接活动。
2) **HTTP 接口（FastAPI）**：实时返回已连接设备列表、每台设备的防区信息、防区状态及最近事件，并可对单个防区或整个主机进行布防/撤防控制。

服务使用线程安全的内存数据结构保存信息，不依赖任何数据库。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env` 并按需调整配置
3. 运行 `python main.py` 启动 TCP 监听和 HTTP 接口

TCP 监听端口由 `.env` 中的配置决定，HTTP API 默认在 <http://localhost:8000> 提供访问。

### 调试

服务默认会以 INFO 级别打印每条设备上报的数据，便于观察实时情况。如需查看更详细的解析结果，可在 `.env` 中设置 `LOG_LEVEL=DEBUG`，届时控制台会输出每条报文及其解析详情，便于排查 HTTP 接口无数据的原因。

## HTTP API 示例

- `GET /devices` 获取当前所有已连接的设备（含 IP 与端口）
- `GET /devices/{id}/zones` 获取指定设备的防区信息
- `GET /devices/{id}/zone-status` 获取指定设备的防区状态
- `GET /devices/{id}/events` 查看指定设备的最近事件
- `GET /devices/{id}/info` 获取设备的主机信息（ID、OEM、MODEL、VERSION 等）
- `POST /devices/{id}/zones/{zid}/arm` 对指定防区布防
- `POST /devices/{id}/zones/{zid}/disarm` 对指定防区撤防
- `POST /devices/{id}/arm` 主机布防（语音提示）
- `POST /devices/{id}/disarm` 主机撤防（语音提示）

### 防区字段说明

`GET /devices/{id}/zones` 返回的每条防区记录包含以下字段：

| 字段 | 说明 |
| --- | --- |
| id | 防区编号 |
| io | 防区输入输出类型：I 表示输入型，O 表示输出型（警号驱动） |
| io_desc | `io` 的中文描述 |
| ena | 防区使能状态：1 表示正常，0 表示防区被禁止 |
| ena_desc | `ena` 的中文描述 |
| type | 防区类型代码 |
| type_desc | 防区类型说明（见下表） |
| code | 警情代码 |
| code_desc | 警情代码说明（见下表） |
| code_type | 警情类别 |
| team | 分组 |
| name | 名称 |

防区类型(`type`) 可选值及含义如下：

| 类型 | 说明 |
| --- | --- |
| NORMAL | 普通 |
| DELAY | 延时 |
| A24H | 有声24小时 |
| S24H | 无声24小时 |
| INSIDE | 内部 |
| PERM | 周界 |
| EMERG | 紧急 |
| FIRE | 火警 |
| GAS | 燃气 |
| MEDICAL | 医疗 |
| BA24H | 24小时盗警 |
| DOORBELL | 门铃 |
| TAMPER | 防拆 |
| REMOTER | 遥控器 |
| KEYPAD | 键盘按钮 |

### 防区状态字段说明

`GET /devices/{id}/zone-status` 返回的每条记录包含：

| 字段 | 说明 |
| --- | --- |
| id | 防区编号 |
| arm | 布防标志：1 表示防区布防，0 表示撤防 |
| arm_desc | `arm` 的中文描述 |
| bypass | 旁路标志：1 表示防区被旁路，0 表示正常 |
| bypass_desc | `bypass` 的中文描述 |
| sta | 防区触发状态代码 |
| sta_desc | `sta` 的中文描述（见下表） |
| acnt | 报警次数 |

防区触发状态(`sta`) 可选值及含义如下：

| 状态 | 说明 |
| --- | --- |
| READY | 防区正常状态 |
| TRIG | 防区触发状态 |
| ALARM | 防区报警状态 |

### 事件消息类型

`GET /devices/{id}/events` 返回的每条事件记录包含字段：`ts`（时间戳）、`type`（消息类型代码）、`type_desc`（类型说明）、`params`（参数字典）以及 `raw`（原始报文）。

常见消息类型及参数说明如下：

| 类型 | 参数 | 说明 |
| --- | --- | --- |
| DFA_ALARM | zone, code | 防区报警 |
| DFA_RESTORE | zone, code | 防区报警恢复 |
| USER_SETARM | p1, p2, p3, p4, p5 | 用户布防 |
| USER_DISARM | p1, p2, p3, p4, p5 | 用户撤防 |
| DEV_ONLINE | dev | 子设备在线 |
| DEV_OFFLINE | dev | 子设备掉线 |
| DFA_BYPASS | dev, zone, user | 防区旁路 |
| DFA_FORCE | dev, zone, user | 防区异常 |
| POWERON | - | 设备启动 |
| STAT_AC | state, source, voltage | 交流供电状态（state:0断开1正常，source:1交流/0直流） |
| STAT_BAT | status, voltage | 电池状态（status:0丢失1连接2欠压3恢复） |
| STAT_PSTN | status | 电话线状态（0无连接1正常） |
| USER_LOGIN | login, dev, user | 用户登陆（login:1登陆0注销） |
| SETTM | - | 配置修改 |
| ZONE_TAMPER | zone, trig | 防区拆动（trig:1触发0恢复） |
| ZONE_LOWBAT | zone, low | 电池低压（low:1低压0恢复） |
| ZONE_ACLOSS | zone, loss | 防区断电（loss:1断电0恢复） |
| ZONE_FAULT | zone, fault | 防区故障（fault:1故障0恢复） |
| SYS_RESTART | - | 报警主机重启 |
| SYS_HALT | - | 报警主机关闭 |
| SYS_TAMPER | - | 报警主机拆动 |
| COMMON | p1, p2 | 未定义消息 |

### 警情代码列表

| 类型 | 代码 | 警情 |
| --- | --- | --- |
| 医疗 | 100 | 医疗求助 |
| 医疗 | 101 | 个人紧急按钮（医疗） |
| 火警 | 110 | 火警 |
| 火警 | 111 | 烟感 |
| 火警 | 112 | 燃烧 |
| 火警 | 113 | 水满 |
| 火警 | 114 | 高温 |
| 火警 | 115 | 警报箱 |
| 火警 | 116 | 管道 |
| 火警 | 117 | 火焰 |
| 火警 | 118 | 危险 |
| 紧急 | 120 | 紧急按钮 |
| 紧急 | 121 | 挟持 |
| 紧急 | 122 | 24小时无声 |
| 紧急 | 123 | 24小时有声 |
| 紧急 | 124 | 挟持进入允许 |
| 紧急 | 125 | 挟持外出允许 |
| 盗警 | 130 | 盗警 |
| 盗警 | 131 | 周界 |
| 盗警 | 132 | 内部 |
| 盗警 | 133 | 24小时（盗窃） |
| 盗警 | 134 | 出入口 |
| 盗警 | 135 | 日夜 |
| 盗警 | 137 | 防拆 |
| 盗警 | 138 | 接近 |
| 盗警 | 139 | 交叉防区报警 |
| 通用警情 | 140 | 通用报警 |
| 通用警情 | 142 | 总线故障 |
| 通用警情 | 143 | 扩充设备故障 |
| 通用警情 | 144 | 探测器防拆 |
| 通用警情 | 145 | 扩充设备防拆 |
| 通用警情 | 146 | 无声盗警 |
| 24小时非盗警 | 150 | 24小时非盗警 |
| 24小时非盗警 | 151 | 燃气 |
| 24小时非盗警 | 152 | 冷却 |
| 24小时非盗警 | 153 | 失温 |
| 24小时非盗警 | 154 | 漏水 |
| 24小时非盗警 | 155 | 箔片破坏 |
| 24小时非盗警 | 156 | 日间故障 |
| 24小时非盗警 | 157 | 气体不足 |
| 24小时非盗警 | 158 | 高温 |
| 24小时非盗警 | 159 | 低温 |
| 24小时非盗警 | 161 | 气流损失 |
| 24小时非盗警 | 162 | 一氧化碳 |
| 24小时非盗警 | 163 | 水位低 |
| 消防 | 200 | 火警监视 |
| 消防 | 201 | 水压低 |
| 消防 | 202 | 二氧化碳压力低 |
| 消防 | 203 | 电子闸门传感 |
| 消防 | 204 | 水位低 |
| 消防 | 205 | 水泵开启 |
| 消防 | 206 | 水泵故障 |

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
