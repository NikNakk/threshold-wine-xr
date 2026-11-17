#!/usr/bin/env python3
# Copyright 2026 Nick Kennedy
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run a public Windows Steam profile without importing private Steam integration."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from managed_profiles import launch_environment,read_stack,check_monado

def command(stack,action,arguments):
    env=launch_environment(stack)
    check_monado(stack,env['MWXR_NATIVE_RUNTIME_JSON'])
    root=Path(env['MWXR_PUBLIC_BRIDGE_ROOT'])
    scripts={'steam':'run-windows-steam.zsh','install-steam':'install-windows-steam.zsh',
        'openxr':'run-in-process-openxr.zsh','openvr':'run-openvr-game.zsh'}
    if action not in scripts:raise ValueError('Unknown Windows Steam action')
    return ['zsh',str(root/'scripts'/scripts[action]),*arguments],env

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stack',required=True)
    parser.add_argument('--action',choices=['steam','install-steam','openxr','openvr'],default='openxr')
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    try:
        cmd,env=command(read_stack(args.stack),args.action,args.arguments)
        sys.exit(subprocess.call(cmd,env=env))
    except (ValueError,OSError) as error:sys.exit(str(error))
