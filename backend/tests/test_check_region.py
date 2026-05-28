"""
_check_region_sufficient 유닛 테스트

수정된 로직:
- collected_info.region 우선
- 없으면 db_profile.region_district → region_city → address 순으로 fallback
- job_type은 필수 아님
"""

from agent.nodes.job_recommend import _check_region_sufficient

# ─── 충분한 케이스 ────────────────────────────────────────────────


def test_region_from_collected_info():
    """대화에서 수집된 region → sufficient"""
    collected = {"region": "대전"}
    db_profile = {}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert missing == []


def test_region_from_db_region_district():
    """collected_info 없고 db_profile.region_district → sufficient"""
    collected = {}
    db_profile = {"region_district": "성북구"}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert missing == []


def test_region_from_db_region_city():
    """collected_info 없고 db_profile.region_city → sufficient"""
    collected = {}
    db_profile = {"region_city": "서울"}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert missing == []


def test_region_from_db_address():
    """collected_info 없고 db_profile.address → sufficient"""
    collected = {}
    db_profile = {"address": "서울 노원구 상계동"}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert missing == []


def test_collected_region_overrides_db():
    """collected_info.region이 db_profile.address보다 우선"""
    collected = {"region": "대전"}
    db_profile = {"address": "서울 노원구"}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert missing == []


def test_region_sufficient_without_job_type():
    """job_type 없어도 region만 있으면 sufficient (job_type은 필수 아님)"""
    collected = {"region": "서울"}
    db_profile = {}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is True
    assert "job_type" not in missing


# ─── 부족한 케이스 ────────────────────────────────────────────────


def test_region_missing_no_profile():
    """collected_info도 없고 db_profile도 없음 → region missing"""
    sufficient, missing = _check_region_sufficient({}, {})
    assert sufficient is False
    assert "region" in missing


def test_region_missing_with_none_values():
    """db_profile에 address가 None → missing"""
    collected = {}
    db_profile = {"address": None, "region_city": None, "region_district": None}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is False
    assert "region" in missing


def test_vague_region_collected_no_db_fallback():
    """막연한 표현("집 근처")은 region으로 인정 안 함 → db fallback 시도"""
    collected = {"region": "집 근처"}
    db_profile = {"region_city": "부산"}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    # db_profile.region_city로 fallback → sufficient
    assert sufficient is True


def test_vague_region_no_fallback():
    """막연한 표현이고 db_profile도 없음 → missing"""
    collected = {"region": "근처"}
    db_profile = {}
    sufficient, missing = _check_region_sufficient(collected, db_profile)
    assert sufficient is False
    assert "region" in missing
