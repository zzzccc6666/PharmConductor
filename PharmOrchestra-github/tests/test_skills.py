# ============================================================
# test_skills.py - 7个技能的基本单元测试
# 大白话：这些测试就是检查每个技能能不能正常工作
# 运行方式: cd PharmOrchestra && python -m pytest tests/test_skills.py -v
# 或者直接: python -m pytest tests/ -v
# ============================================================

import sys
import os

# 把项目根目录加到路径里，确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.base_skill import SkillResult
from skills.pubmed_search import PubMedSearch
from skills.target_extract import TargetExtract
from skills.mol_screening import MolScreening
from skills.docking_score import DockingScore
from skills.binding_site import BindingSite
from skills.tox_predict import ToxPredict
from skills.admet_analysis import ADMETAnalysis


# ============================================================
# 1. PubMedSearch 测试
# ============================================================
class TestPubMedSearch:
    """测试PubMed文献检索技能"""

    def setup_method(self):
        """每个测试前创建一个技能实例"""
        self.skill = PubMedSearch()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "pubmed_search"
        assert "description" in info

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        assert self.skill.validate_params({"disease": "糖尿病"}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"disease": ""}) is False
        assert self.skill.validate_params({"disease": 123}) is False

    def test_execute_diabetes(self):
        """测试执行 - 糖尿病"""
        result = self.skill.run({"disease": "糖尿病"})
        assert result.success is True
        assert result.data["count"] > 0
        assert "papers" in result.data
        assert len(result.data["papers"]) >= 3  # 至少3篇论文

    def test_execute_breast_cancer(self):
        """测试执行 - 乳腺癌"""
        result = self.skill.run({"disease": "乳腺癌"})
        assert result.success is True
        assert result.data["count"] >= 3

    def test_execute_unknown_disease(self):
        """测试执行 - 未知疾病（应该返回默认结果）"""
        result = self.skill.run({"disease": "未知疾病XYZ"})
        assert result.success is True
        assert result.data["count"] >= 2  # 至少返回默认结果

    def test_execution_time(self):
        """测试执行时间是否被记录"""
        result = self.skill.run({"disease": "糖尿病"})
        assert result.execution_time_ms >= 0

    def test_execute_hypertension(self):
        """测试执行 - 高血压"""
        result = self.skill.run({"disease": "高血压"})
        assert result.success is True
        assert result.data["count"] >= 3

    def test_paper_structure(self):
        """测试论文数据结构是否完整"""
        result = self.skill.run({"disease": "糖尿病"})
        for paper in result.data["papers"]:
            assert "title" in paper
            assert "abstract" in paper

    def test_count_matches_papers(self):
        """测试count字段与papers列表长度一致"""
        result = self.skill.run({"disease": "乳腺癌"})
        assert result.data["count"] == len(result.data["papers"])


