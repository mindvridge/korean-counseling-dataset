#!/usr/bin/env python3
"""
실패한 대화 파일 식별 및 목록 생성
"""

import json
from pathlib import Path
from collections import defaultdict


def main():
    base_dir = Path("/home/user/korean-counseling-dataset/data/raw")

    # QualityValidator와 동일한 검증 로직 사용
    from validate_quality import QualityValidator

    validator = QualityValidator()

    failed_files = {
        "adolescent": [],
        "adult": [],
        "crisis": []
    }

    for category in ["adolescent", "adult", "crisis"]:
        cat_dir = base_dir / category
        if not cat_dir.exists():
            continue

        files = sorted(list(cat_dir.glob("conv_*.json")))

        for filepath in files:
            passed, failures = validator.validate_file(filepath)

            if not passed:
                failed_files[category].append({
                    "path": str(filepath),
                    "filename": filepath.name,
                    "failures": failures
                })

    # 결과 저장
    output_file = Path("/home/user/korean-counseling-dataset/failed_files.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(failed_files, f, ensure_ascii=False, indent=2)

    # 통계 출력
    print("❌ 실패한 파일 통계:")
    for category, files in failed_files.items():
        print(f"  • {category:12s}: {len(files):,}개")

    total_failed = sum(len(files) for files in failed_files.values())
    print(f"\n  총 실패: {total_failed:,}개")
    print(f"\n📄 실패 파일 목록 저장: {output_file}")


if __name__ == "__main__":
    main()
