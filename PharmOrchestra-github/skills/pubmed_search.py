# ============================================================
# pubmed_search.py - PubMed文献检索技能
# 大白话：在PubMed上搜关于某个疾病的科研论文
# 这里用mock数据模拟，不需要真实的API
# ============================================================

from typing import Any, Dict, List
from skills.base_skill import BaseSkill, SkillResult


# ============================================================
# Mock数据 - 模拟5种疾病的PubMed检索结果
# 每篇论文包含：PMID（论文ID）、标题、摘要、年份
# ============================================================
MOCK_PAPERS: Dict[str, List[Dict[str, Any]]] = {
    "糖尿病": [
        {
            "pmid": "32845671",
            "title": "GLUT4转运蛋白在2型糖尿病中的调控机制研究",
            "abstract": "本研究探讨了GLUT4葡萄糖转运蛋白在胰岛素抵抗中的关键作用...",
            "year": 2023
        },
        {
            "pmid": "32845672",
            "title": "AMPK信号通路激活：糖尿病治疗的新策略",
            "abstract": "AMPK是细胞能量感受器，其激活可改善葡萄糖代谢...",
            "year": 2023
        },
        {
            "pmid": "32845673",
            "title": "IRS-1磷酸化异常与胰岛素信号传导缺陷",
            "abstract": "胰岛素受体底物1(IRS-1)的异常磷酸化是糖尿病的核心机制...",
            "year": 2022
        },
        {
            "pmid": "32845674",
            "title": "二甲双胍多靶点作用机制的系统药理学分析",
            "abstract": "二甲双胍通过AMPK依赖和非依赖途径发挥降糖作用...",
            "year": 2024
        },
        {
            "pmid": "32845675",
            "title": "GLP-1受体激动剂在糖尿病治疗中的进展",
            "abstract": "GLP-1R激动剂不仅降糖，还具有心血管保护作用...",
            "year": 2024
        }
    ],
    "乳腺癌": [
        {
            "pmid": "33845671",
            "title": "雌激素受体α(ERα)在乳腺癌内分泌治疗中的作用",
            "abstract": "ERα是乳腺癌最重要的治疗靶点之一...",
            "year": 2023
        },
        {
            "pmid": "33845672",
            "title": "HER2阳性乳腺癌的靶向治疗进展",
            "abstract": "HER2过表达驱动乳腺癌恶性进展，靶向HER2的药物显著改善预后...",
            "year": 2023
        },
        {
            "pmid": "33845673",
            "title": "CDK4/6抑制剂联合内分泌治疗的临床疗效",
            "abstract": "CDK4/6是细胞周期关键调控因子，其抑制剂已改变HR+乳腺癌治疗格局...",
            "year": 2024
        },
        {
            "pmid": "33845674",
            "title": "PI3K/AKT/mTOR通路在乳腺癌耐药中的角色",
            "abstract": "PI3K通路异常激活是内分泌治疗耐药的重要机制...",
            "year": 2022
        },
        {
            "pmid": "33845675",
            "title": "BRCA1突变与三阴性乳腺癌的治疗策略",
            "abstract": "BRCA1突变导致DNA修复缺陷，PARP抑制剂对此类乳腺癌有效...",
            "year": 2024
        }
    ],
    "高血压": [
        {
            "pmid": "34845671",
            "title": "血管紧张素转换酶(ACE)抑制剂的高血压治疗机制",
            "abstract": "ACE抑制剂通过抑制血管紧张素II生成来降低血压...",
            "year": 2023
        },
        {
            "pmid": "34845672",
            "title": "AT1受体拮抗剂的降压效果与靶器官保护",
            "abstract": "血管紧张素II 1型受体(AT1R)拮抗剂是一线降压药物...",
            "year": 2023
        },
        {
            "pmid": "34845673",
            "title": "ACE2在肾素-血管紧张素系统中的保护作用",
            "abstract": "ACE2将血管紧张素II转化为保护性的Ang-(1-7)...",
            "year": 2024
        },
        {
            "pmid": "34845674",
            "title": "钙通道阻滞剂的降压机制与临床应用",
            "abstract": "L型钙通道阻滞剂通过舒张血管平滑肌降低血压...",
            "year": 2022
        }
    ],
    "类风湿关节炎": [
        {
            "pmid": "35845671",
            "title": "TNF-α抑制剂在类风湿关节炎治疗中的里程碑意义",
            "abstract": "肿瘤坏死因子α(TNF-α)是RA炎症级联反应的核心因子...",
            "year": 2023
        },
        {
            "pmid": "35845672",
            "title": "IL-6信号通路与类风湿关节炎关节破坏",
            "abstract": "白介素6(IL-6)驱动RA的急性期反应和关节破坏...",
            "year": 2023
        },
        {
            "pmid": "35845673",
            "title": "JAK抑制剂：类风湿关节炎治疗的新选择",
            "abstract": "JAK-STAT通路是多种炎症因子的共同下游信号...",
            "year": 2024
        },
        {
            "pmid": "35845674",
            "title": "B细胞清除疗法在难治性RA中的应用",
            "abstract": "CD20靶向清除B细胞可改善难治性RA症状...",
            "year": 2022
        }
    ],
    "阿尔茨海默病": [
        {
            "pmid": "36845671",
            "title": "乙酰胆碱酯酶(AChE)抑制剂在AD中的胆碱能假说",
            "abstract": "AChE抑制剂通过增加脑内乙酰胆碱改善认知功能...",
            "year": 2023
        },
        {
            "pmid": "36845672",
            "title": "BACE1抑制剂与淀粉样蛋白假说的兴衰",
            "abstract": "BACE1切割APP产生Aβ，是AD药物开发的重要靶点...",
            "year": 2023
        },
        {
            "pmid": "36845673",
            "title": "Tau蛋白过度磷酸化与神经纤维缠结",
            "abstract": "Tau异常磷酸化形成神经纤维缠结，导致神经元死亡...",
            "year": 2024
        },
        {
            "pmid": "36845674",
            "title": "ApoE4基因变异与阿尔茨海默病风险",
            "abstract": "ApoE4是AD最强的遗传风险因子，影响Aβ清除...",
            "year": 2024
        },
        {
            "pmid": "36845675",
            "title": "神经炎症在阿尔茨海默病中的双重角色",
            "abstract": "小胶质细胞介导的神经炎症在AD进展中起重要作用...",
            "year": 2023
        }
    ]
}


