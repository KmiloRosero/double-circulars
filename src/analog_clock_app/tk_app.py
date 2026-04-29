from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from math import cos, radians, sin
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, ttk
from tkinter import filedialog, messagebox

import tkinter as tk

from typing import cast

from analog_clock_app.config.settings import AppSettings, BackgroundMode, TimeMode
from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    CachedSettingsRepositoryProxy,
    SQLiteAlarmRepository,
    SQLitePresetRepository,
    SQLiteSettingsRepository,
    SQLiteWorldClockRepository,
)
from analog_clock_app.services.alarm_service import AlarmService
from analog_clock_app.services.clock_service import ClockService
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService
from analog_clock_app.services.world_clock_service import WorldClockService


def _default_db_path() -> str:
    p = Path.cwd() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return str(p / "app.db")


def _uploads_dir() -> Path:
    p = Path.cwd() / "data" / "uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass(slots=True)
class AppContext:
    engine: ClockEngine
    clock_service: ClockService
    settings_service: SettingsService
    preset_service: PresetService
    alarm_service: AlarmService
    world_clock_service: WorldClockService
    history: HistoryService


def build_context() -> AppContext:
    db = Database(_default_db_path())
    settings_repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
    presets_repo = SQLitePresetRepository(db)
    alarms_repo = SQLiteAlarmRepository(db)
    world_repo = SQLiteWorldClockRepository(db)

    engine = ClockEngine()
    clock_service = ClockService(engine=engine, settings_repo=settings_repo)
    settings_service = SettingsService(settings_repo)
    preset_service = PresetService(presets=presets_repo, settings=settings_repo)
    alarm_service = AlarmService(alarms_repo)
    world_clock_service = WorldClockService(world_repo)
    history = HistoryService()

    return AppContext(
        engine=engine,
        clock_service=clock_service,
        settings_service=settings_service,
        preset_service=preset_service,
        alarm_service=alarm_service,
        world_clock_service=world_clock_service,
        history=history,
    )


class AnalogClockCanvas:
    def __init__(self, parent: tk.Widget, size: int = 320) -> None:
        self.size = size
        self.canvas = tk.Canvas(parent, width=size, height=size, highlightthickness=0)
        self.canvas.configure(bg="white")

    def widget(self) -> tk.Canvas:
        return self.canvas

    def render(self, engine: ClockEngine, dt: datetime, settings: AppSettings) -> None:
        self.canvas.delete("all")
        s = self.size
        cx = cy = s / 2
        radius = min(s, s) * 0.44

        face = settings.face_color
        tick = settings.tick_color
        hand = settings.hand_color

        self.canvas.configure(bg=face)
        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=tick,
            width=3,
        )

        state = engine.state_from_datetime(dt, major_ticks_only=settings.show_major_ticks_only)

        def polar(angle_deg: float, r: float) -> tuple[float, float]:
            a = radians(angle_deg - 90.0)
            return cx + r * cos(a), cy + r * sin(a)

        for t in state.ticks:
            outer = polar(t.angle, radius)
            inner = polar(t.angle, radius - (18 if t.kind == "major" else 10))
            width = 3 if t.kind == "major" else 1
            self.canvas.create_line(inner[0], inner[1], outer[0], outer[1], fill=tick, width=width)

        hour_end = polar(state.angles.hour, radius * 0.55)
        minute_end = polar(state.angles.minute, radius * 0.75)
        second_end = polar(state.angles.second, radius * 0.85)

        if settings.enable_shadow_layer:
            off = 2
            self.canvas.create_line(cx + off, cy + off, hour_end[0] + off, hour_end[1] + off, fill="#000000", width=6)
            self.canvas.create_line(
                cx + off, cy + off, minute_end[0] + off, minute_end[1] + off, fill="#000000", width=4
            )

        self.canvas.create_line(cx, cy, hour_end[0], hour_end[1], fill=hand, width=6)
        self.canvas.create_line(cx, cy, minute_end[0], minute_end[1], fill=hand, width=4)
        self.canvas.create_line(cx, cy, second_end[0], second_end[1], fill="#EF4444", width=2)

        if settings.enable_center_dot_layer:
            self.canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=hand, outline=hand)


