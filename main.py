# global_tools/main.py
import os
import sys
import zipfile
import re
from pathlib import Path
import traceback
import json
import time # Needed for sleep after KeyboardInterrupt

# Import necessary modules from the backend library
from . import utils
from . import conda_manager
from . import git_manager
from . import dependency_manager
from . import project_detector
from . import project_generator
from . import script_generator
from . import config as tool_config
from . import fastapi_utils # <-- IMPORT the new module

# --- Constants ---
BANNER_FILE = Path(__file__).parent / "assets" / "banner.txt"

# --- Helper Functions ---
def display_banner():
    """Displays the ASCII art banner."""
    try:
        with open(BANNER_FILE, 'r', encoding='utf-8') as f: print(f.read())
    except FileNotFoundError: print("--- 环境辅助工具 ---")
    except Exception as e: print(f"加载 Banner 时出错: {e}")

def get_active_conda_env():
    """Tries to get active conda env name. SILENT."""
    env_name_or_path = os.environ.get('CONDA_DEFAULT_ENV')
    if env_name_or_path: return conda_manager.find_env_by_name(os.path.basename(env_name_or_path))
    return None

def package_nodejs_project(project_root):
    """Packages Node.js project into zip."""
    project_name=os.path.basename(project_root); zip_filename=f"{project_name}_package.zip"; zip_filepath=os.path.join(project_root,zip_filename)
    exclude_list={'node_modules','.git','.vscode','dist','build','.DS_Store','Thumbs.db'}; exclude_patterns_end=('.log','.env','.zip','.tgz'); exclude_patterns_start=('.env.',)
    root_path=Path(project_root); zip_filepath_path=Path(zip_filepath)
    utils.clear_console(); print(f"\n--- 打包 Node.js 项目 ---"); print(f"正在打包 '{project_name}' 到 '{zip_filename}'...")
    print(f"排除: {', '.join(exclude_list)}"); print(f"排除模式: {exclude_patterns_start}, {exclude_patterns_end}")
    items_added=0
    try:
        with zipfile.ZipFile(zip_filepath_path,'w',zipfile.ZIP_DEFLATED) as zipf:
            for item_path in root_path.rglob('*'):
                relative_path = item_path.relative_to(root_path)
                if item_path.resolve() == zip_filepath_path.resolve(): continue
                if {part for part in relative_path.parts}.intersection(exclude_list): continue
                item_name = item_path.name
                if item_name.endswith(exclude_patterns_end) or item_name.startswith(exclude_patterns_start): continue
                if item_path.is_file(): zipf.write(item_path, arcname=relative_path); items_added += 1
        if items_added > 0: print(f"\n成功打包 ({items_added} 文件) 到: {zip_filepath}")
        else: print("\n警告: 未添加任何文件。"); zip_filepath_path.unlink(missing_ok=True)
    except Exception as e: print(f"\n打包出错: {e}", file=sys.stderr); zip_filepath_path.unlink(missing_ok=True)
    input("按回车键继续...")


# --- Menu Functions ---

