"""
NOSTROMO Media Terminal screen.
YouTube search & playback with background audio support.
Supports remote play via HTTP API (Nostromo Remote app).
"""

import os
import re
import sys
import json
import subprocess
import threading
import time
import queue as queue_mod
import pygame

from nostromo.screen import Screen
from nostromo.terminal import BaseTerminal
from nostromo.logger import SessionLogger
from nostromo import config as cfg
from nostromo import sound

# ─── Configuration ──────────────────────────────────────────────────────────

MAX_RESULTS = 15

COOKIES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "cookies.txt"
)

YT_FORMAT = (
    "b[vcodec~='^(avc|h264)'][height<=480]/b/"
    "bv[vcodec~='^(avc|h264)'][height<=480]+ba/"
    "bv[vcodec~='^(avc|h264)']+ba"
)

BOOT_LINES = [
    "",
    "  WEYLAND-YUTANI CORP.",
    "  MEDIA TERMINAL v2.37",
    "",
    "  NOSTROMO ENTERTAINMENT SYSTEM",
    "",
    "  SUBSPACE RECEIVER .. ONLINE",
    "  MEDIA DECODER ..... ONLINE",
    "  DISPLAY ADAPTER ... ONLINE",
    "",
    "  [ENTER] SEARCH/SELECT  [TAB] EN/RU",
    "  [PGUP/PGDN] SCROLL  [ESC] BACK",
    "  [CTRL+1/2/3/4] SWITCH  [CTRL+Q] EXIT",
    "",
    "  PLAYBACK: [SPACE] PAUSE  [Q] STOP",
    "  [LEFT/RIGHT] SEEK  [UP/DOWN] VOLUME",
    "",
]

OSD_BG = (0, 0, 0, 160)
OSD_TEXT = (51, 255, 0)
OSD_DIM = (20, 100, 0)


# ─── YouTube Backend ────────────────────────────────────────────────────────

def yt_search(query, max_results=MAX_RESULTS):
    """Search YouTube via yt-dlp.
    Returns (results_list, error_string_or_None).
    """
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json", "--flat-playlist",
        "--no-download",
    ]
    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Log stderr for debugging
        if result.stderr:
            stderr_short = result.stderr.strip()[-300:]
            print(f"[yt-dlp search] stderr: {stderr_short}", file=sys.stderr)

        if result.returncode != 0 and not result.stdout.strip():
            err = result.stderr.strip() if result.stderr else "unknown error"
            err_lines = [l for l in err.split("\n") if l.strip() and "WARNING" not in l]
            err_msg = err_lines[-1][:cfg.COLS - 10] if err_lines else "SEARCH FAILED"
            return [], err_msg

        results = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                results.append({
                    "title": data.get("title", "UNKNOWN").upper(),
                    "id": data.get("id", ""),
                    "duration": _fmt_duration(data.get("duration")),
                    "channel": data.get("channel", data.get("uploader", "")),
                    "duration_sec": data.get("duration", 0),
                })
            except json.JSONDecodeError:
                continue
        return results, None

    except subprocess.TimeoutExpired:
        return [], "SEARCH TIMEOUT (30S)"
    except FileNotFoundError:
        return [], "YT-DLP NOT FOUND"
    except Exception as e:
        return [], str(e)[:cfg.COLS - 10]


def yt_get_stream_url(video_id):
    """Get direct stream URL(s) via yt-dlp."""
    url = f"https://youtube.com/watch?v={video_id}"
    cmd = ["yt-dlp", "-f", YT_FORMAT, "--get-url", url]
    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None, (result.stderr or "format not available").strip()[-200:]
        urls = [u for u in result.stdout.strip().split("\n") if u]
        return urls, None
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return None, str(e)


