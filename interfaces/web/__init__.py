"""Legacy Flask web UI — prefer interfaces.gui or interfaces.api."""

import warnings

warnings.warn(
    "interfaces.web is legacy. Use interfaces.gui.main_gui or interfaces.api.main.",
    DeprecationWarning,
    stacklevel=2,
)
