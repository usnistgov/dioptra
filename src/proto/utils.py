from __future__ import annotations

import logging.handlers
import typing
import urllib.parse
import urllib.request


if typing.TYPE_CHECKING:
    import http.cookiejar
    import logging
    import ssl


class CookieHTTPHandler(logging.handlers.HTTPHandler):
    """
    A logging handler which can send cookies with its logging requests.  This
    can be useful when one needs to maintain an authenticated session.
    """

    def __init__(
        self,
        host: str,
        url: str,
        secure: bool = False,
        cookies: http.cookiejar.CookieJar | None = None,
        context: ssl.SSLContext | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Initialize this logging handler.

        Args:
            host: The host to send to, as a string; a port may be included
                using syntax <host>:<port>.
            url: The path component of a URL to send to
            secure: If True, connect via HTTPS, else HTTP
            cookies: A cookie jar to be consulted for all requests
            context: An SSLContext object to affect secure connection settings.
                Only makes sense if secure=True.
            user_agent: A value for a User-Agent header, to deal with
                flask-login's "strong" session protection.  The header value
                must be consistent for all requests using a given cookie, or
                the server will reject it.
        """
        # Just pass args through, except null out credentials and fix method
        # as POST
        super().__init__(host, url, "POST", secure, None, context)

        self.cookies = cookies
        self.user_agent = user_agent

        scheme = "https" if secure else "http"
        self.full_url = urllib.parse.urlunparse((scheme, host, url, None, None, None))

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send the logging record to the web server.

        Args:
            record: The logging record to send
        """
        data = urllib.parse.urlencode(self.mapLogRecord(record))

        headers = {}
        if self.user_agent:
            headers["User-Agent"] = self.user_agent

        req = urllib.request.Request(
            url=self.full_url, data=data.encode("utf-8"), headers=headers
        )

        if self.cookies:
            self.cookies.add_cookie_header(req)

        with urllib.request.urlopen(req, context=self.context) as resp:
            # Discard response content
            resp.read()
