"""
The MIT License (MIT)

Copyright (c) 2015-2016 Kim Blomqvist

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import re
from SCons.Builder import BuilderBase
from click.testing import CliRunner

from .scripts import yasha


class Builder(BuilderBase):

    def __init__(self, action="yasha $SOURCE -o $TARGET"):
        def scan(node, env, path):
            src = str(node.srcnode())
            src_dir = os.path.dirname(src)
            variant_dir = os.path.dirname(str(node))

            cli_command = [src, "-M"]
            extensions = re.search(r"(-e|--extensions)\s*(.+)", action)
            variables = re.search(r"(-v|--variables)\s*(.+)", action)

            if extensions:
                cli_command += ["-e", extensions.group(2)]
            if variables:
                cli_command += ["-v", extensions.group(2)]
            if re.match(r"--no-variables", action):
                cli_command += ["--no-variables"]
            if re.match(r"--no-extensions", action):
                cli_command += ["--no-extensions"]

            runner = CliRunner()
            result = runner.invoke(yasha.cli, cli_command)

            deps = result.output[:-1].split(" ")[2:]
            deps = [d.replace(src_dir, variant_dir) for d in deps]
            return env.File(deps)

        def emit(target, source, env):
            env.Clean(target[0], str(target[0]) + ".d")
            return target, source

        from SCons.Scanner import Scanner
        from SCons.Action import Action
        BuilderBase.__init__(self,
                             action=Action(action),
                             emitter=emit,
                             source_scanner=Scanner(function=scan),
                             single_source=True
                             )


class CBuilder(Builder):

    def __call__(self, *args, **kw):
        def is_c_file(file, include_headers=True):
            suffix = os.path.splitext(str(file))[1]
            accept = [".c", ".cc", ".cpp", ".s", ".S", ".asm"]
            if include_headers:
                accept += [".h", ".hh", ".hpp"]
            return True if suffix in accept else False

        sources = Builder.__call__(self, *args, **kw)
        return [x for x in sources if is_c_file(x, include_headers=False)]
