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
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node', 'css'],
  roots: ["<rootDir>/src/panels/StateMachine/components"],
  snapshotSerializers: ["enzyme-to-json/serializer"],
  setupFilesAfterEnv: ["<rootDir>/setupEnzyme.ts"],
  setupFiles: ["./setupJest.js"],
  moduleNameMapper: {
    "\\.(css|sass)$": "identity-obj-proxy",
  },
};
