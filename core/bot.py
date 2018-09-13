import re
import os
from Queue import Empty as QueueEmpty
from time import sleep
import collections

from core.config import config
from core.main import main, Handler


class Bot(object):
    def __init__(self):
        self.conns = {}
        self.commands = {}

        self.events = collections.defaultdict(list)
        self.plugs = collections.defaultdict(list)

        self.threads = {}

        self.persist_dir = os.path.abspath('persist')
        if not os.path.exists(self.persist_dir):
            os.mkdir(self.persist_dir)

    def configure(self):
        config(self)

    def refresh(self):
        self.commands.clear()
        self.events.clear()

        for plug in self.plugs['command']:
            name = plug[1]['name'].lower()
            if not re.match(r'^\w+$', name):
                print('### ERROR: invalid command name "%s" (%s)' % (name, format_plug(plug)))
                continue
            if name in self.commands:
                print(
                    "### ERROR: command '%s' already registered (%s, %s)" %
                    (name, format_plug(self.commands[name]), format_plug(plug))
                )
                continue
            self.commands[name] = plug

        for func, args in self.plugs['event']:
            for event in args['events']:
                self.events[event].append((func, args))

    def run(self):
        for conn in self.conns.values():
            try:
                out = conn.out.get_nowait()
                main(self, conn, out)
            except QueueEmpty:
                pass

    def join(self):
        while all(conn.out.empty() for conn in self.conns.values()):
            sleep(.1)

    def unregister_plugin(self, plugin):
        for plugin_type, plugins in self.plugs.items():
            if plugin not in self.plugs:
                continue

            self.plugs[plugin_type] = [
                x for x in plugins
                if x != plugin
            ]

        if plugin in self.threads:
            self.threads[plugin].stop()
            del self.threads[plugin]

    def register_plugin(self, plugin):
        if not hasattr(plugin, '_hook'):
            raise ValueError('not a plugin: %s' % plugin)

        if plugin._thread:
            self.threads[plugin] = Handler(self, plugin)

        for plugin_type, data in plugin._hook:
            self.plugs[plugin_type] += [data]

    def register_plugin_module(self, plugin_module):
        old_plugins = []
        new_plugins = []

        # Find plugins already loaded for this filename
        for data in self.plugs.values():
            old_plugins += [x for x in data if x[0].__module__ == plugin_module.__name__]

        # remove plugins already loaded from this filename
        for plugin in old_plugins:
            self.unregister_plugin(plugin)

        for obj in plugin_module.__dict__.values():
            if hasattr(obj, '_hook'):  # check for magic
                # Just in case, attempt to unregister this plugin first.
                self.unregister_plugin(obj)
                self.register_plugin(obj)

                new_plugins.append(obj)

        return new_plugins