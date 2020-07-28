from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule

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
