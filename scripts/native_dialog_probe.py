"""Optional AT-SPI helper for Finanse's own dialogs. Requires system PyGObject."""

import sys
import time

import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402


def walk(node, depth=0):
    yield node
    if depth >= 14 or node.get_role_name() == "document web":
        return
    for index in range(node.get_child_count()):
        child = node.get_child_at_index(index)
        if child:
            yield from walk(child, depth + 1)


def nodes():
    desktop = Atspi.get_desktop(0)
    for index in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(index)
        name = (app.get_name() or "").casefold()
        if "finanse" in name:
            yield from walk(app)
        elif "portal" in name:
            for index in range(app.get_child_count()):
                window = app.get_child_at_index(index)
                if window and "Finanse" in (window.get_name() or ""):
                    yield from walk(window)


def showing(node):
    return node.get_state_set().contains(Atspi.StateType.SHOWING)


def find(predicate):
    for _ in range(40):
        for node in nodes():
            if showing(node) and predicate(node):
                return node
        time.sleep(0.1)
    raise RuntimeError("Native Finanse control not found")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "save":
        field = find(lambda n: n.get_role_name() == "text")
        field.get_editable_text_iface().set_text_contents(sys.argv[2])
        find(
            lambda n: n.get_role_name() == "button"
            and n.get_name() in ("Save", "Salvar")
        ).get_action_iface().do_action(0)
        print("PASS: native Save dialog selected a temporary backup file")
    elif mode == "cancel":
        find(
            lambda n: n.get_role_name() == "button"
            and n.get_name() in ("Cancel", "Cancelar")
        ).get_action_iface().do_action(0)
        print("PASS: native dialog cancellation")
    elif mode == "open":
        field = find(lambda n: n.get_name() == "native-backup.sqlite3")
        cell = field
        while cell.get_parent().get_role_name() != "table":
            cell = cell.get_parent()
        table = cell.get_parent().get_table_iface()
        row = table.get_row_at_index(cell.get_index_in_parent())
        assert table.add_row_selection(row)
        find(
            lambda n: n.get_role_name() == "button"
            and n.get_name() in ("Open", "Abrir")
        ).get_action_iface().do_action(0)
    elif mode == "confirm":
        try:
            find(
                lambda n: n.get_role_name() == "button"
                and n.get_name() in ("Substituir", "OK")
            ).get_action_iface().do_action(0)
        except RuntimeError:
            print(
                [
                    (n.get_role_name(), n.get_name())
                    for n in nodes()
                    if showing(n)
                    and n.get_role_name() in ("dialog", "file chooser", "button")
                ]
            )
            raise
        print("PASS: native restore confirmation")
    elif mode == "inspect":
        time.sleep(1)
        # Only UI control names; do not serialize file listings.
        for node in nodes():
            if showing(node) and node.get_role_name() in (
                "button",
                "toggle button",
                "text",
                "file chooser",
            ):
                print(node.get_role_name(), repr(node.get_name()))
