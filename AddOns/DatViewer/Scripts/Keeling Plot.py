panel1, panel2 = _VariableSelector_("Select Variables for Keeling Plot")
yData = _Panels_[panel2].yData
yLabel = _Panels_[panel2].varName
xData = 1. / _Panels_[panel1].yData
xLabel = "1 / " + _Panels_[panel1].varName
fig = _PlotXY_(xData, yData, xLabel=xLabel, yLabel=yLabel, enableAnalysis=True)
fig.plot.axes.set_title("Keeling Plot", fontdict = {'size': 18, 'weight': 'bold'})
fig.plot.redraw()