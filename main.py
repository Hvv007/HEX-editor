import argparse
import sys
from src.Application import Application
from src.PyHex import PyHex

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HEX-editor', add_help=False,
                                     usage='main.py [OPTIONS] FILE_NAME')
    parser.add_argument("-h", "--help", help="показывает это сообщение", action="help")
    parser.add_argument("-c", "--create", help="флаг для создания нового файла", action="store_true")
    parser.add_argument("-r", "--read_only", help="флаг только для чтения", action="store_true")
    parser.add_argument("-b", "--base", help="основание системы счисления(2, 8, 10, default=16)", type=int, default=16)
    parser.add_argument("-n", "--number",
                        help="колличество колонок, изначально равно основанию системы счисления", type=int, default=0)
    parser.add_argument("FILE_NAME", help="название файла")
    args = parser.parse_args()
    create = args.create
    read_only = args.read_only
    filename = args.FILE_NAME
    base = args.base
    if base not in {2, 8, 10, 16}:
        print("неподдерживаемая система счисления")
        sys.exit()
    columns = args.number
    columns = base if columns == 0 else columns
    app: Application = Application()
    app.set_main_window(PyHex(create, read_only, filename, base, columns, app.stdscr, app))
    app.run()
