import contextlib
import random
import threading

import numpy as np

with contextlib.redirect_stdout(None):
    # Pygame is noisy on load, for no good reason
    import pygame

from constants import Direction, Colors, Point

pygame.init()
font = pygame.font.Font(None, 24)
big_font = pygame.font.Font(None, 256)


class SnakeGame:
    def __init__(self, w: int = 1280, h: int = 720, fps: int = 2000, block_size: int = 32):
        # Set up the game
        self.w: int = w
        self.h: int = h
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()
        self.framerate: int = fps
        self.block_size: int = block_size
        self.round: int = 0
        self.paused: bool = False

        # Create attributes that will be set elsewhere
        self.direction = None
        self.head = None
        self.snake = None
        self.score = None
        self.food = None
        self.action_timeout = None

        # Initialize game
        self.reset()

    def reset(self):
        # Put the head in the center, whole snake facing to the right
        self.direction = Direction.RIGHT
        self.head = Point(self.w / 2 // self.block_size * self.block_size,
                          self.h / 2 // self.block_size * self.block_size)
        self.snake = [
            self.head,
            Point(self.head.x - self.block_size, self.head.y),
            Point(self.head.x - (2 * self.block_size), self.head.y)
        ]
        self.score = 0
        self.food = None
        self._place_food()
        self.action_timeout = 0
        self.round += 1

    def _place_food(self):
        # Regenerate food in a valid location
        self.food = self.snake[0]
        while self.food in self.snake:
            # Choose x/y within bounds of the game
            # TODO: Probably not performant later in the game - change this to choosing from a set
            x = random.randint(0, (self.w - self.block_size) // self.block_size) * self.block_size
            y = random.randint(0, (self.h - self.block_size) // self.block_size) * self.block_size
            self.food = Point(x, y)

    def play_action(self, action):
        for event in pygame.event.get():
            # Let user quit
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            keymap = pygame.key.get_pressed()
            if event.type == pygame.KEYDOWN:
                # Increase framerate
                if event.key in [pygame.K_w, pygame.K_UP]:
                    if keymap[pygame.K_RSHIFT] or keymap[pygame.K_LSHIFT]:
                        self.framerate += 10
                    else:
                        self.framerate += 1
                # Decrease framerate
                if event.key in [pygame.K_s, pygame.K_DOWN]:
                    if keymap[pygame.K_RSHIFT] or keymap[pygame.K_LSHIFT]:
                        self.framerate = max(1, self.framerate - 10)
                    else:
                        self.framerate = max(1, self.framerate - 1)
                # Allow pausing
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused

        if self.paused:
            # Update screen
            self.draw()
            self.clock.tick(self.framerate)
            return None

        # Snake is moving forward
        self.action_timeout += 1
        self._move(action)
        self.snake.insert(0, self.head)

        # Is the game over?
        reward = 0
        game_over = False
        if self.is_collision() or self.action_timeout > 50 * len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # Game is not over - snake ate food or simply moved
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            self.snake.pop()

        # Update screen
        self.draw()
        self.clock.tick(self.framerate)

        # Output results from this update
        return reward, game_over, self.score

    def is_collision(self, point=None):
        if point is None:
            point = self.head

        # Hit the edges?
        if point.x > self.w - self.block_size or point.x < 0 or point.y > self.h - self.block_size or point.y < 0:
            return True
        # Hit itself?
        if point in self.snake[1:]:
            return True

        return False

    def draw(self):
        # Black background
        self.display.fill(Colors.BLACK)

        outline_width = 2
        for pt in self.snake:
            # Draw snake segment
            pygame.draw.rect(self.display, Colors.FOREST_GREEN,
                             pygame.Rect(pt.x, pt.y, self.block_size, self.block_size))
            pygame.draw.rect(self.display, Colors.LIME_GREEN,
                             pygame.Rect(pt.x + outline_width, pt.y + outline_width,
                                         self.block_size - 2 * outline_width, self.block_size - 2 * outline_width))

        # Draw food
        pygame.draw.rect(self.display, Colors.DARK_RED,
                         pygame.Rect(self.food.x, self.food.y, self.block_size, self.block_size))
        pygame.draw.rect(self.display, Colors.RED,
                         pygame.Rect(self.food.x + outline_width, self.food.y + outline_width,
                                     self.block_size - 2 * outline_width, self.block_size - 2 * outline_width))

        # Text
        texts = [
            font.render(f"Round {self.round}", True, Colors.WHITE),
            font.render(f"Score: {self.score}", True, Colors.WHITE),
            font.render(f"Current FPS: {int(self.clock.get_fps())}", True, Colors.WHITE),
            font.render(f"Target FPS: {int(self.framerate)}", True, Colors.WHITE)
        ]
        for idx, srf in enumerate(texts):
            self.display.blit(srf, (2, 2 + srf.get_height() * idx))

        # Paused indicator
        if self.paused:
            pause_text = big_font.render(f"PAUSED", True, Colors.WHITE)
            pause_text = pygame.transform.scale(pause_text, (self.w / 2, self.h / 2))
            self.display.blit(pause_text, dest=(self.w / 4, self.h / 4))

        # Update display
        pygame.display.flip()

    def _move(self, action):
        # Action is [straight, right, left]
        directions = [
            Direction.RIGHT,
            Direction.DOWN,
            Direction.LEFT,
            Direction.UP
        ]
        idx = directions.index(self.direction)

        # Rotate around the array as needed
        if np.array_equal(action, [1, 0, 0]):
            new_dir = directions[idx]
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = directions[next_idx]
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = directions[next_idx]

        # Move head in the needed direction
        self.direction = new_dir
        x, y = self.head.x, self.head.y
        if self.direction == Direction.RIGHT:
            x += self.block_size
        elif self.direction == Direction.LEFT:
            x -= self.block_size
        elif self.direction == Direction.DOWN:
            y += self.block_size
        elif self.direction == Direction.UP:
            y -= self.block_size

        self.head = Point(x, y)


def modify_fps(game: SnakeGame):
    while True:
        new_fps = input("Enter target fps: ")
        try:
            new_fps = int(new_fps)
            game.framerate = new_fps
        except ValueError:
            print(f"Error: {new_fps=} is not an integer")


def main():
    game = SnakeGame(fps=30, block_size=32)
    threading.Thread(target=modify_fps, args=(game,)).start()
    while True:
        _, game_over, _ = game.play_action(action=[1, 0, 0])
        game.draw()
        if game_over:
            game.reset()


if __name__ == '__main__':
    main()
