"""
Anya File Manager — Safe file operations.
"""

import os
import shutil
import subprocess
import platform
import datetime
import glob
from pathlib import Path
from typing import List, Optional, Callable

SYSTEM = platform.system()


class FileManager:
    def __init__(self, speaker=None):
        self.speaker = speaker
        self.home = str(Path.home())
        self._trash = os.path.join(self.home, ".anya_trash")
        os.makedirs(self._trash, exist_ok=True)

    def open_file_manager(self, path: str = None) -> str:
        target = path or self.home
        try:
            if SYSTEM == "Windows":
                subprocess.Popen(["explorer", target])
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", target])
            else:
                for fm in ["nautilus", "thunar", "dolphin", "nemo", "xdg-open"]:
                    try:
                        subprocess.Popen([fm, target])
                        break
                    except FileNotFoundError:
                        continue
            return f"📂 Opened file manager at:\n{target}"
        except Exception as e:
            return f"❌ Error: {e}"

    def open_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            results = self.search_files(os.path.basename(path))
            if results:
                path = results[0]
            else:
                return f"❌ File not found: {path}"
        try:
            if SYSTEM == "Windows":
                os.startfile(path)
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return f"✅ Opened: {path}"
        except Exception as e:
            return f"❌ Error: {e}"

    def create_file(self, name: str, content: str = "", folder: str = None) -> str:
        folder = folder or os.path.join(self.home, "Documents")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        if os.path.exists(path):
            base, ext = os.path.splitext(name)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(folder, f"{base}_{ts}{ext}")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Created: {path}"
        except Exception as e:
            return f"❌ Error: {e}"

    def create_folder(self, name: str, parent: str = None) -> str:
        parent = parent or self.home
        path = os.path.join(parent, name)
        try:
            os.makedirs(path, exist_ok=True)
            return f"✅ Created folder: {path}"
        except Exception as e:
            return f"❌ Error: {e}"

    def delete_file(self, path: str, force: bool = False) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Not found: {path}"
        try:
            if force:
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
                return f"✅ Deleted: {path}"
            else:
                dest = os.path.join(self._trash, os.path.basename(path))
                shutil.move(path, dest)
                return f"🗑️ Moved to Anya Trash:\n{dest}"
        except Exception as e:
            return f"❌ Error: {e}"

    def restore_from_trash(self, name: str) -> str:
        src = os.path.join(self._trash, name)
        if not os.path.exists(src):
            return f"❌ '{name}' not in trash."
        dest = os.path.join(self.home, "Documents", name)
        shutil.move(src, dest)
        return f"✅ Restored to: {dest}"

    def search_files(self, query: str, start_dir: str = None, limit: int = 20) -> List[str]:
        start_dir = start_dir or self.home
        matches = []
        try:
            for match in Path(start_dir).glob(f"**/*{query}*"):
                matches.append(str(match))
                if len(matches) >= limit:
                    break
        except PermissionError:
            pass
        return sorted(matches)

    def search_and_format(self, query: str) -> str:
        results = self.search_files(query)
        if not results:
            return f"🔍 No files found matching '{query}'."
        lines = [f"🔍 Found {len(results)} match(es) for '{query}':"]
        for i, r in enumerate(results[:15], 1):
            lines.append(f"  {i}. {r}")
        if len(results) > 15:
            lines.append(f"  … and {len(results) - 15} more.")
        return "\n".join(lines)

    def list_directory(self, path: str = None) -> str:
        path = os.path.expanduser(path or self.home)
        if not os.path.isdir(path):
            return f"❌ Not a directory: {path}"
        try:
            items = os.listdir(path)
            dirs = [i for i in items if os.path.isdir(os.path.join(path, i))]
            files = [i for i in items if os.path.isfile(os.path.join(path, i))]
            lines = [f"📂 {path}", f"  {len(dirs)} folder(s), {len(files)} file(s)", ""]
            for d in sorted(dirs)[:20]:
                lines.append(f"  📁 {d}/")
            for f in sorted(files)[:20]:
                lines.append(f"  📄 {f}")
            return "\n".join(lines)
        except PermissionError:
            return f"❌ Permission denied: {path}"

    def get_file_info(self, path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Not found: {path}"
        stat = os.stat(path)
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        kind = "📁 Folder" if os.path.isdir(path) else "📄 File"
        size = self._fmt(stat.st_size)
        return f"{kind}: {os.path.basename(path)}\n  Path: {path}\n  Size: {size}\n  Modified: {modified}"

    @staticmethod
    def _fmt(size: int) -> str:
        for u in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {u}"
            size //= 1024
        return f"{size:.1f} TB"
