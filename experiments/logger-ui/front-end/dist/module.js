define(["@grafana/data","@grafana/ui","react"], function(__WEBPACK_EXTERNAL_MODULE__grafana_data__, __WEBPACK_EXTERNAL_MODULE__grafana_ui__, __WEBPACK_EXTERNAL_MODULE_react__) { return /******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "/";
/******/
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = "./module.tsx");
/******/ })
/************************************************************************/
/******/ ({

/***/ "../node_modules/css-loader/dist/cjs.js?!../node_modules/postcss-loader/src/index.js?!../node_modules/sass-loader/lib/loader.js!./components/Cell/Cells.css":
/*!***************************************************************************************************************************************************************************!*\
  !*** ../node_modules/css-loader/dist/cjs.js??ref--7-1!../node_modules/postcss-loader/src??ref--7-2!../node_modules/sass-loader/lib/loader.js!./components/Cell/Cells.css ***!
  \***************************************************************************************************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__(/*! ../../../node_modules/css-loader/dist/runtime/api.js */ "../node_modules/css-loader/dist/runtime/api.js")(true);
// Module
exports.push([module.i, ".log-row {\n  padding-left: 12px;\n  margin-bottom: 6px;\n  border-left: 6px solid #828282;\n  border-radius: 6px; }\n\n.log-fields {\n  margin: 4px; }\n\n.client-name {\n  background-color: #00a3da;\n  color: rgba(60,60,60,0.96863);\n  padding: 0px 8px 0px 8px;\n  font-weight: 600; }\n\n.severity-level-10 {\n  background-color: #f7a7a7;\n  color: rgba(60,60,60,0.96863);\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.severity-level-20 {\n  background-color: #fd7474;\n  color: rgba(60,60,60,0.96863);\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.severity-level-30 {\n  background-color: #ff6f6f;\n  color: #000;\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.log-message {\n  border-bottom: 2px solid #5f5f5f; }\n", "",{"version":3,"sources":["Cells.css"],"names":[],"mappings":"AAAA;EACE,kBAAkB;EAClB,kBAAkB;EAClB,8BAA8B;EAC9B,kBAAkB,EAAE;;AAEtB;EACE,WAAW,EAAE;;AAEf;EACE,yBAAyB;EACzB,6BAAgB;EAChB,wBAAwB;EACxB,gBAAgB,EAAE;;AAEpB;EACE,yBAAyB;EACzB,6BAAgB;EAChB,gBAAgB;EAChB,wBAAwB,EAAE;;AAE5B;EACE,yBAAyB;EACzB,6BAAgB;EAChB,gBAAgB;EAChB,wBAAwB,EAAE;;AAE5B;EACE,yBAAyB;EACzB,WAAW;EACX,gBAAgB;EAChB,wBAAwB,EAAE;;AAE5B;EACE,gCAAgC,EAAE","file":"Cells.css","sourcesContent":[".log-row {\n  padding-left: 12px;\n  margin-bottom: 6px;\n  border-left: 6px solid #828282;\n  border-radius: 6px; }\n\n.log-fields {\n  margin: 4px; }\n\n.client-name {\n  background-color: #00a3da;\n  color: #3c3c3cf7;\n  padding: 0px 8px 0px 8px;\n  font-weight: 600; }\n\n.severity-level-10 {\n  background-color: #f7a7a7;\n  color: #3c3c3cf7;\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.severity-level-20 {\n  background-color: #fd7474;\n  color: #3c3c3cf7;\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.severity-level-30 {\n  background-color: #ff6f6f;\n  color: #000;\n  font-weight: 600;\n  padding: 0px 8px 0px 8px; }\n\n.log-message {\n  border-bottom: 2px solid #5f5f5f; }\n"]}]);


/***/ }),

/***/ "../node_modules/css-loader/dist/runtime/api.js":
/*!******************************************************!*\
  !*** ../node_modules/css-loader/dist/runtime/api.js ***!
  \******************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

"use strict";


/*
  MIT License http://www.opensource.org/licenses/mit-license.php
  Author Tobias Koppers @sokra
*/
// css base code, injected by the css-loader
// eslint-disable-next-line func-names
module.exports = function (useSourceMap) {
  var list = []; // return the list of modules as css string

  list.toString = function toString() {
    return this.map(function (item) {
      var content = cssWithMappingToString(item, useSourceMap);

      if (item[2]) {
        return "@media ".concat(item[2], "{").concat(content, "}");
      }

      return content;
    }).join('');
  }; // import a list of modules into the list
  // eslint-disable-next-line func-names


  list.i = function (modules, mediaQuery) {
    if (typeof modules === 'string') {
      // eslint-disable-next-line no-param-reassign
      modules = [[null, modules, '']];
    }

    var alreadyImportedModules = {};

    for (var i = 0; i < this.length; i++) {
      // eslint-disable-next-line prefer-destructuring
      var id = this[i][0];

      if (id != null) {
        alreadyImportedModules[id] = true;
      }
    }

    for (var _i = 0; _i < modules.length; _i++) {
      var item = modules[_i]; // skip already imported module
      // this implementation is not 100% perfect for weird media query combinations
      // when a module is imported multiple times with different media queries.
      // I hope this will never occur (Hey this way we have smaller bundles)

      if (item[0] == null || !alreadyImportedModules[item[0]]) {
        if (mediaQuery && !item[2]) {
          item[2] = mediaQuery;
        } else if (mediaQuery) {
          item[2] = "(".concat(item[2], ") and (").concat(mediaQuery, ")");
        }

        list.push(item);
      }
    }
  };

  return list;
};

