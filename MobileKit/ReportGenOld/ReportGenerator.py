import time
from ReportGenSupportNew import ReportBaseMap, ReportMarkerMap, ReportPathMap


class ReportGenerator(object):
    def __init__(self, root, resourceManager, name, paramDict, instructions, ticket, inputs, outputs):
        self.root = root
        self.rm = resourceManager
        self.name = name
        self.paramDict = paramDict
        self.instructions = instructions
        self.ticket = ticket
        self.inputs = inputs
        self.outputs = outputs

    def process(self):
        if self.paramDict["task"] == "base":
            self.makeBaseMap()
        elif self.paramDict["task"] == "path":
            self.makePathMap()
        elif self.paramDict["task"] == "marker":
            self.makeMarkerMap()
        else:
            time.sleep(1.0)
        return

    def resourceLogger(self, d):
        """A logging function which writes detailed status to all specified output resources"""
        for o in self.outputs:
            self.rm.addDetail(o, d)

    def makeBaseMap(self):
        region = self.paramDict["region"]
        ReportBaseMap(self.root, self.ticket, self.instructions, region, self.resourceLogger).run()

    def makePathMap(self):
        region = self.paramDict["region"]
        bm = ReportBaseMap(self.root, self.ticket, self.instructions, region, self.resourceLogger)
        mp = bm.getMapParams()[0]
        ReportPathMap(self.root, self.ticket, self.instructions, mp, region, self.resourceLogger).run()

    def makeMarkerMap(self):
        region = self.paramDict["region"]
        bm = ReportBaseMap(self.root, self.ticket, self.instructions, region, self.resourceLogger)
        mp = bm.getMapParams()[0]
        ReportMarkerMap(self.root, self.ticket, self.instructions, mp, region, self.resourceLogger).run()
