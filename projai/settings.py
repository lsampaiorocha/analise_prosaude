DEBUG = True

# when using logging
CONFIG_LOG = {
    "version": 1,
    "formatters": {
        "client": {
            "format": "%(levelname)s: %(message)s"
        },
        "standard": {
            "format": "%(levelname)s - function: (%(name)s at %(funcName)s line %(lineno)d): %(message)s"
        }
    },
    "handlers": {
        "client": {
            "class": "logging.StreamHandler",
            "formatter": "client",
            "level": "INFO"
        },
        "standard": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG"
        }
    },
    "root": {
        "handlers": [
            "standard"
        ],
        "level": "DEBUG"
    },
    "loggers": {
        "client": {
            "handlers": [
                "client"
            ],
            "level": "DEBUG",
            "propagate": False
        },
        "standard": {
            "handlers": [
                "standard"
            ],
            "level": "DEBUG",
            "propagate": False
        }
    }
}