function cssWithMappingToString(item, useSourceMap) {
  var content = item[1] || ''; // eslint-disable-next-line prefer-destructuring

  var cssMapping = item[3];

  if (!cssMapping) {
    return content;
  }

  if (useSourceMap && typeof btoa === 'function') {
    var sourceMapping = toComment(cssMapping);
    var sourceURLs = cssMapping.sources.map(function (source) {
      return "/*# sourceURL=".concat(cssMapping.sourceRoot).concat(source, " */");
    });
    return [content].concat(sourceURLs).concat([sourceMapping]).join('\n');
  }

  return [content].join('\n');
} // Adapted from convert-source-map (MIT)


function toComment(sourceMap) {
  // eslint-disable-next-line no-undef
  var base64 = btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap))));
  var data = "sourceMappingURL=data:application/json;charset=utf-8;base64,".concat(base64);
  return "/*# ".concat(data, " */");
}

/***/ }),

/***/ "../node_modules/style-loader/lib/addStyles.js":
/*!*****************************************************!*\
  !*** ../node_modules/style-loader/lib/addStyles.js ***!
  \*****************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

/*
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Tobias Koppers @sokra
*/

var stylesInDom = {};

var	memoize = function (fn) {
	var memo;

	return function () {
		if (typeof memo === "undefined") memo = fn.apply(this, arguments);
		return memo;
	};
};

var isOldIE = memoize(function () {
	// Test for IE <= 9 as proposed by Browserhacks
	// @see http://browserhacks.com/#hack-e71d8692f65334173fee715c222cb805
	// Tests for existence of standard globals is to allow style-loader
	// to operate correctly into non-standard environments
	// @see https://github.com/webpack-contrib/style-loader/issues/177
	return window && document && document.all && !window.atob;
});

var getTarget = function (target, parent) {
  if (parent){
    return parent.querySelector(target);
  }
  return document.querySelector(target);
};

var getElement = (function (fn) {
	var memo = {};

	return function(target, parent) {
                // If passing function in options, then use it for resolve "head" element.
                // Useful for Shadow Root style i.e
                // {
                //   insertInto: function () { return document.querySelector("#foo").shadowRoot }
                // }
                if (typeof target === 'function') {
                        return target();
                }
                if (typeof memo[target] === "undefined") {
			var styleTarget = getTarget.call(this, target, parent);
			// Special case to return head of iframe instead of iframe itself
			if (window.HTMLIFrameElement && styleTarget instanceof window.HTMLIFrameElement) {
				try {
					// This will throw an exception if access to iframe is blocked
					// due to cross-origin restrictions
					styleTarget = styleTarget.contentDocument.head;
				} catch(e) {
					styleTarget = null;
				}
			}
			memo[target] = styleTarget;
		}
		return memo[target]
	};
})();

var singleton = null;
var	singletonCounter = 0;
var	stylesInsertedAtTop = [];

var	fixUrls = __webpack_require__(/*! ./urls */ "../node_modules/style-loader/lib/urls.js");

module.exports = function(list, options) {
	if (typeof DEBUG !== "undefined" && DEBUG) {
		if (typeof document !== "object") throw new Error("The style-loader cannot be used in a non-browser environment");
	}

	options = options || {};

	options.attrs = typeof options.attrs === "object" ? options.attrs : {};

	// Force single-tag solution on IE6-9, which has a hard limit on the # of <style>
	// tags it will allow on a page
	if (!options.singleton && typeof options.singleton !== "boolean") options.singleton = isOldIE();

	// By default, add <style> tags to the <head> element
        if (!options.insertInto) options.insertInto = "head";

	// By default, add <style> tags to the bottom of the target
	if (!options.insertAt) options.insertAt = "bottom";

	var styles = listToStyles(list, options);

	addStylesToDom(styles, options);

	return function update (newList) {
		var mayRemove = [];

		for (var i = 0; i < styles.length; i++) {
			var item = styles[i];
			var domStyle = stylesInDom[item.id];

			domStyle.refs--;
			mayRemove.push(domStyle);
		}

		if(newList) {
			var newStyles = listToStyles(newList, options);
			addStylesToDom(newStyles, options);
		}

		for (var i = 0; i < mayRemove.length; i++) {
			var domStyle = mayRemove[i];

			if(domStyle.refs === 0) {
				for (var j = 0; j < domStyle.parts.length; j++) domStyle.parts[j]();

				delete stylesInDom[domStyle.id];
			}
		}
	};
};

function addStylesToDom (styles, options) {
	for (var i = 0; i < styles.length; i++) {
		var item = styles[i];
		var domStyle = stylesInDom[item.id];

		if(domStyle) {
			domStyle.refs++;

			for(var j = 0; j < domStyle.parts.length; j++) {
				domStyle.parts[j](item.parts[j]);
			}

			for(; j < item.parts.length; j++) {
				domStyle.parts.push(addStyle(item.parts[j], options));
			}
		} else {
			var parts = [];

			for(var j = 0; j < item.parts.length; j++) {
				parts.push(addStyle(item.parts[j], options));
			}

			stylesInDom[item.id] = {id: item.id, refs: 1, parts: parts};
		}
	}
}

function listToStyles (list, options) {
	var styles = [];
	var newStyles = {};

	for (var i = 0; i < list.length; i++) {
		var item = list[i];
		var id = options.base ? item[0] + options.base : item[0];
		var css = item[1];
		var media = item[2];
		var sourceMap = item[3];
		var part = {css: css, media: media, sourceMap: sourceMap};

		if(!newStyles[id]) styles.push(newStyles[id] = {id: id, parts: [part]});
		else newStyles[id].parts.push(part);
	}

	return styles;
}