# ============================================================
# 2. TargetExtract 测试
# ============================================================
class TestTargetExtract:
    """测试靶点提取技能"""

    def setup_method(self):
        self.skill = TargetExtract()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "target_extract"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        papers = [{"title": "test", "abstract": "test"}]
        assert self.skill.validate_params({"papers": papers}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"papers": []}) is False
        assert self.skill.validate_params({"papers": "not_a_list"}) is False

    def test_execute_diabetes(self):
        """测试执行 - 从糖尿病论文提取靶点"""
        papers = [
            {"title": "GLUT4在糖尿病中的作用", "abstract": "GLUT4转运蛋白..."},
            {"title": "AMPK与糖尿病", "abstract": "AMPK激活..."}
        ]
        result = self.skill.run({"papers": papers, "disease": "糖尿病"})
        assert result.success is True
        assert result.data["count"] >= 3  # 至少3个靶点
        assert "targets" in result.data

    def test_execute_breast_cancer(self):
        """测试执行 - 乳腺癌靶点"""
        papers = [{"title": "ERα in breast cancer", "abstract": "乳腺癌ERα..."}]
        result = self.skill.run({"papers": papers, "disease": "乳腺癌"})
        assert result.success is True
        assert result.data["count"] >= 3

    def test_target_structure(self):
        """测试靶点数据结构是否正确"""
        papers = [{"title": "糖尿病研究", "abstract": "..."}]
        result = self.skill.run({"papers": papers, "disease": "糖尿病"})
        targets = result.data["targets"]
        for t in targets:
            assert "name" in t
            assert "type" in t
            assert "description" in t

    def test_execute_hypertension(self):
        """测试执行 - 高血压靶点"""
        papers = [{"title": "ACE与高血压", "abstract": "血管紧张素转换酶..."}]
        result = self.skill.run({"papers": papers, "disease": "高血压"})
        assert result.success is True
        assert result.data["count"] >= 3

    def test_target_types_valid(self):
        """测试靶点类型字段值合法"""
        papers = [{"title": "糖尿病研究", "abstract": "..."}]
        result = self.skill.run({"papers": papers, "disease": "糖尿病"})
        for t in result.data["targets"]:
            assert t["type"]  # 非空

    def test_empty_abstract(self):
        """测试空摘要论文的容错处理"""
        papers = [{"title": "test", "abstract": ""}]
        result = self.skill.run({"papers": papers, "disease": "糖尿病"})
        assert result.success is True

    def test_target_count_reasonable(self):
        """测试靶点数量在合理范围内"""
        papers = [{"title": "糖尿病研究", "abstract": "..."}]
        result = self.skill.run({"papers": papers, "disease": "糖尿病"})
        assert 3 <= result.data["count"] <= 20


# ============================================================
# 3. MolScreening 测试
# ============================================================
class TestMolScreening:
    """测试分子筛选技能"""

    def setup_method(self):
        self.skill = MolScreening()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "mol_screening"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        assert self.skill.validate_params({"targets": ["GLUT4", "AMPK"]}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"targets": []}) is False

    def test_execute_with_known_targets(self):
        """测试执行 - 已知靶点"""
        targets = [
            {"name": "GLUT4", "type": "转运蛋白", "description": "葡萄糖转运蛋白"},
            {"name": "AMPK", "type": "激酶", "description": "能量感受器"}
        ]
        result = self.skill.run({"targets": targets})
        assert result.success is True
        assert result.data["count"] >= 5  # 至少5个分子
        assert "molecules" in result.data

    def test_molecule_structure(self):
        """测试分子数据结构是否正确"""
        targets = [{"name": "AMPK", "type": "激酶", "description": "test"}]
        result = self.skill.run({"targets": targets})
        molecules = result.data["molecules"]
        for mol in molecules:
            assert "smiles" in mol
            assert "name" in mol
            assert "cid" in mol
            assert "target" in mol

    def test_deduplication(self):
        """测试分子去重（同一个cid不应该出现两次）"""
        targets = [
            {"name": "GLUT4", "type": "转运蛋白", "description": "test"},
            {"name": "AMPK", "type": "激酶", "description": "test"}
        ]
        result = self.skill.run({"targets": targets})
        cids = [mol["cid"] for mol in result.data["molecules"]]
        assert len(cids) == len(set(cids))  # 没有重复

    def test_execute_single_target(self):
        """测试执行 - 单靶点"""
        targets = [{"name": "GLUT4", "type": "转运蛋白", "description": "test"}]
        result = self.skill.run({"targets": targets})
        assert result.success is True
        assert result.data["count"] >= 3

    def test_molecule_has_smiles(self):
        """测试所有分子都有SMILES字符串"""
        targets = [{"name": "AMPK", "type": "激酶", "description": "test"}]
        result = self.skill.run({"targets": targets})
        for mol in result.data["molecules"]:
            assert isinstance(mol["smiles"], str)
            assert len(mol["smiles"]) > 0

    def test_target_assignment(self):
        """测试每个分子都关联了靶点"""
        targets = [
            {"name": "GLUT4", "type": "转运蛋白", "description": "test"},
            {"name": "AMPK", "type": "激酶", "description": "test"}
        ]
        result = self.skill.run({"targets": targets})
        for mol in result.data["molecules"]:
            assert mol["target"] in ["GLUT4", "AMPK"]

    def test_count_matches_molecules(self):
        """测试count字段与molecules列表长度一致"""
        targets = [{"name": "GLUT4", "type": "转运蛋白", "description": "test"}]
        result = self.skill.run({"targets": targets})
        assert result.data["count"] == len(result.data["molecules"])


