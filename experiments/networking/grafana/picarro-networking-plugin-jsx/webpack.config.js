const path = require('path');
const webpack = require('webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');

module.exports = {
  node: {
    fs: 'empty',
    net: 'empty',
    tls: 'empty',
  },
  context: path.join(__dirname, 'src'),
  entry: {
    module: './module.js',
  },
  devtool: 'source-map',
  output: {
    filename: '[name].js',
    path: path.join(__dirname, 'dist'),
    libraryTarget: 'amd',
  },
  externals: ['lodash', 'moment', 'react', 'react-dom', '@grafana/ui'],
  plugins: [
    new CleanWebpackPlugin('dist', { allowExternal: true }),
    new webpack.optimize.OccurrenceOrderPlugin(),
    new CopyWebpackPlugin([
      { from: '*.json', to: '.' },
      { from: '../README.md', to: '.' },
      { from: 'partials/*', to: '.' },
      { from: 'img/*', to: '.' },
    ]),
  ],
  resolve: {
    extensions: ['.ts', '.js', '.tsx'],
  },
  module: {
    rules: [
      { test: /\.(js)$/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
            "@babel/preset-env",
            "@babel/preset-react",
            ]
          },
        },
      },
      {
        test: /\.css$/,
        use: [
          {
            loader: 'style-loader',
          },
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              sourceMap: true,
            },
          },
        ],
      },
    ],
  },
};
