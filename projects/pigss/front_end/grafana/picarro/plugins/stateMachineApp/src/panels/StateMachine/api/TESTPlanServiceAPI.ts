import plan from './__mocks__/mockExamplePlan.json'

const PlanServiceAPI = {
    postData(url: string, data: object) {
      console.log('hooray');
      return
    },
  
    getRequest(url: string) {
      let fileNames = {"1": "plan1", "2": "plan2"}
      switch (url) {
        case 'fileNames': {return Promise.resolve(new Response(JSON.stringify(fileNames)));}
        case 'planInfo': {
          console.log("HELLO~")
          return Promise.resolve(new Response(JSON.stringify(plan)));
        }
      }
    }
  };
  
  export default PlanServiceAPI;
