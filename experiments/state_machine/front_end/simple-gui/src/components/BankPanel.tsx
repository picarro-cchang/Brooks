import React, {Component, PureComponent} from 'react';

interface BankPanelOptions {
    bank: number,
    uistatus: {
        bank?: {[bankNum:string]: string}
        clean?: {[bankNum:string]: string}
        channel?: {[bankNum:string]: {[channelNum:string]: string}}
    }
}

class BankPanel extends PureComponent<BankPanelOptions> {
    bankStyleOpt = {
        READY:{color:"#fff", backgroundColor:"#888"}, 
        ACTIVE:{color:"#fff", backgroundColor:"#080"}, 
        CLEAN:{color:"#fff", backgroundColor:"#008"}, 
        REFERENCE:{color:"#440", backgroundColor:"#CC0"}};
    cleanClassNameOpt = {
        DISABLED:"btn-light disabled", READY: "btn-light", ACTIVE:"btn-primary", CLEAN:"btn-primary"
    };
    channelClassNameOpt = {
        DISABLED:"btn-light disabled", READY: "btn-light", ACTIVE:"btn-success", CLEAN:"btn-primary", REFERENCE:"btn-light"
    };

    render() {
        let bankStyle = {};
        let cleanClassNames = "";
        let cleanDisabled = true;
        let getChannelClassNames = (_:number) => "";
        let getChannelDisabled = (_:number) => true;

        if ("bank" in (this.props.uistatus as any)) {
            const bankStatus: string = (this.props.uistatus.bank as any)[this.props.bank];
            const channelStatus: {[key:number]: string} = (this.props.uistatus.channel as any)[this.props.bank];
            const cleanStatus: string = (this.props.uistatus.clean as any)[this.props.bank];
            bankStyle = (this.bankStyleOpt as any)[bankStatus];
            cleanClassNames = (this.cleanClassNameOpt as any)[cleanStatus];
            cleanDisabled = cleanStatus === "DISABLED";
            getChannelClassNames = (chan) => (this.channelClassNameOpt as any)[(channelStatus as any)[chan]];
            getChannelDisabled = (chan) => (channelStatus as any)[chan] === "DISABLED";
        }
        let channelButtons = [];
        for (let i=1; i<=8; i++) {
            channelButtons.push(
                <button
                    disabled={getChannelDisabled(i)}
                    className={"btn btn-lg btn-bank " + getChannelClassNames(i)}>
                    Ch {i}
                </button>
            );
        }

        return (

            <div style={{padding: "10px"}}>
                <div className="panel-bank" style={{...{border: "3px solid #111", borderRadius: "10px", padding:"10px"},...bankStyle}}>
                    <div style={{width: "100%"}}>
                        <h2>Bank {this.props.bank}</h2>
                        <div className="grid-bank">
                            {channelButtons}
                        </div>
                        <button style={{width:"100%", border:"3px solid #CCC"}}
                            disabled={cleanDisabled}
                            className={"btn btn-lg " + cleanClassNames}>
                            Clean
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}
export default BankPanel;