def conda_menu(project_root):
    """Handles the Conda environment management submenu."""
    project_name_for_env = utils.get_default_env_name(project_root)
    current_env_name_cased = conda_manager.find_env_by_name(project_name_for_env) # Get initial status
    while True:
        utils.clear_console(); print("\n--- Conda 环境管理 ---")
        env_status = f"(当前关联: {current_env_name_cased})" if current_env_name_cased else ""
        print(env_status)
        options = [
            "创建指定环境",
            "安装库到指定环境",
            "打开环境命令行", # <-- New Option
            "删除选定环境",
            "导出环境配置 (.yml)",
            "列出所有环境",
            "返回主菜单"
            ]
        choice = utils.get_user_choice("请选择操作:", options)
        if choice is None: break
        action_taken = True; requires_pause = True # Assume pause needed unless action changes it

        if choice == options[0]: # Create
            new_env = conda_manager.create_conda_env(project_root)
            if new_env: current_env_name_cased = new_env # Update status
        elif choice == options[1]: # Install Pkgs
            conda_manager.install_packages_to_env(project_root, current_env_name_cased)
        elif choice == options[2]: # Open Terminal
            env_input = utils.get_user_input("请输入要打开命令行的环境名称", default=current_env_name_cased)
            if env_input:
                found_env = conda_manager.find_env_by_name(env_input, use_cache=False)
                if found_env:
                    conda_manager.open_env_terminal(found_env)
                    requires_pause = False # Don't pause after trying to open terminal
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr)
            else: print("未输入环境名称。")
        elif choice == options[3]: # Delete
            conda_manager.delete_conda_env(project_root)
            current_env_name_cased = conda_manager.find_env_by_name(project_name_for_env) # Re-check
        elif choice == options[4]: # Export
            conda_manager.clone_current_env(project_root)
        elif choice == options[5]: # List Environments
            utils.clear_console(); print("\n--- 当前 Conda 环境列表 ---")
            env_list = conda_manager.list_conda_envs(use_cache=False)
            # --- CORRECTED BLOCK AGAIN ---
            if env_list:
                for env in env_list:
                    print(f"  - {env}")
            else:
                print("未能获取环境列表或列表为空。")
            # --- END CORRECTED BLOCK ---
        elif choice == options[6]: # Return
            action_taken = False; requires_pause = False; break
        else: # Invalid
            print("无效选项。"); action_taken = False; requires_pause = False

        if action_taken and requires_pause: input("按回车键继续...")

def python_dependency_menu(project_root, current_env_name_cased):
    """Handles the Python dependency tools submenu."""
    while True:
        utils.clear_console(); print("\n--- Python 依赖工具 ---")
        options = ["检查/同步依赖文件 (req/toml)", "生成 requirements.txt (pipreqs)", "返回主菜单"]
        choice = utils.get_user_choice("请选择操作:", options)
        if choice is None: break
        action_taken = False; requires_pause = True
        if choice == options[0]:
             # check_and_prompt_sync handles its own pause
            dependency_manager.check_and_prompt_sync(project_root)
            requires_pause = False
        elif choice == options[1]:
            default_env_suggestion = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入要运行 pipreqs 的 Conda 环境", default=default_env_suggestion)
            if env_input:
                 env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                 if env_to_use: dependency_manager.generate_req_pipreqs(project_root, env_to_use); action_taken = True
                 else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr)
            else: print("需要环境名称。")
        elif choice == options[2]: requires_pause=False; break
        else: print("无效选项。"); requires_pause=False
        if action_taken and requires_pause: input("按回车键继续...")


def git_menu():
    """Handles the Git utility submenu."""
    while True:
        utils.clear_console(); print("\n--- Git 工具 ---")
        options = ["设置 Git 全局代理", "取消 Git 全局代理", "返回主菜单"]
        choice = utils.get_user_choice("请选择操作:", options)
        if choice is None: break
        action_taken = True; requires_pause=True
        if choice == options[0]: git_manager.set_git_proxy()
        elif choice == options[1]: git_manager.unset_git_proxy()
        elif choice == options[2]: action_taken = False; requires_pause=False; break
        else: print("无效选项。"); action_taken = False; requires_pause=False
        if action_taken and requires_pause: input("按回车键继续...")


def structure_menu(project_root):
     """Handles the project structure generation submenu."""
     utils.clear_console(); print("\n--- 生成项目目录结构 ---")
     project_generator.generate_project_structure(project_root)
     input("按回车键继续...")


# global_tools/main.py
# ... (imports and other functions) ...