function insertStyleElement (options, style) {
	var target = getElement(options.insertInto)

	if (!target) {
		throw new Error("Couldn't find a style target. This probably means that the value for the 'insertInto' parameter is invalid.");
	}

	var lastStyleElementInsertedAtTop = stylesInsertedAtTop[stylesInsertedAtTop.length - 1];

	if (options.insertAt === "top") {
		if (!lastStyleElementInsertedAtTop) {
			target.insertBefore(style, target.firstChild);
		} else if (lastStyleElementInsertedAtTop.nextSibling) {
			target.insertBefore(style, lastStyleElementInsertedAtTop.nextSibling);
		} else {
			target.appendChild(style);
		}
		stylesInsertedAtTop.push(style);
	} else if (options.insertAt === "bottom") {
		target.appendChild(style);
	} else if (typeof options.insertAt === "object" && options.insertAt.before) {
		var nextSibling = getElement(options.insertAt.before, target);
		target.insertBefore(style, nextSibling);
	} else {
		throw new Error("[Style Loader]\n\n Invalid value for parameter 'insertAt' ('options.insertAt') found.\n Must be 'top', 'bottom', or Object.\n (https://github.com/webpack-contrib/style-loader#insertat)\n");
	}
}

function removeStyleElement (style) {
	if (style.parentNode === null) return false;
	style.parentNode.removeChild(style);

	var idx = stylesInsertedAtTop.indexOf(style);
	if(idx >= 0) {
		stylesInsertedAtTop.splice(idx, 1);
	}
}

function createStyleElement (options) {
	var style = document.createElement("style");

	if(options.attrs.type === undefined) {
		options.attrs.type = "text/css";
	}

	if(options.attrs.nonce === undefined) {
		var nonce = getNonce();
		if (nonce) {
			options.attrs.nonce = nonce;
		}
	}

	addAttrs(style, options.attrs);
	insertStyleElement(options, style);

	return style;
}

function createLinkElement (options) {
	var link = document.createElement("link");

	if(options.attrs.type === undefined) {
		options.attrs.type = "text/css";
	}
	options.attrs.rel = "stylesheet";

	addAttrs(link, options.attrs);
	insertStyleElement(options, link);

	return link;
}

function addAttrs (el, attrs) {
	Object.keys(attrs).forEach(function (key) {
		el.setAttribute(key, attrs[key]);
	});
}

function getNonce() {
	if (false) {}

	return __webpack_require__.nc;
}

function addStyle (obj, options) {
	var style, update, remove, result;

	// If a transform function was defined, run it on the css
	if (options.transform && obj.css) {
	    result = typeof options.transform === 'function'
		 ? options.transform(obj.css) 
		 : options.transform.default(obj.css);

	    if (result) {
	    	// If transform returns a value, use that instead of the original css.
	    	// This allows running runtime transformations on the css.
	    	obj.css = result;
	    } else {
	    	// If the transform function returns a falsy value, don't add this css.
	    	// This allows conditional loading of css
	    	return function() {
	    		// noop
	    	};
	    }
	}

	if (options.singleton) {
		var styleIndex = singletonCounter++;

		style = singleton || (singleton = createStyleElement(options));

		update = applyToSingletonTag.bind(null, style, styleIndex, false);
		remove = applyToSingletonTag.bind(null, style, styleIndex, true);

	} else if (
		obj.sourceMap &&
		typeof URL === "function" &&
		typeof URL.createObjectURL === "function" &&
		typeof URL.revokeObjectURL === "function" &&
		typeof Blob === "function" &&
		typeof btoa === "function"
	) {
		style = createLinkElement(options);
		update = updateLink.bind(null, style, options);
		remove = function () {
			removeStyleElement(style);

			if(style.href) URL.revokeObjectURL(style.href);
		};
	} else {
		style = createStyleElement(options);
		update = applyToTag.bind(null, style);
		remove = function () {
			removeStyleElement(style);
		};
	}

	update(obj);

	return function updateStyle (newObj) {
		if (newObj) {
			if (
				newObj.css === obj.css &&
				newObj.media === obj.media &&
				newObj.sourceMap === obj.sourceMap
			) {
				return;
			}

			update(obj = newObj);
		} else {
			remove();
		}
	};
}

var replaceText = (function () {
	var textStore = [];

	return function (index, replacement) {
		textStore[index] = replacement;

		return textStore.filter(Boolean).join('\n');
	};
})();

function applyToSingletonTag (style, index, remove, obj) {
	var css = remove ? "" : obj.css;

	if (style.styleSheet) {
		style.styleSheet.cssText = replaceText(index, css);
	} else {
		var cssNode = document.createTextNode(css);
		var childNodes = style.childNodes;

		if (childNodes[index]) style.removeChild(childNodes[index]);

		if (childNodes.length) {
			style.insertBefore(cssNode, childNodes[index]);
		} else {
			style.appendChild(cssNode);
		}
	}
}

function applyToTag (style, obj) {
	var css = obj.css;
	var media = obj.media;

	if(media) {
		style.setAttribute("media", media)
	}

	if(style.styleSheet) {
		style.styleSheet.cssText = css;
	} else {
		while(style.firstChild) {
			style.removeChild(style.firstChild);
		}

		style.appendChild(document.createTextNode(css));
	}
}

function updateLink (link, options, obj) {
	var css = obj.css;
	var sourceMap = obj.sourceMap;

	/*
		If convertToAbsoluteUrls isn't defined, but sourcemaps are enabled
		and there is no publicPath defined then lets turn convertToAbsoluteUrls
		on by default.  Otherwise default to the convertToAbsoluteUrls option
		directly
	*/
	var autoFixUrls = options.convertToAbsoluteUrls === undefined && sourceMap;

	if (options.convertToAbsoluteUrls || autoFixUrls) {
		css = fixUrls(css);
	}

	if (sourceMap) {
		// http://stackoverflow.com/a/26603875
		css += "\n/*# sourceMappingURL=data:application/json;base64," + btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap)))) + " */";
	}

	var blob = new Blob([css], { type: "text/css" });

	var oldSrc = link.href;

	link.href = URL.createObjectURL(blob);

	if(oldSrc) URL.revokeObjectURL(oldSrc);
}


