# ============================================================
# target_extract.py - 靶点提取技能
# 大白话：从论文里"读出"这个疾病有哪些药物靶点
# 这里用mock数据模拟LLM的文本理解能力
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult


# ============================================================
# Mock数据 - 每种疾病的已知药物靶点
# 这些靶点是药学教科书中常见的重要靶点
# ============================================================
MOCK_TARGETS: Dict[str, List[Dict[str, str]]] = {
    "糖尿病": [
        {"name": "GLUT4", "type": "转运蛋白", "description": "葡萄糖转运蛋白4，负责细胞摄取葡萄糖"},
        {"name": "IRS-1", "type": "信号蛋白", "description": "胰岛素受体底物1，传递胰岛素信号"},
        {"name": "AMPK", "type": "激酶", "description": "AMP激活蛋白激酶，细胞能量感受器"},
        {"name": "GLP-1R", "type": "G蛋白偶联受体", "description": "胰高血糖素样肽-1受体"},
        {"name": "PPAR-γ", "type": "核受体", "description": "过氧化物酶体增殖物激活受体γ"}
    ],
    "乳腺癌": [
        {"name": "ERα", "type": "核受体", "description": "雌激素受体α，乳腺癌核心靶点"},
        {"name": "HER2", "type": "受体酪氨酸激酶", "description": "人表皮生长因子受体2"},
        {"name": "CDK4/6", "type": "激酶", "description": "细胞周期蛋白依赖性激酶4/6"},
        {"name": "PI3K", "type": "激酶", "description": "磷脂酰肌醇3-激酶"},
        {"name": "BRCA1", "type": "肿瘤抑制基因", "description": "乳腺癌易感基因1"}
    ],
    "高血压": [
        {"name": "ACE", "type": "酶", "description": "血管紧张素转换酶"},
        {"name": "AT1R", "type": "G蛋白偶联受体", "description": "血管紧张素II 1型受体"},
        {"name": "ACE2", "type": "酶", "description": "血管紧张素转换酶2"},
        {"name": "CACNA1C", "type": "离子通道", "description": "L型钙通道α1亚基"}
    ],
    "类风湿关节炎": [
        {"name": "TNF-α", "type": "细胞因子", "description": "肿瘤坏死因子α，炎症核心因子"},
        {"name": "IL-6", "type": "细胞因子", "description": "白介素6，驱动急性期反应"},
        {"name": "JAK", "type": "激酶", "description": "Janus激酶，炎症信号传导"},
        {"name": "CD20", "type": "膜蛋白", "description": "B细胞表面标志物"}
    ],
    "阿尔茨海默病": [
        {"name": "AChE", "type": "酶", "description": "乙酰胆碱酯酶，降解乙酰胆碱"},
        {"name": "BACE1", "type": "酶", "description": "β-分泌酶1，切割APP产生Aβ"},
        {"name": "Tau", "type": "微管相关蛋白", "description": "Tau蛋白，异常磷酸化导致缠结"},
        {"name": "ApoE4", "type": "脂蛋白", "description": "载脂蛋白E4，AD遗传风险因子"},
        {"name": "NLRP3", "type": "炎症小体", "description": "NLRP3炎症小体，介导神经炎症"}
    ]
}


class TargetExtract(BaseSkill):
    """靶点提取技能

    输入：论文列表（从PubMed检索得到）
    输出：从论文中提取的药物靶点列表
    模拟LLM的文本理解和实体提取能力
    """

    def __init__(self):
        super().__init__(
            name="target_extract",
            description="从科研论文中提取疾病相关的药物靶点信息"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有papers字段且是列表"""
        return ("papers" in params
                and isinstance(params["papers"], list)
                and len(params["papers"]) > 0)

    def execute(self, papers: List[Dict[str, Any]], **kwargs) -> SkillResult:
        """从论文中提取靶点（mock版本，模拟LLM理解论文内容）

        Args:
            papers: 论文列表，每篇论文是一个字典

        Returns:
            SkillResult，data中包含targets列表和count
        """
        # 从论文摘要中"推断"疾病名称
        disease = kwargs.get("disease", "")

        # 尝试从所有论文的标题和摘要中找到疾病关键词
        if not disease:
            all_text = " ".join(
                p.get("title", "") + " " + p.get("abstract", "")
                for p in papers
            )
            for known_disease in MOCK_TARGETS:
                if known_disease in all_text:
                    disease = known_disease
                    break

        # 获取该疾病的靶点
        targets = MOCK_TARGETS.get(disease, [])

        # 如果没匹配到，返回通用靶点
        if not targets:
            targets = [
                {"name": "Target-A", "type": "激酶", "description": "通用激酶靶点"},
                {"name": "Target-B", "type": "受体", "description": "通用受体靶点"},
                {"name": "Target-C", "type": "酶", "description": "通用酶靶点"}
            ]
            disease = disease or "未知疾病"

        return SkillResult(
            success=True,
            data={
                "disease": disease,
                "targets": targets,
                "count": len(targets)
            },
            trace_info={
                "skill": self.name,
                "disease": disease,
                "target_count": len(targets)
            }
        )
