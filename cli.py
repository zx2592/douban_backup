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
