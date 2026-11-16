
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import math
import array
import configparser
import subprocess
from pathlib import Path

import pygame
import pystray
from PIL import Image, ImageDraw


class ShutdownTimer:

    def __init__(self, root):
        self.root = root
        self.root.title("Apagado Automático 2.0")
        self.root.geometry("430x220")
        self.root.resizable(False, False)

        self.running = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.deadline = 0
        self.warning_shown = False
        self.timer_job = None
        self.warning_window = None
        self.icon = None
        self.closed = False

        # Configuración
        self.config_dir = Path.home() / ".config" / "apagado-automatico"
        self.config_file = self.config_dir / "config.ini"

        self.sound_path = None
        self.alert_sound = None

        self.load_config()
        self.init_sound()

        # ---------------- INTERFAZ ----------------

        frame_time = tk.Frame(root)
        frame_time.pack(pady=10)

        tk.Label(frame_time, text="Horas:").grid(
            row=0, column=0, padx=5
        )

        self.hours = tk.Spinbox(
            frame_time, from_=0, to=23, width=5
        )
        self.hours.grid(row=0, column=1, padx=5)

        tk.Label(frame_time, text="Minutos:").grid(
            row=0, column=2, padx=5
        )

        self.minutes = tk.Spinbox(
            frame_time, from_=0, to=59, width=5
        )
        self.minutes.grid(row=0, column=3, padx=5)

        frame_action = tk.Frame(root)
        frame_action.pack(pady=5)

        tk.Label(
            frame_action, text="Acción al finalizar:"
        ).pack(side=tk.LEFT, padx=5)

        self.action_var = tk.StringVar(value="Apagar")

        self.actions = [
            "Apagar",
            "Reiniciar",
            "Suspender",
            "Hibernar"
        ]

        self.action_menu = ttk.Combobox(
            frame_action,
            textvariable=self.action_var,
            values=self.actions,
            state="readonly",
            width=12
        )
        self.action_menu.pack(side=tk.LEFT, padx=5)

        self.action_menu.bind(
            "<<ComboboxSelected>>",
            self.save_config
        )

        self.time_label = tk.Label(
            root,
            text="Tiempo restante: 00:00:00",
            font=("Arial", 12)
        )
        self.time_label.pack(pady=10)

        self.progress = ttk.Progressbar(
            root,
            length=250,
            mode="determinate"
        )
        self.progress.pack(pady=10)

        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)

        self.start_button = tk.Button(
            frame_buttons,
            text="Iniciar cuenta atrás",
            command=self.start_countdown
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(
            frame_buttons,
            text="Detener",
            command=self.stop_countdown,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.minimize_button = tk.Button(
            frame_buttons,
            text="Minimizar",
            command=self.minimize_to_tray
        )
        self.minimize_button.grid(row=0, column=2, padx=5)

        # Recuperar configuración anterior
        self.hours.delete(0, tk.END)
        self.hours.insert(0, str(self.saved_hours))

        self.minutes.delete(0, tk.END)
        self.minutes.insert(0, str(self.saved_minutes))

        self.action_var.set(self.saved_action)

        # Cerrar ventana
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.quit_app
        )

    # ---------------- CONFIGURACIÓN ----------------

    def load_config(self):

        self.saved_hours = 0
        self.saved_minutes = 30
        self.saved_action = "Apagar"

        config = configparser.ConfigParser()

        try:
            if self.config_file.exists():
                config.read(self.config_file, encoding="utf-8")

                if config.has_section("General"):

                    self.saved_hours = config.getint(
                        "General", "hours", fallback=0
                    )

                    self.saved_minutes = config.getint(
                        "General", "minutes", fallback=30
                    )

                    self.saved_action = config.get(
                        "General", "action", fallback="Apagar"
                    )

        except (ValueError, configparser.Error, OSError):
            pass

        self.saved_hours = max(0, min(23, self.saved_hours))
        self.saved_minutes = max(0, min(59, self.saved_minutes))

        if self.saved_action not in [
            "Apagar", "Reiniciar", "Suspender", "Hibernar"
        ]:
            self.saved_action = "Apagar"

    def save_config(self, event=None):

        config = configparser.ConfigParser()

        config["General"] = {
            "hours": self.hours.get(),
            "minutes": self.minutes.get(),
            "action": self.action_var.get()
        }

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as file:
                config.write(file)

        except OSError as e:
            print("Error guardando configuración:", e)

    # ---------------- SONIDO ----------------

    def init_sound(self):

        try:
            pygame.mixer.init(
                frequency=22050,
                size=-16,
                channels=1
            )

            if self.sound_path:
                self.alert_sound = pygame.mixer.Sound(
                    self.sound_path
                )
            else:
                # Generar tono de 440 Hz durante medio segundo
                rate = 22050
                duration = 0.5

                samples = array.array(
                    "h",
                    (
                        int(
                            10000 *
                            math.sin(2 * math.pi * 440 * i / rate) *
                            min(1, i / 500, (rate * duration - i) / 500)
                        )
                        for i in range(int(rate * duration))
                    )
                )

                self.alert_sound = pygame.mixer.Sound(
                    buffer=samples.tobytes()
                )

        except Exception as e:
            print("No se pudo inicializar el sonido:", e)
            self.alert_sound = None

    def play_sound(self):

        try:
            if self.alert_sound:
                self.alert_sound.play()
            else:
                self.root.bell()

        except Exception as e:
            print("Error reproduciendo sonido:", e)

    # ---------------- CUENTA REGRESIVA ----------------

    def start_countdown(self):

        if self.running:
            return

        try:
            hours = int(self.hours.get())
            minutes = int(self.minutes.get())

            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Error",
                "Introduce un tiempo válido.",
                parent=self.root
            )
            return

        total = hours * 3600 + minutes * 60

        if total == 0:
            messagebox.showwarning(
                "Advertencia",
                "Selecciona un tiempo mayor que cero.",
                parent=self.root
            )
            return

        self.save_config()

        self.total_seconds = total
        self.remaining_seconds = total
        self.deadline = time.monotonic() + total

        self.warning_shown = False
        self.running = True

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.progress["maximum"] = total
        self.progress["value"] = 0

        self.update_countdown()

    def update_countdown(self):

        if not self.running or self.closed:
            return

        self.remaining_seconds = max(
            0,
            math.ceil(self.deadline - time.monotonic())
        )

        remaining = self.remaining_seconds

        mins, secs = divmod(remaining, 60)
        hrs, mins = divmod(mins, 60)

        self.time_label.config(
            text=f"Tiempo restante: {hrs:02}:{mins:02}:{secs:02}"
        )

        elapsed = self.total_seconds - remaining

        self.progress["value"] = elapsed

        # Advertencia 30 segundos antes
        if remaining <= 30 and not self.warning_shown:
            self.warning_shown = True
            self.play_sound()
            self.show_warning_popup()

        # Finalizar cuenta regresiva
        if remaining <= 0:

            self.running = False
            self.timer_job = None

            self.close_warning_popup()

            self.time_label.config(
                text="Tiempo restante: 00:00:00"
            )

            self.progress["value"] = self.total_seconds

            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

            self.execute_action()
            return

        # Actualización periódica sin hilos secundarios
        self.timer_job = self.root.after(
            250,
            self.update_countdown
        )

    # ---------------- ADVERTENCIA FINAL ----------------

    def show_warning_popup(self):

        # Restaurar ventana si estaba minimizada
        self.restore_window()

        self.warning_window = tk.Toplevel(self.root)

        self.warning_window.title("¡Atención!")
        self.warning_window.geometry("340x150")
        self.warning_window.resizable(False, False)

        self.warning_window.transient(self.root)

        tk.Label(
            self.warning_window,
            text="¡Atención!",
            font=("Arial", 13, "bold")
        ).pack(pady=10)

        tk.Label(
            self.warning_window,
            text=(
                f"Se ejecutará la acción: {self.action_var.get()}\n"
                "El sistema actuará en 30 segundos."
            ),
            justify="center"
        ).pack(pady=5)

        tk.Button(
            self.warning_window,
            text="Cancelar cuenta atrás",
            command=self.stop_countdown
        ).pack(pady=10)

        self.warning_window.protocol(
            "WM_DELETE_WINDOW",
		self.close_warning_popup
        )

        self.warning_window.lift()

    def close_warning_popup(self):

        if self.warning_window:

            try:
                self.warning_window.destroy()
            except tk.TclError:
                pass

            self.warning_window = None

    # ---------------- DETENER ----------------

    def stop_countdown(self):

        self.running = False

        if self.timer_job is not None:

            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass

            self.timer_job = None

        self.close_warning_popup()

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.progress["value"] = 0

        self.time_label.config(
            text="Tiempo restante: 00:00:00"
        )

    # ---------------- ACCIONES DEL SISTEMA ----------------

    def execute_action(self):

        commands = {
            "Apagar": ["systemctl", "poweroff"],
            "Reiniciar": ["systemctl", "reboot"],
            "Suspender": ["systemctl", "suspend"],
            "Hibernar": ["systemctl", "hibernate"]
        }

        action = self.action_var.get()
        command = commands.get(action)

        if not command:
            return

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:

                error = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "El sistema rechazó la operación."
                )

                messagebox.showerror(
                    "Error ejecutando acción",
                    f"No se pudo ejecutar: {action}\n\n{error}",
                    parent=self.root
                )

        except subprocess.TimeoutExpired:

            messagebox.showerror(
                "Error",
                "El comando del sistema tardó demasiado.",
                parent=self.root
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e),
                parent=self.root
            )

    # ---------------- BANDEJA DEL SISTEMA ----------------

    def minimize_to_tray(self):

        if self.icon is not None:
            self.root.withdraw()
            return

        image = Image.new(
            "RGB",
            (64, 64),
            (50, 50, 50)
        )

        draw = ImageDraw.Draw(image)

        draw.rectangle(
            (16, 16, 48, 48),
            fill=(0, 200, 0)
        )

        menu = pystray.Menu(
            pystray.MenuItem(
                "Restaurar",
                self.tray_restore,
                default=True
            ),
            pystray.MenuItem(
                "Salir",
                self.tray_quit
            )
        )

        self.icon = pystray.Icon(
            "apagado-automatico",
            image,
            "Apagado Automático 2.0",
            menu
        )

        self.root.withdraw()

        threading.Thread(
            target=self.run_tray_icon,
            args=(self.icon,),
            daemon=True
        ).start()

    def run_tray_icon(self, icon):

        try:
            icon.run()
        except Exception as e:
            print("Error en bandeja del sistema:", e)

    def tray_restore(self, icon=None, item=None):

        try:
            self.root.after(0, self.restore_window)
        except tk.TclError:
            pass

    def tray_quit(self, icon=None, item=None):

        try:
            self.root.after(0, self.quit_app)
        except tk.TclError:
            pass

    def restore_window(self):

        if self.icon:

            try:
                self.icon.stop()
            except Exception:
                pass

            self.icon = None

        if not self.closed:

            self.root.deiconify()
            self.root.lift()

    # ---------------- SALIR ----------------

    def quit_app(self, icon=None, item=None):

        if self.closed:
            return

        self.closed = True
        self.running = False

        if self.timer_job is not None:

            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass

            self.timer_job = None

        self.close_warning_popup()
        self.save_config()

        if self.icon:

            try:
                self.icon.stop()
            except Exception:
                pass

            self.icon = None

        try:
            pygame.mixer.quit()
        except Exception:
            pass

        self.root.destroy()


# ---------------- INICIAR PROGRAMA ----------------

if __name__ == "__main__":

    root = tk.Tk()

    app = ShutdownTimer(root)

    root.mainloop()