/***/ }),

/***/ "../node_modules/style-loader/lib/urls.js":
/*!************************************************!*\
  !*** ../node_modules/style-loader/lib/urls.js ***!
  \************************************************/
/*! no static exports found */
/***/ (function(module, exports) {


/**
 * When source maps are enabled, `style-loader` uses a link element with a data-uri to
 * embed the css on the page. This breaks all relative urls because now they are relative to a
 * bundle instead of the current page.
 *
 * One solution is to only use full urls, but that may be impossible.
 *
 * Instead, this function "fixes" the relative urls to be absolute according to the current page location.
 *
 * A rudimentary test suite is located at `test/fixUrls.js` and can be run via the `npm test` command.
 *
 */

module.exports = function (css) {
  // get current location
  var location = typeof window !== "undefined" && window.location;

  if (!location) {
    throw new Error("fixUrls requires window.location");
  }

	// blank or null?
	if (!css || typeof css !== "string") {
	  return css;
  }

  var baseUrl = location.protocol + "//" + location.host;
  var currentDir = baseUrl + location.pathname.replace(/\/[^\/]*$/, "/");

	// convert each url(...)
	/*
	This regular expression is just a way to recursively match brackets within
	a string.

	 /url\s*\(  = Match on the word "url" with any whitespace after it and then a parens
	   (  = Start a capturing group
	     (?:  = Start a non-capturing group
	         [^)(]  = Match anything that isn't a parentheses
	         |  = OR
	         \(  = Match a start parentheses
	             (?:  = Start another non-capturing groups
	                 [^)(]+  = Match anything that isn't a parentheses
	                 |  = OR
	                 \(  = Match a start parentheses
	                     [^)(]*  = Match anything that isn't a parentheses
	                 \)  = Match a end parentheses
	             )  = End Group
              *\) = Match anything and then a close parens
          )  = Close non-capturing group
          *  = Match anything
       )  = Close capturing group
	 \)  = Match a close parens

	 /gi  = Get all matches, not the first.  Be case insensitive.
	 */
	var fixedCss = css.replace(/url\s*\(((?:[^)(]|\((?:[^)(]+|\([^)(]*\))*\))*)\)/gi, function(fullMatch, origUrl) {
		// strip quotes (if they exist)
		var unquotedOrigUrl = origUrl
			.trim()
			.replace(/^"(.*)"$/, function(o, $1){ return $1; })
			.replace(/^'(.*)'$/, function(o, $1){ return $1; });

		// already a full url? no change
		if (/^(#|data:|http:\/\/|https:\/\/|file:\/\/\/|\s*$)/i.test(unquotedOrigUrl)) {
		  return fullMatch;
		}

		// convert the url to a full url
		var newUrl;

		if (unquotedOrigUrl.indexOf("//") === 0) {
		  	//TODO: should we add protocol?
			newUrl = unquotedOrigUrl;
		} else if (unquotedOrigUrl.indexOf("/") === 0) {
			// path should be relative to the base url
			newUrl = baseUrl + unquotedOrigUrl; // already starts with '/'
		} else {
			// path should be relative to current directory
			newUrl = currentDir + unquotedOrigUrl.replace(/^\.\//, ""); // Strip leading './'
		}

		// send back the fixed url(...)
		return "url(" + JSON.stringify(newUrl) + ")";
	});

	// send back the fixed css
	return fixedCss;
};


/***/ }),

/***/ "../node_modules/tslib/tslib.es6.js":
/*!******************************************!*\
  !*** ../node_modules/tslib/tslib.es6.js ***!
  \******************************************/
/*! exports provided: __extends, __assign, __rest, __decorate, __param, __metadata, __awaiter, __generator, __exportStar, __values, __read, __spread, __spreadArrays, __await, __asyncGenerator, __asyncDelegator, __asyncValues, __makeTemplateObject, __importStar, __importDefault */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__extends", function() { return __extends; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__assign", function() { return __assign; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__rest", function() { return __rest; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__decorate", function() { return __decorate; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__param", function() { return __param; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__metadata", function() { return __metadata; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__awaiter", function() { return __awaiter; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__generator", function() { return __generator; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__exportStar", function() { return __exportStar; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__values", function() { return __values; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__read", function() { return __read; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__spread", function() { return __spread; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__spreadArrays", function() { return __spreadArrays; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__await", function() { return __await; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__asyncGenerator", function() { return __asyncGenerator; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__asyncDelegator", function() { return __asyncDelegator; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__asyncValues", function() { return __asyncValues; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__makeTemplateObject", function() { return __makeTemplateObject; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__importStar", function() { return __importStar; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "__importDefault", function() { return __importDefault; });
/*! *****************************************************************************
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
MERCHANTABLITY OR NON-INFRINGEMENT.

See the Apache Version 2.0 License for specific language governing permissions
and limitations under the License.
***************************************************************************** */
/* global Reflect, Promise */

var extendStatics = function(d, b) {
    extendStatics = Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
        function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
    return extendStatics(d, b);
};

function __extends(d, b) {
    extendStatics(d, b);
    function __() { this.constructor = d; }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
}

var __assign = function() {
    __assign = Object.assign || function __assign(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }
        return t;
    }
    return __assign.apply(this, arguments);
}

function __rest(s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
}

function __decorate(decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
}

function __param(paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
}

function __metadata(metadataKey, metadataValue) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(metadataKey, metadataValue);
}

function __awaiter(thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
}

function __generator(thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
}

function __exportStar(m, exports) {
    for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}

function __values(o) {
    var m = typeof Symbol === "function" && o[Symbol.iterator], i = 0;
    if (m) return m.call(o);
    return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
}

function __read(o, n) {
    var m = typeof Symbol === "function" && o[Symbol.iterator];
    if (!m) return o;
    var i = m.call(o), r, ar = [], e;
    try {
        while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);
    }
    catch (error) { e = { error: error }; }
    finally {
        try {
            if (r && !r.done && (m = i["return"])) m.call(i);
        }
        finally { if (e) throw e.error; }
    }
    return ar;
}

function __spread() {
    for (var ar = [], i = 0; i < arguments.length; i++)
        ar = ar.concat(__read(arguments[i]));
    return ar;
}

function __spreadArrays() {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};

function __await(v) {
    return this instanceof __await ? (this.v = v, this) : new __await(v);
}

function __asyncGenerator(thisArg, _arguments, generator) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var g = generator.apply(thisArg, _arguments || []), i, q = [];
    return i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i;
    function verb(n) { if (g[n]) i[n] = function (v) { return new Promise(function (a, b) { q.push([n, v, a, b]) > 1 || resume(n, v); }); }; }
    function resume(n, v) { try { step(g[n](v)); } catch (e) { settle(q[0][3], e); } }
    function step(r) { r.value instanceof __await ? Promise.resolve(r.value.v).then(fulfill, reject) : settle(q[0][2], r); }
    function fulfill(value) { resume("next", value); }
    function reject(value) { resume("throw", value); }
    function settle(f, v) { if (f(v), q.shift(), q.length) resume(q[0][0], q[0][1]); }
}

function __asyncDelegator(o) {
    var i, p;
    return i = {}, verb("next"), verb("throw", function (e) { throw e; }), verb("return"), i[Symbol.iterator] = function () { return this; }, i;
    function verb(n, f) { i[n] = o[n] ? function (v) { return (p = !p) ? { value: __await(o[n](v)), done: n === "return" } : f ? f(v) : v; } : f; }
}

function __asyncValues(o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
}

function __makeTemplateObject(cooked, raw) {
    if (Object.defineProperty) { Object.defineProperty(cooked, "raw", { value: raw }); } else { cooked.raw = raw; }
    return cooked;
};

function __importStar(mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result.default = mod;
    return result;
}

function __importDefault(mod) {
    return (mod && mod.__esModule) ? mod : { default: mod };
}


/***/ }),

/***/ "./components/Cell/Cell.tsx":
/*!**********************************!*\
  !*** ./components/Cell/Cell.tsx ***!
  \**********************************/
/*! exports provided: Cell */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Cell", function() { return Cell; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "../node_modules/tslib/tslib.es6.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _Cells_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./Cells.css */ "./components/Cell/Cells.css");
/* harmony import */ var _Cells_css__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_Cells_css__WEBPACK_IMPORTED_MODULE_2__);




var Cell =
/** @class */
function (_super) {
  tslib__WEBPACK_IMPORTED_MODULE_0__["__extends"](Cell, _super);

  function Cell(props) {
    return _super.call(this, props) || this;
  }

  Cell.prototype.render = function () {
    var row = this.props.row;
    return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "row log-row"
    }, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "log-fields timestamp"
    }, row[0]), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "log-fields client-name"
    }, row[1]), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: 'log-fields ' + 'severity-level-' + row[4]
    }, row[4]), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "log-fields log-message"
    }, row[3]));
  };

  return Cell;
}(react__WEBPACK_IMPORTED_MODULE_1__["Component"]);



