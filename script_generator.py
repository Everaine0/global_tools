# global_tools/script_generator.py
import os
import stat
import platform
import json
from . import utils

def generate_python_script(project_root, env_name):
    """
    Generates the appropriate run script (.bat or .sh) for the current OS
    to activate the environment and run a Python script.
    """
    if not env_name: print("错误: 需要环境名称。", file=sys.stderr); return
    is_windows = platform.system() == "Windows"; script_extension = ".bat" if is_windows else ".sh"
    script_name_base = "run"; script_path = os.path.join(project_root, f"{script_name_base}{script_extension}")
    utils.clear_console(); print(f"\n--- 生成 Python 启动脚本 ---")
    print(f"将在 '{project_root}' 中为 ({platform.system()}) 生成 '{os.path.basename(script_path)}'...")

    common_mains = ['main.py', 'app.py', 'run.py', 'server.py']; main_script = None
    for fname in common_mains:
        if os.path.exists(os.path.join(project_root, fname)): main_script = fname; print(f"自动检测到主脚本: {main_script}"); break
    if not main_script: main_script = utils.get_user_input("请输入要运行的主 Python 脚本文件名称", default="main.py")
    if not main_script: print("未指定主脚本，操作取消。"); return

    script_content = ""
    if is_windows:
        # Bat script content (remains the same)
        script_content = f"""@echo off\n""" \
                         f"""echo Activating Conda environment: {env_name}...\n""" \
                         f"""call conda activate {env_name}\n\n""" \
                         f"""if %errorlevel% neq 0 (\n""" \
                         f"""    echo Failed to activate Conda environment '{env_name}'.\n""" \
                         f"""    pause\n""" \
                         f"""    exit /b %errorlevel%\n)\n\n""" \
                         f"""echo Running Python script: {main_script}...\n""" \
                         f"""python {main_script} %*\n\n""" \
                         f"""echo Script finished. Deactivating environment...\n""" \
                         f"""call conda deactivate\n""" \
                         f"""echo Press any key to close...\n""" \
                         f"""pause > nul\n"""
    else: # Linux/macOS
        conda_base_path = os.environ.get("CONDA_ROOT", os.environ.get("CONDA_PREFIX")); conda_sh_path = ""
        if conda_base_path:
             conda_sh_path_try = os.path.join(conda_base_path, "etc", "profile.d", "conda.sh")
             if os.path.exists(conda_sh_path_try):
                  conda_sh_path = conda_sh_path_try
             # --- Corrected block ---
             else:
                  # Fallback for different structures maybe?
                  conda_sh_path_try2 = os.path.join(conda_base_path, "condabin", "conda_hook.sh")
                  if os.path.exists(conda_sh_path_try2):
                      conda_sh_path = conda_sh_path_try2
             # --- End Corrected block ---

        source_line = f'source "{conda_sh_path}"' if conda_sh_path else \
                      'echo "Error: Could not find conda init script."\nexit 1'
        # Sh script content (remains the same)
        script_content = f"""#!/bin/bash\n""" \
                         f"""SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )"\n""" \
                         f"""cd "$SCRIPT_DIR"\n\n""" \
                         f"""echo "Activating Conda environment: {env_name}..."\n""" \
                         f"""{source_line}\n\n""" \
                         f"""conda activate {env_name}\n""" \
                         f"""if [ $? -ne 0 ]; then echo "Error: Failed to activate '{env_name}'."; exit 1; fi\n\n""" \
                         f"""echo "Running Python script: {main_script}..."\n""" \
                         f"""python {main_script} "$@"\n\n""" \
                         f"""echo "Script finished. Deactivating environment..."\n""" \
                         f"""conda deactivate\n"""

    try:
        if os.path.exists(script_path):
             overwrite = utils.get_user_choice(f"脚本 '{os.path.basename(script_path)}' 已存在。是否覆盖?", ["否", "是"], 0)
             if overwrite != "是": print("操作取消。"); return
        newline_mode = None if is_windows else '\n'
        with open(script_path, 'w', encoding='utf-8', newline=newline_mode) as f: f.write(script_content)
        print(f"启动脚本 '{os.path.basename(script_path)}' 已生成。")
        if not is_windows:
            try: st = os.stat(script_path); os.chmod(script_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH); print(f"脚本已设为可执行。")
            except Exception as chmod_err: print(f"警告: 无法设置脚本为可执行: {chmod_err}", file=sys.stderr)
    except Exception as e: print(f"生成脚本 '{os.path.basename(script_path)}' 时出错: {e}", file=sys.stderr)


