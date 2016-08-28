import {Dispatcher} from "flux";

class AppDispatcher extends Dispatcher {
    // Do logging before calling actual dispatcher
    dispatch(action = {}) {
        console.log("Dispatched", action);
        super.dispatch(action);
    }
}

export default new AppDispatcher();
