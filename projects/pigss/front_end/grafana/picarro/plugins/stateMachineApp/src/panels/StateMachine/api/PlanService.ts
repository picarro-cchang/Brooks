// import PlanServiceAPI from "./__mocks__/PlanServiceAPI";
import PlanServiceAPI from "./PlanServiceAPI"

const url = `http://${window.location.hostname}:8000/manage_plan/api/v0.1/plan`
export const PlanService = (() => {
  return {
    getFileNames: () => {
      return PlanServiceAPI.getRequest(url+'?names=true');
    },
    getLastRunning: () => {
      return PlanServiceAPI.getRequest(url+'?last_running=true')
    },
    getFileData: (planName: string) => {
      planName = planName || "plan_1";
      return PlanServiceAPI.getRequest(url+`?plan_name=${planName}`);
    },
    overwriteFile: (data) => {
      return PlanServiceAPI.putData(url, data);
    },
    updateLastRunning: (data) => {
      return PlanServiceAPI.putData(url, data);
    },
    saveFile: (data) => {
      return PlanServiceAPI.postData(url, data);
    },
    deleteFile: (planName) => {
      return PlanServiceAPI.deleteData(url+`?name=${planName}`);
    }
  };
})();
