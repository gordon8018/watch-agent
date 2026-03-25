# Watch Agent Dashboard — 设计文档

**日期**：2026-03-25
**技术栈**：Python + Textual
**状态**：已批准

---

## 概述

一个运行在终端中的实时 dashboard，监控多个并行运行的 Claude Code agent 的工作状态。支持从 tmux 输出、状态文件、进程指标三路数据源聚合信息，2 秒刷新一次，纯只读展示。

---

## 整体架构

```
watch-agent/
├── main.py                  # 入口，启动 Textual App
├── dashboard/
│   ├── app.py               # WatchApp(App) — 主应用
│   ├── widgets/
│   │   ├── summary_bar.py   # 顶部摘要栏（所有 agent 状态一览）
│   │   ├── agent_card.py    # 下方选中 agent 的详细面板
│   │   └── agent_badge.py   # 摘要栏中每个 agent 的小徽章
│   └── styles.tcss          # Textual CSS 样式
├── collector/
│   ├── base.py              # AgentState dataclass（共享数据结构）
│   ├── tmux_collector.py    # 从 tmux 窗格读取输出 + psutil 进程指标
│   ├── file_collector.py    # 读取 agent 写入的状态文件
│   └── manager.py           # CollectorManager：聚合多路数据，定期更新状态
└── config.py                # 配置：刷新频率、日志行数、tmux session 名等
```

**数据流：**

```
tmux pane output ──┐
agent status file ──┤─→ CollectorManager ──→ AgentState[] ──→ Textual App (2s 刷新)
agent metrics    ──┘
```

---

## 数据模型

```python
@dataclass
class AgentState:
    id: str                    # agent 唯一标识（如 tmux 窗格名）
    name: str                  # 显示名称
    status: Literal["running", "idle", "error", "unknown"]
    task: str                  # 当前任务描述
    cwd: str                   # 工作目录
    recent_logs: list[str]     # 最近 100 行日志
    elapsed_seconds: float     # 运行耗时
    cpu_percent: float         # CPU 占用 %
    mem_mb: float              # 内存占用 MB
    completed_tasks: int       # 已完成任务数
    current_command: str       # 当前执行的命令
    last_updated: datetime     # 最后更新时间
```

**状态文件格式**（agent 写入 `/tmp/agent-{id}.json`）：

```json
{
  "name": "feature-agent",
  "status": "running",
  "task": "实现用户登录模块",
  "cwd": "/home/user/project",
  "current_command": "pytest tests/",
  "completed_tasks": 3
}
```

tmux 输出和进程指标（CPU/内存）由采集层自动采集，无需 agent 手动写入。

---

## UI 布局

```
┌─────────────────────────────────────────────────────────────┐
│  Watch Agent Dashboard          [总计: 4]  [运行: 3]  [错误: 1] │  ← 标题栏
├──────────┬──────────┬──────────┬─────────────────────────────┤
│ ● agent1 │ ● agent2 │ ✗ agent3 │ ○ agent4                    │  ← 摘要栏
│ 运行中    │ 运行中    │ 出错     │ 空闲                        │
│ 任务: ... │ 任务: ... │ 任务: .. │ 任务: ...                   │
├─────────────────────────────────────────────────────────────┤
│  [详细面板 — 自动展示第一个 running agent，或最近更新的 agent]   │
│                                                              │
│  名称: agent1        状态: ● 运行中      耗时: 00:12:34       │
│  目录: ~/project     命令: pytest ...   已完成: 5 tasks       │
│  CPU: 23%  内存: 128MB                                       │
│  ─────────────────────────────────────────────────────────  │
│  [日志 · 最近 100 行]                                         │
│  > Running test suite...                                     │
│  > test_login.py PASSED                                      │
│  > ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

**布局规则：**
- 摘要栏高度固定（约 4 行），agent 数量超过一行时横向滚动
- 详细面板占剩余所有高度，日志区域可垂直滚动
- agent 多于 8 个时，摘要徽章自动缩小（只显示状态图标 + 名称）
- 状态颜色：`running` 绿色，`idle` 灰色，`error` 红色，`unknown` 黄色

---

## 数据采集策略

### 三路数据源

**1. tmux 输出采集**

```bash
tmux capture-pane -p -t <session>:<window>.<pane> -S -100
```

每 2 秒执行，捕获最近 100 行输出作为 `recent_logs`。

**2. 状态文件采集**

监听 `/tmp/agent-*.json`，每次刷新读取所有匹配文件。文件不存在则 status = `unknown`。

**3. 进程指标采集（psutil）**

通过 tmux 获取窗格 shell PID，使用 `psutil.Process(pid).children(recursive=True)` 汇总所有子进程的 CPU + 内存，避免只采集 shell 本身的指标。CPU 使用非阻塞 `cpu_percent(interval=None)`。

### 合并规则

- 状态文件字段优先（agent 主动上报更准确）
- tmux 输出补充 `recent_logs`
- psutil 补充 `cpu_percent` / `mem_mb`
- 任意一路失败不影响其他，静默降级（对应字段显示 `N/A`）
- 每个字段保留来源时间戳，`last_updated` 取三路中最新的一个

---

## 错误处理与边界情况

| 场景 | 处理方式 |
|------|----------|
| tmux session 不存在 | status = `unknown`，日志显示 "tmux session not found" |
| 状态文件损坏/半写 | 跳过本轮，保留上次有效数据，捕获 `JSONDecodeError` |
| agent 进程已退出 | psutil 抛 `NoSuchProcess`，CPU/内存显示 `N/A` |
| agent 新增（文件出现） | 下次轮询自动发现，动态加入摘要栏 |
| agent 消失（文件删除） | 保留卡片 30 秒后淡出，避免闪烁 |
| 终端窗口缩小 | Textual 响应式布局自动适配，摘要徽章缩略显示 |

---

## 配置

```python
# config.py
REFRESH_INTERVAL = 2.0        # 秒
LOG_LINES = 100               # 保留日志行数
TMUX_SESSION = "agents"       # tmux session 名
STATUS_DIR = "/tmp"           # 状态文件目录
AGENT_LINGER_SECONDS = 30     # agent 消失后保留卡片的秒数
```

**启动方式：**

```bash
python main.py
python main.py --session my-session --status-dir /var/run/agents
```

---

## 依赖

```
textual>=0.50.0
psutil>=5.9.0
```
