# 标签管理独立页签与层级化标签设计文档

## 背景

当前前端只有创建标签分组的入口，缺少在分组下创建标签的功能。标签管理混杂在数据管理页面的侧边栏中，缺乏专门的标签 CRUD 界面。同时，标签体系是扁平的，不支持层级嵌套，无法满足"违规 > 涏黄 > 色情描写"这样的细化分类需求。

## 需求

1. 标签支持不限层级嵌套（parent_id 自引用），分组内形成独立标签树
2. 任意层级标签均可作为标注结果（不仅限于叶子标签）
3. 标签管理独立为单独页签，提供完整的标签分组和标签 CRUD 界面
4. 导航顺序：数据管理 | 标签管理 | 数据标注 | 预处理 | 语料生成

## 数据模型

### Label 表改动

在现有 `labels` 表上新增 `parent_id` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR(100) | 标签名称 |
| description | VARCHAR(500), nullable | 标签描述 |
| color | VARCHAR(20), nullable, default "#409EFF" | 展示颜色 |
| group_id | INT, FK → label_groups.id | 所属标签分组（不变） |
| parent_id | INT, FK → labels.id, nullable | **新增**，父标签ID，NULL表示顶层标签 |
| created_at | DATETIME | 创建时间 |

约束：parent_id 指向的标签必须属于同一 group_id（业务层校验，不设数据库约束以避免跨表检查复杂性）。

删除策略：删除非叶子标签时，子标签的 parent_id 级联置 NULL（子标签变为该分组下的顶层标签），不级联删除子标签，避免误删大量标注数据。

### 其他模型

ImageLabel、PreprocessResult、CorpusRecord 等关联不变。ImageLabel.label_id 可指向任意层级标签。

## API 端点

### 标签分组（不变）
- `POST /api/labels/groups` — 创建分组
- `GET /api/labels/groups` — 列出分组
- `DELETE /api/labels/groups/{id}` — 删除分组

### 标签 CRUD（修改/新增）
- `POST /api/labels/groups/{group_id}/labels` — 创建标签（新增 parent_id 参数）
- `GET /api/labels/groups/{group_id}/labels` — 列出分组下所有标签（扁平列表）
- `GET /api/labels/groups/{group_id}/tree` — **新增**，返回分组下的标签树（嵌套 JSON）
- `PUT /api/labels/{label_id}` — **新增**，更新标签（名称、颜色、描述、移动 parent_id）
- `DELETE /api/labels/{label_id}` — 删除标签（子标签 parent_id 置 NULL）

### 批量标注（不变）
- `POST /api/labels/batch-add`
- `POST /api/labels/batch-remove`

### 树结构响应格式

```json
[
  {
    "id": 1,
    "name": "违规",
    "color": "#F56C6C",
    "parent_id": null,
    "children": [
      {"id": 2, "name": "涉黄", "color": "#E6A23C", "parent_id": 1, "children": [
        {"id": 3, "name": "色情描写", "color": "#E6A23C", "parent_id": 2, "children": []}
      ]},
      {"id": 4, "name": "涉暴", "color": "#F56C6C", "parent_id": 1, "children": []}
    ]
  },
  {"id": 5, "name": "正常", "color": "#67C23A", "parent_id": null, "children": []}
]
```

## 前端设计

### 标签管理页签（Labels.vue）

布局：左侧选择标签分组 + 右侧显示该分组下的标签树（el-tree）。

左侧：
- 标签分组列表，点击切换右侧树
- 创建分组按钮（el-dialog）
- 删除分组按钮

右侧（选中分组后）：
- el-tree 展示层级标签，每个节点显示名称 + 颜色色块
- 点击节点弹出编辑面板：修改名称、颜色、描述、parent_id（拖拽或下拉选择父标签）
- "添加子标签"按钮：在选中节点下添加子标签
- "添加顶层标签"按钮：在分组根层级添加标签
- "删除标签"按钮：删除当前选中标签

### 标注页面（Labeling.vue）

标注面板中展示标签树而非扁平列表，用户可勾选任意层级标签进行标注。

### 数据管理页面（Images.vue）

移除侧边栏中的标签分组管理部分（分组和标签的 CRUD 迁移到 Labels.vue），仅保留标签分组选择下拉用于过滤图片。
