#!/usr/bin/env python

import re
import subprocess
import sys
import traceback

# Subvert output buffering.
def puts(string):
    sys.stdout.write(string)
    sys.stdout.flush()

def pretty_print_stack(binary, line):
    addrs = line.split()[1:]
    # Addresses are return addresses unless preceded by a '@'. We want the
    # caller address so line numbers are more intuitive. Thus we subtract 1
    # from the address to get the call code.
    for i in range(len(addrs)):
        addr = addrs[i]
        if addr.startswith('@'):
            addrs[i] = addr[1:]
        else:
            addrs[i] = '%lx' % (int(addrs[i], 16) - 1)

    # Output like this:
    #        0x004002be: start64 at path/to/kvm-unit-tests/x86/cstart64.S:208
    #         (inlined by) test_ept_violation at path/to/kvm-unit-tests/x86/vmx_tests.c:1719 (discriminator 1)
    cmd = ['addr2line', '-e', binary, '-i', '-f', '--pretty', '--address']
    cmd.extend(addrs)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        puts(line)
        return

    for line in out.splitlines():
        m = re.match('(.*) at [^ ]*/kvm-unit-tests/([^ ]*):([0-9]+)(.*)', line)
        if m is None:
            puts('%s\n' % line)
            return

        head, path, line, tail = m.groups()
        line = int(line)
        puts('%s at %s:%d%s\n' % (head, path, line, tail))
        try:
            lines = open(path).readlines()
        except IOError:
            continue
        if line > 1:
            puts('        %s\n' % lines[line - 2].rstrip())
        puts('      > %s\n' % lines[line - 1].rstrip())
        if line < len(lines):
            puts('        %s\n' % lines[line].rstrip())

def main():
    if len(sys.argv) != 2:
        sys.stderr.write('usage: %s <kernel>\n' % sys.argv[0])
        sys.exit(1)

    binary = sys.argv[1]

    try:
        while True:
            # Subvert input buffering.
            line = sys.stdin.readline()
            if line == '':
                break

            if not line.strip().startswith('STACK:'):
                puts(line)
                continue

            try:
                pretty_print_stack(binary, line)
            except Exception:
                puts('Error pretty printing stack:\n')
                puts(traceback.format_exc())
                puts('Continuing without pretty printing...\n')
                while True:
                    puts(line)
                    line = sys.stdin.readline()
                    if line == '':
                        break
    except:
        sys.exit(1)

if __name__ == '__main__':
    main()
