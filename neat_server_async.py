from flask import Flask
from flask_restful import Resource, Api, reqparse
import neat
import os
import threading
import numpy as np
import tensorflow as tf
import logging

app = Flask(__name__)
api = Api(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


updated = False
tick = 1
EA = []
nets = []
ge = []
counters = []

class Market:
    def __init__(self):
        self.Ask = 0
        self.Bid = 0
        self.spread = self.Ask - self.Bid
        self.mult = 100000

    def update(self, Ask, Bid):
        self.Ask = Ask * self.mult
        self.Bid = Bid * self.mult
        self.spread = self.Ask - self.Bid


MARKET = Market()

class ExpertAdvisor:
    def __init__(self, starting_balance):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.last_trade = 0
        self.entry_price = 0
        self.open_position = False
        self.long = False
        self.short = False
        self.position_duration = 0
        self.leverage = 1
        self.max_prof = 0

    def open_long(self):
        if self.open_position:
            self.do_nothing()
            return False
        self.entry_price = MARKET.Ask
        self.open_position = True
        self.short = False
        self.long = True
        self.position_duration = 0
        return True

    def open_short(self):
        if self.open_position:
            self.do_nothing()
            return False
        self.entry_price = MARKET.Bid
        self.open_position = True
        self.short = True
        self.long = False
        self.position_duration = 0
        return True

    def close_trade(self):
        if not self.open_position:
            self.do_nothing()
            return False
        if self.long:
            self.last_trade = MARKET.Bid - self.entry_price
        else:
            self.last_trade = self.entry_price - MARKET.Ask
        self.balance += self.last_trade
        self.open_position = False
        self.short = False
        self.long = False
        self.position_duration = 0

        return True

    def unrealized_gains(self):
        if self.open_position:
            if self.long:
                return MARKET.Bid - self.entry_price
            else:
                return self.entry_price - MARKET.Ask
        else:
            return 0

    def max_unrealized_gains_during_order(self):
        if self.open_position:
            if self.max_prof < self.unrealized_gains():
                self.max_prof = self.unrealized_gains()
            return self.max_prof
        return 0

    def do_nothing(self):
        self.position_duration += 1
        return


class Users(Resource):
    def get(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('balance', required=False)
        parser.add_argument('indics', required=False)
        parser.add_argument('Ask', required=False)
        parser.add_argument('Bid', required=False)

        args = parser.parse_args()  # parse arguments to dictionary

        global EA
        global counters
        global nets
        global ge
        global MARKET

        MARKET.update(float(args['Ask']), float(args['Bid']))
        global tick
        tick += 1

        indics = eval(args['indics'])

        indics = [(float(i)-min(indics))/(max(indics)-min(indics)) for i in indics]

        response = []
        check_balance = 0
        for ea in list(EA):
            x = EA.index(ea)
            close = False

            activation = indics + [float(ea.unrealized_gains()),
                          int(ea.open_position),
                          int(ea.position_duration),
                          float(ea.max_unrealized_gains_during_order())]

            output = nets[x].activate(activation)
            # output = tf.keras.utils.to_categorical(np.argmax(output), num_classes=4).tolist()
            output_map = {0: 1, 1: 2, 2: -1, 3: 0}
            out = output_map[np.argmax(output)]


            ge[x].fitness = ea.balance - ea.starting_balance

            # print(f'balance: {ea.balance:.2f} gains: {ea.unrealized_gains():.2f} fitness: {ge[x].fitness:.2f}')

            if (ea.balance + ea.unrealized_gains()) <= 0:
                if ea.open_position:
                    ea.close_trade()
                close = True
            elif ea.balance <= 0:
                if ea.open_position:
                    ea.close_trade()
                close = True

            if tick >= 600:
                close = True

            if close:
                if ea.open_position:
                    response.append(f'{x}:-1')
                else:
                    response.append(f'{x}:0')
                ge.pop(x)
                nets.pop(x)
                EA.remove(ea)

            elif out == 1:
                response.append(f'{x}:1')
                ea.open_long()
            elif out == 2:
                response.append(f'{x}:2')
                ea.open_short()
            elif out == -1:
                response.append(f'{x}:-1')
                ea.close_trade()
            elif out == 0:
                response.append(f'{x}:0')
                ea.do_nothing()

        global updated
        updated = True
        return response, 200  # return data and 200 OK code


class Restart(Resource):
    def get(self):
        global EA
        global nets
        global ge
        global MARKET
        global tick
        tick += 1
        for ea in list(EA):
            x = EA.index(ea)
            if ea.open_position:
                ea.close_trade()
            ge[x].fitness = 0
            ge.pop(x)
            nets.pop(x)
            EA.remove(ea)

        global updated
        updated = True
        return 200  # return data and 200 OK cod


api.add_resource(Restart, '/restart')  # '/users' is our entry point
api.add_resource(Users, '/users')  # '/users' is our entry point

def eval_genomes(genomes, configu):
    global updated
    global nets
    global EA
    global ge
    global tick
    nets = []
    ge = []
    EA = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.RecurrentNetwork.create(genome, configu)
        EA.append(ExpertAdvisor(100))
        nets.append(net)
        ge.append(genome)

    while 1:
        if updated:
            updated = False
        else:
            pass

        if len(EA) <= 1:
            tick = 1
            break

def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    #p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-3214')
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    # Run for up to 300 generations.
    winner = p.run(eval_genomes, 50000)


def run_app():
    app.run(port=80)


class RunServer (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("Starting " + self.name)
        run_app()
        print("Exiting " + self.name)

class RunNeat (threading.Thread):
    def __init__(self, threadID, name, counter, config):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.config = config
    def run(self):
        print ("Starting " + self.name)
        run(self.config)
        print ("Exiting " + self.name)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    thread1 = RunServer(1, 'Server', 1)
    thread2 = RunNeat(2, 'Neat', 2, config_path)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

