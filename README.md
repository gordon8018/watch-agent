# Watch Agent Dashboard

终端实时 Dashboard，用于监控多个并行运行的 Claude Code agent 的工作状态、日志和进程指标。

## 功能

- **实时状态监控**：每 2 秒自动刷新，展示所有 agent 的运行状态
- **混合布局**：顶部摘要栏一览所有 agent，底部自动展示最活跃 agent 的详细信息
- **三路数据采集**：tmux 终端输出、agent 状态文件、psutil 进程指标
- **容错设计**：任意一路数据源失败不影响其他；状态文件损坏时自动保留上次有效数据；agent 消失后保留 30 秒避免界面闪烁

## 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  Watch Agent Dashboard    [总计: 4]  [运行: 3]  [错误: 1]    │
├──────────┬──────────┬──────────┬──────────────────────────── ┤
│ ● agent1 │ ● agent2 │ ✗ agent3 │ ○ agent4                    │
│ 运行中    │ 运行中    │ 出错     │ 空闲                        │
│ 实现登录… │ 写测试…   │ 编译错…  │ 等待任务                    │
├─────────────────────────────────────────────────────────────┤
│  名称: agent1    状态: ● 运行中    耗时: 00:12:34              │
│  目录: ~/project 命令: pytest     已完成: 5 tasks             │
│  CPU: 23%  内存: 128MB                                       │
│  ─────────────────────────────────────────────────────────  │
│  > Running test suite...                                     │
│  > test_login.py PASSED                                      │
│  > test_auth.py PASSED                                       │
│  > ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

状态图标：`●` 运行中（绿）`○` 空闲（灰）`✗` 出错（红）`?` 未知（黄）

## 安装

**要求：** Python 3.11+，tmux

```bash
git clone https://github.com/gordon8018/watch-agent.git
cd watch-agent
pip install -e .
```

## 使用

### 启动 Dashboard

```bash
python main.py
```

默认监控名为 `agents` 的 tmux session，从 `/tmp` 读取状态文件。

**自定义参数：**

```bash
python main.py --session my-session --status-dir /var/run/agents
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--session` | `agents` | 要监控的 tmux session 名称 |
| `--status-dir` | `/tmp` | agent 状态文件目录 |

按 `q` 退出。

### Agent 接入

每个 agent 在任务切换时调用写入脚本更新状态：

```bash
python agent_status_writer.py \
  --id agent1 \
  --status running \
  --task "实现用户登录模块" \
  --command "pytest tests/" \
  --completed 3
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id` | ✓ | agent 唯一标识，需与 tmux 窗格标题一致 |
| `--status` | | `running` / `idle` / `error`（默认 `running`） |
| `--task` | | 当前任务描述 |
| `--command` | | 当前执行的命令 |
| `--completed` | | 已完成任务数（整数） |
| `--cwd` | | 工作目录（默认当前目录） |
| `--status-dir` | | 状态文件写入目录（默认 `/tmp`） |

状态文件写入 `/tmp/agent-{id}.json`，采用原子写入（临时文件 + rename），避免 Dashboard 读取到半写文件。

### tmux 配置建议

将 tmux 窗格标题设为 agent id，以便 Dashboard 自动关联日志：

```bash
# 启动 agent 时设置窗格标题
tmux new-window -t agents -n agent1
tmux select-pane -t agents:agent1 -T agent1
```

## 数据采集机制

Dashboard 从三路数据源聚合信息：

| 数据源 | 采集内容 | 失败处理 |
|--------|----------|----------|
| **状态文件** `/tmp/agent-*.json` | 任务名、状态、工作目录、命令、完成数 | 保留上次有效数据 |
| **tmux 输出** | 最近 100 行终端日志 | 返回空日志 |
| **psutil 进程指标** | CPU%、内存 MB（含所有子进程） | 显示 N/A |

## 项目结构

```
watch-agent/
├── main.py                   # 入口
├── config.py                 # 配置常量（刷新间隔、日志行数等）
├── agent_status_writer.py    # Agent 状态写入脚本
├── collector/
│   ├── base.py               # AgentState 数据模型
│   ├── file_collector.py     # 状态文件采集
│   ├── tmux_collector.py     # tmux 日志 + psutil 指标
│   └── manager.py            # 三路数据聚合
├── dashboard/
│   ├── app.py                # Textual 主应用
│   ├── styles.tcss           # 布局样式
│   └── widgets/
│       ├── agent_badge.py    # 摘要栏徽章组件
│       ├── agent_card.py     # 详细信息面板
│       └── summary_bar.py    # 顶部摘要栏
└── tests/                    # 22 个单元测试
```

## 配置

编辑 `config.py` 调整默认值：

```python
REFRESH_INTERVAL = 2.0       # 刷新间隔（秒）
LOG_LINES = 100              # 保留日志行数
TMUX_SESSION = "agents"      # 默认 tmux session 名
STATUS_DIR = "/tmp"          # 默认状态文件目录
AGENT_LINGER_SECONDS = 30    # agent 消失后保留卡片的秒数
```

## 开发

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
