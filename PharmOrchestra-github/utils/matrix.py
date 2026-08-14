# ============================================================
# matrix.py - 内存消息总线
# 模拟Matrix协议的消息传递机制
# 简单理解：这就是一个"邮局"，Agent之间通过它收发消息
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Message:
    """消息类 - 就像一封信，包含寄件人、收件人、内容等信息

    属性说明：
        trace_id:    追踪ID，同一次药物发现任务的所有消息共享同一个ID
        source:      发送者名称（比如"Scout"或"Manager"）
        target:      接收者名称（比如"Screener"或"Manager"）
        msg_type:    消息类型，"task"表示任务，"result"表示结果
        payload:     消息内容，用一个字典存各种数据
        quality_score: 质量评分，0到1之间，1表示质量最好
        timestamp:   时间戳，记录消息发送的时间
        msg_id:      消息唯一ID，自动生成
    """
    trace_id: str                                    # 追踪ID
    source: str                                      # 发送者
    target: str                                      # 接收者
    msg_type: str                                    # 消息类型: "task" 或 "result"
    payload: Dict[str, Any]                          # 消息内容
    quality_score: float = 0.0                       # 质量评分(0-1)
    timestamp: str = field(                          # 时间戳
        default_factory=lambda: datetime.now().isoformat()
    )
    msg_id: str = field(                             # 唯一消息ID
        default_factory=lambda: str(uuid.uuid4())[:8]
    )

    def __str__(self) -> str:
        """打印消息时显示简洁信息"""
        return (f"[{self.msg_type}] {self.source} -> {self.target} "
                f"(质量={self.quality_score:.2f}, ID={self.msg_id})")


class MatrixBus:
    """内存消息总线 - 模拟Matrix协议

    简单理解：这就是一个"邮局系统"
    - register(): 注册一个Agent（相当于开一个信箱）
    - send():     发送消息（相当于投递信件）
    - receive():  接收消息（相当于从信箱取信）
    - 所有消息都会被记录下来，方便后续追溯
    """

    def __init__(self):
        """初始化消息总线"""
        self._messages: List[Message] = []               # 所有消息的记录（日志用）
        self._queues: Dict[str, List[Message]] = {}      # 每个Agent的消息队列

    def register(self, agent_name: str) -> None:
        """注册一个Agent，为它创建一个专属消息队列

        Args:
            agent_name: Agent的名字，比如"Scout"
        """
        if agent_name not in self._queues:
            self._queues[agent_name] = []

    def send(self, message: Message) -> None:
        """发送一条消息到总线

        消息会被放到目标Agent的队列里，同时记录到全局消息列表中

        Args:
            message: 要发送的消息对象
        """
        # 记录到全局消息列表（用于追溯）
        self._messages.append(message)

        # 放到目标Agent的队列里
        target = message.target
        if target not in self._queues:
            self.register(target)  # 如果目标还没注册，先帮他注册
        self._queues[target].append(message)

    def receive(self, agent_name: str) -> Optional[Message]:
        """从队列中取出一条消息（先进先出）

        Args:
            agent_name: 要取消息的Agent名字

        Returns:
            取到的消息，如果没有消息则返回None
        """
        if agent_name in self._queues and self._queues[agent_name]:
            return self._queues[agent_name].pop(0)  # 取出最早的那条消息
        return None

    def get_all_messages(self) -> List[Message]:
        """获取所有消息记录（用于日志和统计）"""
        return list(self._messages)

    def get_messages_by_trace(self, trace_id: str) -> List[Message]:
        """根据trace_id获取相关消息（追溯某次任务的所有消息）

        Args:
            trace_id: 追踪ID

        Returns:
            该次任务相关的所有消息列表
        """
        return [m for m in self._messages if m.trace_id == trace_id]

    def get_messages_by_agent(self, agent_name: str) -> List[Message]:
        """获取某个Agent收发的所有消息"""
        return [m for m in self._messages
                if m.source == agent_name or m.target == agent_name]

    def message_count(self) -> int:
        """返回已发送的消息总数"""
        return len(self._messages)

    def clear(self) -> None:
        """清空所有消息（重置总线）"""
        self._messages.clear()
        for queue in self._queues.values():
            queue.clear()