# ============================================================
# 4. DockingScore 测试
# ============================================================
class TestDockingScore:
    """测试分子对接打分技能"""

    def setup_method(self):
        self.skill = DockingScore()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "docking_score"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        mols = [{"smiles": "CC(=O)O", "name": "test"}]
        assert self.skill.validate_params({"molecules": mols, "target": "GLUT4"}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({"molecules": [], "target": "X"}) is False
        assert self.skill.validate_params({"target": "X"}) is False
        assert self.skill.validate_params({"molecules": [{}]}) is False

    def test_execute_scoring(self):
        """测试执行 - 对接打分"""
        molecules = [
            {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "name": "阿司匹林", "cid": "2244"},
            {"smiles": "CN(C)C(=N)N=C(N)N", "name": "二甲双胍", "cid": "4091"},
            {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "布洛芬", "cid": "3672"}
        ]
        result = self.skill.run({"molecules": molecules, "target": "GLUT4"})
        assert result.success is True
        assert result.data["count"] == 3
        assert "scored_molecules" in result.data

    def test_score_range(self):
        """测试分数范围是否在0.5-0.95之间"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1"},
            {"smiles": "CCN", "name": "mol2", "cid": "2"},
            {"smiles": "CCC", "name": "mol3", "cid": "3"}
        ]
        result = self.skill.run({"molecules": molecules, "target": "AMPK"})
        for mol in result.data["scored_molecules"]:
            score = mol["docking_score"]
            assert 0.5 <= score <= 0.95

    def test_score_consistency(self):
        """测试相同输入得到相同结果（确定性）"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        result1 = self.skill.run({"molecules": molecules, "target": "GLUT4"})
        result2 = self.skill.run({"molecules": molecules, "target": "GLUT4"})
        score1 = result1.data["scored_molecules"][0]["docking_score"]
        score2 = result2.data["scored_molecules"][0]["docking_score"]
        assert score1 == score2

    def test_sorted_by_score(self):
        """测试结果是否按分数从高到低排序"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1"},
            {"smiles": "CCN", "name": "mol2", "cid": "2"},
            {"smiles": "CCC", "name": "mol3", "cid": "3"},
            {"smiles": "CCCC", "name": "mol4", "cid": "4"}
        ]
        result = self.skill.run({"molecules": molecules, "target": "AMPK"})
        scores = [m["docking_score"] for m in result.data["scored_molecules"]]
        assert scores == sorted(scores, reverse=True)

    def test_molecule_names_preserved(self):
        """测试输出保留了输入分子的名称"""
        molecules = [{"smiles": "CC(=O)O", "name": "测试分子", "cid": "1"}]
        result = self.skill.run({"molecules": molecules, "target": "GLUT4"})
        assert result.data["scored_molecules"][0]["name"] == "测试分子"

    def test_all_molecules_scored(self):
        """测试所有输入分子都被打分"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1"},
            {"smiles": "CCN", "name": "mol2", "cid": "2"},
            {"smiles": "CCC", "name": "mol3", "cid": "3"}
        ]
        result = self.skill.run({"molecules": molecules, "target": "AMPK"})
        assert len(result.data["scored_molecules"]) == 3

    def test_docking_score_field_exists(self):
        """测试打分结果包含docking_score字段"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        result = self.skill.run({"molecules": molecules, "target": "GLUT4"})
        assert "docking_score" in result.data["scored_molecules"][0]


# ============================================================
# 5. BindingSite 测试
# ============================================================
class TestBindingSite:
    """测试结合位点预测技能"""

    def setup_method(self):
        self.skill = BindingSite()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "binding_site"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        assert self.skill.validate_params({"target": "GLUT4"}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"target": ""}) is False
        assert self.skill.validate_params({"target": 123}) is False

    def test_execute_known_target(self):
        """测试执行 - 已知靶点"""
        result = self.skill.run({"target": "GLUT4"})
        assert result.success is True
        assert "residues" in result.data
        assert "pocket_volume" in result.data
        assert "pdb_id" in result.data
        assert len(result.data["residues"]) > 0

    def test_execute_unknown_target(self):
        """测试执行 - 未知靶点（应该返回默认结果）"""
        result = self.skill.run({"target": "UNKNOWN_TARGET_XYZ"})
        assert result.success is True
        assert "residues" in result.data
        assert len(result.data["residues"]) > 0

    def test_binding_type(self):
        """测试结合类型字段存在"""
        result = self.skill.run({"target": "AMPK"})
        assert "binding_type" in result.data
        assert "druggability" in result.data

    def test_pdb_id_format(self):
        """测试PDB ID格式合法（4字符）"""
        result = self.skill.run({"target": "GLUT4"})
        pdb_id = result.data["pdb_id"]
        assert len(pdb_id) == 4
        assert pdb_id[0].isdigit()  # PDB ID 首位通常为数字

    def test_pocket_volume_positive(self):
        """测试口袋体积为正值"""
        result = self.skill.run({"target": "AMPK"})
        assert result.data["pocket_volume"] > 0

    def test_druggability_valid(self):
        """测试可成药性值为合法数值"""
        result = self.skill.run({"target": "GLUT4"})
        assert isinstance(result.data["druggability"], (int, float))
        assert result.data["druggability"] > 0

    def test_multiple_targets(self):
        """测试多个不同靶点的结果不重复"""
        r1 = self.skill.run({"target": "GLUT4"})
        r2 = self.skill.run({"target": "AMPK"})
        assert r1.data["pdb_id"] != r2.data["pdb_id"]


# ============================================================
# 6. ToxPredict 测试
# ============================================================
class TestToxPredict:
    """测试毒性预测技能"""

    def setup_method(self):
        self.skill = ToxPredict()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "tox_predict"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        mols = [{"smiles": "CC(=O)O", "name": "test"}]
        assert self.skill.validate_params({"molecules": mols}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"molecules": []}) is False

    def test_execute_prediction(self):
        """测试执行 - 毒性预测"""
        molecules = [
            {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "name": "阿司匹林", "cid": "2244"},
            {"smiles": "CN(C)C(=N)N=C(N)N", "name": "二甲双胍", "cid": "4091"},
            {"smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "name": "布洛芬", "cid": "3672"}
        ]
        result = self.skill.run({"molecules": molecules})
        assert result.success is True
        assert result.data["count"] == 3
        assert "toxicity_results" in result.data
        assert "risk_distribution" in result.data

    def test_risk_level_valid(self):
        """测试风险等级值是否合法"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        result = self.skill.run({"molecules": molecules})
        for mol in result.data["toxicity_results"]:
            level = mol["toxicity"]["risk_level"]
            assert level in ["low", "medium", "high"]

    def test_tox_score_range(self):
        """测试毒性分数范围"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1"},
            {"smiles": "CCN", "name": "mol2", "cid": "2"}
        ]
        result = self.skill.run({"molecules": molecules})
        for mol in result.data["toxicity_results"]:
            score = mol["toxicity"]["tox_score"]
            assert 0.0 <= score <= 1.0

    def test_consistency(self):
        """测试相同输入得到相同结果"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        r1 = self.skill.run({"molecules": molecules})
        r2 = self.skill.run({"molecules": molecules})
        assert r1.data["toxicity_results"][0]["toxicity"]["risk_level"] == \
               r2.data["toxicity_results"][0]["toxicity"]["risk_level"]

    def test_risk_distribution_exists(self):
        """测试风险分布统计存在"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        result = self.skill.run({"molecules": molecules})
        assert "risk_distribution" in result.data
        assert "low" in result.data["risk_distribution"]

    def test_all_molecules_have_toxicity(self):
        """测试所有分子都有毒性结果"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1"},
            {"smiles": "CCN", "name": "mol2", "cid": "2"}
        ]
        result = self.skill.run({"molecules": molecules})
        assert len(result.data["toxicity_results"]) == 2

    def test_count_matches_results(self):
        """测试count字段与toxicity_results长度一致"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1"}]
        result = self.skill.run({"molecules": molecules})
        assert result.data["count"] == len(result.data["toxicity_results"])


# ============================================================
# 7. ADMETAnalysis 测试
# ============================================================
class TestADMETAnalysis:
    """测试ADMET参数分析技能"""

    def setup_method(self):
        self.skill = ADMETAnalysis()

    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        assert info["name"] == "admet_analysis"

    def test_validate_params_valid(self):
        """测试参数验证 - 合法参数"""
        mols = [{"smiles": "CC(=O)O", "name": "test", "mw": 60.0}]
        assert self.skill.validate_params({"molecules": mols}) is True

    def test_validate_params_invalid(self):
        """测试参数验证 - 非法参数"""
        assert self.skill.validate_params({}) is False
        assert self.skill.validate_params({"molecules": []}) is False

    def test_execute_analysis(self):
        """测试执行 - ADMET分析"""
        molecules = [
            {"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "name": "阿司匹林", "cid": "2244", "mw": 180.16},
            {"smiles": "CN(C)C(=N)N=C(N)N", "name": "二甲双胍", "cid": "4091", "mw": 129.16}
        ]
        result = self.skill.run({"molecules": molecules})
        assert result.success is True
        assert result.data["count"] == 2
        assert "admet_results" in result.data

    def test_admet_fields(self):
        """测试ADMET参数字段是否完整"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1", "mw": 60.0}]
        result = self.skill.run({"molecules": molecules})
        admet = result.data["admet_results"][0]["admet"]

        # 检查关键字段是否存在
        assert "logp" in admet           # 脂水分配系数
        assert "solubility" in admet      # 溶解度
        assert "oral_bioavailability" in admet  # 口服生物利用度
        assert "bbb_penetration" in admet       # 血脑屏障穿透性
        assert "half_life" in admet             # 半衰期
        assert "admet_score" in admet           # 综合ADMET评分

    def test_admet_score_range(self):
        """测试ADMET评分范围"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1", "mw": 60.0},
            {"smiles": "CCN", "name": "mol2", "cid": "2", "mw": 45.0}
        ]
        result = self.skill.run({"molecules": molecules})
        for mol in result.data["admet_results"]:
            score = mol["admet"]["admet_score"]
            assert 0.0 <= score <= 1.0

    def test_bbb_valid_values(self):
        """测试血脑屏障穿透性值是否合法"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1", "mw": 60.0}]
        result = self.skill.run({"molecules": molecules})
        bbb = result.data["admet_results"][0]["admet"]["bbb_penetration"]
        assert bbb in ["高", "中", "低"]

    def test_all_molecules_have_admet(self):
        """测试所有分子都有ADMET结果"""
        molecules = [
            {"smiles": "CC(=O)O", "name": "mol1", "cid": "1", "mw": 60.0},
            {"smiles": "CCN", "name": "mol2", "cid": "2", "mw": 45.0}
        ]
        result = self.skill.run({"molecules": molecules})
        assert len(result.data["admet_results"]) == 2

    def test_logp_range(self):
        """测试logP值在合理范围内"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1", "mw": 60.0}]
        result = self.skill.run({"molecules": molecules})
        logp = result.data["admet_results"][0]["admet"]["logp"]
        assert -5 <= logp <= 10  # 合理的logP范围

    def test_count_matches_admet(self):
        """测试count字段与admet_results长度一致"""
        molecules = [{"smiles": "CC(=O)O", "name": "test", "cid": "1", "mw": 60.0}]
        result = self.skill.run({"molecules": molecules})
        assert result.data["count"] == len(result.data["admet_results"])
