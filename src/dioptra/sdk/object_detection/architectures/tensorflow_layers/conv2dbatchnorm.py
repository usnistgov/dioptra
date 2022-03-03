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
from __future__ import annotations

from typing import Tuple

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from tensorflow.keras.layers import (
        Activation,
        BatchNormalization,
        Conv2D,
        Layer,
        LeakyReLU,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )

DEFAULT_ACTIVATION = LeakyReLU(alpha=0.1)


class Conv2DBatchNormalization(Layer):
    def __init__(
        self,
        filters: int,
        kernel_size: Tuple[int, int],
        strides: Tuple[int, int] = (1, 1),
        padding: str = "same",
        data_format=None,
        dilation_rate: Tuple[int, int] = (1, 1),
        groups: int = 1,
        activation=DEFAULT_ACTIVATION,
        use_bias: bool = True,
        kernel_initializer="glorot_uniform",
        bias_initializer="zeros",
        kernel_regularizer=None,
        bias_regularizer=None,
        activity_regularizer=None,
        kernel_constraint=None,
        bias_constraint=None,
        batch_norm_before_activation=True,
        name="conv",
        **kwargs,
    ):
        super().__init__()
        self.conv2d = Conv2D(
            filters=filters,
            kernel_size=kernel_size,
            strides=strides,
            padding=padding,
            data_format=data_format,
            dilation_rate=dilation_rate,
            groups=groups,
            activation=activation,
            use_bias=use_bias,
            kernel_initializer=kernel_initializer,
            bias_initializer=bias_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer,
            activity_regularizer=activity_regularizer,
            kernel_constraint=kernel_constraint,
            bias_constraint=bias_constraint,
            name=name,
            **kwargs,
        )
        self.batch_norm = BatchNormalization(name=f"{name}_batch_norm")
        self.activation = Activation(activation, name=f"{name}_activation")
        self.batch_norm_before_activation = batch_norm_before_activation
        self._batch_norm_and_activation_fn = (
            self._batch_norm_before_activation
            if batch_norm_before_activation
            else self._batch_norm_after_activation
        )

    def call(self, inputs, training=None):
        x = self.conv2d(inputs)

        return self._batch_norm_and_activation_fn(x=x, training=training)

    def get_config(self):
        conv2d_arg_names = [
            "filters",
            "kernel_size",
            "strides",
            "padding",
            "data_format",
            "dilation_rate",
            "groups",
            "activation",
            "use_bias",
            "kernel_initializer",
            "bias_initializer",
            "kernel_regularizer",
            "bias_regularizer",
            "activity_regularizer",
            "kernel_constraint",
            "bias_constraint",
            "name",
        ]
        conv2d_config = {
            k: v for k, v in self.conv2d.get_config().items() if k in conv2d_arg_names
        }

        config = super().get_config()
        config.update(conv2d_config)
        config["batch_norm_before_activation"] = self.batch_norm_before_activation

        return config

    def _batch_norm_after_activation(self, x, training):
        x = self.activation(x)
        return self.batch_norm(x, training=training)

    def _batch_norm_before_activation(self, x, training):
        x = self.batch_norm(x, training=training)
        return self.activation(x)
