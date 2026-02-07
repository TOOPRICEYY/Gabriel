#!/bin/bash

# This script is executed when the countdown reaches zero
# Add your custom commands below

git pull
git merge dev
git commit -am "Trapdoor opened"
git push origin main

