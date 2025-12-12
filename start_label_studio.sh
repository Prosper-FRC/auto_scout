#!/bin/bash
# Script to start label-studio from the virtual environment
cd "$(dirname "$0")"
source .venv/bin/activate
label-studio start
