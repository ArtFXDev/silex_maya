import re
from maya import cmds

from typing import List


def rename_duplicates_nodes() -> List[str]:
    """
    In some cases, having two nodes with the same name makes
    """
    # Find all objects that have the same shortname as another
    # We can indentify them because they have | in the name
    duplicates = [f for f in cmds.ls() if "|" in f]
    # Sort them by hierarchy so that we don't rename a parent before a child.
    duplicates.sort(key=lambda obj: obj.count("|"), reverse=True)

    if not duplicates:
        return []

    for name in duplicates:
        # Extract the base name
        m = re.compile("[^|]*$").search(name)
        if m is None:
            continue
        shortname = m.group(0)

        # Extract the numeric suffix
        m2 = re.compile(".*[^0-9]").match(shortname)
        if m2:
            stripSuffix = m2.group(0)
        else:
            stripSuffix = shortname

        # Rename, adding '#' as the suffix, which tells maya to find the next available number
        cmds.rename(name, (stripSuffix + "#"))

    return duplicates
