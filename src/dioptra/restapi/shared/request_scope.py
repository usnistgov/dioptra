# Code below is copied from Flask-Injector library.  It has the following
# license:
#
# Copyright (c) 2012, Alec Thomas
# Copyright (c) 2015 Smarkets Limited <support@smarkets.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  - Neither the name of SwapOff.org nor the names of its contributors may
#    be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Tell flake8 to ignore this file.  It is mostly just copy-pastes from
# Flask-Injector.
# flake8: noqa

from typing import Any, Dict

import flask
from injector import Injector, Provider, Scope, ScopeDecorator
from werkzeug.local import Local, LocalManager


class CachedProviderWrapper(Provider):
    def __init__(self, old_provider: Provider) -> None:
        self._old_provider = old_provider
        self._cache = {}  # type: Dict[int, Any]

    def get(self, injector: Injector) -> Any:
        key = id(injector)
        try:
            return self._cache[key]
        except KeyError:
            instance = self._cache[key] = self._old_provider.get(injector)
            return instance


class RequestScope(Scope):
    """A scope whose object lifetime is tied to a request.

    @request
    class Session:
        pass
    """

    # We don't want to assign here, just provide type hints
    if False:
        _local_manager = None  # type: LocalManager
        _locals = None  # type: Any

    def cleanup(self) -> None:
        self._local_manager.cleanup()

    def prepare(self) -> None:
        self._locals.scope = {}

    def configure(self) -> None:
        self._locals = Local()
        self._local_manager = LocalManager([self._locals])
        self.prepare()

    def get(self, key: Any, provider: Provider) -> Any:
        try:
            return self._locals.scope[key]
        except KeyError:
            new_provider = self._locals.scope[key] = CachedProviderWrapper(provider)
            return new_provider


request = ScopeDecorator(RequestScope)


def set_request_scope_callbacks(app: flask.Flask, injector: Injector) -> None:
    """
    Set callbacks to enable request scoping behavior: initialize at the
    beginning of request handling, and cleanup at the end.

    Args:
        app: A Flask app
        injector: An injector, used to get the RequestScope object
    """

    def reset_request_scope_before(*args: Any, **kwargs: Any) -> None:
        injector.get(RequestScope).prepare()

    def global_reset_request_scope_after(*args: Any, **kwargs: Any) -> None:
        blueprint = flask.request.blueprint
        # If current blueprint has teardown_request_funcs associated with it we know there may be
        # a some teardown request handlers we need to inject into, so we can't reset the scope just yet.
        # We'll leave it to blueprint_reset_request_scope_after to do the job which we know will run
        # later and we know it'll run after any teardown_request handlers we may want to inject into.
        if blueprint is None or blueprint not in app.teardown_request_funcs:
            injector.get(RequestScope).cleanup()

    def blueprint_reset_request_scope_after(*args: Any, **kwargs: Any) -> None:
        # If we got here we truly know this is the last teardown handler, which means we can reset the
        # scope unconditionally.
        injector.get(RequestScope).cleanup()

    app.before_request_funcs.setdefault(None, []).insert(0, reset_request_scope_before)
    # We're accessing Flask internals here as the app.teardown_request decorator appends to a list of
    # handlers but Flask itself reverses the list when it executes them. To allow injecting request-scoped
    # dependencies into teardown_request handlers we need to run our teardown_request handler after them.
    # Also see https://github.com/alecthomas/flask_injector/issues/42 where it was reported.
    # Secondly, we need to handle blueprints. Flask first executes non-blueprint teardown handlers in
    # reverse order and only then executes blueprint-associated teardown handlers in reverse order,
    # which means we can't just set on non-blueprint teardown handler, but we need to set both.
    # In non-blueprint teardown handler we check if a blueprint handler will run – if so, we do nothing
    # there and leave it to the blueprint teardown handler.
    #
    # We need the None key to be present in the dictionary so that the dictionary iteration always yields
    # None as well. We *always* have to set the global teardown request.
    app.teardown_request_funcs.setdefault(None, []).insert(
        0, global_reset_request_scope_after
    )
    for bp, functions in app.teardown_request_funcs.items():
        if bp is not None:
            functions.insert(0, blueprint_reset_request_scope_after)
