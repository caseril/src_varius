#!/bin/bash


folder=./


# Abilitazione SSH
sudo apt update
sudo apt install openssh-server

# install docker-compose

sudo curl -L "https://github.com/docker/compose/releases/download/1.28.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# install Command-line completion
sudo curl -L "https://raw.githubusercontent.com/docker/compose/1.28.4/contrib/completion/bash/docker-compose" -o /etc/bash_completion.d/docker-compose
