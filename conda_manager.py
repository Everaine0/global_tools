# global_tools/conda_manager.py
import os
import re
import json
import sys
import subprocess # Need subprocess for terminal opening and install
import traceback # Need traceback
import platform # Need platform
import shutil # Need shutil to find executables on Linux/macOS
from . import utils
from . import config as tool_config

# Cached list of environments
_env_list_cache = None
def invalidate_env_cache(): global _env_list_cache; _env_list_cache = None

def list_conda_envs(use_cache=True):
    """Lists Conda environments. SILENT. Uses cache."""
    global _env_list_cache
    if use_cache and _env_list_cache is not None: return _env_list_cache
    envs = []
    try:
        result = utils.run_command(['conda', 'env', 'list', '--json'], capture_output=True, text=True, shell=False, verbose=False)
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            envs_paths = data.get('envs', [])
            envs = [os.path.basename(p) for p in envs_paths if os.path.basename(p).lower() != 'base']
        else: print("内部错误: 无法获取 Conda 环境列表 (JSON)。", file=sys.stderr)
    except json.JSONDecodeError as e: print(f"内部错误: 解析 Conda 环境列表 (JSON) 失败: {e}", file=sys.stderr)
    except FileNotFoundError: print("错误: 'conda' 命令未找到。", file=sys.stderr)
    except Exception as e: print(f"内部错误: 获取 Conda 环境列表时出错: {e}", file=sys.stderr)
    _env_list_cache = envs
    return envs

def find_env_by_name(env_name, use_cache=True):
    """Finds env by name (case-insensitive). SILENT. Uses cache."""
    if not env_name: return None
    envs = list_conda_envs(use_cache=use_cache); env_name_lower = env_name.lower()
    for existing_env in envs:
        if existing_env.lower() == env_name_lower: return existing_env
    return None

def env_exists(env_name, use_cache=True):
    """Checks if env exists (case-insensitive). SILENT. Uses cache."""
    return find_env_by_name(env_name, use_cache=use_cache) is not None

def open_env_terminal(env_name):
    """Attempts to open a new terminal with the specified Conda environment activated."""
    if not env_name: print("错误: 未提供环境名称。"); return
    print(f"尝试打开环境 '{env_name}' 的新终端..."); print("注意: 这依赖于您的终端和 Conda 初始化设置。")
    system = platform.system(); activate_cmd = f"conda activate {env_name}"
    try:
        if system == "Windows":
            full_cmd = f'start cmd /k "{activate_cmd} && title {env_name} Terminal"'
            subprocess.Popen(full_cmd, shell=True); print("已尝试在新的 cmd 窗口中激活环境。")
        elif system == "Darwin": # macOS
            script = f'tell application "Terminal" to do script "{activate_cmd}"\n' \
                     f'tell application "Terminal" to activate'
            proc = subprocess.Popen(['osascript', '-'], stdin=subprocess.PIPE, text=True)
            proc.communicate(script); print("已尝试在新的 Terminal 窗口中激活环境。")
        elif system == "Linux":
            terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'lxterminal', 'mate-terminal', 'xterm']
            terminal_cmd = next((term for term in terminals if shutil.which(term)), None) # Find first available
            if terminal_cmd:
                 shell_exec_cmd = f'{activate_cmd} ; echo \\"--- Env \'{env_name}\' Activated. Type \'exit\' to close. ---\\" ; exec $SHELL'
                 if terminal_cmd in ['gnome-terminal', 'mate-terminal']: cmd_list = [terminal_cmd, '--', 'bash', '-c', shell_exec_cmd]
                 elif terminal_cmd == 'konsole': cmd_list = [terminal_cmd, '-e', 'bash', '-c', shell_exec_cmd]
                 else: cmd_list = [terminal_cmd, '-e', f'bash -c "{shell_exec_cmd}"'] # Others/Fallback
                 subprocess.Popen(cmd_list); print(f"已尝试在 '{terminal_cmd}' 中激活环境。")
            else: print("错误: 未能自动检测到支持的 Linux 终端。"); print(f"请手动运行: {activate_cmd}")
        else: print(f"错误: 不支持的操作系统 '{system}'。"); print(f"请手动运行: {activate_cmd}")
    except FileNotFoundError: print(f"错误: 无法执行命令。确保终端或 conda 在 PATH 中。", file=sys.stderr)
    except Exception as e: print(f"打开终端时发生错误: {e}", file=sys.stderr); print(f"请手动运行: {activate_cmd}")


