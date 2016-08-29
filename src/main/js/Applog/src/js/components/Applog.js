import ApplogNotebook from "../components/ApplogNotebook";
import ApplogStore from "../stores/ApplogStore";


import React, {Component} from "react";
import { Grid } from "react-bootstrap";

export default class Applog extends Component {
    constructor(props) {
        super(props);
        this.state = { ApplogStore: null, autoscroll: true };
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
        let storeData = ApplogStore.getState();
        this.setState( {ApplogStore: storeData} );
    }

    render() {
        return (
            <Grid fluid={true}>
                <h1>Application consoles</h1>
                <ApplogNotebook
                    autoscroll={this.state.autoscroll}
                    data={this.state.ApplogStore.sourceData}
                    names={this.state.ApplogStore.sourceNames}
                    setAutoscroll={(autoscroll) => this.setState({autoscroll})}
                />
            </Grid>
        );
    }
}