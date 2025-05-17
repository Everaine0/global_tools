# global_tools/fastapi_utils.py
import webbrowser
import sys
import os
import subprocess
import traceback
from . import utils # Import utils from the same package

def open_docs_in_browser():
    """
    Prompts the user for FastAPI app URL and doc type, then opens it in a browser.
    Returns True if action was attempted, False if cancelled.
    """
    utils.clear_console()
    print("\n--- 打开 FastAPI 文档 ---")
    base_url = utils.get_user_input("请输入 FastAPI 应用的基础 URL", default="http://127.0.0.1:8000")
    if not base_url:
        print("未输入基础 URL。")
        return False
    base_url = base_url.rstrip('/')
    doc_options = ["Swagger UI (/docs)", "ReDoc (/redoc)"]
    doc_choice = utils.get_user_choice("请选择文档类型:", doc_options, 0)
    if not doc_choice:
        print("未选择文档类型。")
        return False
    doc_path = "/docs" if doc_choice == doc_options[0] else "/redoc"
    full_url = base_url + doc_path
    print(f"正在尝试在浏览器中打开: {full_url}")
    try:
        success = webbrowser.open(full_url, new=2)
        if success:
            print("命令已发送到浏览器。")
        else:
            print("浏览器可能未成功打开。")
            print(f"请手动打开: {full_url}")
        return True # Action attempted
    except Exception as e:
        print(f"无法打开浏览器: {e}", file=sys.stderr)
        print(f"请手动打开: {full_url}")
        return True # Still attempted

# --- Add Function to Run Server ---
def run_fastapi_dev_server(project_root, env_name):
    """Runs the FastAPI development server using uvicorn within the specified environment."""
    if not env_name:
        print("错误: 需要指定 Conda 环境才能运行服务器。", file=sys.stderr)
        return False # Indicate failure

    utils.clear_console()
    print(f"\n--- 运行 FastAPI 开发服务器 (环境: {env_name}) ---")

    # --- Get App Entry Point ---
    # Try to guess common entry points
    default_app = None
    common_apps = ["main:app", "app.main:app", "server:app", "app:app"]
    # Basic check if a file exists that might contain the app
    if os.path.exists(os.path.join(project_root, "main.py")):
        default_app = "main:app"
    elif os.path.exists(os.path.join(project_root, "app", "main.py")):
        default_app = "app.main:app"
    elif os.path.exists(os.path.join(project_root, "server.py")):
        default_app = "server:app"
    elif os.path.exists(os.path.join(project_root, "app.py")):
        default_app = "app:app"

    app_entry = utils.get_user_input("输入 FastAPI 应用入口点 (例如 main:app)", default=default_app)
    if not app_entry:
        print("未提供应用入口点。")
        return False

    # --- Get Host, Port, Reload ---
    host = utils.get_user_input("输入主机地址", default="127.0.0.1")
    if host is None:
        return False # Handle Ctrl+C
    port = utils.get_user_input("输入端口号", default="8000")
    if port is None:
        return False # Handle Ctrl+C
    reload_choice = utils.get_user_choice("是否启用自动重载 (开发模式)?", ["是", "否"], default_index=0)
    if reload_choice is None:
        return False # Handle Ctrl+C

    use_reload = (reload_choice == "是")

    # --- Construct Command ---
    uvicorn_cmd_list = ["uvicorn", app_entry, "--host", host, "--port", port]
    if use_reload:
        uvicorn_cmd_list.append("--reload")

    conda_run_cmd = ['conda', 'run', '-n', env_name, '--no-capture-output'] + uvicorn_cmd_list

    print(f"\n准备执行命令: {' '.join(conda_run_cmd)}")
    print(f"在环境 '{env_name}' 中启动服务器...")
    print("提示: 按 Ctrl+C 停止服务器。")
    print("-" * 30)

    # --- Run Command ---
    try:
        # Run silently to show live server output directly
        # Use shell=False
        utils.run_command(conda_run_cmd, cwd=project_root, check=False, capture_output=False, verbose=False, shell=False)
        print("-" * 30)
        print("服务器已停止。") # Message after server exits normally (e.g., non-reload mode)

    except KeyboardInterrupt:
        print("\n" + "-" * 30)
        print("服务器已由用户停止 (Ctrl+C)。")
    except FileNotFoundError:
        # This could be 'conda' or 'uvicorn' not found
        print(f"\n错误: 命令未找到。请确保 Conda 环境 '{env_name}' 存在，并且 'uvicorn' 已在该环境中安装。", file=sys.stderr)
        print(f"  (尝试运行: conda run -n {env_name} pip install uvicorn)", file=sys.stderr)
    except Exception as e:
        print(f"\n运行服务器时发生未知错误: {e}", file=sys.stderr)
        traceback.print_exc()

    return True # Indicate action was attempted (even if it failed or was interrupted)