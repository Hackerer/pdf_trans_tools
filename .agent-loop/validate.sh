#!/bin/bash
# Validation script for pdf_trans_tools
cd /Users/max/Documents/pdf_trans_tools
export PYTHONPATH=/Users/max/Documents/pdf_trans_tools/src
python3 -m pytest tests/ -v
exit $?
