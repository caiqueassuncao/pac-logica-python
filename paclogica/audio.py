import os
import pygame


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.load_sounds()

        except pygame.error:
            self.enabled = False

    def load_sounds(self):
        project_dir = os.path.dirname(os.path.dirname(__file__))
        sound_dir = os.path.join(project_dir, "assets", "sounds")

        sound_files = {
            "start": "start.wav",
            "collect": "collect.wav",
            "correct": "correct.wav",
            "wrong": "wrong.wav",
            "damage": "damage.wav",
            "victory": "victory.wav",
            "game_over": "game_over.wav",
        }

        for name, filename in sound_files.items():
            path = os.path.join(sound_dir, filename)

            if os.path.isfile(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    print(f"Erro ao carregar o áudio: {filename}")

    def play(self, name):
        if not self.enabled:
            return

        sound = self.sounds.get(name)

        if sound:
            sound.play()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()
        return self.enabled

    def set_volume(self, volume):
        volume = max(0.0, min(1.0, volume))

        for sound in self.sounds.values():
            sound.set_volume(volume)