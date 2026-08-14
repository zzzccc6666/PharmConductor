# ============================================================
# tox_predict.py - 毒性预测技能
# 大白话：检查这些分子有没有毒，会不会伤害人体
# 模拟Tox21毒性预测模型，返回每个分子的毒性风险等级
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult
import hashlib


# ============================================================
# 毒性风险等级说明：
# - low:    低风险，可以继续研究
# - medium: 中等风险，需要谨慎评估
# - high:   高风险，不建议继续开发
# ============================================================


class ToxPredict(BaseSkill):
    """毒性预测技能

    输入：分子列表
    输出：每个分子的毒性预测结果
    模拟Tox21毒性预测模型的输出
    """

    def __init__(self):
        super().__init__(
            name="tox_predict",
            description="预测候选分子的毒性风险等级和毒理学参数"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有molecules字段且是列表"""
        return ("molecules" in params
                and isinstance(params["molecules"], list)
                and len(params["molecules"]) > 0)

    def _predict_toxicity(self, smiles: str) -> Dict[str, Any]:
        """根据SMILES预测毒性（mock版本）

        使用哈希函数生成确定性的毒性预测结果

        Args:
            smiles: 分子的SMILES字符串

        Returns:
            包含毒性信息的字典
        """
        # 用SMILES的哈希值来"预测"毒性
        hash_value = hashlib.md5(smiles.encode()).hexdigest()
        num = int(hash_value[:8], 16)

        # 确定风险等级（约60%低风险，25%中等，15%高风险）
        risk_num = num % 100
        if risk_num < 60:
            risk_level = "low"
        elif risk_num < 85:
            risk_level = "medium"
        else:
            risk_level = "high"

        # 模拟各种毒性测试结果
        # AMES试验：检测致突变性（致癌风险的初步筛查）
        ames_test = "阳性" if (num % 100) < 15 else "阴性"

        # 肝毒性：检测是否损伤肝脏
        hepatotoxicity = True if (num % 100) < 20 else False

        # 心脏毒性（hERG通道抑制）：检测是否影响心律
        herg_inhibition = True if (num % 100) < 25 else False

        # 皮肤致敏性
        skin_sensitization = True if (num % 100) < 10 else False

        # 计算综合毒性分数（0-1，越低越安全）
        tox_score = 0.0
        if risk_level == "low":
            tox_score = 0.1 + (num % 20) / 100.0
        elif risk_level == "medium":
            tox_score = 0.3 + (num % 20) / 100.0
        else:
            tox_score = 0.6 + (num % 30) / 100.0

        return {
            "risk_level": risk_level,
            "tox_score": round(tox_score, 4),
            "ames_test": ames_test,
            "hepatotoxicity": hepatotoxicity,
            "herg_inhibition": herg_inhibition,
            "skin_sensitization": skin_sensitization
        }

    def execute(self, molecules: List[Dict[str, Any]], **kwargs) -> SkillResult:
        """执行毒性预测（mock版本）

        Args:
            molecules: 分子列表

        Returns:
            SkillResult，data中包含每个分子的毒性预测结果
        """
        results: List[Dict[str, Any]] = []

        for mol in molecules:
            smiles = mol.get("smiles", "")
            tox_info = self._predict_toxicity(smiles)

            # 复制分子信息并添加毒性数据
            mol_with_tox = dict(mol)
            mol_with_tox["toxicity"] = tox_info

            results.append(mol_with_tox)

        # 统计各风险等级的数量
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        for r in results:
            level = r["toxicity"]["risk_level"]
            risk_counts[level] = risk_counts.get(level, 0) + 1

        return SkillResult(
            success=True,
            data={
                "toxicity_results": results,
                "count": len(results),
                "risk_distribution": risk_counts,
                "safe_count": risk_counts["low"]
            },
            trace_info={
                "skill": self.name,
                "molecule_count": len(results),
                "safe_count": risk_counts["low"]
            }
        )
