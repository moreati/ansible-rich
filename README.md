# Ansible callback experiments

## Overprint

Rather than print a new line for each failure of a retried task, print on a 
single line until the task fails or succeeds.

## Rich

Use [rich] progress meters to render Ansible progress. Unlike the `overprint`
callback, this handles multiple hosts.

[rich]: https://rich.readthedocs.io
