module.exports = {
    transform: {
      '^.+\\.tsx?$': 'ts-jest',
    },
    globals: {
      "ts-jest": {
        tsConfig: "tsconfig.json"
      }
    },
    automock: false,
    testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.tsx?$',
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node', 'css'],
    roots: ["<rootDir>/src/panels/UserDataFileGenerator/src/"],
    snapshotSerializers: ["enzyme-to-json/serializer"],
    setupFilesAfterEnv: ["<rootDir>/setupEnzyme.ts"],
    moduleNameMapper: {
      "\\.(css|sass)$": "identity-obj-proxy",
    }
  };
