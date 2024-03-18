from copy import deepcopy

class Queue_bad_memory:
    def __init__(self) -> None:
        self.values = []
        self.tail = 0

    def __len__(self):
        return len(self.values) - self.tail
    
    def pop(self):
        self.tail += 1

    def front(self):
        return self.values[self.tail]
    
    def push(self, x):
        self.values.append(x)


#TODO история ходов
class Game:

    class __Component:
        def __init__(self, player, points):
            self.player = player
            self.points = points
            self.is_dead = False

        def __iter__(self):
            self.i = 0
            return self
        
        def __next__(self):
            if self.i >= len(self.points):
                raise StopIteration
            self.i += 1
            return self.points[self.i - 1]
        
        def __len__(self):
            return len(self.points)


    def __init__(self, size) -> None:
        self.field = [['e'] * size for i in range(size)]
        self.move_player = 'b'
        self.opponent_player = 'w'
        self.size = size
        self.__last_positions = set()
        self.__count_captive_stones = {'b': 0, 'w': 0}

        self.__calculation_component()
        self.__calculation_dame()
        

    def __hash(self, field):
        hash = ""
        for row in field:
            for cell in row:
                if cell == 'e' or cell == 'l':
                    hash += '0'
                elif cell == 'b':
                    hash += '1'
                elif cell == 'w':
                    hash += '2'
        return int(hash, 3)


    def __get_neighbors(self, position):
        neighbors = []
        for delta in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
            i = position[0] + delta[0]
            j = position[1] + delta[1]
            if i < 0 or j < 0 or i >= self.size or j >= self.size:
                continue
            neighbors.append([i, j])

        return neighbors
            

    def __get_neighbors_components(self, position):
        set_neighbors = set()
        for [i, j] in self.__get_neighbors(position):
            set_neighbors.add(self.__field_component[i][j])
        return list(set_neighbors)


    def __BFS(self, position, array_label, label):    
        start_value = self.field[position[0]][position[1]]    
        queue = Queue_bad_memory()
        queue.push(position)

        while len(queue):
            position = queue.front()
            queue.pop()

            array_label[position[0]][position[1]] = label

            for [i, j] in self.__get_neighbors(position):
                if self.field[i][j] != start_value or array_label[i][j] == label:
                    continue

                if self.field[i][j] == start_value:
                    queue.push([i, j])

        return queue.values


    def __calculation_component(self):
        self.__field_component = [[0] * self.size for i in range(self.size)]
        self.__components = [self.__Component('e', [])]
        self.__components[0].is_dead = True

        for i in range(self.size):
            for j in range(self.size):
                player = self.field[i][j]
                if player == 'e' or player == 'l':
                    continue
                if self.__field_component[i][j]:
                    continue

                self.__components.append(self.__Component(player,
                    self.__BFS([i, j], self.__field_component, len(self.__components))
                ))

        
    def __calculation_dame(self):
        self.__components_dame = [0] * len(self.__components)

        for i in range(self.size):
            for j in range(self.size):
                if self.__field_component[i][j]:
                    continue
                
                for component in self.__get_neighbors_components([i, j]):
                    self.__components_dame[component] += 1


    def pass_move(self):
        self.move_player, self.opponent_player = self.opponent_player, self.move_player

        self.__calculation_component()
        self.__calculation_dame()

        for i in range(self.size):
            for j in range(self.size):
                if self.field[i][j] != 'e' and self.field[i][j] != 'l':
                    continue

                is_locked = True
                for [next_i, next_j] in self.__get_neighbors([i, j]):
                    component = self.__field_component[next_i][next_j]
                    if not component:
                        is_locked = False
                        break
                    if self.field[next_i][next_j] == self.move_player:
                        if self.__components_dame[component] > 1:
                            is_locked = False
                            break
                    else:
                        if self.__components_dame[component] == 1:
                            is_locked = False
                            break

                # проверяем на КО по всем предыдущих позициям
                # единственное место, из-за которого работает не за O(self.size^2), а за O(self.size^4)
                if not is_locked:
                    copy_field = deepcopy(self.field)
                    copy_field[i][j] = self.move_player
                    for component in self.__get_neighbors_components([i, j]):
                        if component and self.__components_dame[component] == 1:
                            for [k, l] in self.__components[component]:
                                copy_field[k][l] = 'e'
                    
                    if self.__hash(copy_field) in self.__last_positions:
                        is_locked = 'l'

                self.field[i][j] = 'l' if is_locked else 'e'


    def __call__(self, row, column):
        if row < 0 or row >= self.size or column < 0 or column >= self.size:
            return False
        if self.field[row][column] != 'e':
            return False
        
        self.__last_positions.add(self.__hash(self.field))
        
        self.field[row][column] = self.move_player

        for [i, j] in self.__get_neighbors([row, column]):
            component = self.__field_component[i][j]
            if component and self.__components_dame[component] == 1 and self.field[i][j] == self.opponent_player:
                self.__count_captive_stones[self.move_player] += len(self.__components[component])
                for [k, l] in self.__components[component]:
                    self.field[k][l] = 'e'
        
        self.pass_move()

        return True
    

    def __str__(self):
        return '\n'.join(map(lambda x: ' '.join(x), self.field)) + '\n'
    

    def get_groups(self):
        return self.__field_component
    

    def set_dead_group(self, group_id):
        self.__components[group_id].is_dead = 1


    def unset_dead_group(self, group_id):
        self.__components[group_id].is_dead = 0


    def __dead_group_change_status(self):
        for id, component in enumerate(self.__components):
            if self.__components[id].is_dead:
                for [i, j] in component:
                    if self.field[i][j] != 'e':
                        self.field[i][j] = 'e'
                    else:
                        self.field[i][j] = component.player


    def get_result(self):
        field_result = [[0] * self.size for i in range(self.size)]
        self.__dead_group_change_status()
        for i in range(self.size):
            for j in range(self.size):
                if self.field[i][j] == 'l':
                    self.field[i][j] = 'e'

        for i in range(self.size):
            for j in range(self.size):
                group_id = self.__field_component[i][j]
                if not group_id or self.__components[group_id].is_dead:
                    continue
                
                player = self.field[i][j]
                if not field_result[i][j]:
                    self.__BFS([i, j], field_result, player)
                
                for [k, l] in self.__get_neighbors([i, j]):
                    component_id = self.__field_component[k][l]
                    if not self.__components[component_id].is_dead:
                        continue
                    if field_result[k][l] == 0:
                        self.__BFS([k, l], field_result, player)
                    elif player != field_result[k][l] != 'n':
                        self.__BFS([k, l], field_result, 'n')

        self.__dead_group_change_status()
        return field_result






# if __name__ == "__main__":
#     size = int (input("Введите размер поля от 1 до 9\n"))
#     if size < 1 or size > 9:
#         print("неверный ввод")
#         exit(0)

#     game = Game(size)
#     while True:
#         print(game)
#         print("Сейчас ходят " + ("черные" if game.move_player == 'b' else "белые") + \
#               ". Введите ваш ход, как 2 числа от 0 до " + str(size - 1))
    
#         try:
#             move = input()
#             if move[0] == "p":
#                 game.pass_move()
#                 continue
#             row, column = map(int, move.split())
#         except:
#             print("Неверный ввод.")

#         if row < 0 or column < 0 or row >= size or column >= size:
#             print("Числа не входят в запрашиваемый диапазон")

#         if (not game(row, column)):
#             print("В эту клетку нельзя ходить")
        
g = Game(4)
g(1, 1)
g(2, 2)
g(0, 1)
g(2, 3)
g(1, 0)
print(g)
# g.set_dead_group(1)
print(g.get_result())
print(42)

