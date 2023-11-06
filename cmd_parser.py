import argparse


def configure_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('organization', type=str, help='Название организации')
    parser.add_argument('--log', action='store_true',
                        help='Включить логирование запросов в консоли')
    parser.add_argument('-n', type=int, default=100,
                        help='Количество пользователей')
    return parser
