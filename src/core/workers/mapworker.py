import asyncio


async def worker():
    while True:
        # 실제 처리 로직
        print("워커가 실행 중입니다...")
        await asyncio.sleep(5)  # 5초 간격으로 실행
