import collections
import glob
import os
import sys
import traceback


if 'mtimes' not in globals():
    mtimes = {}

if 'lastfiles' not in globals():
    lastfiles = set()


def make_signature(f):
    return os.path.basename(f.func_code.co_filename), f.func_name, f.func_code.co_firstlineno


def format_plug(plug, kind='', lpad=0, width=40):
    out = ' ' * lpad + '%s:%s:%s' % make_signature(plug[0])
    if kind == 'command':
        out += ' ' * (50 - len(out)) + plug[1]['name']

    if kind == 'event':
        out += ' ' * (50 - len(out)) + ', '.join(plug[1]['events'])

    if kind == 'regex':
        out += ' ' * (50 - len(out)) + plug[1]['regex']

    return out


def refresh_bot_object(new_module, old_bot):
    bot = new_module.Bot()
    bot.__dict__.update(old_bot.__dict__)

    return bot

def bot_reload(bot, init=False):
    changed = False

    core_fileset = set(glob.glob(os.path.join("core", "*.py")))

    for filename in core_fileset:
        mtime = os.stat(filename).st_mtime
        if mtime != mtimes.get(filename):
            mtimes[filename] = mtime

            changed = True

            core_module_name = os.path.splitext(os.path.basename(filename))[0]

            try:
                core_module = __import__('core.%s' % core_module_name, fromlist=[core_module_name])
                reload(core_module)

                if core_module_name == 'bot':
                    # Refresh the bot class
                    bot = refresh_bot_object(core_module, bot)

                if core_module_name == 'reload':
                    # Refresh the bot reload function
                    bot_reload.__code__ = core_module.bot_reload.__code__

            except Exception:
                traceback.print_exc()
                if init:        # stop if there's an error (syntax?) in a core
                    sys.exit()  # script on startup
                continue

            if core_module_name == 'reload':
                return bot_reload(bot, init=init)

    fileset = set(glob.glob(os.path.join('plugins', '*.py')))
    fileset = [os.path.realpath(p) for p in fileset]

    # remove deleted/moved plugins
    for name, data in bot.plugs.items():
        bot.plugs[name] = [x for x in data if x[0]._filename in fileset]

    for func, handler in list(bot.threads.items()):
        if func._filename not in fileset:
            handler.stop()
            del bot.threads[func]

    # compile new plugins
    for filename in fileset:
        mtime = os.stat(filename).st_mtime
        if mtime != mtimes.get(filename):
            mtimes[filename] = mtime

            changed = True

            plugin_module_name = os.path.splitext(os.path.basename(filename))[0]

            try:
                plugin_module = __import__('plugins.%s' % plugin_module_name, fromlist=[plugin_module_name])
                reload(plugin_module)

                bot.register_plugin_module(plugin_module)
            except Exception:
                traceback.print_exc()
                continue

    # Clean up mtimes list.
    for filename in list(mtimes):
        if filename not in fileset and filename not in core_fileset:
            mtimes.pop(filename)


    if changed:
        bot.refresh()

    if init:
        print '  plugin listing:'

        if bot.commands:
            # hack to make commands with multiple aliases
            # print nicely

            print '    command:'
            commands = collections.defaultdict(list)

            for name, (func, args) in bot.commands.items():
                commands[make_signature(func)].append(name)

            for sig, names in sorted(commands.items()):
                names.sort(key=lambda x: (-len(x), x))  # long names first
                out = ' ' * 6 + '%s:%s:%s' % sig
                out += ' ' * (50 - len(out)) + ', '.join(names)
                print out

        for kind, plugs in sorted(bot.plugs.items()):
            if kind == 'command':
                continue
            print '    %s:' % kind
            for plug in plugs:
                print format_plug(plug, kind=kind, lpad=6)
        print

    return bot