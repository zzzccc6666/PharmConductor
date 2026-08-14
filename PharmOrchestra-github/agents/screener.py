# ============================================================
# screener.py - 分子筛选手Agent
# 大白话：知道了靶点之后，这个Agent去"分子库"里找能跟靶点结合的分子
# 它用一个技能：mol_screening（分子筛选）
# ============================================================

from typing import Any, Dict
from agents.base_agent import BaseAgent
from skills.base_skill import SkillResult
from skills.mol_screening import MolScreening
from utils.matrix import MatrixBus
from utils.trace import TraceLogger


class ScreenerAgent(BaseAgent):
    """分子筛选手Agent

    职责：
    1. 接收Scout找到的靶点列表
    2. 用mol_screening技能搜索针对每个靶点的候选分子
    3. 质量检查：至少找到5个候选分子，否则重试一次
    """

    def __init__(self, bus: MatrixBus, trace: TraceLogger):
        """初始化筛选手，配备分子筛选技能"""
        super().__init__(
            name="Screener",
            role="分子筛选手 - 根据靶点搜索候选药物分子",
            skills=[MolScreening()],
            bus=bus,
            trace=trace
        )

        # 设置质量检查：候选分子数量必须 >= 5
        self.set_guardrail(self._quality_check)

    def _quality_check(self, result: SkillResult) -> bool:
        """质量检查函数：候选分子数量是否达标

        Args:
            result: 技能执行结果

        Returns:
            分子数量 >= 5 返回True，否则返回False
        """
        if not result.success:
            return False
        mol_count = result.data.get("count", 0)
        return mol_count >= 5

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务：根据靶点筛选分子

        Args:
            task:     任务内容，需要包含targets字段
            trace_id: 追踪ID

        Returns:
            包含候选分子列表的结果
        """
        targets = task.get("targets", [])
        disease = task.get("disease", "未知疾病")

        self.trace.log(
            trace_id, self.name, "start",
            f"开始为 {len(targets)} 个靶点筛选候选分子（疾病: {disease}）"
        )

        # ===== 执行分子筛选技能 =====
        screen_skill = self.skills[0]  # MolScreening
        screen_result = self.run_skill(
            screen_skill,
            {"targets": targets},
            trace_id
        )

        if not screen_result.success:
            return SkillResult(
                success=False,
                data={},
                error=f"分子筛选失败: {screen_result.error}"
            )

        # ===== 质量检查 =====
        if not self.check_quality(screen_result):
            mol_count = screen_result.data.get("count", 0)
            self.trace.log(
                trace_id, self.name, "quality_warning",
                f"候选分子数量不足({mol_count}个)，尝试重试..."
            )

            # 重试一次
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.trace.log(
                    trace_id, self.name, "retry",
                    f"第{self.retry_count}次重试..."
                )
                screen_result = self.run_skill(
                    screen_skill,
                    {"targets": targets},
                    trace_id
                )

        # ===== 组装最终结果 =====
        molecules = screen_result.data.get("molecules", [])

        result = SkillResult(
            success=True,
            data={
                "disease": disease,
                "targets": targets,
                "molecules": molecules,
                "molecule_count": len(molecules),
                "quality_score": min(len(molecules) / 10.0, 1.0)
            },
            trace_info={
                "agent": self.name,
                "disease": disease,
                "molecule_count": len(molecules)
            }
        )

        self.trace.log(
            trace_id, self.name, "done",
            f"完成任务！找到 {len(molecules)} 个候选分子"
        )

        self.reset_retry()
        return result
