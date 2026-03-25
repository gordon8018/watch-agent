"""
Agent 在任务切换时调用此脚本更新状态文件。
用法: python agent_status_writer.py --id agent1 --status running --task "写测试"
"""
import argparse
import json
import os
import tempfile


def write_status(agent_id: str, status: str, task: str,
                 cwd: str, command: str, completed: int,
                 status_dir: str = "/tmp") -> None:
    data = {
        "name": agent_id,
        "status": status,
        "task": task,
        "cwd": cwd,
        "current_command": command,
        "completed_tasks": completed,
    }
    target = os.path.join(status_dir, f"agent-{agent_id}.json")
    # 原子写入：先写临时文件再重命名，避免读写竞争
    fd, tmp_path = tempfile.mkstemp(dir=status_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_path, target)
    except Exception:
        os.unlink(tmp_path)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--status", default="running")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--command", default="")
    parser.add_argument("--completed", type=int, default=0)
    parser.add_argument("--status-dir", default="/tmp")
    args = parser.parse_args()
    write_status(args.id, args.status, args.task,
                 args.cwd, args.command, args.completed, args.status_dir)
    target_path = os.path.join(args.status_dir, f"agent-{args.id}.json")
    print(f"Status written: {target_path}")
