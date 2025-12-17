#!/usr/bin/env python3
"""템플릿 파일 삭제 스크립트"""

import json
import os
from pathlib import Path

def delete_template_files():
    data_dir = Path("data/raw")

    deleted_count = 0
    kept_count = 0

    for json_file in data_dir.glob("**/*.json"):
        if json_file.name.startswith("conv_"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 첫 번째 대화 확인
                if data.get('conversation') and len(data['conversation']) > 0:
                    first_client_text = data['conversation'][0].get('text', '')

                    # 템플릿 텍스트인지 확인
                    if '내담자 발화' in first_client_text or '관련 고민' in first_client_text:
                        os.remove(json_file)
                        deleted_count += 1
                        if deleted_count % 500 == 0:
                            print(f"  삭제 중... {deleted_count}개")
                    else:
                        kept_count += 1
            except Exception as e:
                print(f"오류: {json_file}: {e}")

    print(f"\n✅ 삭제 완료: {deleted_count}개")
    print(f"✅ 유지: {kept_count}개")
    return deleted_count, kept_count

if __name__ == "__main__":
    print("템플릿 파일 삭제 시작...")
    delete_template_files()
