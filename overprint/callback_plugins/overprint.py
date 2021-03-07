# encoding: utf-8
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from ansible import constants as C
from ansible import context
from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule
from ansible.utils.color import colorize, hostcolor

DOCUMENTATION = '''
    callback: overprint
    type: stdout
    extends_documentation_fragment:
      - default_callback
'''

class CallbackModule(DefaultCallbackModule):
    CALLBACK_NAME = 'overprint'
    CALLBACK_TYPE = 'stdout'
    CALLBACK_VERSION = 2.0

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_runner_retry(self, result):
        if self._run_is_verbose(result, verbosity=2):
            return super(CallbackModule, self).v2_runner_retry(result)

        task_name = result.task_name or result._task
        retries = result._result['retries']
        attempts = result._result['attempts']
        msg = "\rFAILED - RETRYING: %s (%d of %d)" % (task_name, attempts, retries - 1)
        if attempts < retries - 1:
            end=''
        else:
            end='\n'
        print(msg, end=end)
        sys.stdout.flush()

    def v2_playbook_on_stats(self, stats):
        self._display.banner("PLAY RECAP")

        faces = {
            u'ok':              u'😊',  # or 🙂, 😀
            u'changed':         u'🤖',  # or 🙃
            u'unreachable':     u'💀',  # or 😴, 🤢
            u'failed':          u'😱',  # or 🙁, 😞, 🤒, 💩, 😵‍
            u'skipped':         u'😶',  # or 🤐, , 👤
            u'rescued':         u'⛑',
            u'ignored':         u'🙈',  # or 🤷, 🤫, 😶
        }

        hands = {
            u'ok':              u'👌',
            u'changed':         u'👍',  # or 🖊, 📝, 💪,
            u'unreachable':     u'🤙',
            u'failed':          u'👎',
            u'skipped':         u'👋',
            u'rescued':         u'🤝',  # or 🤟
            u'ignored':         u'💅',  # or 🤞
        }

        letters = {
            u'ok':              u'O',
            u'changed':         u'C',
            u'unreachable':     u'U',
            u'failed':          u'F',
            u'skipped':         u'S',
            u'rescued':         u'R',
            u'ignored':         u'I',
        }

        media = {
            u'ok':              u'▶',
            u'changed':         u'⏺',
            u'unreachable':     u'⏏',  # or ♾️, \N{GREEK CAPITAL LETTER DELTA}
            u'failed':          u'⏹',
            u'skipped':         u'⏭',
            u'rescued':         u'🔁',  # or ♻, ↩
            u'ignored':         u'🔇',  # or 🔕
        }

        kaomoji = {
            u'ok':              u'{^.^}',
            u'changed':         u'(⊃｡•́‿•̀｡)⊃━✿✿✿',
            u'unreachable':     u'┬┴┬┴┤(･_├┬┴┬┴',
            u'failed':          u'(/▿＼ )',
            u'skipped':         u'(∪｡∪)｡｡｡zzZ',
            u'rescued':         u'┬──┬ノ(º_ºノ)',
            u'ignored':         u'¯\_(ツ)_/¯',
        }

        signs = {
            u'ok':              u'✅',  # or ✔, ☑️, 🎉, 
            u'changed':         u'✨',  # or ⚙️, 🔧, 🔨, 💾, ⚡
            u'unreachable':     u'⛔',  # or ☠, 🚫, 🔥, 🔌, 🔗, 🕳️, 💣
            u'failed':          u'❌',  # or ✘, ⚠, ‼, ⁉
            u'skipped':         u'🍺',
            u'rescued':         u'🆘',  # or 🩺, 🚑, 💊, ✚, ✙, ⚕️, ✍, 🩹, ♻
            u'ignored':         u'💤',
        }

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(
                u"%s : %s %s %s %s %s %s %s" % (
                    hostcolor(h, t),
                    colorize(u'ok', t['ok'], C.COLOR_OK),
                    colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                    colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                    colorize(u'failed', t['failures'], C.COLOR_ERROR),
                    colorize(u'skipped', t['skipped'], C.COLOR_SKIP),
                    colorize(u'rescued', t['rescued'], C.COLOR_OK),
                    colorize(u'ignored', t['ignored'], C.COLOR_WARN),
                ),
                screen_only=True
            )

            self._display.display(
                u"%s : %s %s %s %s %s %s %s" % (
                    hostcolor(h, t, False),
                    colorize(u'ok', t['ok'], None),
                    colorize(u'changed', t['changed'], None),
                    colorize(u'unreachable', t['unreachable'], None),
                    colorize(u'failed', t['failures'], None),
                    colorize(u'skipped', t['skipped'], None),
                    colorize(u'rescued', t['rescued'], None),
                    colorize(u'ignored', t['ignored'], None),
                ),
                log_only=True
            )

        self._display.display("", screen_only=True)

        # print custom stats if required
        if stats.custom and self.show_custom_stats:
            self._display.banner("CUSTOM STATS: ")
            # per host
            # TODO: come up with 'pretty format'
            for k in sorted(stats.custom.keys()):
                if k == '_run':
                    continue
                self._display.display('\t%s: %s' % (k, self._dump_results(stats.custom[k], indent=1).replace('\n', '')))

            # print per run custom stats
            if '_run' in stats.custom:
                self._display.display("", screen_only=True)
                self._display.display('\tRUN: %s' % self._dump_results(stats.custom['_run'], indent=1).replace('\n', ''))
            self._display.display("", screen_only=True)

        if context.CLIARGS['check'] and self.check_mode_markers:
            self._display.banner("DRY RUN")

