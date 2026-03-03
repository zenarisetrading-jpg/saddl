# Session State Centralization Report

## Summary

- **Total unique keys found and initialized:** 69
- **File created:** `app_core/session_state.py`
- **Wired into:** `ppcsuite_v4_ui_experiment.py` — `init_session_state()` is called as the **first line of `main()`**, before any routing or auth logic.

---

## Syntax Check Results

```
session_state.py SYNTAX OK
ppcsuite_v4_ui_experiment.py SYNTAX OK
```

---

## Where init_session_state() Was Wired In

**File:** `ppcsuite_v4_ui_experiment.py`

**Location:** `def main():` function body — line 1 of the function, before `query_params = st.query_params`.

**Import added** (line ~84, alongside other `app_core` imports):
```python
from app_core.session_state import init_session_state
```

**Call added** (first line of `main()`):
```python
def main():
    # Initialize all session state keys with safe defaults before any logic runs.
    # This eliminates the entire class of KeyError crashes permanently.
    init_session_state()
    ...
```

---

## Complete Key List with Assigned Defaults

### Navigation
| Key | Default | Type |
|-----|---------|------|
| `current_module` | `"home"` | str |
| `active_perf_tab` | `"Business Overview"` | str |
| `active_creator_tab` | `"Launch New Product"` | str |
| `active_opt_tab` | `"Overview"` | str |
| `active_neg_tab` | `"Keyword Negatives"` | str |
| `active_bid_tab` | `"Exact Keywords"` | str |
| `auth_view` | `"login"` | str |

### Auth / Account
| Key | Default | Type |
|-----|---------|------|
| `user` | `None` | None |
| `current_user` | `None` | None |
| `active_account_id` | `None` | None |
| `active_account_name` | `""` | str |
| `active_account` | `{}` | dict |
| `permission_account_context` | `None` | None |
| `amazon_connected` | `False` | bool |
| `amazon_client_id` | `""` | str |
| `amazon_oauth_state` | `""` | str |
| `client_id` | `""` | str |
| `login_tracked` | `False` | bool |

### Database / App Config
| Key | Default | Type |
|-----|---------|------|
| `db_manager` | `None` | None |
| `test_mode` | `False` | bool |
| `theme_mode` | `"dark"` | str |
| `read_only_mode` | `False` | bool |

### Data / Upload
| Key | Default | Type |
|-----|---------|------|
| `unified_data` | `{search_term_report: None, advertised_product_report: None, bulk_id_mapping: None, category_mapping: None, enriched_data: None, upload_status: {...}, upload_timestamps: {}}` | dict |
| `data_upload_timestamp` | `None` | None |
| `data_version` | `"v1"` | str |
| `last_stats_save` | `{}` | dict |
| `latest_data_date` | `None` | None |

### Optimizer (Shared)
| Key | Default | Type |
|-----|---------|------|
| `run_optimizer_refactored` | `False` | bool |
| `optimizer_results_refactored` | `None` | None |
| `optimizer_results` | `None` | None |
| `latest_optimizer_run` | `None` | None |
| `optimizer_config` | `{}` | dict |
| `optimizer_css_injected` | `False` | bool |
| `optimizer_actions_accepted` | `False` | bool |
| `opt_profile` | `"balanced"` | str |
| `opt_risk_profile` | `"Balanced"` | str |
| `opt_target_roas` | `2.5` | float |
| `opt_neg_clicks_threshold` | `10` | int |
| `opt_min_clicks_exact` | `5` | int |
| `opt_min_clicks_pt` | `5` | int |
| `opt_min_clicks_broad` | `8` | int |
| `opt_min_clicks_auto` | `8` | int |
| `opt_alpha_exact` | `25` | int |
| `opt_alpha_broad` | `20` | int |
| `opt_max_bid_change` | `25` | int |
| `opt_harvest_roas_mult` | `85` | int |
| `opt_test_mode` | `False` | bool |
| `opt_show_ids` | `False` | bool |
| `opt_start_date` | `None` | None |
| `opt_end_date` | `None` | None |
| `opt_date_start` | `None` | None |
| `opt_date_end` | `None` | None |
| `pending_actions` | `None` | None |
| `consolidation_negatives` | `[]` | list |
| `trigger_save` | `False` | bool |

