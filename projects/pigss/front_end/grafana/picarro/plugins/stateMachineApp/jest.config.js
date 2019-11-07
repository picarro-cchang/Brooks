module.exports = {
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest"
  },
  roots: ["<rootDir>/src/panels/StateMachine/components"],
  moduleNameMapper: {
    "\\.(css|less)$": "<rootDir>/__mocks__/styleMock.js",
    "\\.(gif|ttf|eot|svg)$": "<rootDir>/__mocks__/fileMock.js"
  },
  setupFiles: ["./test/jest-shim.ts", "./test/jest-setup.ts"],
  snapshotSerializers: ["enzyme-to-json/serializer"]
};
