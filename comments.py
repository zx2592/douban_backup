"""从收藏条目里提取"我的评语"。

豆瓣四类收藏页对评语的标记并不统一：

* 电影：``<span class="comment">评语</span>``
* 书籍：``<p class="comment">评语</p>``
* 音乐：评语是 info 列表里最后一个**没有 class** 的 ``<li>``
* 游戏：评语是条目末尾一个**没有 class** 的 ``<p>``

原先四个解析器各自只认 ``.comment``，所以电影和书籍正常，音乐和游戏
永远抓不到评语——其余字段照常，只有"我的评语"一列全空。

这里把提取逻辑收敛成一个函数：优先用 ``.comment``（豆瓣哪天给音乐/游戏
补上这个 class 也能直接命中），命中不了再在纯文本的 ``li``/``p`` 里找。
"""

# 条目里除评语之外的文本块所用的 class。命中这些的节点不可能是评语。
_NON_COMMENT_CLASSES = {
    'title', 'intro', 'desc', 'date', 'pub', 'author', 'tags',
    'info', 'pic', 'nbg', 'pl', 'star', 'rating-info',
}

# 评分 class 形如 rating5-t / allstar40 / rating-star，统一按前缀排除。
_NON_COMMENT_PREFIXES = ('rating', 'allstar')

# 评语所在的标签。音乐用 li，游戏用 p，书影两类靠 .comment 命中。
_CANDIDATE_TAGS = ('li', 'p')


def _text(node):
    return node.get_text(' ', strip=True) if node else ''


def _is_excluded(node):
    """节点自身的 class 表明它是标题/简介/日期/评分等非评语内容。"""
    for cls in node.get('class', []):
        if cls in _NON_COMMENT_CLASSES:
            return True
        if cls.startswith(_NON_COMMENT_PREFIXES):
            return True
    return False


def _looks_like_comment(node):
    """只认纯文本节点。

    音乐把日期和评分包在一个同样没有 class 的 ``<li>`` 里，游戏条目里也有
    带链接的 ``<p>``；这类节点只要含有被排除的后代（或者链接、图片）就一律
    跳过，免得把日期或标题当成评语写进备份。
    """
    for child in node.find_all(True):
        if child.name in ('a', 'img', 'ul', 'ol', 'table'):
            return False
        if _is_excluded(child):
            return False
    return bool(_text(node))


def extract_comment(item, exclude_texts=()):
    """返回条目的"我的评语"，取不到时返回空字符串。

    ``exclude_texts`` 用于排除已经被解析成别的字段的文本（比如游戏的简介、
    音乐的艺术家信息），避免同一段内容既进简介又进评语。
    """
    tagged = item.select_one('.comment')
    if tagged is not None:
        return _text(tagged)

    skip = {text.strip() for text in exclude_texts if text and text.strip()}
    for node in item.find_all(_CANDIDATE_TAGS):
        if _is_excluded(node) or not _looks_like_comment(node):
            continue
        text = _text(node)
        if text in skip:
            continue
        return text
    return ''
