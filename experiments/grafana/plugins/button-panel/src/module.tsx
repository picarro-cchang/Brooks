import React from 'react';
import { PanelPlugin } from "@grafana/ui";
import ButtonLayout from "./components/ButtonLayout"

export const plugin = new PanelPlugin(ButtonLayout);
