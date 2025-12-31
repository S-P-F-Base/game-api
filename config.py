class Config:
    _data = {}

    @classmethod
    def steam_api(cls) -> str:
        return cls._data.get("steam_api", "")
