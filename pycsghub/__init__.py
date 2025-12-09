from datetime import datetime, timezone
from unittest import mock

__version__ = "0.8.0"

# This method is copied from huggingface_hub v0.27.0
# Source: https://github.com/huggingface/huggingface_hub/blob/v0.27.0/src/huggingface_hub/utils/_datetime.py
# The method is copied due to a bug in huggingface_hub versions earlier than v0.26.2,
# where RFC 3339 datetime strings without milliseconds cannot be parsed correctly.
# To ensure datetime string can be handled correctly, we patch this method using mock.patch.
# For more details, see the related PR and issue:
# https://github.com/huggingface/huggingface_hub/pull/2683
def _parse_datetime(date_string: str) -> datetime:
    """
    Parse a date_string returned from the server to a datetime object.

    This parser is a weak-parser is the sense that it handles only a single format of
    date_string. It is expected that the server format will never change. The
    implementation depends only on the standard lib to avoid an external dependency
    (python-dateutil). See full discussion about this decision on PR:
    https://github.com/huggingface/huggingface_hub/pull/999.

    Example:
        ```py
        > parse_datetime('2022-08-19T07:19:38.123Z')
        datetime.datetime(2022, 8, 19, 7, 19, 38, 123000, tzinfo=timezone.utc)
        ```

    Args:
        date_string (`str`):
            A string representing a datetime returned by the Hub server.
            String is expected to follow '%Y-%m-%dT%H:%M:%S.%fZ' pattern.

    Returns:
        A python datetime object.

    Raises:
        :class:`ValueError`:
            If `date_string` cannot be parsed.
    """
    try:
        # Normalize the string to always have 6 digits of fractional seconds
        if date_string.endswith("Z"):
            # Case 1: No decimal point (e.g., "2024-11-16T00:27:02Z")
            if "." not in date_string:
                # No fractional seconds - insert .000000
                date_string = date_string[:-1] + ".000000Z"
            # Case 2: Has decimal point (e.g., "2022-08-19T07:19:38.123456789Z")
            else:
                # Get the fractional and base parts
                base, fraction = date_string[:-1].split(".")
                # fraction[:6] takes first 6 digits and :0<6 pads with zeros if less than 6 digits
                date_string = f"{base}.{fraction[:6]:0<6}Z"

        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise ValueError(
            f"Cannot parse '{date_string}' as a datetime. Date string is expected to"
            " follow '%Y-%m-%dT%H:%M:%S.%fZ' pattern."
        ) from e


patcher = mock.patch(
    'huggingface_hub.hf_api.parse_datetime',
    new=_parse_datetime
)
patcher.start()