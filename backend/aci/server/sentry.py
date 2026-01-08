import sentry_sdk

from aci.server import config


def setup_sentry() -> None:
    if config.ENVIRONMENT != "local":
        sentry_sdk.init(
            environment=config.ENVIRONMENT,
            dsn=config.SENTRY_DSN,
            # Add data like request headers and IP for users,
            # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
            traces_sample_rate=0.1 if config.ENVIRONMENT == "production" else 1.0,
            _experiments={
                "continuous_profiling_auto_start": True,
            },
        )
