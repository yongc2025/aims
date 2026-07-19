const tailwindcss = require('./node_modules/tailwindcss/lib/index.js');
const autoprefixer = require('./node_modules/autoprefixer/lib/autoprefixer.js');

module.exports = {
  plugins: [
    tailwindcss(),
    autoprefixer(),
  ],
};
