"""调用deepseek来生成会议总结这是抽象基类"""
from abc import ABC, abstractmethod


class deepseeksummary(ABC):
    @abstractmethod
    async def summary(self,context:str,)->str:
        """"调用ds对会议内容进行总结"""