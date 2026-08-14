# ============================================================
# main.py - PharmOrchestra 演示入口
# 大白话：这是整个程序的"启动按钮"
# 输入一个疾病名字，程序会自动走完整个药物发现流程
# 最后输出安全的候选药物分子
# ============================================================

import sys
import json
import os
from datetime import datetime
from typing import Any, Dict, List

# 导入项目模块
from utils.matrix import MatrixBus
from utils.trace import TraceLogger
from agents.manager import ManagerAgent


# ============================================================
# 颜色定义 - 用ANSI转义码给终端文字上色，让输出更好看
# ============================================================
class Color:
    """终端颜色工具类"""
    PURPLE = "\033[95m"   # 紫色 - 标题
    BLUE = "\033[94m"     # 蓝色 - 信息
    CYAN = "\033[96m"     # 青色 - 步骤
    GREEN = "\033[92m"    # 绿色 - 成功
    YELLOW = "\033[93m"   # 黄色 - 警告
    RED = "\033[91m"      # 红色 - 错误
    BOLD = "\033[1m"      # 粗体
    RESET = "\033[0m"     # 重置颜色


def print_header(title: str) -> None:
    """打印一个漂亮的标题栏"""
    line = "=" * 70
    print(f"\n{Color.PURPLE}{Color.BOLD}{line}")
    print(f"  {title}")
    print(f"{line}{Color.RESET}\n")


def print_step(step: str, agent: str, message: str) -> None:
    """打印一个步骤信息"""
    print(f"  {Color.CYAN}[{step}] {Color.BOLD}{agent}{Color.RESET}{Color.CYAN}: {message}{Color.RESET}")


def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"  {Color.GREEN}[OK] {message}{Color.RESET}")


def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"  {Color.YELLOW}[!] {message}{Color.RESET}")


def print_info(message: str) -> None:
    """打印普通信息"""
    print(f"  {Color.BLUE}[i] {message}{Color.RESET}")


def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"  {Color.RED}[X] {message}{Color.RESET}")


def print_molecule_table(molecules: List[Dict[str, Any]], top_n: int = 10) -> None:
    """打印候选分子表格

    Args:
        molecules: 分子列表
        top_n: 显示前几名
    """
    if not molecules:
        print_warning("没有找到安全候选分子")
        return

    # 取前top_n个
    top_mols = molecules[:top_n]

    print(f"\n  {Color.GREEN}{Color.BOLD}  TOP {len(top_mols)} 安全候选分子{Color.RESET}")
    print(f"  {'-' * 100}")
    print(f"  {'排名':<4} {'分子名称':<22} {'综合分':<8} {'对接分':<8} {'毒性':<6} {'ADMET':<8} {'靶点':<10}")
    print(f"  {'-' * 100}")

    for mol in top_mols:
        rank = mol.get("final_rank", 0)
        name = mol.get("name", "未知")[:20]
        composite = mol.get("composite_score", 0.0)
        docking = mol.get("docking_score", 0.0)
        tox_level = mol.get("toxicity", {}).get("risk_level", "?")
        admet_score = mol.get("admet", {}).get("admet_score", 0.0)
        target = mol.get("target", "?")[:10]

        # 根据综合分选择颜色
        if composite >= 0.7:
            color = Color.GREEN
        elif composite >= 0.5:
            color = Color.YELLOW
        else:
            color = Color.RED

        print(f"  {color}{rank:<6}{name:<22}{composite:<10.4f}{docking:<10.4f}{tox_level:<8}{admet_score:<10.2f}{target:<12}{Color.RESET}")

    print(f"  {'-' * 100}")


def print_summary(result: Dict[str, Any], trace: TraceLogger) -> None:
    """打印流程摘要

    Args:
        result: 最终结果
        trace: 日志记录器
    """
    summary = trace.summary()

    print(f"\n  {Color.PURPLE}{Color.BOLD}  流程摘要{Color.RESET}")
    print(f"  {'-' * 60}")
    print(f"  追踪ID:        {result.get('trace_id', 'N/A')}")
    print(f"  疾病:          {result.get('disease', 'N/A')}")
    print(f"  总耗时:        {summary['total_time_ms']} 毫秒")
    print(f"  消息总数:      {result.get('message_count', 0)} 条")
    print(f"  日志总数:      {summary['total_logs']} 条")
    print(f"  参与Agent:     {', '.join(summary['agents_involved'])}")
    print(f"  {'-' * 60}")

    # 打印各Agent操作统计
    print(f"\n  {Color.BLUE}  各Agent操作统计:{Color.RESET}")
    for agent, count in summary["agent_stats"].items():
        bar = "#" * count  # 用#号画一个简单的柱状图
        print(f"    {agent:<12} ({count:>3}次操作) {bar}")

    # 打印流程数据
    pipeline = result.get("data", {}).get("pipeline_summary", {})
    if pipeline:
        print(f"\n  {Color.BLUE}  流程数据:{Color.RESET}")
        print(f"    论文数量:        {pipeline.get('papers_found', 0)}")
        print(f"    靶点:            {', '.join(pipeline.get('targets_found', []))}")
        print(f"    筛选分子数:      {pipeline.get('molecules_screened', 0)}")
        print(f"    对接打分分子数:  {pipeline.get('molecules_scored', 0)}")
        print(f"    最高对接分数:    {pipeline.get('best_docking_score', 0.0)}")
        print(f"    安全分子数:      {pipeline.get('safe_molecules', 0)}")

        risk = pipeline.get("risk_distribution", {})
        if risk:
            print(f"    毒性分布:        低风险={risk.get('low', 0)}, "
                  f"中风险={risk.get('medium', 0)}, 高风险={risk.get('high', 0)}")


