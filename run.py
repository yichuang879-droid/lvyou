"""
一键启动 旅游规划助手（后端 + 前端）。

用法：在 PyCharm 中右键此文件 → 运行 'run'

自动：
  1. 启动 FastAPI 后端   → http://localhost:8000
  2. 启动 Vue 前端       → http://localhost:5173
  3. 接口文档            → http://localhost:8000/docs
"""
import subprocess
import sys
import os
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")


def main():
    print("=" * 60)
    print("  旅游规划助手 — 启动中...")
    print("=" * 60)

    # 1. 启动后端
    print("\n[1/2] 启动后端 FastAPI (http://localhost:8000)")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", "8000",
        "--reload",
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 2. 启动前端
    print("\n[2/2] 启动前端 Vite (http://localhost:5173)")
    npm_cmd = ["cmd", "/c", "npx vite --host 0.0.0.0 --port 5173"]
    frontend_proc = subprocess.Popen(
        npm_cmd,
        cwd=FRONTEND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    print("\n" + "=" * 60)
    print("  后端: http://localhost:8000")
    print("  接口文档: http://localhost:8000/docs")
    print("  前端: http://localhost:5173")
    print("=" * 60)
    print("\n按 Ctrl+C 停止所有服务...\n")

    # 等待一会儿后自动打开浏览器
    time.sleep(3)
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    try:
        for line in backend_proc.stdout:
            if line.strip():
                print(f"[backend]  {line.strip()}")
    except KeyboardInterrupt:
        print("\n正在停止服务...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("已停止所有服务。")


if __name__ == "__main__":
    main()
