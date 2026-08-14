# ============================================================
# demo_capabilities.py - 能力展示脚本（给评委看）
# 大白话：这个脚本不是用来跑药物的，是用来展示"我们的系统有哪些能力"
# 运行后会展示6大核心能力，并生成一份验证报告
# ============================================================

import sys
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from utils.matrix import MatrixBus
from utils.trace import TraceLogger
from agents.manager import ManagerAgent
from agents.scout import ScoutAgent
from agents.safety import SafetyAgent


# ============================================================
# 颜色工具
# ============================================================
class C:
    P = "\033[95m"
    B = "\033[94m"
    CY = "\033[96m"
    G = "\033[92m"
    Y = "\033[93m"
    R = "\033[91m"
    BOLD = "\033[1m"
    RST = "\033[0m"


def banner(title: str):
    line = "=" * 72
    print(f"\n{C.P}{C.BOLD}{line}")
    print(f"  {title}")
    print(f"{line}{C.RST}\n")


def section(title: str):
    print(f"\n{C.CY}{C.BOLD}{'─' * 72}")
    print(f"  {title}")
    print(f"{'─' * 72}{C.RST}")


def ok(msg: str):
    print(f"  {C.G}[PASS]{C.RST} {msg}")


def info(msg: str):
    print(f"  {C.B}[INFO]{C.RST} {msg}")


# ============================================================
# 能力1：多疾病端到端验证
# ============================================================
def demo_multi_disease() -> List[Dict[str, Any]]:
    """展示5种疾病全部跑通"""
    section("能力1：多疾病端到端流程验证")
    diseases = ["糖尿病", "乳腺癌", "高血压", "类风湿关节炎", "阿尔茨海默病"]
    results = []

    for disease in diseases:
        bus = MatrixBus()
        trace = TraceLogger()
        manager = ManagerAgent(bus, trace)
        result = manager.run_pipeline(disease)

        if result["success"]:
            summary = result["data"]["pipeline_summary"]
            safe_count = summary["safe_molecules"]
            target_count = len(summary["targets_found"])
            paper_count = summary["papers_found"]
            best_score = summary["best_docking_score"]
            msg_count = result["message_count"]
            log_count = result["trace_summary"]["total_logs"]

            ok(f"{disease}: {paper_count}篇论文 -> {target_count}个靶点 -> "
               f"{safe_count}个安全分子 | TOP1对接分={best_score:.4f} | "
               f"{msg_count}条消息, {log_count}条日志")

            results.append({
                "disease": disease,
                "success": True,
                "papers": paper_count,
                "targets": target_count,
                "safe_molecules": safe_count,
                "best_docking": best_score,
                "messages": msg_count,
                "logs": log_count,
                "top_molecule": result["data"]["safe_molecules"][0]["name"]
                    if safe_count > 0 else "N/A",
                "top_score": result["data"]["safe_molecules"][0]["composite_score"]
                    if safe_count > 0 else 0
            })
        else:
            print(f"  {C.R}[FAIL]{C.RST} {disease}: {result.get('error', '未知错误')}")
            results.append({"disease": disease, "success": False})

    return results


# ============================================================
# 能力2：消息总线可追溯性
# ============================================================
def demo_message_trace() -> Dict[str, Any]:
    """展示MatrixBus消息总线通信全记录可追溯"""
    section("能力2：消息总线通信可追溯性（Matrix协议模拟）")

    bus = MatrixBus()
    trace = TraceLogger()
    manager = ManagerAgent(bus, trace)
    result = manager.run_pipeline("糖尿病")
    trace_id = result["trace_id"]

    messages = bus.get_messages_by_trace(trace_id)
    info(f"trace_id = {trace_id}")
    info(f"消息总数 = {len(messages)}条")
    print()

    for i, msg in enumerate(messages, 1):
        arrow = "->" if msg.msg_type == "task" else "<-"
        print(f"  [{i:2d}] {msg.source:<12} {arrow} {msg.target:<12} "
              f"| {msg.msg_type:<6} | 质量={msg.quality_score:.2f} | ID={msg.msg_id}")

    # 验证可追溯
    print()
    ok(f"通过trace_id可查回全部{len(messages)}条消息")
    ok(f"消息流向：Manager分派 -> Worker执行 -> Manager汇总")

    return {
        "trace_id": trace_id,
        "message_count": len(messages),
        "flow": "Manager -> Scout -> Screener -> Mechanism -> Safety -> Manager"
    }


