# ============================================================
# trace.py - 追踪日志记录器
# 记录整个药物发现流程中每一步的操作
# 简单理解：这就是一个"行车记录仪"，记录谁在什么时候做了什么
# ============================================================

from datetime import datetime
from typing import Any, Dict, List


class TraceLogger:
    """追踪日志记录器

    功能：
    - 记录每个Agent的每一步操作
    - 计算总耗时
    - 生成流程摘要
    - 支持按trace_id过滤日志
    """

    def __init__(self):
        """初始化日志记录器"""
        self._logs: List[Dict[str, Any]] = []   # 日志列表
        self._start_time: datetime = datetime.now()  # 记录开始时间

    def log(self, trace_id: str, agent: str, action: str,
            detail: str = "") -> None:
        """记录一条日志

        Args:
            trace_id: 追踪ID，标识属于哪次任务
            agent:    执行操作的Agent名字
            action:   操作类型（比如"start_task"、"send_result"）
            detail:   操作的详细描述
        """
        entry: Dict[str, Any] = {
            "trace_id": trace_id,
            "agent": agent,
            "action": action,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        }
        self._logs.append(entry)

    def get_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志"""
        return list(self._logs)

    def get_logs_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """根据trace_id获取相关日志"""
        return [l for l in self._logs if l["trace_id"] == trace_id]

    def get_total_time_ms(self) -> int:
        """获取从开始到现在的总耗时（毫秒）"""
        elapsed = (datetime.now() - self._start_time).total_seconds()
        return int(elapsed * 1000)

    def get_agent_stats(self) -> Dict[str, int]:
        """统计每个Agent的操作次数"""
        stats: Dict[str, int] = {}
        for log in self._logs:
            agent = log["agent"]
            stats[agent] = stats.get(agent, 0) + 1
        return stats

    def summary(self) -> Dict[str, Any]:
        """生成整个流程的摘要信息"""
        return {
            "total_logs": len(self._logs),               # 总日志条数
            "total_time_ms": self.get_total_time_ms(),    # 总耗时
            "agents_involved": list(set(                  # 涉及的Agent
                l["agent"] for l in self._logs
            )),
            "agent_stats": self.get_agent_stats()         # 各Agent操作次数
        }

    def clear(self) -> None:
        """清空所有日志（重置记录器）"""
        self._logs.clear()
        self._start_time = datetime.now()
