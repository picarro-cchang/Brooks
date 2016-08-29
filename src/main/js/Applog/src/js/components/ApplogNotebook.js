import React, {Component, PropTypes} from "react";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";

export default class ApplogNotebook extends Component {
    constructor(props) {
        super(props);
    }

    componentDidUpdate() {
        if (this.props.autoscroll) {
            let nodeList = document.getElementsByClassName("scrollBottom");
            Array.from(nodeList).forEach((node) => {
                node.scrollTop = node.scrollHeight;
            });
        }
    }

    render() {
        let tabs = this.props.names.map((name) => (<Tab key={name}> { name.slice(1) }</Tab>));
        let panels = this.props.names.map((name) => (
            <TabPanel key={name}>
                <textarea style={{ width: "100%", height: "80vh" }} className={"scrollBottom"}
                    readonly value={this.props.data[name]}>
                </textarea>
            </TabPanel>));
        return (
            <div>
                <Tabs onSelect = {(index, last) => { } }>
                    <TabList>
                        { tabs }
                    </TabList>
                    { panels }
                </Tabs>
                <div>
                    <input type="checkbox" checked={ this.props.autoscroll }
                            onChange={(e) => { this.props.setAutoscroll(e.target.checked);}} />
                    <span style={{marginLeft: "10px"}}>Autoscroll window</span>
                </div>
            </div>
        );
    }
}


ApplogNotebook.propTypes = {
    autoscroll: PropTypes.bool.isRequired,
    data: PropTypes.object.isRequired,
    names: PropTypes.array.isRequired,
    setAutoscroll: PropTypes.func.isRequired
};
