# ============================================================
# mechanism.py - 机制分析师Agent
# 大白话：这个Agent的工作是"分析药物怎么起作用的"
# 它用两个技能：先预测结合位点，再计算分子对接分数
# 看看分子能不能卡进靶点蛋白的口袋里
# ============================================================

from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from skills.base_skill import SkillResult
from skills.docking_score import DockingScore
from skills.binding_site import BindingSite
from utils.matrix import MatrixBus
from utils.trace import TraceLogger


class MechanismAgent(BaseAgent):
    """机制分析师Agent

    职责：
    1. 对每个靶点预测结合位点（用binding_site技能）
    2. 对每个分子计算对接分数（用docking_score技能）
    3. 质量检查：最高对接分数 >= 0.8，否则重试一次
    """

    def __init__(self, bus: MatrixBus, trace: TraceLogger):
        """初始化机制分析师，配备对接打分和结合位点预测技能"""
        super().__init__(
            name="Mechanism",
            role="机制分析师 - 分析分子与靶点的结合机制",
            skills=[DockingScore(), BindingSite()],
            bus=bus,
            trace=trace
        )

        # 设置质量检查：最高对接分数 >= 0.8
        self.set_guardrail(self._quality_check)

    def _quality_check(self, result: SkillResult) -> bool:
        """质量检查函数：最高对接分数是否达标

        Args:
            result: 技能执行结果

        Returns:
            最高分数 >= 0.8 返回True，否则返回False
        """
        if not result.success:
            return False
        best_score = result.data.get("best_docking_score", 0.0)
        return best_score >= 0.8

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务：预测结合位点 + 计算对接分数

        Args:
            task:     任务内容，需要包含molecules和targets字段
            trace_id: 追踪ID

        Returns:
            包含对接分数和结合位点信息的结果
        """
        molecules = task.get("molecules", [])
        targets = task.get("targets", [])
        disease = task.get("disease", "未知疾病")

        self.trace.log(
            trace_id, self.name, "start",
            f"开始分析 {len(molecules)} 个分子与 {len(targets)} 个靶点的结合机制"
        )

        binding_skill = self.skills[1]  # BindingSite
        docking_skill = self.skills[0]  # DockingScore

        # ===== 第一步：对每个靶点预测结合位点 =====
        binding_sites: Dict[str, Any] = {}
        for target in targets:
            target_name = target["name"] if isinstance(target, dict) else str(target)

            site_result = self.run_skill(
                binding_skill,
                {"target": target_name},
                trace_id
            )

            if site_result.success:
                binding_sites[target_name] = site_result.data

        self.trace.log(
            trace_id, self.name, "info",
            f"完成了 {len(binding_sites)} 个靶点的结合位点预测"
        )

        # ===== 第二步：对每个靶点的分子计算对接分数 =====
        all_scored_molecules: List[Dict[str, Any]] = []
        best_score = 0.0

        for target in targets:
            target_name = target["name"] if isinstance(target, dict) else str(target)

            # 筛选属于这个靶点的分子
            target_molecules = [
                mol for mol in molecules
                if mol.get("target") == target_name
            ]

            if not target_molecules:
                # 如果没有按靶点分类的分子，就用全部分子
                target_molecules = molecules

            # 计算对接分数
            docking_result = self.run_skill(
                docking_skill,
                {"molecules": target_molecules, "target": target_name},
                trace_id
            )

            if docking_result.success:
                scored_mols = docking_result.data.get("scored_molecules", [])
                # 给每个分子添加结合位点信息
                site_info = binding_sites.get(target_name, {})
                for mol in scored_mols:
                    mol["binding_site"] = site_info
                all_scored_molecules.extend(scored_mols)

                # 更新最高分
                current_best = docking_result.data.get("best_score", 0.0)
                if current_best > best_score:
                    best_score = current_best

        # 按对接分数排序
        all_scored_molecules.sort(
            key=lambda x: x.get("docking_score", 0.0),
            reverse=True
        )

        # ===== 质量检查 =====
        if best_score < 0.8:
            self.trace.log(
                trace_id, self.name, "quality_warning",
                f"最高对接分数({best_score:.4f})未达标(>=0.8)，尝试重试..."
            )

            # 重试一次
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.trace.log(
                    trace_id, self.name, "retry",
                    f"第{self.retry_count}次重试对接计算..."
                )
                # 重新对第一个靶点做一次对接
                if targets:
                    target_name = targets[0]["name"] if isinstance(targets[0], dict) else str(targets[0])
                    docking_result = self.run_skill(
                        docking_skill,
                        {"molecules": molecules, "target": target_name},
                        trace_id
                    )
                    if docking_result.success:
                        new_best = docking_result.data.get("best_score", 0.0)
                        if new_best > best_score:
                            best_score = new_best

        # ===== 组装最终结果 =====
        avg_score = (
            sum(m.get("docking_score", 0.0) for m in all_scored_molecules) / len(all_scored_molecules)
            if all_scored_molecules else 0.0
        )

        result = SkillResult(
            success=True,
            data={
                "disease": disease,
                "scored_molecules": all_scored_molecules,
                "molecule_count": len(all_scored_molecules),
                "binding_sites": binding_sites,
                "best_docking_score": round(best_score, 4),
                "avg_docking_score": round(avg_score, 4),
                "quality_score": min(best_score, 1.0)
            },
            trace_info={
                "agent": self.name,
                "disease": disease,
                "molecule_count": len(all_scored_molecules),
                "best_docking_score": round(best_score, 4)
            }
        )

        self.trace.log(
            trace_id, self.name, "done",
            f"完成任务！分析了 {len(all_scored_molecules)} 个分子，"
            f"最高对接分数={best_score:.4f}，平均={avg_score:.4f}"
        )

        self.reset_retry()
        return result
