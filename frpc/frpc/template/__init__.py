
"""File template utility functions."""


import pkg_resources


def load_template(name: str, **kwargs) -> str:
    """Load a template with format keywords replaced to those in **kwargs.

    Arguments:
        name (:obj:`str`): Template path.
    """
    tpl = pkg_resources.resource_string(__name__, name).decode()

    for key, value in kwargs.items():
        tpl = tpl.replace("# {{{{{{{}}}}}}}".format(key), value)

    return tpl


def make_from_template(tpl_name: str, out_path: str, **kwargs) -> None:
    """Create a file from template based on `load_template()`.

    Arguments:
        tpl_name (:obj:`str`): Template path.
        out_path (:obj:`str`): Output file path.
    """
    with open(out_path, "w") as out_file:
        out_file.write(load_template(tpl_name, **kwargs))


def list_templates(tpl_dir: str = ""):
    """List available templates in `tpl_dir`."""
    templates = [
            name
            for name in pkg_resources.resource_listdir(__name__, tpl_dir)
            if not name.startswith(".") and not name.startswith("__") and
            not name.endswith(".py") and not name.endswith(".pyc")
            ]

    return templates
