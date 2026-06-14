"""
用例校对校验规则
"""
import re
from typing import Any, Optional, Dict, List
from abc import ABC, abstractmethod


class FieldIssue:
    """字段问题"""
    def __init__(
        self,
        field: str,
        issue_type: str,
        message: str,
        fixable: bool = False,
        fix_suggestion: Optional[str] = None
    ):
        self.field = field
        self.issue_type = issue_type
        self.message = message
        self.fixable = fixable
        self.fix_suggestion = fix_suggestion
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "issue_type": self.issue_type,
            "message": self.message,
            "fixable": self.fixable,
            "fix_suggestion": self.fix_suggestion
        }


class ValidationRule(ABC):
    """校验规则基类"""
    
    @abstractmethod
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        """
        校验值
        
        Args:
            value: 要校验的值
            field_name: 字段名称
            field_config: 字段配置
        
        Returns:
            FieldIssue 如果有问题，否则 None
        """
        pass
    
    @abstractmethod
    def fix(self, value: Any, field_config: dict) -> Any:
        """
        修复值
        
        Args:
            value: 要修复的值
            field_config: 字段配置
        
        Returns:
            修复后的值
        """
        pass


class RequiredRule(ValidationRule):
    """必填校验"""
    
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        if not field_config.get("required", False):
            return None
        
        # 检查是否为空
        if value is None or (isinstance(value, str) and not value.strip()):
            return FieldIssue(
                field=field_name,
                issue_type="required",
                message="必填字段不能为空",
                fixable=False
            )
        return None
    
    def fix(self, value: Any, field_config: dict) -> Any:
        # 必填字段无法自动修复
        return value


class EnumRule(ValidationRule):
    """枚举值校验"""
    
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        if field_config.get("field_type") != "enum":
            return None
        
        enum_values = field_config.get("enum_values", [])
        if not enum_values:
            return None
        
        # 空值由必填规则处理
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        
        str_value = str(value).strip()
        
        # 忽略大小写比较
        enum_lower = [v.lower() for v in enum_values]
        if str_value.lower() not in enum_lower:
            return FieldIssue(
                field=field_name,
                issue_type="enum",
                message=f"值 '{str_value}' 不在可选范围内，可选值: {', '.join(enum_values)}",
                fixable=self._can_fix(str_value, enum_values),
                fix_suggestion=self._get_fix_suggestion(str_value, enum_values)
            )
        
        # 检查大小写是否标准
        if str_value not in enum_values and str_value.lower() in enum_lower:
            idx = enum_lower.index(str_value.lower())
            return FieldIssue(
                field=field_name,
                issue_type="enum_case",
                message=f"值 '{str_value}' 大小写不标准，建议使用 '{enum_values[idx]}'",
                fixable=True,
                fix_suggestion=enum_values[idx]
            )
        
        return None
    
    def _can_fix(self, value: str, enum_values: List[str]) -> bool:
        """检查是否可以修复"""
        value_lower = value.lower()
        enum_lower = [v.lower() for v in enum_values]
        return value_lower in enum_lower
    
    def _get_fix_suggestion(self, value: str, enum_values: List[str]) -> Optional[str]:
        """获取修复建议"""
        value_lower = value.lower()
        enum_lower = [v.lower() for v in enum_values]
        if value_lower in enum_lower:
            idx = enum_lower.index(value_lower)
            return enum_values[idx]
        return None
    
    def fix(self, value: Any, field_config: dict) -> Any:
        if field_config.get("field_type") != "enum":
            return value
        
        enum_values = field_config.get("enum_values", [])
        if not enum_values or not value:
            return value
        
        str_value = str(value).strip()
        enum_lower = [v.lower() for v in enum_values]
        
        if str_value.lower() in enum_lower:
            idx = enum_lower.index(str_value.lower())
            return enum_values[idx]
        
        return value


