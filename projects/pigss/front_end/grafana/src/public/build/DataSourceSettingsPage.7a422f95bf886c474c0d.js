(window.webpackJsonp=window.webpackJsonp||[]).push([[7],{"/2Mn":function(e,t,a){"use strict";var n=a("q1tI"),r=a.n(n),o=a("ZFWI");t.a=function(e){var t=e.isReadOnly,a=e.onDelete,n=e.onSubmit,s=e.onTest;return r.a.createElement("div",{className:"gf-form-button-row"},!t&&r.a.createElement("button",{type:"submit",className:"btn btn-primary",disabled:t,onClick:function(e){return n(e)},"aria-label":"Save and Test button"},"Save & Test"),t&&r.a.createElement("button",{type:"submit",className:"btn btn-success",onClick:s},"Test"),r.a.createElement("button",{type:"submit",className:"btn btn-danger",disabled:t,onClick:a},"Delete"),r.a.createElement("a",{className:"btn btn-inverse",href:o.b.appSubUrl+"/datasources"},"Back"))}},"7iUX":function(e,t,a){"use strict";var n=a("mrSG"),r=a("q1tI"),o=a.n(r),s=a("kDLi"),i=a("PAeb");var u;t.a=function(e){var t=function(e){switch(e){case s.PluginState.alpha:return"Alpha Plugin: This plugin is a work in progress and updates may include breaking changes";case s.PluginState.beta:return"Beta Plugin: There could be bugs and minor breaking changes to this plugin"}return null}(e.state);return t?o.a.createElement(s.AlphaNotice,{state:e.state,text:t,className:Object(i.css)(u||(u=n.e(["\n        margin-left: 16px;\n      "],["\n        margin-left: 16px;\n      "])))}):null}},EREr:function(e,t,a){"use strict";a.d(t,"a",function(){return c});var n=a("mrSG"),r=a("q1tI"),o=a.n(r),s=a("LvDl"),i=a.n(s),u=a("t8hP"),c=function(e){function t(t){var a=e.call(this,t)||this;return a.onModelChanged=function(e){a.props.onModelChange(e)},a.scopeProps={ctrl:{datasourceMeta:t.dataSourceMeta,current:i.a.cloneDeep(t.dataSource)},onModelChanged:a.onModelChanged},a.onModelChanged=a.onModelChanged.bind(a),a}return n.c(t,e),t.prototype.componentDidMount=function(){var e=this.props.plugin;if(this.element&&!e.components.ConfigEditor){var t=Object(u.getAngularLoader)();this.component=t.load(this.element,this.scopeProps,'<plugin-component type="datasource-config-ctrl" />')}},t.prototype.componentDidUpdate=function(e){this.props.plugin.components.ConfigEditor||this.props.dataSource===e.dataSource||(this.scopeProps.ctrl.current=i.a.cloneDeep(this.props.dataSource),this.component.digest())},t.prototype.componentWillUnmount=function(){this.component&&this.component.destroy()},t.prototype.render=function(){var e=this,t=this.props,a=t.plugin,n=t.dataSource;return a?o.a.createElement("div",{ref:function(t){return e.element=t}},a.components.ConfigEditor&&o.a.createElement(a.components.ConfigEditor,{options:n,onOptionsChange:this.onModelChanged})):null},t}(r.PureComponent)},Jjpq:function(e,t,a){"use strict";var n=a("q1tI"),r=a.n(n),o=a("kDLi");t.a=function(e){var t=e.dataSourceName,a=e.isDefault,n=e.onDefaultChange,s=e.onNameChange;return r.a.createElement("div",{className:"gf-form-group"},r.a.createElement("div",{className:"gf-form-inline"},r.a.createElement("div",{className:"gf-form max-width-30",style:{marginRight:"3px"}},r.a.createElement(o.FormLabel,{tooltip:"The name is used when you select the data source in panels. The Default data source is preselected in new panels."},"Name"),r.a.createElement(o.Input,{className:"gf-form-input max-width-23",type:"text",value:t,placeholder:"Name",onChange:function(e){return s(e.target.value)},required:!0})),r.a.createElement(o.Switch,{label:"Default",checked:a,onChange:function(e){return n(e.target.checked)}})))}},Klwq:function(e,t,a){"use strict";a.r(t),function(e){a.d(t,"DataSourceSettingsPage",function(){return C});var n=a("mrSG"),r=a("q1tI"),o=a.n(r),s=a("0cfB"),i=a("/MKj"),u=a("4qC0"),c=a.n(u),l=a("ZGyg"),d=a("EREr"),p=a("Jjpq"),f=a("/2Mn"),m=a("Xmxp"),g=a("NXk7"),h=a("WnbS"),b=a("frIo"),S=a("5BCB"),v=a("lzJ5"),y=a("X+V3"),E=a("HUMP"),D=a("7iUX"),N=a("Vw/f"),C=function(e){function t(t){var a=e.call(this,t)||this;return a.onSubmit=function(e){return n.b(a,void 0,void 0,function(){return n.d(this,function(t){switch(t.label){case 0:return e.preventDefault(),[4,this.props.updateDataSource(n.a({},this.props.dataSource))];case 1:return t.sent(),this.testDataSource(),[2]}})})},a.onTest=function(e){return n.b(a,void 0,void 0,function(){return n.d(this,function(t){return e.preventDefault(),this.testDataSource(),[2]})})},a.onDelete=function(){m.b.emit("confirm-modal",{title:"Delete",text:"Are you sure you want to delete this data source?",yesText:"Delete",icon:"fa-trash",onConfirm:function(){a.confirmDelete()}})},a.confirmDelete=function(){a.props.deleteDataSource()},a.onModelChange=function(e){a.props.dataSourceLoaded(e)},a.state={plugin:t.plugin},a}return n.c(t,e),t.prototype.loadPlugin=function(e){return n.b(this,void 0,void 0,function(){var e,t,a;return n.d(this,function(n){switch(n.label){case 0:e=this.props.dataSourceMeta,n.label=1;case 1:return n.trys.push([1,3,,4]),[4,Object(N.b)(e)];case 2:return t=n.sent(),[3,4];case 3:return a=n.sent(),console.log("Failed to import plugin module",a),[3,4];case 4:return this.setState({plugin:t}),[2]}})})},t.prototype.componentDidMount=function(){return n.b(this,void 0,void 0,function(){var e,t,a,r;return n.d(this,function(n){switch(n.label){case 0:if(e=this.props,t=e.loadDataSource,a=e.pageId,isNaN(a))return this.setState({loadError:"Invalid ID"}),[2];n.label=1;case 1:return n.trys.push([1,5,,6]),[4,t(a)];case 2:return n.sent(),this.state.plugin?[3,4]:[4,this.loadPlugin()];case 3:n.sent(),n.label=4;case 4:return[3,6];case 5:return r=n.sent(),this.setState({loadError:r}),[3,6];case 6:return[2]}})})},t.prototype.isReadOnly=function(){return!0===this.props.dataSource.readOnly},t.prototype.renderIsReadOnlyMessage=function(){return o.a.createElement("div",{className:"grafana-info-box span8"},"This datasource was added by config and cannot be modified using the UI. Please contact your server admin to update this datasource.")},t.prototype.testDataSource=function(){return n.b(this,void 0,void 0,function(){var e,t=this;return n.d(this,function(a){switch(a.label){case 0:return[4,Object(h.a)().get(this.props.dataSource.name)];case 1:return(e=a.sent()).testDatasource?(this.setState({isTesting:!0,testingMessage:"Testing...",testingStatus:"info"}),Object(g.b)().withNoBackendCache(function(){return n.b(t,void 0,void 0,function(){var t,a,r;return n.d(this,function(n){switch(n.label){case 0:return n.trys.push([0,2,,3]),[4,e.testDatasource()];case 1:return t=n.sent(),this.setState({isTesting:!1,testingStatus:t.status,testingMessage:t.message}),[3,3];case 2:return a=n.sent(),r="",r=a.statusText?"HTTP Error "+a.statusText:a.message,this.setState({isTesting:!1,testingStatus:"error",testingMessage:r}),[3,3];case 3:return[2]}})})}),[2]):[2]}})})},Object.defineProperty(t.prototype,"hasDataSource",{get:function(){return this.props.dataSource.id>0},enumerable:!0,configurable:!0}),t.prototype.renderLoadError=function(e){var t=!1,a=e.toString();e.data?e.data.message&&(a=e.data.message):c()(e)&&(t=!0);var n={text:a,subTitle:"Data Source Error",icon:"fa fa-fw fa-warning"},r={node:n,main:n};return o.a.createElement(l.a,{navModel:r},o.a.createElement(l.a.Contents,null,o.a.createElement("div",null,o.a.createElement("div",{className:"gf-form-button-row"},t&&o.a.createElement("button",{type:"submit",className:"btn btn-danger",onClick:this.onDelete},"Delete"),o.a.createElement("a",{className:"btn btn-inverse",href:"datasources"},"Back")))))},t.prototype.renderConfigPageBody=function(e){var t,a,r=this.state.plugin;if(!r||!r.configPages)return null;try{for(var s=n.i(r.configPages),i=s.next();!i.done;i=s.next()){var u=i.value;if(u.id===e)return o.a.createElement(u.body,{plugin:r,query:this.props.query})}}catch(e){t={error:e}}finally{try{i&&!i.done&&(a=s.return)&&a.call(s)}finally{if(t)throw t.error}}return o.a.createElement("div",null,"Page Not Found: ",e)},t.prototype.renderSettings=function(){var e=this,t=this.props,a=t.dataSourceMeta,n=t.setDataSourceName,r=t.setIsDefault,s=t.dataSource,i=this.state,u=i.testingMessage,c=i.testingStatus,l=i.plugin;return o.a.createElement("form",{onSubmit:this.onSubmit},this.isReadOnly()&&this.renderIsReadOnlyMessage(),a.state&&o.a.createElement("div",{className:"gf-form"},o.a.createElement("label",{className:"gf-form-label width-10"},"Plugin state"),o.a.createElement("label",{className:"gf-form-label gf-form-label--transparent"},o.a.createElement(D.a,{state:a.state}))),o.a.createElement(p.a,{dataSourceName:s.name,isDefault:s.isDefault,onDefaultChange:function(e){return r(e)},onNameChange:function(e){return n(e)}}),l&&o.a.createElement(d.a,{plugin:l,dataSource:s,dataSourceMeta:a,onModelChange:this.onModelChange}),o.a.createElement("div",{className:"gf-form-group"},u&&o.a.createElement("div",{className:"alert-"+c+" alert","aria-label":"Datasource settings page Alert"},o.a.createElement("div",{className:"alert-icon"},"error"===c?o.a.createElement("i",{className:"fa fa-exclamation-triangle"}):o.a.createElement("i",{className:"fa fa-check"})),o.a.createElement("div",{className:"alert-body"},o.a.createElement("div",{className:"alert-title","aria-label":"Datasource settings page Alert message"},u)))),o.a.createElement(f.a,{onSubmit:function(t){return e.onSubmit(t)},isReadOnly:this.isReadOnly(),onDelete:this.onDelete,onTest:function(t){return e.onTest(t)}}))},t.prototype.render=function(){var e=this.props,t=e.navModel,a=e.page,n=this.state.loadError;return n?this.renderLoadError(n):o.a.createElement(l.a,{navModel:t},o.a.createElement(l.a.Contents,{isLoading:!this.hasDataSource},this.hasDataSource&&o.a.createElement("div",null,a?this.renderConfigPageBody(a):this.renderSettings())))},t}(r.PureComponent);var M={deleteDataSource:S.g,loadDataSource:S.h,setDataSourceName:S.k,updateDataSource:S.p,setIsDefault:S.o,dataSourceLoaded:S.b};t.default=Object(s.hot)(e)(Object(i.b)(function(e){var t=Object(y.a)(e.location),a=Object(b.a)(e.dataSources,t),n=e.location.query.page;return{navModel:Object(v.a)(e.navIndex,n?"datasource-page-"+n:"datasource-settings-"+t,Object(E.b)("settings")),dataSource:Object(b.a)(e.dataSources,t),dataSourceMeta:Object(b.b)(e.dataSources,a.type),pageId:t,query:e.location.query,page:n}},M)(C))}.call(this,a("3UD+")(e))},"X+V3":function(e,t,a){"use strict";a.d(t,"a",function(){return n}),a.d(t,"b",function(){return r});var n=function(e){return e.routeParams.id},r=function(e){return e.routeParams.page}},frIo:function(e,t,a){"use strict";a.d(t,"d",function(){return n}),a.d(t,"c",function(){return r}),a.d(t,"a",function(){return o}),a.d(t,"b",function(){return s}),a.d(t,"g",function(){return i}),a.d(t,"f",function(){return u}),a.d(t,"e",function(){return c});var n=function(e){var t=new RegExp(e.searchQuery,"i");return e.dataSources.filter(function(e){return t.test(e.name)||t.test(e.database)})},r=function(e){var t=new RegExp(e.dataSourceTypeSearchQuery,"i");return e.dataSourceTypes.filter(function(e){return t.test(e.name)})},o=function(e,t){return e.dataSource.id===parseInt(t,10)?e.dataSource:{}},s=function(e,t){return e.dataSourceMeta.id===t?e.dataSourceMeta:{}},i=function(e){return e.searchQuery},u=function(e){return e.layoutMode},c=function(e){return e.dataSourcesCount}}}]);
//# sourceMappingURL=DataSourceSettingsPage.7a422f95bf886c474c0d.js.map