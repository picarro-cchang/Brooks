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
        'panels/Modbus-Settings/module': "./panels/Modbus-Settings/module.tsx",
        'panels/Network-Settings/module': "./panels/Network-Settings/module.tsx",
        'panels/MFC/module': "./panels/MFC/module.tsx"
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
            { from: 'panels/Modbus-Settings/*.json', to: "."},
            { from: 'panels/Network-Settings/*.json', to: "."},
            { from: 'panels/MFC/*.json', to: "."},
            { from: 'img', to: "./img"},
            { from: 'dashboards/*', to: "."}
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


