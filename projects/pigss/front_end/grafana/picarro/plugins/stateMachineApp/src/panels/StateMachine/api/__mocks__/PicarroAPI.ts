import data from "./mockData.json";
import plan from "./mockPlan.json";
import info from "./mockModalInfo.json";

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
      case apiLoc + "/modal_info": {
        return Promise.resolve(new Response(JSON.stringify(info)));
      }
    }
  }
};

export default PicarroAPI;
