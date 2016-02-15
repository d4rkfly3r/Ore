from itertools import zip_longest


def cmp(a, b):
    return (a > b) - (a < b)


class CmpShim(object):

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0


class Item(CmpShim):
    pass


class IntegerItem(Item):

    def __init__(self, value=0):
        self.value = int(value)

    @property
    def is_null(self):
        return self.value == 0

    def __cmp__(self, item):
        if item is None:
            return 0 if self.is_null else 1

        if isinstance(item, IntegerItem):
            return cmp(self.value, item.value)
        elif isinstance(item, StringItem):
            return 1
        elif isinstance(item, ListItem):
            return 1

        raise ValueError("invalid item: {0!r}".format(item))

    def __str__(self):
        return str(self.value)


class StringItem(Item):
    FOLLOWED_BY_DIGIT_TRANSFORMS = {
        'a': 'alpha',
        'b': 'beta',
        'm': 'milestone',
    }

    ALIASES = {
        'ga': '',
        'final': '',
        'cr': 'rc',
    }

    QUALIFIERS = ['alpha', 'beta', 'milestone', 'rc', 'snapshot', '', 'sp']

    def __init__(self, value, followed_by_digit):
        if followed_by_digit and len(value) == 1:
            value = self.FOLLOWED_BY_DIGIT_TRANSFORMS.get(value, value)
        value = self.ALIASES.get(value, value)
        self.value = value

    @property
    def is_null(self):
        return self.comparable_qualifier == self.QUALIFIERS.index('')

    @property
    def comparable_qualifier(self):
        try:
            return str(self.QUALIFIERS.index(self.value))
        except ValueError:
            return '{}-{}'.format(len(self.QUALIFIERS), self.value)

    def __cmp__(self, item):
        if item is None:
            return cmp(self.comparable_qualifier, str(self.QUALIFIERS.index('')))

        if isinstance(item, IntegerItem):
            return -1
        elif isinstance(item, StringItem):
            return cmp(self.comparable_qualifier, item.comparable_qualifier)
        elif isinstance(item, ListItem):
            return -1

        raise ValueError("invalid item: {0!r}".format(item))

    def __str__(self):
        return self.value


class ListItem(Item):

    def __init__(self, value=None):
        if value is None:
            value = []
        self.value = list(value)

    @property
    def is_null(self):
        return len(self.value) == 0

    def normalize(self):
        value = []
        for n in range(len(self.value) - 1, -1, -1):
            item = self.value[n]
            if item.is_null:
                continue
            elif not isinstance(item, ListItem):
                value = self.value[:n + 1] + value
                break
        self.value = value

    def __cmp__(self, item):
        if item is None:
            if self.is_null:
                return 0
            return cmp(self.value[0], None)

        if isinstance(item, IntegerItem):
            return -1
        elif isinstance(item, StringItem):
            return 1
        elif isinstance(item, ListItem):
            for l, r in zip_longest(self.value, item.value):
                result = 0

                if l is None and r is None:
                    result = 0
                elif l is None:
                    result = -1 * cmp(r, l)
                else:
                    result = cmp(l, r)

                if result != 0:
                    return result

            return 0

        raise ValueError("invalid item: {0!r}".format(item))

    def __str__(self):
        out = []
        for n, item in enumerate(self.value):
            if n > 0:
                out.append('-' if isinstance(item, ListItem) else '.')
            out.append(str(item))
        return ''.join(out)


class ComparableVersion(CmpShim):

    def __init__(self, version):
        if isinstance(version, ComparableVersion):
            version = version.value

        self.value = version

        self.populate()

    def populate(self):
        self.items = ListItem()

        version = self.value.lower()
        cur_list = self.items
        stack = []
        is_digit = False
        start_index = 0

        for i, char in enumerate(version):
            if char == '.' or char == '-':
                if i == start_index:
                    cur_list.value.append(IntegerItem(0))
                else:
                    cur_list.value.append(self._parse_item(is_digit, version[start_index:i]))
                start_index = i + 1

                if char == '-':
                    new_list = ListItem()
                    cur_list.value.append(new_list)
                    cur_list = new_list

                    stack.append(cur_list)
            elif char in '0123456789':
                if not is_digit and i > start_index:
                    cur_list.value.append(StringItem(version[start_index:i], True))
                    start_index = i

                    new_list = ListItem()
                    cur_list.value.append(new_list)
                    cur_list = new_list

                    stack.append(cur_list)
                is_digit = True
            else:
                if is_digit and i > start_index:
                    cur_list.value.append(self._parse_item(is_digit, version[start_index:i]))
                    start_index = i

                    new_list = ListItem()
                    cur_list.value.append(new_list)
                    cur_list = new_list

                    stack.append(cur_list)
                is_digit = False

        if len(version) > start_index:
            cur_list.value.append(self._parse_item(is_digit, version[start_index:]))

        while stack:
            cur_list = stack.pop()
            cur_list.normalize()

        self.canonical_value = str(self.items)

    def _parse_item(self, is_digit, buf):
        return IntegerItem(buf) if is_digit else StringItem(buf, False)

    def __cmp__(self, item):
        if isinstance(item, ComparableVersion):
            return cmp(self.items, item.items)
        raise TypeError("unorderable {0!r} vs {1!r}".format(self, item))

    def __repr__(self):
        return self.canonical_value
