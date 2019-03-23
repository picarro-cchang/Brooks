import { createStore, combineReducers, applyMiddleware } from "redux";
import { createLogger } from "redux-logger";
import promise from "redux-promise-middleware";
import valveReducer from "./reducers/valveReducer";

export default createStore(
    combineReducers({valve: valveReducer}), 
    {}, 
    applyMiddleware(createLogger(), promise));
    