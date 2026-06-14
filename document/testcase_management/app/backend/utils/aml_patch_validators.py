"""
AML Patch 表单验证规则

与现有平台验证规则保持一致
"""
from typing import Any, Optional, Dict, List
import re


FIELD_RULES = {
    "project": {
        "required": True,
        "max_length": 50,
        "error_messages": {
            "required": "项目不能为空",
            "max_length": "项目名称不能超过50个字符"
        }
    },
    "feature_branch": {
        "required": True,
        "max_length": 500,
        "error_messages": {
            "required": "代码分支不能为空",
            "max_length": "代码分支不能超过500个字符"
        }
    },
    "corresponding_directory": {
        "required": True,
        "max_length": 1000,
        "error_messages": {
            "required": "代码路径不能为空",
            "max_length": "代码路径不能超过1000个字符"
        }
    },
    "commit_record": {
        "required": True,
        "max_length": 2000,
        "error_messages": {
            "required": "commit message不能为空",
            "max_length": "commit message不能超过2000个字符"
        }
    },
    "zmind_numbers": {
        "required": True,
        "field_type": "array",
        "max_items": 50,
        "item_max_length": 100,
        "error_messages": {
            "required": "Zmind号不能为空",
            "max_items": "Zmind号最多50个",
            "item_max_length": "单个Zmind号不能超过100个字符"
        }
    },
    "amlogic_jira": {
        "required": True,
        "max_length": 200,
        "error_messages": {
            "required": "Amlogic Jira不能为空",
            "max_length": "Amlogic Jira不能超过200个字符"
        }
    },
    "patch_provider": {
        "required": True,
        "max_length": 100,
        "error_messages": {
            "required": "patch提供人不能为空",
            "max_length": "patch提供人不能超过100个字符"
        }
    },
    "is_odm_exclusive": {
        "required": True,
        "field_type": "enum",
        "enum_values": ["是", "否"],
        "error_messages": {
            "required": "该ODM专属不能为空",
            "enum": "该ODM专属必须是 是 或 否"
        }
    },
    "root_cause": {
        "required": True,
        "max_length": 2000,
        "error_messages": {
            "required": "Root Cause不能为空",
            "max_length": "Root Cause不能超过2000个字符"
        }
    },
    "patch_solution": {
        "required": True,
        "max_length": 2000,
        "error_messages": {
            "required": "解决方案不能为空",
            "max_length": "解决方案不能超过2000个字符"
        }
    },
    "impact_scope": {
        "required": True,
        "max_length": 2000,
        "error_messages": {
            "required": "推荐测试范围不能为空",
            "max_length": "推荐测试范围不能超过2000个字符"
        }
    },
    "aml_sri_result": {
        "required": True,
        "field_type": "enum",
        "enum_values": ["Pass", "Failed", "无法测试", "未测试"],
        "error_messages": {
            "required": "Aml SRI自测结果不能为空",
            "enum": "Aml SRI自测结果必须是: Pass, Failed, 无法测试, 未测试"
        }
    },
    "zeasn_merge_record": {
        "required": False,
        "max_length": 1000,
        "error_messages": {
            "max_length": "Zeasn合入记录不能超过1000个字符"
        }
    },
    "remarks": {
        "required": False,
        "max_length": 2000,
        "error_messages": {
            "max_length": "备注不能超过2000个字符"
        }
    }
}


class ValidationError:
    """验证错误"""
    def __init__(self, field: str, message: str, error_type: str = "validation"):
        self.field = field
        self.message = message
        self.error_type = error_type
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "error_type": self.error_type
        }


def validate_field(field_name: str, value: Any) -> List[ValidationError]:
    """验证单个字段"""
    errors = []
    
    if field_name not in FIELD_RULES:
        return errors
    
    rules = FIELD_RULES[field_name]
    error_messages = rules.get("error_messages", {})
    
    if rules.get("required", False):
        if value is None:
            errors.append(ValidationError(
                field=field_name,
                message=error_messages.get("required", "该字段不能为空"),
                error_type="required"
            ))
            return errors
        if isinstance(value, str) and not value.strip():
            errors.append(ValidationError(
                field=field_name,
                message=error_messages.get("required", "该字段不能为空"),
                error_type="required"
            ))
            return errors
        if isinstance(value, list) and len(value) == 0:
            errors.append(ValidationError(
                field=field_name,
                message=error_messages.get("required", "该字段不能为空"),
                error_type="required"
            ))
            return errors
    
    if value is None or (isinstance(value, str) and not value.strip()):
        return errors
    
    max_length = rules.get("max_length")
    if max_length and isinstance(value, str) and len(value) > max_length:
        errors.append(ValidationError(
            field=field_name,
            message=error_messages.get("max_length", f"不能超过{max_length}个字符"),
            error_type="max_length"
        ))
    
    field_type = rules.get("field_type")
    if field_type == "enum":
        enum_values = rules.get("enum_values", [])
        if enum_values and value not in enum_values:
            errors.append(ValidationError(
                field=field_name,
                message=error_messages.get("enum", f"值必须是 {', '.join(enum_values)} 之一"),
                error_type="enum"
            ))
    
    if field_type == "array":
        max_items = rules.get("max_items", 50)
        item_max_length = rules.get("item_max_length", 100)
        if isinstance(value, list) and len(value) > max_items:
            errors.append(ValidationError(
                field=field_name,
                message=error_messages.get("max_items", f"最多{max_items}个"),
                error_type="max_items"
            ))
        if isinstance(value, list) and item_max_length:
            for i, item in enumerate(value):
                if isinstance(item, str) and len(item) > item_max_length:
                    errors.append(ValidationError(
                        field=field_name,
                        message=error_messages.get("item_max_length", f"单个值不能超过{item_max_length}个字符"),
                        error_type="item_max_length"
                    ))
                    break
    
    return errors


def validate_patch_data(data: Dict[str, Any]) -> List[ValidationError]:
    """验证AML Patch数据"""
    all_errors = []
    
    for field_name in data:
        field_errors = validate_field(field_name, data.get(field_name))
        all_errors.extend(field_errors)
    
    return all_errors


def format_validation_errors(errors: List[ValidationError]) -> Dict[str, Any]:
    """格式化验证错误为标准响应格式"""
    if not errors:
        return {"valid": True, "errors": []}
    
    field_errors = {}
    for error in errors:
        if error.field not in field_errors:
            field_errors[error.field] = []
        field_errors[error.field].append(error.message)
    
    return {
        "valid": False,
        "errors": [e.to_dict() for e in errors],
        "field_errors": field_errors
    }


REQUIRED_FIELDS = [
    "project",
    "feature_branch",
    "corresponding_directory",
    "commit_record",
    "zmind_numbers",
    "amlogic_jira",
    "patch_provider",
    "is_odm_exclusive",
    "root_cause",
    "patch_solution",
    "impact_scope",
    "aml_sri_result"
]


def get_required_fields() -> List[str]:
    """获取必填字段列表"""
    return REQUIRED_FIELDS.copy()


def get_all_fields() -> List[str]:
    """获取所有字段列表"""
    return list(FIELD_RULES.keys())


def get_field_config(field_name: str) -> Optional[Dict[str, Any]]:
    """获取字段配置"""
    return FIELD_RULES.get(field_name)