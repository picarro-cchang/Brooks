# build_version.py
#
# Yeah this is a bit of a hack. It just returns the version from the defs file.
# Someday the build script should autogenerate a release_version.py script
# similar to the way we do host software release builds.

import Win7MigrationToolsDefs as mdefs

def versionNumString():
    return mdefs.MIGRATION_TOOLS_VERSION

