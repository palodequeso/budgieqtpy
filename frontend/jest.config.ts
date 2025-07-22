import type { Config } from 'jest';

const config: Config = {
    verbose: true,
    testEnvironment: 'jsdom',
    testMatch: [
        '<rootDir>/tests/**/*.spec.tsx',
        '<rootDir>/tests/**/*.spec.ts',
    ],
    transform: {
        '^.+\\.tsx?$': 'ts-jest',
    },
    collectCoverage: true,
    coverageDirectory: '<rootDir>/coverage/frontend',
    coveragePathIgnorePatterns: ['<rootDir>/tests/'],
    coverageReporters: ['text', 'lcovonly'],
    setupFilesAfterEnv: ['<rootDir>/tests/setupTests.ts'],
};

export default config;
