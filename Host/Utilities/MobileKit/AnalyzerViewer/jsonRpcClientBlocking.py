from Host.Utilities.MobileKit.AnalyzerViewer.jsonrpcutils import Proxy

if __name__ == "__main__":
    service = Proxy('http://localhost:5000/jsonrpc')
    result = service.getData()
    print result.keys()