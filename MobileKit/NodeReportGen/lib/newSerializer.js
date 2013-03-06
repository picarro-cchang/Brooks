/* newSerializer.js constructs a Serializer object. */
/*global exports, module, require */

(function() {
	'use strict';
    var events = require('events');
    var util = require('util');
    var _ = require('underscore');

    // A serializer is used to listen to a dataEmitter (something which emits "data", "error"
    //    and "end" events) and which serializes the data for at most one consumer which receives a
    //    "data" event from the serializer when data are available. The consumer must then call
    //    the "acknowledge" method before it is able to receive another "data" event.

    function Serializer(dataEmitter) {
        var that = this;
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.rack = [];
        this.active = true;
        this.ended = false;

        dataEmitter.on("error", function (err) {
            that.rack = [];
            that.active = false;
            that.emit("error", err);
        });

        dataEmitter.on("data", function (data) {
            that.rack.push(data);
            if (that.active) {
                that.active = false;
                that.emit("data", that.rack.shift());
            }
        });

        dataEmitter.on("end", function () {
            that.ended = true;
            if (that.active) {
                that.emit("end");
            }
        });
        this.setMaxListeners(1);
    }

    util.inherits(Serializer, events.EventEmitter);

    Serializer.prototype.acknowledge = function () {
        this.active = true;
        if (!_.isEmpty(this.rack)) {
            this.active = false;
            this.emit("data", this.rack.shift());
        }
        else if (this.ended) this.emit("end");
    };

    function newSerializer(dataEmitter) {
        return new Serializer(dataEmitter);
    }

    module.exports = newSerializer;

})();