def generate_node_script(project_root, env_name):
    """
    Generates the appropriate run script (.bat or .sh) for the current OS
    to activate the environment and run a CHOSEN Node.js script (dev/start).
    """
    if not env_name: print("错误: 需要环境名称。", file=sys.stderr); return
    is_windows = platform.system() == "Windows"; script_extension = ".bat" if is_windows else ".sh"
    script_name_base = "run_node"; script_path = os.path.join(project_root, f"{script_name_base}{script_extension}")
    utils.clear_console(); print(f"\n--- 生成 Node.js 启动脚本 ---")
    print(f"将在 '{project_root}' 中为 ({platform.system()}) 生成 '{os.path.basename(script_path)}'...")

    package_json_path = os.path.join(project_root, 'package.json')
    scripts = {}; possible_modes = []; chosen_script_name = None
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f: data = json.load(f)
            scripts = data.get('scripts', {})
        except Exception as e: print(f"读取 package.json 时出错: {e}", file=sys.stderr)
    if 'dev' in scripts: possible_modes.append('dev')
    if 'start' in scripts: possible_modes.append('start')

    if len(possible_modes) >= 1: # Offer choice if dev or start exists
        default_idx = 0 if 'dev' in possible_modes else (possible_modes.index('start') if 'start' in possible_modes else 0)
        choice = utils.get_user_choice("选择要在脚本中运行的模式:", possible_modes, default_idx)
        chosen_script_name = choice
    else:
        print("未在 package.json 中找到 'dev' 或 'start' 脚本。")
        chosen_script_name = utils.get_user_input("请输入要在脚本中运行的 npm script 名称 (例如 build, serve):")

    if not chosen_script_name: print("未指定运行脚本，操作取消。"); return
    run_command = f"pnpm run {chosen_script_name}"
    print(f"脚本将执行命令: {run_command}")

    script_content = ""
    if is_windows:
        # Bat script content (remains the same)
        script_content = f"""@echo off\n""" \
                         f"""echo Activating Conda environment: {env_name}...\n""" \
                         f"""call conda activate {env_name}\n\n""" \
                         f"""if %errorlevel% neq 0 (\n""" \
                         f"""    echo Failed to activate Conda environment '{env_name}'.\n""" \
                         f"""    pause\n""" \
                         f"""    exit /b %errorlevel%\n)\n\n""" \
                         f"""echo Running Node.js command: {run_command}...\n""" \
                         f"""{run_command} %*\n\n""" \
                         f"""echo Script finished. Deactivating environment...\n""" \
                         f"""call conda deactivate\n""" \
                         f"""echo Press any key to close...\n""" \
                         f"""pause > nul\n"""
    else: # Linux/macOS
        conda_base_path = os.environ.get("CONDA_ROOT", os.environ.get("CONDA_PREFIX")); conda_sh_path = ""
        if conda_base_path:
             conda_sh_path_try = os.path.join(conda_base_path, "etc", "profile.d", "conda.sh")
             if os.path.exists(conda_sh_path_try):
                 conda_sh_path = conda_sh_path_try
             # --- Corrected block ---
             else:
                 # Fallback for different structures maybe?
                 conda_sh_path_try2 = os.path.join(conda_base_path, "condabin", "conda_hook.sh")
                 if os.path.exists(conda_sh_path_try2):
                      conda_sh_path = conda_sh_path_try2
             # --- End Corrected block ---

        source_line = f'source "{conda_sh_path}"' if conda_sh_path else \
                      'echo "Error: Could not find conda init script."\nexit 1'
        # Sh script content (remains the same)
        script_content = f"""#!/bin/bash\n""" \
                         f"""SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )"\n""" \
                         f"""cd "$SCRIPT_DIR"\n\n""" \
                         f"""echo "Activating Conda environment: {env_name}..."\n""" \
                         f"""{source_line}\n\n""" \
                         f"""conda activate {env_name}\n""" \
                         f"""if [ $? -ne 0 ]; then echo "Error: Failed to activate '{env_name}'."; exit 1; fi\n\n""" \
                         f"""echo "Running Node.js command: {run_command}..."\n""" \
                         f"""{run_command} "$@"\n\n""" \
                         f"""echo "Script finished. Deactivating environment..."\n""" \
                         f"""conda deactivate\n"""

    try:
        if os.path.exists(script_path):
             overwrite = utils.get_user_choice(f"脚本 '{os.path.basename(script_path)}' 已存在。是否覆盖?", ["否", "是"], 0)
             if overwrite != "是": print("操作取消。"); return
        newline_mode = None if is_windows else '\n'
        with open(script_path, 'w', encoding='utf-8', newline=newline_mode) as f: f.write(script_content)
        print(f"启动脚本 '{os.path.basename(script_path)}' 已生成。")
        if not is_windows:
            try: st = os.stat(script_path); os.chmod(script_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH); print(f"脚本已设为可执行。")
            except Exception as chmod_err: print(f"警告: 无法设置脚本为可执行: {chmod_err}", file=sys.stderr)
    except Exception as e: print(f"生成脚本 '{os.path.basename(script_path)}' 时出错: {e}", file=sys.stderr)