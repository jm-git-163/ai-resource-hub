#!/usr/bin/env python3
"""
신선도 관리 스크립트 (Freshness Manager)
- 각 리소스의 신선도 점수를 계산
- 점수가 너무 낮은 리소스 자동 폐기
- first_seen 필드 관리
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'resources.json')

# 신선도 점수 임계값
THRESHOLD_REMOVE = 20    # 이 점수 미만: 자동 제거
THRESHOLD_STALE = 30     # 이 점수 미만: "오래된 자료" 태그
THRESHOLD_FRESH = 70     # 이 점수 이상: "신선한 자료" 뱃지
NEW_DAYS = 30            # 첫 수집 후 이 기간 내: "NEW" 뱃지
MAX_AGE_DAYS = 90        # 90일(3개월) 초과 비큐레이션 리소스 폐기

def calculate_freshness(resource):
    """리소스의 신선도 점수를 계산합니다 (0~100)"""
    now = datetime.now(timezone.utc)

    # updated_at 파싱
    updated_str = resource.get('updated_at', '')
    try:
        if 'T' in updated_str:
            updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
        else:
            updated = datetime.strptime(updated_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        updated = now - timedelta(days=365)  # 파싱 실패 시 1년 전으로 간주

    # first_seen 파싱
    first_seen_str = resource.get('first_seen', updated_str)
    try:
        if 'T' in first_seen_str:
            first_seen = datetime.fromisoformat(first_seen_str.replace('Z', '+00:00'))
        else:
            first_seen = datetime.strptime(first_seen_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        first_seen = updated

    days_since_update = max(0, (now - updated).days)
    days_since_first_seen = max(0, (now - first_seen).days)
    stars = resource.get('stars', 0) or 0

    # 1. 활동 점수 (40%)
    if days_since_update <= 7:
        activity = 100
    elif days_since_update <= 30:
        activity = 80
    elif days_since_update <= 90:
        activity = 60
    elif days_since_update <= 180:
        activity = 30
    else:
        activity = 10

    # 2. 나이 점수 (30%) - 최근 수집된 것에 보너스
    if days_since_first_seen <= 30:
        age = 100
    elif days_since_first_seen <= 90:
        age = 70
    elif days_since_first_seen <= 180:
        age = 40
    else:
        age = 20

    # 3. 인기도 점수 (30%)
    if stars > 10000:
        popularity = 100
    elif stars > 1000:
        popularity = 80
    elif stars > 100:
        popularity = 60
    elif stars > 10:
        popularity = 40
    else:
        popularity = 20

    score = round(activity * 0.4 + age * 0.3 + popularity * 0.3)

    # 큐레이션 리소스는 폐기 방지 (최소 점수 보장)
    if resource.get('platform') == 'curated':
        score = max(score, 50)

    return score


def manage_freshness(data):
    """신선도 관리: 점수 계산, 태그 부여, 자동 폐기"""
    resources = data.get('resources', [])
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    now = datetime.now(timezone.utc)

    print("🧹 신선도 관리 시작...")
    print(f"   총 리소스: {len(resources)}개")

    # 90일 경과 리소스 사전 필터링 (큐레이션 리소스는 제외)
    aged_out = 0
    filtered_resources = []
    for r in resources:
        if r.get('platform') == 'curated':
            filtered_resources.append(r)
            continue

        updated_str = r.get('updated_at', '')
        try:
            if 'T' in updated_str:
                updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
            else:
                updated = datetime.strptime(updated_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            updated = now - timedelta(days=365)

        if (now - updated).days > MAX_AGE_DAYS:
            aged_out += 1
            continue

        filtered_resources.append(r)

    removed = []
    stale_count = 0
    fresh_count = 0
    new_count = 0

    updated_resources = []

    for r in filtered_resources:
        # first_seen 필드가 없으면 현재 날짜로 설정
        if 'first_seen' not in r:
            r['first_seen'] = r.get('updated_at', now_str)

        score = calculate_freshness(r)
        r['freshness_score'] = score

        # 자동 폐기
        if score < THRESHOLD_REMOVE:
            removed.append(r)
            continue

        # 상태 분류
        first_seen_str = r.get('first_seen', '')
        try:
            if 'T' in first_seen_str:
                first_seen = datetime.fromisoformat(first_seen_str.replace('Z', '+00:00'))
            else:
                first_seen = datetime.strptime(first_seen_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            days_since_first = (datetime.now(timezone.utc) - first_seen).days
        except (ValueError, TypeError):
            days_since_first = 999

        if days_since_first <= NEW_DAYS:
            new_count += 1
        elif score >= THRESHOLD_FRESH:
            fresh_count += 1
        elif score < THRESHOLD_STALE:
            stale_count += 1

        updated_resources.append(r)

    data['resources'] = updated_resources

    # 결과 출력
    print(f"\n📊 신선도 관리 결과:")
    print(f"   🔥 NEW (30일 이내):  {new_count}개")
    print(f"   🌿 신선 (70점 이상):  {fresh_count}개")
    print(f"   ⚠️ 오래됨 (30점 미만): {stale_count}개")
    print(f"   ⏰ 기간 만료 ({MAX_AGE_DAYS}일 초과): {aged_out}개")
    print(f"   ❌ 자동 폐기 ({THRESHOLD_REMOVE}점 미만): {len(removed)}개")
    print(f"   ─────────────────────")
    print(f"   📦 최종 유지: {len(updated_resources)}개")

    if removed:
        print(f"\n   폐기된 리소스:")
        for r in removed[:10]:
            print(f"     - [{r.get('category')}] {r.get('title')} (점수: {r.get('freshness_score')})")
        if len(removed) > 10:
            print(f"     ... 외 {len(removed) - 10}개")

    return data


def main():
    print("=" * 50)
    print("🔄 AI 리소스 신선도 관리 시스템")
    print("=" * 50)

    if not os.path.exists(DATA_FILE):
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {DATA_FILE}")
        print("   먼저 collector.py를 실행해주세요.")
        sys.exit(1)

    # 데이터 로드
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 신선도 관리
    data = manage_freshness(data)

    # 저장
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {DATA_FILE}")


if __name__ == '__main__':
    main()
