"""
시니어 구인구직 AI 에이전트 - CLI 실행 진입점

사용법:
    python cli.py
    python cli.py --user-id 42   # 특정 사용자 ID로 실행
"""

import argparse
import asyncio

from agent.router import process_message


def main():
    parser = argparse.ArgumentParser(description="시니어 구인구직 AI 에이전트")
    parser.add_argument("--user-id", type=str, default="1", help="테스트용 사용자 ID")
    args = parser.parse_args()

    user_id = args.user_id

    print("=" * 55)
    print("  시니어 일자리 상담 챗봇에 오신 것을 환영합니다! 😊")
    print("  종료하려면 'quit' 또는 'exit'을 입력하세요.")
    print("=" * 55)

    while True:
        try:
            user_input = input("\n사용자: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n이용해 주셔서 감사합니다! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "종료"}:
            print("\n이용해 주셔서 감사합니다! 건강하세요! 👋")
            break

        response = asyncio.run(process_message(user_id, user_input))
        print(f"\n챗봇: {response['text']}")


if __name__ == "__main__":
    main()
