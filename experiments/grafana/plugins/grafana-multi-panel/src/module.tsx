// import { AppPlugin } from "@grafana/ui";
// import {RootPage} from "./RootPage";
// // import { MyPanel } from "./panels/components/MyPanel";
// // import { ExtraOptions, defaults } from "./panels/types";
// // import { MyPanelEditor } from "./panels/components/MyPanelEditor";
// // import { Root } from './Root';
//
//
// export const plugin = new AppPlugin()
//     .setRootPage(RootPage);
//     // .addConfigPage({
//     //     title: 'Page 1',
//     //     icon: 'fa fa-info',
//     //     body: ExamplePage1,
//     //     id: 'page1',
//     // })
//     // .addConfigPage({
//     //     title: 'Page 2',
//     //     icon: 'fa fa-user',
//     //     body: ExamplePage2,
//     //     id: 'page2',
//     // });
// Angular pages
import { ExampleConfigCtrl } from './legacy/config';
import { AngularExamplePageCtrl } from './legacy/angular_example_page';
import { AppPlugin } from '@grafana/ui';
import ExamplePage1 from "./config/ExamplePage1";
//import { ExamplePge1 } from './config/ExamplePage1';
import ExamplePage2  from './config/ExamplePage2';
//mport { ExampleRootPage } from './ExampleRootPage';

// Legacy exports just for testing
export {
    ExampleConfigCtrl as ConfigCtrl,
    AngularExamplePageCtrl, // Must match `pages.component` in plugin.json
};


// Libraries
import React, { PureComponent } from 'react';

// Types
import { AppRootProps } from '@grafana/ui';
import { NavModelItem } from "@grafana/data";

interface Props extends AppRootProps {}

const TAB_ID_A = 'A';
const TAB_ID_B = 'B';
const TAB_ID_C = 'C';

export class ExampleRootPage extends PureComponent<Props> {
    constructor(props: Props) {
        super(props);
    }

    componentDidMount() {
        this.updateNav();
    }

    componentDidUpdate(prevProps: Props) {
        if (this.props.query !== prevProps.query) {
            if (this.props.query.tab !== prevProps.query.tab) {
                this.updateNav();
            }
        }
    }

    updateNav() {
        const { path, onNavChanged, query, meta } = this.props;

        const tabs: NavModelItem[] = [];
        tabs.push({
            text: 'Tab A',
            icon: 'fa fa-fw fa-file-text-o',
            url: path + '?tab=' + TAB_ID_A,
            id: TAB_ID_A,
        });
        tabs.push({
            text: 'Tab B',
            icon: 'fa fa-fw fa-file-text-o',
            url: path + '?tab=' + TAB_ID_B,
            id: TAB_ID_B,
        });
        tabs.push({
            text: 'Tab C',
            icon: 'fa fa-fw fa-file-text-o',
            url: path + '?tab=' + TAB_ID_C,
            id: TAB_ID_C,
        });

        // Set the active tab
        let found = false;
        const selected = query.tab || TAB_ID_B;
        for (const tab of tabs) {
            tab.active = !found && selected === tab.id;
            if (tab.active) {
                found = true;
            }
        }
        if (!found) {
            tabs[0].active = true;
        }

        const node = {
            text: 'This is the Page title',
            img: meta.info.logos.large,
            subTitle: 'subtitle here',
            url: path,
            children: tabs,
        };



        // Update the page header
        onNavChanged({
            node: node,
            main: node,
        });
    }

    render() {
        const { path, query } = this.props;

        return (
            <div>
                QUERY: <pre>{JSON.stringify(query)}</pre>
                <br />
                <ul>
                    <li>
                        <a href={path + '?x=1'}>111</a>
                    </li>
                    <li>
                        <a href={path + '?x=AAA'}>AAA</a>
                    </li>
                    <li>
                        <a href={path + '?x=1&y=2&y=3'}>ZZZ</a>
                    </li>
                </ul>
            </div>
        );
    }
}


export const plugin = new AppPlugin()
    .setRootPage(ExampleRootPage)
    .addConfigPage({
        title: 'Page 1',
        icon: 'fa fa-info',
        body: ExamplePage1,
        id: 'page1',
    })
    .addConfigPage({
        title: 'Page 2',
        icon: 'fa fa-user',
        body: ExamplePage2,
        id: 'page2',
    });

