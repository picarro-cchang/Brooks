import argparse
import pathlib
import yamale

BASE_DIR = pathlib.Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "udfg.yaml"
SCHEMA_PATH = BASE_DIR / "config" / "udfg_schema.yaml"


def get_config(argv=None):
    schema = yamale.make_schema(SCHEMA_PATH)
    data = yamale.make_data(CONFIG_PATH)

    try:
        config = yamale.validate(schema, data)
    except ValueError as ve:
        print("Not a valid configuration for User Data File Generator", ve)

    return config[0][0]
