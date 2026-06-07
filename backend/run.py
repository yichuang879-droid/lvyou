"""一键启动旅游规划助手后端服务。

用法：在 PyCharm 中右键此文件 → 运行 'run'，或终端执行：
  cd backend && python run.py

服务地址: http://localhost:8000
接口文档: http://localhost:8000/docs
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