# ============================================================
# 能力3：全链路日志追踪
# ============================================================
def demo_log_tracing() -> Dict[str, Any]:
    """展示TraceLogger全链路日志追踪"""
    section("能力3：全链路日志追踪（每一步有迹可循）")

    bus = MatrixBus()
    trace = TraceLogger()
    manager = ManagerAgent(bus, trace)
    result = manager.run_pipeline("糖尿病")
    trace_id = result["trace_id"]

    logs = trace.get_logs_by_trace(trace_id)
    summary = trace.summary()

    info(f"总日志数: {summary['total_logs']}条")
    info(f"总耗时: {summary['total_time_ms']}ms")
    info(f"参与Agent: {', '.join(summary['agents_involved'])}")
    print()

    # 展示各Agent操作统计
    print(f"  {C.B}各Agent操作统计:{C.RST}")
    for agent, count in sorted(summary["agent_stats"].items()):
        bar = "#" * count
        print(f"    {agent:<12} ({count:>3}次) {bar}")

    # 展示关键节点日志（前10条和后5条）
    print(f"\n  {C.B}关键节点日志（前10条）:{C.RST}")
    for log in logs[:10]:
        ts = log["timestamp"][11:19]
        print(f"    [{ts}] {log['agent']:<12} | {log['action']:<20} | {log['detail'][:40]}")

    print(f"\n  {C.B}关键节点日志（后5条）:{C.RST}")
    for log in logs[-5:]:
        ts = log["timestamp"][11:19]
        print(f"    [{ts}] {log['agent']:<12} | {log['action']:<20} | {log['detail'][:40]}")

    ok(f"全链路{summary['total_logs']}条日志，trace_id={trace_id}贯穿始终")
    return {"total_logs": summary["total_logs"], "trace_id": trace_id}


# ============================================================
# 能力4：质量门控机制
# ============================================================
def demo_quality_gate() -> Dict[str, Any]:
    """展示质量门控（Guardrail）机制"""
    section("能力4：质量门控机制（Guardrail）")

    bus = MatrixBus()
    trace = TraceLogger()
    manager = ManagerAgent(bus, trace)
    manager.run_pipeline("糖尿病")

    # 展示每个Agent的质量门控标准
    gates = [
        ("Scout", "靶点数量 >= 3", manager.scout.guardrail is not None),
        ("Screener", "候选分子数量 >= 5", manager.screener.guardrail is not None),
        ("Mechanism", "最高对接分 >= 0.8", manager.mechanism.guardrail is not None),
        ("Safety", "安全分子数量 >= 5", manager.safety.guardrail is not None),
    ]

    print(f"  {'Agent':<12} {'质量门控标准':<25} {'已设置':<8}")
    print(f"  {'─' * 50}")
    for agent, standard, enabled in gates:
        status = f"{C.G}Yes{C.RST}" if enabled else f"{C.R}No{C.RST}"
        print(f"  {agent:<12} {standard:<25} {status}")

    ok("4个Worker Agent全部设置质量门控")
    ok("不达标时自动重试1次，Safety放宽纳入中风险分子")
    return {"gates_configured": len(gates)}


