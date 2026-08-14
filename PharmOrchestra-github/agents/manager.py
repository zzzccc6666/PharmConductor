# ============================================================
# manager.py - 编排器（Manager Agent）
# 大白话：这是团队的"项目经理"，负责把任务按顺序分配给4个Worker
# 流程：Scout(找靶点) -> Screener(找分子) -> Mechanism(分析机制) -> Safety(评估安全)
# 每一步之间都有质量检查，不合格会重试
# ============================================================

from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent
from agents.scout import ScoutAgent
from agents.screener import ScreenerAgent
from agents.mechanism import MechanismAgent
from agents.safety import SafetyAgent
from skills.base_skill import SkillResult
from utils.matrix import MatrixBus
from utils.trace import TraceLogger
import uuid


class ManagerAgent(BaseAgent):
    """编排器Agent - 协调整个药物发现流程

    职责：
    1. 创建并管理4个Worker Agent
    2. 按顺序分配任务：Scout -> Screener -> Mechanism -> Safety
    3. 在每一步之间传递数据
    4. 汇总最终结果
    """

    def __init__(self, bus: MatrixBus, trace: TraceLogger):
        """初始化编排器，创建4个Worker"""
        super().__init__(
            name="Manager",
            role="编排器 - 协调药物发现全流程",
            skills=[],  # Manager自己不执行技能，它负责协调
            bus=bus,
            trace=trace
        )

        # 创建4个Worker Agent
        self.scout: ScoutAgent = ScoutAgent(bus, trace)
        self.screener: ScreenerAgent = ScreenerAgent(bus, trace)
        self.mechanism: MechanismAgent = MechanismAgent(bus, trace)
        self.safety: SafetyAgent = SafetyAgent(bus, trace)

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务：协调整个药物发现流程

        Args:
            task:     任务内容，需要包含disease字段
            trace_id: 追踪ID

        Returns:
            包含最终安全候选分子列表的结果
        """
        disease = task.get("disease", "未知疾病")

        self.trace.log(
            trace_id, self.name, "pipeline_start",
            f"===== 药物发现流程开始 ===== 疾病: {disease}"
        )

        # ===== 第一步：Scout - 文献检索和靶点发现 =====
        self.trace.log(trace_id, self.name, "dispatch", ">>> 分配任务给 Scout（文献侦察兵）")
        self.send_task("Scout", trace_id, task)

        scout_result = self.scout.process(task, trace_id)

        if not scout_result.success:
            return SkillResult(
                success=False, data={},
                error=f"Scout阶段失败: {scout_result.error}"
            )

        self.scout.send_result("Manager", trace_id, scout_result)

        # ===== 第二步：Screener - 分子筛选 =====
        screener_task: Dict[str, Any] = {
            "disease": disease,
            "targets": scout_result.data.get("targets", []),
            "target_names": scout_result.data.get("target_names", [])
        }

        self.trace.log(trace_id, self.name, "dispatch", ">>> 分配任务给 Screener（分子筛选手）")
        self.send_task("Screener", trace_id, screener_task)

        screener_result = self.screener.process(screener_task, trace_id)

        if not screener_result.success:
            return SkillResult(
                success=False, data={},
                error=f"Screener阶段失败: {screener_result.error}"
            )

        self.screener.send_result("Manager", trace_id, screener_result)

        # ===== 第三步：Mechanism - 机制分析 =====
        mechanism_task: Dict[str, Any] = {
            "disease": disease,
            "targets": scout_result.data.get("targets", []),
            "molecules": screener_result.data.get("molecules", [])
        }

        self.trace.log(trace_id, self.name, "dispatch", ">>> 分配任务给 Mechanism（机制分析师）")
        self.send_task("Mechanism", trace_id, mechanism_task)

        mechanism_result = self.mechanism.process(mechanism_task, trace_id)

        if not mechanism_result.success:
            return SkillResult(
                success=False, data={},
                error=f"Mechanism阶段失败: {mechanism_result.error}"
            )

        self.mechanism.send_result("Manager", trace_id, mechanism_result)

        # ===== 第四步：Safety - 安全评估 =====
        safety_task: Dict[str, Any] = {
            "disease": disease,
            "scored_molecules": mechanism_result.data.get("scored_molecules", [])
        }

        self.trace.log(trace_id, self.name, "dispatch", ">>> 分配任务给 Safety（安全评估官）")
        self.send_task("Safety", trace_id, safety_task)

        safety_result = self.safety.process(safety_task, trace_id)

        if not safety_result.success:
            return SkillResult(
                success=False, data={},
                error=f"Safety阶段失败: {safety_result.error}"
            )

        self.safety.send_result("Manager", trace_id, safety_result)

        # ===== 汇总最终结果 =====
        final_result = SkillResult(
            success=True,
            data={
                "disease": disease,
                "pipeline_summary": {
                    "papers_found": scout_result.data.get("paper_count", 0),
                    "targets_found": scout_result.data.get("target_names", []),
                    "molecules_screened": screener_result.data.get("molecule_count", 0),
                    "molecules_scored": mechanism_result.data.get("molecule_count", 0),
                    "best_docking_score": mechanism_result.data.get("best_docking_score", 0.0),
                    "safe_molecules": safety_result.data.get("safe_molecule_count", 0),
                    "risk_distribution": safety_result.data.get("risk_distribution", {})
                },
                "safe_molecules": safety_result.data.get("safe_molecules", []),
                "binding_sites": mechanism_result.data.get("binding_sites", {}),
                "quality_score": safety_result.data.get("quality_score", 0.0)
            },
            trace_info={
                "agent": self.name,
                "disease": disease,
                "total_messages": self.bus.message_count(),
                "trace_id": trace_id
            }
        )

        self.trace.log(
            trace_id, self.name, "pipeline_done",
            f"===== 药物发现流程完成 ===== "
            f"找到 {len(safety_result.data.get('safe_molecules', []))} 个安全候选分子"
        )

        return final_result

    def run_pipeline(self, disease: str) -> Dict[str, Any]:
        """运行完整的药物发现流程（对外接口）

        Args:
            disease: 疾病名称

        Returns:
            包含完整结果的字典
        """
        # 生成追踪ID
        trace_id = str(uuid.uuid4())[:8]

        # 构建初始任务
        task = {"disease": disease}

        # 执行流程
        result = self.process(task, trace_id)

        # 汇总信息
        return {
            "trace_id": trace_id,
            "success": result.success,
            "disease": disease,
            "data": result.data,
            "error": result.error,
            "trace_summary": self.trace.summary(),
            "message_count": self.bus.message_count(),
            "total_messages": [str(m) for m in self.bus.get_all_messages()]
        }
