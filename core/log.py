"""Módulo com funções para impressão de mensagens coloridas no terminal."""


def print_green(text: str) -> None:
    """Prints a message in green.

    Args:
        text (str): Message to be printed.
    """
    print(f'\033[32m{text}\033[0m')  # Verde


def print_yellow(text: str) -> None:
    """Prints a message in yellow.

    Args:
        text (str): Message to be printed.
    """
    print(f'\033[33m{text}\033[0m')  # Amarelo


def print_red(text: str) -> None:
    """Prints a message in red.

    Args:
        text (str): Message to be printed.
    """
    print(f'\033[31m{text}\033[0m')  # Vermelho


def print_blue(text: str) -> None:
    """Prints a message in blue.

    Args:
        text (str): Message to be printed.
    """
    print(f'\033[34m{text}\033[0m')  # Azul


# Exemplos de uso:
# print_green("[LOG] Esta é uma mensagem em verde")
# print_yellow("[WARN] Esta é uma mensagem em amarelo")
# print_red("[ERROR] Esta é uma mensagem em vermelho")
# print_blue("[INFO] Esta é uma mensagem em azul")
