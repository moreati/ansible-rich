# Ansible Collection - moreati.rich

Richer output for `ansible-playbook`, using [Rich] by [Will McGugan].

## Installing

Install moreati.rich

```sh
ansible-galaxy collection install "moreati.rich"
```

Install Ansible and Rich

```sh
python3 -m pip install "ansible>=2.10" "rich"
```

## Usage

Configure moreati.rich in ansible.cfg

```ini
[defaults]
stdout_callback=moreati.rich
```

Create an inventory

```
[locals]
local1 canary=1
local2 canary=2
local3 canary=3
local4 canary=4
local5 canary=5
```

Try it


```
ANSIBLE_STDOUT_CALLBACK=moreati.rich.rich ansible-playbook -i inventory.ini moreati.rich.demo
```

## Requirements

moreati.rich requires (on your Ansible controller)

- Ansible 2.10+
- Python 3.6+
- Rich


[Rich]: https://github.com/Textualize/rich
[Will McGugan]: https://github.com/willmcgugan
