# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
"""Apply a connection-local TLS policy without changing global SSL configuration."""

import ssl

KEY_EXCHANGES = {"default", "hybrid-required"}


def validate_key_exchange(value: str) -> str:
    """Require one of the supported TLS key-exchange selections.

    Args:
        value: default permits the runtime's ordinary groups; hybrid-required requires
            X25519MLKEM768, combining classical and post-quantum exchange.

    Returns:
        The unchanged selection string, suitable for later policy enforcement.

    Raises:
        ValueError: The value is not a supported selection.
    """
    if value not in KEY_EXCHANGES:
        raise ValueError("key_exchange must be default or hybrid-required")
    return value


def enforce_tls(
    context: ssl.SSLContext, key_exchange: str = "default"
) -> ssl.SSLContext:
    """Require TLS 1.3 and optionally hybrid key exchange on one SSL context.

    A required hybrid exchange must be supported by the runtime; it never falls back to
    classical-only exchange. Failure to select the hybrid group can occur after the
    context's TLS minimum has been changed. Callers that need to preserve the original
    context must account for that partial update.

    Args:
        context: Existing client or server SSL context to modify in place. Its
            certificate, trust and hostname-verification configuration is retained.
        key_exchange: default retains the runtime's groups; hybrid-required selects only
            X25519MLKEM768 and requires runtime support for set_groups.

    Returns:
        The same context, with a minimum of TLS 1.3. An already stricter minimum is
        retained. No process-wide SSL defaults are changed.

    Raises:
        ValueError: The selection is unknown, the context disables TLS 1.3 or sets a
            lower maximum, or the runtime cannot enforce the required hybrid group.
    """
    validate_key_exchange(key_exchange)
    maximum = context.maximum_version
    if maximum != ssl.TLSVersion.MAXIMUM_SUPPORTED and maximum < ssl.TLSVersion.TLSv1_3:
        raise ValueError("TLS maximum_version must permit TLS 1.3")
    if context.options & ssl.OP_NO_TLSv1_3:
        raise ValueError("TLS 1.3 must not be disabled")
    context.minimum_version = max(context.minimum_version, ssl.TLSVersion.TLSv1_3)
    if key_exchange == "hybrid-required":
        setter = getattr(context, "set_groups", None)
        if not callable(setter):
            raise ValueError(
                "hybrid-required needs SSLContext.set_groups and X25519MLKEM768 support"
            )
        try:
            setter("X25519MLKEM768")
        except (ValueError, ssl.SSLError) as exc:
            raise ValueError(
                "hybrid-required cannot select X25519MLKEM768 on this runtime"
            ) from exc
    return context
