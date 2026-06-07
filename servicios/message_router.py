from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import wx

from globals import data_store
from globals.resources import rutasonidos
from setup import player, reader


@dataclass
class RoutableMessage:
    """Message to be routed through the standard pipeline.
    
    Attributes:
        text: Message content
        author: Author name (prepended to text if non-empty)
        category: Message category for routing (general, member, moderator, verified, donation, event)
        event_type: Specific event type for event category (chest, follow, join, like, share, etc.)
        platform: Source platform identifier
        is_past: Whether this is from a past stream (suppresses sound playback)
        eventos_index: Override for eventos/unread config index (used for events with non-standard indices)
        sound_index: Override for listasonidos/rutasonidos index (used for events with non-standard indices)
    """
    text: str
    author: str = ''
    category: str = 'general'
    event_type: Optional[str] = None
    platform: str = ''
    is_past: bool = False
    eventos_index: Optional[int] = None
    sound_index: Optional[int] = None


class MessageRouter:
    """Centralized message routing: config check → sound → reader → ListBox.
    
    Routes messages through a standard pipeline:
    1. Check config toggles (eventos, categorias)
    2. Play sound if enabled and not from past stream
    3. Read message via TTS if enabled
    4. Dispatch to appropriate ListBox via chat_controller
    
    All UI updates are wrapped in wx.CallAfter for thread safety.
    """
    
    # Category mapping: (eventos_idx, categorias_idx, listasonidos_idx, unread_idx, listbox_attr, sound_idx)
    CATEGORY_MAP = {
        'general':   (0, 0, 0, 0, 'list_box_general', 0),
        'member':    (1, 2, 1, 1, 'list_box_miembros', 1),
        'donation':  (3, 3, 3, 3, 'list_box_donaciones', 3),
        'moderator': (4, 4, 4, 4, 'list_box_moderadores', 4),
        'verified':  (5, 5, 5, 5, 'list_box_verificados', 5),
    }
    
    def __init__(self, chat_controller):
        """Initialize router with chat controller.
        
        Args:
            chat_controller: ChatController instance for dispatching messages
        """
        self.chat_controller = chat_controller
    
    def _get_ui(self):
        """Safely get UI reference — may not exist during shutdown."""
        return getattr(self.chat_controller, 'ui', None)
    
    def route(self, msg: RoutableMessage) -> None:
        """Route a message through config check → sound → reader → ListBox dispatch.
        
        All UI updates happen via wx.CallAfter for thread safety.
        
        Args:
            msg: RoutableMessage to process
        """
        config = data_store.config
        cat_info = self.CATEGORY_MAP.get(msg.category)
        
        # For event category, use list_box_eventos with default indices
        if msg.category == 'event':
            eventos_idx = msg.eventos_index if msg.eventos_index is not None else 7
            categorias_idx = 1  # Events always use categorias[1]
            listasonidos_idx = msg.sound_index if msg.sound_index is not None else 9
            unread_idx = msg.eventos_index if msg.eventos_index is not None else 7
            listbox_attr = 'list_box_eventos'
            sound_idx = msg.sound_index if msg.sound_index is not None else 9
        elif cat_info is not None:
            eventos_idx, categorias_idx, listasonidos_idx, unread_idx, listbox_attr, sound_idx = cat_info
        else:
            return
        
        ui = self._get_ui()
        if ui is None:
            return
        
        listbox = getattr(ui, listbox_attr, None)
        if listbox is None:
            return
        
        # Config checks
        if not config['eventos'][eventos_idx]:
            return
        if not config['categorias'][categorias_idx]:
            return
        
        full_text = f"{msg.author}: {msg.text}" if msg.author else msg.text
        
        # Build the display function to run via wx.CallAfter
        def _do_route():
            nonlocal full_text
            # Guard: UI may have been destroyed since route() was called
            ui = self._get_ui()
            if ui is None:
                return
            listbox = getattr(ui, listbox_attr, None)
            if listbox is None:
                return
            # Guard: C++ object may have been deleted before CallAfter executed
            try:
                # Dispatch to the correct ListBox via chat_controller
                if msg.category == 'event':
                    self.chat_controller.agregar_mensaje_evento(full_text, msg.event_type or '')
                elif msg.category == 'general':
                    self.chat_controller.agregar_mensaje_general(full_text)
                elif msg.category == 'member':
                    self.chat_controller.agregar_mensaje_miembro(full_text)
                elif msg.category == 'moderator':
                    self.chat_controller.agregar_mensaje_moderador(full_text)
                elif msg.category == 'verified':
                    self.chat_controller.agregar_mensaje_verificado(full_text)
                elif msg.category == 'donation':
                    self.chat_controller.agregar_mensaje_donacion(full_text)
                
                # Sound
                if config['sonidos'] and config['listasonidos'][listasonidos_idx] and not msg.is_past:
                    player.play(rutasonidos[sound_idx])
                
                # TTS read
                if config['reader'] and config['unread'][unread_idx]:
                    reader.leer_mensaje(full_text)
            except RuntimeError:
                pass  # wx object was deleted before we could use it
        
        wx.CallAfter(_do_route)