@dataclass(slots=True)
class StopwatchState:
    running: bool
    start_monotonic: float
    elapsed_seconds: float


@dataclass(slots=True)
class TimerState:
    running: bool
    duration_seconds: float
    start_monotonic: float
    elapsed_seconds: float


class TkApp:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx
        self.root = Tk()
        self.root.title("Reloj Analógico")
        self.root.geometry("1200x760")

        self._bg_label: tk.Label | None = None
        self._bg_image: tk.PhotoImage | None = None

        self._stopwatch = StopwatchState(running=False, start_monotonic=0.0, elapsed_seconds=0.0)
        self._timer = TimerState(running=False, duration_seconds=60.0, start_monotonic=0.0, elapsed_seconds=0.0)

        self._build_ui()
        self.apply_theme_and_background()
        self._start_loops()

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.outer = tk.Frame(self.root)
        self.outer.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(self.outer)
        header.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(header, text="Reloj Analógico", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="Pasto, Colombia", font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        self.content = tk.Frame(self.outer)
        self.content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_clock = tk.Frame(self.notebook)
        self.tab_alarms = tk.Frame(self.notebook)
        self.tab_world = tk.Frame(self.notebook)
        self.tab_stopwatch = tk.Frame(self.notebook)
        self.tab_timer = tk.Frame(self.notebook)
        self.tab_settings = tk.Frame(self.notebook)

        self.notebook.add(self.tab_clock, text="Reloj")
        self.notebook.add(self.tab_alarms, text="Alarmas")
        self.notebook.add(self.tab_world, text="Mundial")
        self.notebook.add(self.tab_stopwatch, text="Cronómetro")
        self.notebook.add(self.tab_timer, text="Temporizador")
        self.notebook.add(self.tab_settings, text="Configuración")

        self._build_clock_tab()
        self._build_alarms_tab()
        self._build_world_tab()
        self._build_stopwatch_tab()
        self._build_timer_tab()
        self._build_settings_tab()

    def apply_theme_and_background(self) -> None:
        settings = self.ctx.settings_service.get()

        bg_color = "#ffffff"
        fg_color = "#111111"
        if settings.background_mode == "black" or settings.dark_theme:
            bg_color = "#000000"
            fg_color = "#f3f4f6"

        self.root.configure(bg=bg_color)
        self.outer.configure(bg=bg_color)
        self.content.configure(bg=bg_color)

        if settings.background_mode == "image" and settings.background_image_filename:
            path = _uploads_dir() / settings.background_image_filename
            if path.exists():
                try:
                    self._bg_image = tk.PhotoImage(file=str(path))
                    if self._bg_label is None:
                        self._bg_label = tk.Label(self.root, image=self._bg_image)
                        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                        self.outer.lift()
                    else:
                        self._bg_label.configure(image=self._bg_image)
                        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                except Exception:
                    self._clear_background_image()
            else:
                self._clear_background_image()
        else:
            self._clear_background_image()

        self._status_var.set(f"Fondo: {settings.background_mode}")
        self._status_label.configure(bg=bg_color, fg=fg_color)

    def _clear_background_image(self) -> None:
        if self._bg_label is not None:
            self._bg_label.place_forget()
        self._bg_image = None

    def _build_clock_tab(self) -> None:
        settings = self.ctx.settings_service.get()

        left = tk.Frame(self.tab_clock)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        right = tk.Frame(self.tab_clock)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=12, pady=12)

        self.clock_canvas = AnalogClockCanvas(left, size=420)
        self.clock_canvas.widget().pack()

        tk.Label(right, text="Controles", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.mode_var = StringVar(value=settings.time_mode)
        ttk.Radiobutton(right, text="Real", value="real", variable=self.mode_var).pack(anchor="w")
        ttk.Radiobutton(right, text="Simulado", value="simulated", variable=self.mode_var).pack(anchor="w")

        tk.Label(right, text="Velocidad de simulación").pack(anchor="w", pady=(10, 0))
        self.speed_var = tk.DoubleVar(value=settings.simulation_speed)
        tk.Spinbox(right, from_=0.1, to=30.0, increment=0.1, textvariable=self.speed_var, width=10).pack(anchor="w")

        tk.Label(right, text="Desfase (segundos)").pack(anchor="w", pady=(10, 0))
        self.offset_var = tk.IntVar(value=settings.time_offset_seconds)
        tk.Spinbox(right, from_=-86400, to=86400, increment=10, textvariable=self.offset_var, width=10).pack(anchor="w")

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        tk.Label(right, text="Configuraciones guardadas").pack(anchor="w")
        self.preset_name_var = StringVar(value="")
        ttk.Entry(right, textvariable=self.preset_name_var, width=26).pack(anchor="w", pady=(4, 8))

        ttk.Button(right, text="Guardar configuración", command=self._save_preset).pack(fill=tk.X)

        self.preset_list = tk.Listbox(right, height=8, width=30)
        self.preset_list.pack(fill=tk.X, pady=(10, 6))
        ttk.Button(right, text="Aplicar selección", command=self._apply_selected_preset).pack(fill=tk.X)

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        ttk.Button(right, text="Aplicar", command=self._apply_clock_controls).pack(fill=tk.X)
        ttk.Button(right, text="Deshacer", command=self._undo_settings).pack(fill=tk.X, pady=(8, 0))
        ttk.Button(right, text="Rehacer", command=self._redo_settings).pack(fill=tk.X)

        self._status_var = StringVar(value="")
        self._status_label = tk.Label(right, textvariable=self._status_var)
        self._status_label.pack(fill=tk.X, pady=(12, 0))

        self._refresh_presets_listbox()

    def _apply_clock_controls(self) -> None:
        before = self.ctx.settings_service.get()
        updated = self.ctx.settings_service.apply_patch(
            SettingsPatch(
                time_mode=cast(TimeMode, self.mode_var.get()),
                simulation_speed=float(self.speed_var.get()),
                time_offset_seconds=int(self.offset_var.get()),
            )
        )
        self.ctx.history.record_change(before, updated, "Se actualizaron los controles")

    def _save_preset(self) -> None:
        name = self.preset_name_var.get().strip()
        if not name:
            messagebox.showwarning("Falta nombre", "Se requiere un nombre")
            return
        self.ctx.preset_service.save_current_settings_as_preset(name)
        self.preset_name_var.set("")
        self._refresh_presets_listbox()

    def _refresh_presets_listbox(self) -> None:
        self.preset_list.delete(0, tk.END)
        self._presets_cache = self.ctx.preset_service.list_presets()
        for p in self._presets_cache:
            self.preset_list.insert(tk.END, p.name)

    def _apply_selected_preset(self) -> None:
        sel = self.preset_list.curselection()
        if not sel:
            messagebox.showwarning("Selecciona", "Selecciona una configuración")
            return
        idx = int(sel[0])
        preset = self._presets_cache[idx]
        before = self.ctx.settings_service.get()
        settings = self.ctx.preset_service.apply_preset(preset.id)
        self.ctx.history.record_change(before, settings, "Se aplicó una configuración")

        self.mode_var.set(settings.time_mode)
        self.speed_var.set(settings.simulation_speed)
        self.offset_var.set(settings.time_offset_seconds)
        self.apply_theme_and_background()

    def _undo_settings(self) -> None:
        current = self.ctx.settings_service.get()
        if not self.ctx.history.can_undo():
            return
        previous = self.ctx.history.undo(current)
        self.ctx.settings_service.save(previous)
        self.mode_var.set(previous.time_mode)
        self.speed_var.set(previous.simulation_speed)
        self.offset_var.set(previous.time_offset_seconds)
        self.apply_theme_and_background()

    def _redo_settings(self) -> None:
        current = self.ctx.settings_service.get()
        if not self.ctx.history.can_redo():
            return
        nxt = self.ctx.history.redo(current)
        self.ctx.settings_service.save(nxt)
        self.mode_var.set(nxt.time_mode)
        self.speed_var.set(nxt.simulation_speed)
        self.offset_var.set(nxt.time_offset_seconds)
        self.apply_theme_and_background()

    def _build_alarms_tab(self) -> None:
        frame = tk.Frame(self.tab_alarms)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        top = tk.Frame(frame)
        top.pack(fill=tk.X)
        tk.Label(top, text="Crear alarma", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        form = tk.Frame(frame)
        form.pack(fill=tk.X, pady=10)

        self.alarm_label_var = StringVar(value="")
        tk.Label(form, text="Etiqueta").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.alarm_label_var, width=30).grid(row=0, column=1, sticky="w", padx=8)

        self.alarm_hour_var = StringVar(value="7")
        self.alarm_minute_var = StringVar(value="0")
        tk.Label(form, text="Hora").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(form, values=[str(h) for h in range(24)], textvariable=self.alarm_hour_var, width=6).grid(
            row=1, column=1, sticky="w", padx=8, pady=(8, 0)
        )
        tk.Label(form, text="Minuto").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        ttk.Combobox(
            form, values=[str(m) for m in range(60)], textvariable=self.alarm_minute_var, width=6
        ).grid(row=1, column=3, sticky="w", padx=8, pady=(8, 0))

        ttk.Button(form, text="Crear", command=self._create_alarm).grid(row=0, column=4, rowspan=2, padx=16)

        self.alarms_list = tk.Listbox(frame, height=12)
        self.alarms_list.pack(fill=tk.BOTH, expand=True, pady=(10, 6))

        actions = tk.Frame(frame)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Activar/Desactivar", command=self._toggle_alarm).pack(side=tk.LEFT)
        ttk.Button(actions, text="Eliminar", command=self._delete_alarm).pack(side=tk.LEFT, padx=8)

        self._refresh_alarms_list()

    def _refresh_alarms_list(self) -> None:
        self._alarms_cache = self.ctx.alarm_service.list_alarms()
        self.alarms_list.delete(0, tk.END)
        for a in self._alarms_cache:
            state = "Activa" if a.enabled else "Inactiva"
            self.alarms_list.insert(tk.END, f"{a.label} — {a.hour:02d}:{a.minute:02d} ({state})")

    def _create_alarm(self) -> None:
        label = self.alarm_label_var.get().strip() or "Alarma"
        hour = int(self.alarm_hour_var.get())
        minute = int(self.alarm_minute_var.get())
        settings = self.ctx.settings_service.get()
        self.ctx.alarm_service.add_alarm(label=label, hour=hour, minute=minute, timezone=settings.timezone)
        self.alarm_label_var.set("")
        self._refresh_alarms_list()

    def _selected_alarm_id(self) -> str | None:
        sel = self.alarms_list.curselection()
        if not sel:
            return None
        return self._alarms_cache[int(sel[0])].id

    def _toggle_alarm(self) -> None:
        alarm_id = self._selected_alarm_id()
        if alarm_id is None:
            return
        alarm = next(a for a in self._alarms_cache if a.id == alarm_id)
        self.ctx.alarm_service.set_enabled(alarm_id, not alarm.enabled)
        self._refresh_alarms_list()

    def _delete_alarm(self) -> None:
        alarm_id = self._selected_alarm_id()
        if alarm_id is None:
            return
        self.ctx.alarm_service.delete_alarm(alarm_id)
        self._refresh_alarms_list()

    def _build_world_tab(self) -> None:
        frame = tk.Frame(self.tab_world)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left = tk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = tk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Ciudades", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.world_list = tk.Listbox(left, width=34, height=16)
        self.world_list.pack(pady=(8, 6))

        self.city_choices: dict[str, str] = {
            "Pasto, Colombia": "America/Bogota",
            "New York, USA": "America/New_York",
            "Mexico City, Mexico": "America/Mexico_City",
            "Buenos Aires, Argentina": "America/Argentina/Buenos_Aires",
            "London, UK": "Europe/London",
            "Madrid, España": "Europe/Madrid",
            "Tokyo, Japón": "Asia/Tokyo",
            "Sydney, Australia": "Australia/Sydney",
        }

        self.world_add_var = StringVar(value="Pasto, Colombia")
        ttk.Combobox(left, values=list(self.city_choices.keys()), textvariable=self.world_add_var, width=30).pack(
            pady=(10, 4)
        )
        ttk.Button(left, text="Agregar", command=self._add_world_city).pack(fill=tk.X)
        ttk.Button(left, text="Quitar", command=self._remove_world_city).pack(fill=tk.X, pady=(6, 0))

        tk.Label(right, text="Reloj analógico", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.world_canvas = AnalogClockCanvas(right, size=420)
        self.world_canvas.widget().pack(pady=10)
        self.world_info = tk.Label(right, text="Selecciona una ciudad", font=("Segoe UI", 10))
        self.world_info.pack(anchor="w")

        self.world_list.bind("<<ListboxSelect>>", lambda _e: self._render_world_selected())
        self._refresh_world_list()

    def _refresh_world_list(self) -> None:
        self._world_cache = self.ctx.world_clock_service.list_favorites()
        self.world_list.delete(0, tk.END)
        for f in self._world_cache:
            self.world_list.insert(tk.END, f.label)

    def _add_world_city(self) -> None:
        label = self.world_add_var.get()
        tz_name = self.city_choices.get(label)
        if tz_name is None:
            return
        self.ctx.world_clock_service.add_favorite(label=label, timezone=tz_name)
        self._refresh_world_list()

    def _remove_world_city(self) -> None:
        sel = self.world_list.curselection()
        if not sel:
            return
        fav = self._world_cache[int(sel[0])]
        self.ctx.world_clock_service.delete_favorite(fav.id)
        self._refresh_world_list()

    def _render_world_selected(self) -> None:
        sel = self.world_list.curselection()
        if not sel:
            return
        fav = self._world_cache[int(sel[0])]
        self.world_info.configure(text=f"{fav.label} — {fav.timezone}")

    def _build_stopwatch_tab(self) -> None:
        frame = tk.Frame(self.tab_stopwatch)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(frame, text="Cronómetro (analógico)", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.stopwatch_canvas = tk.Canvas(frame, width=420, height=420, highlightthickness=0)
        self.stopwatch_canvas.pack(pady=10)

        actions = tk.Frame(frame)
        actions.pack()
        ttk.Button(actions, text="Iniciar", command=self._stopwatch_start).pack(side=tk.LEFT)
        ttk.Button(actions, text="Pausar", command=self._stopwatch_pause).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Reiniciar", command=self._stopwatch_reset).pack(side=tk.LEFT)

    def _stopwatch_start(self) -> None:
        if self._stopwatch.running:
            return
        self._stopwatch.running = True
        self._stopwatch.start_monotonic = time.monotonic()

    def _stopwatch_pause(self) -> None:
        if not self._stopwatch.running:
            return
        self._stopwatch.elapsed_seconds = self._stopwatch_elapsed()
        self._stopwatch.running = False
        self._stopwatch.start_monotonic = 0.0

    def _stopwatch_reset(self) -> None:
        self._stopwatch = StopwatchState(running=False, start_monotonic=0.0, elapsed_seconds=0.0)

    def _stopwatch_elapsed(self) -> float:
        if not self._stopwatch.running:
            return self._stopwatch.elapsed_seconds
        return self._stopwatch.elapsed_seconds + (time.monotonic() - self._stopwatch.start_monotonic)

    def _build_timer_tab(self) -> None:
        frame = tk.Frame(self.tab_timer)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(frame, text="Temporizador (analógico)", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        form = tk.Frame(frame)
        form.pack(fill=tk.X, pady=10)

        self.timer_minutes_var = tk.IntVar(value=1)
        self.timer_seconds_var = tk.IntVar(value=0)

        tk.Label(form, text="Minutos").pack(side=tk.LEFT)
        tk.Spinbox(form, from_=0, to=180, textvariable=self.timer_minutes_var, width=6).pack(side=tk.LEFT, padx=8)
        tk.Label(form, text="Segundos").pack(side=tk.LEFT)
        tk.Spinbox(form, from_=0, to=59, textvariable=self.timer_seconds_var, width=6).pack(side=tk.LEFT, padx=8)

        self.timer_canvas = tk.Canvas(frame, width=420, height=420, highlightthickness=0)
        self.timer_canvas.pack(pady=10)

        actions = tk.Frame(frame)
        actions.pack()
        ttk.Button(actions, text="Iniciar", command=self._timer_start).pack(side=tk.LEFT)
        ttk.Button(actions, text="Pausar", command=self._timer_pause).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Reiniciar", command=self._timer_reset).pack(side=tk.LEFT)

    def _timer_start(self) -> None:
        if self._timer.running:
            return
        duration = float(int(self.timer_minutes_var.get()) * 60 + int(self.timer_seconds_var.get()))
        if duration <= 0:
            messagebox.showwarning("Duración", "Configura una duración mayor a 0")
            return
        self._timer.duration_seconds = duration
        self._timer.running = True
        self._timer.start_monotonic = time.monotonic()

    def _timer_pause(self) -> None:
        if not self._timer.running:
            return
        self._timer.elapsed_seconds = self._timer_elapsed()
        self._timer.running = False
        self._timer.start_monotonic = 0.0

    def _timer_reset(self) -> None:
        self._timer.running = False
        self._timer.start_monotonic = 0.0
        self._timer.elapsed_seconds = 0.0

    def _timer_elapsed(self) -> float:
        if not self._timer.running:
            return self._timer.elapsed_seconds
        return self._timer.elapsed_seconds + (time.monotonic() - self._timer.start_monotonic)

    def _timer_remaining(self) -> float:
        rem = self._timer.duration_seconds - self._timer_elapsed()
        return max(0.0, rem)

    def _build_settings_tab(self) -> None:
        frame = tk.Frame(self.tab_settings)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        settings = self.ctx.settings_service.get()

        tk.Label(frame, text="Configuración", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        form = tk.Frame(frame)
        form.pack(fill=tk.X, pady=10)

        self.dark_var = BooleanVar(value=settings.dark_theme)
        ttk.Checkbutton(form, text="Modo oscuro (negro)", variable=self.dark_var).grid(row=0, column=0, sticky="w")

        tk.Label(form, text="Fondo fuera del recuadro").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.bg_mode_var = StringVar(value=settings.background_mode)
        ttk.Combobox(
            form, values=["white", "black", "image"], textvariable=self.bg_mode_var, width=12
        ).grid(row=1, column=1, sticky="w", padx=8, pady=(8, 0))

        ttk.Button(form, text="Elegir imagen...", command=self._choose_background_image).grid(
            row=1, column=2, padx=8, pady=(8, 0)
        )

        ttk.Button(frame, text="Guardar", command=self._save_settings).pack(anchor="w", pady=(10, 0))

    def _choose_background_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecciona una imagen (PNG)",
            filetypes=[("PNG", "*.png"), ("All files", "*.*")],
        )
        if not path:
            return
        src = Path(path)
        if src.suffix.lower() != ".png":
            messagebox.showwarning("Formato", "Usa una imagen PNG para el fondo")
            return
        dst = _uploads_dir() / "background.png"
        shutil.copyfile(src, dst)
        before = self.ctx.settings_service.get()
        updated = self.ctx.settings_service.apply_patch(
            SettingsPatch(background_mode="image", background_image_filename=dst.name)
        )
        self.ctx.history.record_change(before, updated, "Se actualizó el fondo")
        self.apply_theme_and_background()

    def _save_settings(self) -> None:
        before = self.ctx.settings_service.get()
        updated = self.ctx.settings_service.apply_patch(
            SettingsPatch(
                dark_theme=bool(self.dark_var.get()),
                background_mode=cast(BackgroundMode, self.bg_mode_var.get()),
            )
        )
        self.ctx.history.record_change(before, updated, "Se actualizó la configuración")
        self.apply_theme_and_background()

    def _start_loops(self) -> None:
        self._loop_clock()
        self._loop_alarm()
        self._loop_stopwatch()
        self._loop_timer()
        self._loop_world()

    def _loop_clock(self) -> None:
        settings = self.ctx.settings_service.get()
        state = self.ctx.clock_service.get_state()
        now_dt = datetime.now(timezone.utc)
        local_dt = ClockService._to_local_time(now_dt, settings.timezone)
        self.clock_canvas.render(self.ctx.engine, local_dt, settings)
        self.root.after(200, self._loop_clock)

    def _loop_alarm(self) -> None:
        now_utc = datetime.now(timezone.utc)
        due = self.ctx.alarm_service.check_due(now_utc)
        for alarm in due:
            messagebox.showinfo("Alarma", alarm.label)
        self.root.after(1000, self._loop_alarm)

    def _loop_world(self) -> None:
        sel = self.world_list.curselection() if hasattr(self, "world_list") else ()
        if sel:
            fav = self._world_cache[int(sel[0])]
            settings = self.ctx.settings_service.get()
            now_utc = datetime.now(timezone.utc)
            local = ClockService._to_local_time(now_utc, fav.timezone)
            self.world_canvas.render(self.ctx.engine, local, settings)
        self.root.after(1000, self._loop_world)

    def _loop_stopwatch(self) -> None:
        c = self.stopwatch_canvas
        c.delete("all")
        s = 420
        cx = cy = s / 2
        radius = 170
        c.configure(bg="#111827")
        c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#E5E7EB", width=3)

        elapsed = self._stopwatch_elapsed()
        angle = (elapsed % 60.0) / 60.0 * 360.0
        a = radians(angle - 90.0)
        x = cx + radius * 0.85 * cos(a)
        y = cy + radius * 0.85 * sin(a)
        c.create_line(cx, cy, x, y, fill="#F9FAFB", width=3)
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#F9FAFB", outline="#F9FAFB")

        self.root.after(100, self._loop_stopwatch)

    def _loop_timer(self) -> None:
        c = self.timer_canvas
        c.delete("all")
        s = 420
        cx = cy = s / 2
        radius = 170
        c.configure(bg="#111827")
        c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#374151", width=14)

        rem = self._timer_remaining()
        total = max(1.0, self._timer.duration_seconds)
        progress = min(max(1.0 - rem / total, 0.0), 1.0)
        extent = progress * 360.0
        c.create_arc(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            start=90,
            extent=-extent,
            style=tk.ARC,
            outline="#10B981",
            width=14,
        )

        angle = progress * 360.0
        a = radians(angle - 90.0)
        x = cx + radius * 0.85 * cos(a)
        y = cy + radius * 0.85 * sin(a)
        c.create_line(cx, cy, x, y, fill="#F9FAFB", width=3)
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#F9FAFB", outline="#F9FAFB")

        if self._timer.running and rem <= 0.0:
            self._timer.running = False
            self._timer.start_monotonic = 0.0
            self._timer.elapsed_seconds = self._timer.duration_seconds
            messagebox.showinfo("Temporizador", "¡Temporizador finalizado!")

        self.root.after(200, self._loop_timer)


def run_tk() -> None:
    ctx = build_context()
    TkApp(ctx).run()
