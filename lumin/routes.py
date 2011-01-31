import warnings


CHANGE_YOUR_IMPORT = """

******************************************************
The lumin.routes.Node as moved to lumin.node.NodeById.
***Please update your code to import from there.***
******************************************************
"""
warnings.warn(CHANGE_YOUR_IMPORT, stacklevel=2)

from lumin.node import NodeById
Node = NodeById




