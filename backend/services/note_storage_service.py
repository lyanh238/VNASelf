"""
JSON Storage for Notes
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiofiles


class NoteStorageService:
    """Store notes as JSON files for fast local access.

    Storage layout:
      notes/
        all.json                # append-only list of notes (all users)
        {user_id}.json          # per-user notes (if user_id provided)
    """

    def __init__(self, storage_dir: str = "notes"):
        self.storage_dir = storage_dir
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            if not os.path.exists(self.storage_dir):
                os.makedirs(self.storage_dir)
                print(f"[OK] Created notes storage directory: {self.storage_dir}")
            self._initialized = True
            print("[OK] Note Storage Service initialized")
        except Exception as e:
            print(f"[ERROR] Error initializing Note Storage: {str(e)}")
            self._initialized = True

    def _file_path(self, user_id: Optional[str]) -> str:
        if user_id and user_id.strip():
            safe = user_id.replace('/', '_').replace('\\', '_')
            return os.path.join(self.storage_dir, f"{safe}.json")
        return os.path.join(self.storage_dir, "all.json")

    async def _read(self, path: str) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(path):
                return []
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content.strip() else []
        except Exception:
            return []

    async def _write(self, path: str, data: List[Dict[str, Any]]) -> bool:
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except Exception:
            return False

    async def add_note(self, note: Dict[str, Any]) -> bool:
        if not self._initialized:
            return False
        # Write to all.json
        all_path = self._file_path(None)
        all_notes = await self._read(all_path)
        note_with_id = {**note, "local_id": len(all_notes) + 1}
        all_notes.append(note_with_id)
        ok_all = await self._write(all_path, all_notes)

        # Write to per-user if user_id exists
        ok_user = True
        user_id = note.get("user_id")
        if user_id:
            user_path = self._file_path(user_id)
            user_notes = await self._read(user_path)
            user_notes.append(note_with_id)
            ok_user = await self._write(user_path, user_notes)

        return ok_all and ok_user

    async def list_notes(self, user_id: Optional[str] = None, limit: int = 20, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._initialized:
            return []
        path = self._file_path(user_id)
        notes = await self._read(path)
        # Newest first by timestamp if present
        notes.sort(key=lambda n: n.get("timestamp", 0), reverse=True)
        if category:
            notes = [n for n in notes if n.get("category") == category]
        return notes[:limit]


