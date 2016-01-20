class AllanVar(object):

    """ Class for computation of Allan Variance of a data series. Variances are computed over sets of
  size 1,2,...,2**(nBins-1). In order to process a new data point call processDatum(value). In order
  to recover the results, call getVariances(). In order to reset the calculation, call reset(). """

    def __init__(self, nBins):
        """ Construct an AllanVar object for calculating Allan variances over 1,2,...,2**(nBins-1) points """
        self.nBins = nBins
        self.counter = 0
        self.bins = []
        for i in range(nBins):
            self.bins.append(AllanBin(2 ** i))

    def reset(self):
        """ Resets calculation """
        self.counter = 0
        for bin in self.bins:
            bin.reset()

    def processDatum(self, value):
        """ Process a value for the Allan variance calculation """
        for bin in self.bins:
            bin.process(value)
        self.counter += 1

    def getVariances(self):
        """ Get the result of the Allan variance calculation as (count,(var1,var2,var4,...)) """
        return (self.counter, tuple([bin.allanVar for bin in self.bins]))

class AllanBin(object):

    """ Internal class for Allan variance calculation """

    def __init__(self, averagingLength):
        self.averagingLength = averagingLength
        self.reset()

    def reset(self):
        self.sum, self.sumSq = 0, 0
        self.sumPos, self.numPos = 0, 0
        self.sumNeg, self.numNeg = 0, 0
        self.nPairs, self.allanVar = 0, 0

    def process(self, value):
        if self.numPos < self.averagingLength:
            self.sumPos += value
            self.numPos += 1
        elif self.numNeg < self.averagingLength:
            self.sumNeg += value
            self.numNeg += 1
        if self.numNeg == self.averagingLength:
            var = (self.sumPos / self.numPos) - (self.sumNeg / self.numNeg)
            self.sum += var
            self.sumSq += var ** 2
            self.nPairs += 1
            self.allanVar = 0.5 * self.sumSq / self.nPairs
            self.sumPos, self.numPos = 0, 0
            self.sumNeg, self.numNeg = 0, 0

ax = _Figure_.gca()
tMin, tMax = ax.get_xlim()
selection = (x >= tMin) & (x <= tMax)
x_sel = x[selection]
y_sel = y[selection]
n = len(x_sel)
if not n > 0:
    raise ValueError
# Find conversion from points to a time axis
slope, offset = polyfit(arange(n), x_sel, 1)
    
npts = int(floor(log(n) / log(2)))
av = AllanVar(int(npts))
for var in y_sel:
    av.processDatum(var)
v = av.getVariances()
sdev = sqrt(asarray(v[1]))

fig = _PlotXY_(2 ** arange(npts) * slope*24*3600, sdev, xLabel="Time (s)", yLabel='Allan Std Dev', 
              xMin=1, xMax=2 ** npts, yMin=sdev.min(), yMax=sdev.max(), xScale='log', yScale='log')
fig.getSelection()
fit_yData = fig.yData[0] / sqrt(fig.xData / fig.xData[0])
fig.fitHandle.set_data(fig.xData, fit_yData)
fig.plot.axes.set_title("Allen Standard Deviation Plot", fontdict = {'size': 18, 'weight': 'bold'})
fig.plot.redraw()