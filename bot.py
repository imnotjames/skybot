#!/usr/bin/env python

import os
import sys
import traceback

from core.bot import Bot
from core.reload import bot_reload


def main():

    sys.path += ['plugins']  # so 'import hook' works without duplication
    sys.path += ['lib']
    os.chdir(os.path.dirname(__file__) or '.')  # do stuff relative to the install directory

    bot = Bot()

    print 'Loading plugins'

    # bootstrap the reloader
    bot = bot_reload(bot, init=True)

    print 'Connecting to IRC'

    try:
        bot.configure()
        if not hasattr(bot, 'config'):
            sys.exit()
    except Exception as e:
        print 'ERROR: malformed config file:'
        traceback.print_exc()
        sys.exit()

    print 'Running main loop'

    while True:
        try:
            bot = bot_reload(bot)

            bot.configure()
            bot.run()
            bot.join()
        except ValueError:
            traceback.print_exc()

if __name__ == '__main__':
    main()
