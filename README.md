# NEAT-Forex-Server
a multi threaded implementation of a flask server which runs the NEAT training algorithm that listens for api calls from a forex backtesting agent such as MetaTrader

What is NEAT?
NeuroEvolution of Augmenting Topologies.

It is an algorithm that allows the user to create agents which learn to solve any problem. 
These agents start as tiny neural networks and grow over time as they learn the complexities of the problem at hand.

MetaTrader is a program that allows the user to write c++ looking code to perform automated trading.

Having a bunch of automated traders learning to trade Forex sounds like a worthy problem to tackle.

From my time back testing, my agents never grew complex enough, even after 200 generations, to find a pattern in the numbers.

However, they were only ever aware of the current state, or only looking back for the past 5 minutes. 
With some expansion, this code could potentially produce some winning bots.

The included MetaTrader code is an example of how to write API calls from .mql files and process the requests. 
It can have as many concurrent agents training as you define. This number must match the number in the python server.

### Disclaimer: only use for back-testing and with demo accounts!
