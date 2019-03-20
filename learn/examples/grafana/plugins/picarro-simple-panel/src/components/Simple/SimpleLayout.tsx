import React, { Component } from 'react';

import { LayoutProps } from '../../types';
import PicarroAPI from '../../api/PicarroAPI';

interface Props extends LayoutProps { }

export class SimpleLayout extends Component<Props, any> {
    constructor(props) {
        super(props);
        this.state = { message: 'None' };
    }

    onButtonClick(options) {
        PicarroAPI.getRequest("http://numbersapi.com/random/trivia").then(response => {
            response.text().then(text => { 
                this.setState({ message: text });
                PicarroAPI.postData("http://localhost:8888/testing", {message: text}).then(response => {
                    response.text().then(text => { console.log(text) });
                });
            });
        });
    }

    render() {
        const { height, width, theme, options, onInterpolate } = this.props;
        const { minValue, maxValue, textValue } = options;
        // <div>Text = {templateSrv.replace(textValue)}</div>
        return (
            <div>
                <div
                    style={{
                        display: 'flex',
                        width: '100%',
                        height: '100%',
                        flexDirection: 'column',
                    }}>
                </div>
                <div>
                    <h1>Parameter values</h1>
                    <div>Minimum = {minValue}</div>
                    <div>Maximum = {maxValue}</div>
                    <div>Text = { onInterpolate(textValue) }</div>
                    <div>Height = {height}</div>
                    <div>Width = {width}</div>
                    <div>Theme = {theme.type}</div>
                    <button className="btn btn-primary btn-large" onClick={(options) => this.onButtonClick(options)}>
                        Click Me
                    </button>
                    <div>Message = {this.state.message}</div>
                </div>
            </div>
        );
    }
}
