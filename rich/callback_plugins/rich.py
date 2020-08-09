from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule

import rich.console
import rich.padding


DOCUMENTATION = '''
  callback: rich
  callback_type: stdout
  requirements:
    - Set as stdout in config
    - Rich Python library
  short_description: rich Ansible screen output
  description:
    - Displays ansible screen out using Rich
'''


class CallbackModule(CallbackBase):
    CALLBACK_NAME = 'rich'
    CALLBACK_TYPE = 'stdout'
    CALLBACK_VERSION = 2.0

    def __init__(self):
        self._console = rich.console.Console(
            emoji=False,
            highlight=False,
            markup=False,  # Don't interpret [square brackets] as styling
        )
        self._play = None

    def print(self, msg, indent=0, **kwargs):
        msg = rich.padding.Padding.indent(msg, indent)
        return self._console.print(msg, **kwargs)

    def v2_playbook_on_play_start(self, play):
        #self._play = play
        name = play.get_name().strip()
        
        self.print('PLAY [{name}]'.format(name=name), style='bold')

    def v2_playbook_on_task_start(self, task, is_conditional):
        name = task.get_name().strip()
        self.print('TASK [{name}]'.format(name=name), indent=2, style='bold')

    def v2_runner_on_failed(self, result, ignore_errors=False):
        hostname = result._host.get_name()
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            host_spec = '{hostname} -> {delegated_host}'.format(hostname=hostname, delegated_host=delegated_vars['ansible_host'])
        else:
            host_spec = hostname
        self._clean_results(result._result, result._task.action)
        result = result._result
        self.print('fatal: [{host_spec}]: FAILED! => {result}'.format(host_spec=host_spec, result=result), indent=4, style='red')
