import pkgutil
import warnings
from typing import Any, List, Set

# Suppress warnings, since these are depreciation warnings when importing a submodule
warnings.filterwarnings("ignore")

ANNOTATIONS = "__annotations__"
UNDERSCORE = "_"
word_set: Set[str] = set()
name_set: Set[str] = set()  # used to see if we already iterated over something with that name
dict_set: Set[str] = set()

add_to_word_set = word_set.add
add_to_name_set = name_set.add
add_to_dict_set = dict_set.add


for dictionary in ["en_US.txt", "python.txt", "technical.txt"]:
    with open(dictionary) as f:
        for line in f.readlines():
            add_to_dict_set(line.lower().strip())


def add_words(name: str) -> None:
    add_to_name_set(name)
    words = name.split(UNDERSCORE)
    for word in words:
        word = word.lower()
        if word not in dict_set:
            add_to_word_set(word)


def is_private(attr_name: str) -> bool:
    return attr_name.startswith(UNDERSCORE)


def _get_annotations(attr: str) -> None:
    if attr is not None and hasattr(attr, ANNOTATIONS):
        argument_dict = getattr(attr, ANNOTATIONS)
        # some objects that aren't functions implement __annotations__
        if not isinstance(argument_dict, dict):
            return
        for key in argument_dict.keys():
            if is_private(key) or key == "return":
                return
            add_words(key)


def _get_sub_attrs(attr: str) -> None:
    _get_annotations(attr)
    for sub_attr_name in dir(attr):
        if is_private(sub_attr_name) or sub_attr_name in name_set:
            continue
        if not hasattr(attr, sub_attr_name):
            continue
        add_words(sub_attr_name)
        sub_attr = getattr(attr, sub_attr_name)
        _get_sub_attrs(sub_attr)


def get_word_set(mod: Any) -> None:
    add_words(mod.__name__)
    # it doesn't get all result if you call _get_sub_attrs on mod!?
    for part in dir(mod):
        if is_private(part):
            continue
        add_words(part)
        cls = getattr(mod, part)
        _get_sub_attrs(cls)


def word_set_for_submodule(sub_mod_name: str) -> None:
    # Prevent that tests get loaded
    if "test" in sub_mod_name:
        return
    try:
        sub_mod = __import__(sub_mod_name)
        get_word_set(sub_mod)
    # Don't care for imports and backends that aren't available
    except ImportError:
        return
    # This could be problematic, investigare the error further
    except RuntimeError:
        return


def write_word_file(mod_name: str, filename: str, abbreviations: List[str] = None) -> None:
    mod = __import__(mod_name)

    if abbreviations is not None:
        for abbreviation in abbreviations:
            add_words(abbreviation)

    get_word_set(mod)

    try:
        for importer, sub_mod_name, ispkg in pkgutil.walk_packages(
            path=mod.__path__, prefix=mod.__name__ + ".", onerror=lambda x: None
        ):
            word_set_for_submodule(sub_mod_name)
    # Some modules don't have a __path__ attribute
    except AttributeError:
        print(f"{mod.__name__} has no __path__ attribute. Can't find submodules!")

    if "" in word_set:
        word_set.remove("")

    words = "\n".join(sorted(word_set))
    with open(filename, "w") as f:
        f.write(words)


if __name__ == "__main__":
    mod_name = "matplotlib"
    filename = ".".join([mod_name, "txt"])
    abbreviations = ["pd"]  # common abbrevations used in this package
    write_word_file(mod_name, filename, abbreviations)