def python_project_menu(project_root, current_env_name_cased):
    """Handles the Python project specific actions submenu (including FastAPI docs)."""
    original_env = current_env_name_cased # Store the initial value passed in
    while True:
        utils.clear_console(); print("\n--- Python 项目辅助 ---")
        env_status = f"(当前关联环境: {current_env_name_cased})" if current_env_name_cased else "(未找到关联环境)"
        print(env_status)
        options = [
            "创建环境并安装依赖",
            "安装依赖到指定环境",
            "创建启动脚本",
            "打开 FastAPI 文档",
            "运行 FastAPI 开发服务器",
            "返回主菜单"
            ]
        choice = utils.get_user_choice("请选择操作:", options)
        if choice is None: break
        newly_created_env = None; action_taken = True; requires_pause = True

        if choice == options[0]: # Create Env & Install
            newly_created_env = conda_manager.create_conda_env(project_root)
            if newly_created_env:
                current_env_name_cased = newly_created_env # Update local status immediately
                print(f"\n尝试在 '{newly_created_env}' 中安装依赖...")
                req_file=os.path.join(project_root,'requirements.txt'); proj_file=os.path.join(project_root,'pyproject.toml')
                cmd_base = ['conda', 'run', '-n', newly_created_env, '--no-capture-output']
                install_failed = False # Flag for installation failure

                if os.path.exists(req_file):
                    print(f"找到 requirements.txt..."); cmd = cmd_base + ['pip', 'install', '-r', 'requirements.txt']
                    try: utils.run_command(cmd, cwd=project_root, check=True, verbose=True); print("依赖安装成功(pip)。")
                    except Exception as e: print(f"Pip 安装失败: {e}", file=sys.stderr); install_failed=True
                elif os.path.exists(proj_file):
                    print(f"找到 pyproject.toml...")
                    # --- >>> INSTALL POETRY FIRST <<< ---
                    print(f"正在环境 '{newly_created_env}' 中安装 Poetry...")
                    cmd_install_poetry = ['conda', 'run', '-n', newly_created_env, '--no-capture-output', 'pip', 'install', 'poetry']
                    try:
                        utils.run_command(cmd_install_poetry, check=True, verbose=True, shell=False) # Use shell=False
                        print("Poetry 安装成功。")

                        # --- Now run poetry install ---
                        print(f"正在运行 poetry install...")
                        cmd_poetry_install = cmd_base + ['poetry', 'install']
                        try:
                            utils.run_command(cmd_poetry_install, cwd=project_root, check=True, verbose=True, shell=False) # Use shell=False
                            print("依赖安装成功(poetry)。")
                        except FileNotFoundError: print("错误: 'poetry' 命令在安装后仍未找到？", file=sys.stderr); install_failed=True
                        except subprocess.CalledProcessError as e: print(f"Poetry install 失败 (返回码: {e.returncode})。", file=sys.stderr); install_failed=True
                        except Exception as e: print(f"Poetry install 时发生未知错误: {e}", file=sys.stderr); install_failed=True
                    except subprocess.CalledProcessError as e:
                        print(f"Poetry 安装失败 (返回码: {e.returncode})。", file=sys.stderr); install_failed=True
                    except Exception as e:
                         print(f"安装 Poetry 时发生未知错误: {e}", file=sys.stderr); install_failed=True
                    # --- >>> END POETRY INSTALLATION <<< ---
                else:
                    print("未找到依赖文件 (requirements.txt / pyproject.toml)。")
                    action_taken = False # No real action performed if no files found

                if install_failed: requires_pause = True # Ensure pause if install failed
            else: action_taken = False

        elif choice == options[1]: # Install Deps to Env
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入要安装依赖的环境", default=default_env)
            if env_input:
                env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_use:
                    print(f"\n尝试在 '{env_to_use}' 中安装依赖...")
                    req_file=os.path.join(project_root,'requirements.txt'); proj_file=os.path.join(project_root,'pyproject.toml')
                    cmd_base = ['conda', 'run', '-n', env_to_use, '--no-capture-output']
                    install_failed = False
                    if os.path.exists(req_file):
                         print(f"找到 requirements.txt..."); cmd = cmd_base + ['pip', 'install', '-r', 'requirements.txt']
                         try: utils.run_command(cmd, cwd=project_root, check=True, verbose=True); print("依赖安装成功(pip)。")
                         except Exception as e: print(f"Pip 安装失败: {e}", file=sys.stderr); install_failed=True
                    elif os.path.exists(proj_file):
                        print(f"找到 pyproject.toml...")
                        # --- >>> INSTALL POETRY FIRST <<< ---
                        print(f"检查/安装 Poetry 到环境 '{env_to_use}'...")
                        cmd_install_poetry = ['conda', 'run', '-n', env_to_use, '--no-capture-output', 'pip', 'install', 'poetry']
                        try:
                            utils.run_command(cmd_install_poetry, check=True, verbose=True, shell=False)
                            print("Poetry 安装/验证成功。")
                            # --- Now run poetry install ---
                            print(f"正在运行 poetry install...")
                            cmd_poetry_install = cmd_base + ['poetry', 'install']
                            try:
                                utils.run_command(cmd_poetry_install, cwd=project_root, check=True, verbose=True, shell=False)
                                print("依赖安装成功(poetry)。")
                            except FileNotFoundError: print("错误: 'poetry' 命令在安装后仍未找到？", file=sys.stderr); install_failed=True
                            except subprocess.CalledProcessError as e: print(f"Poetry install 失败 (返回码: {e.returncode})。", file=sys.stderr); install_failed=True
                            except Exception as e: print(f"Poetry install 时发生未知错误: {e}", file=sys.stderr); install_failed=True
                        except subprocess.CalledProcessError as e: print(f"Poetry 安装失败 (返回码: {e.returncode})。", file=sys.stderr); install_failed=True
                        except Exception as e: print(f"安装 Poetry 时发生未知错误: {e}", file=sys.stderr); install_failed=True
                        # --- >>> END POETRY INSTALLATION <<< ---
                    else:
                        print("未找到依赖文件。")
                        action_taken = False # No action if no files found

                    if install_failed: requires_pause = True
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken = False
            else: print("需要环境名称。"); action_taken = False

        elif choice == options[2]: # Create Script
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入启动脚本要激活的环境", default=default_env)
            if env_input:
                env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_use: script_generator.generate_python_script(project_root, env_to_use)
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken = False
            else: print("需要环境名称。"); action_taken = False

        elif choice == options[3]: # Open FastAPI Docs
            action_taken = fastapi_utils.open_docs_in_browser() # Call the moved function
            # This function returns True/False but doesn't inherently need a pause after it

        elif choice == options[4]: # Run FastAPI Server
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入要运行服务器的 Conda 环境", default=default_env)
            if env_input:
                env_to_run = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_run:
                    # Call the function, it will handle interaction and execution
                    action_taken = fastapi_utils.run_fastapi_dev_server(project_root, env_to_run)
                    requires_pause = False # Don't pause after server runs/stops
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken = False
            else: print("需要环境名称。"); action_taken = False

        elif choice == options[5]: # Return to main menu
            action_taken = False; requires_pause = False; break
        else: # Invalid choice
            print("无效选项。"); action_taken = False; requires_pause = False

        if action_taken and requires_pause: input("按回车键继续...")

    # Return the *current* status of the associated env name when exiting the menu
    return current_env_name_cased