class PubMedSearch(BaseSkill):
    """PubMed文献检索技能

    输入：疾病名称（中文或英文）
    输出：相关的科研论文列表
    """

    def __init__(self):
        super().__init__(
            name="pubmed_search",
            description="检索PubMed数据库中与指定疾病相关的科研论文"
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数：必须有disease字段且不为空"""
        return "disease" in params and isinstance(params["disease"], str) and len(params["disease"]) > 0

    def execute(self, disease: str, **kwargs) -> SkillResult:
        """执行PubMed检索（mock版本）

        Args:
            disease: 疾病名称，比如"糖尿病"

        Returns:
            SkillResult，data中包含papers列表和count
        """
        # 尝试从mock数据中获取
        papers = MOCK_PAPERS.get(disease, [])

        # 如果没找到精确匹配，尝试模糊匹配
        if not papers:
            for key, val in MOCK_PAPERS.items():
                if disease in key or key in disease:
                    papers = val
                    break

        # 如果还是没找到，返回通用结果
        if not papers:
            papers = [
                {
                    "pmid": "00000001",
                    "title": f"关于{disease}的综合性研究",
                    "abstract": f"本文综述了{disease}的病理机制和潜在治疗靶点...",
                    "year": 2023
                },
                {
                    "pmid": "00000002",
                    "title": f"{disease}的分子机制与药物开发",
                    "abstract": f"本研究分析了{disease}的关键信号通路...",
                    "year": 2024
                },
                {
                    "pmid": "00000003",
                    "title": f"{disease}治疗的新兴靶点",
                    "abstract": f"探讨了{disease}治疗中具有潜力的新靶点...",
                    "year": 2024
                }
            ]

        return SkillResult(
            success=True,
            data={
                "disease": disease,
                "papers": papers,
                "count": len(papers)
            },
            trace_info={"skill": self.name, "paper_count": len(papers)}
        )