def create_conda_env(project_root):
    """Creates a new Conda environment."""
    default_env_name_suggestion = utils.get_default_env_name(project_root)
    env_name_input = utils.get_user_input("请输入新环境名称", default=default_env_name_suggestion)
    if not env_name_input: print("环境名称不能为空。"); return None
    existing_env_casing = find_env_by_name(env_name_input, use_cache=False)
    if existing_env_casing:
        print(f"错误：环境 '{existing_env_casing}' 已存在。", file=sys.stderr)
        use_existing = utils.get_user_choice(f"是否直接使用 '{existing_env_casing}'?", ["是", "否"], 1)
        if use_existing == "是": print(f"将使用现有环境 '{existing_env_casing}'。"); return existing_env_casing
        else: print("操作取消。"); return None
    default_py_version = tool_config.get_default_python_version()
    py_version = utils.get_user_input(f"请输入 Python 版本", default=default_py_version)
    if not py_version: print("需要 Python 版本。"); return None
    print(f"正在创建环境 '{env_name_input}' (Python {py_version})...")
    command = ['conda', 'create', '-n', env_name_input, f'python={py_version}', '-y']
    created_env_name = None
    try:
        result = utils.run_command(command, check=True, verbose=True, capture_output=False, shell=False)
        if result.returncode == 0:
            print(f"环境 '{env_name_input}' 创建命令已成功执行。")
            invalidate_env_cache(); created_env_name = find_env_by_name(env_name_input, use_cache=False) or env_name_input
            print(f"环境 '{created_env_name}' 已确认创建。")
            return created_env_name
        # else case handled by check=True raising an error
    except subprocess.CalledProcessError as e: print(f"创建环境 '{env_name_input}' 失败 (返回码: {e.returncode})。", file=sys.stderr); return None
    except Exception as e: print(f"创建环境时发生异常: {e}", file=sys.stderr); return None


def delete_conda_env(project_root):
    """Deletes a selected Conda environment."""
    envs = list_conda_envs(use_cache=False); default_selection_index = None
    if not envs: print("没有找到可删除的环境。"); return
    default_env_name_lower = utils.get_default_env_name(project_root).lower()
    for i, env in enumerate(envs):
        if env.lower() == default_env_name_lower: default_selection_index = i; break
    selected_env = utils.get_user_choice("请选择要删除的环境:", envs, default_selection_index)
    if not selected_env: print("未选择环境。"); return
    confirm = utils.get_user_choice(f"警告：确定要永久删除 '{selected_env}'?", ["否", "是"], 0)
    if confirm == "是":
        print(f"正在删除环境 '{selected_env}'...")
        command = ['conda', 'env', 'remove', '-n', selected_env, '-y']
        try:
            result = utils.run_command(command, check=True, verbose=True, capture_output=False, shell=False)
            if result.returncode == 0: print(f"环境 '{selected_env}' 删除命令已成功执行。"); invalidate_env_cache()
            # else case handled by check=True
        except subprocess.CalledProcessError as e: print(f"删除环境 '{selected_env}' 失败 (返回码: {e.returncode})。", file=sys.stderr)
        except Exception as e: print(f"删除环境时发生异常: {e}", file=sys.stderr)
    else: print("删除操作已取消。")