def nodejs_project_menu(project_root, current_env_name_cased):
    """Handles the Node.js project specific actions submenu."""
    original_env = current_env_name_cased # Store initial value
    while True:
        utils.clear_console(); print("\n--- Node.js 项目辅助 ---")
        env_status = f"(当前关联环境: {current_env_name_cased})" if current_env_name_cased else "(未找到关联环境)"
        print(env_status)
        options = ["创建环境并安装依赖", "安装依赖", "启动服务(模式可选)", "创建启动脚本", "打包项目(.zip)", "返回主菜单"]
        choice = utils.get_user_choice("请选择操作:", options)
        if choice is None: break
        newly_created_env = None; action_taken = True; requires_pause=True

        if choice == options[0]: # Create Env & Install
             default_env = utils.get_default_env_name(project_root)
             new_env_input = utils.get_user_input("请输入新环境名称", default=default_env)
             if not new_env_input: print("环境名不能为空。"); action_taken=False; continue
             existing_env = conda_manager.find_env_by_name(new_env_input, use_cache=False)
             if existing_env: print(f"错误: 环境 '{existing_env}' 已存在。", file=sys.stderr); action_taken=False; continue
             print(f"正在创建环境 '{new_env_input}' 并安装 Node.js/pnpm...")
             cmd_create = ['conda', 'create', '-n', new_env_input, 'nodejs', 'pnpm', '-c', 'conda-forge', '-y']
             try:
                 utils.run_command(cmd_create, check=True, verbose=True)
                 created_env_name = conda_manager.find_env_by_name(new_env_input, use_cache=False) or new_env_input
                 print(f"环境 '{created_env_name}' 创建成功。"); current_env_name_cased = created_env_name; newly_created_env = created_env_name
                 print(f"\n尝试在 '{created_env_name}' 中运行 pnpm install...")
                 if os.path.exists(os.path.join(project_root, 'package.json')):
                      cmd_inst = ['conda', 'run', '-n', created_env_name, '--no-capture-output', 'pnpm', 'install']
                      try: utils.run_command(cmd_inst, cwd=project_root, check=True, verbose=True); print("pnpm install 成功。")
                      except Exception as e: print(f"pnpm install 失败: {e}", file=sys.stderr)
                 else: print("未找到 package.json，跳过。")
             except Exception as e: print(f"创建 Node.js 环境失败: {e}", file=sys.stderr); action_taken=False

        elif choice == options[1]: # Install Deps
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入要运行 pnpm install 的环境", default=default_env)
            if env_input:
                env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_use:
                    print(f"\n尝试在 '{env_to_use}' 中运行 pnpm install...")
                    if os.path.exists(os.path.join(project_root, 'package.json')):
                        cmd_inst = ['conda', 'run', '-n', env_to_use, '--no-capture-output', 'pnpm', 'install']
                        try: utils.run_command(cmd_inst, cwd=project_root, check=True, verbose=True); print("pnpm install 成功。")
                        except Exception as e: print(f"pnpm install 失败: {e}", file=sys.stderr)
                    else: print("未找到 package.json。")
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken=False
            else: print("需要环境名称。"); action_taken=False

        elif choice == options[2]: # Start Service
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入要启动服务的环境", default=default_env)
            if env_input:
                env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_use:
                    pkg_path = os.path.join(project_root, 'package.json'); scripts={}; scripts_list=[]
                    if os.path.exists(pkg_path):
                        try:
                            with open(pkg_path, 'r', encoding='utf-8') as f: data=json.load(f)
                            scripts=data.get('scripts',{}); scripts_list=list(scripts.keys())
                        except Exception as e: print(f"读取 package.json 错: {e}", file=sys.stderr)
                    if not scripts_list: print("错误: package.json 中无 scripts。", file=sys.stderr); action_taken=False
                    else:
                        print("可用的 package.json 脚本:")
                        def_idx = scripts_list.index('dev') if 'dev' in scripts_list else (scripts_list.index('start') if 'start' in scripts_list else 0)
                        chosen_script = utils.get_user_choice("请选择要运行的脚本:", scripts_list, def_idx)
                        if chosen_script:
                             cmd_str = f"pnpm run {chosen_script}"; print(f"\n尝试在 '{env_to_use}' 运行 '{cmd_str}'..."); print("注意：按 Ctrl+C 停止。")
                             cmd = ['conda', 'run', '-n', env_to_use, '--no-capture-output'] + cmd_str.split()
                             try: utils.run_command(cmd, cwd=project_root, check=False, capture_output=False, verbose=False)
                             except KeyboardInterrupt: print("\n服务已由用户停止。"); requires_pause=False # No pause after stopping server
                             except FileNotFoundError: print(f"错误: 命令 '{cmd_str.split()[0]}' 未找到。", file=sys.stderr)
                             except Exception as e: print(f"运行 '{cmd_str}' 失败: {e}", file=sys.stderr)
                        else: print("未选择脚本。"); action_taken=False
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken=False
            else: print("需要环境名称。"); action_taken=False
            if action_taken: requires_pause = False # Don't pause after server interaction

        elif choice == options[3]: # Create Script
            default_env = current_env_name_cased or utils.get_default_env_name(project_root)
            env_input = utils.get_user_input(f"请输入启动脚本要激活的环境", default=default_env)
            if env_input:
                env_to_use = conda_manager.find_env_by_name(env_input, use_cache=False)
                if env_to_use: script_generator.generate_node_script(project_root, env_to_use)
                else: print(f"错误: 环境 '{env_input}' 不存在。", file=sys.stderr); action_taken=False
            else: print("需要环境名称。"); action_taken=False

        elif choice == options[4]: package_nodejs_project(project_root); action_taken=False; requires_pause=False
        elif choice == options[5]: action_taken = False; requires_pause=False; break
        else: print("无效选项。"); action_taken=False; requires_pause=False
        if action_taken and requires_pause: input("按回车键继续...")

    # Return the potentially updated environment name
    return current_env_name_cased


