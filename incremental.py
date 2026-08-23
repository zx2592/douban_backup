"""增量备份支持。

豆瓣的收藏页按标记时间倒序排列，因此从第一页往后抓时，一旦遇到上次备份
中已经存在、且内容没有变化的条目，就可以断定它后面的条目也都已经备份过，
不必继续翻页。本模块提供这一判断所需的指纹、截断和合并逻辑，以及记录上
次备份结果的基线存储。

需要注意的取舍：
- 判断"没有变化"用的是指纹而不只是条目 ID。用户修改评分或评语会让条目
  重新排到最前面，若只比 ID 就会把它当成已备份而跳过，改动就丢了。
- 增量模式无法感知"用户删除了某条收藏"——那条记录不会再出现在页面上，
  但它仍留在基线里。需要清理删除项时应运行一次完整备份。
"""

import hashlib
import json
import os
from datetime import datetime

# 参与"是否发生变化"判断的字段。不同分类的字段不完全一致（例如音乐没有
# 标记日期），取值一律用 get 兜底，缺失字段视为空串。
FINGERPRINT_KEYS = ("title", "rating", "comment", "date", "tags")

BASELINE_FORMAT = 1


def item_key(item):
    """条目的稳定标识。豆瓣 ID 缺失时退回标题，避免整页被当成新条目。"""
    douban_id = str(item.get("douban_id") or "").strip()
    if douban_id:
        return f"id:{douban_id}"
    return "title:" + str(item.get("title") or "").strip()


def item_fingerprint(item):
    """条目中会被用户改动的字段快照。"""
    return tuple(str(item.get(key, "") or "") for key in FINGERPRINT_KEYS)


def build_index(items):
    """把基线条目转成 {标识: 指纹}，供翻页时快速比对。"""
    return {item_key(item): item_fingerprint(item) for item in items}


def take_until_known(items, index):
    """截断当前页，返回 (需要保留的条目, 是否已到达基线边界)。

    逐条扫描：遇到第一个"已存在且指纹相同"的条目就停止，该条目及其后面的
    条目都不再返回。已存在但指纹不同的条目（用户改了评分或评语）会被保留，
    并继续往后扫描。
    """
    if not index:
        return list(items), False

    fresh = []
    for item in items:
        key = item_key(item)
        if key in index and index[key] == item_fingerprint(item):
            return fresh, True
        fresh.append(item)
    return fresh, False


def merge_items(fresh, baseline_items):
    """合并本次抓到的条目与基线条目。

    新抓到的排在前面（它们的标记时间更新），基线中剩下的保持原有顺序。
    同一条目以本次抓到的版本为准，这样用户的修改才能覆盖旧数据。
    """
    seen = set()
    merged = []
    for item in fresh:
        key = item_key(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    for item in baseline_items:
        key = item_key(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


class Baseline:
    """上次成功备份的完整条目快照，按豆瓣账号隔离。

    与 BackupState（断点）不同：断点记录的是"这次跑到哪了"，跑完即清空；
    基线记录的是"上次备份的全部结果"，长期保留，供下次增量比对。
    """

    def __init__(self, output_dir, user_id, filename=None):
        self.output_dir = output_dir
        self.user_id = user_id
        os.makedirs(self.output_dir, exist_ok=True)
        if filename is None:
            user_key = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
            filename = f"backup_baseline_{user_key}.json"
        self.path = os.path.join(self.output_dir, filename)
        self.state = self._load()

    def _default_state(self):
        return {
            "format": BASELINE_FORMAT,
            "user_id": self.user_id,
            "updated_at": None,
            "collections": {},
        }

    def _load(self):
        if not os.path.exists(self.path):
            return self._default_state()

        try:
            with open(self.path, "r", encoding="utf-8") as file_obj:
                state = json.load(file_obj)
        except (OSError, json.JSONDecodeError):
            print(f"[WARN] 基线文件无法读取，本次将做完整备份: {self.path}")
            return self._default_state()

        # 只在账号或基线格式不匹配时作废。应用版本升级不应清空基线，
        # 否则每次升级后的第一次增量备份都会退化成全量抓取。
        if state.get("user_id") != self.user_id:
            print("[WARN] 基线属于其他账号，本次将做完整备份。")
            return self._default_state()
        if state.get("format") != BASELINE_FORMAT:
            print("[WARN] 基线格式已变更，本次将做完整备份。")
            return self._default_state()
        return state

    def get_items(self, category, collection):
        category_state = self.state.get("collections", {}).get(category, {})
        return list(category_state.get(collection, []))

    def index_for(self, category, collection):
        return build_index(self.get_items(category, collection))

    def is_empty(self):
        for category_state in self.state.get("collections", {}).values():
            for items in category_state.values():
                if items:
                    return False
        return True

    def update(self, category, collection, items):
        category_state = self.state.setdefault("collections", {}).setdefault(category, {})
        category_state[collection] = list(items)

    def save(self):
        self.state["updated_at"] = datetime.now().astimezone().isoformat()
        temp_path = f"{self.path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file_obj:
            json.dump(self.state, file_obj, ensure_ascii=False, indent=2)
            file_obj.flush()
            os.fsync(file_obj.fileno())
        os.replace(temp_path, self.path)
        return self.path
