const PlanServiceAPI = {
  getRequest(url: string) {
    return fetch(url, {
      method: "GET",
    })
      .then(response => {
        if (!response.ok) {
          throw Error("Network GET request failed");
        }
        return response;
      })
      .catch(err => {
        throw Error("Network GET request failed.");
      });
  },
  putData(url: string, data: object) {
    return fetch(url, {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    }).then(response => {
      if (!response.ok) {
        throw Error("Network PUT request failed");
      }
      return response;
    });
  },
  postData(url: string, data: object) {
    return fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    }).then(response => {
      if (!response.ok) {
        throw Error("Network POST request failed");
      }
      return response;
    });
  },
  deleteData(url: string) {
    return fetch(url, {
      method: "DELETE",
    })
      .then(response => {
        if (!response.ok) {
          throw Error("Network DELETE request failed");
        }
        return response;
      })
      .catch(err => {
        throw Error("Network DELETE request failed.");
      });
  }
};

export default PlanServiceAPI;
