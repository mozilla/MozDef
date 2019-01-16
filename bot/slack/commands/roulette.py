import random


class Command():
    def __init__(self):
        self.command_name = '!r'
        self.help_text = 'Play a game of Russian Roulette'
        self.gun_max_load = 6
        self.gun_bullet_slot = random.randint(1, self.gun_max_load)
        self.gun_current_slot = 0

    def handle_command(self, parameters):
        response = ""
        self.gun_current_slot = self.gun_current_slot + 1
        if self.gun_current_slot == self.gun_max_load:
            response = "I'm not gonna kill you this time... another try?"
            self.gun_bullet_slot = random.randint(1, self.gun_max_load)
            self.gun_current_slot = 0
        if self.gun_current_slot == self.gun_bullet_slot:
            response = "*BANG* - You're dead!"
            self.gun_bullet_slot = random.randint(1, self.gun_max_load)
            self.gun_current_slot = 0
        else:
            response = "*click* (slot {0})".format(self.gun_current_slot)
        return response
