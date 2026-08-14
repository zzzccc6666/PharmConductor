# ============================================================
# safety.py - 安全评估官Agent
# 大白话：这个Agent是"安全检查员"
# 它用两个技能：先预测毒性，再算ADMET参数
# 最后筛出安全的分子，给出最终排名
# ============================================================

from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from skills.base_skill import SkillResult
from skills.tox_predict import ToxPredict
from skills.admet_analysis import ADMETAnalysis
from utils.matrix import MatrixBus
from utils.trace import TraceLogger


class SafetyAgent(BaseAgent):
    """安全评估官Agent

    职责：
    1. 用tox_predict技能预测每个分子的毒性
    2. 用admet_analysis技能计算每个分子的ADMET参数
    3. 综合评分，筛选出安全的候选分子
    4. 质量检查：安全分子数量 >= 5，否则重试一次
    """

    def __init__(self, bus: MatrixBus, trace: TraceLogger):
        """初始化安全评估官，配备毒性预测和ADMET分析技能"""
        super().__init__(
            name="Safety",
            role="安全评估官 - 评估分子毒性和药代动力学性质",
            skills=[ToxPredict(), ADMETAnalysis()],
            bus=bus,
            trace=trace
        )

        # 设置质量检查：安全分子数量必须 >= 5
        self.set_guardrail(self._quality_check)

    def _quality_check(self, result: SkillResult) -> bool:
        """质量检查函数：安全分子数量是否达标

        Args:
            result: 技能执行结果

        Returns:
            安全分子数量 >= 5 返回True，否则返回False
        """
        if not result.success:
            return False
        safe_count = result.data.get("safe_molecule_count", 0)
        return safe_count >= 5

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务：毒性预测 + ADMET分析 + 综合评分

        Args:
            task:     任务内容，需要包含scored_molecules字段
            trace_id: 追踪ID

        Returns:
            包含安全分子列表和最终排名的结果
        """
        molecules = task.get("scored_molecules", [])
        disease = task.get("disease", "未知疾病")

        self.trace.log(
            trace_id, self.name, "start",
            f"开始评估 {len(molecules)} 个分子的安全性和ADMET性质"
        )

        tox_skill = self.skills[0]   # ToxPredict
        admet_skill = self.skills[1] # ADMETAnalysis

        # ===== 第一步：毒性预测 =====
        tox_result = self.run_skill(
            tox_skill,
            {"molecules": molecules},
            trace_id
        )

        if not tox_result.success:
            return SkillResult(
                success=False,
                data={},
                error=f"毒性预测失败: {tox_result.error}"
            )

        molecules_with_tox = tox_result.data.get("toxicity_results", [])

        self.trace.log(
            trace_id, self.name, "info",
            f"毒性预测完成: {tox_result.data.get('risk_distribution', {})}"
        )

        # ===== 第二步：ADMET分析 =====
        admet_result = self.run_skill(
            admet_skill,
            {"molecules": molecules_with_tox},
            trace_id
        )

        if not admet_result.success:
            return SkillResult(
                success=False,
                data={},
                error=f"ADMET分析失败: {admet_result.error}"
            )

        molecules_final = admet_result.data.get("admet_results", [])

        # ===== 第三步：综合评分和筛选 =====
        safe_molecules: List[Dict[str, Any]] = []

        for mol in molecules_final:
            tox = mol.get("toxicity", {})
            admet = mol.get("admet", {})
            docking = mol.get("docking_score", 0.0)

            # 只保留低毒性的分子
            if tox.get("risk_level") == "low":
                # 计算综合分数
                # 综合分 = 对接分数 * 0.4 + ADMET分 * 0.3 + (1-毒性分) * 0.3
                tox_score = tox.get("tox_score", 0.5)
                admet_score = admet.get("admet_score", 0.5)

                composite_score = (
                    docking * 0.4 +           # 对接分数权重40%
                    admet_score * 0.3 +       # ADMET评分权重30%
                    (1 - tox_score) * 0.3     # 安全性权重30%
                )

                mol["composite_score"] = round(composite_score, 4)
                mol["final_rank"] = 0  # 后面再排名
                safe_molecules.append(mol)

        # 按综合分数排序
        safe_molecules.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)

        # 排名
        for i, mol in enumerate(safe_molecules):
            mol["final_rank"] = i + 1

        # ===== 质量检查 =====
        if len(safe_molecules) < 5:
            self.trace.log(
                trace_id, self.name, "quality_warning",
                f"安全分子数量不足({len(safe_molecules)}个)，尝试重试..."
            )

            # 重试一次：放宽标准，加入中等风险分子
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.trace.log(
                    trace_id, self.name, "retry",
                    f"第{self.retry_count}次重试：放宽标准，纳入中等风险分子..."
                )
                # 把中等风险的分子也加进来
                for mol in molecules_final:
                    tox = mol.get("toxicity", {})
                    if tox.get("risk_level") == "medium" and mol not in safe_molecules:
                        docking = mol.get("docking_score", 0.0)
                        tox_score = tox.get("tox_score", 0.5)
                        admet = mol.get("admet", {})
                        admet_score = admet.get("admet_score", 0.5)

                        composite_score = (
                            docking * 0.4 +
                            admet_score * 0.3 +
                            (1 - tox_score) * 0.3
                        )
                        mol["composite_score"] = round(composite_score, 4)
                        mol["final_rank"] = 0
                        safe_molecules.append(mol)

                # 重新排序
                safe_molecules.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
                for i, mol in enumerate(safe_molecules):
                    mol["final_rank"] = i + 1

        # ===== 组装最终结果 =====
        result = SkillResult(
            success=True,
            data={
                "disease": disease,
                "safe_molecules": safe_molecules,
                "safe_molecule_count": len(safe_molecules),
                "total_molecules_evaluated": len(molecules_final),
                "risk_distribution": tox_result.data.get("risk_distribution", {}),
                "avg_admet_score": admet_result.data.get("avg_admet_score", 0.0),
                "quality_score": min(len(safe_molecules) / 10.0, 1.0)
            },
            trace_info={
                "agent": self.name,
                "disease": disease,
                "safe_molecule_count": len(safe_molecules),
                "total_evaluated": len(molecules_final)
            }
        )

        self.trace.log(
            trace_id, self.name, "done",
            f"完成任务！评估了 {len(molecules_final)} 个分子，"
            f"筛选出 {len(safe_molecules)} 个安全候选分子"
        )

        self.reset_retry()
        return result
