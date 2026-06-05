"""示例预处理脚本：基于上游描述结果判断违规类别（续接任务）
输入: {"image_id": ..., "file_path": ..., ..., "parent_result": {"description": "..."}}
输出: {"predicted_labels": ["正常"], "confidence": {"正常": 0.95}, "label_group_id": 1}
"""
_output = {
    "predicted_labels": ["正常"],
    "confidence": {"正常": 0.95},
    "label_group_id": 1,
}