VERSION := $(shell sed -n -E -e 's/version: (.+)/\1/p' galaxy.yml)
SOURCES := galaxy.yml meta/runtime.yml playbooks/demo.yml plugins/callback/rich.py
TARGET := moreati-rich-$(VERSION).tar.gz

$(TARGET): $(SOURCES)
	ansible-galaxy collection build --force

.PHONY: clean
clean:
	rm -f *.tar.gz

.PHONY: install
install: $(TARGET)
	ansible-galaxy collection install --force $(TARGET)

.PHONY: demo
demo: install
	ANSIBLE_STDOUT_CALLBACK=moreati.rich.rich ansible-playbook -i local1,local2, moreati.rich.demo

