'''
	Module containing Hopfiled Network Layers.
	Classes embody Parametric Synchronous Autoassociative Recurrent Layers,
	used to recall stored patterns.
'''
import math, numpy
from . import configure, layer, error

class HopfieldNetwork(layer.Layer):
	'''
		Hopfield Network Layer
		Mathematically, f(x) = W * x where W(i)(j) = W(j)(i)
										and W(i)(i) = 0
	'''
	def __init__(self, inputs, alpha = None):
		'''
			Constructor
			: param inputs : dimension of input (and output) feature space
			: param alpha : learning rate constant hyperparameter
		'''
		layer.Layer.__init__(self, inputs, inputs, alpha)
		self.parameters['weights'] = numpy.random.normal(0.0, 1.0 / math.sqrt(self.inputs), (self.inputs, self.inputs))
		self.parameters['weights'] = configure.functions['add'](self.parameters['weights'], configure.functions['transpose'](self.parameters['weights']))
		self.cleardeltas()

	def cleardeltas(self):
		'''
			Method to clear accumulated parameter changes
		'''
		self.deltaparameters = self.modifier.cleardeltas()
		for i in range(self.inputs):
			self.parameters['weights'][i][i] = 0.0

	def updateweights(self):
		'''
			Method to update weights based on accumulated parameter changes
		'''
		self.deltaparameters['weights'] = configure.functions['add'](self.deltaparameters['weights'], configure.functions['transpose'](self.deltaparameters['weights']))
		self.deltaparameters = self.modifier.updateweights()
		for parameter in self.parameters:
			self.parameters[parameter] = configure.functions['subtract'](self.parameters[parameter], self.deltaparameters[parameter])
		self.cleardeltas()

	def feedforward(self, inputvector):
		'''
			Method to feedforward a vector through the layer
			: param inputvector : vector in input feature space
			: returns : fedforward vector mapped to output feature space
		'''
		self.previousinput.append(self.modifier.feedforward(inputvector))
		self.previousoutput.append(configure.functions['dot'](self.parameters['weights'], self.previousinput[-1]))
		return self.previousoutput[-1]

	def backpropagate(self, outputvector):
		'''
			Method to backpropagate derivatives through the layer
			: param outputvector : derivative vector in output feature space
			: returns : backpropagated vector mapped to input feature space
		'''
		self.previousoutput.pop()
		self.deltaparameters['weights'] = configure.functions['add'](self.deltaparameters['weights'], configure.functions['dot'](outputvector, configure.functions['transpose'](self.previousinput.pop())))
		return configure.functions['dot'](configure.functions['transpose'](self.parameters['weights']), outputvector)

	def pretrain(self, trainingset, criterion = None):
		'''
			Method to pretrain parameters using Hebbian Learning
			: param trainingset : unsupervised training set
			: param criterion : criterion used to quantify reconstruction error
			: returns : elementwise reconstruction error on termination
		'''
		if criterion is None:
			criterion = error.MeanSquared(self.inputs)
		self.parameters['weights'] = numpy.zeros((self.inputs, self.inputs), dtype = float)
		for vector in trainingset:
			self.parameters['weights'] = configure.functions['add'](self.parameters['weights'], configure.functions['dot'](vector, configure.functions['transpose'](vector)))
		self.parameters['weights'] = configure.functions['divide'](self.parameters['weights'], len(trainingset))
		self.updateweights()
		errorvector = numpy.zeros((self.outputs, 1), dtype = float)
		for vector in trainingset:
			errorvector = configure.functions['add'](errorvector, criterion.compute(self.feedforward(vector), vector))
		errorvector = configure.functions['divide'](errorvector, len(trainingset))
		return errorvector
