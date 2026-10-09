# PharmOrchestra — 多智能体药物研发流程编排系统

> 输入一个疾病名称，4 个专业 Agent 自动完成「文献侦察 → 分子筛选 → 机制分析 → 安全评估」全流程，输出 TOP 10 安全候选分子。
> 完全离线可跑、零第三方依赖、中文注释、确定性输出——评委克隆后 1 分钟即可复现。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

---

## 一、项目简介

PharmConductor（药智·多智能体药物研发流程编排系统）是一个用 Python 实现的「虚拟药物研发团队」：把药物早期发现中四个关键角色变成四个 AI 智能体（Agent），由编排器统一调度，自动完成从疾病到候选分子的完整链路。

- **4-Agent 编排架构**：1 个 Manager（编排器）+ 4 个 Worker（文献侦察兵 / 分子筛选手 / 机制分析师 / 安全评估官），经消息总线（MatrixBus）协作；
- **质量门控（Quality Gate）**：每个环节有最低质量标准，不达标自动重试，保证管线输出可信；
- **完全离线、零依赖**：核心流程只用 Python 标准库，mock 数据由哈希确定性生成——相同输入永远得到相同输出，演示与评审完全可复现；
- **7 个技能（Skill）**：文献检索、靶点提取、分子筛选、结合位点预测、对接打分、毒性预测、ADMET 分析；
- **全中文注释**：代码即教材，药学背景也能逐行读懂。

> ⚠️ 本项目为技术演示与教学项目，输出为模拟数据，不构成任何医学建议。

## 二、架构示意

```
                    +-----------------------+
                    |    Manager（编排器）   |
                    |  负责: 协调整个流程    |
                    +-----------+-----------+
                                |
          +---------+---------+---------+---------+
          |         |                   |         |
          v         v                   v         v
  +-------+--+ +----+------+  +--------+---+ +---+--------+
  |  Scout   | | Screener  |  | Mechanism  | |  Safety    |
  | 文献侦察兵| | 分子筛选手 |  | 机制分析师  | | 安全评估官  |
  +----+-----+ +-----+-----+  +-----+------+ +-----+------+
       |              |              |              |
       v              v              v              v
  +----+-----+ +-----+-----+  +-----+------+ +-----+------+
  |PubMed   | |MolScreen  |  |DockingScore| |ToxPredict  |
  |Search   | |ing        |  |BindingSite | |ADMETAnalysis|
  +---------+ +-----------+  +------------+ +------------+

  技能(Skills):  7个
  智能体(Agent): 5个 (1个Manager + 4个Worker)
  消息总线:      MatrixBus (内存消息传递)
```

**流程**：输入疾病名称 → Scout 查文献提靶点（质检：靶点 ≥3）→ Screener 筛候选分子（质检：分子 ≥5）→ Mechanism 分析结合机制并打分（质检：最高分 ≥0.8）→ Safety 评估毒性与 ADMET（质检：安全分子 ≥5）→ 输出 TOP 10 安全候选分子。

## 三、快速开始

**环境要求**：Python 3.8+，无需安装任何第三方库（运行测试需 `pip install pytest`）。

```bash
git clone https://github.com/zzzccc6666/PharmConductor.git
cd PharmConductor/PharmOrchestra-github

# 运行（默认疾病：糖尿病）
python main.py

# 指定疾病（内置 5 种 mock 数据：糖尿病 / 乳腺癌 / 高血压 / 类风湿关节炎 / 阿尔茨海默病）
python main.py 乳腺癌
```

**运行测试**：

```bash
python -m pytest tests/ -v
```

**Docker（可选）**：

```bash
docker build -t pharmorchestra .
docker run pharmorchestra python main.py 糖尿病
```

## 四、使用示例

执行 `python main.py 糖尿病`，终端实时输出 55 条编排事件（确定性输出，节选）：

```
>>> 分配任务给 Scout（文献侦察兵）
Scout:    检索到相关文献，提取靶点 5 个，质量评分=1.00
>>> 分配任务给 Screener（分子筛选手）
Screener: 筛选出 17 个候选分子，质量评分=1.00
>>> 分配任务给 Mechanism（机制分析师）
Mechanism: 分析了 17 个分子，最高对接分数=0.9460，平均=0.7596
>>> 分配任务给 Safety（安全评估官）
Safety:   毒性分布 {'low': 13, 'medium': 3, 'high': 1}，筛出 13 个安全候选分子
===== 药物发现流程完成 ===== 找到 13 个安全候选分子
```

结果同时落盘为 `results_<疾病>_<时间戳>.json`（含 trace_id、各阶段摘要、安全分子清单与评分），可直接作为评审核查材料。

另有能力展示脚本（面向评审的 6 大核心能力验证）：

```bash
python demo_capabilities.py
```

## 五、演示视频与线上 Demo

- **演示视频（约 3 分钟，推荐）**：[PharmConductor 演示视频](https://github.com/user-attachments/assets/855a1c7a-6dbd-45d8-adf1-69a7ae79a9b1) —— 覆盖一键离线运行（55 事件确定性输出）、Safety 毒性否决闭环（红占比 40% → 自动重规划 → 0 红）、ChEMBL + GLM 真实数据回测（西地那非 #5，与临床事实一致）。
- **实时可视化版（PharmConductor Web Demo）**：https://dcniaqwtmoca.feishuapp.com/app/app_17d67yfvzcc （需飞书账号登录）
  多 Agent 协作实时可视化：启动任务 → 事件流 → Safety 红牌否决 → 自动 replan → 报告生成，全过程网页可见。

## 六、项目结构

```
PharmOrchestra-github/
├── main.py                # 演示入口
├── demo_capabilities.py   # 能力展示脚本（面向评审）
├── agents/                # 5 个智能体（manager + 4 个 worker）
├── skills/                # 7 个技能（检索/筛选/对接/毒性/ADMET 等）
├── utils/                 # 消息总线 MatrixBus + 追踪日志 TraceLogger
├── tests/                 # 单元测试与集成测试
├── requirements.txt       # 依赖清单（核心零依赖，仅测试用 pytest）
└── Dockerfile             # 容器化（可选）
```

## 七、参与贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)（分支命名、代码约定、本地验证、提交格式），提 Issue / PR 请使用仓库内置模板。新手推荐从「新增疾病 mock 数据」或「文档改进」入手。

## 八、第三方依赖与知识产权

- 运行时**零第三方依赖**（仅 Python 标准库）；测试依赖 pytest（MIT，仅开发期）。
- 完整清单与协议核查见 [NOTICE](NOTICE)；所有演示数据为自行构造的模拟数据，不含第三方受版权保护内容。

## 九、许可证

本项目以 [MIT License](LICENSE) 开源。Copyright (c) 2026 罗啸 (zzzccc6666)。
