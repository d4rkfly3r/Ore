from zipfile import ZipFile

from jawa.cf import ClassFile
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from .mavenversion import ComparableVersion

DEPENDENCY_GRAMMAR = Grammar(r"""
    start            = dependencies
    dependencies     = dependency (";" dependency)*
    dependency       = instruction ":" target
    instruction      = "required-"? ("after" / "before")
    pluginid         = ~"[a-zA-Z0-9_\-*][a-zA-Z0-9_\-*]*"
    pluginidver      = pluginid ("@" versionspecifier)?
    rangedelimstart  = "[" / "("
    rangedelimend    = "]" / ")"
    version          = ~"[^[\](),]+"
    versionrange     = rangedelimstart ((version "," version?) / ("," version)) rangedelimend
    versionranges    = versionrange ("," versionrange)*
    versionspecifier = version / versionranges
    target           = "*" / pluginidver
    """)


class VersionRange(object):

    def __init__(self, lower_bound, lower_bound_inclusive, upper_bound, upper_bound_inclusive):
        self.lower_bound = ComparableVersion(lower_bound) if lower_bound else None
        self.lower_bound_inclusive = bool(lower_bound_inclusive)

        self.upper_bound = ComparableVersion(upper_bound) if upper_bound else None
        self.upper_bound_inclusive = bool(upper_bound_inclusive)

        if self.upper_bound and self.lower_bound and self.upper_bound < self.lower_bound:
            raise ValueError("The upper bound '{}' is less than the lower bound '{}'".format(self.upper_bound, self.lower_bound))

    def matches(self, version):
        version = ComparableVersion(version)

        if self.upper_bound is not None:
            if version > self.upper_bound:
                return False
            elif not self.upper_bound_inclusive and self.upper_bound == version:
                return False

        if self.lower_bound is not None:
            if version < self.lower_bound:
                return False
            elif not self.lower_bound_inclusive and self.lower_bound == version:
                return False

        return True

    def __repr__(self):
        return "{0}{1},{2}{3}".format(
            '[' if self.lower_bound_inclusive else '(',
            repr(self.lower_bound) if self.lower_bound else '',
            repr(self.upper_bound) if self.upper_bound else '',
            ']' if self.upper_bound_inclusive else ')',
        )

    def to_json(self):
        return {
            'lower_bound': {
                'version': str(self.lower_bound) if self.lower_bound else None,
                'inclusive': self.lower_bound_inclusive,
            },
            'upper_bound': {
                'version': str(self.upper_bound) if self.upper_bound else None,
                'inclusive': self.upper_bound_inclusive,
            }
        }


class Version(VersionRange):

    def __init__(self, version):
        self.version = ComparableVersion(version)

    @property
    def lower_bound(self):
        return self

    @property
    def upper_bound(self):
        return self

    def matches(self, version):
        return self.version == version

    def to_json(self):
        return {'raw_version': str(self.version)}


class DependencyParser(NodeVisitor):

    grammar = DEPENDENCY_GRAMMAR

    def __init__(self):
        self.deps = []

    def visit_rangedelimstart(self, node, children):
        return node.text

    def visit_rangedelimend(self, node, children):
        return node.text

    def visit_version(self, node, children):
        return ComparableVersion(node.text)

    def visit_versionrange(self, versionrange, children):
        leftdelim, middle, rightdelim = children

        lower_bound_inclusive = leftdelim == '['
        upper_bound_inclusive = rightdelim == ']'

        middle = middle[0]
        if len(middle) == 2:
            lower_bound = None
            upper_bound = middle[1]
        else:
            lower_bound = None if isinstance(middle[0], list) else middle[0]
            upper_bound = None if len(middle[2]) == 0 else middle[2][0]

        return VersionRange(lower_bound, lower_bound_inclusive, upper_bound, upper_bound_inclusive)

    def visit_versionranges(self, versionranges, children):
        firstvr, vrlist = children
        ranges = [firstvr]
        for comma, versionspecifier in vrlist:
            ranges.append(versionspecifier)

        # perform sanity check
        lower_bound = None
        upper_bound = None
        for range in ranges:
            if not lower_bound:
                lower_bound = range.lower_bound
            if upper_bound:
                if not range.lower_bound or range.lower_bound < upper_bound:
                    raise ValueError('Ranges overlap: {} < {}'.format(range.lower_bound, upper_bound))
            upper_bound = range.upper_bound

        return ranges

    def visit_instruction(self, node, children):
        return node.text

    def visit_versionspecifier(self, node, children):
        return children[0]

    def visit_pluginidver(self, node, children):
        pluginid, maybeversion = children
        if not maybeversion:
            return (pluginid, [VersionRange(None, True, None, True)])
        return (pluginid, maybeversion[0][1])

    def visit_target(self, node, children):
        if node.text == '*':
            return '*'
        return children[0]

    def visit_dependency(self, node, children):
        instruction, _, target = children
        return (instruction, target)

    def visit_dependencies(self, node, children):
        first_dep, deplist = children
        dependencies = [first_dep]
        for semicolon, odep in deplist:
            dependencies.append(odep)
        return dependencies

    def visit_(self, node, children):
        return children

    def visit_pluginid(self, node, pluginid):
        return node.text