# --- Main Program Flow ---

def run_main_menu():
    """Runs the main menu loop of the auxiliary tool."""
    utils.clear_console(); display_banner(); conda_manager.invalidate_env_cache()
    try:
        project_root = utils.get_project_root(); print(f"当前项目目录: {project_root}")
    except Exception as e: print(f"错误: 无法确定项目根目录: {e}", file=sys.stderr); sys.exit(1)
    project_type = project_detector.detect_project_type(project_root) # Silent detection
    detected_type_display = project_type if project_type != 'unknown' else '未知'
    print(f"检测到的项目类型: {detected_type_display}") # User-facing print
    project_name_for_env = utils.get_default_env_name(project_root)
    current_env_name_cased = conda_manager.find_env_by_name(project_name_for_env)

    while True:
        utils.clear_console(); print("\n============== 主菜单 ==============")
        env_status = f"(关联环境: {current_env_name_cased})" if current_env_name_cased else "(未找到关联环境)"
        print(f"项目: {os.path.basename(project_root)} ({detected_type_display}) {env_status}")
        options = ["Conda 环境管理"]
        if project_type == 'python': options.extend(["Python 项目辅助", "Python 依赖工具"])
        elif project_type == 'node': options.append("Node.js 项目辅助")
        options.extend(["Git 工具", "生成常见目录结构", "配置工具默认设置", "退出"])

        choice = utils.get_user_choice("请选择功能:", options)
        if choice is None: choice = "退出"

        try:
            action_may_change_envs = choice in ["Conda 环境管理", "Python 项目辅助", "Node.js 项目辅助"]
            if action_may_change_envs: conda_manager.invalidate_env_cache()

            # --- Menu Action Handling ---
            if choice == "Conda 环境管理":
                conda_menu(project_root)
                # Refresh status after returning from the menu
                current_env_name_cased = conda_manager.find_env_by_name(project_name_for_env)

            elif choice == "Python 项目辅助":
                if project_type == 'python':
                    # Capture the returned env name to update status display
                    current_env_name_cased = python_project_menu(project_root, current_env_name_cased)
                else: utils.clear_console(); print("此选项仅适用于 Python 项目。"); input("按回车键继续...")

            elif choice == "Python 依赖工具":
                if project_type == 'python': python_dependency_menu(project_root, current_env_name_cased)
                else: utils.clear_console(); print("此选项仅适用于 Python 项目。"); input("按回车键继续...")

            elif choice == "Node.js 项目辅助":
                if project_type == 'node':
                    # Capture the returned env name to update status display
                    current_env_name_cased = nodejs_project_menu(project_root, current_env_name_cased)
                else: utils.clear_console(); print("此选项仅适用于 Node.js 项目。"); input("按回车键继续...")

            elif choice == "Git 工具": git_menu()
            elif choice == "生成常见目录结构": structure_menu(project_root)
            elif choice == "配置工具默认设置": utils.clear_console(); tool_config.configure_defaults(); input("按回车键继续...")
            elif choice == "退出": utils.clear_console(); print("感谢使用，再见！"); break
            else: print("无效选项，请重试。")

        except KeyboardInterrupt:
             print("\n操作被用户中断 (Ctrl+C)。返回主菜单。"); conda_manager.invalidate_env_cache()
             try: time.sleep(1) # Brief pause allows user to see message
             except NameError: pass # time might not be imported if error happened early
        except Exception as e:
             print(f"\n处理菜单选项时发生错误: {e}", file=sys.stderr); traceback.print_exc()
             input("发生错误，按回车键返回主菜单...")
             conda_manager.invalidate_env_cache()

if __name__ == '__main__':
    import time # Needed here for KeyboardInterrupt pause
    print("警告: 通过 `python -m global_tools.main` 运行主要用于测试。")
    print("建议为您的项目生成 tool.py 并通过 `python tool.py` 启动。")
    run_main_menu()