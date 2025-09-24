from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6 import QtWidgets
from pedit.core.theme import color_theme

class MainMenu:
    """
    Build a QMenuBar from a declarative spec.

    Spec format:
    menu_spec = [
        {
            "title": "File",
            "items": [
                {"text": "Open", "shortcut": "Ctrl+O", "triggered": "on_open"},
                {"text": "Save", "shortcut": "Ctrl+S", "triggered": "on_save"},
                {"separator": True},
                {"text": "Exit", "shortcut": "Ctrl+Q", "triggered": "close"}
            ]
        },
        {
            "title": "Edit",
            "items": [
                {"text": "Undo", "shortcut": "Ctrl+Z", "triggered": "on_undo"},
                {"text": "Redo", "shortcut": "Ctrl+Y", "triggered": "on_redo"},
            ]
        },
        {
            "title": "Help",
            "items": [
                {"text": "About", "triggered": "on_about"},
                {
                    "text": "More",
                    "submenu": [
                        {"text": "Docs", "triggered": "on_docs"},
                        {"text": "Check for Updates", "triggered": "on_check_updates"},
                    ],
                },
            ]
        }
    ]
    """

    @staticmethod
    def create_menu(main_window, menu_spec, stylesheet: str = None):
        """
        Creates the menu bar on main_window using menu_spec.
        Returns (menu_bar, registry) where registry maps 'Menu/Item' to QAction/QMenu.
        """
        menu_bar = main_window.menuBar()
        registry = {}  # e.g. {"File": QMenu, "File/Open": QAction, ...}

        def _connect_trigger(action: QAction, target):
            """
            target can be:
              - callable
              - str: name of a method on main_window (e.g., "on_open" or "close")
            """
            if target is None:
                return
            if callable(target):
                action.triggered.connect(target)
            elif isinstance(target, str):
                slot = getattr(main_window, target, None)
                if callable(slot):
                    action.triggered.connect(slot)
                else:
                    # No-op if method not found; you can raise if you prefer
                    pass

        def _apply_action_props(action: QAction, spec: dict):
            if spec.get("shortcut"):
                action.setShortcut(QKeySequence(spec["shortcut"]))
                action.setShortcutVisibleInContextMenu(True)
            if "checkable" in spec:
                action.setCheckable(bool(spec["checkable"]))
            if "checked" in spec:
                action.setChecked(bool(spec["checked"]))
            if "enabled" in spec:
                action.setEnabled(bool(spec["enabled"]))
            if "visible" in spec:
                action.setVisible(bool(spec["visible"]))
            if spec.get("statusTip"):
                action.setStatusTip(spec["statusTip"])
            if spec.get("whatsThis"):
                action.setWhatsThis(spec["whatsThis"])
            if spec.get("icon"):
                action.setIcon(QIcon(spec["icon"]))
            if spec.get("objectName"):
                action.setObjectName(spec["objectName"])
            if "data" in spec:
                action.setData(spec["data"])
            _connect_trigger(action, spec.get("triggered"))

        def _build_menu(parent_menu, title: str, items: list, prefix_path: str):
            menu = parent_menu.addMenu(title) if isinstance(parent_menu, QtWidgets.QMenuBar) else QMenu(title, parent_menu)
            full_path = title if not prefix_path else f"{prefix_path}/{title}"
            registry[full_path] = menu

            for it in items or []:
                if it.get("separator"):
                    menu.addSeparator()
                    continue

                if "submenu" in it:
                    sub_title = it.get("text", "Submenu")
                    sub_items = it.get("submenu", [])
                    sub_menu = menu.addMenu(sub_title)
                    registry[f"{full_path}/{sub_title}"] = sub_menu
                    # Recurse into submenu items
                    for sub_it in sub_items:
                        if sub_it.get("separator"):
                            sub_menu.addSeparator()
                            continue
                        if "submenu" in sub_it:
                            # Nested submenu
                            nested_title = sub_it.get("text", "Submenu")
                            nested_items = sub_it.get("submenu", [])
                            _build_menu(sub_menu, nested_title, nested_items, full_path)
                            continue
                        # Regular action in submenu
                        act = QAction(sub_it.get("text", "Unnamed"), menu)
                        _apply_action_props(act, sub_it)
                        sub_menu.addAction(act)
                        registry[f"{full_path}/{sub_title}/{act.text()}"] = act
                    continue

                # Regular action
                text = it.get("text", "Unnamed")
                act = QAction(text, menu)
                _apply_action_props(act, it)
                menu.addAction(act)
                registry[f"{full_path}/{text}"] = act

            return menu

        # Build top-level menus
        for top in menu_spec:
            title = top.get("title", "Menu")
            items = top.get("items", [])
            _build_menu(menu_bar, title, items, prefix_path="")

        # Apply stylesheet if provided (or keep yours)
        if stylesheet:
            menu_bar.setStyleSheet(stylesheet)

        return menu_bar, registry

# In your main window code:

MENU_SPEC = [
    {
        "title": "File",
        "items": [
            {"text": "Open", "shortcut": "Ctrl+O", "triggered": "on_open"},
            {"text": "Save", "shortcut": "Ctrl+S", "triggered": "on_save"},
            {"separator": True},
            {"text": "Exit", "shortcut": "Ctrl+Q", "triggered": "close"},
        ],
    },
    {
        "title": "Edit",
        "items": [
            {"text": "Undo", "shortcut": "Ctrl+Z", "triggered": "on_undo"},
            {"text": "Redo", "shortcut": "Ctrl+Y", "triggered": "on_redo"},
        ],
    },
    {
        "title": "Help",
        "items": [
            {"text": "About", "triggered": "on_about"},
            {
                "text": "More",
                "submenu": [
                    {"text": "Docs", "triggered": "on_docs"},
                    {"text": "Check for Updates", "triggered": "on_check_updates"},
                ],
            },
        ],
    },
]

MENU_STYLESHEET = f"""
        QMenuBar {{
            spacing: 1px;
            padding: 1px 1px;
            background-color: {color_theme.COLOR_BACKGROUND};
            color: {color_theme.COLOR_TEXT_PRIMARY};
            border-bottom: 1px solid {color_theme.COLOR_BORDER};
        }}
        QMenuBar::item {{
            spacing: 5px;
            padding: 4px 10px;
            background: transparent;
            color: {color_theme.COLOR_TEXT_PRIMARY};
        }}
        QMenuBar::item:selected {{ 
            background: {color_theme.COLOR_SURFACE_LIGHT}; 
            color: {color_theme.COLOR_TEXT_PRIMARY}; 
        }}
        QMenuBar::item:pressed  {{ 
            background: {color_theme.COLOR_PRIMARY}; 
            color: {color_theme.COLOR_TEXT_PRIMARY}; 
        }}

        QMenu {{
            background-color: {color_theme.COLOR_SURFACE};
            border: 1px solid {color_theme.COLOR_BORDER};
            color: {color_theme.COLOR_TEXT_PRIMARY};
        }}
        QMenu::item {{
            padding: 4px 20px;
            background: transparent;
            color: {color_theme.COLOR_TEXT_PRIMARY};
        }}
        QMenu::item:selected {{ 
            background: {color_theme.COLOR_PRIMARY}; 
            color: {color_theme.COLOR_TEXT_PRIMARY}; 
        }}
        /* Note: QSS can't separately style shortcut vs label */
    """
