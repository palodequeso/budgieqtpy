import { api } from '../../components/renderUtils';

const request = {
    url: '',
    method: '',
    body: {},
};
beforeAll(() => {
    global.fetch = jest.fn((url: string, opts: any) => {
        request.url = url;
        request.method = opts.method;
        request.body = opts.body;
        return Promise.resolve({
            json: () => {
                return Promise.resolve(true);
            },
        });
    }) as jest.Mock;
});

afterAll(() => {
    jest.clearAllMocks();
});

test('api should exist I guess', () => {
    expect(api).toBeDefined();
});
