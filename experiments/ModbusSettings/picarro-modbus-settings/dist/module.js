define(["@grafana/ui","react"],function(e,t){return function(e){var t={};function n(o){if(t[o])return t[o].exports;var r=t[o]={i:o,l:!1,exports:{}};return e[o].call(r.exports,r,r.exports,n),r.l=!0,r.exports}return n.m=e,n.c=t,n.d=function(e,t,o){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:o})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var o=Object.create(null);if(n.r(o),Object.defineProperty(o,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)n.d(o,r,function(t){return e[t]}.bind(null,r));return o},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="",n(n.s=3)}([function(t,n){t.exports=e},function(e,n){e.exports=t},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var o={postData:function(e,t){return console.log(t),fetch(e,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)}).then(function(e){if(!e.ok)throw Error("Network POST request failed");return e})},getRequest:function(e){return fetch(e,{method:"GET"}).then(function(e){if(!e.ok)throw Error("Network GET request failed");return e.json()})}};t.default=o},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.reactPanel=void 0;var o,r=n(0),a=n(4),u=n(6),l=n(7),i=(o=n(2))&&o.__esModule?o:{default:o},s=function(){return(s=Object.assign||function(e){for(var t,n=1,o=arguments.length;n<o;n++)for(var r in t=arguments[n])Object.prototype.hasOwnProperty.call(t,r)&&(e[r]=t[r]);return e}).apply(this,arguments)},c=t.reactPanel=new r.ReactPanelPlugin(a.ModbusPanel);console.log(l.defaults),i.default.getRequest("http://localhost:4000/modbus_settings").then(function(e){var t=s({},l.defaults);t.slaveId=parseInt(e.slave),t.tcpPort=parseInt(e.port),console.log(t),c.setEditor(u.ModbusPanelEditor),c.setDefaults(t)})},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.ModbusPanel=void 0;var o,r,a=n(1),u=(o=a)&&o.__esModule?o:{default:o},l=n(0),i=n(5),s=(r=function(e,t){return(r=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}r(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)}),c=function(e){function t(){return null!==e&&e.apply(this,arguments)||this}return s(t,e),t.prototype.render=function(){var e=this.props,t=e.options,n=e.width,o=e.height;return u.default.createElement(l.ThemeContext.Consumer,null,function(e){return u.default.createElement(i.ModbusLayout,{width:n,height:o,options:t,theme:e})})},t}(a.PureComponent);t.ModbusPanel=c},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.ModbusLayout=void 0;var o=n(1),r=u(o),a=u(n(2));function u(e){return e&&e.__esModule?e:{default:e}}var l,i=(l=function(e,t){return(l=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}l(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)}),s=function(e){function t(t){var n=e.call(this,t)||this;return n.state={ipAddress:"127.0.0.1"},n}return i(t,e),t.prototype.componentDidMount=function(){this.getIpAddress()},t.prototype.getIpAddress=function(){var e=this,t={};a.default.getRequest("http://localhost:4000/network").then(function(n){t.ipAddress=n.ip,console.log(t),e.setState(t)})},t.prototype.onSaveClick=function(e){var t=e.slaveId,n=e.tcpPort;console.log(t),console.log(n),a.default.postData("http://localhost:4000/modbus_settings",{slave:t,port:n})},t.prototype.render=function(){var e=this,t=this.props.options,n=t.slaveId,o=t.tcpPort;return r.default.createElement("div",null,r.default.createElement("div",{style:{display:"flex",width:"100%",height:"100%",flexDirection:"column"}}),r.default.createElement("div",{className:"gf-form-group"},r.default.createElement("div",{className:"gf-form margin-top-50"},r.default.createElement("span",{className:"gf-form-label min-width-10"},"Ip Address"),r.default.createElement("input",{type:"text",className:"gf-form-input",placeholder:"",value:this.state.ipAddress,readOnly:!0})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label min-width-10"},"Salve Id"),r.default.createElement("input",{type:"text",className:"gf-form-input",placeholder:"",value:n,readOnly:!0})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label min-width-10"},"TCP Port"),r.default.createElement("input",{type:"text",className:"gf-form-input",placeholder:"",value:o,readOnly:!0})),r.default.createElement("div",{className:"gf-form-button-row"},r.default.createElement("button",{onClick:function(){return e.onSaveClick(t)},className:"btn btn-primary"},"Save and Restart Server"))))},t}(o.Component);t.ModbusLayout=s},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.ModbusPanelEditor=void 0;var o,r,a=n(1),u=(o=a)&&o.__esModule?o:{default:o},l=n(0),i=(r=function(e,t){return(r=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}r(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)}),s=function(){return(s=Object.assign||function(e){for(var t,n=1,o=arguments.length;n<o;n++)for(var r in t=arguments[n])Object.prototype.hasOwnProperty.call(t,r)&&(e[r]=t[r]);return e}).apply(this,arguments)},c=function(e){function t(){var t=null!==e&&e.apply(this,arguments)||this;return t.labelWidth=8,t.onMinValueChange=function(e){var n=e.target;return t.props.onChange(s({},t.props.options,{slaveId:n.value}))},t.onMaxValueChange=function(e){var n=e.target;return t.props.onChange(s({},t.props.options,{tcpPort:n.value}))},t}return i(t,e),t.prototype.render=function(){var e=this.props.options,t=e.slaveId,n=e.tcpPort;return u.default.createElement(l.PanelOptionsGroup,{title:"Simple options"},u.default.createElement(l.FormField,{label:"Min value",labelWidth:this.labelWidth,onChange:this.onMinValueChange,value:t}),u.default.createElement(l.FormField,{label:"Max value",labelWidth:this.labelWidth,onChange:this.onMaxValueChange,value:n}))},t}(a.PureComponent);t.ModbusPanelEditor=c},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.defaults={slaveId:1,tcpPort:50500}}])});
//# sourceMappingURL=module.js.map