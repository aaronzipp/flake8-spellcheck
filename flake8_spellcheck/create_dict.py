import pkgutil

ANNOTATIONS = "__annotations__"
UNDERSCORE = "_"
word_set = set()
name_set = set() # used to see if we already iterated over something with that name
dict_set = set()

add_to_word_set = word_set.add
add_to_name_set = name_set.add
add_to_dict_set = dict_set.add


for dictionary in ["en_US.txt", "python.txt", "technical.txt"]:
    with open(dictionary, "r") as f:
        for line in f.readlines():
            add_to_dict_set(line.lower())

def add_words(name):
    add_to_name_set(name)
    words = name.split(UNDERSCORE)
    for word in words:
        word = word.lower()
        if word not in dict_set:
            add_to_word_set(word)

def is_private(attr_name):
    return attr_name.startswith(UNDERSCORE)

def _get_annotations(attr):
    if attr is not None and hasattr(attr, ANNOTATIONS):
        argument_dict = getattr(attr, ANNOTATIONS)
        # some objects that aren't functions implement __annotations__
        if not isinstance(argument_dict, dict):
            return
        for key in argument_dict.keys():
            if is_private(key) or key == "return":
                return
            add_words(key)

def _get_sub_attrs(attr):
    _get_annotations(attr)
    for sub_attr_name in dir(attr):
        if is_private(sub_attr_name) or sub_attr_name in name_set:
            continue
        if not hasattr(attr, sub_attr_name):
            continue
        add_words(sub_attr_name)
        sub_attr = getattr(attr, sub_attr_name)
        _get_sub_attrs(sub_attr)


def get_word_set(mod):
    add_words(mod.__name__)
    # it doesn't get all result if you call _get_sub_attrs on mod!?
    for part in dir(mod):
        if is_private(part):
            continue
        add_words(part)
        cls = getattr(mod, part)
        _get_sub_attrs(cls)


def write_word_file(mod_name, filename, abbreviations=None):
    mod = __import__(mod_name)

    if abbreviations is not None:
        for abbreviation in abbreviations:
            add_words(abbreviation)

    get_word_set(mod)

    for importer, sub_mod_name, ispkg in pkgutil.walk_packages(
        path=mod.__path__,
        prefix=mod.__name__ + '.',
        onerror=lambda x: None
    ):
        try:
            # Prevent that tests get loaded
            if "test" in sub_mod_name:
                continue
            sub_mod = __import__(sub_mod_name)
            get_word_set(sub_mod)
        # Don't care for imports and backends that aren't available
        except ImportError:
            continue
        except RuntimeError:
            continue

    if "" in word_set:
        word_set.remove("")

    words = "\n".join(sorted(word_set))
    with open(filename, "w") as f:
        f.write(words)

mod_name = "pandas"
filename = ".".join([mod_name, "txt"])
abbreviations = ["pd"]
write_word_file(mod_name, filename, abbreviations)
