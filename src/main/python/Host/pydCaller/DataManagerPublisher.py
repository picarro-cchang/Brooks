from Host.DataManager.DataManagerPublisher import DataManagerPublisher, HandleCommandSwitches

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    pub = DataManagerPublisher(configFile)
    pub.run()