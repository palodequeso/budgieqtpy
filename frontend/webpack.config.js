const path = require('path');

module.exports = {
  cache: true,
  mode: 'development',
  devtool: 'source-map',
  entry: './index.tsx',
  module: {
    rules: [{
        test: /\.tsx?$/,
        use: ['ts-loader'],
        exclude: /node_modules/
    }, {
        test: /\.scss$/,
        use: ['style-loader', 'css-loader', 'sass-loader'],
        exclude: /node_modules/
    }, {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
        include: path.resolve(__dirname, 'node_modules', '@mui', 'x-data-grid')
    }]
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js", ".scss", ".css"],
  },
  output: {
    filename: 'index.js',
    path: path.resolve(__dirname, 'dist/frontend')
  },
  target: 'web',
  plugins: [],
  watchOptions: {
    ignored: '**/dist/**',
  }
};
