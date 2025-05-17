# global_tools/utils.py
import subprocess
import sys
import os
import platform # Import platform
import configparser
import re
from pathlib import Path
from pypinyin import pinyin, Style

# --- Console Clearing ---
def clear_console():
    """Clears the terminal screen."""
    # Simple check for interactive mode (might not be foolproof in all scenarios)
    if sys.stdout.isatty():
        os.system('cls' if platform.system() == "Windows" else 'clear')
    # If not interactive (e.g., output redirected), don't attempt to clear

# --- Configuration ---
CONFIG_FILE_NAME = ".env_assist_tool_config.ini"

def get_config_path():
    """Gets the path to the configuration file in the user's home directory."""
    return Path.home() / CONFIG_FILE_NAME

def load_config():
    """Loads the configuration from the INI file."""
    config_path = get_config_path()
    config = configparser.ConfigParser()
    if config_path.exists():
        config.read(config_path, encoding='utf-8')
    return config

def save_config(config):
    """Saves the configuration object to the INI file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except Exception as e:
        print(f"错误: 无法写入配置文件 '{config_path}': {e}", file=sys.stderr)

def get_config_value(section, key, default=None):
    """Gets a specific value from the config, returning default if not found."""
    config = load_config()
    return config.get(section, key, fallback=default)

def set_config_value(section, key, value):
    """Sets a specific value in the config and saves it."""
    config = load_config()
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))
    save_config(config)

# --- System & Execution ---

def is_windows():
    """Checks if the current operating system is Windows."""
    return platform.system() == "Windows"

def run_command(command, cwd=None, capture_output=True, text=True, encoding='utf-8', env=None, check=False, shell=True, verbose=True):
    """
    Runs a shell command. Suppresses command echo and stdout if verbose=False.
    Always prints stderr if it exists.
    """
    cmd_str = ' '.join(command) if isinstance(command, list) else command
    if verbose:
        print(f"执行命令 ({'shell' if shell else 'no shell'}): {cmd_str}")
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=capture_output, text=text, encoding=encoding,
            errors='replace', env=env or os.environ, check=check, shell=shell
        )
        if verbose and capture_output and result.stdout:
            print("命令输出:\n", result.stdout)
        if result.stderr:
            print("错误输出:\n", result.stderr, file=sys.stderr)
        if not check and result.returncode != 0:
             print(f"命令执行警告: 返回码 {result.returncode}", file=sys.stderr)
        return result
    except FileNotFoundError:
        print(f"错误：命令 '{command if isinstance(command, str) else command[0]}' 未找到。", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}", file=sys.stderr)
        if e.stdout: print("STDOUT:", e.stdout)
        if e.stderr: print("STDERR:", e.stderr)
        raise
    except Exception as e:
        print(f"执行命令时发生未知错误: {e}", file=sys.stderr)
        raise

def get_project_root(start_path=None):
    """Determines the project root directory (where tool.py usually resides)."""
    if start_path is None:
         try:
             start_path = os.path.dirname(os.path.abspath(sys.argv[0]))
         except Exception:
             start_path = os.getcwd()
    return start_path

# --- User Input & Interaction ---

def get_user_input(prompt, default=None):
    """Gets input from the user, providing a default value."""
    if default: prompt_text = f"{prompt} (默认: {default}): "
    else: prompt_text = f"{prompt}: "
    try:
        user_input = input(prompt_text).strip()
        return user_input if user_input else default
    except EOFError: print("\n输入流结束，将使用默认值。", file=sys.stderr); return default
    except KeyboardInterrupt: print("\n操作取消。"); return None # Return None on Ctrl+C

def get_user_choice(prompt, options, default_index=None):
    """Presents options to the user and gets their choice."""
    print(prompt)
    if not options: print("错误: 没有提供选项。", file=sys.stderr); return None
    for i, option in enumerate(options):
        default_marker = "(默认)" if i == default_index else ""
        print(f"  {i + 1}. {option} {default_marker}")
    while True:
        try:
            choice_str = input(f"请输入选项编号 (1-{len(options)}): ")
            if not choice_str and default_index is not None:
                if 0 <= default_index < len(options): return options[default_index]
                else: print("内部错误: 默认索引无效。", file=sys.stderr); return None
            try:
                choice_index = int(choice_str) - 1
                if 0 <= choice_index < len(options): return options[choice_index]
                else: print(f"无效编号。请输入 1 到 {len(options)} 之间的数字。")
            except ValueError: print("请输入有效的数字编号。")
        except EOFError: print("\n输入流结束，操作取消。", file=sys.stderr); return None
        except KeyboardInterrupt: print("\n操作取消。"); return None

# --- String & Naming ---

def to_pinyin(text):
    """Converts Chinese text to Pinyin (lowercase, no spaces)."""
    try:
        pinyin_list = pinyin(text, style=Style.NORMAL)
        return "".join(syllable.replace(" ", "") for item in pinyin_list for syllable in item).lower()
    except Exception as e: print(f"转换为拼音时出错: {e}. 返回原始文本。", file=sys.stderr); return text

def get_default_env_name(project_dir):
    """Generates default Conda env name (lowercase, sanitized)."""
    if not project_dir: return "my_env"
    dir_name = os.path.basename(project_dir); processed_name = dir_name
    if any('\u4e00' <= char <= '\u9fff' for char in dir_name): processed_name = to_pinyin(dir_name)
    sanitized_name = re.sub(r'[^\w_]+', '_', processed_name)
    final_name = sanitized_name.strip('_').lower()
    if not final_name or final_name.replace('_', '') == '': return "my_env"
    return final_name

# --- File System ---

def ensure_dir_exists(dir_path):
    """Ensures a directory exists, creating it if necessary."""
    path = Path(dir_path)
    try: path.mkdir(parents=True, exist_ok=True)
    except Exception as e: print(f"错误: 无法创建目录 '{dir_path}': {e}", file=sys.stderr); raise