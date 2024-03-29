from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import logging

from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleAssertionError
from ansible.utils.color import colorize, hostcolor
try:
    from ansible.utils.display import color_to_log_level
except ImportError:
    def color_to_log_level(color):
        return logging.ERROR if color == C.COLOR_ERROR else logging.INFO
from ansible.utils.display import Display, logger
from ansible_collections.community.general.plugins.callback.yaml import CallbackModule as YAMLCallBackModule

import rich.align
import rich.box
import rich.console
import rich.padding
import rich.progress
import rich.table
import rich.theme


DOCUMENTATION = '''
  callback: moreati.rich.rich
  callback_type: stdout
  requirements:
    - Set as stdout in config
    - Rich Python library
  short_description: rich Ansible screen output
  description:
    - Displays ansible screen out using Rich
  extends_documentation_fragment:
    - default_callback
'''


SIMPLER = rich.box.Box(
    '    \n'
    '    \n'
    ' ─  \n'
    '    \n'
    '    \n'
    ' ─  \n'
    '    \n'
    '    \n'
)


def timedelta_fmt(td: datetime.timedelta) -> str:
    hours, rem = divmod(td.seconds, 3600)
    mins, secs = divmod(rem, 60)

    if td.days: return f'{td.days:2d}d {hours:2d}h'
    if hours:   return f'{hours:2ds}h {mins:2d}m'
    if mins:    return f'{mins:2d}m {secs:2d}s'
    return f'{td.seconds:>7.2f}s'


class Console(rich.console.Console):
    _printed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def print(self, *args, **kwargs):
        super().print(*args, **kwargs)
        self._printed = True

    def banner(self, *args, **kwargs):
        if self._printed:
            self.line(1)
        self.print(*args, **kwargs)


class RichDisplay(Display):
    def __init__(self, verbosity=0):
        super().__init__(verbosity=verbosity)
        theme = rich.theme.Theme({
            'banner': 'bold',
            'banner.prefix': 'bold underline on dark_blue',
            'banner.time': 'dim',
            'banner.timedelta': 'dim',
            'banner.title': 'bold',
            'ok': self.color_to_style(C.COLOR_OK),
            'changed': self.color_to_style(C.COLOR_CHANGED),
            'unreachable': self.color_to_style(C.COLOR_UNREACHABLE),
            'failed': self.color_to_style(C.COLOR_ERROR),
            'skipped': self.color_to_style(C.COLOR_SKIP),
            'rescued': self.color_to_style(C.COLOR_OK),
            'ignored': self.color_to_style(C.COLOR_WARN),
            'table.header': 'default',
            'table.footer': 'default',
        })
        self.console = Console(
            emoji=False,
            highlight=False,
            markup=False,  # Don't interpret [markup]foo[/markup] by default
            theme=theme,
        )
        self.error_console = Console(
            emoji=False,
            highlight=False,
            markup=False,  # Don't interpret [markup]foo[/markup] by default
            theme=theme,
            stderr=True,
        )

    @staticmethod
    def color_to_style(color):
        """Convert an Ansible color spec to a rich style.
        """
        if color is None:
            return color
        return color.replace('bright', 'bold')

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=True, **kwargs):
        style = self.color_to_style(color)
        console = self.error_console if stderr else self.console
        end = '\n' if newline and not msg.endswith('\n') else ''

        if not log_only:
            if style:
                msg_escaped = msg.replace('[', r'\[')
                msg_markup = f"[{style}]{msg_escaped}[/{style}]"
                console.print(msg_markup, markup=True, end=end, crop=False, soft_wrap=True, **kwargs)
            else:
                console.print(msg, end=end, crop=False, soft_wrap=True, **kwargs)

        if logger and not screen_only:
            log_level = logging.INFO
            if color:
                try:
                    log_level = color_to_log_level[color]
                except KeyError:
                    # this should not happen, but JIC
                    raise AnsibleAssertionError(f'Invalid color supplied to display: {color}')
            logger.log(log_level, msg)

    def banner(self, msg, color=None):
        style = 'banner' if color is None else self.color_to_style(color)
        self.console.banner(msg, style=style)


