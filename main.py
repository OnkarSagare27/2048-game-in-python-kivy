from kivy.animation import Animation
import random
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.app import App
from kivy.core.window import Keyboard, Window
from kivy.graphics import BorderImage, Color
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.vector import Vector
import json

#Window.size = (100,100)
#Window.size = (350, 720)
#spacing = 5

spacing = 10

key_vectors = {Keyboard.keycodes['up']: (0, 1), Keyboard.keycodes['right']: (1, 0), Keyboard.keycodes['down']: (0, -1), Keyboard.keycodes['left']: (-1, 0)}

colors = ["87CEEB", "0000FF", "0096FF", "0047AB", "87CEEB", "7DF9FF", "5D3FD3", "1F51FF"]

tile_colors = {2**i: color for i, color in enumerate(colors, start=1)}

times = 0

score = ''
board = ''
highest_score = ''

def all_cells(flip_x=False, flip_y=False):
    for x in (reversed(range(4)) if flip_x else range(4)):
        for y in (reversed(range(4)) if flip_y else range(4)):
            yield (x, y)

class Tile(Widget):
    font_size = NumericProperty(24)
    number = NumericProperty(2)
    color = ListProperty(get_color_from_hex(tile_colors[2]))
    number_color = get_color_from_hex('FFFFFF')

    def __init__(self, number=2, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.font_size = 0.5 * self.width
        self.number = number
        self.update_colors()

    def update_colors(self):
        self.color = get_color_from_hex(tile_colors[self.number])
        if self.number > 4:
            self.number_color = get_color_from_hex('F9F6F2')

    def resize(self, pos, size):
        self.pos = pos
        self.size = size
        self.font_size = 0.5 * self.width

class Board(Widget,App):
    b = None
    moving = False

    def valid_cell(self, board_x, board_y):
        return (board_x >= 0 and board_y >= 0 and board_x <= 3 and board_y <= 3)

    def can_move(self, board_x, board_y):
        return (self.valid_cell(board_x, board_y) and self.b[int(board_x)][int(board_y)] is None)

    def is_deadlocked(self):
        for x, y in all_cells():
            if self.b[int(x)][int(y)] is None:
                return False
            number = self.b[int(x)][int(y)].number
            if self.can_merge(x + 1, y, number) or self.can_merge(x, y + 1, number):
                return False
        return True

    def saveGame(self):
        list = []
        with open("last_save.json", "r") as file:
            list = json.load(file)
            list[0]["lastSave"] = True
            list[0]["data"]["score"] = score.text
            tilesList = []
            for x, y in all_cells():
                if self.b[int(x)][int(y)] is not None:
                    tilesList.append({"number": self.b[int(x)][int(y)].number, "xy": [x, y], "color": self.b[int(x)][int(y)].color})
            list[0]["data"]["tiles"] = tilesList
            if int(score.text) >= int(list[1]["highestScore"]):
                list[1]["highestScore"] = str(score.text)
            with open("last_save.json", "w") as newFile:
                json.dump(list, newFile)

    def loadGame(self):
        self.b = [[None for i in range(4)] for j in range(4)]
        with open("last_save.json", "r") as file:
            lastSave = json.load(file)
            score.text = str(lastSave[0]["data"]["score"])
            highest_score.text = str(lastSave[1]["highestScore"])
            for tile in lastSave[0]["data"]["tiles"]:
                newTile = Tile(pos=self.cell_pos(tile["xy"][0], tile["xy"][1]), size=self.cell_size)
                self.b[int(tile["xy"][0])][int(tile["xy"][1])] = newTile
                newTile.number = tile["number"]
                newTile.color = tile["color"]
                self.add_widget(newTile)
            if self.is_deadlocked():
                print("Game Over!")
            self.moving = False

    def get_tiles(self):
        for x, y in all_cells():
            if self.b[int(x)][int(y)] is not None:
                print(self.b[int(x)][int(y)].number, self.b[int(x)][int(y)].color)

    def new_tile(self, *args):
        global times
        times = times + 1
        empty_cells = [(x, y) for x, y in all_cells() if self.b[int(x)][int(y)] is None]
        x, y = random.choice(empty_cells)
        tile = Tile(pos=self.cell_pos(x, y), size=self.cell_size)
        self.b[int(x)][int(y)] = tile
        if times == 8:
            tile.number = 4
            tile.color = [0.0, 0.0, 1.0, 1.0]
            times = 0
        self.add_widget(tile)
        
        if len(empty_cells) == 1 and self.is_deadlocked():
            print('Game Over(board is deadlocked)')
        self.moving = False

    def reset(self):
        self.b = [[None for i in range(4)] for j in range(4)]
        self.new_tile()
        self.new_tile()
        global times
        times = 0
    
    def restart(self):
        for x, y in all_cells():
            if self.b[int(x)][int(y)] is not None:
                self.remove_widget(self.b[int(x)][int(y)])
        self.reset()
        appManger.setScore(0)

    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self.resize()

    def cell_pos(self, board_x, board_y):
        return (self.x + spacing + board_x * (self.cell_size[0] + spacing), self.y + spacing + board_y * (self.cell_size[1] + spacing))

    def can_merge(self, board_x, board_y, number):
        return (self.valid_cell(board_x, board_y) and self.b[int(board_x)][int(board_y)] is not None and self.b[int(board_x)][int(board_y)].number == number)

    def move(self, dir_x, dir_y):
        if self.moving:
            return

        for board_x, board_y in all_cells(dir_x > 0, dir_y > 0):
            tile = self.b[int(board_x)][int(board_y)]
            if not tile:
                continue
            x, y = board_x, board_y

            while self.can_move(x + dir_x, y + dir_y):
                self.b[int(x)][int(y)] = None
                x += dir_x
                y += dir_y
                self.b[int(x)][int(y)] = tile

            if self.can_merge(x + dir_x, y + dir_y, tile.number):
                self.b[int(x)][int(y)] = None
                x += dir_x
                y += dir_y
                self.remove_widget(self.b[int(x)][int(y)])
                self.b[int(x)][int(y)] = tile
                tile.number *= 2
                appManger.updateScore(tile.number)
                if tile.number == 2048:
                    print('You win the game.')
                tile.update_colors()
            if x == board_x and y == board_y:
                continue
            anim = Animation(pos=self.cell_pos(x, y), duration=0.15, transition='linear')
            if not self.moving:
                anim.on_complete = self.new_tile
                self.moving = True
            anim.start(tile)

    def resize(self, *args):
        self.cell_size = (.25 * (self.width - 5 * spacing),) * 2
        self.canvas.before.clear()
        with self.canvas.before:
            BorderImage(pos=self.pos, size=self.size, source='board.png')
            Color(get_color_from_hex('ccc0b4'))
            for board_x, board_y in all_cells():
                BorderImage(pos=self.cell_pos(board_x, board_y), size=self.cell_size, source='cell.png')
        if not self.b:
            return

        for board_x, board_y in all_cells():
            tile = self.b[int(board_x)][int(board_y)]
            if tile:
                tile.resize(pos=self.cell_pos(board_x, board_y), size=self.cell_size)

    on_pos = resize
    on_size = resize

    def on_key_down(self, window, key, *args):
        if key in key_vectors:
            self.move(*key_vectors[key])

    def on_touch_up(self, touch):
        v = Vector(touch.pos) - Vector(touch.opos)
        if v.length() < 20:
            return
        if abs(v.x) > abs(v.y):
            v.y = 0
        else:
            v.x = 0
        self.move(*v.normalize())

class GameApp(App):

    def on_start(self):
        global score, board, highest_score
        board = self.root.ids.board
        score = self.root.ids.score
        highest_score = self.root.ids.highest_score
        file = open("last_save.json", "r")
        data = json.load(file)
        if data[0]["lastSave"]:
            board.loadGame()
        else:
            board.reset()
        Window.bind(on_key_down=board.on_key_down)
    
    def updateScore(self, addScore):
        score.text = str(int(score.text) + addScore)
        if int(highest_score.text) <= int(score.text):
            highest_score.text = score.text

    def setScore(self, scoreSet):
        score.text = str(scoreSet)

    def on_stop(self):
        board.saveGame()

appManger = GameApp()

if __name__ == '__main__':
    Window.clearcolor = get_color_from_hex('222233')
    GameApp().run()