/***/ }),

/***/ "./components/Cell/Cells.css":
/*!***********************************!*\
  !*** ./components/Cell/Cells.css ***!
  \***********************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {


var content = __webpack_require__(/*! !../../../node_modules/css-loader/dist/cjs.js??ref--7-1!../../../node_modules/postcss-loader/src??ref--7-2!../../../node_modules/sass-loader/lib/loader.js!./Cells.css */ "../node_modules/css-loader/dist/cjs.js?!../node_modules/postcss-loader/src/index.js?!../node_modules/sass-loader/lib/loader.js!./components/Cell/Cells.css");

if(typeof content === 'string') content = [[module.i, content, '']];

var transform;
var insertInto;



var options = {"hmr":true}

options.transform = transform
options.insertInto = undefined;

var update = __webpack_require__(/*! ../../../node_modules/style-loader/lib/addStyles.js */ "../node_modules/style-loader/lib/addStyles.js")(content, options);

if(content.locals) module.exports = content.locals;

if(false) {}

/***/ }),

/***/ "./components/LogLayout.tsx":
/*!**********************************!*\
  !*** ./components/LogLayout.tsx ***!
  \**********************************/
/*! exports provided: LogLayout */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogLayout", function() { return LogLayout; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "../node_modules/tslib/tslib.es6.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _Cell_Cell__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./Cell/Cell */ "./components/Cell/Cell.tsx");




var LogLayout =
/** @class */
function (_super) {
  tslib__WEBPACK_IMPORTED_MODULE_0__["__extends"](LogLayout, _super);

  function LogLayout(props) {
    return _super.call(this, props) || this;
  }

  LogLayout.prototype.render = function () {
    var data = this.props.options.data;
    var styleObj = {
      overflow: 'scroll',
      height: 'inherit'
    };
    return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(react__WEBPACK_IMPORTED_MODULE_1__["Fragment"], null, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("h3", {
      className: "text-center",
      style: {
        marginTop: '24px'
      }
    }, "Logs"), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "container-fluid",
      style: styleObj
    }, data.map(function (cell) {
      return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_Cell_Cell__WEBPACK_IMPORTED_MODULE_2__["Cell"], {
        key: Math.random(),
        row: cell
      });
    })));
  };

  return LogLayout;
}(react__WEBPACK_IMPORTED_MODULE_1__["Component"]);



