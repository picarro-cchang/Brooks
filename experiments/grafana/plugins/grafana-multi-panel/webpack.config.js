const path = require("path");
const webpack = require("webpack");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const CleanWebpackPlugin = require("clean-webpack-plugin");

module.exports = {
  node: {
    fs: "empty",
    net: "empty",
    tls: "empty"
  },
  context: path.join(__dirname, "src"),
  entry: {
    './module': "./module.tsx",
    'panels/StateMachine/module': "./panels/StateMachine/module.tsx"
  },
  devtool: "source-map",
  output: {
    filename: "[name].js",
    path: path.join(__dirname, "dist"),
    libraryTarget: "amd"
  },
  externals: ["react", "react-dom", "@grafana/ui"],
  plugins: [
    new CleanWebpackPlugin(),
    new webpack.optimize.OccurrenceOrderPlugin(),
    new CopyWebpackPlugin([
      { from: "plugin.json", to: "." },
      { from: "../README.md", to: "." },
      { from: 'img', to: "./img"},
      { from: 'panels/StateMachine/*.json', to: "."},

     // { from: 'config', to: "./config"},
      { from: 'dashboards/*', to: "."}

      // { from: 'panels/plugin.json', to: "."},

      //{ from: 'dashboards/DashboardCopy.json', to: "."}
    ])
  ],
  resolve: {
    extensions: [".ts", ".js", ".tsx"]
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loaders: [
          {
            loader: "babel-loader",
            options: { presets: ["env"] }
          },
          "ts-loader"
        ],
        exclude: /(node_modules)/
      }
    ]
  }
};


