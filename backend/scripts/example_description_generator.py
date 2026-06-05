"""示例预处理脚本：模拟生成图片描述
输入: {"image_id": ..., "file_path": ..., "width": ..., "height": ..., "format": ..., "parent_result": null}
输出: {"description": "...", "label_group_id": 1}
脚本必须将输出赋值给 _output 变量，因为引擎会自动将 _output 写入输出文件。
"""
_output = {
    "description": f"图片 {_input['file_path']} 的模拟描述内容",
    "label_group_id": 1,
}