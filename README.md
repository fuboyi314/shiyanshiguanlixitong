# 实验室管理系统（排课数据处理基础模块）

本仓库提供实验排课场景中的数据建模、Excel 导入导出、字段映射和示例数据生成能力，便于后续接入 UI 与排课算法。

## 1. 安装

### 环境要求

- Python 3.10+
- 推荐使用虚拟环境

### 安装依赖

```bash
pip install pandas openpyxl
```

## 2. 运行

### 2.1 生成示例 Excel 数据

```bash
python sample_data/generate_sample_data.py
```

执行后会在 `sample_data/` 下生成：

- `theory_schedule.xlsx`
- `labs.xlsx`
- `lab_tasks.xlsx`

### 2.2 按字段映射读取 Excel

示例代码：

```python
from services.excel_loader import load_theory_class_slots, load_labs, load_lab_tasks
from utils.config import merge_user_field_mappings

# 模拟 UI 传入的用户自定义映射（仅覆盖了一个字段）
user_mapping = {
    "task": {
        "project_name": "实验名称"
    }
}

field_mappings = merge_user_field_mappings(user_mapping)

theory_slots = load_theory_class_slots("sample_data/theory_schedule.xlsx", field_mappings["theory"])
labs = load_labs("sample_data/labs.xlsx", field_mappings["lab"])
tasks = load_lab_tasks("sample_data/lab_tasks.xlsx", field_mappings["task"])
```

### 2.3 导出排课结果（多 Sheet）

`services/exporter.py` 提供 `export_schedule_result`，可导出：

1. 已排课
2. 未排课
3. 实验室利用率
4. 班级统计

```python
from services.exporter import export_schedule_result

export_schedule_result(
    output_path="schedule_result.xlsx",
    scheduled_items=[...],
    unscheduled_items=[...],
)
```

## 3. Excel 模板字段说明

> 默认字段在 `utils/config.py` 里维护，可按 UI 配置动态覆盖。

### 3.1 理论课（theory）

- 班级（`class_name`）
- 课程（`course_name`）
- 教师（`teacher`）
- 星期（`weekday`）
- 开始节次（`start_period`）
- 结束节次（`end_period`）
- 周次（`weeks`，支持 `1,2,3` 或 `1-16`）
- 学期（`semester`）

### 3.2 实验室（lab）

- 实验室编号（`lab_id`）
- 实验室名称（`lab_name`）
- 容量（`capacity`）
- 校区（`campus`）
- 可用课程（`supported_courses`，逗号分隔）

### 3.3 实验任务（task）

- 任务编号（`task_id`）
- 班级（`class_name`）
- 课程（`course_name`）
- 实验项目（`project_name`）
- 人数（`student_count`）
- 时长节次（`duration_periods`）
- 期望周（`expected_week`，可空）
- 期望星期（`expected_weekday`，可空）
- 教师（`teacher`，可空）
- 备注（`notes`，可空）

## 4. 字段映射说明（支持 UI 调整）

`utils/config.py` 中：

- `DEFAULT_FIELD_MAPPINGS`：三类默认映射（theory/lab/task）
- `get_default_field_mappings()`：返回可安全修改的副本
- `merge_user_field_mappings(user_mappings)`：将 UI 增量映射覆盖到默认映射

前端/配置中心可按如下结构传入：

```json
{
  "task": {
    "project_name": "实验名称",
    "student_count": "学生数"
  }
}
```

## 5. 常见错误排查

1. **报错：`缺少列`**
   - 原因：Excel 表头与当前字段映射不一致。
   - 处理：检查表头拼写，或在 UI 中更新字段映射。

2. **报错：`不是有效整数`**
   - 原因：如 `人数/星期/节次` 出现文本值（如“约40人”）。
   - 处理：改为纯数字，或在导入前做数据清洗。

3. **周次解析异常**
   - 原因：`周次` 格式不符合 `1,2,3` 或 `1-16`。
   - 处理：统一周次填写规则，避免非法字符。

4. **导出文件为空**
   - 原因：传入 `scheduled_items`/`unscheduled_items` 为空。
   - 处理：检查排课算法输出阶段是否返回了结果。

## 6. 扩展点建议

1. **教师冲突检测**
   - 在排课阶段叠加 teacher + week + weekday + period 约束，避免教师双占用。

2. **手工调课支持**
   - 为 `ScheduledItem` 增加锁定字段（如 `locked=True`），二次排课时跳过被锁定记录。

3. **班级拆分排课**
   - 对超大班任务拆分为多个子任务（A/B 班），分别匹配容量与时段。

4. **高级利用率分析**
   - 结合学期配置计算理论可用时段，输出实验室利用率百分比与峰值时段热力统计。



## 7. 测试与试运行文件

仓库已提供 `tests/` 下的部署后试运行测试文件（基于 `unittest`）：

- `tests/test_models.py`：验证核心数据模型可正常实例化。
- `tests/test_config.py`：验证字段映射默认值与 UI 增量覆盖逻辑。
- `tests/test_excel_loader.py`：验证 Excel 导入、字段转换与异常抛出。
- `tests/test_exporter.py`：验证多 Sheet 导出结果结构。
- `tests/test_sample_data_generator.py`：验证示例数据生成脚本输出文件。

执行方式：

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

> 说明：涉及 Excel 读写的测试依赖 `pandas/openpyxl`，若环境未安装会自动 `skip`，不会阻塞其它测试。

## 8. 本地网页界面（手工维护配置）

为方便部署后试运行，新增了一个本地 Web 配置界面，可手动维护：

- 理论课（班级/课程/教师/星期/节次/周次）
- 实验室（编号/名称/容量/校区/可用课程）
- 学期配置（学期名/开学日期/总周数/每日节次/工作日）
- 法定节假日（日期+名称）

### 启动界面

```bash
python -m webui.server --port 8000
```

浏览器打开：`http://127.0.0.1:8000`

### 数据存储

- 界面加载与保存均走 `/api/config`
- 默认配置文件：`data/ui_config.json`
- 你可以直接编辑该 JSON，或在网页里维护后点击“保存配置”。

