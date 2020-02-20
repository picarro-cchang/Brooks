const apiLoc = `http://localhost:8000/controller`;

let PicarroAPI = {
    getRequest(url: string) {
        switch(url) {
            case apiLoc+'/uistatus': {
                const data = {
                    "standby": "ACTIVE",
                    "identify": "READY",
                    "loop_plan": "READY",
                    "run": "READY",
                    "plan": "READY",
                    "plan_run": "READY",
                    "plan_loop": "READY",
                    "reference": "READY",
                    "run_plan": "READY",
                    "edit": "READY",
                    "clean": {
                      "1": "READY",
                      "3": "READY",
                      "4": "READY"
                    },
                    "bank": {
                      "1": "READY",
                      "3": "READY",
                      "4": "READY"
                    },
                    "channel": {
                      "1": {
                        "1": "DISABLED",
                        "2": "AVAILABLE",
                        "3": "DISABLED",
                        "4": "AVAILABLE",
                        "5": "DISABLED",
                        "6": "AVAILABLE",
                        "7": "DISABLED",
                        "8": "AVAILABLE"
                      },
                      "3": {
                        "1": "DISABLED",
                        "2": "AVAILABLE",
                        "3": "DISABLED",
                        "4": "AVAILABLE",
                        "5": "DISABLED",
                        "6": "AVAILABLE",
                        "7": "DISABLED",
                        "8": "AVAILABLE"
                      },
                      "4": {
                        "1": "DISABLED",
                        "2": "AVAILABLE",
                        "3": "DISABLED",
                        "4": "AVAILABLE",
                        "5": "DISABLED",
                        "6": "AVAILABLE",
                        "7": "DISABLED",
                        "8": "AVAILABLE"
                      }
                    }
                }
                return Promise.resolve(new Response(JSON.stringify(data)))
            }
            case apiLoc+'/plan': {
                const plan = {
                    "max_steps": 32,
                    "panel_to_show": 0,
                    "current_step": 11,
                    "looping": false,
                    "focus": {
                      "row": 12,
                      "column": 1
                    },
                    "last_step": 11,
                    "steps": {
                      "1": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 2
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "2": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 32
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "3": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 8
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "4": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 128
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "5": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 32
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "6": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 8
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "7": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 128
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 0
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "8": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 2
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "9": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 32
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "10": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 8
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      },
                      "11": {
                        "banks": {
                          "1": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "3": {
                            "clean": 0,
                            "chan_mask": 0
                          },
                          "4": {
                            "clean": 0,
                            "chan_mask": 128
                          }
                        },
                        "reference": 0,
                        "duration": 20
                      }
                    },
                    "num_plan_files": 2,
                    "plan_files": {
                      "1": "__default__",
                      "2": "tr"
                    },
                    "plan_filename": "__default__",
                    "bank_names": {
                      "1": {
                        "name": "Bank 1",
                        "channels": {
                          "1": "Ch. 1",
                          "2": "Ch. 2",
                          "3": "Ch. 3",
                          "4": "Ch. 4",
                          "5": "Ch. 5",
                          "6": "Ch. 6",
                          "7": "Ch. 7",
                          "8": "Ch. 8"
                        }
                      },
                      "2": {
                        "name": "Bank 2",
                        "channels": {
                          "1": "Ch. 1",
                          "2": "Ch. 2",
                          "3": "Ch. 3",
                          "4": "Ch. 4",
                          "5": "Ch. 5",
                          "6": "Ch. 6",
                          "7": "Ch. 7",
                          "8": "Ch. 8"
                        }
                      },
                      "3": {
                        "name": "Bank 3",
                        "channels": {
                          "1": "Ch. 1",
                          "2": "Ch. 2",
                          "3": "Ch. 3",
                          "4": "Ch. 4",
                          "5": "Ch. 5",
                          "6": "Ch. 6",
                          "7": "Ch. 7",
                          "8": "Ch. 8"
                        }
                      },
                      "4": {
                        "name": "Bank 4",
                        "channels": {
                          "1": "Ch. 1",
                          "2": "Ch. 2",
                          "3": "Ch. 3",
                          "4": "Ch. 4",
                          "5": "Ch. 5",
                          "6": "Ch. 6",
                          "7": "Ch. 7",
                          "8": "Ch. 8"
                        }
                      }
                    },
                    "available_ports": {
                      "1": 170,
                      "2": 0,
                      "3": 170,
                      "4": 170
                    }
                }
                return Promise.resolve(new Response(JSON.stringify(plan)))
            }
            case apiLoc+'/modal_info': {
                const info = {
                    "show": false,
                    "html": "<h2 class='test'>Confirm Loop Plan</h2><p>Loop plan starting at step 1</p>",
                    "num_buttons": 2,
                    "buttons": {
                      "1": {
                        "caption": "OK",
                        "className": "btn btn-success btn-large",
                        "response": "modal_ok"
                      },
                      "2": {
                        "caption": "Cancel",
                        "className": "btn btn-danger btn-large",
                        "response": "modal_close"
                      }
                    }
                }
                return Promise.resolve(new Response(JSON.stringify(info)))
            }
        }
    //   return fetch(url, {
    //     method: "GET"
    //   }).then(response => {
    //     if (!response.ok) {
    //       throw Error("Network GET request failed");
    //     }
    //     return response;
    //   });
    }
  };
  
  export default PicarroAPI;
  