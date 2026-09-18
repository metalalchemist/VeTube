"""Startup donation dialog."""

import wx


def donation() -> None:
    """Show donation dialog."""
    dlg = wx.MessageDialog(
        None,
        _(
            "Con tu apoyo contribuyes a que este programa siga siendo gratuito. ¿Te unes a nuestra causa?"
        ),
        _("Atención:"),
        wx.YES_NO | wx.ICON_ASTERISK,
    )
    dlg.SetYesNoLabels(_("&Aceptar"), _("&Cancelar"))
    if dlg.ShowModal() == wx.ID_YES:
        wx.LaunchDefaultBrowser(
            "https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U"
        )
