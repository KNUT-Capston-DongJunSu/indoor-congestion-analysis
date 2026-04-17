#!/usr/bin/env python
import os
import sys
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent
    SRC_DIR = BASE_DIR / "src"

    # src를 모듈 경로에 추가해서 'core', 'apps' 등을 import 가능하게 함
    if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    # 👇 실제 settings 경로로 교체
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()

