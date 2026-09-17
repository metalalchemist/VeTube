"""Release notes dialog with formatted HTML display."""

import logging
import re

import wx
import wx.html2

from globals.data_store import config

logger = logging.getLogger(__name__)


def _markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML with basic formatting.

    This is a simple converter that handles common markdown patterns.
    For more advanced features, consider using the 'markdown' library.

    Args:
        markdown_text: Markdown-formatted text.

    Returns:
        HTML-formatted string.
    """
    if not markdown_text:
        return ""

    html = markdown_text

    # Escape HTML special characters first (but preserve markdown)
    html = html.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")

    # Headers
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Links
    html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)

    # Unordered lists
    html = re.sub(r"^\* (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", html, flags=re.DOTALL)

    # Line breaks
    html = html.replace("\n\n", "</p><p>")
    html = f"<p>{html}</p>"

    # Clean up empty paragraphs
    html = html.replace("<p></p>", "")

    return html


def _get_styled_html(title: str, content_html: str) -> str:
    """Wrap HTML content in a styled page.

    Args:
        title: Page title.
        content_html: HTML content to display.

    Returns:
        Complete HTML page with styling.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            margin: 20px;
            background-color: #ffffff;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 24px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #34495e;
            font-size: 20px;
            margin-top: 20px;
        }}
        h3 {{
            color: #7f8c8d;
            font-size: 16px;
            margin-top: 15px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        li {{
            margin: 5px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
        em {{
            color: #7f8c8d;
        }}
        p {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {content_html}
</body>
</html>"""


class ReleaseNotesDialog(wx.Dialog):
    """Dialog to display formatted release notes."""

    def __init__(self, parent, version: str, release_notes: str):
        """Initialize the release notes dialog.

        Args:
            parent: Parent window.
            version: Version string to display.
            release_notes: Release notes in markdown format.
        """
        super().__init__(
            parent,
            title=_("Novedades - v%s") % version,
            size=(650, 550),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.version = version
        self.release_notes = release_notes
        self.user_accepted = False

        self._init_ui()
        self._load_content()
        self.Center()

    def _init_ui(self):
        """Initialize the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # WebView for release notes
        self.webview = wx.html2.WebView.New(self)
        main_sizer.Add(self.webview, 1, wx.EXPAND | wx.ALL, 10)

        # Backup status panel
        backup_sizer = wx.BoxSizer(wx.HORIZONTAL)
        create_backup = config.get("create_backup_before_update", True)

        if create_backup:
            backup_text = _("✓ Se creará una copia de seguridad antes de actualizar")
            backup_color = wx.Colour(39, 174, 96)  # Green
        else:
            backup_text = _(
                "⚠ No se creará ninguna copia de seguridad. Si la actualización falla, no podrás volver atrás."
            )
            backup_color = wx.Colour(231, 76, 60)  # Red

        backup_label = wx.StaticText(self, label=backup_text)
        backup_label.SetForegroundColour(backup_color)
        backup_sizer.Add(backup_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)

        # Link to settings
        settings_link = wx.adv.HyperlinkCtrl(
            self, wx.ID_ANY, _("Cambiar los ajustes"), "", style=wx.adv.HL_ALIGN_RIGHT
        )
        settings_link.SetNormalColour(wx.Colour(52, 152, 219))
        settings_link.SetHoverColour(wx.Colour(41, 128, 185))
        settings_link.Bind(wx.adv.EVT_HYPERLINK, self._on_open_settings)
        backup_sizer.Add(settings_link, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        main_sizer.Add(backup_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Button sizer
        button_sizer = wx.StdDialogButtonSizer()

        # Update button
        self.btn_update = wx.Button(self, wx.ID_OK, _("&Actualizar ahora"))
        self.btn_update.SetDefault()
        button_sizer.AddButton(self.btn_update)

        # Cancel button
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, _("Más &tarde"))
        button_sizer.AddButton(self.btn_cancel)

        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.SetSizer(main_sizer)

        # Bind events
        self.btn_update.Bind(wx.EVT_BUTTON, self._on_update)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)

        # Handle link clicks in WebView
        self.Bind(
            wx.html2.EVT_WEBVIEW_NAVIGATING, self._on_webview_navigating, self.webview
        )

    def _load_content(self):
        """Load the release notes content into the WebView."""
        try:
            # Convert markdown to HTML
            content_html = _markdown_to_html(self.release_notes)

            # Wrap in styled page
            title = _("Novedades de la versión %s") % self.version
            full_html = _get_styled_html(title, content_html)

            # Load into WebView
            self.webview.SetPage(full_html, "")

        except Exception:
            logger.exception("Failed to load release notes")
            # Fallback to plain text
            # La cadena sale de la f-string a propósito: los extractores de
            # gettext no siempre ven un _() metido dentro de un campo de
            # sustitución, y la entrada desaparecería del .pot en la próxima
            # regeneración sin que nadie se diera cuenta.
            aviso = _(
                "No se han podido interpretar las novedades. Se muestra el texto tal cual:"
            )
            fallback_html = _get_styled_html(
                _("Error al cargar las novedades"),
                f"<p>{aviso}</p><pre>{self.release_notes}</pre>",
            )
            self.webview.SetPage(fallback_html, "")

    def _on_update(self, event):
        """Handle update button click."""
        self.user_accepted = True
        self.EndModal(wx.ID_OK)

    def _on_cancel(self, event):
        """Handle cancel button click."""
        self.user_accepted = False
        self.EndModal(wx.ID_CANCEL)

    def _on_open_settings(self, event):
        """Open settings dialog to change backup configuration."""
        from ui.ajustes import configuracionDialog

        # Close this dialog temporarily
        self.Hide()

        # Open settings dialog
        settings_dlg = configuracionDialog(self.GetParent())
        settings_dlg.ShowModal()
        settings_dlg.Destroy()

        # Show this dialog again
        self.Show()
        self.Raise()
        self.SetFocus()

    def _on_webview_navigating(self, event):
        """Handle link clicks in WebView - open external links in browser."""
        url = event.GetURL()

        # Allow internal navigation (empty URLs, about:blank, etc.)
        if not url or url.startswith("about:") or url.startswith("data:"):
            return

        # Open external links in default browser
        if url.startswith("http://") or url.startswith("https://"):
            wx.LaunchDefaultBrowser(url)
            event.Veto()  # Don't navigate in the WebView

    def get_user_choice(self) -> bool:
        """Get the user's choice.

        Returns:
            True if user clicked "Update Now", False otherwise.
        """
        return self.user_accepted


def show_release_notes_dialog(parent, version: str, release_notes: str) -> bool:
    """Show the release notes dialog and return user's choice.

    Args:
        parent: Parent window.
        version: Version string.
        release_notes: Release notes in markdown format.

    Returns:
        True if user wants to update, False otherwise.
    """
    dialog = ReleaseNotesDialog(parent, version, release_notes)
    result = dialog.ShowModal()
    user_wants_update = dialog.get_user_choice()
    dialog.Destroy()

    return result == wx.ID_OK and user_wants_update
