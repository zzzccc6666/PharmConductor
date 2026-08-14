# ============================================================
# test_integration.py - 端到端集成测试
# 大白话：这不是测试单个零件，而是测试"整台机器"能不能跑通
# 证明：输入一个疾病名 -> 4个Agent接力工作 -> 输出安全候选分子
# ============================================================

import pytest
from utils.matrix import MatrixBus
from utils.trace import TraceLogger
from agents.manager import ManagerAgent


# ============================================================
# 测试夹具：每次测试都创建一个全新的环境
# ============================================================
@pytest.fixture
def pipeline():
    """创建一个全新的Manager + 消息总线 + 日志记录器"""
    bus = MatrixBus()
    trace = TraceLogger()
    manager = ManagerAgent(bus, trace)
    return manager, bus, trace


# ============================================================
# 1. 端到端流程测试：5种疾病全部跑通
# ============================================================
class TestEndToEndPipeline:
    """端到端流程测试 - 验证从疾病名称到候选分子的完整链路"""

    DISEASES = ["糖尿病", "乳腺癌", "高血压", "类风湿关节炎", "阿尔茨海默病"]

    @pytest.mark.parametrize("disease", DISEASES)
    def test_pipeline_success(self, pipeline, disease):
        """每种疾病都能端到端跑通"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline(disease)

        assert result["success"] is True, f"{disease}流程应该成功"
        assert result["disease"] == disease
        assert result["error"] is None

    @pytest.mark.parametrize("disease", DISEASES)
    def test_pipeline_produces_safe_molecules(self, pipeline, disease):
        """每种疾病都能产出安全候选分子"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline(disease)

        safe_mols = result["data"].get("safe_molecules", [])
        assert len(safe_mols) > 0, f"{disease}应该至少有1个安全分子"
        assert len(safe_mols) >= 5, f"{disease}安全分子应>=5个（质量门控要求）"

    @pytest.mark.parametrize("disease", DISEASES)
    def test_pipeline_finds_targets(self, pipeline, disease):
        """每种疾病都能发现药物靶点"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline(disease)

        targets = result["data"]["pipeline_summary"]["targets_found"]
        assert len(targets) >= 3, f"{disease}靶点数应>=3（Scout质量门控）"

    @pytest.mark.parametrize("disease", DISEASES)
    def test_pipeline_finds_papers(self, pipeline, disease):
        """每种疾病都能检索到文献"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline(disease)

        papers = result["data"]["pipeline_summary"]["papers_found"]
        assert papers >= 3, f"{disease}论文数应>=3"


# ============================================================
# 2. 消息总线测试：Agent间通信可追溯
# ============================================================
class TestMessageBus:
    """验证MatrixBus消息总线的通信记录完整性"""

    def test_all_messages_recorded(self, pipeline):
        """所有Agent间的消息都被完整记录"""
        manager, bus, trace = pipeline
        manager.run_pipeline("糖尿病")

        # Manager给4个Worker各发1条task = 4条
        # 4个Worker各给Manager回1条result = 4条
        # 合计至少8条消息
        assert bus.message_count() >= 8, "消息总数应>=8条"

    def test_messages_have_trace_id(self, pipeline):
        """所有消息都携带trace_id，可追溯"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")
        trace_id = result["trace_id"]

        messages = bus.get_messages_by_trace(trace_id)
        assert len(messages) >= 8, "通过trace_id应能查到所有消息"
        for msg in messages:
            assert msg.trace_id == trace_id

    def test_message_flow_correct(self, pipeline):
        """消息流向正确：Manager -> Worker -> Manager"""
        manager, bus, trace = pipeline
        manager.run_pipeline("糖尿病")

        all_msgs = bus.get_all_messages()
        # 应该有Manager发给Scout的task
        scout_tasks = [m for m in all_msgs if m.target == "Scout" and m.msg_type == "task"]
        assert len(scout_tasks) >= 1, "应有Manager发给Scout的任务"

        # 应该有Safety发给Manager的result
        safety_results = [m for m in all_msgs if m.source == "Safety" and m.msg_type == "result"]
        assert len(safety_results) >= 1, "应有Safety发给Manager的结果"

    def test_all_agents_registered(self, pipeline):
        """所有5个Agent都在消息总线上注册了"""
        manager, bus, trace = pipeline
        manager.run_pipeline("糖尿病")

        expected_agents = {"Manager", "Scout", "Screener", "Mechanism", "Safety"}
        for agent in expected_agents:
            assert agent in bus._queues, f"{agent}应该在消息总线上注册"


# ============================================================
# 3. 日志追踪测试：每一步操作都有记录
# ============================================================
class TestTraceLogger:
    """验证TraceLogger日志记录的完整性"""

    def test_logs_cover_all_agents(self, pipeline):
        """日志覆盖所有5个Agent"""
        manager, bus, trace = pipeline
        manager.run_pipeline("糖尿病")

        summary = trace.summary()
        agents = set(summary["agents_involved"])
        expected = {"Manager", "Scout", "Screener", "Mechanism", "Safety"}
        assert expected.issubset(agents), f"日志应覆盖所有Agent，实际: {agents}"

    def test_logs_have_pipeline_start_and_done(self, pipeline):
        """日志包含流程开始和结束标记"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")
        trace_id = result["trace_id"]

        logs = trace.get_logs_by_trace(trace_id)
        actions = [l["action"] for l in logs]

        assert "pipeline_start" in actions, "应有流程开始日志"
        assert "pipeline_done" in actions, "应有流程结束日志"

    def test_logs_have_dispatch_records(self, pipeline):
        """日志包含4次任务分派记录"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")
        trace_id = result["trace_id"]

        logs = trace.get_logs_by_trace(trace_id)
        dispatches = [l for l in logs if l["action"] == "dispatch"]
        assert len(dispatches) >= 4, "应有4次任务分派记录"

    def test_logs_have_skill_executions(self, pipeline):
        """日志包含所有7个Skill的执行记录"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")
        trace_id = result["trace_id"]

        logs = trace.get_logs_by_trace(trace_id)
        skill_starts = [l for l in logs if l["action"] == "skill_start"]
        skill_names = set(l["detail"].replace("执行技能: ", "") for l in skill_starts)

        expected_skills = {
            "pubmed_search", "target_extract", "mol_screening",
            "binding_site", "docking_score", "tox_predict", "admet_analysis"
        }
        assert expected_skills.issubset(skill_names), \
            f"所有7个Skill都应有执行记录，实际: {skill_names}"

    def test_log_count_reasonable(self, pipeline):
        """日志总数合理（至少40条）"""
        manager, bus, trace = pipeline
        manager.run_pipeline("糖尿病")

        summary = trace.summary()
        assert summary["total_logs"] >= 40, f"日志总数应>=40，实际: {summary['total_logs']}"


