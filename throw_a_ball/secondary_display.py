"""Emulator-only window for the logical 64x32 secondary display."""
from __future__ import annotations

import tkinter as tk

from throw_a_ball.rendering import LOWER_HEIGHT, LOWER_RGB888_BYTE_LENGTH, LOWER_WIDTH


class SecondaryDisplayWindow:
    """Show RGB888 Screen 2 frames without depending on the cabinet SDK."""

    def __init__(self, scale: int = 8):
        self.scale = scale
        self._root = tk.Tk()
        self._root.title("Throw a Ball — Screen 2 (64×32)")
        self._root.resizable(False, False)
        self._image = tk.PhotoImage(width=LOWER_WIDTH, height=LOWER_HEIGHT)
        self._scaled = self._image.zoom(scale, scale)
        self._label = tk.Label(self._root, image=self._scaled, borderwidth=0)
        self._label.pack()
        self._closed = False
        self._root.protocol("WM_DELETE_WINDOW", self.close)

    def submit(self, frame: bytes) -> None:
        if self._closed:
            return
        if len(frame) != LOWER_RGB888_BYTE_LENGTH:
            raise ValueError("Screen 2 frame must be 64x32 RGB888")
        rows = []
        for y in range(LOWER_HEIGHT):
            colors = []
            for x in range(LOWER_WIDTH):
                offset = (y * LOWER_WIDTH + x) * 3
                colors.append("#%02x%02x%02x" % tuple(frame[offset:offset + 3]))
            rows.append("{" + " ".join(colors) + "}")
        try:
            self._image.put(" ".join(rows))
            self._scaled = self._image.zoom(self.scale, self.scale)
            self._label.configure(image=self._scaled)
            self._root.update_idletasks()
            self._root.update()
        except tk.TclError:
            self._closed = True

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            try:
                self._root.destroy()
            except tk.TclError:
                pass
