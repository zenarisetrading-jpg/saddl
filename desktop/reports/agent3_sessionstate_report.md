# Session State Audit Report

## Summary

| Metric | Count |
|--------|-------|
| Total Unique Session State Keys | 57 |
| Properly Initialized | 36 (63%) |
| Read-Before-Set Crash Risks | 12 (21%) |
| Write-Only / Memory Bloat | 8 (14%) |
| Duplicate / Conflicting Keys | 3 |
| Files Using Session State | 55 |

---

## CRASH RISKS: Read-Before-Set Keys

| Key | File:Line | Risk | Notes |
|-----|-----------|------|-------|
| `theme_mode` | `ui/theme.py:18` | **HIGH** | Dot-notation access without init check; should guard with `if "theme_mode" not in st.session_state` |
| `unified_data` | `features/assistant.py:260` | **HIGH** | Direct `st.session_state.unified_data['search_term_report']` — no None check |
| `current_module` | `features/optimizer_shared/ui/landing.py` | MEDIUM | Accessed without init check in landing page |
| `active_perf_tab` | `ppcsuite_v4_ui_experiment.py:226` | MEDIUM | Feature-flag branches at lines 215–216 can skip initialization |
| `onboarding_step` | `ui/onboarding.py:100` | MEDIUM | Read in render path without guaranteed prior set |
| `_impact_metrics` | `features/impact/components/hero.py:62` | MEDIUM | Assigned but unclear if init check is performed before first read |
| `amazon_connected` | `ui/onboarding.py:407` | MEDIUM | Read via `.get()` (safe) but **never set anywhere** — dead/incomplete feature |
| `amazon_client_id` | `ui/onboarding.py:458` | MEDIUM | Same as above — key never set in codebase |
| `read_only_mode` | `ui/client_report_page.py:1295` | MEDIUM | Never explicitly set — presumably set via URL param; no fallback init |
| `optimizer_results` | `features/assistant.py:351` | LOW | Falls back to `latest_optimizer_run` (itself unclear if set) |
| `pending_actions` | `ui/action_confirmation.py:19` | LOW | Uses `.get()` — safe, but key could be stale across page reloads |
| `active_account_id` | `features/executive_dashboard.py:301` | LOW | Uses `.get()` — safe |

---

## MEMORY BLOAT: Write-Only Keys

| Key | Set Location | Never Read | Recommendation |
|-----|-------------|------------|----------------|
| `last_upload_result` | `ui/data_hub.py:370` | Confirmed | Remove |
| `onboarding_completed` | `ui/onboarding.py:65` | Confirmed | Remove or wire to a check |
| `perf_dash_spapi_available` | `ui/performance_dashboard/business_overview.py:1672` | Confirmed | Remove |
| `run_optimizer` | `app_core/data_hub.py:130, 576` | Confirmed | Remove |
| `should_log_actions` | `app_core/data_hub.py:131, 577` | Confirmed | Remove |
| `data` | `ppcsuite_v4_ui_experiment.py:154` | Confirmed | Remove |
| `single_account_mode` | `ui/account_manager.py:84, 99` | Not found read | Verify — possible dead remnant |
| `_impact_metrics` | `features/impact/components/hero.py:62` | Unconfirmed | Verify read location or remove |

---

## DUPLICATE / CONFLICTING Keys

| Key | Conflict Description | Files Involved |
|-----|----------------------|----------------|
| `active_account_id` | Used both as UI selection state AND as fallback in `get_active_account_id()` — dual-purpose blurs read/write ownership | `ui/account_manager.py`, `app_core/account_utils.py` |
| `_pending_navigation_target` | Named as internal (`_` prefix) but read across 2 modules — hidden cross-module coupling | `ui/layout.py:277`, `ui/action_confirmation.py:26, 56` |
| `opt_*` config keys (12 keys) | 12 individual flat keys should be one `opt_config` dict — fragile, hard to audit, easy to miss during init | `features/optimizer_shared/__init__.py:36–59` |

---

## Full Key Inventory (Alphabetical)

### Authentication & User State

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `auth_view` | `ui/auth/login.py:33,86,94,127,183` | `ui/auth/login.py:101,127` | OK |
| `amazon_connected` | **NEVER SET** | `ui/onboarding.py:407` | **CRASH RISK / DEAD CODE** |
| `amazon_client_id` | **NEVER SET** | `ui/onboarding.py:458` | **CRASH RISK / DEAD CODE** |

