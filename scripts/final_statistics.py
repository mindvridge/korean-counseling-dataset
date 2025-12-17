#!/usr/bin/env python3
"""최종 데이터셋 생성 통계"""

import json
from pathlib import Path

def main():
    data_dir = Path("data/raw")

    # 카테고리별 파일 카운트
    categories = {
        "adolescent": "청소년",
        "adult": "성인",
        "crisis": "위기대응"
    }

    counts = {}
    for cat_en, cat_kr in categories.items():
        cat_dir = data_dir / cat_en
        if cat_dir.exists():
            counts[cat_en] = len(list(cat_dir.glob("conv_*.json")))
        else:
            counts[cat_en] = 0

    total = sum(counts.values())

    print("=" * 70)
    print("🎉 한국어 심리상담 데이터셋 생성 완료!")
    print("=" * 70)
    print()
    print(f"📊 전체 생성 개수: {total:,}개")
    print()
    print("📈 카테고리별 분포:")
    print(f"  ├─ 청소년(adolescent): {counts['adolescent']:,}개 ({counts['adolescent']/total*100:.1f}%) [목표: 55%]")
    print(f"  ├─ 성인(adult): {counts['adult']:,}개 ({counts['adult']/total*100:.1f}%) [목표: 40%]")
    print(f"  └─ 위기대응(crisis): {counts['crisis']:,}개 ({counts['crisis']/total*100:.1f}%) [목표: 5%]")
    print()

    # 샘플 파일 검증
    print("✅ 샘플 파일 검증:")
    sample_files = [
        data_dir / "adolescent" / "conv_adolescent_000001.json",
        data_dir / "adult" / "conv_adult_005000.json",
        data_dir / "crisis" / "conv_crisis_009800.json"
    ]

    for sample_file in sample_files:
        if sample_file.exists():
            try:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    turns = data['metadata']['total_turns']
                    topic = data['metadata']['topic']
                    print(f"  ✓ {sample_file.name}: {turns}턴, 주제='{topic}'")
            except Exception as e:
                print(f"  ✗ {sample_file.name}: 오류 - {e}")
        else:
            print(f"  - {sample_file.name}: 파일 없음")

    print()
    print("📁 저장 위치: data/raw/{category}/")
    print("📝 파일 형식: conv_{category}_{index:06d}.json")
    print()
    print("💡 특징:")
    print("  - 대화 턴 수: 25-35턴")
    print("  - 상담 기법: empathy, reflection, validation, goal_setting 등 10+ 종류")
    print("  - 품질 지표: metadata.quality_indicators")
    print("  - 시드 정보: seed_info.source_file")
    print()

    # 디스크 사용량
    import subprocess
    try:
        result = subprocess.run(
            ['du', '-sh', 'data/raw/adolescent', 'data/raw/adult', 'data/raw/crisis'],
            capture_output=True,
            text=True,
            check=True
        )
        print("💾 디스크 사용량:")
        for line in result.stdout.strip().split('\n'):
            size, path = line.split('\t')
            category = path.split('/')[-1]
            print(f"  {category}: {size}")

        total_result = subprocess.run(
            ['du', '-sh', 'data/raw/'],
            capture_output=True,
            text=True,
            check=True
        )
        total_size = total_result.stdout.strip().split('\t')[0]
        print(f"  전체: {total_size}")
    except Exception:
        pass

    print()
    print("=" * 70)
    print("✨ 데이터셋 생성이 성공적으로 완료되었습니다!")
    print("=" * 70)

if __name__ == "__main__":
    main()