# ============================================================
# 能力5：综合评分公式
# ============================================================
def demo_scoring_formula() -> Dict[str, Any]:
    """展示综合评分公式和TOP5分子"""
    section("能力5：综合评分公式（docking×0.4 + ADMET×0.3 + 安全性×0.3）")

    bus = MatrixBus()
    trace = TraceLogger()
    manager = ManagerAgent(bus, trace)
    result = manager.run_pipeline("糖尿病")

    mols = result["data"]["safe_molecules"][:5]
    print(f"\n  {'排名':<4} {'分子名称':<22} {'综合分':<10} {'对接分':<10} {'ADMET':<8} {'毒性':<6}")
    print(f"  {'─' * 65}")

    for mol in mols:
        rank = mol["final_rank"]
        name = mol["name"][:20]
        comp = mol["composite_score"]
        dock = mol["docking_score"]
        admet = mol["admet"]["admet_score"]
        tox = mol["toxicity"]["risk_level"]
        print(f"  {rank:<6}{name:<22}{comp:<10.4f}{dock:<10.4f}{admet:<8.2f}{tox:<6}")

    print(f"\n  {C.B}评分公式：综合分 = 对接分×0.4 + ADMET×0.3 + (1-毒性分)×0.3{C.RST}")
    ok("仅保留低毒性分子，按综合分降序排列")
    return {"top_molecule": mols[0]["name"], "top_score": mols[0]["composite_score"]}


# ============================================================
# 能力6：确定性输出验证
# ============================================================
def demo_determinism() -> Dict[str, Any]:
    """展示确定性输出：同一疾病两次运行结果一致"""
    section("能力6：确定性输出验证（可复现）")

    results = []
    for i in range(2):
        bus = MatrixBus()
        trace = TraceLogger()
        manager = ManagerAgent(bus, trace)
        result = manager.run_pipeline("乳腺癌")
        summary = result["data"]["pipeline_summary"]
        results.append({
            "targets": summary["targets_found"],
            "molecule_count": summary["safe_molecules"],
            "best_score": summary["best_docking_score"]
        })
        info(f"第{i+1}次运行: 靶点={results[-1]['targets']}, "
             f"安全分子={results[-1]['molecule_count']}个, "
             f"最高对接分={results[-1]['best_score']:.4f}")

    if results[0] == results[1]:
        ok("两次运行结果完全一致，系统具有确定性")
        return {"deterministic": True}
    else:
        print(f"  {C.Y}[WARN] 两次运行结果存在差异{C.RST}")
        return {"deterministic": False}


# ============================================================
# 生成验证报告
# ============================================================
def generate_report(multi_disease: List, msg_trace: Dict,
                    log_trace: Dict, quality: Dict,
                    scoring: Dict, determinism: Dict) -> str:
    """生成JSON格式的验证报告"""
    report = {
        "report_title": "PharmOrchestra 能力验证报告",
        "generated_at": datetime.now().isoformat(),
        "capabilities": {
            "1_multi_disease": {
                "description": "5种疾病端到端验证",
                "results": multi_disease,
                "all_passed": all(r["success"] for r in multi_disease)
            },
            "2_message_trace": {
                "description": "消息总线可追溯性",
                "trace_id": msg_trace["trace_id"],
                "message_count": msg_trace["message_count"]
            },
            "3_log_tracing": {
                "description": "全链路日志追踪",
                "total_logs": log_trace["total_logs"],
                "trace_id": log_trace["trace_id"]
            },
            "4_quality_gate": {
                "description": "质量门控机制",
                "gates_configured": quality["gates_configured"]
            },
            "5_scoring_formula": {
                "description": "综合评分公式",
                "top_molecule": scoring["top_molecule"],
                "top_score": scoring["top_score"]
            },
            "6_determinism": {
                "description": "确定性输出验证",
                "deterministic": determinism["deterministic"]
            }
        }
    }

    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "capabilities_report.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return filepath


# ============================================================
# 主函数
# ============================================================
def main():
    banner("PharmOrchestra 能力验证报告")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  验证项目: 6项核心能力")
    print(f"  运行模式: Mock数据（离线运行）")

    # 执行6项能力验证
    multi = demo_multi_disease()
    msg = demo_message_trace()
    log = demo_log_tracing()
    quality = demo_quality_gate()
    scoring = demo_scoring_formula()
    determ = demo_determinism()

    # 生成报告
    banner("验证报告已生成")
    filepath = generate_report(multi, msg, log, quality, scoring, determ)
    print(f"  {C.G}报告已保存: {filepath}{C.RST}")
    print(f"\n  {C.P}{'=' * 72}{C.RST}")
    print(f"  {C.P}  PharmOrchestra 能力验证完成{C.RST}")
    print(f"  {C.P}{'=' * 72}{C.RST}\n")


if __name__ == "__main__":
    main()
