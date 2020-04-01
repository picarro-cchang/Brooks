import PlanServiceAPI from "./__mocks__/PlanServiceAPI";
//import PlanServiceAPI from "./PlanServiceAPI"
export const PlanService = (() => {
  return {
    getFileNames: () => {
      return PlanServiceAPI.getRequest("fileNames");
    },
    getFileData: (fileName: string) => {
      return PlanServiceAPI.getRequest("planInfo");
    },
    // getCurrentPlan: () => {
    //   return PlanServiceAPI.getRequest("currentPlan");
    // },
    saveFile: (data, fileName) => {
      return PlanServiceAPI.postData("/save/" + fileName, data, fileName);
    },
    saveFileAs: (data, fileName) => {
      console.log("plan service");
      return PlanServiceAPI.postData("/saveAs/" + fileName, data, fileName); // real implementation will not use filename
    },
    deleteFile: (fileName) => {
      return PlanServiceAPI.putData("/delete/" + fileName)//, {}, fileName);
    }
  };
})();
