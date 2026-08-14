# ============================================================
# mol_screening.py - 分子筛选技能
# 大白话：知道了靶点后，去PubChem数据库找跟已知药物相似的分子
# 这里用mock数据模拟，返回一些假的SMILES分子
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult
import random


# ============================================================
# Mock数据 - 每个靶点对应的候选分子库
# SMILES是化学分子的文本表示方式，就像分子的"身份证号"
# ============================================================
MOCK_MOLECULES: Dict[str, List[Dict[str, Any]]] = {
    # ===== 糖尿病相关靶点的分子 =====
    "GLUT4": [
        {"smiles": "CN(C)C(=N)N=C(N)N", "name": "二甲双胍类似物-1", "cid": "4091", "mw": 129.16},
        {"smiles": "CC1=CC=C(C=C1)C(=O)NC2=CC=CC=C2", "name": "GLUT4调节剂-A", "cid": "50001", "mw": 211.24},
        {"smiles": "OC(=O)CCCCCCC(=O)O", "name": "GLUT4调节剂-B", "cid": "50002", "mw": 174.19},
        {"smiles": "CC(=O)NC1=CC=C(C=C1)S(=O)(=O)N", "name": "GLUT4调节剂-C", "cid": "50003", "mw": 214.24},
    ],
    "IRS-1": [
        {"smiles": "CC1=CC=C(C=C1)NC(=O)C2=CC=CC=C2", "name": "IRS-1调节剂-A", "cid": "50004", "mw": 211.24},
        {"smiles": "OC1=CC=CC=C1C(=O)NC2=CC=CC=C2", "name": "IRS-1调节剂-B", "cid": "50005", "mw": 213.23},
        {"smiles": "CN(C)CCCN1C2=CC=CC=C2CCC2=C1C=CC=C2", "name": "IRS-1调节剂-C", "cid": "50006", "mw": 290.40},
    ],
    "AMPK": [
        {"smiles": "CN(C)C(=N)N=C(N)N", "name": "二甲双胍(AMPK激活剂)", "cid": "4091", "mw": 129.16},
        {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "name": "阿司匹林(AMPK相关)", "cid": "2244", "mw": 180.16},
        {"smiles": "OC1=CC=C(C=C1)C(=O)O", "name": "AMPK激活剂-A", "cid": "50007", "mw": 138.12},
        {"smiles": "CC(=O)CC1=CC=C(C=C1)O", "name": "AMPK激活剂-B", "cid": "50008", "mw": 150.17},
        {"smiles": "OC(=O)C1=CC=C(C=C1)O", "name": "AMPK激活剂-C", "cid": "50009", "mw": 138.12},
    ],
    "GLP-1R": [
        {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "GLP-1R调节剂-A", "cid": "50010", "mw": 206.24},
        {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)NC2=CC=CC=C2", "name": "GLP-1R调节剂-B", "cid": "50011", "mw": 281.31},
        {"smiles": "OC(=O)CCC1=CC=CC=C1", "name": "GLP-1R调节剂-C", "cid": "50012", "mw": 150.17},
    ],
    "PPAR-γ": [
        {"smiles": "CC1=CC=C(C=C1)CC(=O)O", "name": "PPAR-γ激动剂-A", "cid": "50013", "mw": 150.17},
        {"smiles": "CC(=O)NC1=CC=C(C=C1)C(=O)O", "name": "PPAR-γ激动剂-B", "cid": "50014", "mw": 179.17},
        {"smiles": "CC1=CC=C(C=C1)C(=O)NC2=CC=CC=C2", "name": "PPAR-γ激动剂-C", "cid": "50015", "mw": 211.24},
    ],

    # ===== 乳腺癌相关靶点的分子 =====
    "ERα": [
        {"smiles": "CC12CCC3C(CCc4cc(O)ccc43)C1CCC2O", "name": "雌二醇(ERα配体)", "cid": "5757", "mw": 272.38},
        {"smiles": "CC(C)(C)c1ccc(O)cc1", "name": "ERα调节剂-A", "cid": "50020", "mw": 164.20},
        {"smiles": "OC1=CC=C(C=C1)C2=CC=CC=C2", "name": "ERα调节剂-B", "cid": "50021", "mw": 170.21},
    ],
    "HER2": [
        {"smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN4CCOCC4", "name": "HER2抑制剂-A", "cid": "50022", "mw": 449.90},
        {"smiles": "Cc1cc(N2CCNCC2)cc3ncnc13", "name": "HER2抑制剂-B", "cid": "50023", "mw": 228.29},
    ],
    "CDK4/6": [
        {"smiles": "CC1(C)CC2(C)CC3(C)CCC4CCCCC4(C)C3C2C1", "name": "CDK4/6抑制剂-A", "cid": "50024", "mw": 276.46},
        {"smiles": "CNC(=O)c1cc(-c2ccccc2)nc(-c2ccc(N)cc2)n1", "name": "CDK4/6抑制剂-B", "cid": "50025", "mw": 330.36},
    ],
    "PI3K": [
        {"smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "name": "PI3K抑制剂-A", "cid": "50026", "mw": 194.19},
        {"smiles": "CC1=CC2=C(C=C1)N(C3=CC=CC=C3)C=N2", "name": "PI3K抑制剂-B", "cid": "50027", "mw": 232.28},
    ],

    # ===== 高血压相关靶点的分子 =====
    "ACE": [
        {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "ACE抑制剂-A", "cid": "50030", "mw": 206.24},
        {"smiles": "OC(=O)CCCCCCC(=O)O", "name": "ACE抑制剂-B", "cid": "50031", "mw": 174.19},
        {"smiles": "CC(C)NCC(O)COc1ccc(cc1)CC(=O)N", "name": "ACE抑制剂-C", "cid": "50032", "mw": 266.34},
    ],
    "AT1R": [
        {"smiles": "CCCCC1=NC(=C(N1CCC2=CC=CC=C2)C3=CC=CC=C3)C4=CC=CC=C4", "name": "AT1R拮抗剂-A", "cid": "50033", "mw": 380.49},
        {"smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN4CCOCC4", "name": "AT1R拮抗剂-B", "cid": "50034", "mw": 449.90},
    ],
    "ACE2": [
        {"smiles": "OC(=O)C1=CC=C(C=C1)C2=CC=CC=C2", "name": "ACE2调节剂-A", "cid": "50035", "mw": 198.22},
        {"smiles": "CC(=O)NC1=CC=C(C=C1)O", "name": "ACE2调节剂-B", "cid": "50036", "mw": 151.16},
    ],

    # ===== 类风湿关节炎相关靶点的分子 =====
    "TNF-α": [
        {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "TNF-α调节剂-A", "cid": "50040", "mw": 206.24},
        {"smiles": "CC1=CC=C(C=C1)CC(=O)O", "name": "TNF-α调节剂-B", "cid": "50041", "mw": 150.17},
    ],
    "IL-6": [
        {"smiles": "OC1=CC=C(C=C1)C(=O)O", "name": "IL-6调节剂-A", "cid": "50042", "mw": 138.12},
        {"smiles": "CC(=O)NC1=CC=C(C=C1)O", "name": "IL-6调节剂-B", "cid": "50043", "mw": 151.16},
    ],
    "JAK": [
        {"smiles": "CC1=CC2=C(C=C1)N(C3=CC=CC=C3)C=N2", "name": "JAK抑制剂-A", "cid": "50044", "mw": 232.28},
        {"smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1O", "name": "JAK抑制剂-B", "cid": "50045", "mw": 362.77},
    ],

    # ===== 阿尔茨海默病相关靶点的分子 =====
    "AChE": [
        {"smiles": "CCN(CC)CCOC1=CC=CC=C1OC2=CC=CC=C2", "name": "AChE抑制剂-A", "cid": "50050", "mw": 287.36},
        {"smiles": "CC1=CC=C(C=C1)C(=O)NC2=CC=CC=C2", "name": "AChE抑制剂-B", "cid": "50051", "mw": 211.24},
        {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "name": "AChE抑制剂-C", "cid": "2244", "mw": 180.16},
    ],
    "BACE1": [
        {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "BACE1抑制剂-A", "cid": "50052", "mw": 206.24},
        {"smiles": "CN(C)C(=N)N=C(N)N", "name": "BACE1抑制剂-B", "cid": "50053", "mw": 129.16},
    ],
    "Tau": [
        {"smiles": "OC1=CC=C(C=C1)C(=O)O", "name": "Tau调节剂-A", "cid": "50054", "mw": 138.12},
        {"smiles": "CC(=O)NC1=CC=C(C=C1)O", "name": "Tau调节剂-B", "cid": "50055", "mw": 151.16},
    ],
}


class MolScreening(BaseSkill):
    """分子筛选技能

    输入：靶点列表
    输出：针对每个靶点的候选分子列表（含SMILES结构式）
    模拟从PubChem数据库检索相似分子的过程
    """

    def __init__(self):
        super().__init__(
            name="mol_screening",
            description="根据靶点信息从分子数据库中筛选候选药物分子"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有targets字段且是列表"""
        return ("targets" in params
                and isinstance(params["targets"], list)
                and len(params["targets"]) > 0)

    def execute(self, targets: List[Any], **kwargs) -> SkillResult:
        """执行分子筛选（mock版本）

        Args:
            targets: 靶点列表，每个靶点可以是字符串或字典

        Returns:
            SkillResult，data中包含molecules列表和count
        """
        all_molecules: List[Dict[str, Any]] = []
        seen_cids = set()  # 用于去重

        for target in targets:
            # 提取靶点名称（可能是字符串或字典）
            if isinstance(target, dict):
                target_name = target.get("name", "")
            else:
                target_name = str(target)

            # 从mock数据库中获取分子
            mols = MOCK_MOLECULES.get(target_name, [])

            for mol in mols:
                if mol["cid"] not in seen_cids:
                    # 给每个分子添加来源靶点信息
                    mol_copy = dict(mol)
                    mol_copy["target"] = target_name
                    all_molecules.append(mol_copy)
                    seen_cids.add(mol["cid"])

            # 如果mock库里没有，生成一些通用分子
            if not mols:
                for i in range(3):
                    cid = f"GEN_{target_name}_{i}"
                    if cid not in seen_cids:
                        all_molecules.append({
                            "smiles": f"CC({i})CC1=CC=C(C=C1)C(=O)O",
                            "name": f"{target_name}_通用分子_{i+1}",
                            "cid": cid,
                            "mw": round(150 + i * 20, 2),
                            "target": target_name
                        })
                        seen_cids.add(cid)

        # 随机打乱一下顺序（模拟检索结果的随机性）
        random.seed(42)  # 固定随机种子，保证结果可复现
        random.shuffle(all_molecules)

        return SkillResult(
            success=True,
            data={
                "molecules": all_molecules,
                "count": len(all_molecules),
                "targets_covered": len(targets)
            },
            trace_info={
                "skill": self.name,
                "molecule_count": len(all_molecules)
            }
        )
