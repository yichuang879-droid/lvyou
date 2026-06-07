'''
使用pydatic定义三个数据类型，做数据的校验和类型的约束
'''

from pydantic import BaseModel, Field   # BaseModel 是基类，Field 用来加校验规则
from typing import List, Optional        # List 列表类型，Optional 可选类型，List / Optional 是给类型注解用的标签，不是新数据类型。

from datetime import date                # 日期类型

class TripGenerateRequest(BaseModel):
    '''
     请求体格式，前端发送Get或者Post请求
     定义requet的格式
     使用pydantic的数据定义格式
    '''
    destination: str = Field(..., examples=["成都"])#请求的：目的地
    start_date: date#请求的：开始时间
    days: int = Field(..., ge=1, le=30)#请求的：天数
    people: int = Field(..., ge=1)  #请求的：人数
    budget: Optional[int] = None#请求的：预算
    preferences: List[str] = []#请求的：偏好，使用list字符列表储存


class DailyPlan(BaseModel):
    '''
    每一天的行程结构。 所有字段都是普通类型，没加 Field 校验，表示全是必填的字符串和整数，tips 默认空列表。
    '''
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str
    tips: List[str] = []


class TripPlan(BaseModel):
    '''
   接口返回给用户的完整旅行计划。

    '''
    trip_id: str#旅行计划id
    destination: str#目的地
    days: int#天数
    summary: str#总结
    itinerary: List[DailyPlan]# 每一天的行程