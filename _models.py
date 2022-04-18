import re
import typing

# steamcommunity.com:443
# https://steamcommunity.com:443
from _utils import normalize_header_key, normalize_header_value, obfuscate_sensitive_headers, _decode_header_lines
from log import log

URI_RE = re.compile(
    r"^(?:([a-zA-Z][a-zA-Z0-9+.-]*)://)?"  # scheme 匹配协议 :号结束
    r"(?:([^\\/?#]*))?"  # authority # 匹配鉴权域名  user:password@127.0.0.1:3128
    r"([^?#]*)"  # path /path/xx  匹配非?#开头的
    r"(?:\?([^#]*))?"  # query # 匹配?号开头的非#号结束的
    r"(?:#(.*))?$",  # fragment # 匹配#号开头,任意结束的
    re.UNICODE | re.DOTALL,
)
REG_NAME_PAT = r"(?:[^\[\]%:/?#]|%[a-fA-F0-9]{2})*"
IPV4_PAT = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"

SUBAUTHORITY_PAT = (u"^(?:(.*)@)?(%s|%s)(?::([0-9]{0,5}))?$") % (
    REG_NAME_PAT,
    IPV4_PAT,
)
SUBAUTHORITY_RE = re.compile(SUBAUTHORITY_PAT, re.UNICODE | re.DOTALL)


class LocationParseError(Exception):
    """Raised when get_host or similar fails to parse the URL input."""

    def __init__(self, location):
        message = "Failed to parse: %s" % location
        self.location = location


class Url:
    def __init__(self, url: typing.Union["URL", str] = ""):
        pass
        port_map = {
            "ftp": 21,
            "http": 80,
            "https": 443,
            "ws": 80,
            "wss": 443,
        }
        try:
            scheme, authority, path, query, fragment = URI_RE.match(url).groups()
        except Exception as e:
            raise LocationParseError(url)

        self.scheme: str = scheme
        if authority:
            auth, host, port = SUBAUTHORITY_RE.match(authority).groups()
            if port == "":
                port = None
        else:
            auth, host, port = None, None, None

        if port is not None:
            port = int(port)
            if not (0 <= port <= 65535):
                raise LocationParseError(url)
        else:
            port = port_map.get(self.scheme)

        self.port = port
        self.host = host
        self.auth = host

    @property
    def raw_scheme(self) -> bytes:
        """
        The raw bytes representation of the URL scheme, such as b"http", b"https".
        Always normalised to lowercase.
        """
        return self.scheme.encode("ascii")


HeaderTypes = typing.Union[
    "Headers",
    typing.Dict[str, str],
    typing.Dict[bytes, bytes],
    typing.Sequence[typing.Tuple[str, str]],
    typing.Sequence[typing.Tuple[bytes, bytes]],
]


