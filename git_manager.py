# global_tools/git_manager.py
from . import utils
from . import config as tool_config

def set_git_proxy():
    """Sets the global Git HTTP/HTTPS proxy."""
    default_proxy = tool_config.get_default_git_proxy()
    proxy_address = utils.get_user_input("请输入 Git 代理地址 (例如 http://127.0.0.1:8080 或 socks5://127.0.0.1:1080)", default=default_proxy)

    if not proxy_address:
        print("未输入代理地址，操作取消。")
        return

    print(f"正在设置全局 Git 代理为: {proxy_address} ...")
    commands = [
        ['git', 'config', '--global', 'http.proxy', proxy_address],
        ['git', 'config', '--global', 'https.proxy', proxy_address]
    ]
    success = True
    for cmd in commands:
        try:
            utils.run_command(cmd, check=True)
        except Exception as e:
            print(f"执行命令 {' '.join(cmd)} 时出错: {e}", file=sys.stderr)
            success = False
            break # Stop if one command fails

    if success:
        print("Git 全局代理设置成功。")
    else:
        print("Git 代理设置失败。请检查 Git 是否安装或代理地址是否有效。")


def unset_git_proxy():
    """Unsets the global Git HTTP/HTTPS proxy."""
    print("正在取消全局 Git 代理...")
    commands = [
        ['git', 'config', '--global', '--unset', 'http.proxy'],
        ['git', 'config', '--global', '--unset', 'https.proxy']
    ]
    success_count = 0
    for cmd in commands:
        try:
            # Don't use check=True, as the setting might not exist, which is okay.
            result = utils.run_command(cmd)
            # Check stderr for common 'did not found' errors which are acceptable here
            if result.returncode == 0 or (result.returncode != 0 and 'not found' in result.stderr.lower()):
                 success_count +=1
            else:
                 print(f"执行命令 {' '.join(cmd)} 时出错: {result.stderr}", file=sys.stderr)
        except Exception as e:
            # Handle cases where git command itself fails (e.g., git not installed)
             print(f"执行命令 {' '.join(cmd)} 时发生异常: {e}", file=sys.stderr)


    if success_count > 0: # Be lenient, maybe only one was set
         print("Git 全局代理已取消 (如果之前已设置)。")
    else:
         print("取消 Git 代理时遇到问题或代理未设置。")