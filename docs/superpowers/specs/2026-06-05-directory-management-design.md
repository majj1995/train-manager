# 数据源目录管理设计文档

## 背景

当前图片导入是一次性操作，没有持久化管理目录的能力。 用户期望将文件目录作为数据源进行持续管理——添加目录时自动导入图片，删除目录时智能移除图片。

## 需求

1. 添加目录作为数据源，自动扫描并导入该目录下所有图片文件（仅处理图片格式，忽略其他格式文件）
2. 删除目录时智能移除：如果一张图片只被该目录导入（无其他目录关联），则删除图片及级联数据；如果还被其他目录关联，则只解除关联、保留图片
3. 前端页面展示已添加的数据源目录列表，支持添加和删除操作

## 数据模型

### SourceDirectory（数据源目录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| path | VARCHAR(500), UNIQUE | 目录绝对路径 |
| recursive | BOOL | 是否递归扫描子目录 |
| image_count | INT | 该目录下已导入的图片数量 |
| created_at | DATETIME | 添加时间 |

### ImageSourceDirectory（图片-目录关联）

多对多关联表，记录每张图片是由哪些目录导入的。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| image_id | INT, FK → Image | 图片ID |
| directory_id | INT, FK → SourceDirectory | 目录ID |

同一张图片可关联多个目录（被两个不同目录导入时，第二次导入因哈希去重跳过创建，但建立关联记录）。

### Image 模型新增 relationship

在 Image 模型上增加 `source_directories` relationship，指向 SourceDirectory，通过 ImageSourceDirectory 关联表。

## 核心逻辑

### 添加目录

1. 校验目录路径是否存在且是否已添加过（path UNIQUE 约束）
2. 创建 SourceDirectory 记录
3. 扫描目录下所有文件， 仅处理 IMAGE_EXTENSIONS 中的格式
4. 对每张图片计算 file_hash:
   - hash 已存在于 Image 表: 跳过创建, 仅建立 ImageSourceDirectory 关联
   - hash 不存在: 创建 Image 记录 + 建立 ImageSourceDirectory 关联
5. 更新 SourceDirectory.image_count

### 删除目录（智能去重）

1. 查找 ImageSourceDirectory 中所有 directory_id = 该目录ID 的记录
2. 对每张关联的图片:
   - 查询该图片关联的目录总数（count）
   - count = 1: 删除 Image 记录（级联删除 ImageLabel、PreprocessResult、CorpusRecord）
   - count > 1: 仅删除 ImageSourceDirectory 关联, 保留 Image 记录
3. 删除 SourceDirectory 记录
4. 返回结果: {deleted_images_count, x, kept_images_count: y}

## API 端点

- `POST /api/directories` — 添加目录（参数: path, recursive）
- `GET /api/directories` — 列出所有目录
- `DELETE /api/directories/{id}` — 删除目录

## 前端改动

在 Images.vue 左侧 sidebar 中, 在"标签分组"卡片上方增加"数据源目录"卡片:
- 列表显示已添加的目录（path + image_count）
- 添加按钮: 弹出对话框, 输入目录路径 + 是否递归扫描开关
- 删除按钮: 认对话框, 显示将删除多少图片、保留多少图片

## 与现有功能的关系

- 原有的 `POST /api/images/import` 接口保留但不再作为主要入口
- 添加目录时优先使用新的 `/api/directories` 接口
- 原有的 import_images 服务函数改造为同时建立 ImageSourceDirectory 关联
- Image 模型增加 `source_directories` relationship