class Headers(typing.MutableMapping[str, str]):
    """
    HTTP headers, as a case-insensitive multi-dict.
    """

    def __init__(self, headers: HeaderTypes = None, encoding: str = None) -> None:
        if headers is None:
            self._list = []  # type: typing.List[typing.Tuple[bytes, bytes, bytes]]
        elif isinstance(headers, Headers):
            self._list = list(headers._list)
        elif isinstance(headers, dict):
            self._list = [
                (
                    normalize_header_key(k, lower=False, encoding=encoding),
                    normalize_header_key(k, lower=True, encoding=encoding),
                    normalize_header_value(v, encoding),
                )
                for k, v in headers.items()
            ]
        else:
            self._list = [
                (
                    normalize_header_key(k, lower=False, encoding=encoding),
                    normalize_header_key(k, lower=True, encoding=encoding),
                    normalize_header_value(v, encoding),
                )
                for k, v in headers
            ]

        self._encoding = encoding

    @property
    def encoding(self) -> str:
        """
        Header encoding is mandated as ascii, but we allow fallbacks to utf-8
        or iso-8859-1.
        """
        if self._encoding is None:
            for encoding in ["ascii", "utf-8"]:
                for key, value in self.raw:
                    try:
                        key.decode(encoding)
                        value.decode(encoding)
                    except UnicodeDecodeError:
                        break
                else:
                    # The else block runs if 'break' did not occur, meaning
                    # all values fitted the encoding.
                    self._encoding = encoding
                    break
            else:
                # The ISO-8859-1 encoding covers all 256 code points in a byte,
                # so will never raise decode errors.
                self._encoding = "iso-8859-1"
        return self._encoding

    @encoding.setter
    def encoding(self, value: str) -> None:
        self._encoding = value

    @property
    def raw(self) -> typing.List[typing.Tuple[bytes, bytes]]:
        """
        Returns a list of the raw header items, as byte pairs.
        """
        return [(raw_key, value) for raw_key, _, value in self._list]

    def keys(self) -> typing.KeysView[str]:
        return {key.decode(self.encoding): None for _, key, value in self._list}.keys()

    def values(self) -> typing.ValuesView[str]:
        values_dict: typing.Dict[str, str] = {}
        for _, key, value in self._list:
            str_key = key.decode(self.encoding)
            str_value = value.decode(self.encoding)
            if str_key in values_dict:
                values_dict[str_key] += f", {str_value}"
            else:
                values_dict[str_key] = str_value
        return values_dict.values()

    def items(self) -> typing.ItemsView[str, str]:
        """
        Return `(key, value)` items of headers. Concatenate headers
        into a single comma separated value when a key occurs multiple times.
        """
        values_dict: typing.Dict[str, str] = {}
        for _, key, value in self._list:
            str_key = key.decode(self.encoding)
            str_value = value.decode(self.encoding)
            if str_key in values_dict:
                values_dict[str_key] += f", {str_value}"
            else:
                values_dict[str_key] = str_value
        return values_dict.items()

    def multi_items(self) -> typing.List[typing.Tuple[str, str]]:
        """
        Return a list of `(key, value)` pairs of headers. Allow multiple
        occurrences of the same key without concatenating into a single
        comma separated value.
        """
        return [
            (key.decode(self.encoding), value.decode(self.encoding))
            for _, key, value in self._list
        ]

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        """
        Return a header value. If multiple occurrences of the header occur
        then concatenate them together with commas.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def get_list(self, key: str, split_commas: bool = False) -> typing.List[str]:
        """
        Return a list of all header values for a given key.
        If `split_commas=True` is passed, then any comma separated header
        values are split into multiple return strings.
        """
        get_header_key = key.lower().encode(self.encoding)

        values = [
            item_value.decode(self.encoding)
            for _, item_key, item_value in self._list
            if item_key.lower() == get_header_key
        ]

        if not split_commas:
            return values

        split_values = []
        for value in values:
            split_values.extend([item.strip() for item in value.split(",")])
        return split_values

    def update(self, headers: HeaderTypes = None) -> None:  # type: ignore
        headers = Headers(headers)
        for key in headers.keys():
            if key in self:
                self.pop(key)
        self._list.extend(headers._list)

    def copy(self) -> "Headers":
        return Headers(self, encoding=self.encoding)

    def __getitem__(self, key: str) -> str:
        """
        Return a single header value.

        If there are multiple headers with the same key, then we concatenate
        them with commas. See: https://tools.ietf.org/html/rfc7230#section-3.2.2
        """
        normalized_key = key.lower().encode(self.encoding)

        items = [
            header_value.decode(self.encoding)
            for _, header_key, header_value in self._list
            if header_key == normalized_key
        ]

        if items:
            return ", ".join(items)

        raise KeyError(key)

    def __setitem__(self, key: str, value: str) -> None:
        """
        Set the header `key` to `value`, removing any duplicate entries.
        Retains insertion order.
        """
        set_key = key.encode(self._encoding or "utf-8")
        set_value = value.encode(self._encoding or "utf-8")
        lookup_key = set_key.lower()

        found_indexes = [
            idx
            for idx, (_, item_key, _) in enumerate(self._list)
            if item_key == lookup_key
        ]

        for idx in reversed(found_indexes[1:]):
            del self._list[idx]

        if found_indexes:
            idx = found_indexes[0]
            self._list[idx] = (set_key, lookup_key, set_value)
        else:
            self._list.append((set_key, lookup_key, set_value))

    def __delitem__(self, key: str) -> None:
        """
        Remove the header `key`.
        """
        del_key = key.lower().encode(self.encoding)

        pop_indexes = [
            idx
            for idx, (_, item_key, _) in enumerate(self._list)
            if item_key.lower() == del_key
        ]

        if not pop_indexes:
            raise KeyError(key)

        for idx in reversed(pop_indexes):
            del self._list[idx]

    def __contains__(self, key: typing.Any) -> bool:
        header_key = key.lower().encode(self.encoding)
        return header_key in [key for _, key, _ in self._list]

    def __iter__(self) -> typing.Iterator[typing.Any]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._list)

    def __eq__(self, other: typing.Any) -> bool:
        try:
            other_headers = Headers(other)
        except ValueError:
            return False

        self_list = [(key, value) for _, key, value in self._list]
        other_list = [(key, value) for _, key, value in other_headers._list]
        return sorted(self_list) == sorted(other_list)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__

        encoding_str = ""
        if self.encoding != "ascii":
            encoding_str = f", encoding={self.encoding!r}"

        as_list = list(obfuscate_sensitive_headers(self.multi_items()))
        as_dict = dict(as_list)

        no_duplicate_keys = len(as_dict) == len(as_list)
        if no_duplicate_keys:
            return f"{class_name}({as_dict!r}{encoding_str})"
        return f"{class_name}({as_list!r}{encoding_str})"




class Header():
    """
    处理tcp数据头
    """

    def __init__(self, data: bytes):
        # log.debug(f'header \n  {data!r}')
        self.data = data
        data = data.split(b'\r\n\r\n')
        self.header: bytes = data[0] # http协议头
        self.content: bytes = data[1] # http body
        header_list: typing.List[bytes] = self.header.split(b'\r\n')
        self.line0 = header_list[0]
        line = header_list[0].decode('utf8').split(' ')
        self.method: str = line[0].upper()
        url = Url(line[1])
        self.host: str = url.host
        self.port: int = url.port
        self.scheme: str = url.scheme

        if self.method == 'CONNECT':
            pass
            self.is_ssl = True
        else:
            pass
            self.is_ssl = False
        # auto_headers: typing.List[typing.Tuple[bytes, bytes]] = []
        # for item in header_list[1:]:
        #     raw = item.split(b':')
        #     auto_headers.append((raw[0], raw[1]))
        headers = _decode_header_lines(header_list[1:])
        # self.auto_header = auto_headers
        self.headers = Headers(headers)
        if self.headers.get('proxy'):
            proxy_url = Url( self.headers.get('proxy'))
            self.proxy_host = proxy_url.host
            self.proxy_port = proxy_url.port
        else:
            self.proxy_host = None
            self.proxy_port = None

        self.is_proxy2 = self.headers.get('proxy2')