╭───────────────────────────────────────────── Traceback (most recent call last) ─────────────────────────────────────────────╮
│ C:\Users\rabas\Desktop\Hackaton_Mistral\mistral-vibe\.venv\Lib\site-packages\textual\message_pump.py:596 in _pre_process    │
│                                                                                                                             │
│   593 │   │   │   │   │   await self._dispatch_message(events.Mount())                                                      │
│   594 │   │   │   else:                                                                                                     │
│   595 │   │   │   │   await self._dispatch_message(events.Mount())                                                          │
│ ❱ 596 │   │   │   self._post_mount()                                                                                        │
│   597 │   │   except Exception as error:                                                                                    │
│   598 │   │   │   self.app._handle_exception(error)                                                                         │
│   599 │   │   │   return False                                                                                              │
│                                                                                                                             │
│ ╭─────────────────── locals ────────────────────╮                                                                           │
│ │ error = IndexError('list index out of range') │                                                                           │
│ │  self = LearnPanelApp(id='learnpanel-app')    │                                                                           │
│ ╰───────────────────────────────────────────────╯                                                                           │
│                                                                                                                             │
│ C:\Users\rabas\Desktop\Hackaton_Mistral\mistral-vibe\vibe\cli\textual_ui\widgets\learn_panel_app.py:739 in                  │
│ _watch_selected_option                                                                                                      │
│                                                                                                                             │
│   736 │   # ── navigation ───────────────────────────────────────────────────                                               │
│   737 │                                                                                                                     │
│   738 │   def _watch_selected_option(self) -> None:                                                                         │
│ ❱ 739 │   │   if self._phase == Phase.ASKING and self._is_mc:                                                               │
│   740 │   │   │   self._show_mc_options()                                                                                   │
│   741 │   │   elif self._phase == Phase.VALIDATING and not self._is_mc:                                                     │
│   742 │   │   │   self._show_open_ended_validation()                                                                        │
│                                                                                                                             │
│ ╭───────────────── locals ──────────────────╮                                                                               │
│ │ self = LearnPanelApp(id='learnpanel-app') │                                                                               │
│ ╰───────────────────────────────────────────╯                                                                               │
│                                                                                                                             │
│ C:\Users\rabas\Desktop\Hackaton_Mistral\mistral-vibe\vibe\cli\textual_ui\widgets\learn_panel_app.py:420 in _is_mc           │
│                                                                                                                             │
│   417 │                                                                                                                     │
│   418 │   @property                                                                                                         │
│   419 │   def _is_mc(self) -> bool:                                                                                         │
│ ❱ 420 │   │   return self._current_q["type"] == "multiple_choice"                                                           │
│   421 │                                                                                                                     │
│   422 │   @property                                                                                                         │
│   423 │   def _correct_answer(self) -> str:                                                                                 │
│                                                                                                                             │
│ ╭───────────────── locals ──────────────────╮                                                                               │
│ │ self = LearnPanelApp(id='learnpanel-app') │                                                                               │
│ ╰───────────────────────────────────────────╯                                                                               │
│                                                                                                                             │
│ C:\Users\rabas\Desktop\Hackaton_Mistral\mistral-vibe\vibe\cli\textual_ui\widgets\learn_panel_app.py:416 in _current_q       │
│                                                                                                                             │
│   413 │                                                                                                                     │
│   414 │   @property                                                                                                         │
│   415 │   def _current_q(self) -> dict[str, Any]:                                                                           │
│ ❱ 416 │   │   return self._questions[self._question_idx]                                                                    │
│   417 │                                                                                                                     │
│   418 │   @property                                                                                                         │
│   419 │   def _is_mc(self) -> bool:                                                                                         │
│                                                                                                                             │
│ ╭───────────────── locals ──────────────────╮                                                                               │
│ │ self = LearnPanelApp(id='learnpanel-app') │                                                                               │
│ ╰───────────────────────────────────────────╯                                                                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
IndexError: list index out of range
