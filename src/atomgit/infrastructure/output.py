"""User-facing terminal output and interactive prompt helpers."""

from colorama import Fore, Style, init

init(autoreset=True)


def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """打印信息"""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作"""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        response = input(f"{message}{suffix}: ").strip().lower()
        if response == "":
            return default
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("请输入 y/yes 或 n/no")
