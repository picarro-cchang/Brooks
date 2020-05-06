module.exports = {
    transform: {
      '^.+\\.tsx?$': 'ts-jest',
    },
    globals: {
      "ts-jest": {
        tsConfigFile: "tsconfig.json"
      }
    },
    automock: false,
    testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.tsx?$',
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node', 'css', 'sass'],
    roots: ["<rootDir>/src/panels/GrafanaLogger/src/components"],
    snapshotSerializers: ["enzyme-to-json/serializer"],
    setupFilesAfterEnv: ["<rootDir>/setupEnzyme.ts"],
    moduleNameMapper: {
      "\\.(css|sass)$": "identity-obj-proxy",
    },
  };
  