import re
import typing


def normalize_header_key(
        value: typing.Union[str, bytes],
        lower: bool,
        encoding: str = None,
) -> bytes:
    """
    Coerce str/bytes into a strictly byte-wise HTTP header key.
    """
    if isinstance(value, bytes):
        bytes_value = value
    else:
        bytes_value = value.encode(encoding or "ascii")

    return bytes_value.lower() if lower else bytes_value


def normalize_header_value(
        value: typing.Union[str, bytes], encoding: str = None
) -> bytes:
    """
    Coerce str/bytes into a strictly byte-wise HTTP header value.
    """
    if isinstance(value, bytes):
        return value
    return value.encode(encoding or "ascii")


def to_bytes(value: typing.Union[str, bytes], encoding: str = "utf-8") -> bytes:
    return value.encode(encoding) if isinstance(value, str) else value


def to_str(value: typing.Union[str, bytes], encoding: str = "utf-8") -> str:
    return value if isinstance(value, str) else value.decode(encoding)


def to_bytes_or_str(value: str, match_type_of: typing.AnyStr) -> typing.AnyStr:
    return value if isinstance(match_type_of, str) else value.encode()


def unquote(value: str) -> str:
    return value[1:-1] if value[0] == value[-1] == '"' else value


SENSITIVE_HEADERS = {"authorization", "proxy-authorization"}


def obfuscate_sensitive_headers(
        items: typing.Iterable[typing.Tuple[typing.AnyStr, typing.AnyStr]]
) -> typing.Iterator[typing.Tuple[typing.AnyStr, typing.AnyStr]]:
    for k, v in items:
        if to_str(k.lower()) in SENSITIVE_HEADERS:
            v = to_bytes_or_str("[secure]", match_type_of=v)
        yield k, v


# Remember that this has to run in O(n) time -- so e.g. the bytearray cast is
# critical.
obs_fold_re = re.compile(br"[ \t]+")


def _obsolete_line_fold(lines):
    it = iter(lines)
    last = None
    for line in it:
        match = obs_fold_re.match(line)
        if match:
            if last is None:
                raise Exception("continuation line at start of headers")
            if not isinstance(last, bytearray):
                last = bytearray(last)
            last += b" "
            last += line[match.end():]
        else:
            if last is not None:
                yield last
            last = line
    if last is not None:
        yield last


#  header-field   = field-name ":" OWS field-value OWS
token = r"[-!#$%&'*+.^_`|~0-9a-zA-Z]+"
field_name = token
OWS = r"[ \t]*"
vchar = r"[\x21-\x7e]"
vchar_or_obs_text = r"[^\x00\s]"
field_vchar = vchar_or_obs_text
field_content = r"{field_vchar}+(?:[ \t]+{field_vchar}+)*".format(**globals())

# We handle obs-fold at a different level, and our fixed-up field_content
# already grows to swallow the whole value, so ? instead of *
field_value = r"({field_content})?".format(**globals())
header_field = (
    r"(?P<field_name>{field_name})"
    r":"
    r"{OWS}"
    r"(?P<field_value>{field_value})"
    r"{OWS}".format(**globals())
)
header_field_re = re.compile(header_field.encode("ascii"))


def validate(regex, data, msg="malformed data", *format_args):
    match = regex.fullmatch(data)
    if not match:
        if format_args:
            msg = msg.format(*format_args)
        raise Exception(msg)
    return match.groupdict()


def _decode_header_lines(lines):
    for line in _obsolete_line_fold(lines):
        matches = validate(header_field_re, line, "illegal header line: {!r}", line)
        yield (matches["field_name"], matches["field_value"])
