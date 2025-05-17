# global_tools/config.py
from . import utils

# Default values - can be overridden by user config file
DEFAULT_PYTHON_VERSION = "3.10"
DEFAULT_GIT_PROXY = "socks5://127.0.0.1:10090" # Example default proxy

def get_default_python_version():
    """Gets the default Python version, checking user config first."""
    return utils.get_config_value("Defaults", "PythonVersion", DEFAULT_PYTHON_VERSION)

def set_default_python_version(version):
    """Sets the default Python version in the user config."""
    utils.set_config_value("Defaults", "PythonVersion", version)
    print(f"默认 Python 版本已更新为: {version}")

def get_default_git_proxy():
    """Gets the default Git proxy, checking user config first."""
    return utils.get_config_value("Defaults", "GitProxy", DEFAULT_GIT_PROXY)

def set_default_git_proxy(proxy_url):
    """Sets the default Git proxy in the user config."""
    utils.set_config_value("Defaults", "GitProxy", proxy_url)
    print(f"默认 Git 代理已更新为: {proxy_url}")

def configure_defaults():
    """Interactive menu to allow users to set default values."""
    print("\n--- 配置默认设置 ---")
    current_py = get_default_python_version()
    new_py = utils.get_user_input(f"输入新的默认 Python 版本 (当前: {current_py})", default=current_py)
    if new_py != current_py:
        set_default_python_version(new_py)

    current_proxy = get_default_git_proxy()
    new_proxy = utils.get_user_input(f"输入新的默认 Git 代理地址 (当前: {current_proxy})", default=current_proxy)
    if new_proxy != current_proxy:
        set_default_git_proxy(new_proxy)

    print("默认设置已更新。")