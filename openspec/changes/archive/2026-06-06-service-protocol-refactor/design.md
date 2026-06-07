# Design: Chat Service Protocol & Message Router Refactor

## Technical Approach

Two-phase incremental refactor. **Phase 1** adds a `typing.Protocol` type and annotates the 5 service classes — zero runtime change, pure type safety. **Phase 2** extracts the duplicated message-routing pipeline (config → sound → reader → ListBox) into a shared `MessageRouter`, refactoring one service at a time, and wrapping the YouTube/Twitch/Sala/`YouTubeRealDataTime` UI calls in `wx.CallAfter` as each service is touched.

## Architecture Decisions

### Decision: Protocol vs ABC
**Choice**: `typing.Protocol` (structural subtyping). **Alternative**: `abc.ABC` (nominal, forces explicit inheritance). **Rationale**: TikTok, Kick, YT, Twitch, Sala already share shape organically; Protocol accepts them as-is without altering their (already-divergent) class hierarchies or threading models. Same `ty` checking, zero coupling.

### Decision: MessageRouter as injected class
**Choice**: `MessageRouter(chat_controller, player, reader, config_provider)` with dependencies at init. **Alternative**: Module-level functions reading `data_store` directly. **Rationale**: Per-service testability — unit tests can pass a mock chat_controller/player/reader. Also unblocks future config-injection refactor.

### Decision: Single `RoutableMessage` dataclass
**Choice**: One dataclass with `text`, `author`, `category`, `event_type`, `platform`, `is_past`, `event_index`. **Alternative**: Union of platform-specific message types. **Rationale**: The routing logic is identical across platforms — only the *classification* differs. A single shape keeps the router signature trivial and avoids type-explosion.

### Decision: Router wraps UI calls in `wx.CallAfter` internally
**Choice**: Router invokes `wx.CallAfter(player.play, ...)`, `wx.CallAfter(reader.leer_mensaje, ...)`, `wx.CallAfter(chat_controller.agregar_mensaje_*, ...)`. **Alternative**: Require callers to wrap before invoking. **Rationale**: YouTube/Twitch/Sala/YouTubeRealDataTime all run routing inside a background thread. Forcing every service to remember the wrap is exactly the bug we are fixing. Centralizing thread-safety in the router eliminates the entire class of bug.

### Decision: Phase order (Protocol → Router)
**Choice**: Two separate PRs. **Alternative**: Single PR. **Rationale**: Phase 1 is a no-op at runtime (revertable trivially), gives reviewers a checkpoint, and lets `ty` validate the protocol surface before refactoring logic on top of it.

## Data Flow (Phase 2)

```
Platform lib → service callback
   ├─ build RoutableMessage (text, author, category, event_type, is_past)
   └─ router.route(msg)
        ├─ category → (eventos_idx, categorias_idx, listasonidos_idx, unread_idx)
        ├─ eventos[i] AND categorias[i] AND ui-has-listbox  → else: drop
        ├─ sonidos AND listasonidos[i] AND not is_past       → wx.CallAfter(player.play)
        ├─ reader AND unread[i]                             → wx.CallAfter(reader.leer_mensaje)
        └─ wx.CallAfter(chat_controller.agregar_mensaje_<category>)
```

## File Changes

| File | Action | Phase | Description |
|---|---|---|---|
| `servicios/chat_service_protocol.py` | Create | 1 | ~25-line `ChatService(Protocol)` |
| `servicios/tiktok.py` | Modify | 1+2 | Annotate `: ChatService`; build `RoutableMessage` in each `on_*`; replace inline blocks with `router.route(msg)` |
| `servicios/kick.py` | Modify | 1+2 | Same |
| `servicios/youtube.py` | Modify | 1+2 | Same + wrap remaining `player.play` in `wx.CallAfter` |
| `servicios/twich.py` | Modify | 1+2 | Same + wrap all `player.play`/`reader.leer_mensaje`/ListBox calls in `wx.CallAfter` |
| `servicios/sala.py` | Modify | 1+2 | Same + wrap calls (Timer runs off-main-thread) |
| `servicios/YouTubeRealDataTime.py` | Modify | 1+2 | Same + wrap `player.play` calls |
| `servicios/message_router.py` | Create | 2 | `RoutableMessage` dataclass + `MessageRouter` class + `CATEGORY_INDICES` map |
| `controller/main_controller.py` | Modify | 1 | Type `servicio: ChatService` after the if/elif chain |
| `controller/menus/chat_menu_controller.py` | Modify | 1 | Replace `servicio.chat.status` with `getattr(servicio, 'status', None)` |

## Interfaces / Contracts

```python
# Phase 1
class ChatService(Protocol):
    url: str
    chat_controller: 'ChatController'
    estadisticas_manager: 'EstadisticasManager'
    media_controller: Optional['MediaController']
    def iniciar_chat(self) -> None: ...
    def detener(self) -> None: ...

# Phase 2
@dataclass
class RoutableMessage:
    text: str
    author: str
    category: str        # 'general'|'miembro'|'moderador'|'verificado'|'donacion'|'evento'
    event_type: Optional[str] = None   # 'chest'|'follow'|'join'|'like'|'share'|'subscribe'|...
    platform: str = ''
    is_past: bool = False
    event_index: int = 0  # fallback for events

class MessageRouter:
    def __init__(self, chat_controller, player, reader, config_provider): ...
    def route(self, msg: RoutableMessage) -> None: ...
```

Router uses `CATEGORY_INDICES = {'general':0,'miembro':1,'donacion':3,'moderador':4,'verificado':5}` to map category → `data_store.config['eventos'|'categorias'|'listasonidos'|'unread']` indices. For `'evento'` category, uses `msg.eventos_index` instead. For `moderador`, plays `rutasonidos[4]` (or `[7]` for propietario — router gets a `sound_index` override field). For 'past' streams, skip sound.

## Testing Strategy

| Layer | What | How |
|---|---|---|
| Phase 1 | Type conformance | `ty check` over all service files |
| Phase 2 | Routing output parity | Per-service side-by-side: capture pre-refactor `RoutableMessage` traces, run new router, assert identical dispatch |
| Phase 2 | Thread safety | Manual live test on YT past/live + Twitch sub/cheer; verify no `wx._core.PyAssertionError` |
| Regression | Existing suite | All 24 `EstadisticasManager` tests + manual smoke per platform |

## Migration / Rollout

No data migration. Two-PR phased rollout: PR-1 lands Protocol + annotations + chat_menu_controller fix (zero behavior change). PR-2 lands `MessageRouter` + service refactors + `wx.CallAfter` fixes (one service per commit for bisect-ability).

## Open Questions

None. Exploration mapped all 5 services, 3 listbox-dispatch methods, 4 `agregar_mensaje_evento` call sites, and the `chat.status` assumption surface.
