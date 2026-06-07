# Tasks: Chat Service Protocol & Message Router Refactor

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~300-400 (Phase 1: ~50, Phase 2: ~250-350) |
| 400-line budget risk | Low-Medium |
| Chained PRs recommended | No |
| Suggested split | 2 sequential PRs (PR 1 → PR 2) |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low-Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | ChatService Protocol + annotations + chat_menu fix | PR 1 | Zero runtime change, ~50 lines |
| 2 | MessageRouter + per-service refactors + wx.CallAfter fixes | PR 2 | ~250-350 lines, under 400 budget |

## Phase 1: ChatService Protocol (Zero Behavior Change)

- [x] 1.1 Create `servicios/chat_service_protocol.py` with ChatService Protocol (url, iniciar_chat, detener, estadisticas_manager, chat_controller, media_controller)
- [x] 1.2 Add `: ChatService` annotation to ServicioTiktok in `servicios/tiktok.py`
- [x] 1.3 Add `: ChatService` annotation to ServicioKick in `servicios/kick.py`
- [x] 1.4 Add `: ChatService` annotation to ServicioYouTube in `servicios/youtube.py`
- [x] 1.5 Add `: ChatService` annotation to ServicioTwich in `servicios/twich.py`
- [x] 1.6 Add `: ChatService` annotation to ServicioSala in `servicios/sala.py`
- [x] 1.7 Add `: ChatService` annotation to YouTubeRealTimeService in `servicios/YouTubeRealDataTime.py`
- [x] 1.8 Update `controller/main_controller.py` service variable type hint to `ChatService`
- [x] 1.9 Fix `controller/menus/chat_menu_controller.py` — replace `servicio.chat.status` with `getattr(servicio, 'status', None)`
- [x] 1.10 Verify: `ty check` passes on all modified files

## Phase 2: MessageRouter + Per-Service Refactors + Fixes

- [x] 2.1 Create `servicios/message_router.py` with RoutableMessage dataclass + CATEGORY_INDICES map + MessageRouter class
- [x] 2.2 Refactor ServicioTiktok: build RoutableMessage in each on_* handler → router.route(msg)
- [x] 2.3 Refactor ServicioKick: build RoutableMessage in message handlers → router.route(msg)
- [x] 2.4 Refactor ServicioYouTube: replace inline routing + wrap remaining UI calls in wx.CallAfter
- [x] 2.5 Refactor ServicioTwich: replace inline routing + wrap all UI calls in wx.CallAfter
- [x] 2.6 Refactor ServicioSala: build RoutableMessage → router.route(msg) + wrap Timer UI calls in wx.CallAfter
- [x] 2.7 Refactor YouTubeRealDataTime: wrap player.play calls in wx.CallAfter
- [x] 2.8 Verify: each service produces identical routing output to pre-refactor (side-by-side trace)
- [x] 2.9 Verify: `ty check` passes on all modified files
- [x] 2.10 Verify: YouTube/Twitch thread safety (no `wx._core.PyAssertionError` in live test)
