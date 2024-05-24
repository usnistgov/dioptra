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
"""Error handlers for the user endpoints."""
from __future__ import annotations

from flask_restx import Api


class NoCurrentUserError(Exception):
    """There is no currently logged-in user."""


class UserPasswordChangeError(Exception):
    """Password change failed."""


class UserPasswordChangeSamePasswordError(Exception):
    """Password change failed."""


class UserPasswordExpiredError(Exception):
    """Password expired."""


class UserPasswordVerificationError(Exception):
    """Password verification failed."""


class UsernameNotAvailableError(Exception):
    """The username is not available."""


class UserEmailNotAvailableError(Exception):
    """The email address is not available."""


class UserDoesNotExistError(Exception):
    """The requested user does not exist."""


class UserRegistrationError(Exception):
    """The user registration form contains invalid parameters."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(NoCurrentUserError)
    def handle_no_current_user_error(error):
        return {"message": "There is no currently logged-in user"}, 401

    @api.errorhandler(UserPasswordChangeError)
    def handle_user_password_change_error_error(error):
        return {"message": "Password Change Failed"}, 403

    @api.errorhandler(UserPasswordChangeSamePasswordError)
    def handle_user_password_change_same_error_error(error):
        return {
            "message": "Password Change Failed - The provided password matches"
            "the existing password. Please provide a different password."
        }, 403

    @api.errorhandler(UserPasswordExpiredError)
    def handle_user_password_expired_error(error):
        return {"message": "Password expired."}, 401

    @api.errorhandler(UserPasswordVerificationError)
    def handle_user_password_verification_error_error(error):
        return {"message": "Password Verification Failed"}, 403

    @api.errorhandler(UserDoesNotExistError)
    def handle_user_does_not_exist_error(error):
        return {"message": "Not Found - The requested user does not exist"}, 404

    @api.errorhandler(UsernameNotAvailableError)
    def handle_username_not_available_error(error):
        return (
            {
                "message": "Bad Request - The username on the registration form "
                "is not available. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(UserEmailNotAvailableError)
    def handle_email_not_available_error(error):
        return (
            {
                "message": "Bad Request - The email on the registration form "
                "is not available. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(UserRegistrationError)
    def handle_user_registration_error(error):
        return (
            {
                "message": "Bad Request - The user registration form contains "
                "invalid parameters. Please verify and resubmit."
            },
            400,
        )
