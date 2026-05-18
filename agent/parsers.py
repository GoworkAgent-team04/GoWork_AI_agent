"""
RobustPydanticParser

로컬/외부 LLM이 JSON 형식을 지키지 못하는 경우를 처리합니다.
파싱 실패 시 즉시 에러를 던지지 않고 아래 전략을 순서대로 시도합니다.

각 단계에서 "언래핑 없이" 먼저 시도 후, 실패하면 "언래핑 적용"으로 재시도합니다.
(언래핑: {"job_type": ["경비"]} → {"job_type": "경비"})

전략 순서:
  1. JSON 블록 추출 → 직접 파싱 → 언래핑 후 파싱
  2. json-repair 적용 → 직접 파싱 → 언래핑 후 파싱
  3. 전체 텍스트에 json-repair → 직접 파싱 → 언래핑 후 파싱
  4. LangChain 표준 파싱 (최후 수단)
"""

import json
import re

from json_repair import repair_json
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser


class RobustPydanticParser(PydanticOutputParser):
    def parse(self, text: str):
        block = self._extract_json_block(text)

        # ── 전략 1: JSON 블록 추출 ─────────────────────────────────────
        if block:
            result = self._try_parse(block)
            if result is not None:
                return result

        # ── 전략 2: JSON 블록에 json-repair 적용 ──────────────────────
        if block:
            result = self._try_parse(repair_json(block))
            if result is not None:
                return result

        # ── 전략 3: 전체 텍스트에 json-repair 적용 ────────────────────
        result = self._try_parse(repair_json(text))
        if result is not None:
            return result

        # ── 전략 4: LangChain 표준 파싱 (최후 수단) ───────────────────
        try:
            return super().parse(text)
        except Exception:
            pass

        raise OutputParserException(f"모든 파싱 전략 실패 (4/4)\n원문: {text[:300]}")

    def _try_parse(self, json_str: str):
        """
        JSON 문자열을 두 가지 방법으로 파싱 시도합니다.
        1) 그대로 파싱 (리스트 필드가 있는 경우 보존)
        2) 스마트 언래핑 후 파싱 (모델 필드 타입을 확인해 List 타입은 유지)
        성공하면 Pydantic 모델 인스턴스 반환, 실패하면 None 반환.
        """
        try:
            data = json.loads(json_str)
        except Exception:
            return None

        # 1) 언래핑 없이 직접 시도
        try:
            return self.pydantic_object.model_validate(data)
        except Exception:
            pass

        # 2) 스마트 언래핑 후 시도 (List 타입 필드는 언래핑하지 않음)
        try:
            return self.pydantic_object.model_validate(_smart_unwrap(data, self.pydantic_object))
        except Exception:
            pass

        return None

    @staticmethod
    def _extract_json_block(text: str) -> str | None:
        """텍스트에서 첫 번째 { ... } 블록을 추출합니다."""
        match = re.search(r"\{[\s\S]*\}", text)
        return match.group() if match else None


def _smart_unwrap(data: dict, model) -> dict:
    """
    Pydantic 모델의 필드 타입을 확인해 스마트하게 단일 요소 배열을 언래핑합니다.

    - List 타입으로 선언된 필드     → 배열 유지  {"missing_fields": ["region"]} 그대로
    - 스칼라 타입으로 선언된 필드   → 단일 요소 언래핑  {"job_type": ["경비"]} → "경비"
    - 모델에 없는 필드              → 단일 요소 언래핑 (안전하게 언래핑 시도)
    - 빈 배열 / 다중 요소 배열      → 항상 그대로 유지
    """
    fields = model.model_fields
    result = {}
    for k, v in data.items():
        if isinstance(v, list) and len(v) == 1:
            field_info = fields.get(k)
            if field_info is not None:
                annotation = field_info.annotation
                origin = getattr(annotation, "__origin__", None)
                # Optional[List[...]] 처리: Optional → Union[List[...], None]
                if origin is list:
                    result[k] = v  # List 타입 → 언래핑 안 함
                    continue
                # typing.get_args로 내부 타입 확인 (Optional[List[str]] 등)
                import typing

                args = typing.get_args(annotation)
                if args and any(getattr(a, "__origin__", None) is list for a in args):
                    result[k] = v  # Optional[List[...]] → 언래핑 안 함
                    continue
            result[k] = v[0]  # 스칼라 타입 → 언래핑
        else:
            result[k] = v
    return result
