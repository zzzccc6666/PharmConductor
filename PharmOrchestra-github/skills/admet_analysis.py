# ============================================================
# admet_analysis.py - ADMET参数分析技能
# 大白话：检查药物在人体里的"旅行"表现
# ADMET是五个英文单词的缩写：
#   A - Absorption（吸收）：药物能不能被身体吸收
#   D - Distribution（分布）：药物在身体里怎么分布
#   M - Metabolism（代谢）：药物怎么被分解
#   E - Excretion（排泄）：药物怎么排出体外
#   T - Toxicity（毒性）：药物有没有毒
# 这里用mock数据模拟ADMET参数的计算
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult
import hashlib


class ADMETAnalysis(BaseSkill):
    """ADMET参数分析技能

    输入：分子列表
    输出：每个分子的ADMET参数（吸收、分布、代谢、排泄相关指标）
    模拟药物代谢动力学参数的计算
    """

    def __init__(self):
        super().__init__(
            name="admet_analysis",
            description="计算候选分子的ADMET参数（吸收、分布、代谢、排泄、毒性）"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有molecules字段且是列表"""
        return ("molecules" in params
                and isinstance(params["molecules"], list)
                and len(params["molecules"]) > 0)

    def _calculate_admet(self, smiles: str, mw: float) -> Dict[str, Any]:
        """计算单个分子的ADMET参数（mock版本）

        Args:
            smiles: 分子的SMILES字符串
            mw: 分子量

        Returns:
            包含ADMET参数的字典
        """
        # 用SMILES的哈希值来"计算"ADMET参数
        hash_value = hashlib.md5(smiles.encode()).hexdigest()
        num = int(hash_value[:8], 16)

        # ===== 吸收相关参数 =====
        # logP：脂水分配系数，衡量分子亲脂性（-2到5之间比较好）
        logp = round(-1.0 + (num % 70) / 10.0, 2)  # -1.0 到 6.0

        # 溶解度：药物在水中的溶解能力（g/L）
        solubility = round(0.01 + (num % 100) / 10.0, 3)

        # Caco-2渗透性：模拟肠道吸收能力（×10^-6 cm/s）
        caco2 = round(5 + (num % 40), 2)

        # 口服生物利用度（%）：吃下去后能进入血液的比例
        bioavailability = round(20 + (num % 60), 1)

        # ===== 分布相关参数 =====
        # 血浆蛋白结合率（%）：药物和血液蛋白结合的比例
        ppb = round(50 + (num % 49), 1)

        # BBB穿透性：血脑屏障穿透能力（能不能进入大脑）
        bbb_score = round((num % 100) / 100.0, 2)
        bbb_penetration = "高" if bbb_score > 0.7 else ("中" if bbb_score > 0.4 else "低")

        # 表观分布容积（Vd, L/kg）：药物在体内的分布广度
        vd = round(0.5 + (num % 50) / 10.0, 2)

        # ===== 代谢相关参数 =====
        # CYP3A4抑制：是否抑制肝脏最重要的代谢酶
        cyp3a4_inhibition = True if (num % 100) < 30 else False

        # CYP2D6抑制：是否抑制另一个重要代谢酶
        cyp2d6_inhibition = True if (num % 100) < 15 else False

        # 代谢稳定性（半衰期，小时）：药物在体内能存在多久
        half_life = round(1 + (num % 23), 1)

        # ===== 排泄相关参数 =====
        # 清除率（mL/min/kg）：身体清除药物的速度
        clearance = round(2 + (num % 30), 1)

        # ===== 类药性评估 =====
        # Lipinski五规则：评估分子是否符合口服药物的基本条件
        # 规则：分子量<500, logP<5, 氢键供体<5, 氢键受体<10
        lipinski_violations = 0
        if mw > 500:
            lipinski_violations += 1
        if logp > 5:
            lipinski_violations += 1
        # 简化判断
        hbd = num % 6  # 氢键供体数
        hba = num % 12  # 氢键受体数
        if hbd > 5:
            lipinski_violations += 1
        if hba > 10:
            lipinski_violations += 1

        # 综合ADMET评分（0-1，越高越好）
        admet_score = 0.0
        if lipinski_violations == 0:
            admet_score += 0.3
        if 30 < bioavailability < 80:
            admet_score += 0.2
        if logp < 5:
            admet_score += 0.2
        if not cyp3a4_inhibition:
            admet_score += 0.15
        if half_life > 4:
            admet_score += 0.15
        admet_score = round(admet_score, 2)

        return {
            # 吸收参数
            "logp": logp,
            "solubility": solubility,
            "caco2_permeability": caco2,
            "oral_bioavailability": bioavailability,
            # 分布参数
            "plasma_protein_binding": ppb,
            "bbb_penetration": bbb_penetration,
            "bbb_score": bbb_score,
            "vd": vd,
            # 代谢参数
            "cyp3a4_inhibition": cyp3a4_inhibition,
            "cyp2d6_inhibition": cyp2d6_inhibition,
            "half_life": half_life,
            # 排泄参数
            "clearance": clearance,
            # 类药性
            "lipinski_violations": lipinski_violations,
            "hbd": hbd,
            "hba": hba,
            "admet_score": admet_score
        }

    def execute(self, molecules: List[Dict[str, Any]], **kwargs) -> SkillResult:
        """执行ADMET分析（mock版本）

        Args:
            molecules: 分子列表

        Returns:
            SkillResult，data中包含每个分子的ADMET参数
        """
        results: List[Dict[str, Any]] = []

        for mol in molecules:
            smiles = mol.get("smiles", "")
            mw = mol.get("mw", 200.0)  # 默认分子量200
            admet_info = self._calculate_admet(smiles, mw)

            # 复制分子信息并添加ADMET数据
            mol_with_admet = dict(mol)
            mol_with_admet["admet"] = admet_info

            results.append(mol_with_admet)

        # 计算平均ADMET评分
        avg_score = sum(r["admet"]["admet_score"] for r in results) / len(results) if results else 0.0

        return SkillResult(
            success=True,
            data={
                "admet_results": results,
                "count": len(results),
                "avg_admet_score": round(avg_score, 4),
                "best_admet_score": max(r["admet"]["admet_score"] for r in results) if results else 0.0
            },
            trace_info={
                "skill": self.name,
                "molecule_count": len(results),
                "avg_admet_score": round(avg_score, 4)
            }
        )