### Account Management

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `active_account_id` | `ui/account_manager.py:79,204,295`; `ui/data_hub.py:467,471,475` | `app_core/account_utils.py:29`; `ui/layout.py:385`; many features | OK — widely used, `.get()` safe |
| `active_account_name` | `ui/account_manager.py:80,205,296` | `app_core/account_utils.py:30,43`; `ui/layout.py:386`; entry point | OK |
| `single_account_mode` | `ui/account_manager.py:84,99` | Not found | **WRITE-ONLY** |

### Dashboard & UI State

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `active_perf_tab` | `ppcsuite_v4_ui_experiment.py:212,216,228,239,250,272` | `ppcsuite_v4_ui_experiment.py:226,237,248,254,257,260` | **INIT RISK** in feature-flag branches |
| `current_module` | `ppcsuite_v4_ui_experiment.py:151`; `ui/layout.py:1103,1134,1165`; many | `ui/layout.py:268,344`; entry point | OK — init at top level |
| `theme_mode` | `ui/theme.py:10,23` | `ui/theme.py:18,22,33,285`; `ui/layout.py:284`; `features/executive_dashboard.py:1203` | **HIGH CRASH RISK** — dot notation without guard |
| `biz_overview_window` | `ui/performance_dashboard/business_overview.py:1647` | `ui/performance_dashboard/business_overview.py:1669` | OK |
| `ppc_window_days` | `ui/performance_dashboard/ppc_overview.py:803` | `ui/performance_dashboard/ppc_overview.py:826,832,838` | OK |
| `ppc_match_filter` | `ui/performance_dashboard/ppc_overview.py:805` | `ui/performance_dashboard/ppc_overview.py:880,958` | OK |
| `perf_dash_spapi_available` | `ui/performance_dashboard/business_overview.py:1672` | **NEVER READ** | **WRITE-ONLY** |

### Onboarding

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `show_onboarding` | `ui/onboarding.py:48,57`; `ui/auth/accept_invite.py:463` | `ui/onboarding.py:43`; entry point | OK — `.get()` used |
| `onboarding_step` | `ui/onboarding.py:49,58,94,100,273,360,370,529` | `ui/onboarding.py:100,766` | **MEDIUM RISK** — render path read without guaranteed init |
| `onboarding_completed` | `ui/onboarding.py:65` | **NEVER READ** | **WRITE-ONLY** |

### Data & Upload State

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `unified_data` | `app_core/data_hub.py:25,299,470`; `ui/account_manager.py:169,266` | `ui/data_hub.py:299,306,359,385,408,428`; `features/assistant.py:260,261`; many | **HIGH RISK** at `features/assistant.py:260` — no None guard |
| `data_upload_timestamp` | `ui/data_hub.py:194` | `ui/performance_dashboard/business_overview.py:1679`; `features/executive_dashboard.py:520,561` | OK — used in cache versioning |
| `last_stats_save` | `app_core/data_hub.py:186,208,605` | `app_core/account_utils.py:31` | OK — `.get()` used |
| `last_upload_result` | `ui/data_hub.py:370` | **NEVER READ** | **WRITE-ONLY** |
| `data` | `ppcsuite_v4_ui_experiment.py:154` | **NEVER READ** | **WRITE-ONLY** |

### Optimizer Configuration (12 flat keys — fragile pattern)

| Key | Set Location | Status |
|-----|-------------|--------|
| `opt_profile` | `features/optimizer_shared/__init__.py:37` | OK — but should be in single dict |
| `opt_harvest_roas_mult` | `features/optimizer_shared/__init__.py:39` | OK |
| `opt_alpha_exact` | `features/optimizer_shared/__init__.py:41` | OK |
| `opt_alpha_broad` | `features/optimizer_shared/__init__.py:43` | OK |
| `opt_max_bid_change` | `features/optimizer_shared/__init__.py:45` | OK |
| `opt_target_roas` | `features/optimizer_shared/__init__.py:47` | OK — also read in `features/assistant.py:449` |
| `opt_neg_clicks_threshold` | `features/optimizer_shared/__init__.py:49` | OK |
| `opt_min_clicks_exact` | `features/optimizer_shared/__init__.py:51` | OK |
| `opt_min_clicks_pt` | `features/optimizer_shared/__init__.py:53` | OK |
| `opt_min_clicks_broad` | `features/optimizer_shared/__init__.py:55` | OK |
| `opt_min_clicks_auto` | `features/optimizer_shared/__init__.py:57` | OK |
| `opt_test_mode` | `features/optimizer_shared/__init__.py:59,63` | OK |

