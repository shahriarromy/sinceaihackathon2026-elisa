"""Persistent tracker for processed channel items to ensure idempotency."""

import json
import logging
import os
from pathlib import Path
from typing import Set
from agents.config import STATE_STORAGE_PATH

logger = logging.getLogger("agents.state_store")


class StateStore:
    def __init__(self, file_path: str = STATE_STORAGE_PATH):
        self.file_path = Path(file_path)

    def _load(self) -> Set[str]:
        if not self.file_path.exists():
            return set()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception as e:
            logger.error(f"Error reading state file {self.file_path}: {e}")
            return set()

    def is_processed(self, item_id: str) -> bool:
        """Check if an item ID has already been ingested."""
        return item_id in self._load()

    def mark_processed(self, item_ids: list[str]) -> None:
        """Mark a list of item IDs as processed."""
        current = self._load()
        current.update(item_ids)
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({"processed_ids": sorted(current)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state file {self.file_path}: {e}")

    def reset(self) -> None:
        """Clear processed state (useful for test resets)."""
        if self.file_path.exists():
            try:
                self.file_path.unlink()
            except Exception as e:
                logger.error(f"Error removing state file: {e}")

        ca_file = self.file_path.with_name("captured_assertions.json")
        if ca_file.exists():
            try:
                ca_file.unlink()
            except Exception as e:
                logger.error(f"Error removing captured assertions file: {e}")

    def save_captured_assertions(self, assertions: list[dict]) -> None:
        """Cache captured assertions for resilient state lookup."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            ca_file = self.file_path.with_name("captured_assertions.json")
            existing = self.get_captured_assertions()
            existing_map = {f"{c.get('title')}:{c.get('source_ref')}": c for c in existing}
            for a in assertions:
                existing_map[f"{a.get('title')}:{a.get('source_ref')}"] = a
            with open(ca_file, "w", encoding="utf-8") as f:
                json.dump(list(existing_map.values()), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving captured assertions: {e}")

    def get_captured_assertions(self) -> list[dict]:
        """Retrieve cached captured assertions."""
        ca_file = self.file_path.with_name("captured_assertions.json")
        if not ca_file.exists():
            return []
        try:
            with open(ca_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading captured assertions: {e}")
            return []
