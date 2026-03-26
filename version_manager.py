# version_manager.py
import os
import json
import re
import sys
from pathlib import Path

class VersionManager:
    def __init__(self, version_file='version.json'):
        self.version_file = Path(version_file)
        self.version = self._load_version()
    
    def _load_version(self):
        """加载版本号"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                data = json.load(f)
                return data.get('version', '1.0.0')
        return '1.0.0'
    
    def _save_version(self):
        """保存版本号"""
        with open(self.version_file, 'w') as f:
            json.dump({'version': self.version}, f, indent=2)
    
    def _parse_version(self, version_str):
        """解析版本号"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return 1, 0, 0
    
    def bump_patch(self):
        """补丁版本递增 1.0.0 -> 1.0.1"""
        major, minor, patch = self._parse_version(self.version)
        self.version = f"{major}.{minor}.{patch + 1}"
        self._save_version()
        return self.version
    
    def bump_minor(self):
        """次版本递增 1.0.0 -> 1.1.0"""
        major, minor, _ = self._parse_version(self.version)
        self.version = f"{major}.{minor + 1}.0"
        self._save_version()
        return self.version
    
    def bump_major(self):
        """主版本递增 1.0.0 -> 2.0.0"""
        major, _, _ = self._parse_version(self.version)
        self.version = f"{major + 1}.0.0"
        self._save_version()
        return self.version
    
    def set_version(self, version):
        """设置指定版本"""
        if re.match(r'^\d+\.\d+\.\d+$', version):
            self.version = version
            self._save_version()
            return self.version
        raise ValueError(f"Invalid version format: {version}")

if __name__ == "__main__":
    vm = VersionManager()
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == 'patch':
            new_version = vm.bump_patch()
        elif action == 'minor':
            new_version = vm.bump_minor()
        elif action == 'major':
            new_version = vm.bump_major()
        elif action == 'set' and len(sys.argv) > 2:
            new_version = vm.set_version(sys.argv[2])
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
        
        print(f"new_version={new_version}")
    else:
        print(f"current_version={vm.version}")
