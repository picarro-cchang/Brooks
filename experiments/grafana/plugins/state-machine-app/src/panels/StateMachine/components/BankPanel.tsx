import React, {Component, PureComponent} from 'react';
import './bankpanel.css'


interface BankPanelOptions {
    bank: number,
    uistatus: {
        bank?: {[bankNum:string]: string}
        clean?: {[bankNum:string]: string}
        channel?: {[bankNum:string]: {[channelNum:string]: string}}
    }
    ws_sender: (o: object)=>void;
    plan: {
        bank_names: {
            [key: number]: {
                name: string,
                channels: { [key: number]: string }
            }
        }
    }
}

class BankPanel extends PureComponent<BankPanelOptions> {
    bankStyleOpt = {
        READY:{color:"#fff", backgroundColor:"#c5d2e6"},
        ACTIVE:{color:"#fff", backgroundColor:"rgb(86, 166, 75)"},
        CLEAN:{color:"#fff", backgroundColor:"#4BBEE3"},
        REFERENCE:{color:"#440", backgroundColor:"rgb(224, 180, 0)"}}; //hope this will work to not display any inactive banks
    cleanClassNameOpt = {
        DISABLED:"btn-inverse disabled", READY: "btn-light", ACTIVE:"btn-light", CLEAN:"btn-secondary btn-clean-act"
    };
    channelClassNameOpt = {
        DISABLED:"btn-inverse disabled", READY: "btn-light", AVAILABLE:"btn-light", ACTIVE:"btn-green", CLEAN:"btn-light", REFERENCE:"btn-warning"
    };

    render() {
        let bankStyle = {};
        let cleanClassNames = "";
        let cleanDisabled = true;
        let getChannelClassNames = (_:number) => "";
        let getChannelDisabled = (_:number) => true;
        let test = {}

        if ("bank" in (this.props.uistatus as any)) {
            //console.log("In bankPanel.render", this.props.uistatus);
            const bankStatus: string = (this.props.uistatus.bank as any)[this.props.bank];
            const channelStatus: {[key:number]: string} = (this.props.uistatus.channel as any)[this.props.bank];
            const cleanStatus: string = (this.props.uistatus.clean as any)[this.props.bank];
            bankStyle = (this.bankStyleOpt as any)[bankStatus];
            cleanClassNames = (this.cleanClassNameOpt as any)[cleanStatus];
            cleanDisabled = cleanStatus !== "READY";
            getChannelClassNames = (chan) => (this.channelClassNameOpt as any)[(channelStatus as any)[chan]];
            getChannelDisabled = (chan) => (channelStatus as any)[chan] !== "READY";
            test = channelStatus;
        }
       // console.log("hello", channelStatus);

        let channelButtons = [];
        for (let i=1; i<=8; i++) {
            channelButtons.push(
                (getChannelDisabled(i)) ? (
                    <button
                        key={i}
                        className={"btn btn-large bank-btn " + getChannelClassNames(i)}
                        style={{color: 'black'}}>
                        <p className="chn-label">{this.props.plan.bank_names[this.props.bank].channels[i]}</p>
                        <p style={{fontSize: 10, marginTop: 30}}>Status: {test[i]} </p>
                    </button>
                ) : (
                    <button
                        onClick={e => this.props.ws_sender({element: "channel", bank: this.props.bank, channel: i})}
                        disabled={getChannelDisabled(i)}
                        key={i}
                        className={"btn btn-large bank-btn " + getChannelClassNames(i)}>
                        <p className="chn-label">{this.props.plan.bank_names[this.props.bank].channels[i]}</p>
                        <p style={{ fontSize: 10, marginTop: 30 }}>Status: {test[i]}</p>
                    </button>
                )
            );
        }

        const cleanButton = (cleanDisabled) ? (
            <div
                className={"btn btn-large btn-clean " + cleanClassNames}>
                {"Clean"}
            </div>
        ) : (
            <button
                onClick={e => this.props.ws_sender({element: "clean", bank: this.props.bank})}
                className={"btn btn-large btn-clean " + cleanClassNames}>
                {"Clean"}
            </button>
        );
        const value: string = this.props.plan.bank_names[this.props.bank].name;
        //const value: string = "Bank " + this.props.bank;
        return (
            <div>
                <div className="panel-bank" style={bankStyle}>
                    <div style={{width: "100%"}}>
                        <h2 style={{color: "white"}}>{value}</h2>
                        <div className="grid-bank">
                            {channelButtons}
                        </div>
                        {cleanButton}
                    </div>
                </div>
            </div>
        );
    }
}
export default BankPanel;
