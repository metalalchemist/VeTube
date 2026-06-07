# Service Contract Specification

## Purpose

Formal interface contract and shared message routing for the five VeTube chat platform services (TikTok, Kick, YouTube, Twitch, Sala). Eliminates duplicated routing logic and establishes thread-safety guarantees.

## Requirements

### Requirement: ChatService Protocol

The system MUST define a `ChatService` protocol in `servicios/chat_service_protocol.py`. Every platform service (ServicioTiktok, ServicioKick, ServicioYouTube, ServicioTwich, ServicioSala) MUST conform to this protocol.

The protocol MUST declare: `url: str`, `iniciar_chat()`, `detener()`, `estadisticas_manager`, `chat_controller`, `media_controller`. It MAY declare optional members: `is_live()`, `enviar_mensaje()`.

#### Scenario: Protocol defined and type-checked

- GIVEN `servicios/chat_service_protocol.py` exists with the protocol definition
- WHEN `ty check` runs on all service files
- THEN no type errors related to ChatService conformance are reported

#### Scenario: All five services conform

- GIVEN each service file imports ChatService
- WHEN each service class is checked against the protocol
- THEN ServicioTiktok, ServicioKick, ServicioYouTube, ServicioTwich, and ServicioSala all satisfy the protocol

### Requirement: MessageRouter

The system SHOULD extract message routing into a shared `MessageRouter` class in `servicios/message_router.py`.

The router MUST check `data_store.config` toggles (`eventos`, `categorias`, `sonidos`, `reader`, `unread`), play sounds via `player.play`, read messages via `reader.leer_mensaje`, and dispatch to the correct ListBox method (`agregar_mensaje_general`, `agregar_mensaje_miembro`, `agregar_mensaje_moderador`, `agregar_mensaje_donacion`, `agregar_mensaje_verificado`, `agregar_mensaje_evento`).

The router MUST accept a `RoutableMessage` dataclass with: `text`, `author`, `category`, `event_type`, `platform`, `is_past`. Each service SHOULD build a `RoutableMessage` and delegate routing instead of inline config/sound/reader/ListBox blocks.

#### Scenario: Router dispatches to correct ListBox

- GIVEN a RoutableMessage with category="moderator"
- WHEN the router processes it
- THEN the message appears in `list_box_moderadores` when `eventos[4]` and `categorias[4]` are enabled

#### Scenario: Router respects config toggles

- GIVEN `eventos[0]` is disabled and a general message arrives
- WHEN the router processes it
- THEN no sound plays and no TTS reads for that message

#### Scenario: Identical routing across platforms

- GIVEN an equivalent chat message arrives on TikTok and on Kick
- WHEN each service builds a RoutableMessage and delegates to the router
- THEN resulting sound/reader/ListBox dispatch matches pre-refactor behavior

### Requirement: Threading Safety

YouTube (`recibir`) and Twitch chat loops run in background threads. Both services MUST wrap ALL UI calls in `wx.CallAfter`. Direct UI calls from threads (`player.play`, `reader.leer_mensaje`, `chat_controller` methods, wx.Dialog creation) MUST NOT occur without `wx.CallAfter`. The MessageRouter MUST be thread-safe or only invoked via `wx.CallAfter`.

#### Scenario: YouTube message from thread

- GIVEN ServicioYouTube running `recibir()` in a background thread
- WHEN a chat message arrives
- THEN all UI updates execute via `wx.CallAfter`

#### Scenario: Twitch message from thread

- GIVEN ServicioTwich chat loop running in a background thread
- WHEN any chat message triggers routing
- THEN no wxPython object is mutated without `wx.CallAfter`

### Requirement: Chat Menu Status Fix

`controller/menus/chat_menu_controller.py` MUST NOT assume `servicio.chat.status` exists. Each service SHOULD expose a `status` attribute that `chat_menu_controller` can safely query without AttributeError.

#### Scenario: No crash without chat_downloader

- GIVEN ServicioTiktok or ServicioSala is the active service
- WHEN `chat_menu_controller.addFavoritos` checks service status
- THEN no AttributeError occurs — the check degrades safely

#### Scenario: Twitch past status still detected

- GIVEN ServicioTwich with `chat.status == 'past'`
- WHEN `chat_menu_controller.addFavoritos` checks status
- THEN the title is correctly extracted via `funciones.extractUser(url)`
