"""A controlled substitute for Redis/DB/Kafka resources in Phase 0."""

class FakeResource:
    def __init__(self) -> None:
        self.connected = False
        self.connect_count = 0
        self.close_count = 0

    async def connect(self) -> None:
        self.connect_count += 1
        self.connected = True

    async def close(self) -> None:
        self.close_count += 1
        self.connected = False
