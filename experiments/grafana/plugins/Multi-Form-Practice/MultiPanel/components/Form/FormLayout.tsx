import React, { PureComponent } from 'react';
import {MyProps} from '../../types';

// interface Props extends MyProps { }
// interface Props {
//     options: Options;
//     onChange: (formOptions: Options) => void;
// }
interface Props extends MyProps {}


export class FormLayout extends PureComponent<Props> {
    // constructor(props) {
    //     super(props);
    //     this.state = {
    //         fName: null,
    //         lName: null,
    //         age: null,
    //         gender: null,
    //         imageUrl: null
    //     };
    // }

    render() {
        const { options } = this.props;
        const { fName, lName, age, gender, imageUrl } = options.formOptions;
        return (
            <div>
                <p>Name:  <b>{ fName } { lName }</b></p>
                <p>Age: <b>{ age }</b></p>
                <span className="gf-form-label width-4">Hello</span>
                <input
                    type="text"
                    className="gf-form-input width-8"
                    value={gender}
                />
                <p>Here is my favorite photo! </p>
                <iframe src={imageUrl} width="700px" height="400px" />
            </div>
        );
    }
}
