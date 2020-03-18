import  TESTPlanServiceAPI from "./TESTPlanServiceAPI";

export const PlanService = (() => {
  return {
    getFileNames: () => {
        return TESTPlanServiceAPI.getRequest('fileNames')
    },
    getFileData: (fileName: string) => {
        return TESTPlanServiceAPI.getRequest('planInfo')
    },
    saveFile: () => {
        let data = {}
        return TESTPlanServiceAPI.postData('', data)
    },
    saveFileAs: () => {
        let data = {}
        return TESTPlanServiceAPI.postData('', data)
    }
  };
})();
