## Exploration: Send Chat Messages in Live Streams

### Current State

VeTube is a **read-only** live stream chat viewer. It connects to 5 platforms (TikTok, YouTube, Twitch, Kick, "La Sala de Juegos") and displays incoming messages in categorized `wx.ListBox` widgets inside a `ChatPanel`. There is **no existing mechanism to send messages** — no text input field, no send buttons, no controller methods, and no service layer for outbound communication.

The chat UI (`chat_ui.py`) is structured as a `ChatPanel` with a `Treebook` of list boxes (General, Events, Members, Donations, Moderators, Verified, Favorites) and action buttons (Close, Delete, Options, Filter). All user interaction is receive-only: navigate between list boxes, copy messages, archive, add to favorites, search.

### Key Platform API Findings

| Platform | Library | Send API Available |
|----------|---------|-------------------|
| TikTok | `TikTokLive` (vía WebSocket) | **No** — purely read-only; no `send_message` anywhere in the client |
| Kick | `kick.py` (git: iamoverit/kick.py) | **Yes** — `Chatroom.send(content: str) -> Message` (async) |
| YouTube | `chat-downloader` / `pytchat` | **No** — both are read-only scrapers |
| Twitch | `chat-downloader` | **No** — read-only |
| La Sala | `PlayroomHelper` (custom) | **No** — only `get_new_messages()` |

### Affected Areas

- `servicios/tiktok.py` — `ServicioTiktok`: needs an HTTP-based send method (TikTokLive has no send capability)
- `servicios/kick.py` — `ServicioKick`: has `kick.Chatroom.send()` available, needs wiring
- `servicios/youtube.py`, `servicios/twich.py`, `servicios/YouTubeRealDataTime.py` — YouTube/Twitch: no send API in their libraries
- `servicios/sala.py` — `ServicioSala`: no send capability in PlayroomHelper
- `controller/chat_controller.py` — `ChatController`: needs a `send_message(text)` method to bridge UI → service
- `ui/chat_ui.py` — `ChatPanel`: needs a `wx.TextCtrl` input field + `wx.Button` ("Send") at the bottom
- `ui/chat_dialog.py` — `ChatDialog`: may need global send shortcut registration
- `keymaps/keys.txt` — new shortcut (e.g. `Enter` to send when input focused)
- `globals/data_store.py` — may need config options (e.g. enable/disable send, default platform identity)

### Approaches

1. **Send via Kick only (native support)**
   - Add a send input bar to `ChatPanel` (TextCtrl + Button)
   - Add `send_message(text)` to `ChatController` → delegates to `servicio.enviar_mensaje(text)`
   - Implement `enviar_mensaje()` only on `ServicioKick` using `self.client.get_chatroom().send(content)`
   - Other platforms show the input bar disabled with a tooltip "Send not supported for this platform"
   - **Pros**: Minimal risk, works today on Kick, clean separation
   - **Cons**: Only 1/5 platforms supported; inconsistent UX
   - **Effort**: Medium (2-3 days)

2. **Send via Kick + TikTok HTTP reverse-engineering**
   - Same UI + controller changes as approach 1
   - For TikTok: reverse-engineer the `https://www.tiktok.com/api/live/chat/post` or similar endpoint (requires auth cookies from the same session, TT-signature, etc.)
   - Implement TikTok send in `ServicioTiktok.enviar_mensaje()` using `httpx.AsyncClient` with cookies from the existing connection
   - **Pros**: Covers 2 most-used platforms
   - **Cons**: TikTok send API is undocumented, requires sign server or reverse-engineering, likely breaks with TikTok updates; high maintenance burden
   - **Effort**: High (1-2 weeks, mostly TikTok research)

3. **Pluggable send interface (future-proof)**
   - Define a protocol/abstract method `enviar_mensaje(text) -> bool` in a base class or interface
   - Each service implements it if supported (Kick natively, TikTok via HTTP, others via `NotImplementedError`)
   - UI input field always visible but the button calls the controller which checks if `hasattr(servicio, 'enviar_mensaje')` and the method doesn't raise
   - **Pros**: Clean architecture, easy to add new platforms later
   - **Cons**: Same per-platform challenges; more up-front design overhead
   - **Effort**: Medium-High (depends on how many platforms to support at launch)

### Recommendation

**Start with Approach 1 (Kick-only send) but designed with Approach 3's interface in mind.**

Concrete steps:
1. Add an abstract method or protocol `enviar_mensaje(text: str) -> bool` that each service can optionally implement. Start with a mixin or duck-typing check.
2. Add the UI components (TextCtrl + Send button) to `ChatPanel` — always visible but disabled for platforms that don't support sending.
3. Wire `ChatController.send_message(text)` → delegates to `self.servicio.enviar_mensaje(text)` if available.
4. Implement `ServicioKick.enviar_mensaje()` using `await chatroom.send(text)` (runs in the existing asyncio loop).
5. For TikTok, YouTube, Twitch, Sala — leave unimplemented (input bar shown but button disabled with a descriptive tooltip).

This gives you a working feature on Kick immediately while keeping the door open for TikTok later without refactoring.

### Risks

- **TikTok sent message API is undocumented**: TikTokLive is a read-only WebSocket client. Sending requires a separate HTTP endpoint with proper session cookies that likely need to be obtained from a real browser session (not available from the WebSocket-only connection). This may not be feasible without a headless browser or sign server integration.
- **Kick send requires login**: The `kick.py` library's `Chatroom.send()` requires an authenticated user session. The current `ServicioKick` connects anonymously (no `client.login()` call). Sending will require adding or obtaining auth credentials.
- **Platform restrictions**: TikTok restricts chat sending to users who have certain permissions (followed for X days, etc.). Not all viewers can chat.
- **Threading model**: All services run chat reading in background threads with `wx.CallAfter` for UI updates. Sending needs to bridge the UI thread → asyncio thread safely (use `asyncio.run_coroutine_threadsafe`).
- **Accessibility**: The app is screen-reader oriented (wxPython with accessibility). Any new input must be fully keyboard-accessible and announced.

### Ready for Proposal

**No** — there are blocking unknowns that the user needs to clarify:

1. **Which platforms should support sending?** Kick is guaranteed (native API). TikTok is the primary platform but requires undocumented reverse-engineering. YouTube/Twitch would need OAuth/IRI integration.
2. **Does the user expect to send as themselves (authenticated) or as an anonymous viewer?** Authenticated sending (especially on TikTok) is a fundamentally different challenge than anonymous read-only.
3. **Is the user willing to accept a Kick-only send feature initially?** This is the pragmatic starting point but may not match the expectation if TikTok is the primary use case.
4. **Is there a TikTok account/cookie the user can provide for sending?** Without session authentication, TikTok sending is likely impossible.
