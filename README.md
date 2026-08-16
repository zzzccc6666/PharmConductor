# PharmOrchestra - 多智能体药物发现平台

## 项目简介（大白话版）

PharmOrchestra（药学交响乐团）是一个用Python写的"虚拟药物研发团队"。

想象一下，你要研发一种治疗糖尿病的新药，传统流程需要很多人协作：
- 有人负责查文献找靶点
- 有人负责筛选分子
- 有人负责分析药物怎么起作用
- 有人负责检查药物安不安全

PharmOrchestra就是把这四个"人"变成四个AI智能体（Agent），让它们自动完成这些工作。

**特点：**
- 完全离线运行，不需要任何API密钥（用mock数据模拟）
- 代码通俗易懂，适合药学新生学习
- 所有注释都是中文
- 输入一个疾病名字，输出安全的候选药物分子

---

## 架构图

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

### 流程说明

```
输入: 疾病名称 (如 "糖尿病")
  |
  v
[1. Scout 文献侦察兵]
  - 用 pubmed_search 搜论文
  - 用 target_extract 提取靶点
  - 质量检查: 靶点数 >= 3
  |
  v
[2. Screener 分子筛选手]
  - 用 mol_screening 搜候选分子
  - 质量检查: 分子数 >= 5
  |
  v
[3. Mechanism 机制分析师]
  - 用 binding_site 预测结合位点
  - 用 docking_score 计算对接分数
  - 质量检查: 最高分 >= 0.8
  |
  v
[4. Safety 安全评估官]
  - 用 tox_predict 预测毒性
  - 用 admet_analysis 计算ADMET参数
  - 质量检查: 安全分子数 >= 5
  |
  v
输出: TOP 10 安全候选分子 (含综合评分)
```

---

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- 不需要安装任何额外的库（标准库即可运行）
- 运行测试需要 pytest（可选）

### 运行演示

```bash
# 进入项目目录
cd PharmOrchestra

# 运行（默认疾病: 糖尿病）
python main.py

# 指定疾病
python main.py 糖尿病
python main.py 乳腺癌
python main.py 高血压
python main.py 类风湿关节炎
python main.py 阿尔茨海默病
```

### 运行测试

```bash
# 安装pytest（如果没有的话）
pip install pytest

# 运行所有测试
python -m pytest tests/ -v

# 运行单个测试类
python -m pytest tests/test_skills.py::TestPubMedSearch -v
```

---

## 项目结构说明

```
PharmOrchestra/
├── README.md                  # 项目说明文档（就是你在看的这个）
├── requirements.txt           # Python依赖列表
├── Dockerfile                 # Docker容器配置
├── main.py                    # 演示入口，运行这个开始
│
├── agents/                    # 智能体模块
│   ├── __init__.py
│   ├── base_agent.py          # Agent基类（消息传递、质量检查）
│   ├── manager.py             # 编排器（协调4个Worker）
│   ├── scout.py               # 文献侦察兵（找靶点）
│   ├── screener.py            # 分子筛选手（找分子）
│   ├── mechanism.py           # 机制分析师（分析结合机制）
│   └── safety.py              # 安全评估官（评估毒性）
│
├── skills/                    # 技能模块
│   ├── __init__.py
│   ├── base_skill.py          # 技能基类
│   ├── pubmed_search.py       # PubMed文献检索
│   ├── target_extract.py      # 靶点提取
│   ├── mol_screening.py       # 分子筛选
│   ├── docking_score.py       # 分子对接打分
│   ├── binding_site.py        # 结合位点预测
│   ├── tox_predict.py         # 毒性预测
│   └── admet_analysis.py      # ADMET参数分析
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── matrix.py              # 消息总线（模拟Matrix协议）
│   └── trace.py               # 日志记录器
│
└── tests/                     # 测试模块
    ├── __init__.py
    └── test_skills.py         # 7个技能的单元测试
```

---

## Agent（智能体）说明

### Manager（编排器）
- **角色**：项目经理，负责按顺序分配任务给4个Worker
- **流程**：Scout -> Screener -> Mechanism -> Safety
- **特点**：每一步之间传递数据，汇总最终结果

