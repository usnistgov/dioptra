# This is a fork of the work
# https://github.com/gahjelle/pyplugs/blob/5e1586994051e32b0e6bdc6b1b75a3d011443940/pyplugs/_exceptions.py  # noqa: B950
# See copyright below.
#
# Copyright (c) 2019 Geir Arne Hjelle
# Distributed under the terms of the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Exceptions for the mitre.securingai.pyplugs package

Custom exceptions used by PyPlugs for more helpful error messages
"""

from .base import BasePyPlugsException


class UnknownPackageError(BasePyPlugsException):
    """PyPlugs could not import the given package."""


class UnknownPluginError(BasePyPlugsException):
    """PyPlugs could not locate the given plugin."""


class UnknownPluginFunctionError(BasePyPlugsException):
    """PyPlugs could not locate the given function within a plugin."""
