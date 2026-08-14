# ============================================================
# base_skill.py - 所有技能的基类
# 技能（Skill）就是Agent能做的具体事情，比如"搜文献"、"算对接分数"
# ============================================================

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


@dataclass
class SkillResult:
    """技能执行结果 - 每个技能执行后都返回这个结构

    属性说明：
        success:            是否执行成功
        data:               返回的数据（字典格式）
        error:              错误信息，成功时为None
        execution_time_ms:  执行耗时（毫秒）
        trace_info:         追踪信息，记录技能名、时间等
    """
    success: bool                                    # 是否成功
    data: Dict[str, Any]                             # 返回数据
    error: Optional[str] = None                      # 错误信息
    execution_time_ms: int = 0                       # 执行耗时(毫秒)
    trace_info: Dict[str, Any] = field(              # 追踪信息
        default_factory=dict
    )


class BaseSkill:
    """技能基类 - 所有具体技能的父类

    一个技能需要实现三个核心方法：
    1. validate_params(): 检查输入参数对不对
    2. execute():         执行具体操作
    3. get_info():        返回技能的名称和描述
    """

    def __init__(self, name: str, description: str):
        """初始化技能

        Args:
            name:        技能名称，比如"pubmed_search"
            description: 技能描述，用大白话解释这个技能干什么
        """
        self.name = name
        self.description = description

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证输入参数是否合法

        子类应该重写此方法来检查自己的参数

        Args:
            params: 输入参数字典

        Returns:
            参数合法返回True，否则返回False
        """
        return True

    def get_info(self) -> Dict[str, str]:
        """获取技能信息（名称和描述）"""
        return {"name": self.name, "description": self.description}

    def execute(self, **kwargs) -> SkillResult:
        """执行技能 - 子类必须重写此方法

        Raises:
            NotImplementedError: 如果子类没有实现此方法
        """
        raise NotImplementedError("子类必须实现execute方法")

    def run(self, params: Dict[str, Any]) -> SkillResult:
        """带计时和异常处理的执行方法（推荐用这个来调用技能）

        这个方法会：
        1. 先验证参数
        2. 执行技能
        3. 自动计算耗时
        4. 捕获异常，返回错误结果

        Args:
            params: 输入参数字典

        Returns:
            技能执行结果
        """
        start_time = time.time()

        try:
            # 第一步：验证参数
            if not self.validate_params(params):
                return SkillResult(
                    success=False,
                    data={},
                    error="参数验证失败：输入参数不合法",
                    execution_time_ms=0,
                    trace_info={"skill": self.name}
                )

            # 第二步：执行技能
            result = self.execute(**params)

            # 第三步：补充追踪信息
            elapsed_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = elapsed_ms
            result.trace_info["skill"] = self.name
            result.trace_info["execution_time_ms"] = elapsed_ms

            return result

        except Exception as e:
            # 如果出错了，返回错误结果
            elapsed_ms = int((time.time() - start_time) * 1000)
            return SkillResult(
                success=False,
                data={},
                error=f"技能执行出错: {str(e)}",
                execution_time_ms=elapsed_ms,
                trace_info={"skill": self.name}
            )
