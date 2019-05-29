import React, { PureComponent } from 'react';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux';
import Page from 'app/core/components/Page/Page';
import { getNavModel } from 'app/core/selectors/navModel';
import { NavModel } from 'app/types';
import {InstrumentsEditor} from './src/components/InstrumentsEditor';
import "./src/css/style.scss";

export interface Props {
  navModel: NavModel;
}
export interface State {
}
export class SystemConfigurationSettings extends PureComponent<Props, State> {
  render() {
    const { navModel } = this.props;
    return (
      <Page navModel={navModel}>
        <Page.Contents>
          <InstrumentsEditor />
        </Page.Contents>
      </Page>
    );
  }
}
function mapStateToProps(state) {
  return {
    navModel: getNavModel(state.navIndex, 'system_configuration_settings'),
  };
}
const mapDispatchToProps = {};
export default hot(module)(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )(SystemConfigurationSettings)
);
