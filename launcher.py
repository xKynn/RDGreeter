from bot import Greeter
import sys


def main():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = 'data/config.json'

    bot = Greeter()
    bot.run()


if __name__ == '__main__':
    main()