### Scout（文献侦察兵）
- **角色**：去"图书馆"查资料，从科研文献中发现药物靶点
- **技能**：pubmed_search（搜论文）+ target_extract（提取靶点）
- **质量检查**：至少找到3个靶点

### Screener（分子筛选手）
- **角色**：根据靶点去"分子库"找能结合的候选分子
- **技能**：mol_screening（分子筛选）
- **质量检查**：至少找到5个候选分子

### Mechanism（机制分析师）
- **角色**：分析分子怎么跟靶点结合，结合得好不好
- **技能**：binding_site（找结合位点）+ docking_score（打分）
- **质量检查**：最高对接分数 >= 0.8

### Safety（安全评估官）
- **角色**：检查分子有没有毒，在人体里表现怎么样
- **技能**：tox_predict（毒性预测）+ admet_analysis（ADMET分析）
- **质量检查**：至少5个安全分子

---

## Skill（技能）说明

| 技能名 | 大白话解释 | 输入 | 输出 |
|--------|-----------|------|------|
| pubmed_search | 在PubMed上搜论文 | 疾病名 | 论文列表 |
| target_extract | 从论文里读出靶点 | 论文列表 | 靶点列表 |
| mol_screening | 去分子库找候选分子 | 靶点列表 | 分子列表(SMILES) |
| docking_score | 算分子跟靶点结合得多好 | 分子+靶点 | 对接分数(0-1) |
| binding_site | 找靶点上分子能卡进去的口袋 | 靶点名 | 结合位点信息 |
| tox_predict | 预测分子有没有毒 | 分子列表 | 毒性等级(低/中/高) |
| admet_analysis | 算药物在人体里的表现 | 分子列表 | ADMET参数 |

### ADMET是什么？

ADMET是五个英文单词的缩写，描述药物在人体内的"旅程"：
- **A**bsorption（吸收）：药物能不能被身体吸收
- **D**istribution（分布）：药物在身体里怎么分布
- **M**etabolism（代谢）：药物怎么被分解
- **E**xcretion（排泄）：药物怎么排出体外
- **T**oxicity（毒性）：药物有没有毒

---

## 支持的疾病

目前内置了5种疾病的mock数据：

| 疾病 | 中文 | 主要靶点 |
|------|------|---------|
| 糖尿病 | diabetes | GLUT4, IRS-1, AMPK, GLP-1R, PPAR-γ |
| 乳腺癌 | breast cancer | ERα, HER2, CDK4/6, PI3K, BRCA1 |
| 高血压 | hypertension | ACE, AT1R, ACE2 |
| 类风湿关节炎 | rheumatoid arthritis | TNF-α, IL-6, JAK |
| 阿尔茨海默病 | Alzheimer's | AChE, BACE1, Tau |

---

## 技术特点

1. **消息总线（MatrixBus）**：模拟Matrix协议，Agent之间通过消息队列通信
2. **质量门控（Quality Gate）**：每个Agent都有质量检查，不达标会自动重试一次
3. **追踪日志（TraceLogger）**：记录每一步操作，方便调试和审计
4. **完全离线**：所有外部API调用都有mock实现，不需要网络和密钥
5. **确定性结果**：使用哈希函数生成mock数据，保证相同输入得到相同输出

---

## Docker运行

```bash
# 构建镜像
docker build -t pharmorchestra .

# 运行容器
docker run pharmorchestra python main.py 糖尿病
```

---

## 给药学新生的学习建议

1. 先看 `main.py`，了解整个流程怎么跑的
2. 再看 `agents/manager.py`，理解4个Agent怎么协作
3. 然后看各个Worker Agent（scout/screener/mechanism/safety），理解每个Agent做什么
4. 最后看 `skills/` 目录里的技能，理解每个技能的具体实现
5. `utils/` 目录是工具类，消息总线和日志记录器，可以最后看

**重点理解概念：**
- **Agent**：就是AI团队的"成员"，每个成员有特定的职责
- **Skill**：就是Agent能做的"具体技能"，比如搜文献、算分数
- **消息总线**：就是Agent之间的"通信系统"，类似微信群
- **质量门控**：就是"及格线"，每个环节都有最低要求