### Optimizer V2
| Key | Default | Type |
|-----|---------|------|
| `v2_opt_state` | `"entry"` | str |
| `v2_opt_results` | `None` | None |
| `v21_commerce_fetch_ok` | `False` | bool |
| `v21_commerce_rows` | `0` | int |
| `v21_spapi_missing` | `False` | bool |

### Performance / Reporting
| Key | Default | Type |
|-----|---------|------|
| `target_roas` | `3.0` | float |
| `biz_overview_window` | `"30D"` | str |
| `ppc_window_days` | `30` | int |
| `ppc_match_filter` | `"All"` | str |
| `date_range` | `""` | str |
| `exec_dash_date_range` | `"Last 30 Days"` | str |
| `report_config` | `{}` | dict |
| `report_card_ai_summary` | `""` | str |
| `show_client_report` | `False` | bool |
| `show_share_result` | `False` | bool |
| `_cockpit_data_source` | `""` | str |

### Impact Dashboard
| Key | Default | Type |
|-----|---------|------|
| `_impact_metrics` | `{}` | dict |
| `validated_only_toggle` | `True` | bool |
| `validated_only_toggle_v2` | `True` | bool |
| `impact_horizon_v2` | `None` | None |

### ASIN / Cluster / AI
| Key | Default | Type |
|-----|---------|------|
| `latest_asin_analysis` | `None` | None |
| `latest_ai_insights` | `{}` | dict |
| `asin_mapper_integration_stats` | `{}` | dict |

### Creator / Harvest
| Key | Default | Type |
|-----|---------|------|
| `harvest_payload` | `None` | None |

### Chat / Assistant
| Key | Default | Type |
|-----|---------|------|
| `messages` | `[]` | list |

### Onboarding
| Key | Default | Type |
|-----|---------|------|
| `show_onboarding` | `False` | bool |
| `onboarding_step` | `1` | int |
| `onboarding_completed` | `False` | bool |

### UI Flags
| Key | Default | Type |
|-----|---------|------|
| `show_account_form` | `False` | bool |
| `reassign_preview_active` | `False` | bool |

### Action Confirmation / Navigation Guards
| Key | Default | Type |
|-----|---------|------|
| `_show_action_confirmation` | `False` | bool |
| `_pending_navigation_target` | `None` | None |
| `_last_saved_batch_id` | `None` | None |
| `_last_saved_client_id` | `None` | None |
| `_undo_window_start` | `None` | None |

### Sidebar / Layout State
| Key | Default | Type |
|-----|---------|------|
| `_sidebar_state` | `"expanded"` | str |
| `sidebar_state` | `"expanded"` | str |
| `_main_menu_visibility` | `"hidden"` | str |

---

## Sources Searched

- `ppcsuite_v4_ui_experiment.py`
- `app_core/` (account_utils.py, auth/service.py, data_hub.py)
- `ui/` (action_confirmation.py, account_manager.py, auth/login.py, auth/accept_invite.py, client_report_page.py, components/empty_states.py, data_hub.py, layout.py, onboarding.py, performance_dashboard/business_overview.py, performance_dashboard/ppc_overview.py, theme.py)
- `features/` (account_settings.py, asin_mapper.py, assistant.py, creator.py, debug_ui.py, diagnostics/control_center.py, executive_dashboard.py, impact_dashboard.py, impact/*, kw_cluster.py, optimizer_shared/*, optimizer_ui.py, optimizer_v2/*, platform_admin.py, report_card.py, simulator.py)
- `utils/` (amazon_oauth.py, formatters.py)
