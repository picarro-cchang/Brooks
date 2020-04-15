import PlanServiceAPI from "./__mocks__/PlanServiceAPI";
// import PlanServiceAPI from "./PlanServiceAPI"

const url = `http://${window.location.hostname}:8080/plan/api/v0.1/plan`
export const PlanService = (() => {
  return {
    getFileNames: () => {
      return PlanServiceAPI.getRequest(url+'?names=true');
    },
    getLastRunning: () => {
      return PlanServiceAPI.getRequest(url+'?last_running=true')
    },
    getFileData: (fileName: string) => {
      console.log("hello")
      return PlanServiceAPI.getRequest(url+'?plan_name=TestFile')//+fileName);
    },
    saveFileAs: (data) => {
      return PlanServiceAPI.putData(url, data);
    },
    saveFile: (data) => {
      return PlanServiceAPI.postData(url, data);
    },
    deleteFile: (fileName) => {
      return PlanServiceAPI.deleteData(url+"?name="+fileName);
    }
  };
})();