def clone_current_env(project_root):
    """Exports the configuration of a selected environment to a .yml file."""
    envs = list_conda_envs(use_cache=False); default_selection_index = None
    if not envs: print("没有找到可导出的环境。"); return
    default_env_name_lower = utils.get_default_env_name(project_root).lower()
    default_env_casing = find_env_by_name(default_env_name_lower, use_cache=False)
    if default_env_casing in envs: default_selection_index = envs.index(default_env_casing)
    env_to_export = utils.get_user_choice("请选择要导出配置的环境:", envs, default_selection_index)
    if not env_to_export: print("未选择环境。"); return
    actual_env = find_env_by_name(env_to_export, use_cache=False) # Get actual casing
    if not actual_env: print(f"错误：环境 '{env_to_export}' 不存在。", file=sys.stderr); return
    output_dir = os.path.join(project_root, '.env'); output_file = os.path.join(output_dir, f"{actual_env}_environment.yml")
    utils.ensure_dir_exists(output_dir)
    print(f"正在导出 '{actual_env}' 配置到 '{os.path.relpath(output_file, project_root)}'...")
    command = ['conda', 'env', 'export', '-n', actual_env, '--no-builds']
    try:
        result = utils.run_command(command, capture_output=True, text=True, check=True, verbose=False)
        if result.stdout:
             with open(output_file, 'w', encoding='utf-8') as f: f.write(result.stdout)
             print(f"环境配置已成功导出到 {os.path.relpath(output_file, project_root)}")
             print(f"创建命令: conda env create -f \"{os.path.relpath(output_file, os.getcwd())}\"")
        else: print(f"警告: Conda 命令成功，但未生成输出到 {os.path.basename(output_file)}。", file=sys.stderr)

    # --- CORRECTED EXCEPTION HANDLING ---
    except subprocess.CalledProcessError as e:
        print(f"导出环境 '{actual_env}' 配置失败 (命令返回码: {e.returncode})。", file=sys.stderr)
    except FileNotFoundError: print(f"错误: 'conda' 命令未找到。", file=sys.stderr)
    except Exception as e:
        print(f"导出配置时发生未知异常: {e}", file=sys.stderr)
        traceback.print_exc()
    # --- END CORRECTION ---


def install_packages_to_env(project_root, current_env_name_cased):
    """Installs user-specified packages into a selected Conda environment."""
    utils.clear_console()
    print("\n--- 安装库到指定 Conda 环境 ---")
    envs = list_conda_envs(use_cache=False)
    if not envs: print("错误: 未找到任何可用的 Conda 环境。"); return
    default_env_suggestion = current_env_name_cased or utils.get_default_env_name(project_root)
    default_selection_index = None
    found_default_casing = find_env_by_name(default_env_suggestion, use_cache=False)
    if found_default_casing and found_default_casing in envs: default_selection_index = envs.index(found_default_casing)
    env_to_install_in = utils.get_user_choice("请选择要安装库的目标环境:", envs, default_selection_index)
    if not env_to_install_in: print("未选择环境，操作取消。"); return
    packages_input = utils.get_user_input(f"请输入要安装的库 (空格分隔, 可带版本/通道):")
    if not packages_input: print("未输入库名称，操作取消。"); return
    packages_list = packages_input.split()
    command = ['conda', 'install', '-n', env_to_install_in] + packages_list + ['-y']
    print(f"\n将在环境 '{env_to_install_in}' 中尝试安装: {packages_input}...")
    try:
        utils.run_command(command, check=True, verbose=True, capture_output=False, shell=False)
        print(f"\n库安装命令已成功执行到环境 '{env_to_install_in}'。")
    except FileNotFoundError: print(f"错误: 'conda' 命令未找到。", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"\n安装库时出错 (命令返回非零代码: {e.returncode})。", file=sys.stderr)
        print("请检查 Conda 的输出信息以了解具体错误原因。")
    except Exception as e:
        print(f"\n安装库时发生未知错误: {e}", file=sys.stderr)
        traceback.print_exc()