/***/ }),

/***/ "./components/LogPanel.tsx":
/*!*********************************!*\
  !*** ./components/LogPanel.tsx ***!
  \*********************************/
/*! exports provided: LogPanel */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogPanel", function() { return LogPanel; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "../node_modules/tslib/tslib.es6.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @grafana/ui */ "@grafana/ui");
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _LogLayout__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./LogLayout */ "./components/LogLayout.tsx");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./../constants */ "./constants/index.ts");
/* harmony import */ var _services_LogService__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./../services/LogService */ "./services/LogService.ts");




 // @ts-ignore




var LogPanel =
/** @class */
function (_super) {
  tslib__WEBPACK_IMPORTED_MODULE_0__["__extends"](LogPanel, _super);

  function LogPanel(props) {
    var _this = _super.call(this, props) || this;

    _this.ws = new WebSocket(_constants__WEBPACK_IMPORTED_MODULE_4__["SocketURL"]);

    _this.getQueryObj = function (props) {
      // @ts-ignore
      var start_date = new Date(_this.props.data.request.range.from).getTime(); // @ts-ignore

      var end_date = new Date(_this.props.data.request.range.to).getTime(); // @ts-ignore

      var interval = parseInt(_this.props.replaceVariables('$interval')); // console.log("Intrerval Now ", interval);

      var query = {
        level: _this.props.options.level.map(function (item) {
          return item.value;
        }),
        limit: _this.props.options.limit,
        start_date: start_date,
        end_date: end_date,
        interval: interval
      };
      return query;
    };

    _this.getLogsData = function (query) {
      _services_LogService__WEBPACK_IMPORTED_MODULE_5__["LogService"].getLogs(query).then(function (response) {
        response.json().then(function (logArr) {
          _this.setState({
            data: tslib__WEBPACK_IMPORTED_MODULE_0__["__spread"](_this.state.data, logArr)
          });
        });
      });
    };

    _this.updateLogsData = function (query) {
      if (_this.ws.readyState) {
        _this.ws.send(JSON.stringify(query));
      }
    };

    _this.state = {
      data: [],
      query: {},
      interval: parseInt(_this.props.replaceVariables('$interval')) || 1
    };
    return _this;
  }

  LogPanel.prototype.componentDidMount = function () {
    var _this = this;

    this.ws.onopen = function () {
      console.log('web socket connected');
      console.log(_this.ws);

      _this.updateLogsData(_this.state.query);
    };

    this.ws.onmessage = function (evt) {
      // on receiving a message, add it to the list of messages
      var rows = JSON.parse(evt.data); // Remove the previous logs data on front-end, if the rows are more than 1000.

      if (_this.state.data.length > _constants__WEBPACK_IMPORTED_MODULE_4__["LOG_LIMIT"]) {
        _this.setState({
          data: []
        });
      }

      _this.setState({
        data: tslib__WEBPACK_IMPORTED_MODULE_0__["__spread"](rows.reverse(), _this.state.data)
      });
    };

    this.ws.onclose = function () {
      console.log('web socket disconnected');
      _this.ws = new WebSocket(_constants__WEBPACK_IMPORTED_MODULE_4__["SocketURL"]);

      _this.updateLogsData(_this.state.query);
    };
  };

  LogPanel.prototype.componentDidUpdate = function (prevProps, prevState) {
    // @ts-ignore
    var isDateTimeFromChanged = this.props.data.request.range.raw.from !== prevProps.data.request.range.raw.from; // @ts-ignore

    var isDateTimeToChanged = this.props.data.request.range.raw.to !== prevProps.data.request.range.raw.to; // @ts-ignore

    var isIntervalChanged = this.props.data.request.interval !== prevProps.data.request.interval; // ERASE
    // @ts-ignore

    var interval = parseInt(this.props.replaceVariables('$interval'));

    if (JSON.stringify(this.props.options.level) !== JSON.stringify(prevProps.options.level) || this.props.options.limit !== prevProps.options.limit || interval !== this.state.interval || isDateTimeFromChanged || isDateTimeToChanged) {
      this.setState(function () {
        return {
          interval: interval
        };
      });
      console.log("Intrerval Now ", interval, isDateTimeFromChanged, isDateTimeToChanged, isIntervalChanged);
      var queryObj = this.getQueryObj(this.props);
      this.updateLogsData(queryObj);
    }
  };

  LogPanel.prototype.componentWillUnmount = function () {
    console.log('Component will unmount');
    this.ws.send('CLOSE');
    this.ws.close(1000, 'Client Initited Connection Termination');
  };

  LogPanel.prototype.render = function () {
    var _this = this;

    var options = this.props.options;
    return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["ThemeContext"].Consumer, null, function (theme) {
      return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_LogLayout__WEBPACK_IMPORTED_MODULE_3__["LogLayout"], {
        options: tslib__WEBPACK_IMPORTED_MODULE_0__["__assign"]({}, options, {
          data: _this.state.data
        }),
        theme: theme
      });
    });
  };

  return LogPanel;
}(react__WEBPACK_IMPORTED_MODULE_1__["PureComponent"]);



/***/ }),

/***/ "./components/LogPanelEditor.tsx":
/*!***************************************!*\
  !*** ./components/LogPanelEditor.tsx ***!
  \***************************************/
/*! exports provided: LogPanelEditor */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogPanelEditor", function() { return LogPanelEditor; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "../node_modules/tslib/tslib.es6.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @grafana/ui */ "@grafana/ui");
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../constants */ "./constants/index.ts");


 // import { LEVEL_OPTIONS, LIMIT_OPTIONS, DEFAULT_TIME_OPTIONS } from '../constants';


