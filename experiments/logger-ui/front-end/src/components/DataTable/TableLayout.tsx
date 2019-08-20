import React, { Component, Fragment } from 'react';
import { Cell } from './Cell';
import { TableProps } from './types';

interface Props extends TableProps {}

const tbody = [
  ['2019-08-01 01:13:14.281224', 'IDRIVER_192.168.10.103_subthread', 'flushing to db failed, try again in 5 seconds', '10'],
  ['2019-08-01 01:13:14.281224', 'IDRIVER_192.168.10.103_subthread', 'flushing to db failed, try again in 5 seconds', '20'],
  ['2019-08-01 01:13:14.281224', 'IDRIVER_192.168.10.103_subthread', 'flushing to db failed, try again in 5 seconds', '30'],
  [
    '2019-08-01 17:41:33.923678',
    'MadMapper',
    `Reading from /home/picarro/.config/picarro/madmapper.json:
{
  ""Name"": ""MadMapper"",
  ""Devices"": {
    ""Network_Devices"": {
      ""2755-SBDS2015"": {
        ""IP"": ""192.168.10.100"",
        ""SN"": ""2755-SBDS2015"",
        ""Driver"": ""IDriver"",
        ""RPC_Port"": 33000
      },
      ""2633-AMBDS2002"": {
        ""IP"": ""192.168.10.103"",
        ""SN"": ""2633-AMBDS2002"",
        ""Driver"": ""IDriver"",
        ""RPC_Port"": 33001
      }
    },
    ""Serial_Devices"": {
      ""/dev/ttyUSB1"": {
        ""Driver"": ""AlicatDriver"",
        ""Path"": ""/dev/ttyUSB1"",
        ""Baudrate"": 19200,
        ""RPC_Port"": 33020
      },
      ""/dev/ttyACM3"": {
        ""Driver"": ""PigletDriver"",
        ""Bank_ID"": 3,
        ""Topaz_A_HW_Rev"": ""Null"",
        ""Topaz_B_HW_Rev"": ""Null"",
        ""Whitfield_HW_Rev"": ""Null"",
        ""Path"": ""/dev/ttyACM3"",
        ""Baudrate"": 38400,
        ""RPC_Port"": 33042
      },
      ""/dev/ttyACM0"": {
        ""Driver"": ""PigletDriver"",
        ""Bank_ID"": 4,
        ""Topaz_A_HW_Rev"": ""Null"",
        ""Topaz_B_HW_Rev"": ""Null"",
        ""Whitfield_HW_Rev"": ""Null"",
        ""Path"": ""/dev/ttyACM0"",
        ""Baudrate"": 38400,
        ""RPC_Port"": 33043
      },
      ""/dev/ttyACM1"": {
        ""Driver"": ""NumatoDriver"",
        ""Path"": ""/dev/ttyACM1"",
        ""Baudrate"": 19200,
        ""Numato_ID"": 0,
        ""RPC_Port"": 33030
      },
      ""/dev/ttyACM2"": {
        ""Driver"": ""NumatoDriver"",
        ""Path"": ""/dev/ttyACM2"",
        ""Baudrate"": 19200,
        ""Numato_ID"": 1,
        ""RPC_Port"": 33031
      }
    }
  }
}`,
    '10',
  ],
];

export class TableLayout extends Component<Props, any> {
  constructor(props: any) {
    super(props);
    this.state = {
      level: '',
      limit: 0,
      date: '',
      tbody: [],
    };
    this.fetchLogs = this.fetchLogs.bind(this);
  }

  fetchLogs() {
    return tbody;
  }

  componentWillMount() {
    this.setState({ tbody: this.fetchLogs() });
  }

  componentDidUpdate(prevProps: Props) {
    if (
      this.props.options.level !== prevProps.options.level ||
      this.props.options.limit !== prevProps.options.limit ||
      this.props.options.date !== prevProps.options.date
    ) {
      console.log('Make call to the API');
      this.setState(() => {
        return {
          tbody: [
            ...this.fetchLogs(),
            ['2019-08-01 01:13:14.281224', 'IDRIVER_192.168.10.103_subthread', 'flushing to db failed, try again in 5 seconds', '90'],
          ],
        };
      });
    }
  }

  render() {
    const { options } = this.props;
    const { thead } = options;
    const data: any = this.state.tbody;

    const tableStyle = {
      border: '1px solid white',
      width: '100%',
    };

    const theadStyle = {
      border: '1px solid white',
      fontSize: '1.25em',
      fontWeight: 600,
    };

    const trStyle = {
      border: '1px solid white',
    };

    const tdStyle = {
      padding: '4px',
    };

    return (
      <Fragment>
        <div className="container-fluid">
          {tbody.map(cell => (
            <Cell key={Math.random()} data={cell} />
          ))}
        </div>
      </Fragment>
    );
  }
}
