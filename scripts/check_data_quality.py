#!/usr/bin/env python3
"""데이터 품질 확인 스크립트"""

import json
import os
from pathlib import Path

def check_data_quality():
    data_dir = Path("data/raw")

    real_conversations = []
    template_files = []

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
                        template_files.append(str(json_file))
                    else:
                        real_conversations.append(str(json_file))
            except Exception as e:
                print(f"오류: {json_file}: {e}")

    print("="*70)
    print("📊 데이터 품질 분석 결과")
    print("="*70)
    print(f"\n✅ 실제 대화 파일: {len(real_conversations)}개")
    print(f"⚠️  템플릿 파일: {len(template_files)}개")
    print(f"📁 전체 파일: {len(real_conversations) + len(template_files)}개")

    if len(real_conversations) > 0:
        print(f"\n실제 대화 예시 (처음 5개):")
        for file in sorted(real_conversations)[:5]:
            print(f"  - {Path(file).name}")

    if len(template_files) > 0:
        print(f"\n템플릿 파일 예시 (처음 5개):")
        for file in sorted(template_files)[:5]:
            print(f"  - {Path(file).name}")

    print("\n" + "="*70)

    return len(real_conversations), len(template_files)

if __name__ == "__main__":
    check_data_quality()
