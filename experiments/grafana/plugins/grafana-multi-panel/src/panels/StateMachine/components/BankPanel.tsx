import React, {Component, PureComponent} from 'react';

interface BankPanelOptions {
    bank: number,
    uistatus: {
        bank?: {[bankNum:string]: string}
        clean?: {[bankNum:string]: string}
        channel?: {[bankNum:string]: {[channelNum:string]: string}}
    }
    ws_sender: (o: object)=>void;
}

class BankPanel extends PureComponent<BankPanelOptions> {
    bankStyleOpt = {
        READY:{color:"#fff", backgroundColor:"#888"},
        ACTIVE:{color:"#fff", backgroundColor:"#080"},
        CLEAN:{color:"#fff", backgroundColor:"#4BBEE3"},
        REFERENCE:{color:"#440", backgroundColor:"#febb00"},
        DISABLED:{ display: "none" }}; //hope this will work to not display any inactive banks
    cleanClassNameOpt = {
        DISABLED:"btn-inverse disabled", READY: "btn-light", ACTIVE:"btn-primary", CLEAN:"btn-secondary"
    };
    channelClassNameOpt = {
        DISABLED:"btn-inverse disabled", READY: "btn-light", AVAILABLE:"btn-light", ACTIVE:"btn-primary", CLEAN:"btn-primary", REFERENCE:"btn-warning"
    };

    render() {
        let bankStyle = {};
        let cleanClassNames = "";
        let cleanDisabled = true;
        let getChannelClassNames = (_:number) => "";
        let getChannelDisabled = (_:number) => true;
        let test = {}

        if ("bank" in (this.props.uistatus as any)) {
            console.log("In bankPanel.render", this.props.uistatus);
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
                        className={"btn btn-large " + getChannelClassNames(i)}
                        style={{ height: 90, width: 90,  color: 'black', position: "relative"}}>
                        <p style={{ position: "absolute", top: 20, left: "-0.37em", bottom: 0, right: 0}}>{"Ch " + i}</p>

                        <p style={{fontSize: 10, marginTop: 30}}>Status: {test[i]} </p>


                    </button>
                ) : (
                    <button
                        onClick={e => this.props.ws_sender({element: "channel", bank: this.props.bank, channel: i})}
                        disabled={getChannelDisabled(i)}
                        key={i}
                        className={"btn btn-large " + getChannelClassNames(i)}
                        style={{ height: 90, width: 90,  color: 'black',  position: "relative"}}>
                        <p style={{ position: "absolute", top: 20, left: "-0.37em", bottom: 0, right: 0}}>{"Ch " + i}</p>

                        <p style={{ fontSize: 10, marginTop: 30 }}>Status: {test[i]}</p>
                    </button>
                )
            );
        }

        const cleanButton = (cleanDisabled) ? (
            <div
                style={{width:"100%", border:"3px solid #CCC", color: "black"}}
                className={"btn btn-large " + cleanClassNames}>
                {"Clean"}
            </div>
        ) : (
            <button
                style={{width:"100%", border:"3px solid #CCC", color: 'black'}}
                onClick={e => this.props.ws_sender({element: "clean", bank: this.props.bank})}
                className={"btn btn-large " + cleanClassNames}>
                {"Clean"}
            </button>
        );

        return (
            <div style={{padding: "10px"}}>
                <div className="panel-bank" style={{...{border: "3px solid #111", borderRadius: "10px", padding:"10px", float: "left"},...bankStyle}}>
                    <div style={{width: "100%"}}>
                        <h2>Bank {this.props.bank}</h2>
                        <div className="grid-bank" style={{display: "grid", gridGap: 10, gridTemplateColumns: "1fr 1fr", paddingBottom: 10}}>
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
