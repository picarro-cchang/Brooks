import plan from "./__mocks__/mockExamplePlan.json";

const PlanServiceAPI = {
  postData(url: string, data: object, fileName: string) {
    let urlstring;
    if (url.includes("/save/")) {
      urlstring = "save";
    } else if (url.includes("/saveAs")) {
      urlstring = "saveAs";
    }
    switch (urlstring) {
      case "save": {
        // save data to a new file
        // const a = document.createElement("a");
        // const file = new Blob([JSON.stringify(data)]);
        // a.href = URL.createObjectURL(file);
        // a.download = fileName;
        // a.click();
        return Promise.resolve(new Response(JSON.stringify(data)))
      }
      case "saveAs": {
        // overwrite current file
        // const a = document.createElement("a");
        // const file = new Blob([JSON.stringify(data)]);
        // a.href = URL.createObjectURL(file);
        // a.download = fileName;
        // a.click();
        return Promise.resolve(new Response(JSON.stringify(data)))
      }
    }
  },

  getRequest(url: string) {
    const fileNames = { "1": "plan1", "2": "plan2" };
    switch (url) {
      case "fileNames": {
        return Promise.resolve(new Response(JSON.stringify(fileNames)));
      }
      case "planInfo": {
        return Promise.resolve(new Response(JSON.stringify(plan)));
      }
    }
  }
};

export default PlanServiceAPI;
