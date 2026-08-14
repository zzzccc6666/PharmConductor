# ============================================================
# docking_score.py - 分子对接打分技能
# 大白话：把分子"塞"到靶点蛋白的口袋里，看看结合得好不好
# 分数越高说明结合越好，药效可能越强
# 这里用mock数据模拟，真实的对接需要RDKit和AutoDock等工具
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult
import random
import hashlib


class DockingScore(BaseSkill):
    """分子对接打分技能

    输入：分子列表 + 靶点名称
    输出：每个分子的对接分数（0到1之间，越高越好）
    模拟分子与靶点蛋白的结合能力评估
    """

    def __init__(self):
        super().__init__(
            name="docking_score",
            description="计算候选分子与靶点蛋白的对接分数，评估结合能力"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有molecules和target"""
        return ("molecules" in params
                and isinstance(params["molecules"], list)
                and len(params["molecules"]) > 0
                and "target" in params)

    def _generate_score(self, smiles: str, target: str) -> float:
        """根据SMILES和靶点生成一个确定性的分数

        使用哈希函数保证：相同的分子+靶点组合总是得到相同的分数
        这样结果可复现，不会每次运行都不同

        Args:
            smiles: 分子的SMILES字符串
            target: 靶点名称

        Returns:
            对接分数（0.5到0.95之间）
        """
        # 把SMILES和靶点名拼在一起做哈希
        key = f"{smiles}_{target}"
        hash_value = hashlib.md5(key.encode()).hexdigest()

        # 把哈希值转成数字，再映射到0.5-0.95的范围
        num = int(hash_value[:8], 16)  # 取前8位十六进制转成数字
        score = 0.5 + (num % 451) / 1000.0  # 0.5 + 0~0.45 = 0.5~0.95

        return round(score, 4)

    def execute(self, molecules: List[Dict[str, Any]], target: str, **kwargs) -> SkillResult:
        """执行分子对接打分（mock版本）

        Args:
            molecules: 分子列表，每个分子是包含smiles等信息的字典
            target: 靶点名称

        Returns:
            SkillResult，data中包含每个分子的对接分数
        """
        scored_molecules: List[Dict[str, Any]] = []
        total_score = 0.0

        for mol in molecules:
            smiles = mol.get("smiles", "")
            score = self._generate_score(smiles, target)

            # 复制分子信息并添加对接分数
            scored_mol = dict(mol)
            scored_mol["docking_score"] = score
            scored_mol["docking_target"] = target

            # 添加一些额外的对接信息
            scored_mol["binding_energy"] = round(-12 * score - 0.5, 2)  # 模拟结合能(kcal/mol)
            scored_mol["hbond_count"] = (int(score * 10) % 5) + 1       # 模拟氢键数量

            scored_molecules.append(scored_mol)
            total_score += score

        # 按对接分数从高到低排序
        scored_molecules.sort(key=lambda x: x["docking_score"], reverse=True)

        avg_score = total_score / len(scored_molecules) if scored_molecules else 0.0

        return SkillResult(
            success=True,
            data={
                "scored_molecules": scored_molecules,
                "count": len(scored_molecules),
                "avg_score": round(avg_score, 4),
                "best_score": scored_molecules[0]["docking_score"] if scored_molecules else 0.0,
                "target": target
            },
            trace_info={
                "skill": self.name,
                "target": target,
                "molecule_count": len(scored_molecules),
                "avg_score": round(avg_score, 4)
            }
        )