def print_trace_logs(trace: TraceLogger, trace_id: str) -> None:
    """打印追踪日志（简要版）"""
    logs = trace.get_logs_by_trace(trace_id)
    print(f"\n  {Color.BLUE}{Color.BOLD}  追踪日志（共{len(logs)}条）:{Color.RESET}")
    print(f"  {'-' * 80}")

    for log in logs:
        agent = log["agent"]
        action = log["action"]
        detail = log["detail"]
        timestamp = log["timestamp"][11:19]  # 只取时分秒

        # 根据action类型选择颜色
        if "start" in action or "dispatch" in action:
            color = Color.CYAN
        elif "done" in action or "success" in action:
            color = Color.GREEN
        elif "error" in action or "warning" in action or "quality_warning" in action:
            color = Color.YELLOW
        elif "retry" in action:
            color = Color.YELLOW
        else:
            color = Color.BLUE

        print(f"  {color}[{timestamp}] {agent:<12} | {action:<20} | {detail}{Color.RESET}")


def save_results(result: Dict[str, Any], disease: str) -> str:
    """把结果保存到JSON文件

    Args:
        result: 结果数据
        disease: 疾病名称

    Returns:
        保存的文件路径
    """
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_disease = disease.replace(" ", "_")
    filename = f"results_{safe_disease}_{timestamp}.json"

    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, filename)

    # 准备要保存的数据（去掉不能序列化的内容）
    save_data = {
        "trace_id": result.get("trace_id"),
        "disease": disease,
        "timestamp": datetime.now().isoformat(),
        "success": result.get("success"),
        "pipeline_summary": result.get("data", {}).get("pipeline_summary", {}),
        "safe_molecules": result.get("data", {}).get("safe_molecules", []),
        "message_count": result.get("message_count", 0),
        "trace_summary": result.get("trace_summary", {})
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    return filepath


def main() -> None:
    """主函数 - 程序入口"""

    # ===== 第一步：获取疾病名称 =====
    if len(sys.argv) > 1:
        disease = sys.argv[1]
    else:
        disease = "糖尿病"  # 默认疾病

    print_header(f"PharmOrchestra - 多智能体药物发现平台")
    print_info(f"目标疾病: {Color.BOLD}{disease}{Color.RESET}")
    print_info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"运行模式: Mock数据（离线运行，无需API密钥）")
    print()

    # ===== 第二步：创建消息总线和日志记录器 =====
    bus = MatrixBus()
    trace = TraceLogger()

    # ===== 第三步：创建编排器（Manager） =====
    print_header("初始化智能体团队")
    manager = ManagerAgent(bus, trace)

    print_info(f"Manager（编排器）已就绪 - 负责协调整个流程")
    print_info(f"  Scout（文献侦察兵） - 搜索文献，发现靶点")
    print_info(f"  Screener（分子筛选手） - 搜索候选分子")
    print_info(f"  Mechanism（机制分析师） - 分析结合机制")
    print_info(f"  Safety（安全评估官） - 评估毒性和ADMET")

    # ===== 第四步：运行完整流程 =====
    print_header(f"开始药物发现流程: {disease}")

    result = manager.run_pipeline(disease)

    # ===== 第五步：输出结果 =====
    if result["success"]:
        print_header("流程执行成功!")

        # 打印TOP 10安全候选分子
        safe_mols = result.get("data", {}).get("safe_molecules", [])
        print_molecule_table(safe_mols, top_n=10)

        # 打印摘要
        print_summary(result, trace)

        # 打印追踪日志
        print_trace_logs(trace, result.get("trace_id", ""))

        # 保存结果到文件
        print_header("保存结果")
        filepath = save_results(result, disease)
        print_success(f"结果已保存到: {filepath}")

    else:
        print_header("流程执行失败!")
        print_error(f"错误信息: {result.get('error', '未知错误')}")

        # 即使失败也打印日志
        print_trace_logs(trace, result.get("trace_id", ""))

    print(f"\n{Color.PURPLE}{'=' * 70}{Color.RESET}")
    print(f"{Color.PURPLE}  PharmOrchestra 运行结束{Color.RESET}")
    print(f"{Color.PURPLE}{'=' * 70}{Color.RESET}\n")


if __name__ == "__main__":
    main()
