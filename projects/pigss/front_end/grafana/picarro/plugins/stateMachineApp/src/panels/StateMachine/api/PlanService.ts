import TESTPlanServiceAPI from "./TESTPlanServiceAPI";

export const PlanService = (() => {
  return {
    getFileNames: () => {
      return TESTPlanServiceAPI.getRequest("fileNames");
    },
    getFileData: (fileName: string) => {
      return TESTPlanServiceAPI.getRequest("planInfo");
    },
    saveFile: (data, fileName) => {
      return TESTPlanServiceAPI.postData("/save/" + fileName, data, fileName);
    },
    saveFileAs: (data, fileName) => {
      console.log("plan service");
      return TESTPlanServiceAPI.postData("/saveAs/" + fileName, data, fileName); // real implementation will not use filename
    }
  };
})();
