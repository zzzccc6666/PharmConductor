# ============================================================
# base_agent.py - Agent基类
# 所有Agent（不管是Manager还是Worker）都继承这个类
# Agent就是"团队成员"，每个成员有自己的名字、角色和技能
# ============================================================

from typing import Any, Callable, Dict, List, Optional
from utils.matrix import MatrixBus, Message
from utils.trace import TraceLogger
from skills.base_skill import BaseSkill, SkillResult


class BaseAgent:
    """Agent基类 - 所有Agent的父类

    核心属性：
        name:   Agent名字，比如"Scout"（侦察兵）
        role:   角色描述，比如"从文献中找靶点"
        skills: 这个Agent掌握的技能列表
        bus:    消息总线，用来和其他Agent通信
        trace:  日志记录器，记录操作日志

    核心方法：
        process():       处理收到的任务（子类必须实现）
        send_result():   把结果发给其他Agent
        receive_task():  从消息总线接收任务
        check_quality(): 质量检查（质量门控）
    """

    def __init__(self, name: str, role: str, skills: List[BaseSkill],
                 bus: MatrixBus, trace: TraceLogger):
        """初始化Agent

        Args:
            name:   Agent名字
            role:   角色描述
            skills: 技能列表
            bus:    消息总线
            trace:  日志记录器
        """
        self.name: str = name
        self.role: str = role
        self.skills: List[BaseSkill] = skills
        self.bus: MatrixBus = bus
        self.trace: TraceLogger = trace

        # 在消息总线上注册自己（相当于开一个信箱）
        self.bus.register(self.name)

        # 质量检查函数（guardrail，也就是"质量门槛"）
        # 如果不设置，默认总是通过
        self.guardrail: Optional[Callable[[SkillResult], bool]] = None

        # 重试次数计数
        self.retry_count: int = 0
        self.max_retries: int = 1  # 最多重试1次

    def set_guardrail(self, func: Callable[[SkillResult], bool]) -> None:
        """设置质量检查函数

        质量检查函数接收一个SkillResult，返回True表示通过，False表示不通过

        Args:
            func: 质量检查函数
        """
        self.guardrail = func

    def check_quality(self, result: SkillResult) -> bool:
        """检查结果质量是否达标

        Args:
            result: 技能执行结果

        Returns:
            质量达标返回True，否则返回False
        """
        if self.guardrail is None:
            return True  # 没有设置质量检查，默认通过
        return self.guardrail(result)

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务 - 子类必须实现此方法

        Args:
            task:     任务内容
            trace_id: 追踪ID

        Returns:
            处理结果
        """
        raise NotImplementedError("子类必须实现process方法")

    def send_result(self, target: str, trace_id: str,
                    result: SkillResult) -> None:
        """通过消息总线把结果发送给目标Agent

        Args:
            target:   接收者名字
            trace_id: 追踪ID
            result:   要发送的结果
        """
        msg = Message(
            trace_id=trace_id,
            source=self.name,
            target=target,
            msg_type="result",
            payload={
                "data": result.data,
                "success": result.success,
                "error": result.error
            },
            quality_score=result.data.get("quality_score", 0.8)
        )
        self.bus.send(msg)

        # 记录日志
        self.trace.log(
            trace_id, self.name, "send_result",
            f"发送结果给 {target}，质量评分={msg.quality_score:.2f}"
        )

    def send_task(self, target: str, trace_id: str,
                  task_data: Dict[str, Any]) -> None:
        """通过消息总线把任务发送给目标Agent

        Args:
            target:    接收者名字
            trace_id:  追踪ID
            task_data: 任务数据
        """
        msg = Message(
            trace_id=trace_id,
            source=self.name,
            target=target,
            msg_type="task",
            payload=task_data,
            quality_score=0.0
        )
        self.bus.send(msg)

        # 记录日志
        self.trace.log(
            trace_id, self.name, "send_task",
            f"发送任务给 {target}"
        )

    def receive_task(self) -> Optional[Message]:
        """从消息总线接收任务

        Returns:
            收到的消息，如果没有消息返回None
        """
        return self.bus.receive(self.name)

    def run_skill(self, skill: BaseSkill, params: Dict[str, Any],
                  trace_id: str) -> SkillResult:
        """执行一个技能并记录日志

        Args:
            skill:    要执行的技能
            params:   技能参数
            trace_id: 追踪ID

        Returns:
            技能执行结果
        """
        # 记录开始日志
        self.trace.log(
            trace_id, self.name, "skill_start",
            f"执行技能: {skill.name}"
        )

        # 执行技能
        result = skill.run(params)

        # 记录结束日志
        if result.success:
            self.trace.log(
                trace_id, self.name, "skill_done",
                f"技能 {skill.name} 执行成功，耗时 {result.execution_time_ms}ms"
            )
        else:
            self.trace.log(
                trace_id, self.name, "skill_error",
                f"技能 {skill.name} 执行失败: {result.error}"
            )

        return result

    def reset_retry(self) -> None:
        """重置重试计数器"""
        self.retry_count = 0
