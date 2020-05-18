import plan from "./mockExamplePlan.json";
const mockURLs = {
  GETFILENAMES: `?names=true`,
  GETLASTRUNNING: `http://${window.location.hostname}:8080/plan/api/v0.1/plan?last_running=true`,
  GETFILEDATA: `?plan_name=TestFile`,
  SAVEFILEAS: `http://${window.location.hostname}:8080/plan/api/v0.1/plan`,
  DELETEFILE: `http://${window.location.hostname}:8080/plan/api/v0.1/plan?name=TestFile2`
}
const PlanServiceAPI = {
  getRequest(url: string) {
    const fileNames = { "1": "plan1", "2": "plan2" };
    switch (url) {
      case mockURLs.GETFILENAMES: {
        return Promise.resolve(new Response(JSON.stringify(fileNames)));
      }
      case mockURLs.GETLASTRUNNING: {
        return Promise.resolve(new Response(JSON.stringify(plan)))
      }
      case mockURLs.GETFILEDATA: {
        return Promise.resolve(new Response(JSON.stringify(plan)));
      }
    }
  },
  postData(url: string, data: object) {
    return Promise.resolve(new Response(JSON.stringify(data)))
  },
  putData(url: string, data: object) {
    return Promise.resolve(new Response(JSON.stringify(data)))
  },
  deleteData(url: string) {
    return Promise.resolve(new Response(JSON.stringify({"url":url})));
  }
};

export default PlanServiceAPI;