var labelWidth = 6;
var selectWidth = 12;

var LogPanelEditor =
/** @class */
function (_super) {
  tslib__WEBPACK_IMPORTED_MODULE_0__["__extends"](LogPanelEditor, _super);

  function LogPanelEditor() {
    var _this = _super !== null && _super.apply(this, arguments) || this;

    _this.onLevelChange = function (item) {
      _this.props.onOptionsChange(tslib__WEBPACK_IMPORTED_MODULE_0__["__assign"]({}, _this.props.options, {
        level: tslib__WEBPACK_IMPORTED_MODULE_0__["__spread"](item)
      }));
    };

    _this.onLimitChange = function (limit) {
      _this.props.onOptionsChange(tslib__WEBPACK_IMPORTED_MODULE_0__["__assign"]({}, _this.props.options, {
        limit: limit.value
      }));
    };

    return _this;
  } // onDateChange = (timeRange: TimeRange) => {
  //   this.props.onOptionsChange({ ...this.props.options, timeRange });
  // };


  LogPanelEditor.prototype.render = function () {
    var _a = this.props.options,
        level = _a.level,
        limit = _a.limit; // Fix for grafana TimePicker issue, where from and to are string instead of DateTime Objects
    // if (typeof timeRange.from === 'string') {
    //   timeRange.from = dateTime(timeRange.from);
    // }
    // if (typeof timeRange.to === 'string') {
    //   timeRange.to = dateTime(timeRange.to);
    // }

    return react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["PanelOptionsGroup"], {
      title: "Configuration"
    }, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "row"
    }, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "gf-form col-md-3 col-sm-3"
    }, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["FormLabel"], {
      width: labelWidth
    }, "Level"), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["Select"], {
      width: selectWidth,
      options: _constants__WEBPACK_IMPORTED_MODULE_3__["LEVEL_OPTIONS"],
      onChange: this.onLevelChange,
      value: level,
      backspaceRemovesValue: true,
      isLoading: true,
      isMulti: true
    })), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement("div", {
      className: "gf-form col-md-3 col-sm-3"
    }, react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["FormLabel"], {
      width: labelWidth
    }, "Limit"), react__WEBPACK_IMPORTED_MODULE_1___default.a.createElement(_grafana_ui__WEBPACK_IMPORTED_MODULE_2__["Select"], {
      width: selectWidth,
      options: _constants__WEBPACK_IMPORTED_MODULE_3__["LIMIT_OPTIONS"],
      onChange: this.onLimitChange,
      value: _constants__WEBPACK_IMPORTED_MODULE_3__["LIMIT_OPTIONS"].find(function (option) {
        return option.value === limit.toString();
      }),
      backspaceRemovesValue: true,
      isLoading: true
    }))));
  };

  return LogPanelEditor;
}(react__WEBPACK_IMPORTED_MODULE_1__["PureComponent"]);



/***/ }),

/***/ "./constants/index.ts":
/*!****************************!*\
  !*** ./constants/index.ts ***!
  \****************************/
/*! exports provided: LoggerGetLogsAPI, SocketURL, DEFAULT_TIME_RANGE, DEFAULT_LOG_PROPS, LOG_LIMIT, LEVEL_OPTIONS, LIMIT_OPTIONS, DEFAULT_TIME_OPTIONS */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LoggerGetLogsAPI", function() { return LoggerGetLogsAPI; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SocketURL", function() { return SocketURL; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_TIME_RANGE", function() { return DEFAULT_TIME_RANGE; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_LOG_PROPS", function() { return DEFAULT_LOG_PROPS; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LOG_LIMIT", function() { return LOG_LIMIT; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LEVEL_OPTIONS", function() { return LEVEL_OPTIONS; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LIMIT_OPTIONS", function() { return LIMIT_OPTIONS; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_TIME_OPTIONS", function() { return DEFAULT_TIME_OPTIONS; });
/* harmony import */ var _grafana_data__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @grafana/data */ "@grafana/data");
/* harmony import */ var _grafana_data__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_grafana_data__WEBPACK_IMPORTED_MODULE_0__);
 // Constants for LogService

var LoggerGetLogsAPI = "http://" + window.location.hostname + ":8004/api_ws/getlogs";
var SocketURL = "ws://" + window.location.hostname + ":8004/api_ws/ws";
var DEFAULT_TIME_RANGE = {
  from: Object(_grafana_data__WEBPACK_IMPORTED_MODULE_0__["dateTime"])(),
  to: Object(_grafana_data__WEBPACK_IMPORTED_MODULE_0__["dateTime"])(),
  raw: {
    from: 'now-6h',
    to: 'now'
  }
};
var DEFAULT_LEVEL = [{
  value: '10',
  label: '10'
}];
var DEFAULT_LOG_PROPS = {
  level: DEFAULT_LEVEL,
  limit: 20,
  timeRange: DEFAULT_TIME_RANGE,
  data: [[]]
}; // Constants for LogPanel

var LOG_LIMIT = 100; // Constants for LogPanelEditor

