# pragma: no cover
import asyncio
import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
