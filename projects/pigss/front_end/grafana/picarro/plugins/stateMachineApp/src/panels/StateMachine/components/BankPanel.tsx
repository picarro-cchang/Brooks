import React, { PureComponent } from "react";
import "./bankpanel.css";

export interface BankPanelOptions {
  bank: number;
  uistatus: {
    bank?: { [bankNum: string]: string };
    clean?: { [bankNum: string]: string };
    channel?: { [bankNum: string]: { [channelNum: string]: string } };
  };
  ws_sender: (o: object) => void;
  plan: {
    bank_names: {
      [key: number]: {
        name: string;
        channels: { [key: number]: string };
      };
    };
  };
}

class BankPanel extends PureComponent<BankPanelOptions> {
  bankStyleOpt = {
    READY: { color: "#424242", backgroundColor: "#e4e4e4" },
    ACTIVE: { color: "#fff", backgroundColor: "#56a64b" },
    CLEAN: { color: "#fff", backgroundColor: "#4BBEE3" },
    REFERENCE: { color: "#440", backgroundColor: "#e0b400" }
  };
  cleanClassNameOpt = {
    DISABLED: "btn-inverse-2 disabled",
    READY: "btn-ready",
    ACTIVE: "btn-light",
    CLEAN: "btn-secondary btn-clean-act"
  };
  channelClassNameOpt = {
    DISABLED: "btn-inverse-2 disabled",
    READY: "btn-ready",
    AVAILABLE: "btn-ready",
    ACTIVE: "btn-green",
    CLEAN: "btn-light",
    REFERENCE: "btn-warning"
  };

  render() {
    let bankStyle = {};
    let cleanClassNames = "";
    let cleanDisabled = true;
    let getChannelClassNames = (_: number) => "";
    let getChannelDisabled = (_: number) => true;
    let test = {};

    if ("bank" in (this.props.uistatus as any)) {
      const bankStatus: string = this.props.uistatus.bank && (this.props.uistatus.bank as any)[
        this.props.bank
      ];
      const channelStatus: { [key: number]: string } = this.props.uistatus.channel && (this.props.uistatus
        .channel as any)[this.props.bank];
      const cleanStatus: string = this.props.uistatus.clean && (this.props.uistatus.clean as any)[
        this.props.bank
      ];
      bankStyle = (this.bankStyleOpt as any)[bankStatus];
      cleanClassNames = (this.cleanClassNameOpt as any)[cleanStatus];
      cleanDisabled = cleanStatus !== "READY";
      getChannelClassNames = chan => {
        return this.channelClassNameOpt !== undefined && 
                channelStatus !== undefined && 
                (this.channelClassNameOpt as any)[(channelStatus as any)[chan]];
      }
      getChannelDisabled = chan => { return channelStatus !== undefined && (channelStatus as any)[chan] !== "READY" };
      test = channelStatus;
    }

    const channelButtons = [];
    for (let i = 1; i <= 8; i++) {
      channelButtons.push(
        getChannelDisabled(i) ? (
          <button
            key={i}
            id={"channel-" + i}
            className={"btn btn-large bank-btn " + getChannelClassNames(i)}
            style={{ color: "black" }}
          >
            <p className="chn-label">
              <u className={"chn-name-" + i}>
                {this.props.plan.bank_names[this.props.bank].channels[i]}
              </u>
            </p>
            <p id={"chn-status-" + i} className={"chn-status"}>
              {" "}
              {test && test[i]}{" "}
            </p>
          </button>
        ) : (
          <button
            onClick={e => {
              this.props.ws_sender({
                element: "channel",
                bank: this.props.bank,
                channel: i
              });
            }}
            id={"channel-" + i}
            disabled={getChannelDisabled(i)}
            key={i}
            className={"btn btn-large bank-btn " + getChannelClassNames(i)}
          >
            <p className="chn-label">
              <u className={"chn-name-" + i}>
                {this.props.plan.bank_names[this.props.bank].channels[i]}{" "}
              </u>
            </p>

            <p id={"chn-status-" + i} className={"chn-status"}>
              {" "}
              {test && test[i]}
            </p>
          </button>
        )
      );
    }

    const cleanButton = cleanDisabled ? (
      <div className={"btn btn-large btn-clean " + cleanClassNames}>
        {"Clean"}
      </div>
    ) : (
      <button
        id="clean"
        onClick={e =>
          this.props.ws_sender({ element: "clean", bank: this.props.bank })
        }
        className={"btn btn-large btn-clean " + cleanClassNames}
      >
        {"Clean"}
      </button>
    );
    const value: string = this.props.plan.bank_names[this.props.bank].name;
    return (
      <div>
        <div className="panel-bank" style={bankStyle}>
          <div style={{ width: "100%" }}>
            <h2 style={{ color: "#424242", marginBottom: "10px" }}>{value}</h2>
            <div className="grid-bank">{channelButtons}</div>
            {cleanButton}
          </div>
        </div>
      </div>
    );
  }
}
export default BankPanel;
