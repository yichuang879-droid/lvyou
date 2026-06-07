"""
Agent 层 —— LLM 调用与智能规划。

本层职责：
  接收结构化的用户输入 → 拼装 prompt → 调用 LLM → 解析结构化输出。

当前模块：
  trip_planner.py   行程规划 Agent（调用 qwen-plus / DashScope）
"""
