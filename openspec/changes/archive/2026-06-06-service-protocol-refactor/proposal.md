# Proposal: Chat Service Protocol & Message Router Refactor

## Intent

Five chat services (TikTok, Kick, YouTube, Twitch, Sala) share the same constructor/lifecycle shape with no formal contract. Message routing (badge/tipo → category → sound → reader → ListBox) is copy-pasted across all five with platform-specific variations. Two threading bugs exist: YouTube/Twitch call UI methods from threads without wx.CallAfter. Eliminate duplication, establish a contract, fix bugs — without behavioral changes to the routing output.

## Scope

### In Scope
- `ChatService` Protocol definition + type annotations on all 5 services
- `MessageRouter` extraction (shared routing: config → category → sound → reader → ListBox)
- YouTube/Twitch `wx.CallAfter` threading fixes
- `chat_menu_controller.py` `.chat.status` assumption fix
- Unify `agregar_mensaje_evento(tipo)` param inconsistency

### Out of Scope
- Full base class hierarchy (threading models too divergent)
- Service factory pattern or DI
- Any other architectural changes

## Capabilities

### New Capabilities
- `service-contract`: Formal ChatService protocol + shared message routing extracted from 5 platforms

### Modified Capabilities
- None

## Approach

2-phase incremental:
- **Phase 1** — Protocol: Add `servicios/chat_service_protocol.py`, type-annotate 5 service classes, update `main_controller.py`. Zero behavior change.
- **Phase 2** — Router: Extract `MessageRouter` + `RoutableMessage` dataclass. Refactor one service at a time (build RoutableMessage → pass to router). Fix threading bugs during each service's refactor pass.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `servicios/chat_service_protocol.py` | **New** | ChatService Protocol |
| `servicios/message_router.py` | **New** | Shared routing (Phase 2) |
| `servicios/tiktok.py` | Modified | Annotations + routing extraction |
| `servicios/kick.py` | Modified | Annotations + routing extraction |
| `servicios/youtube.py` | Modified | Annotations + routing + wx.CallAfter |
| `servicios/twich.py` | Modified | Annotations + routing + wx.CallAfter |
| `servicios/sala.py` | Modified | Annotations + routing extraction |
| `controller/main_controller.py` | Modified | Protocol type usage |
| `controller/menus/chat_menu_controller.py` | Modified | Fix .chat.status assumption |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Router refactor introduces sound/reader regressions | Med | Test each service individually after refactor |
| Threading fix alters YT/Twitch timing | Low | Semantics identical — additive change only |
| Router misses platform quirk (Kick priority, YT past/live, Sala private, Twitch subs) | Med | Platform-specific tests per service |

## Rollback

Phase 1: Delete protocol file + revert annotations (zero behavior change — trivially safe).
Phase 2: Delete `message_router.py` + restore inline routing per service. Threading `wx.CallAfter` fixes are additive and safe to revert independently.

## Dependencies

None — internal refactoring within existing `servicios/`.

## Success Criteria

- [ ] `ty check` passes on all service files
- [ ] Each service's message routing produces identical output to before refactor
- [ ] YouTube/Twitch thread-safety confirmed (no UI calls without wx.CallAfter)
- [ ] chat_menu_controller.py doesn't assume .chat.status
- [ ] All existing tests pass
