define(["react","@grafana/ui"],function(e,t){return function(e){var t={};function n(r){if(t[r])return t[r].exports;var o=t[r]={i:r,l:!1,exports:{}};return e[r].call(o.exports,o,o.exports,n),o.l=!0,o.exports}return n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)n.d(r,o,function(t){return e[t]}.bind(null,o));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="",n(n.s=3)}([function(t,n){t.exports=e},function(e,n){e.exports=t},function(e,t,n){var r=n(6);"string"==typeof r&&(r=[[e.i,r,""]]);n(8)(r,{hmr:!0,transform:void 0,insertInto:void 0}),r.locals&&(e.exports=r.locals)},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.reactPanel=t.MyPanel=void 0;var r,o=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var n in e)if(Object.prototype.hasOwnProperty.call(e,n)){var r=Object.defineProperty&&Object.getOwnPropertyDescriptor?Object.getOwnPropertyDescriptor(e,n):{};r.get||r.set?Object.defineProperty(t,n,r):t[n]=e[n]}return t.default=e,t}(n(0)),a=n(1),i=(r=n(4))&&r.__esModule?r:{default:r},l=n(10);function s(e){return(s="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function u(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,r.key,r)}}function c(e){return(c=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function f(e,t){return(f=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}var p=function(e){function t(){return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t),function(e,t){return!t||"object"!==s(t)&&"function"!=typeof t?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(e):t}(this,c(t).apply(this,arguments))}var n,r;return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&f(e,t)}(t,o.Component),n=t,(r=[{key:"render",value:function(){return o.default.createElement("div",null,o.default.createElement(i.default,null))}}])&&u(n.prototype,r),t}();t.MyPanel=p;var d=new a.ReactPanelPlugin(p);(t.reactPanel=d).setEditor(l.NetworkSettingsEditor),d.setDefaults({networkType:"",ip:"",gateway:"",netmask:"",dns:""})},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.default=void 0;var r,o=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var n in e)if(Object.prototype.hasOwnProperty.call(e,n)){var r=Object.defineProperty&&Object.getOwnPropertyDescriptor?Object.getOwnPropertyDescriptor(e,n):{};r.get||r.set?Object.defineProperty(t,n,r):t[n]=e[n]}return t.default=e,t}(n(0)),a=(r=n(5))&&r.__esModule?r:{default:r};function i(e){return(i="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function l(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,r.key,r)}}function s(e,t){return!t||"object"!==i(t)&&"function"!=typeof t?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(e):t}function u(e){return(u=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function c(e,t){return(c=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}var f=function(e){function t(){return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t),s(this,u(t).apply(this,arguments))}var n,r;return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&c(e,t)}(t,o.Component),n=t,(r=[{key:"render",value:function(){return o.default.createElement("div",{className:"container"},o.default.createElement(a.default,null))}}])&&l(n.prototype,r),t}();t.default=f},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.default=void 0;var r=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var n in e)if(Object.prototype.hasOwnProperty.call(e,n)){var r=Object.defineProperty&&Object.getOwnPropertyDescriptor?Object.getOwnPropertyDescriptor(e,n):{};r.get||r.set?Object.defineProperty(t,n,r):t[n]=e[n]}return t.default=e,t}(n(0)),o=n(1);function a(e){return(a="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function i(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,r.key,r)}}function l(e,t){return!t||"object"!==a(t)&&"function"!=typeof t?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(e):t}function s(e){return(s=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function u(e,t){return(u=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}function c(e){return r.default.createElement("form",{className:"gf-form-group ng-pristine ng-invalid network-grid"},r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"Network Type"),r.default.createElement("input",{type:"text",className:"gf-form-input max-width-14 ng-not-empty ng-valid ng-valid-required",placeholder:"",value:e.networkType})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"IP"),r.default.createElement("input",{type:"text",className:"gf-form-input max-width-14",placeholder:"",value:e.ip})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"Gateway"),r.default.createElement("input",{type:"text",className:"gf-form-input max-width-14",placeholder:"",value:e.gateway})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"Netmask"),r.default.createElement("input",{type:"text",className:"gf-form-input max-width-14",placeholder:"",value:e.netmask})),r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"DNS"),r.default.createElement("input",{type:"text",className:"gf-form-input max-width-14",placeholder:"",value:e.dns})))}n(2);var f=function(e){function t(e){var n;return function(e,n){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this),(n=l(this,s(t).call(this,e))).state={networkType:"",ip:"",gateway:"",netmask:"",dns:"",fetch:null},n}var n,a;return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&u(e,t)}(t,r.Component),n=t,(a=[{key:"componentDidMount",value:function(){var e=this;fetch("http://localhost:3030/get_network_settings").then(function(e){return e.json()}).then(function(t){e.setState(function(){return{networkType:t.networkType,ip:t.ip,gateway:t.gateway,netmask:t.netmask,dns:t.dns}})})}},{key:"render",value:function(){var e=this;return r.default.createElement(o.ThemeContext.Consumer,null,function(t){return r.default.createElement("div",null,r.default.createElement(c,{networkType:e.state.networkType,ip:e.state.ip,gateway:e.state.gateway,netmask:e.state.netmask,dns:e.state.dns}))})}}])&&i(n.prototype,a),t}();t.default=f},function(e,t,n){(e.exports=n(7)(!0)).push([e.i,".network-editor-combo-box {\n  margin-bottom: -1px;\n}\n\n.network-editor-form {\n  padding-top: 2px;\n}\n\n.network-editor-button {\n  padding-top: 2px;\n}\n\n.network-grid {\n  padding-top: 2px;\n}\n","",{version:3,sources:["/home/gerald/git/picarro-networking-plugin-jsx/src/components/App.css"],names:[],mappings:"AAAA;EACE,oBAAoB;CACrB;;AAED;EACE,iBAAiB;CAClB;;AAED;EACE,iBAAiB;CAClB;;AAED;EACE,iBAAiB;CAClB",file:"App.css",sourcesContent:[".network-editor-combo-box {\n  margin-bottom: -1px;\n}\n\n.network-editor-form {\n  padding-top: 2px;\n}\n\n.network-editor-button {\n  padding-top: 2px;\n}\n\n.network-grid {\n  padding-top: 2px;\n}\n"],sourceRoot:""}])},function(e,t,n){"use strict";e.exports=function(e){var t=[];return t.toString=function(){return this.map(function(t){var n=function(e,t){var n,r=e[1]||"",o=e[3];if(!o)return r;if(t&&"function"==typeof btoa){var a=(n=o,"/*# sourceMappingURL=data:application/json;charset=utf-8;base64,"+btoa(unescape(encodeURIComponent(JSON.stringify(n))))+" */"),i=o.sources.map(function(e){return"/*# sourceURL="+o.sourceRoot+e+" */"});return[r].concat(i).concat([a]).join("\n")}return[r].join("\n")}(t,e);return t[2]?"@media "+t[2]+"{"+n+"}":n}).join("")},t.i=function(e,n){"string"==typeof e&&(e=[[null,e,""]]);for(var r={},o=0;o<this.length;o++){var a=this[o][0];"number"==typeof a&&(r[a]=!0)}for(o=0;o<e.length;o++){var i=e[o];"number"==typeof i[0]&&r[i[0]]||(n&&!i[2]?i[2]=n:n&&(i[2]="("+i[2]+") and ("+n+")"),t.push(i))}},t}},function(e,t,n){var r,o,a,i={},l=(r=function(){return window&&document&&document.all&&!window.atob},function(){return void 0===o&&(o=r.apply(this,arguments)),o}),s=(a={},function(e){if("function"==typeof e)return e();if(void 0===a[e]){var t=function(e){return document.querySelector(e)}.call(this,e);if(window.HTMLIFrameElement&&t instanceof window.HTMLIFrameElement)try{t=t.contentDocument.head}catch(e){t=null}a[e]=t}return a[e]}),u=null,c=0,f=[],p=n(9);function d(e,t){for(var n=0;n<e.length;n++){var r=e[n],o=i[r.id];if(o){o.refs++;for(var a=0;a<o.parts.length;a++)o.parts[a](r.parts[a]);for(;a<r.parts.length;a++)o.parts.push(g(r.parts[a],t))}else{var l=[];for(a=0;a<r.parts.length;a++)l.push(g(r.parts[a],t));i[r.id]={id:r.id,refs:1,parts:l}}}}function y(e,t){for(var n=[],r={},o=0;o<e.length;o++){var a=e[o],i=t.base?a[0]+t.base:a[0],l={css:a[1],media:a[2],sourceMap:a[3]};r[i]?r[i].parts.push(l):n.push(r[i]={id:i,parts:[l]})}return n}function m(e,t){var n=s(e.insertInto);if(!n)throw new Error("Couldn't find a style target. This probably means that the value for the 'insertInto' parameter is invalid.");var r=f[f.length-1];if("top"===e.insertAt)r?r.nextSibling?n.insertBefore(t,r.nextSibling):n.appendChild(t):n.insertBefore(t,n.firstChild),f.push(t);else if("bottom"===e.insertAt)n.appendChild(t);else{if("object"!=typeof e.insertAt||!e.insertAt.before)throw new Error("[Style Loader]\n\n Invalid value for parameter 'insertAt' ('options.insertAt') found.\n Must be 'top', 'bottom', or Object.\n (https://github.com/webpack-contrib/style-loader#insertat)\n");var o=s(e.insertInto+" "+e.insertAt.before);n.insertBefore(t,o)}}function b(e){if(null===e.parentNode)return!1;e.parentNode.removeChild(e);var t=f.indexOf(e);0<=t&&f.splice(t,1)}function h(e){var t=document.createElement("style");return void 0===e.attrs.type&&(e.attrs.type="text/css"),v(t,e.attrs),m(e,t),t}function v(e,t){Object.keys(t).forEach(function(n){e.setAttribute(n,t[n])})}function g(e,t){var n,r,o,a,i,l;if(t.transform&&e.css){if(!(a=t.transform(e.css)))return function(){};e.css=a}if(t.singleton){var s=c++;n=u||(u=h(t)),r=j.bind(null,n,s,!1),o=j.bind(null,n,s,!0)}else o=e.sourceMap&&"function"==typeof URL&&"function"==typeof URL.createObjectURL&&"function"==typeof URL.revokeObjectURL&&"function"==typeof Blob&&"function"==typeof btoa?(i=t,l=document.createElement("link"),void 0===i.attrs.type&&(i.attrs.type="text/css"),i.attrs.rel="stylesheet",v(l,i.attrs),m(i,l),r=function(e,t,n){var r=n.css,o=n.sourceMap,a=void 0===t.convertToAbsoluteUrls&&o;(t.convertToAbsoluteUrls||a)&&(r=p(r)),o&&(r+="\n/*# sourceMappingURL=data:application/json;base64,"+btoa(unescape(encodeURIComponent(JSON.stringify(o))))+" */");var i=new Blob([r],{type:"text/css"}),l=e.href;e.href=URL.createObjectURL(i),l&&URL.revokeObjectURL(l)}.bind(null,n=l,t),function(){b(n),n.href&&URL.revokeObjectURL(n.href)}):(n=h(t),r=function(e,t){var n=t.css,r=t.media;if(r&&e.setAttribute("media",r),e.styleSheet)e.styleSheet.cssText=n;else{for(;e.firstChild;)e.removeChild(e.firstChild);e.appendChild(document.createTextNode(n))}}.bind(null,n),function(){b(n)});return r(e),function(t){if(t){if(t.css===e.css&&t.media===e.media&&t.sourceMap===e.sourceMap)return;r(e=t)}else o()}}e.exports=function(e,t){if("undefined"!=typeof DEBUG&&DEBUG&&"object"!=typeof document)throw new Error("The style-loader cannot be used in a non-browser environment");(t=t||{}).attrs="object"==typeof t.attrs?t.attrs:{},t.singleton||"boolean"==typeof t.singleton||(t.singleton=l()),t.insertInto||(t.insertInto="head"),t.insertAt||(t.insertAt="bottom");var n=y(e,t);return d(n,t),function(e){for(var r=[],o=0;o<n.length;o++){var a=n[o];(l=i[a.id]).refs--,r.push(l)}for(e&&d(y(e,t),t),o=0;o<r.length;o++){var l;if(0===(l=r[o]).refs){for(var s=0;s<l.parts.length;s++)l.parts[s]();delete i[l.id]}}}};var w,O=(w=[],function(e,t){return w[e]=t,w.filter(Boolean).join("\n")});function j(e,t,n,r){var o=n?"":r.css;if(e.styleSheet)e.styleSheet.cssText=O(t,o);else{var a=document.createTextNode(o),i=e.childNodes;i[t]&&e.removeChild(i[t]),i.length?e.insertBefore(a,i[t]):e.appendChild(a)}}},function(e,t,n){"use strict";e.exports=function(e){var t="undefined"!=typeof window&&window.location;if(!t)throw new Error("fixUrls requires window.location");if(!e||"string"!=typeof e)return e;var n=t.protocol+"//"+t.host,r=n+t.pathname.replace(/\/[^\/]*$/,"/");return e.replace(/url\s*\(((?:[^)(]|\((?:[^)(]+|\([^)(]*\))*\))*)\)/gi,function(e,t){var o,a=t.trim().replace(/^"(.*)"$/,function(e,t){return t}).replace(/^'(.*)'$/,function(e,t){return t});return/^(#|data:|http:\/\/|https:\/\/|file:\/\/\/|\s*$)/i.test(a)?e:(o=0===a.indexOf("//")?a:0===a.indexOf("/")?n+a:r+a.replace(/^\.\//,""),"url("+JSON.stringify(o)+")")})}},function(e,t,n){"use strict";Object.defineProperty(t,"__esModule",{value:!0}),t.NetworkSettingsEditor=void 0;var r=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var n in e)if(Object.prototype.hasOwnProperty.call(e,n)){var r=Object.defineProperty&&Object.getOwnPropertyDescriptor?Object.getOwnPropertyDescriptor(e,n):{};r.get||r.set?Object.defineProperty(t,n,r):t[n]=e[n]}return t.default=e,t}(n(0)),o=n(1);function a(e){return(a="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function i(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function l(e,t){for(var n=0;n<t.length;n++){var r=t[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(e,r.key,r)}}function s(e){return(s=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function u(e){if(void 0===e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return e}function c(e,t){return(c=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}n(2);var f=function(e){function t(e){var n,r;return function(e,n){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this),this,(n=!(r=s(t).call(this,e))||"object"!==a(r)&&"function"!=typeof r?u(this):r).modes=[{value:"Static",label:"Static"},{value:"DHCP",label:"DHCP"}],n.state={networkType:n.props.networkType,ip:n.props.ip,gateway:n.props.gateway,netmask:n.props.netmask,dns:n.props.dns,btnEnabled:!1},n.handleChange=n.handleChange.bind(u(n)),n.handleSelectChange=n.handleSelectChange.bind(u(n)),n.handleClick=n.handleClick.bind(u(n)),n}var n,f;return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&c(e,t)}(t,r.Component),n=t,(f=[{key:"handleChange",value:function(e){var t=e.target,n=t.name,r=t.value;this.setState(i({},n,r)),this.setState({btnEnabled:!0})}},{key:"handleSelectChange",value:function(e){console.log(this.props),console.log(this.state),this.props.onChange(function(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{},r=Object.keys(n);"function"==typeof Object.getOwnPropertySymbols&&(r=r.concat(Object.getOwnPropertySymbols(n).filter(function(e){return Object.getOwnPropertyDescriptor(n,e).enumerable}))),r.forEach(function(t){i(e,t,n[t])})}return e}({},this.state.networkType,{selection:e.value})),console.log(this.state)}},{key:"handleClick",value:function(){console.log(this.state.networkType),fetch("http://localhost:3030/set_network_settings",{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify({networkType:this.state.networkType,ip:this.state.ip,gateway:this.state.gateway,netmask:this.state.netmask,dns:this.state.dns})})}},{key:"componentDidMount",value:function(){var e=this;fetch("http://localhost:3030/get_network_settings").then(function(e){return e.json()}).then(function(t){e.setState(function(){return{networkType:t.networkType,ip:t.ip,gateway:t.gateway,netmask:t.netmask,dns:t.dns}})})}},{key:"render",value:function(){return this.props.options.networkType,r.default.createElement(o.PanelOptionsGroup,{title:"Network Settings"},r.default.createElement("div",{className:"gf-form-inline network-editor-combo-box"},r.default.createElement("div",{className:"gf-form"},r.default.createElement("span",{className:"gf-form-label width-10"},"Network Type"),r.default.createElement(o.Select,{options:this.modes,name:"networkType",value:this.modes.find(function(e){return"Static"===e.value||"DHCP"}),placeholder:this.state.networkType,onChange:this.handleSelectChange,isLoading:console.log("Loading!"),backspaceRemovesValue:!0}))),r.default.createElement("div",{className:"network-editor-form"},r.default.createElement(o.FormField,{label:"IP",labelWidth:"10",placeholder:this.props.ip,onChange:this.handleChange,value:this.state.ip,name:"ip"}),r.default.createElement(o.FormField,{label:"Gateway",labelWidth:"10",placeholder:this.props.gateway,onChange:this.handleChange,value:this.state.gateway,name:"gateway"}),r.default.createElement(o.FormField,{label:"Netmask",labelWidth:"10",placeholder:this.props.netmask,onChange:this.handleChange,value:this.state.netmask,name:"netmask"}),r.default.createElement(o.FormField,{label:"DNS",labelWidth:"10",placeholder:this.props.dns,onChange:this.handleChange,value:this.state.dns,name:"dns"})),r.default.createElement("div",{className:"network-editor-button"},r.default.createElement("button",{className:"btn btn-primary",disabled:!this.state.btnEnabled,onClick:this.handleClick},"Apply")))}}])&&l(n.prototype,f),t}();t.NetworkSettingsEditor=f}])});
//# sourceMappingURL=module.js.map