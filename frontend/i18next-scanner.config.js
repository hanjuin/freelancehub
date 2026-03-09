module.exports = {
  input: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}'
  ],
  output: './',

  options: {
    debug: false,
    removeUnusedKeys: false,

    lngs: ['en', 'zh'],
    defaultLng: 'en',

    ns: ['translation'],
    defaultNs: 'translation',

    resource: {
      loadPath: 'src/locales/{{lng}}/{{ns}}.json',
      savePath: 'src/locales/{{lng}}/{{ns}}.json',
      jsonIndent: 2
    },

    keySeparator: false,
    nsSeparator: false,

    interpolation: {
      prefix: '{{',
      suffix: '}}'
    }
  }
}