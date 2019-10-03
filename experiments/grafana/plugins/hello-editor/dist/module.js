define(["@grafana/ui","react"],function(e,t){return r={},n.m=o=[function(t,n){t.exports=e},function(e,n){e.exports=t},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.plugin=void 0;var o=n(0),r=n(3),l=n(5),u=n(6),a=t.plugin=new o.PanelPlugin(r.HelloPanel);a.setEditor(l.HelloPanelEditor),a.setDefaults(u.defaults)},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.HelloPanel=void 0;var o,r,l,u=n(1),a=(o=u)&&o.__esModule?o:{default:o},i=n(0),c=n(4),f=((r=function(e,t){return(r=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}r(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)})(p,l=u.PureComponent),p.prototype.render=function(){var e=this.props.options;return a.default.createElement(i.ThemeContext.Consumer,null,function(t){return a.default.createElement(c.HelloLayout,{options:e,theme:t})})},p);function p(){return null!==l&&l.apply(this,arguments)||this}t.HelloPanel=f},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.HelloLayout=void 0;var o,r,l,u=n(1),a=(o=u)&&o.__esModule?o:{default:o},i=((r=function(e,t){return(r=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}r(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)})(c,l=u.Component),c.prototype.render=function(){var e=this.props.options.worldString;return a.default.createElement("div",{className:"gf-form"},a.default.createElement("span",{className:"gf-form-label width-4"},"Hello"),a.default.createElement("input",{type:"text",className:"gf-form-input width-8",value:e}))},c);function c(e){var t=l.call(this,e)||this;return t.state={worldString:""},t}t.HelloLayout=i},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.HelloPanelEditor=void 0;var o,r,l,u=n(1),a=(o=u)&&o.__esModule?o:{default:o},i=n(0),c=(r=function(e,t){return(r=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)t.hasOwnProperty(n)&&(e[n]=t[n])})(e,t)},function(e,t){function n(){this.constructor=e}r(e,t),e.prototype=null===t?Object.create(t):(n.prototype=t.prototype,new n)}),f=function(){return(f=Object.assign||function(e){for(var t,n=1,o=arguments.length;n<o;n++)for(var r in t=arguments[n])Object.prototype.hasOwnProperty.call(t,r)&&(e[r]=t[r]);return e}).apply(this,arguments)},p=[{value:"World",label:"World"},{value:"Emma",label:"Emma"},{value:"Joel",label:"Joel"},{value:"Jordan",label:"Jordan"},{value:"Kevin",label:"Kevin"}],s=(c(d,l=u.PureComponent),d.prototype.render=function(){var e=this.props.options.worldString;return console.log(this.props.options),a.default.createElement(i.PanelOptionsGroup,{title:"Gauge value"},a.default.createElement("div",{className:"gf-form"},a.default.createElement(i.FormLabel,{width:4},"Name"),a.default.createElement(i.Select,{width:8,options:p,onChange:this.onNameChange,value:p.find(function(t){return t.value===e}),defaultValue:"World",backspaceRemovesValue:!0,isLoading:!0})))},d);function d(){var e=null!==l&&l.apply(this,arguments)||this;return e.onNameChange=function(t){return e.props.onOptionsChange(f({},e.props.options,{worldString:t.value}))},e}t.HelloPanelEditor=s},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.defaults={worldString:"World"}}],n.c=r,n.d=function(e,t,o){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:o})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var o=Object.create(null);if(n.r(o),Object.defineProperty(o,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)n.d(o,r,function(t){return e[t]}.bind(null,r));return o},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="",n(n.s=2);function n(e){if(r[e])return r[e].exports;var t=r[e]={i:e,l:!1,exports:{}};return o[e].call(t.exports,t,t.exports,n),t.l=!0,t.exports}var o,r});
//# sourceMappingURL=module.js.map