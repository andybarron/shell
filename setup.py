#!/usr/bin/env python3
import subprocess
from shutil import which
from pathlib import Path
from os import chdir, getcwd, environ
import string
from typing import Union
import sys

CONFIG_FILENAME = '.zshrc-base.zsh'

CONFIG_CONTENTS = '''
# Andy's base zsh config

# Run the following command to install or update this config:
# python3 <(curl -sLH 'Cache-Control: no-cache' https://raw.githubusercontent.com/AndyBarron/shell/main/setup.py)

# init antigen
source ~/.antigen.zsh

# init oh-my-zsh
antigen use oh-my-zsh

# default oh-my-zsh plugins
antigen bundle git
antigen bundle asdf
antigen bundle kubectl

# third-party oh-my-zsh plugins
antigen bundle zsh-users/zsh-autosuggestions
ZSH_AUTOSUGGEST_STRATEGY=(completion history)
ZSH_AUTOSUGGEST_USE_ASYNC=true

antigen bundle zsh-users/zsh-completions
antigen bundle zsh-users/zsh-syntax-highlighting # must be last

# specify theme
antigen theme romkatv/powerlevel10k

# apply config
antigen apply

# my settings :)
export VISUAL=nvim
'''

REQUIRED_TOOLS = (
    'zsh',
    'git',
    'neovim',
    'byobu',
)


def esc(s: str) -> str:
    has_whitespace = any(c in string.whitespace for c in s)
    return repr(s) if has_whitespace else s


def cmd(*parts: str) -> None:
    print('RUN:', *[esc(part) for part in parts])
    subprocess.run(parts)


def cmd_output(*parts: str) -> str:
    print('RUN:', *[esc(part) for part in parts])
    return subprocess.check_output(parts).decode('utf-8').strip()


_stack = []


def pushd(dir: Union[str, Path]) -> None:
    global _stack
    _stack.append(getcwd())
    chdir(dir)

def popd() -> None:
    chdir(_stack.pop())


def main() -> None:
    print(f"Installing required tools: {', '.join(REQUIRED_TOOLS)}")
    cmd('sudo', 'apt', 'update')
    cmd('sudo', 'apt', 'install', *REQUIRED_TOOLS)

    print('Checking for asdf')
    asdf_path = Path.home() / '.asdf'
    if not asdf_path.is_dir():
        cmd('git', 'clone', 'https://github.com/asdf-vm/asdf.git', str(asdf_path))

    print('Updating asdf')
    try:
        pushd(asdf_path)
        cmd('git', 'checkout', cmd_output(
            *'git describe --abbrev=0 --tags'.split()))
    finally:
        popd()

    # No need to set up asdf; zsh plugin will do it

    print('Making sure important files exist')
    zshrc_path = Path.home() / '.zshrc'
    cmd('touch', str(zshrc_path))
    ssh_dir_path = Path.home() / '.ssh'
    cmd('mkdir', '-p', str(ssh_dir_path))

    antigen_path = Path.home() / '.antigen.zsh'
    print(f"Installing latest version of Antigen to {antigen_path}")
    antigen_src = cmd_output(
        'curl', '-sLH', 'Cache-Control: no-cache', 'https://git.io/antigen')
    with open(antigen_path, 'w') as f:
        f.write(antigen_src)

    config_path = Path.home() / CONFIG_FILENAME
    print(f'Creating/updating zsh base config at {config_path}')
    with open(config_path, 'w') as f:
        f.write(CONFIG_CONTENTS)

    print('Making sure .zshrc reads from base config')
    zshrc_line = f'source ~/{CONFIG_FILENAME}'
    found_line = False
    with open(zshrc_path, 'r') as f:
        found_line = any(line.rstrip() == zshrc_line for line in f)
    if not found_line:
        print('Adding source line to .zshrc')
        with open(zshrc_path, 'a') as f:
            f.write(f'\n{zshrc_line}\n')

    zsh_path = which('zsh')
    if zsh_path:
        print('Checking default shell')
        shell = environ['SHELL']
        if shell and (shell != zsh_path):
            print('Changing default shell to zsh')
            cmd('chsh', '-s', zsh_path)
    else:
        sys.exit('Unable to change default shell!')

    print('Done! You probably have to log out and back in again. Enjoy!')


if __name__ == '__main__':
    main()
