"""
行程规划 Agent —— 调用 LLM 生成真实旅行计划。

职责：
  1. 把用户请求（目的地、天数、偏好…）拼成自然语言 prompt
  2. 调 DashScope（qwen-plus，OpenAI 兼容协议）
  3. 解析 LLM 返回的 JSON → TripPlan 对象

依赖：
  .env 中的 LLM_MODEL_ID / LLM_API_KEY / LLM_BASE_URL / LLM_TIMEOUT
"""
import json
import os
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas import TripGenerateRequest, TripPlan, DailyPlan

# 加载 .env（在 backend/ 目录下）
load_dotenv()

# ── LLM 客户端 ─────────────────────────────────────────────
_client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    timeout=int(os.getenv("LLM_TIMEOUT", "120")),
)

MODEL = os.getenv("LLM_MODEL_ID", "qwen-plus")

# ── System Prompt ──────────────────────────────────────────

SYSTEM_PROMPT = """\
你是一个资深旅行规划师。根据用户的需求，生成一份详细的旅行计划。

## 输出要求
你必须返回一个严格的 JSON 对象，格式如下：
{
  "summary": "行程摘要，一段话概括本次旅行",
  "itinerary": [
    {
      "day": 1,
      "title": "当日主题，例如'初见成都：宽窄巷子与锦里'",
      "morning": "上午具体安排，包含景点名称和简短描述",
      "afternoon": "下午具体安排，包含景点名称和简短描述",
      "evening": "晚上具体安排，包含美食或活动推荐",
      "tips": ["实用提示1", "实用提示2"]
    }
  ]
}

## 规则
- 每天必须有 morning / afternoon / evening 三个时段的内容
- 每天至少给出 2 条 tips
- 景点和美食推荐要具体、真实、有可操作性
- 行程要合理安排，避免来回奔波
- 如果用户指定了偏好（如"美食"、"户外"），行程要向这个方向倾斜
- 如果用户指定了预算，推荐相应档次的餐厅和活动
- 只返回 JSON，不要输出任何其他文字
"""


def _build_user_prompt(req: TripGenerateRequest) -> str:
    """把请求参数拼成自然语言 prompt。"""
    parts = [
        f"目的地：{req.destination}",
        f"出发日期：{req.start_date}",
        f"旅行天数：{req.days} 天",
        f"出行人数：{req.people} 人",
    ]

    if req.budget is not None:
        parts.append(f"预算：{req.budget} 元")

    if req.preferences:
        parts.append(f"偏好：{'、'.join(req.preferences)}")

    return "\n".join(parts)


def _parse_response(raw: str) -> TripPlan:
    """解析 LLM 返回的 JSON 字符串，返回 TripPlan。

    做了两步容错：
      1. 去除 markdown 代码块标记（```json ... ```）
      2. JSON 解码 → 用 DailyPlan(**dict) 重建对象
    """
    # 如果 LLM 用 markdown 包裹了，先剥掉
    text = raw.strip()
    if text.startswith("```"):
        # 找到第一个换行后的内容，去掉结尾的 ```
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()

    data = json.loads(text)

    itinerary = [
        DailyPlan(
            day=d["day"],
            title=d["title"],
            morning=d["morning"],
            afternoon=d["afternoon"],
            evening=d["evening"],
            tips=d.get("tips", []),
        )
        for d in data["itinerary"]
    ]

    return TripPlan(
        trip_id=str(uuid4()),
        destination="",  # 由上层 service 填充更合适
        days=len(itinerary),
        summary=data["summary"],
        itinerary=itinerary,
    )


def plan_trip(req: TripGenerateRequest) -> TripPlan:
    """调用 LLM 生成旅行计划。

    参数: req — Pydantic 校验后的请求体
    返回: TripPlan 对象

    异常: 如果 LLM 返回格式异常，会带原始内容一起抛出 ValueError
    """
    user_prompt = _build_user_prompt(req)

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,  # 需要一定创造力，但不能太离谱
        max_tokens=3000,
        response_format={"type": "json_object"},  # qwen-plus 支持 JSON 模式
    )

    raw_text = response.choices[0].message.content

    try:
        plan = _parse_response(raw_text)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(
            f"LLM 返回格式异常，无法解析为 TripPlan。"
            f"原始内容:\n{raw_text[:500]}"
        ) from e

    # 回填目的地和实际天数（LLM 不一定返回和请求一致）
    plan.destination = req.destination
    plan.days = len(plan.itinerary)

    return plan