def _fmt_duration(seconds):
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _extract_video_id(text):
    """Extract YouTube video ID from URL or raw 11-char ID."""
    patterns = [
        r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', text.strip()):
        return text.strip()
    return None


# ─── Video Player ───────────────────────────────────────────────────────────

class VideoPlayer:
    """Native video+audio player using ffpyplayer."""

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.player = None
        self.playing = False
        self.paused = False
        self.volume = 0.3
        self.muted = False
        self.duration = 0
        self.position = 0
        self.error = None
        self.decode_video = False  # enabled by on_activate(), off by default for thread safety

        # OSD
        self._osd_visible = True
        self._osd_timer = 0
        self._osd_timeout = 3000

        # Thread-safe frame sharing
        self._current_surface = None
        self._lock = threading.Lock()
        self._decoder_thread = None

    def start(self, stream_urls, duration_sec=0):
        from ffpyplayer.player import MediaPlayer

        # Stop previous playback cleanly before starting new one
        if self.playing or self.player:
            self.stop()

        self.duration = duration_sec
        self.error = None
        self.paused = False
        self._current_surface = None

        video_url = stream_urls[0]

        ff_opts = {
            'paused': False,
            'volume': self.volume if not self.muted else 0.0,
            'out_fmt': 'rgb24',
        }

        if len(stream_urls) > 1:
            ff_opts['audio_file'] = stream_urls[1]
            print(f"[player] separate audio stream", file=sys.stderr)
        else:
            print(f"[player] merged audio+video stream", file=sys.stderr)

        try:
            if pygame.mixer.get_init():
                sound.quit()
                pygame.mixer.quit()
                time.sleep(0.1)
            self.player = MediaPlayer(video_url, ff_opts=ff_opts)
            self.player.set_volume(self.volume)
            self.playing = True
            self._osd_timer = pygame.time.get_ticks()
            self._osd_visible = True
            print(f"[player] started OK", file=sys.stderr)

            self._decoder_thread = threading.Thread(
                target=self._decode_loop, daemon=True
            )
            self._decoder_thread.start()

        except Exception as e:
            self.error = str(e)
            self.playing = False
            print(f"[player] ERROR: {e}", file=sys.stderr)

    def _decode_loop(self):
        player = self.player  # local ref — avoid race with stop()
        while self.playing and player:
            try:
                frame, val = player.get_frame()
            except Exception:
                break

            if not self.playing:
                break

            if val == 'eof':
                self.playing = False
                break

            if frame is not None:
                img, pts = frame
                self.position = pts

                if self.decode_video:
                    try:
                        w, h = img.get_size()
                        data = bytes(img.to_bytearray()[0])
                        surf = pygame.image.frombuffer(data, (w, h), 'RGB')
                        scale_fn = max if cfg.VIDEO_SCALE == "fill" else min
                        scale = scale_fn(self.screen_w / w, self.screen_h / h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        scaled = pygame.transform.scale(surf, (new_w, new_h))

                        with self._lock:
                            self._current_surface = (scaled, new_w, new_h)
                    except Exception:
                        pass

            if isinstance(val, (int, float)) and val > 0:
                time.sleep(val)
            else:
                time.sleep(0.001)

    def stop(self):
        self.playing = False
        if self._decoder_thread:
            self._decoder_thread.join(timeout=2)
            self._decoder_thread = None
        if self.player:
            self.player.close_player()
            self.player = None
        with self._lock:
            self._current_surface = None
        # Re-init mixer for terminal sounds
        sound.reinit()

    def toggle_pause(self):
        if self.player:
            self.player.toggle_pause()
            self.paused = not self.paused
            self._show_osd()

    def seek(self, delta_sec):
        if self.player:
            self.player.seek(delta_sec, relative=True)
            self._show_osd()

    def set_volume(self, delta):
        self.volume = max(0.0, min(1.0, self.volume + delta))
        if self.player and not self.muted:
            self.player.set_volume(self.volume)
        self._show_osd()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.player:
            self.player.set_volume(0.0 if self.muted else self.volume)
        self._show_osd()

    def _show_osd(self):
        self._osd_visible = True
        self._osd_timer = pygame.time.get_ticks()

    def render(self, screen, font):
        screen.fill((0, 0, 0))

        with self._lock:
            frame_data = self._current_surface

        if frame_data:
            surface, w, h = frame_data
            x = (self.screen_w - w) // 2
            y = (self.screen_h - h) // 2
            screen.blit(surface, (x, y))

        now = pygame.time.get_ticks()
        if self._osd_visible and now - self._osd_timer > self._osd_timeout:
            self._osd_visible = False
        if self.paused:
            self._osd_visible = True
        if self._osd_visible:
            self._render_osd(screen, font)

    def _render_osd(self, screen, font):
        bar_h = 30
        osd_surf = pygame.Surface((self.screen_w, bar_h), pygame.SRCALPHA)
        osd_surf.fill(OSD_BG)
        y_offset = 4

        status = "|| " if self.paused else "> "
        s = font.render(status, True, OSD_TEXT)
        osd_surf.blit(s, (8, y_offset))

        pos_str = _fmt_duration(self.position) or "0:00"
        dur_str = _fmt_duration(self.duration) or "?"
        s = font.render(f"{pos_str} / {dur_str}", True, OSD_TEXT)
        osd_surf.blit(s, (40, y_offset))

        vol_str = "MUTE" if self.muted else f"VOL {int(self.volume * 100)}%"
        s = font.render(vol_str, True, OSD_DIM)
        osd_surf.blit(s, (self.screen_w - s.get_width() - 8, y_offset))

        screen.blit(osd_surf, (0, self.screen_h - bar_h))

        if self.duration > 0:
            bar_y = self.screen_h - bar_h - 3
            bar_w = self.screen_w - 16
            progress = min(1.0, self.position / self.duration)
            pygame.draw.rect(screen, OSD_DIM, (8, bar_y, bar_w, 2))
            pygame.draw.rect(screen, OSD_TEXT,
                             (8, bar_y, int(bar_w * progress), 2))


# ─── Media Terminal ─────────────────────────────────────────────────────────

class MediaTerminal(BaseTerminal):
    """YouTube search & playback terminal."""

    def __init__(self, renderer, logger):
        super().__init__(renderer, boot_lines=BOOT_LINES, prompt="SEARCH> ",
                         history_name="ytplay")
        self.logger = logger
        self.results = []
        self._search_thread = None
        self._search_results = None
        self._search_error = None
        self._searching = False
        self._resolving = False
        self._resolve_thread = None
        self._resolve_result = None
        self._resolve_video = None
        self._play_queue = queue_mod.Queue()
        self.video_player = VideoPlayer(cfg.SCREEN_W, cfg.SCREEN_H)

    def on_boot_complete(self):
        self.logger.log_boot()

    def queue_play(self, video_id, url=""):
        """Thread-safe: queue a video for playback (called from API)."""
        self._play_queue.put((video_id, url))

    def on_submit(self, query):
        if self.results and query.isdigit():
            num = int(query)
            if 1 <= num <= len(self.results):
                self._start_resolve(num - 1)
                return
            else:
                self.add_line(f"  INVALID SELECTION: {num}")
                self.add_line("")
                return

        # Direct URL or video ID
        video_id = _extract_video_id(query)
        if video_id:
            self._start_resolve_by_id(video_id, query)
            return

        self._start_search(query)

    def _start_search(self, query):
        self.logger.log_event("SEARCH", query)
        self.results = []
        self._searching = True
        self._search_error = None
        self.set_busy(True)
        self._working_dots = 0
        self._last_dot_time = pygame.time.get_ticks()
        self._search_results = None
        self._search_thread = threading.Thread(
            target=self._do_search, args=(query,), daemon=True
        )
        self._search_thread.start()

    def _do_search(self, query):
        results, error = yt_search(query)
        self._search_results = results
        self._search_error = error

    def _start_resolve(self, index):
        video = self.results[index]
        self.add_line(f"  LOADING: {video['title'][:cfg.COLS - 12]}")
        self.add_line("")
        self.logger.log_event("PLAY", f"{video['title']} [{video['id']}]")
        self._resolving = True
        self._resolve_video = video
        self.set_busy(True)
        self._working_dots = 0
        self._last_dot_time = pygame.time.get_ticks()
        self._resolve_result = None
        self._resolve_thread = threading.Thread(
            target=self._do_resolve, args=(video["id"],), daemon=True
        )
        self._resolve_thread.start()

    def _start_resolve_by_id(self, video_id, display_text=""):
        """Resolve and play by video ID directly (no search)."""
        label = display_text[:cfg.COLS - 12] if display_text else video_id
        self.add_line(f"  DIRECT: {label}")
        self.add_line("")
        self.logger.log_event("DIRECT", video_id)
        self._resolving = True
        self._resolve_video = {
            "title": (display_text or video_id).upper(),
            "id": video_id,
            "duration_sec": 0,
        }
        self.set_busy(True)
        self._working_dots = 0
        self._last_dot_time = pygame.time.get_ticks()
        self._resolve_result = None
        self._resolve_thread = threading.Thread(
            target=self._do_resolve, args=(video_id,), daemon=True
        )
        self._resolve_thread.start()

    def _do_resolve(self, video_id):
        urls, error = yt_get_stream_url(video_id)
        if urls:
            print(f"[resolve] got {len(urls)} stream URL(s)", file=sys.stderr)
        self._resolve_result = (urls, error)

    def _show_results(self):
        self.add_line(f"  FOUND {len(self.results)} RESULTS:")
        self.add_line("")
        for i, v in enumerate(self.results):
            num = f"{i + 1:2d}."
            dur = f" [{v['duration']}]" if v['duration'] else ""
            title = v['title'][:cfg.COLS - len(num) - len(dur) - 2]
            self.add_line(f"  {num} {title}{dur}")
        self.add_line("")
        self.add_line("  ENTER NUMBER TO PLAY  [ESC] NEW SEARCH")
        self.add_line("")

    def handle_key(self, event):
        if self.video_player.playing:
            if event.key == pygame.K_SPACE:
                self.video_player.toggle_pause()
                return True
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.video_player.stop()
                self.add_line("  PLAYBACK STOPPED.")
                self.add_line("")
                return True
            elif event.key == pygame.K_LEFT:
                self.video_player.seek(-10)
                return True
            elif event.key == pygame.K_RIGHT:
                self.video_player.seek(10)
                return True
            elif event.key == pygame.K_UP:
                self.video_player.set_volume(0.1)
                return True
            elif event.key == pygame.K_DOWN:
                self.video_player.set_volume(-0.1)
                return True
            elif event.key == pygame.K_m:
                self.video_player.toggle_mute()
                return True
            return True

        if event.key == pygame.K_ESCAPE and self.idle:
            if self.results:
                self.results = []
                self.input_buf = ""
                self.add_line("  READY FOR NEW SEARCH.")
                self.add_line("")
                return True

        return super().handle_key(event)

    def update(self):
        super().update()

        # Check for remote play commands (from API)
        try:
            video_id, url = self._play_queue.get_nowait()
            if not self._resolving and not self._searching:
                self._start_resolve_by_id(video_id, url)
            else:
                # Re-queue if busy
                self._play_queue.put((video_id, url))
        except queue_mod.Empty:
            pass

        if self._searching and self._search_thread:
            if not self._search_thread.is_alive():
                self._search_thread = None
                self._searching = False
                self.set_busy(False)
                self.results = self._search_results or []
                if self.results:
                    self._show_results()
                elif self._search_error:
                    self.add_line(f"  ERROR: {self._search_error}")
                    self.add_line("")
                    self.logger.log_event("ERROR", self._search_error)
                else:
                    self.add_line("  NO RESULTS FOUND.")
                    self.add_line("")

        if self._resolving and self._resolve_thread:
            if not self._resolve_thread.is_alive():
                self._resolve_thread = None
                self._resolving = False
                self.set_busy(False)
                urls, error = self._resolve_result
                if urls:
                    dur = self._resolve_video.get("duration_sec", 0)
                    self.video_player.start(urls, dur)
                else:
                    self.add_line(f"  ERROR: {error[:cfg.COLS - 10]}")
                    self.add_line("")
                    self.logger.log_event("ERROR", error)

        if self.video_player.player and not self.video_player.playing:
            self.video_player.stop()
            self.add_line("  PLAYBACK COMPLETE.")
            self.add_line("")

    def render(self):
        if self.video_player.playing:
            screen = pygame.display.get_surface()
            if screen:
                self.video_player.render(screen, self.renderer.font)
            return

        if self._searching or self._resolving:
            r = self.renderer
            visible = self._get_visible_lines(self.output_rows - 1)
            for i, line in enumerate(visible):
                row = self.output_rows - 1 - len(visible) + i
                r.render_text_line(line, row)
            self.show_working()
        else:
            super().render()


# ─── Screen Adapter ─────────────────────────────────────────────────────────

class MediaScreen(Screen):
    """Screen adapter for media player."""

    def __init__(self):
        super().__init__("MEDIA", "C-3")
        self.terminal = None
        self.logger = None

    def init(self, renderer):
        super().init(renderer)
        self.logger = SessionLogger(app_name="ytplay")
        self.terminal = MediaTerminal(renderer, self.logger)
        print(f"[MEDIA] logging to: {self.logger.filepath}",
              file=sys.stderr)

    def handle_event(self, event):
        if self.terminal and event.type == pygame.KEYDOWN:
            return self.terminal.handle_key(event)
        return False

    def update(self):
        if self.terminal:
            self.terminal.update()

    def render(self):
        if self.terminal:
            self.terminal.render()

    def on_activate(self):
        super().on_activate()
        if self.terminal:
            self.terminal.video_player.decode_video = True

    @property
    def show_status_bar(self):
        if self.terminal and self.terminal.video_player.playing:
            return False
        return True

    def on_deactivate(self):
        super().on_deactivate()
        # Stop video decoding but keep audio playing
        if self.terminal and self.terminal.video_player.playing:
            self.terminal.video_player.decode_video = False

    def is_alive(self):
        """Keep updating while audio is playing or work is queued."""
        if self.terminal:
            vp = self.terminal.video_player
            if vp.playing:
                return True
            if self.terminal._searching or self.terminal._resolving:
                return True
            if not self.terminal._play_queue.empty():
                return True
        return False

    def cleanup(self):
        if self.terminal and self.terminal.video_player.playing:
            self.terminal.video_player.stop()
        if self.logger:
            self.logger.close()


def create():
    """Factory function."""
    return MediaScreen()
