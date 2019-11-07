import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO


if __name__ == "__main__":
    ip = "localhost"
    port = 33001
    tags = {'analyzer': "AMADS2002",
                'chassis': "2633"}
    proxy = CmdFIFO.CmdFIFOServerProxy(
     "http://{}:{}".format(ip,port), 
     ClientName="some_dummy_client_name", 
     IsDontCareConnection = False)
    proxy.IDRIVER_add_tags(tags)





    ip = "localhost"
    port = 33000
    tags = {'analyzer': "SBDS2016",
                'chassis': "2755"}
    proxy = CmdFIFO.CmdFIFOServerProxy(
     "http://{}:{}".format(ip,port), 
     ClientName="some_dummy_client_name", 
     IsDontCareConnection = False)
    proxy.IDRIVER_add_tags(tags)
