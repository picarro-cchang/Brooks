import data from "./mockData.json";
import plan from "./mockPlan.json";

const apiLoc = `http://localhost:8000/controller`;

const PicarroAPI = {
  getRequest(url: string) {
    switch (url) {
      case apiLoc + "/uistatus": {
        return Promise.resolve(new Response(JSON.stringify(data)));
      }
      case apiLoc + "/plan": {
        return Promise.resolve(new Response(JSON.stringify(plan)));
      }
    }
  }
};

export default PicarroAPI;
