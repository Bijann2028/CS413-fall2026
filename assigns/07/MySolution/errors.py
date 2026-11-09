from dataclasses import dataclass


@dataclass
class RpcError(Exception):
    code: int
    message: str
    data: dict | None = None

    def payload(self):
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result
