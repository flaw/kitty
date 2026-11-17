Mappable actions
-----------------------

.. highlight:: conf

The actions described below can be mapped to any key press or mouse action
using the ``map`` and ``mouse_map`` directives in :file:`kitty.conf`. For
configuration examples, see the default shortcut links for each action.
To read about keyboard mapping in more detail, see :doc:`mapping`.

You can also browse and trigger these actions by pressing :sc:`command_palette`
to run the :doc:`/kittens/command-palette`.

.. _in_window_toasts:

In-window status messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :ac:`show_toast` action to display a short message in the top-right
corner of the current kitty OS window::

    map f8 show_toast Hello from kitty

Toasts are rendered inside the existing window, above panes and floating
terminals. They do not create an OS window or terminal process, take focus,
change layouts, or intercept mouse input. Messages use the configured foreground
and background with an active-border accent. A new message replaces the old one
and restarts its two-second expiry. Toasts use the same terminal-cell renderer,
font family, font size, shaping and fallback fonts as panes, with a square outline
matching :opt:`window_border_width`. Long messages are truncated to fit and
control characters are removed.

A successful :ac:`save_as_session` displays ``Session saved`` only after the file
has been written. A failed write shows an error toast as well as a detailed
error panel. Manual :ac:`load_config_file` displays ``Configuration reloaded``;
config errors instead display ``Configuration has errors`` without replacing
the existing detailed config-error UI. Error toasts last four seconds and use
the bell-border color for their outline, but do not ring the bell.

Automatic config reloads (including the SIGUSR1 reload path) do not show success
toasts, but still report config errors. Bells and desktop notifications are
unchanged; toasts do not use macOS Notification Center or other desktop
notification services.

.. include:: /generated/actions.rst
