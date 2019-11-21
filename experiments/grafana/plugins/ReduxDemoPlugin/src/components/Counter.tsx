import React, { Component, } from 'react'
import PropTypes from 'prop-types'
import { CounterComponentProps } from './types';

interface Props extends CounterComponentProps { };

class Counter extends Component<Props, any> {
  constructor(props: Props) {
    super(props);
    this.incrementAsync = this.incrementAsync.bind(this);
    this.incrementIfOdd = this.incrementIfOdd.bind(this);
  }

  incrementIfOdd() {
    if (this.props.value % 2 !== 0) {
      this.props.onIncrement()
    }
  }

  incrementAsync() {
    setTimeout(this.props.onIncrement, 1000)
  }

  render() {
    const { value, onIncrement, onDecrement } = this.props;
    return (
      <p>
        Clicked: {value} times
            {' '}
        <button onClick={onIncrement}>
          +
            </button>
        {' '}
        <button onClick={onDecrement}>
          -
            </button>
        {' '}
        <button onClick={this.incrementIfOdd}>
          Increment if odd
            </button>
        {' '}
        <button onClick={this.incrementAsync}>
          Increment async
            </button>
      </p>
    )
  }
}

export default Counter;