### Optimizer Actions & Results

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `pending_actions` | `ui/action_confirmation.py:52,107` | `ui/action_confirmation.py:19,83`; `ui/layout.py:272` | OK — `.get()` used |
| `optimizer_actions_accepted` | `ui/action_confirmation.py:104,190` | `ui/layout.py:273` | OK — `.get()` used |
| `optimizer_results` | Not found set clearly | `features/assistant.py:351` | **MEDIUM RISK** — falls back to `latest_optimizer_run` which also unclear |
| `latest_optimizer_run` | Not found | `features/assistant.py:351` | **UNDEFINED** |
| `run_optimizer` | `app_core/data_hub.py:130,576` | **NEVER READ** | **WRITE-ONLY** |
| `should_log_actions` | `app_core/data_hub.py:131,577` | **NEVER READ** | **WRITE-ONLY** |

### Action Confirmation & Navigation

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `_show_action_confirmation` | `ui/layout.py:278`; `ui/action_confirmation.py:21,53,66,108` | `ui/action_confirmation.py:75`; `ui/layout.py:268,278` | OK |
| `_pending_navigation_target` | `ui/layout.py:277`; `ui/action_confirmation.py:56,67,109` | `ui/action_confirmation.py:26,67` | OK — `.get()` — but cross-module coupling |
| `_last_saved_batch_id` | `ui/action_confirmation.py:99,137,167,187` | `ui/action_confirmation.py:125,154` | OK — `.get()` |
| `_last_saved_client_id` | `ui/action_confirmation.py:100,138,168,188` | `ui/action_confirmation.py:155` | OK |
| `_undo_window_start` | `ui/action_confirmation.py:101,138,169,189` | `ui/action_confirmation.py:126` | OK — `.get()` |

### Impact Analysis

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `_impact_metrics` | `features/impact/components/hero.py:62` | Not confirmed | **POTENTIALLY WRITE-ONLY** |
| Dynamic impact cache key | `ui/layout.py:442` | `ui/layout.py:445` | OK — cleaned up in try/finally |

### Report & Client State

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `report_config` | `ui/client_report_page.py:792` | `ui/client_report_page.py:1177` | OK — `.get()` |
| `show_client_report` | `ui/client_report_page.py:798,1163` | `ui/client_report_page.py:1153` | OK |
| `date_range` | `ui/client_report_page.py:802` | `ui/client_report_page.py:1250,1251` | OK — `.get()` |
| `show_share_result` | `ui/client_report_page.py:890` | `ui/client_report_page.py:894` | OK |
| `read_only_mode` | **NEVER SET** | `ui/client_report_page.py:1295` | **READ WITHOUT SET** — shared report feature incomplete |
| `client_report_narratives_*` (dynamic) | `ui/client_report_page.py:1201` | `ui/client_report_page.py:1236`; cleanup at 805 | OK — dynamic cache pattern |

### App Infrastructure

| Key | Set Location(s) | Read Location(s) | Status |
|-----|----------------|-----------------|--------|
| `db_manager` | `ppcsuite_v4_ui_experiment.py:160` | Multiple features via `.get()` | OK — properly initialized at startup |
| `test_mode` | `ppcsuite_v4_ui_experiment.py:157` | Multiple features via `.get()` | OK |

---

## Most Referenced Keys

1. `active_account_id` — 23 references
2. `current_module` — 18 references
3. `test_mode` — 15 references
4. `db_manager` — 12 references
5. `unified_data` — 11 references

---

## Recommendations

### Immediate (Crash Prevention)
1. **`ui/theme.py:10`** — Add `if "theme_mode" not in st.session_state:` guard before assignment
2. **`features/assistant.py:260`** — Change to `st.session_state.get("unified_data", {}).get("search_term_report")`
3. **`ppcsuite_v4_ui_experiment.py:212–228`** — Ensure `active_perf_tab` is initialized before all feature-flag branches
4. **`ui/onboarding.py`** — Audit `amazon_connected` / `amazon_client_id` — either set them or remove the dead read code
5. **`ui/client_report_page.py`** — Add explicit `read_only_mode` initialization in the shared report handler

### Short-Term (Cleanup)
6. Remove write-only keys: `last_upload_result`, `onboarding_completed`, `perf_dash_spapi_available`, `run_optimizer`, `should_log_actions`, `data`
7. Consolidate 12 `opt_*` keys into a single `opt_config` dict at `features/optimizer_shared/__init__.py`
8. Standardize all initialization to use bracket notation with explicit guards

### Long-Term (Architecture)
9. Create a centralized `init_session_state()` function to initialize all known keys at startup
10. Consider a `TypedDict` or `dataclass` to enforce session state schema and enable IDE type checking
