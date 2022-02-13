#!/usr/bin/env sh

GREEN='\033[0;32m'
NO_COLOR='\033[0m'

echo "${GREEN}Running flake8...${NO_COLOR}"
flake8 --append-config .flake8.docker pyblish_lite
echo "\n${GREEN}Running mypy...${NO_COLOR}"
mypy
echo "\n${GREEN}Running nosetests...${NO_COLOR}"
nosetests \
    --verbose \
    --with-doctest \
    --exe \
    --exclude=vendor