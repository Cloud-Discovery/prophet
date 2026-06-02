<p align="center"><a href="https://oneprocloud.com"><img src="./docs/images/prophet-logo.png" alt="Prophet" width="300" /></a></p>
<h3 align="center">资源自动采集分析工具集，云迁移/云灾备必备的调研工具</h3>

<p align="center">
  <a href="https://shields.io/github/downloads/Cloud-Discovery/prophet/total"><img src="https://shields.io/github/downloads/Cloud-Discovery/prophet/total" alt=" release"></a>
  <a href="https://github.com/Cloud-Discovery/prophet"><img src="https://img.shields.io/github/stars/Cloud-Discovery/prophet?color=%231890FF&style=flat-square" alt="Stars"></a>
</p>

---

- [ENGLISH](./docs/README_EN.md)

## 目录

- [项目说明](#项目说明)
- [主要功能](#主要功能)
- [安装说明](#安装说明)
  - [Docker Compose 部署（推荐）](#docker-compose-部署推荐)
  - [源码安装](#源码安装)
- [使用说明](#使用说明)
  - [Web 界面使用](#web-界面使用)
  - [命令行工具使用](#命令行工具使用)
- [项目结构](#项目结构)
- [如何贡献](#如何贡献)
- [安全政策](#安全政策)
- [贡献者](#贡献者)
- [协议说明](#协议说明)

## 项目说明

Prophet 是一个自动化资源采集、分析和管理的工具集，专为云迁移与云灾备前期技术调研设计。项目提供现代化的 Web 界面和强大的命令行工具，支持对物理机、VMware 环境的全面采集和分析，帮助用户快速了解源端基础设施状况，确保迁移和灾备方案的可行性。

### 核心价值

- **自动化采集**：通过多种协议（nmap、Ansible、WMI、VMware API）自动采集主机详细信息
- **可视化分析**：提供直观的 Web 界面，支持应用拓扑可视化和管理
- **数据脱敏**：自动移除敏感信息，确保数据安全
- **容器化部署**：一键部署，开箱即用，减少环境依赖

### 应用场景

- 云迁移前期调研：全面了解源端基础设施，制定迁移方案
- 云灾备规划：评估灾备可行性，预测数据传输时间
- 基础设施管理：统一管理主机、应用和依赖关系
- 技术文档生成：自动生成技术调研报告

## 主要功能

### Web 界面功能

- **主机管理**：查看、搜索、管理已采集的主机信息
- **应用管理**：创建应用，通过可视化画布梳理业务拓扑和主机依赖关系
- **扫描任务**：创建和管理网络扫描任务，批量发现主机
- **虚拟化平台**：管理 VMware 平台和虚拟机信息
- **标签管理**：为主机添加标签，便于分类管理
- **数据导入导出**：支持批量导入主机数据，导出采集结果

### 命令行功能

- **网络扫描**：通过 nmap 扫描网段内存活的主机
- **详细信息采集**：
  - 通过 VMware API 采集虚拟机和 ESXi 主机信息
  - 通过 Ansible 采集 Linux 主机详细信息
  - 通过 Windows WMI 接口采集 Windows 主机信息
- **数据分析**：对采集结果进行分析，生成技术调研报告
- **数据打包**：将采集结果打包压缩，自动脱敏处理

## 安装说明

### Docker Compose 部署（推荐）

推荐使用 Docker Compose 方式部署，简单快速，无需配置复杂的环境依赖。

#### 前提条件

- Docker >= 20.10
- Docker Compose >= 2.0

#### 快速开始

1. **克隆项目**

```bash
git clone https://github.com/Cloud-Discovery/prophet
cd prophet
```

2. **配置环境变量（可选）**

复制环境变量示例文件并修改：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置必要的密钥：

```bash
# 必须修改的安全密钥
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

3. **启动服务**

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

4. **访问应用**

- **Web 界面**：http://localhost
- **API 健康检查**：http://localhost:5000/api/v1/health

#### 服务说明

- **backend**：后端服务容器（端口 5000）
  - Flask REST API
  - Celery Worker（异步任务处理）
  - Redis（消息队列和缓存）
- **frontend**：前端服务容器（端口 80）
  - Nginx 静态文件服务
  - 自动代理 API 请求

#### 数据持久化

以下目录通过 volume 挂载，数据会持久化：

- `./data`：数据库文件
- `./logs`：日志文件
- `./uploads`：上传文件

#### 常用命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看后端日志
docker-compose logs -f backend

# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

更多详细信息请参考 [Docker 部署文档](./docker/README.md)。

### 源码安装

#### 前提条件

- **Python 环境**：Python 3.8 以上版本
- **系统依赖**（RHEL & CentOS）：
  ```bash
  yum install -y epel-release
  yum install -y nmap sshpass python3 python3-pip python3-devel
  ```

#### 安装步骤

```bash
# 克隆项目
git clone https://github.com/Cloud-Discovery/prophet
cd prophet

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -U pip
pip install -r requirements.txt
pip install .

# 安装 Windows WMI 模块（仅 RHEL/CentOS）
yum install -y ./tools/wmi-1.3.14-4.el7.art.x86_64.rpm

# 初始化数据库
python -c "from app import create_app; from db import init_db; app = create_app(); init_db(app)"

# 启动 Web 服务
python app.py

# 启动 Celery Worker（另开终端）
celery -A celery_worker.celery worker --loglevel=info
```

## 使用说明

### Web 界面使用

#### 1. 登录系统

首次使用需要注册账号，注册后使用账号密码登录。

#### 2. 主机管理

- **查看主机列表**：在"主机"页面查看所有已采集的主机
- **搜索和筛选**：支持按 IP、主机名、操作系统类型等条件搜索
- **查看详情**：点击主机查看详细信息（CPU、内存、磁盘、网络等）
- **添加标签**：为主机添加标签，便于分类管理

#### 3. 应用管理

应用管理提供可视化画布，用于梳理业务中主机之间的依赖关系。

**创建应用**：

1. 点击"创建应用"按钮
2. 输入应用名称和描述
3. 进入应用详情页面

**可视化画布操作**：

1. **资源面板**（左侧）
   - 搜索并添加未加入应用的主机
   - 使用模板节点（网络、存储、服务等）补充业务架构
2. **画布操作**（中间）
   - 拖拽节点移动位置
   - 连接两个节点创建关系
   - 使用工具栏调整布局（网格、横向、纵向）
   - 缩放和视图复位
3. **属性面板**（右侧）
   - 选中节点或连线查看/编辑属性
   - 修改关系类型和描述
   - 重新绑定主机

**线条样式设置**：

- 点击画布上的连线，在顶部工具栏点击"线条样式"
- 可设置线条类型（折线、直线、贝塞尔曲线）
- 可设置线条样式（实线、虚线、点线）
- 可设置线条宽度和颜色

#### 4. 扫描任务

- **创建扫描任务**：在"扫描"页面创建网络扫描任务
- **查看任务状态**：实时查看扫描进度和结果
- **下载扫描结果**：扫描完成后可下载 CSV 格式的结果文件

#### 5. 数据导入

- 在"集合"页面可以批量导入主机数据
- 支持 CSV 和 YAML 格式

## 项目结构

详细的项目结构说明请参考 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)。

主要目录：

- `api/` - Flask API 端点
- `frontend/` - Vue.js 前端应用
- `models/` - 数据库模型
- `prophet/` - 核心库（采集、解析、扫描等）
- `services/` - 业务逻辑服务
- `tasks/` - Celery 异步任务
- `docker/` - Docker 部署配置

## 如何贡献

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详细的贡献指南。

## 安全政策

如果您发现安全漏洞，请查看 [SECURITY.md](./SECURITY.md) 了解如何报告。

## 协议说明

本项目采用[木兰公共许可证，第 2 版](http://license.coscl.org.cn/MulanPubL-2.0)

## 贡献者

感谢以下贡献者为本项目做出的贡献

<a href="https://github.com/Cloud-Discovery/prophet/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Cloud-Discovery/prophet" />
</a>
