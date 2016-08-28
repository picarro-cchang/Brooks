import React from "react";
import {render} from "react-dom";
import Applog from "./components/Applog";

const app = document.getElementById('app');

render((
    <Applog/>
), app);