var LEVEL_OPTIONS = [{
  value: '10',
  label: '10'
}, {
  value: '20',
  label: '20'
}, {
  value: '30',
  label: '30'
}];
var LIMIT_OPTIONS = [{
  value: '10',
  label: '10'
}, {
  value: '20',
  label: '20'
}, {
  value: '50',
  label: '50'
}];
var DEFAULT_TIME_OPTIONS = [{
  from: 'now-5m',
  to: 'now',
  display: 'Last 5 minutes',
  section: 3
}, {
  from: 'now-15m',
  to: 'now',
  display: 'Last 15 minutes',
  section: 3
}, {
  from: 'now-30m',
  to: 'now',
  display: 'Last 30 minutes',
  section: 3
}, {
  from: 'now-1h',
  to: 'now',
  display: 'Last 1 hour',
  section: 3
}, {
  from: 'now-3h',
  to: 'now',
  display: 'Last 3 hours',
  section: 3
}, {
  from: 'now-6h',
  to: 'now',
  display: 'Last 6 hours',
  section: 3
}, {
  from: 'now-12h',
  to: 'now',
  display: 'Last 12 hours',
  section: 3
}, {
  from: 'now-24h',
  to: 'now',
  display: 'Last 24 hours',
  section: 3
}, {
  from: 'now-2d',
  to: 'now',
  display: 'Last 2 days',
  section: 3
}, {
  from: 'now-7d',
  to: 'now',
  display: 'Last 7 days',
  section: 3
}, {
  from: 'now-30d',
  to: 'now',
  display: 'Last 30 days',
  section: 3
}, {
  from: 'now-90d',
  to: 'now',
  display: 'Last 90 days',
  section: 3
}, {
  from: 'now-6M',
  to: 'now',
  display: 'Last 6 months',
  section: 3
}, {
  from: 'now-1y',
  to: 'now',
  display: 'Last 1 year',
  section: 3
}, {
  from: 'now-2y',
  to: 'now',
  display: 'Last 2 years',
  section: 3
}, {
  from: 'now-5y',
  to: 'now',
  display: 'Last 5 years',
  section: 3
}, {
  from: 'now-1d/d',
  to: 'now-1d/d',
  display: 'Yesterday',
  section: 3
}, {
  from: 'now-2d/d',
  to: 'now-2d/d',
  display: 'Day before yesterday',
  section: 3
}, {
  from: 'now-7d/d',
  to: 'now-7d/d',
  display: 'This day last week',
  section: 3
}, {
  from: 'now-1w/w',
  to: 'now-1w/w',
  display: 'Previous week',
  section: 3
}, {
  from: 'now-1M/M',
  to: 'now-1M/M',
  display: 'Previous month',
  section: 3
}, {
  from: 'now-1y/y',
  to: 'now-1y/y',
  display: 'Previous year',
  section: 3
}, {
  from: 'now/d',
  to: 'now/d',
  display: 'Today',
  section: 3
}, {
  from: 'now/d',
  to: 'now',
  display: 'Today so far',
  section: 3
}, {
  from: 'now/w',
  to: 'now/w',
  display: 'This week',
  section: 3
}, {
  from: 'now/w',
  to: 'now',
  display: 'This week so far',
  section: 3
}, {
  from: 'now/M',
  to: 'now/M',
  display: 'This month',
  section: 3
}, {
  from: 'now/M',
  to: 'now',
  display: 'This month so far',
  section: 3
}, {
  from: 'now/y',
  to: 'now/y',
  display: 'This year',
  section: 3
}, {
  from: 'now/y',
  to: 'now',
  display: 'This year so far',
  section: 3
}];

/***/ }),

/***/ "./module.tsx":
/*!********************!*\
  !*** ./module.tsx ***!
  \********************/
/*! exports provided: plugin */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "plugin", function() { return plugin; });
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @grafana/ui */ "@grafana/ui");
/* harmony import */ var _grafana_ui__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_grafana_ui__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _components_LogPanel__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./components/LogPanel */ "./components/LogPanel.tsx");
/* harmony import */ var _components_LogPanelEditor__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./components/LogPanelEditor */ "./components/LogPanelEditor.tsx");
/* harmony import */ var _src_services_LogService__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../src/services/LogService */ "./services/LogService.ts");




var plugin = new _grafana_ui__WEBPACK_IMPORTED_MODULE_0__["PanelPlugin"](_components_LogPanel__WEBPACK_IMPORTED_MODULE_1__["LogPanel"]);
plugin.setEditor(_components_LogPanelEditor__WEBPACK_IMPORTED_MODULE_2__["LogPanelEditor"]);
plugin.setDefaults(_src_services_LogService__WEBPACK_IMPORTED_MODULE_3__["LogService"].getDefaults());

/***/ }),

/***/ "./services/LogService.ts":
/*!********************************!*\
  !*** ./services/LogService.ts ***!
  \********************************/
/*! exports provided: LogService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogService", function() { return LogService; });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "./constants/index.ts");

var LogService = function () {
  function getLogs(query) {
    if (query === void 0) {
      query = '';
    }

    var url = _constants__WEBPACK_IMPORTED_MODULE_0__["LoggerGetLogsAPI"] + query;
    console.log('url', url);
    return fetch(url, {
      method: 'GET'
    }).then(function (response) {
      if (!response.ok) {
        throw Error('Network GET request failed');
      }

      console.log('Response to GET', response);
      return response;
    });
  }

  return {
    getDefaults: function getDefaults() {
      return _constants__WEBPACK_IMPORTED_MODULE_0__["DEFAULT_LOG_PROPS"];
    },
    getLogs: getLogs
  };
}();

/***/ }),

/***/ "@grafana/data":
/*!********************************!*\
  !*** external "@grafana/data" ***!
  \********************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = __WEBPACK_EXTERNAL_MODULE__grafana_data__;

/***/ }),

/***/ "@grafana/ui":
/*!******************************!*\
  !*** external "@grafana/ui" ***!
  \******************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = __WEBPACK_EXTERNAL_MODULE__grafana_ui__;

/***/ }),

/***/ "react":
/*!************************!*\
  !*** external "react" ***!
  \************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = __WEBPACK_EXTERNAL_MODULE_react__;

/***/ })

/******/ })});;
//# sourceMappingURL=module.js.map