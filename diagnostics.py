def classify_response(response):
    if response is None:
        return "error", "request_failed", "请求失败，请稍后重试。"

    status_code = getattr(response, "status_code", 0)
    response_url = getattr(response, "url", "") or ""
    response_text = getattr(response, "text", "") or ""

    if "accounts/login" in response_url:
        return "error", "login_expired", "登录已失效，请重新导入 Cookie。"

    if status_code == 403 or "异常请求" in response_text:
        return "error", "rate_limited", "请求受限，可能触发了豆瓣风控。"

    if status_code == 404 or "页面不存在" in response_text:
        return "error", "not_found", "页面不存在，或当前账号没有访问权限。"

    if status_code >= 500:
        return "error", "server_error", "豆瓣服务暂时不可用。"

    return "ok", "ok", "可访问"


def describe_empty_parse(response):
    response_text = getattr(response, "text", "") or ""
    empty_markers = (
        "暂无",
        "还没有",
        "没有内容",
        "没有找到",
    )
    if any(marker in response_text for marker in empty_markers):
        return "当前分类暂无数据。"
    return "页面返回成功，但未解析到条目，可能是页面结构发生了变化。"
