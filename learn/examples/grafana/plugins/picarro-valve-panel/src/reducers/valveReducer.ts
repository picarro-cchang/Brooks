const valveReducer = (state = {
    valveMode: -1
}, action) => {
    switch (action.type) {
        case "SET_VALVE_MODE_FULFILLED":
            state = {
                ...state,
                valveMode: Number(action.payload)
            };
            break;
        case "GET_VALVE_MODE_FULFILLED":
        state = {
            ...state,
            valveMode: Number(action.payload)
        };
        break;
    }
    return state;
}

export default valveReducer;
