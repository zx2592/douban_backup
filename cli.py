"""命令行入口共用的辅助逻辑。"""


def exit_code(result):
    """把命令的返回值翻译成进程退出码。

    此前两个入口都直接丢弃 main() 的返回值，于是 Cookie 过期、抓取中断、
    校验不通过全都以退出码 0 结束，脚本化调用无法据此判断成败。

    约定：
    - None / False          -> 1（失败）
    - 带 "ok" 键的报告或结果 -> 按 ok 判定
    - 其他（如备份列表）     -> 0
    """
    if result is None or result is False:
        return 1
    if isinstance(result, dict) and "ok" in result:
        return 0 if result["ok"] else 1
    return 0


# 支持的导出格式。JSON 始终会写，它是结构化原始数据，不参与选择。
VALID_FORMATS = ('xlsx', 'csv', 'md')


def parse_formats(raw_value):
    """解析 --format 的取值，返回去重且顺序稳定的格式列表。"""
    if not raw_value:
        return ['xlsx']
    parts = [part.strip().lower() for part in raw_value.split(',') if part.strip()]
    if 'all' in parts:
        return list(VALID_FORMATS)

    invalid = [part for part in parts if part not in VALID_FORMATS]
    if invalid:
        raise ValueError(
            f"不支持的导出格式: {', '.join(invalid)}；"
            f"可选 {', '.join(VALID_FORMATS)} 或 all"
        )
    return [fmt for fmt in VALID_FORMATS if fmt in parts]


def export_all(storage, data, formats, timestamp):
    """按所选格式导出。JSON 无条件写出，作为结构化原始数据。"""
    storage.save_all_json(data, timestamp=timestamp)
    if 'xlsx' in formats:
        storage.save_all_excel(data, timestamp=timestamp)
    if 'csv' in formats:
        storage.save_all_csv(data, timestamp=timestamp)
    if 'md' in formats:
        storage.save_all_markdown(data, timestamp=timestamp)


def export_category(storage, category_data, data, formats, category, timestamp):
    """单分类导出。JSON 里只放该分类的数据，与既有行为一致。"""
    storage.save_category_json(category_data, category, timestamp=timestamp)
    if 'xlsx' in formats:
        storage.save_category_excel(data, category, timestamp=timestamp)
    if 'csv' in formats:
        storage.save_category_csv(data, category, timestamp=timestamp)
    if 'md' in formats:
        storage.save_category_markdown(data, category, timestamp=timestamp)