class CallbackModule(YAMLCallBackModule):
    CALLBACK_NAME = 'moreati.rich.rich'
    CALLBACK_TYPE = 'stdout'
    CALLBACK_VERSION = 2.0

    def __init__(self):
        self._progress = None
        self._progress_tasks = {}
        super().__init__()
        self._display = RichDisplay()

    def v2_playbook_on_play_start(self, play):
        self._play = play
        self._play_start = datetime.datetime.now()
        prefix = rich.markup.escape('PLAY')
        name = rich.markup.escape(play.get_name().strip())
        time = self._play_start
        text = f'[banner.prefix]{prefix}[/] [banner.time]T={time:%H:%M:%S}[/] [banner.title][{name}][/]'
        self._display.console.banner(text, markup=True)

    def _print_task_banner(self, task):
        prefix = rich.markup.escape(self._task_type_cache.get(task._uuid, 'TASK'))
        if self._last_task_name is not None:
            name = rich.markup.escape(self._last_task_name)
        else:
            name = rich.markup.escape(task.get_name().strip())
        tdelta = rich.markup.escape(timedelta_fmt(datetime.datetime.now() - self._play_start))
        text = f'[banner.prefix]{prefix}[/] [banner.timedelta]T+{tdelta:>8}[/] [banner.title][{name}][/]'
        self._display.console.banner(text, markup=True)
        self._last_task_banner = task._uuid

    def v2_playbook_on_task_start(self, task, is_conditional):
        super().v2_playbook_on_task_start(task, is_conditional)
        if task.until:
            self._progress = rich.progress.Progress(
                rich.progress.SpinnerColumn(),
                '[{task.description}]',
                '{task.completed} of {task.total}',
                console=self._display.console,
                auto_refresh=True,
                transient=True,
            )
            self._progress.start()

    def v2_runner_on_start(self, host, task):
        if task.until:
            progress_task = self._progress.add_task(host.name, total=task.retries)
            self._progress_tasks[(host.name, task._uuid)] = progress_task

    def v2_runner_retry(self, result):
        progress_task = self._progress_tasks[(result._host.name, result._task._uuid)]
        self._progress.update(progress_task, advance=1)

    def _progress_finish(self, result):
        total = result._result['attempts']
        progress_task = self._progress_tasks.pop((result._host.name, result._task._uuid))
        self._progress.update(progress_task, total=total)
        self._progress.remove_task(progress_task)
        if not self._progress_tasks:
            self._progress.stop()
            self._progress = None

    def v2_runner_on_ok(self, result):
        super().v2_runner_on_ok(result)
        if self._progress: self._progress_finish(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super().v2_runner_on_failed(result, ignore_errors)
        if self._progress: self._progress_finish(result)

    def v2_playbook_on_stats(self, stats):
        self._display.banner('RECAP')

        def cell(v, style, align='right'):
            if v:
                return rich.align.Align(str(v), align=align, style=style)
            else:
                return rich.align.Align(str(v), align=align, style='dim')

        def stat_column(header, field, style):
            total = sum(field.values())
            return rich.table.Column(
                header=rich.align.Align(header, align='center'),
                footer=cell(total, style=style)
            )

        table = rich.table.Table(
            rich.table.Column(header='Host', footer='Total'),
            stat_column('OK', stats.ok, style='ok'),
            stat_column('Changed', stats.changed, style='changed'),
            stat_column('Unreachable', stats.dark, style='unreachable'),
            stat_column('Failed', stats.failures, style='failed'),
            stat_column('Skipped', stats.skipped, style='skipped'),
            stat_column('Rescued', stats.rescued, style='rescued'),
            stat_column('Ignored', stats.ignored, style='ignored'),
            rich.table.Column(header='Total'),
            box=SIMPLER,
            padding=(0, 0, 0, 0),  # Top, Right, Bottom, Left
            pad_edge=False,
            show_edge=False,
            show_footer=True,
        )

        overall_total = 0
        for h in sorted(stats.processed.keys()):
            t = stats.summarize(h)
            host_total = sum(t.values())
            overall_total += host_total
            table.add_row(
                h,
                cell(t['ok'], style='ok'),
                cell(t['changed'], style='changed'),
                cell(t['unreachable'], style='unreachable'),
                cell(t['failures'], style='failed'),
                cell(t['skipped'], style='skipped'),
                cell(t['rescued'], style='rescued'),
                cell(t['ignored'], style='ignored'),
                cell(host_total, style='default'),
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
        table.columns[-1].footer = cell(overall_total, style='default')
        self._display.console.print(table)

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
