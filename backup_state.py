import json
import os
import hashlib
from datetime import datetime

from config import APP_VERSION


class BackupState:
    def __init__(self, output_dir, user_id, filename=None):
        self.output_dir = output_dir
        self.user_id = user_id
        os.makedirs(self.output_dir, exist_ok=True)
        if filename is None:
            user_key = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
            filename = f"backup_state_{user_key}.json"
        self.path = os.path.join(self.output_dir, filename)
        self.state = self._load()

    def _default_state(self):
        return {
            "context": {
                "user_id": self.user_id,
                "app_version": APP_VERSION,
            },
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
            print(f"[WARN] 断点文件无法读取，将从头开始: {self.path}")
            return self._default_state()

        if state.get("context") != self._default_state()["context"]:
            print("[WARN] 断点所属账号或版本不匹配，将从头开始。")
            return self._default_state()
        return state

    def _save(self):
        self.state["updated_at"] = datetime.now().astimezone().isoformat()
        temp_path = f"{self.path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file_obj:
            json.dump(self.state, file_obj, ensure_ascii=False, indent=2)
            file_obj.flush()
            os.fsync(file_obj.fileno())
        os.replace(temp_path, self.path)

    def _entry(self, category, collection):
        category_state = self.state["collections"].setdefault(category, {})
        return category_state.setdefault(
            collection,
            {
                "current_url": None,
                "next_url": None,
                "completed": False,
                "items": [],
            },
        )

    def update_progress(self, category, collection, current_url, next_url, items):
        entry = self._entry(category, collection)
        entry["current_url"] = current_url
        entry["next_url"] = next_url
        entry["completed"] = False
        entry["items"] = list(items)
        self._save()

    def mark_complete(self, category, collection, items):
        entry = self._entry(category, collection)
        entry["current_url"] = None
        entry["next_url"] = None
        entry["completed"] = True
        entry["items"] = list(items)
        self._save()

    def get_resume_url(self, category, collection):
        entry = self._entry(category, collection)
        return entry.get("next_url")

    def get_partial_items(self, category, collection):
        entry = self._entry(category, collection)
        return list(entry.get("items", []))

    def is_collection_complete(self, category, collection):
        entry = self._entry(category, collection)
        return bool(entry.get("completed"))

    def has_incomplete_collections(self):
        for category_state in self.state["collections"].values():
            for entry in category_state.values():
                if not entry.get("completed"):
                    return True
        return False

    def clear(self):
        self.state = self._default_state()
        if os.path.exists(self.path):
            os.remove(self.path)
