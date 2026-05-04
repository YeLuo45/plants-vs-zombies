import pygame
import numpy as np
import time as time_module

# Music note frequencies (A4 = 440 Hz)
def note_freq(n):
    return 440.0 * (2.0 ** (n / 12.0))

# Note numbers relative to C4
C4, D4, E4, F4, G4, A4, B4 = 0, 2, 4, 5, 7, 9, 11
C5, D5, E5, F5, G5, A5, B5 = 12, 14, 16, 17, 19, 21, 23
Bb4 = 10
Eb4 = 3
REST = -999


class SoundManager:
    _instance = None

    def __init__(self):
        if SoundManager._instance is not None:
            return
        SoundManager._instance = self
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        self.sounds = {}
        self.sfx_volume = 0.8
        self.music_volume = 0.7
        self._load_volume_settings()
        self._generate_sounds()
        self._generate_music()

        # Music channels (stereo for music)
        try:
            self.music_channel = pygame.mixer.Channel(1)
            self.music_channel.set_volume(self.music_volume)
        except Exception:
            self.music_channel = None

        self.current_music = None

    def _load_volume_settings(self):
        try:
            import os, json
            sf = os.path.expanduser('~/.hermes/prj-plants-vs-zombies/settings.json')
            if os.path.exists(sf):
                with open(sf) as f:
                    d = json.load(f)
                self.sfx_volume = d.get('sfx_volume', 0.8)
                self.music_volume = d.get('music_volume', 0.7)
        except Exception:
            pass

    def apply_volume_settings(self):
        self._load_volume_settings()
        if self.music_channel:
            self.music_channel.set_volume(self.music_volume)

    @staticmethod
    def get_instance():
        if SoundManager._instance is None:
            SoundManager()
        return SoundManager._instance

    # ========== MUSIC GENERATION ==========
    def _generate_music(self):
        """Generate all background music tracks."""
        self.music_tracks = {}

        self.music_tracks['menu'] = self._make_track(
            self._menu_melody(), bpm=120, loop=True
        )
        self.music_tracks['adventure'] = self._make_track(
            self._adventure_melody(), bpm=100, loop=True
        )
        self.music_tracks['endless'] = self._make_track(
            self._endless_melody(), bpm=130, loop=True
        )
        self.music_tracks['zen'] = self._make_track(
            self._zen_melody(), bpm=60, loop=True
        )
        self.music_tracks['bowling'] = self._make_track(
            self._bowling_melody(), bpm=140, loop=True
        )

    def _note_to_freq(self, n):
        if n == REST:
            return 0
        return note_freq(n)

    def _make_track(self, pattern, bpm, loop=True):
        """Convert a pattern of (note_offset, note_num, duration_beats) into a pygame Sound."""
        beat_duration = 60.0 / bpm
        sample_rate = 22050
        channels = 2

        total_beats = sum(d for _, _, d in pattern)
        total_seconds = total_beats * beat_duration
        n_samples = int(total_seconds * sample_rate)

        # Stereo buffer
        left = np.zeros(n_samples, dtype=np.float32)
        right = np.zeros(n_samples, dtype=np.float32)

        for note_offset, note_num, duration_beats in pattern:
            start_beat = note_offset
            start_sample = int(start_beat * beat_duration * sample_rate)
            n_note_samples = int(duration_beats * beat_duration * sample_rate)

            if start_sample >= n_samples:
                continue

            freq = self._note_to_freq(note_num)
            if freq > 0:
                t = np.linspace(0, n_note_samples / sample_rate, n_note_samples, dtype=np.float32)
                # Soft piano-like tone (sine + harmonic)
                tone = np.sin(2 * np.pi * freq * t) * 0.5
                tone += np.sin(2 * np.pi * freq * 2 * t) * 0.15
                tone += np.sin(2 * np.pi * freq * 0.5 * t) * 0.1
                # ADSR envelope
                attack = int(n_note_samples * 0.05)
                decay = int(n_note_samples * 0.1)
                sustain_level = 0.7
                release_start = int(n_note_samples * 0.7)
                env = np.ones(n_note_samples, dtype=np.float32)
                env[:attack] = np.linspace(0, 1, attack)
                env[attack:attack+decay] = np.linspace(1, sustain_level, decay)
                env[release_start:] = np.linspace(sustain_level, 0, n_note_samples - release_start)
                tone *= env
                tone *= 0.3

                end = min(start_sample + n_note_samples, n_samples)
                actual_len = end - start_sample
                left[start_sample:end] += tone[:actual_len]
                right[start_sample:end] += tone[:actual_len]

        # Normalize
        max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 0.001)
        left = left / max_val * 0.7
        right = right / max_val * 0.7

        # Convert to stereo int16 interleaved
        left_i = (left * 32767).astype(np.int16)
        right_i = (right * 32767).astype(np.int16)
        stereo = np.empty((n_samples, 2), dtype=np.int16)
        stereo[:, 0] = left_i
        stereo[:, 1] = right_i

        sound = pygame.mixer.Sound(buffer=stereo)
        sound.set_volume(self.music_volume)
        return sound

    def _menu_melody(self):
        """Cheerful C major bounce - 'Don't Panic' inspired."""
        b = 0
        pattern = []
        # Phrase 1: C-E-G-C (arpeggio up)
        for n, d in [(C4, 0.25), (E4, 0.25), (G4, 0.25), (C5, 0.5)]:
            pattern.append((b, n, d)); b += d
        # Phrase 2: walk down
        for n, d in [(B4, 0.25), (A4, 0.25), (G4, 0.5)]:
            pattern.append((b, n, d)); b += d
        # Phrase 3: G-C-E-G (ascending)
        for n, d in [(G4, 0.25), (C5, 0.25), (E5, 0.25), (G5, 0.5)]:
            pattern.append((b, n, d)); b += d
        # Phrase 4: resolve
        for n, d in [(E5, 0.25), (D5, 0.25), (C5, 0.5)]:
            pattern.append((b, n, d)); b += d
        # Bar 3: dotted rhythm
        for n, d in [(C4, 0.75), (G4, 0.25), (A4, 0.5), (G4, 0.5)]:
            pattern.append((b, n, d)); b += d
        # Bar 4: C chord resolution
        for n, d in [(C5, 0.5), (G4, 0.5), (C4, 1.0)]:
            pattern.append((b, n, d)); b += d
        # Repeat bars 1-4
        bar1_4 = pattern[:]
        for po, pn, pd in bar1_4:
            pattern.append((b + po, pn, pd))
        return pattern

    def _adventure_melody(self):
        """Energetic adventure theme - building tension."""
        b = 0
        pattern = []
        # Main theme - ascending energy
        notes = [
            (G4, 0.5), (A4, 0.5), (B4, 0.5), (C5, 0.5),
            (D5, 0.5), (E5, 0.5), (D5, 0.5), (C5, 0.5),
            (B4, 0.5), (A4, 0.5), (G4, 0.5), (REST, 0.5),
            (C5, 0.25), (B4, 0.25), (A4, 0.25), (G4, 0.25),
            (A4, 0.25), (B4, 0.25), (C5, 0.25), (D5, 0.25),
            (E5, 0.5), (D5, 0.5), (C5, 1.0),
            (G4, 0.5), (REST, 0.25), (G4, 0.25), (A4, 0.5), (G4, 0.5),
            (C5, 0.5), (REST, 0.5), (G4, 1.0),
        ]
        for n, d in notes:
            pattern.append((b, n, d)); b += d
        # Repeat
        base = b
        for po, pn, pd in pattern[:]:
            pattern.append((b + po, pn, pd))
        return pattern

    def _endless_melody(self):
        """Tense, urgent endless theme."""
        b = 0
        pattern = []
        # Tense motif - minor key, driving
        notes = [
            # Motif A
            (G4, 0.25), (Bb4, 0.25), (C5, 0.25), (Bb4, 0.25),
            (A4, 0.25), (G4, 0.25), (F4, 0.25), (G4, 0.25),
            # Motif B
            (A4, 0.25), (C5, 0.25), (D5, 0.25), (C5, 0.25),
            (Bb4, 0.25), (A4, 0.25), (G4, 0.25), (F4, 0.25),
            # Climax
            (C5, 0.5), (D5, 0.25), (Eb4, 0.25), (E4, 0.5),
            (F4, 0.25), (G4, 0.25), (A4, 0.5), (G4, 0.5),
            # Cool down
            (F4, 0.5), (REST, 0.25), (G4, 0.25), (F4, 0.5),
            (G4, 0.25), (A4, 0.25), (Bb4, 0.5), (A4, 0.5),
            (G4, 1.0), (REST, 0.5),
        ]
        for n, d in notes:
            pattern.append((b, n, d)); b += d
        # Repeat
        for po, pn, pd in pattern[:]:
            pattern.append((b + po, pn, pd))
        return pattern

    def _zen_melody(self):
        """Peaceful zen garden - pentatonic, slow, dreamy."""
        b = 0
        pattern = []
        # Pentatonic C: C D E G A
        notes = [
            # Soft ascending pattern
            (C4, 1.0), (E4, 1.0), (G4, 1.0), (A4, 1.0),
            (G4, 1.5), (E4, 0.5), (C4, 1.0),
            (D4, 1.0), (E4, 1.0), (G4, 1.0), (A4, 1.0),
            (C5, 1.5), (G4, 0.5), (E4, 1.0),
            (A4, 1.0), (G4, 1.0), (E4, 1.0), (D4, 1.0),
            (C4, 2.0), (REST, 1.0),
            (E4, 1.0), (G4, 1.0), (A4, 1.0), (C5, 1.0),
            (G4, 1.5), (E4, 0.5), (D4, 1.0),
            (C4, 2.0), (REST, 2.0),
        ]
        for n, d in notes:
            pattern.append((b, n, d)); b += d
        # Repeat
        for po, pn, pd in pattern[:]:
            pattern.append((b + po, pn, pd))
        return pattern

    def _bowling_melody(self):
        """Upbeat bowling fun - major key, energetic."""
        b = 0
        pattern = []
        notes = [
            # Main jingle
            (C4, 0.25), (C4, 0.25), (G4, 0.5), (C5, 0.5),
            (B4, 0.25), (A4, 0.25), (G4, 0.5), (F4, 0.25), (F4, 0.25),
            (E4, 0.25), (E4, 0.25), (D4, 0.5), (G4, 0.5),
            # Variation
            (C4, 0.25), (D4, 0.25), (E4, 0.25), (F4, 0.25),
            (G4, 0.25), (A4, 0.25), (B4, 0.25), (C5, 0.25),
            (D5, 0.5), (C5, 0.25), (B4, 0.25), (A4, 0.5), (G4, 0.5),
            # Second phrase
            (F4, 0.25), (E4, 0.25), (D4, 0.25), (C4, 0.25),
            (G4, 0.5), (F4, 0.25), (E4, 0.25), (D4, 0.5),
            (C4, 0.5), (REST, 0.25), (C4, 0.25), (D4, 0.25), (E4, 0.25),
            (F4, 0.25), (G4, 0.25), (A4, 0.25), (B4, 0.25),
            (C5, 0.5), (G4, 0.5), (C4, 1.0),
        ]
        for n, d in notes:
            pattern.append((b, n, d)); b += d
        # Repeat
        for po, pn, pd in pattern[:]:
            pattern.append((b + po, pn, pd))
        return pattern

    # ========== SFX ==========
    def _generate_tone(self, freq, duration_ms, volume=0.3, fade_out=True):
        try:
            import numpy as np
        except ImportError:
            return None
        n_samples = int(22050 * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, dtype=np.float32)
        samples = np.sin(2 * np.pi * freq * t) * 0.6
        samples += np.sin(2 * np.pi * freq * 2 * t) * 0.2
        samples += np.sin(2 * np.pi * freq * 0.5 * t) * 0.2
        if fade_out:
            envelope = np.linspace(1.0, 0.0, n_samples)
            samples *= envelope
        samples = (samples * volume * 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=samples)

    def _generate_chomper_chomp(self):
        try:
            import numpy as np
        except ImportError:
            return None
        n_samples = int(22050 * 0.3 / 1000)
        t = np.linspace(0, 0.3, n_samples, dtype=np.float32)
        env1 = np.zeros(n_samples)
        env1[:n_samples//4] = np.linspace(0, 1, n_samples//4)
        env1[n_samples//4:n_samples//2] = np.linspace(1, 0, n_samples//4)
        env1[n_samples//2:3*n_samples//4] = np.linspace(0, 1, n_samples//4)
        env1[3*n_samples//4:] = np.linspace(1, 0, n_samples//4)
        samples = np.sin(2 * np.pi * 120 * t) * env1
        samples += np.sin(2 * np.pi * 80 * t) * env1 * 0.5
        samples = (samples * 0.4 * 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=samples)

    def _generate_laugh(self):
        try:
            import numpy as np
        except ImportError:
            return None
        n_samples = int(22050 * 0.5 / 1000)
        t = np.linspace(0, 0.5, n_samples, dtype=np.float32)
        freq = np.linspace(400, 80, n_samples)
        samples = np.sin(2 * np.pi * freq * t)
        envelope = np.linspace(1.0, 0.0, n_samples)
        samples *= envelope
        samples = (samples * 0.4 * 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=samples)

    def _generate_sounds(self):
        if not self.enabled:
            return
        try:
            import numpy as np
        except ImportError:
            self.enabled = False
            return

        self.sounds['shoot'] = self._generate_tone(600, 80, volume=0.2)
        self.sounds['sun_collect'] = self._generate_tone(880, 80, volume=0.2)
        self.sounds['plant'] = self._generate_tone(200, 100, volume=0.25)
        self.sounds['zombie_hit'] = self._generate_tone(150, 60, volume=0.15)
        self.sounds['zombie_groan'] = self._generate_tone(100, 300, volume=0.15)
        self.sounds['explode'] = self._generate_laugh()
        self.sounds['sun_appear'] = self._generate_tone(880, 80, volume=0.15)
        self.sounds['chomper'] = self._generate_chomper_chomp()
        self.sounds['click'] = self._generate_tone(440, 60, volume=0.15)
        self.sounds['lawnmower'] = self._generate_tone(200, 100, volume=0.25)

        # Victory: triumphant arpeggio
        victory_sounds = []
        for freq in [523, 659, 784, 1047]:
            snd = self._generate_tone(freq, 250, volume=0.2)
            if snd:
                victory_sounds.append(snd)
        self.sounds['victory'] = victory_sounds

        # Game over: descending sad tones
        defeat_sounds = []
        for freq in [392, 349, 311, 261]:
            snd = self._generate_tone(freq, 400, volume=0.2)
            if snd:
                defeat_sounds.append(snd)
        self.sounds['gameover'] = defeat_sounds

    # ========== PLAYBACK ==========
    def play(self, name, volume=1.0):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        effective = volume * self.sfx_volume
        if isinstance(sound, list):
            for snd in sound:
                snd.set_volume(effective)
                snd.play()
        else:
            sound.set_volume(effective)
            sound.play()

    def play_music(self, mode):
        """Play background music for given mode. None to stop."""
        if not self.enabled or not self.music_channel:
            return
        if mode == self.current_music:
            return
        self.stop_music()
        if mode is None:
            return
        track = self.music_tracks.get(mode)
        if track is None:
            return
        self.current_music = mode
        self.music_channel.set_volume(self.music_volume)
        self.music_channel.play(track, loops=-1)

    def stop_music(self):
        if self.current_music and self.music_channel:
            self.music_channel.stop()
        self.current_music = None

    def stop_all(self):
        if not self.enabled:
            return
        pygame.mixer.stop()
