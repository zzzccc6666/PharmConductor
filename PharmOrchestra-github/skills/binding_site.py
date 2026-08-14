# ============================================================
# binding_site.py - 结合位点预测技能
# 大白话：找出靶点蛋白上分子能"卡进去"的那个口袋（结合位点）
# 告诉你这个口袋由哪些氨基酸残基组成、有多大
# 这里用mock数据模拟，真实的需要PDB蛋白结构数据
# ============================================================

from typing import Any, Dict
from skills.base_skill import BaseSkill, SkillResult
import hashlib


# ============================================================
# Mock数据 - 每个靶点蛋白的结合位点信息
# residues: 组成结合位点的氨基酸残基（用三字母代码表示）
# pocket_volume: 结合口袋的体积（立方埃）
# ============================================================
MOCK_BINDING_SITES: Dict[str, Dict[str, Any]] = {
    "GLUT4": {
        "residues": ["GLU380", "GLN311", "ASN317", "PHE383", "ILE164"],
        "pocket_volume": 850.5,
        "pdb_id": "7ZY3",
        "binding_type": "竞争性结合"
    },
    "IRS-1": {
        "residues": ["TYR895", "SER307", "LYS306", "ARG608"],
        "pocket_volume": 720.3,
        "pdb_id": "5U1M",
        "binding_type": "变构调节"
    },
    "AMPK": {
        "residues": ["LYS45", "ASP157", "GLU94", "THR172", "ARG69"],
        "pocket_volume": 980.7,
        "pdb_id": "4CFE",
        "binding_type": "ATP竞争性"
    },
    "GLP-1R": {
        "residues": ["ARG190", "GLU293", "ASN340", "LEU144", "TRP297"],
        "pocket_volume": 1100.2,
        "pdb_id": "6X18",
        "binding_type": "正构位点"
    },
    "PPAR-γ": {
        "residues": ["HIS449", "LEU228", "CYS285", "ARG288", "MET364"],
        "pocket_volume": 1300.0,
        "pdb_id": "3DZY",
        "binding_type": "配体结合域"
    },
    "ERα": {
        "residues": ["ARG394", "GLU353", "HIS524", "LEU387", "MET421"],
        "pocket_volume": 450.8,
        "pdb_id": "1ERE",
        "binding_type": "配体结合域"
    },
    "HER2": {
        "residues": ["LYS753", "MET801", "THR862", "ASP863"],
        "pocket_volume": 650.2,
        "pdb_id": "3PP0",
        "binding_type": "ATP结合口袋"
    },
    "CDK4/6": {
        "residues": ["VAL72", "LYS43", "ASP99", "GLU144", "HIS95"],
        "pocket_volume": 580.6,
        "pdb_id": "2W99",
        "binding_type": "ATP竞争性"
    },
    "PI3K": {
        "residues": ["LYS833", "ASP841", "TYR867", "MET953"],
        "pocket_volume": 730.4,
        "pdb_id": "1E7V",
        "binding_type": "ATP结合口袋"
    },
    "ACE": {
        "residues": ["HIS383", "GLU384", "LYS511", "TYR523", "ALA354"],
        "pocket_volume": 620.1,
        "pdb_id": "1O8A",
        "binding_type": "活性位点"
    },
    "AT1R": {
        "residues": ["ARG167", "TYR35", "PHE182", "ASN295"],
        "pocket_volume": 890.3,
        "pdb_id": "4YAY",
        "binding_type": "跨膜结合口袋"
    },
    "TNF-α": {
        "residues": ["TYR59", "TYR119", "GLY121", "LEU94"],
        "pocket_volume": 550.7,
        "pdb_id": "2AZ5",
        "binding_type": "蛋白-蛋白界面"
    },
    "JAK": {
        "residues": ["LYY908", "GLY909", "LEU905", "ASP994"],
        "pocket_volume": 670.8,
        "pdb_id": "3FUP",
        "binding_type": "ATP结合口袋"
    },
    "AChE": {
        "residues": ["SER203", "HIS447", "GLU334", "TRP86", "PHE295"],
        "pocket_volume": 520.4,
        "pdb_id": "1EVE",
        "binding_type": "催化三联体"
    },
    "BACE1": {
        "residues": ["ASP32", "ASP228", "GLY11", "TYR71", "LYY198"],
        "pocket_volume": 780.9,
        "pdb_id": "1FKN",
        "binding_type": "催化天冬氨酸"
    },
    "Tau": {
        "residues": ["LYS280", "SER262", "SER356", "PRO301"],
        "pocket_volume": 420.5,
        "pdb_id": "2MZ7",
        "binding_type": "微管结合域"
    }
}


class BindingSite(BaseSkill):
    """结合位点预测技能

    输入：靶点名称
    输出：靶点蛋白上的结合位点信息（残基列表、口袋体积等）
    模拟从PDB数据库获取蛋白结构并预测结合位点的过程
    """

    def __init__(self):
        super().__init__(
            name="binding_site",
            description="预测靶点蛋白上的药物结合位点信息"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有target字段"""
        return "target" in params and isinstance(params["target"], str) and len(params["target"]) > 0

    def execute(self, target: str, **kwargs) -> SkillResult:
        """执行结合位点预测（mock版本）

        Args:
            target: 靶点名称

        Returns:
            SkillResult，data中包含结合位点信息
        """
        # 从mock数据中获取
        site_info = MOCK_BINDING_SITES.get(target)

        if not site_info:
            # 如果没有找到，生成通用的结合位点信息
            key = hashlib.md5(target.encode()).hexdigest()
            num = int(key[:4], 16)
            site_info = {
                "residues": [f"RES{num % 500}", f"RES{(num + 50) % 500}",
                             f"RES{(num + 100) % 500}", f"RES{(num + 150) % 500}"],
                "pocket_volume": round(400 + (num % 800), 1),
                "pdb_id": f"MOCK_{num}",
                "binding_type": "预测结合位点"
            }

        # 补充一些额外信息
        result_data = {
            "target": target,
            "residues": site_info["residues"],
            "residue_count": len(site_info["residues"]),
            "pocket_volume": site_info["pocket_volume"],
            "pdb_id": site_info["pdb_id"],
            "binding_type": site_info.get("binding_type", "未知"),
            "druggability": round(0.6 + (site_info["pocket_volume"] / 2000), 2)  # 可成药性评分
        }

        return SkillResult(
            success=True,
            data=result_data,
            trace_info={
                "skill": self.name,
                "target": target,
                "residue_count": len(site_info["residues"])
            }
        )