class StepNumberingRule(ValidationRule):
    """步骤序号校验"""
    
    STEP_PATTERN = re.compile(r'^\d+\.\s')
    
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        # 只对有 format_check = step_numbering 的字段生效
        if field_config.get("format_check") != "step_numbering":
            return None
        
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        
        str_value = str(value).strip()
        
        # 检查是否以序号开头
        if not self.STEP_PATTERN.match(str_value):
            return FieldIssue(
                field=field_name,
                issue_type="step_numbering",
                message="操作步骤建议以序号开头，如 '1. '",
                fixable=True,
                fix_suggestion=f"1. {str_value}"
            )
        
        return None
    
    def fix(self, value: Any, field_config: dict) -> Any:
        if field_config.get("format_check") != "step_numbering":
            return value
        
        if not value:
            return value
        
        str_value = str(value).strip()
        
        if not self.STEP_PATTERN.match(str_value):
            # 检查是否有多行
            lines = str_value.split('\n')
            if len(lines) > 1:
                # 多行，每行添加序号
                numbered_lines = []
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not self.STEP_PATTERN.match(line):
                        numbered_lines.append(f"{i}. {line}")
                    else:
                        numbered_lines.append(line)
                return '\n'.join(numbered_lines)
            else:
                # 单行，添加 "1. "
                return f"1. {str_value}"
        
        return value


class AutomationRule(ValidationRule):
    """自动化标识校验"""
    
    YES_VALUES = {'y', 'yes', 'true', '是', '1'}
    NO_VALUES = {'n', 'no', 'false', '否', '0'}
    
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        # 只对自动化字段生效（通过字段名或枚举值判断）
        enum_values = field_config.get("enum_values") or []
        if not (set(enum_values) == {'Y', 'N'} or field_name in ['自动化', 'automation']):
            return None
        
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        
        str_value = str(value).strip().lower()
        
        if str_value in self.YES_VALUES and str(value).strip() != 'Y':
            return FieldIssue(
                field=field_name,
                issue_type="automation",
                message=f"值 '{value}' 建议标准化为 'Y'",
                fixable=True,
                fix_suggestion="Y"
            )
        
        if str_value in self.NO_VALUES and str(value).strip() != 'N':
            return FieldIssue(
                field=field_name,
                issue_type="automation",
                message=f"值 '{value}' 建议标准化为 'N'",
                fixable=True,
                fix_suggestion="N"
            )
        
        return None
    
    def fix(self, value: Any, field_config: dict) -> Any:
        if not value:
            return value
        
        str_value = str(value).strip().lower()
        
        if str_value in self.YES_VALUES:
            return 'Y'
        if str_value in self.NO_VALUES:
            return 'N'
        
        return value


class FuzzyWordRule(ValidationRule):
    """模糊词检测（仅警告，不自动修复）"""
    
    FUZZY_WORDS = ['正常', '应该', '可能', '大概', '差不多', '基本上']
    
    def validate(self, value: Any, field_name: str, field_config: dict) -> Optional[FieldIssue]:
        # 只对预期结果字段生效
        if field_config.get("quality_check") != "avoid_fuzzy_words":
            return None
        
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        
        str_value = str(value)
        
        found_words = [w for w in self.FUZZY_WORDS if w in str_value]
        if found_words:
            return FieldIssue(
                field=field_name,
                issue_type="fuzzy_word",
                message=f"预期结果包含模糊词: {', '.join(found_words)}，建议使用更具体的描述",
                fixable=False  # 模糊词不自动修复
            )
        
        return None
    
    def fix(self, value: Any, field_config: dict) -> Any:
        # 模糊词不自动修复
        return value


# 所有校验规则
ALL_RULES: List[ValidationRule] = [
    RequiredRule(),
    EnumRule(),
    StepNumberingRule(),
    AutomationRule(),
    FuzzyWordRule()
]


def validate_field(value: Any, field_name: str, field_config: dict) -> List[FieldIssue]:
    """
    对单个字段执行所有校验规则
    
    Returns:
        问题列表
    """
    issues = []
    for rule in ALL_RULES:
        issue = rule.validate(value, field_name, field_config)
        if issue:
            issues.append(issue)
    return issues


def fix_field(value: Any, field_config: dict, issue_type: str) -> Any:
    """
    修复字段值
    
    Args:
        value: 原始值
        field_config: 字段配置
        issue_type: 问题类型
    
    Returns:
        修复后的值
    """
    for rule in ALL_RULES:
        if isinstance(rule, EnumRule) and issue_type in ['enum', 'enum_case']:
            return rule.fix(value, field_config)
        if isinstance(rule, StepNumberingRule) and issue_type == 'step_numbering':
            return rule.fix(value, field_config)
        if isinstance(rule, AutomationRule) and issue_type == 'automation':
            return rule.fix(value, field_config)
    
    return value
