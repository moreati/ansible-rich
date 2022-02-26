# Ansible Collection - moreati.rich

Richer output for `ansible-playbook`, using [Rich] by [Will McGugan].

[![](https://asciinema.org/a/vRIFoyfPNHDkOVGnUbEOeVTI2.svg "Demo of moreati.rich.rich callback")](https://asciinema.org/a/vRIFoyfPNHDkOVGnUbEOeVTI2)

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

Try it

```sh
ANSIBLE_STDOUT_CALLBACK=moreati.rich.rich ansible-playbook moreati.rich.demo
```

Configure the callback in ansible.cfg

```ini
[defaults]
stdout_callback=moreati.rich.rich
```

## Requirements

moreati.rich requires (on your Ansible controller)

- Ansible 2.10+
- Python 3.6+
- Rich


[Rich]: https://github.com/Textualize/rich
[Will McGugan]: https://github.com/willmcgugan
