import ApplogStore from "../stores/ApplogStore";

import React from "react";
import { Grid } from "react-bootstrap";

export default class Applog extends React.Component {
    constructor(props) {
        super(props);
        this.state = { ApplogStore: null };
        this.storeSubscriptions = [];
    }

    componentWillMount() {
        this.handleApplogStoreChange();
        console.log("Added listener to ApplogStoreChange");
        this.storeSubscriptions.push(ApplogStore.addListener(data => this.handleApplogStoreChange(data)));
    }

    componentWillUnmount() {
        this.storeSubscriptions.forEach((subscription) => { subscription.remove(); });
    }

    handleApplogStoreChange() {
        this.setState( {ApplogStore: ApplogStore.getState()} );
    }

    render() {
        return (
            <Grid fluid={true}>
                <h1>Hello Applog!</h1>
            </Grid>
        );
    }
}