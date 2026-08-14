# ============================================================
# scout.py - 文献侦察兵Agent
# 大白话：这个Agent的工作是"去图书馆查资料"
# 它用两个技能：先搜PubMed找论文，再从论文里提取药物靶点
# ============================================================

from typing import Any, Dict
from agents.base_agent import BaseAgent
from skills.base_skill import SkillResult
from skills.pubmed_search import PubMedSearch
from skills.target_extract import TargetExtract
from utils.matrix import MatrixBus
from utils.trace import TraceLogger


class ScoutAgent(BaseAgent):
    """文献侦察兵Agent

    职责：
    1. 用pubmed_search技能检索疾病相关论文
    2. 用target_extract技能从论文中提取药物靶点
    3. 质量检查：至少找到3个靶点，否则重试一次
    """

    def __init__(self, bus: MatrixBus, trace: TraceLogger):
        """初始化侦察兵，配备两个技能"""
        super().__init__(
            name="Scout",
            role="文献侦察兵 - 从科研文献中发现药物靶点",
            skills=[PubMedSearch(), TargetExtract()],
            bus=bus,
            trace=trace
        )

        # 设置质量检查：靶点数量必须 >= 3
        self.set_guardrail(self._quality_check)

    def _quality_check(self, result: SkillResult) -> bool:
        """质量检查函数：检查找到的靶点数量是否达标

        Args:
            result: 技能执行结果

        Returns:
            靶点数量 >= 3 返回True，否则返回False
        """
        if not result.success:
            return False
        target_count = result.data.get("count", 0)
        return target_count >= 3

    def process(self, task: Dict[str, Any], trace_id: str) -> SkillResult:
        """处理任务：检索文献 -> 提取靶点

        Args:
            task:     任务内容，需要包含disease字段
            trace_id: 追踪ID

        Returns:
            包含论文和靶点信息的结果
        """
        disease = task.get("disease", "未知疾病")

        self.trace.log(
            trace_id, self.name, "start",
            f"开始为疾病'{disease}'检索文献和靶点"
        )

        # ===== 第一步：检索PubMed论文 =====
        pubmed_skill = self.skills[0]  # PubMedSearch
        pubmed_result = self.run_skill(
            pubmed_skill,
            {"disease": disease},
            trace_id
        )

        if not pubmed_result.success:
            return SkillResult(
                success=False,
                data={},
                error=f"PubMed检索失败: {pubmed_result.error}"
            )

        papers = pubmed_result.data.get("papers", [])
        self.trace.log(
            trace_id, self.name, "info",
            f"找到 {len(papers)} 篇相关论文"
        )

        # ===== 第二步：从论文中提取靶点 =====
        extract_skill = self.skills[1]  # TargetExtract
        extract_result = self.run_skill(
            extract_skill,
            {"papers": papers, "disease": disease},
            trace_id
        )

        if not extract_result.success:
            return SkillResult(
                success=False,
                data={},
                error=f"靶点提取失败: {extract_result.error}"
            )

        # ===== 第三步：质量检查 =====
        if not self.check_quality(extract_result):
            self.trace.log(
                trace_id, self.name, "quality_warning",
                f"靶点数量不足({extract_result.data.get('count', 0)}个)，尝试重试..."
            )

            # 重试一次（用调整后的参数）
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.trace.log(
                    trace_id, self.name, "retry",
                    f"第{self.retry_count}次重试，扩大检索范围..."
                )
                # 重试时直接用疾病名重新提取
                extract_result = self.run_skill(
                    extract_skill,
                    {"papers": papers, "disease": disease},
                    trace_id
                )

        # ===== 组装最终结果 =====
        targets = extract_result.data.get("targets", [])
        target_names = [t["name"] if isinstance(t, dict) else str(t) for t in targets]

        result = SkillResult(
            success=True,
            data={
                "disease": disease,
                "papers": papers,
                "paper_count": len(papers),
                "targets": targets,
                "target_names": target_names,
                "target_count": len(targets),
                "quality_score": min(len(targets) / 5.0, 1.0)  # 质量评分
            },
            trace_info={
                "agent": self.name,
                "disease": disease,
                "paper_count": len(papers),
                "target_count": len(targets)
            }
        )

        self.trace.log(
            trace_id, self.name, "done",
            f"完成任务！找到 {len(papers)} 篇论文，{len(targets)} 个靶点: {target_names}"
        )

        self.reset_retry()
        return result
