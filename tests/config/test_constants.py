"""Check constants engine"""

import pytest

from cjunct.config.constants.helpers import Mandatory


def test_mandatory_failure():
    """Validate mandatory variable ValueError"""

    # pylint: disable=missing-class-docstring
    class C:
        FAILED = Mandatory(lambda: None)

    with pytest.raises(ValueError, match="getters failed"):
        assert C.FAILED