def class_name_to_filesystem_name(class_name):
    return class_name.replace('.', '/') + '.class'


def filesystem_name_to_class_name(filesystem_name):
    if not filesystem_name.endswith('.class'):
        raise ValueError("{} doesn't end in .class".format(filesystem_name))

    return filesystem_name[:-len('.class')].replace('/', '.')


class SpongePoweredPlugin(object):

    DEPENDENCY_INSTRUCTIONS = {'required-before', 'required-after', 'before', 'after'}

    def __init__(self, classname, kvps):
        self.classname = classname
        self.data = {
            'id': None,
            'name': None,
            'version': None
        }
        self.data.update(kvps)
        self.dependencies = self.compute_dependencies()

    def validate(self):
        errors = []

        if not self.data['id']:
            errors.append('No "id" attribute set')

        if not self.data['name']:
            errors.append('No "name" attribute set')

        if not self.data['version']:
            errors.append('No "version" attribute set')

        try:
            self.compute_dependencies()
        except Exception as ex:
            errors.append(str(ex))

        return errors

    def compute_dependencies(self):
        # Forge dependencies take the following format:
        # `dependency`(;`dependency`)+
        # where `dependency` is
        # (required-)?(before|after):(*|`id`@`version`)
        if 'dependencies' in self.data:
            dep_list = DependencyParser().parse(self.data['dependencies'])
            deps = {}
            for dep_type, dep in dep_list:
                deps.setdefault(dep_type, []).append(dep)
            return deps
        else:
            return {}

    @property
    def json_dependencies(self):
        jdeps = {}
        for k, v in self.dependencies.items():
            jdeps[k] = []
            d = jdeps[k]

            for plugin_id, version_ranges in v:
                d.append((plugin_id, [version_range.to_json() for version_range in version_ranges]))
        return jdeps

    def __repr__(self):
        return "SpongePoweredPlugin(classname={0!r}, data={1!r}, dependencies={2!r})".format(self.classname, self.data, self.dependencies)


class Plugalyzer(object):

    def __init__(self, zf):
        self.zipfile = zf
        self._cache = {}

    def run(self):
        return list(self.find_plugin_classes())

    def find_plugin_classes(self):
        for filename in filter(lambda fn: fn.endswith('.class'), self.zipfile.namelist()):
            spp = self.is_spongepowered_plugin(filename)
            if spp:
                yield SpongePoweredPlugin(filesystem_name_to_class_name(filename), spp)

    def is_spongepowered_plugin(self, filename):
        cf = self.analyze_class_file(filename)
        rva = cf.attributes.find_one('RuntimeVisibleAnnotations')
        if not rva:
            return False

        plugin_annotations = [(a.type, a.key_value_pairs) for a in rva.annotations if a.type == 'Lorg/spongepowered/api/plugin/Plugin;']
        if not plugin_annotations:
            return False

        return plugin_annotations[0][1]

    def analyze_class_file(self, filename):
        if filename in self._cache:
            return self._cache[filename]

        with self.zipfile.open(filename, 'r') as cf_fp:
            cf = ClassFile(cf_fp)
            self._cache[filename] = cf
            return cf

    @classmethod
    def analyze(self, fp_or_filename):
        with ZipFile(fp_or_filename, 'r') as jf:
            return Plugalyzer(jf).run()


if __name__ == '__main__':
    import sys

    def usage():
        print("{} [JAR file path]".format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) != 2:
        usage()

    plugalyzer = Plugalyzer.analyze(sys.argv[1])
    print(sys.argv[1], plugalyzer)
