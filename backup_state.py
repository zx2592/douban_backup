import json
import os
from datetime import datetime


class BackupState:
    def __init__(self, output_dir, filename="backup_state.json"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.path = os.path.join(self.output_dir, filename)
        self.state = self._load()

    def _default_state(self):
        return {
            "updated_at": None,
            "collections": {},
        }

    def _load(self):
        if not os.path.exists(self.path):
            return self._default_state()

        with open(self.path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)

    def _save(self):
        self.state["updated_at"] = datetime.now().astimezone().isoformat()
        with open(self.path, "w", encoding="utf-8") as file_obj:
            json.dump(self.state, file_obj, ensure_ascii=False, indent=2)

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

    def clear(self):
        self.state = self._default_state()
        if os.path.exists(self.path):
            os.remove(self.path)