# ============================================================
# 4. 结果数据结构测试：输出格式规范完整
# ============================================================
class TestResultStructure:
    """验证最终结果的数据结构完整性"""

    def test_result_has_trace_id(self, pipeline):
        """结果包含trace_id"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")
        assert "trace_id" in result
        assert len(result["trace_id"]) > 0

    def test_result_has_pipeline_summary(self, pipeline):
        """结果包含流程摘要"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        summary = result["data"]["pipeline_summary"]
        required_keys = [
            "papers_found", "targets_found", "molecules_screened",
            "molecules_scored", "best_docking_score", "safe_molecules",
            "risk_distribution"
        ]
        for key in required_keys:
            assert key in summary, f"流程摘要应包含{key}"

    def test_safe_molecules_have_required_fields(self, pipeline):
        """每个安全分子都包含必要字段"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        mols = result["data"]["safe_molecules"]
        required_fields = ["name", "composite_score", "docking_score",
                          "toxicity", "admet", "final_rank"]
        for mol in mols[:3]:  # 检查前3个
            for field in required_fields:
                assert field in mol, f"分子应包含字段: {field}"

    def test_molecules_sorted_by_score(self, pipeline):
        """分子按综合分降序排列"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        mols = result["data"]["safe_molecules"]
        for i in range(len(mols) - 1):
            assert mols[i]["composite_score"] >= mols[i + 1]["composite_score"], \
                "分子应按综合分降序排列"

    def test_risk_distribution_valid(self, pipeline):
        """毒性分布数据有效"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        risk = result["data"]["pipeline_summary"]["risk_distribution"]
        assert "low" in risk, "应有低风险计数"
        assert "medium" in risk, "应有中风险计数"
        assert "high" in risk, "应有高风险计数"
        assert risk["low"] >= 5, "低风险分子应>=5"


# ============================================================
# 5. 确定性测试：相同输入得到相同输出
# ============================================================
class TestDeterminism:
    """验证系统的确定性输出（可复现）"""

    def test_same_disease_same_targets(self):
        """同一疾病两次运行，靶点结果一致"""
        bus1, trace1 = MatrixBus(), TraceLogger()
        manager1 = ManagerAgent(bus1, trace1)
        r1 = manager1.run_pipeline("糖尿病")

        bus2, trace2 = MatrixBus(), TraceLogger()
        manager2 = ManagerAgent(bus2, trace2)
        r2 = manager2.run_pipeline("糖尿病")

        t1 = r1["data"]["pipeline_summary"]["targets_found"]
        t2 = r2["data"]["pipeline_summary"]["targets_found"]
        assert t1 == t2, "同一疾病的靶点结果应一致"

    def test_same_disease_same_molecule_count(self):
        """同一疾病两次运行，安全分子数量一致"""
        bus1, trace1 = MatrixBus(), TraceLogger()
        manager1 = ManagerAgent(bus1, trace1)
        r1 = manager1.run_pipeline("乳腺癌")

        bus2, trace2 = MatrixBus(), TraceLogger()
        manager2 = ManagerAgent(bus2, trace2)
        r2 = manager2.run_pipeline("乳腺癌")

        c1 = r1["data"]["pipeline_summary"]["safe_molecules"]
        c2 = r2["data"]["pipeline_summary"]["safe_molecules"]
        assert c1 == c2, "同一疾病的安全分子数量应一致"


# ============================================================
# 6. 质量门控测试：Guardrail机制有效
# ============================================================
class TestQualityGate:
    """验证质量门控（Guardrail）机制正常工作"""

    def test_scout_finds_minimum_targets(self, pipeline):
        """Scout质量门控：靶点数>=3"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        targets = result["data"]["pipeline_summary"]["targets_found"]
        assert len(targets) >= 3, "Scout质量门控要求靶点>=3"

    def test_safety_finds_minimum_safe_molecules(self, pipeline):
        """Safety质量门控：安全分子>=5"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        safe_count = result["data"]["pipeline_summary"]["safe_molecules"]
        assert safe_count >= 5, "Safety质量门控要求安全分子>=5"

    def test_quality_score_positive(self, pipeline):
        """质量评分>0"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        quality = result["data"].get("quality_score", 0)
        assert quality > 0, "质量评分应>0"

    def test_best_docking_score_reasonable(self, pipeline):
        """最高对接分数在合理范围(0-1)"""
        manager, bus, trace = pipeline
        result = manager.run_pipeline("糖尿病")

        best = result["data"]["pipeline_summary"]["best_docking_score"]
        assert 0 < best <= 1.0, f"对接分数应在(0,1]范围，实际: {best}"
